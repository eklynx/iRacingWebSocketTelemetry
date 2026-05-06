import asyncio
import json
import logging
import threading
import time
from collections import deque

import websockets.exceptions
from websockets.sync.server import serve as ws_serve

from iracing_client import IRacingClient
from telemetry_vars import TELEMETRY_VAR_NAMES, TELEMETRY_VAR_SET
from mdns import MDNSAdvertiser

logger = logging.getLogger(__name__)

_TICK_INTERVAL = 1 / 60  # ~60 Hz


class LoopMetrics:
    def __init__(self, maxlen: int = 1000):
        self._samples: deque[float] = deque(maxlen=maxlen)

    def record(self, ms: float) -> None:
        self._samples.append(ms)

    def to_dict(self) -> dict:
        samples = sorted(self._samples)
        n = len(samples)
        if n == 0:
            return {"count": 0}

        def pct(p: float) -> float:
            idx = p / 100 * (n - 1)
            lo = int(idx)
            hi = min(lo + 1, n - 1)
            return round(samples[lo] + (idx - lo) * (samples[hi] - samples[lo]), 3)

        return {
            "count": n,
            "min": round(samples[0], 3),
            "max": round(samples[-1], 3),
            "avg": round(sum(samples) / n, 3),
            "p50": pct(50),
            "p90": pct(90),
            "p95": pct(95),
        }


