import asyncio
import json
import logging
import time

import websockets.exceptions
from websockets.asyncio.server import serve as ws_serve

from iracing_client import IRacingClient
from metrics import LoopMetrics, SampleMetrics, SessionMetrics
from telemetry_vars import TELEMETRY_VAR_NAMES, TELEMETRY_VAR_SET
from mdns import MDNSAdvertiser

logger = logging.getLogger(__name__)

_TICK_INTERVAL = 1 / 60  # ~60 Hz


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
        self._client: IRacingClient | None = None
        self._connection_count = 0
        self._loop_metrics = LoopMetrics()
        self._var_get_metrics = SampleMetrics()

    # -------------------------------------------------------------------------
    # Client handler — called for each new WebSocket connection
    # -------------------------------------------------------------------------

    async def handle_client(self, websocket) -> None:
        if self._connection_count == 0:
            self._client = self._ir_client_factory()
            self._client.startup()
        self._connection_count += 1
        client = self._client
        logger.info("WebSocket client connected")

        subscriptions: set[str] = set()
        session_metrics = SessionMetrics()
        read_task = asyncio.create_task(self._read_commands(websocket, client, subscriptions, self._loop_metrics, session_metrics))
        try:
            await self._telemetry_loop(websocket, client, subscriptions, self._loop_metrics, session_metrics)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            read_task.cancel()
            try:
                await read_task
            except (asyncio.CancelledError, Exception):
                pass
            self._connection_count -= 1
            if self._connection_count == 0:
                client.shutdown()
                self._client = None
            logger.info("WebSocket client disconnected")

    # -------------------------------------------------------------------------
    # Command reader — runs concurrently with _telemetry_loop
    # -------------------------------------------------------------------------

    async def _read_commands(self, websocket, client: IRacingClient, subscriptions: set[str], loop_metrics: LoopMetrics, session_metrics: SessionMetrics) -> None:
        try:
            async for raw in websocket:
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
                    await self._handle_read(websocket, client, var)
                elif command == "sessioninfo":
                    await self._handle_session_info(websocket, client)
                elif command == "metrics":
                    await self._handle_metrics(websocket, loop_metrics)
                elif command == "ping":
                    await websocket.send(json.dumps({"type": "pong"}))
                elif command == "status":
                    await websocket.send(json.dumps({"type": "status", "connected": client.is_connected}))
        except websockets.exceptions.ConnectionClosed:
            pass

    # -------------------------------------------------------------------------
    # Telemetry loop — polls iRacing and pushes to client; survives reconnects
    # -------------------------------------------------------------------------

    async def _telemetry_loop(self, websocket, client: IRacingClient, subscriptions: set[str], loop_metrics: LoopMetrics, session_metrics: SessionMetrics) -> None:
        was_connected = False
        nextUpdateTime = 0.0
        while True:
            connected = client.is_connected
            if not connected:
                if was_connected:
                    was_connected = False
                    await websocket.send(json.dumps({"type": "status", "connected": False}))
                client.startup()
                await asyncio.sleep(0.25)
                continue

            if not was_connected:
                was_connected = True
                await websocket.send(json.dumps({"type": "status", "connected": True}))

            if nextUpdateTime <= time.monotonic():
                loop_metrics.record_get(session_metrics.record_get())
                nextUpdateTime = time.monotonic() + self.update_interval
                if subscriptions:
                    t0 = time.monotonic()
                    snapshot = client.get_telemetry(frozenset(subscriptions), self._var_get_metrics)
                    data = {k: v for k, v in snapshot.items() if k in subscriptions}
                    await websocket.send(json.dumps({"type": "telemetry", "data": data}))
                    loop_metrics.record((time.monotonic() - t0) * 1000)
            else:
                loop_metrics.record_skip()
                session_metrics.record_skip()
            await asyncio.sleep(0.001)

    # -------------------------------------------------------------------------
    # Command handlers
    # -------------------------------------------------------------------------

    async def _handle_metrics(self, websocket, loop_metrics: LoopMetrics) -> None:
        await websocket.send(json.dumps({
            "type": "metrics",
            "data": {
                "telemetry_loop": loop_metrics.report(),
                "var_get": self._var_get_metrics.report(),
            },
        }))

    async def _handle_session_info(self, websocket, client: IRacingClient) -> None:
        data = client.get_session_info()
        await websocket.send(json.dumps({"type": "sessionInfo", "data": data}))

    async def _handle_read(self, websocket, client: IRacingClient, var_str: str) -> None:
        if not var_str:
            return
        if var_str == "all":
            var_names = frozenset(TELEMETRY_VAR_NAMES)
        else:
            var_names = frozenset(v.strip() for v in var_str.split(",") if v.strip())
        if not var_names:
            return
        data = client.get_telemetry(var_names, self._var_get_metrics)
        await websocket.send(json.dumps({"type": "read", "data": data}))

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
        asyncio.run(self._serve())

    async def _serve(self) -> None:
        logger.info("Starting telemetry server on ws://%s:%d", self.host, self.port)
        advertiser = MDNSAdvertiser(port=self.port) if self.advertise_mdns else None
        if advertiser:
            await advertiser.start()
        try:
            async with ws_serve(self.handle_client, self.host, self.port):
                await asyncio.Future()  # Run until cancelled (Ctrl+C)
        finally:
            if advertiser:
                await advertiser.stop()
