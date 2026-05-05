import asyncio
import json
import logging

import websockets
import websockets.exceptions

from iracing_client import IRacingClient
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

    async def handle_client(self, websocket) -> None:
        client = self._ir_client_factory()
        client.startup()
        subscriptions: set[str] = set()
        logger.info("WebSocket client connected")
        try:
            await asyncio.gather(
                self._read_commands(websocket, client, subscriptions),
                self._telemetry_loop(websocket, client, subscriptions),
            )
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket client disconnected")
        finally:
            client.shutdown()

    async def _read_commands(self, websocket, client, subscriptions: set[str]) -> None:
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
            elif command == "ping":
                await websocket.send(json.dumps({"type": "pong"}))

    async def _telemetry_loop(self, websocket, client, subscriptions: set[str]) -> None:
        was_connected = False

        while True:
            now_connected = client.is_connected

            if not now_connected:
                if was_connected:
                    was_connected = False
                    await websocket.send(json.dumps({"type": "disconnected"}))
                    logger.info("iRacing disconnected")
                else:
                    client.startup()  # silent reconnect attempt
                await asyncio.sleep(self.update_interval)
                continue

            was_connected = True

            if not subscriptions:
                await asyncio.sleep(self.update_interval)
                continue

            current_subs = frozenset(subscriptions)
            telemetry = client.get_telemetry(current_subs)
            await websocket.send(json.dumps({"type": "telemetry", "data": telemetry}))
            await asyncio.sleep(self.update_interval)

    async def _handle_session_info(self, websocket, client) -> None:
        data = client.get_session_info()
        await websocket.send(json.dumps({"type": "sessionInfo", "data": data}))

    async def _handle_read(self, websocket, client, var_str: str) -> None:
        if not var_str:
            return
        if var_str == "all":
            var_names = frozenset(TELEMETRY_VAR_NAMES)
        else:
            var_names = frozenset(v.strip() for v in var_str.split(",") if v.strip())
        if not var_names:
            return
        data = client.get_telemetry(var_names)
        await websocket.send(json.dumps({"type": "read", "data": data}))

    def _handle_subscribe(self, var_str: str, subscriptions: set[str]) -> None:
        if var_str == "all":
            subscriptions.update(TELEMETRY_VAR_NAMES)
            logger.debug("Subscribed to all vars")
        elif var_str:
            var_list = var_str.split(",")
            for var in var_list:
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
            var_list = var_str.split(",")
            for var in var_list:
                var = var.strip()
                if var not in TELEMETRY_VAR_SET:
                    logger.debug("Specified var not valid: %s", var)
                    continue
                subscriptions.discard(var)
                logger.debug("Unsubscribed from: %s", var)

    async def start(self) -> None:
        logger.info("Starting telemetry server on ws://%s:%d", self.host, self.port)
        advertiser = MDNSAdvertiser(port=self.port) if self.advertise_mdns else None
        if advertiser:
            await advertiser.start()
        try:
            async with websockets.serve(self.handle_client, self.host, self.port):
                await asyncio.Future()
        finally:
            if advertiser:
                await advertiser.stop()