class TelemetryServer:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        ir_client_factory=None,
        update_interval: float = _TICK_INTERVAL,
        advertise_mdns: bool = True,
    ):
        self.host = host
        self.port = port
        self._ir_client_factory = ir_client_factory or (lambda: IRacingClient())
        self.update_interval = update_interval
        self.advertise_mdns = advertise_mdns
        self._tick_condition = threading.Condition()
        self._tick_generation = 0
        self._telemetry_snapshot: dict = {}
        self._ir_connected: bool = False
        self._shared_client: IRacingClient | None = None
        self._shutdown = threading.Event()
        self._active_connections: set = set()
        self._connections_lock = threading.Lock()

    # -------------------------------------------------------------------------
    # Ticker — runs in its own thread with its own asyncio event loop
    # -------------------------------------------------------------------------

    async def _run_ticker(self) -> None:
        advertiser = MDNSAdvertiser(port=self.port) if self.advertise_mdns else None
        if advertiser:
            await advertiser.start()
        try:
            await self._ticker()
        finally:
            if advertiser:
                await advertiser.stop()
            if self._shared_client:
                self._shared_client.shutdown()

    async def _ticker(self) -> None:
        client = self._ir_client_factory()
        self._shared_client = client
        client.startup()
        was_connected = False
        loop = asyncio.get_running_loop()
        next_tick = loop.time()

        while True:
            connected = client.is_connected

            if not connected:
                if was_connected:
                    was_connected = False
                    logger.info("iRacing disconnected")
                    with self._tick_condition:
                        self._ir_connected = False
                        self._tick_generation += 1
                        self._tick_condition.notify_all()
                client.startup()
                await asyncio.sleep(0.5)
                next_tick = loop.time()
                continue

            if not was_connected:
                was_connected = True
                logger.info("iRacing connected")

            snapshot = client.get_telemetry()

            with self._tick_condition:
                self._ir_connected = True
                self._telemetry_snapshot = snapshot
                self._tick_generation += 1
                self._tick_condition.notify_all()

            next_tick += self.update_interval
            now = loop.time()
            if next_tick <= now:
                next_tick = now
                await asyncio.sleep(0)
            else:
                while loop.time() < next_tick:
                    await asyncio.sleep(0.001)

    # -------------------------------------------------------------------------
    # Session handling — each connection runs _handle_client in its own thread
    # -------------------------------------------------------------------------

    def _handle_client(self, websocket) -> None:
        subscriptions: set[str] = set()
        stop_event = threading.Event()
        metrics = LoopMetrics()
        logger.info("WebSocket client connected")

        with self._connections_lock:
            self._active_connections.add(websocket)

        reader = threading.Thread(
            target=self._read_commands,
            args=(websocket, subscriptions, stop_event, metrics),
            daemon=True,
        )
        reader.start()

        try:
            self._telemetry_loop(websocket, subscriptions, stop_event, metrics)
        finally:
            stop_event.set()
            websocket.close()
            with self._connections_lock:
                self._active_connections.discard(websocket)
            with self._tick_condition:
                self._tick_condition.notify_all()
            reader.join(timeout=2)
            logger.info("WebSocket client disconnected")

    def _read_commands(self, websocket, subscriptions: set[str], stop_event: threading.Event, metrics: LoopMetrics) -> None:
        try:
            for raw in websocket:
                if stop_event.is_set():
                    break
                parts = str(raw).strip().split(maxsplit=1)
                if not parts:
                    continue
                command = parts[0].lower()
                var = parts[1].strip() if len(parts) > 1 else ""

                if command == "sub":
                    self._handle_subscribe(var, subscriptions)
                elif command == "unsub":
                    self._handle_unsubscribe(var, subscriptions)
                elif command == "read":
                    self._handle_read(websocket, var)
                elif command == "sessioninfo":
                    self._handle_session_info(websocket)
                elif command == "ping":
                    websocket.send(json.dumps({"type": "pong"}))
                elif command == "status":
                    websocket.send(json.dumps({"type": "status", "connected": self._ir_connected}))
                elif command == "metrics":
                    websocket.send(json.dumps({"type": "metrics", **metrics.to_dict()}))
        except Exception:
            stop_event.set()

    def _telemetry_loop(self, websocket, subscriptions: set[str], stop_event: threading.Event, metrics: LoopMetrics) -> None:
        was_connected = False
        last_tick = 0

        while not stop_event.is_set():
            with self._tick_condition:
                self._tick_condition.wait_for(
                    lambda: self._tick_generation != last_tick or stop_event.is_set() or self._shutdown.is_set(),
                    timeout=1.0,
                )
                if stop_event.is_set() or self._shutdown.is_set():
                    break
                last_tick = self._tick_generation
                connected = self._ir_connected
                snapshot = self._telemetry_snapshot

            t0 = time.perf_counter()
            try:
                if not connected:
                    if was_connected:
                        was_connected = False
                        websocket.send(json.dumps({"type": "disconnected"}))
                    continue

                if not was_connected:
                    was_connected = True
                    websocket.send(json.dumps({"type": "status", "connected": True}))

                if subscriptions:
                    data = {k: v for k, v in snapshot.items() if k in subscriptions}
                    websocket.send(json.dumps({"type": "telemetry", "data": data}))
            except websockets.exceptions.ConnectionClosed:
                break
            finally:
                metrics.record((time.perf_counter() - t0) * 1000)

    # -------------------------------------------------------------------------
    # Command handlers
    # -------------------------------------------------------------------------

    def _handle_session_info(self, websocket) -> None:
        if self._shared_client is None:
            return
        data = self._shared_client.get_session_info()
        websocket.send(json.dumps({"type": "sessionInfo", "data": data}))

    def _handle_read(self, websocket, var_str: str) -> None:
        if not var_str or self._shared_client is None:
            return
        if var_str == "all":
            var_names = frozenset(TELEMETRY_VAR_NAMES)
        else:
            var_names = frozenset(v.strip() for v in var_str.split(",") if v.strip())
        if not var_names:
            return
        data = self._shared_client.get_telemetry(var_names)
        websocket.send(json.dumps({"type": "read", "data": data}))

    def _handle_subscribe(self, var_str: str, subscriptions: set[str]) -> None:
        if var_str == "all":
            subscriptions.update(TELEMETRY_VAR_NAMES)
            logger.debug("Subscribed to all vars")
        elif var_str:
            for var in var_str.split(","):
                var = var.strip()
                if var not in TELEMETRY_VAR_SET:
                    logger.debug("Specified var not valid: %s", var)
                    continue
                subscriptions.add(var)
                logger.debug("Subscribed to: %s", var)

    def _handle_unsubscribe(self, var_str: str, subscriptions: set[str]) -> None:
        if var_str == "all":
            subscriptions.clear()
            logger.debug("Unsubscribed from all vars")
        elif var_str:
            for var in var_str.split(","):
                var = var.strip()
                if var not in TELEMETRY_VAR_SET:
                    logger.debug("Specified var not valid: %s", var)
                    continue
                subscriptions.discard(var)
                logger.debug("Unsubscribed from: %s", var)

    # -------------------------------------------------------------------------
    # Entry point
    # -------------------------------------------------------------------------

    def start(self) -> None:
        logger.info("Starting telemetry server on ws://%s:%d", self.host, self.port)
        ticker_thread = threading.Thread(
            target=lambda: asyncio.run(self._run_ticker()),
            daemon=True,
            name="iracing-ticker",
        )
        ticker_thread.start()
        try:
            with ws_serve(self._handle_client, self.host, self.port) as server:
                server.serve_forever()
        finally:
            self._shutdown.set()
            with self._connections_lock:
                connections = list(self._active_connections)
            for ws in connections:
                try:
                    ws.close()
                except Exception:
                    pass
            with self._tick_condition:
                self._tick_condition.notify_all()
