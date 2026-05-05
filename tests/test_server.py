import asyncio
import json

import pytest
import websockets.exceptions

from iracing_client import IRacingClient
from telemetry_vars import TELEMETRY_VARS, TELEMETRY_VAR_NAMES
from server import TelemetryServer
from tests.fake_iracing import FakeIRSDK


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class MockWebSocket:
    """
    Dual-purpose mock:
      - async-iterable to feed incoming commands to _read_commands
      - send() to capture outgoing messages from _telemetry_loop
    """

    def __init__(self, incoming: list[str] | None = None, close_after: int | None = None):
        self._incoming = list(incoming or [])
        self._read_idx = 0
        self.outgoing: list[dict] = []
        self._close_after = close_after
        self._send_count = 0

    # --- async iterator (commands → server) ---
    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._read_idx < len(self._incoming):
            msg = self._incoming[self._read_idx]
            self._read_idx += 1
            return msg
        raise StopAsyncIteration

    # --- send (server → client) ---
    async def send(self, raw: str) -> None:
        if self._close_after is not None and self._send_count >= self._close_after:
            raise websockets.exceptions.ConnectionClosedOK(None, None)
        self._send_count += 1
        self.outgoing.append(json.loads(raw))

    def message_types(self) -> list[str]:
        return [m["type"] for m in self.outgoing]


def make_server(fake: FakeIRSDK, incoming=None, close_after=None) -> tuple[TelemetryServer, MockWebSocket]:
    ws = MockWebSocket(incoming=incoming, close_after=close_after)
    client = IRacingClient(ir_sdk=fake)
    server = TelemetryServer(
        ir_client_factory=lambda: client,
        update_interval=0.005,
        advertise_mdns=False,
    )
    return server, ws


def bare_server() -> TelemetryServer:
    return TelemetryServer(ir_client_factory=lambda: None, advertise_mdns=False)


async def run_briefly(server, ws, seconds=0.08):
    task = asyncio.create_task(server.handle_client(ws))
    await asyncio.sleep(seconds)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ---------------------------------------------------------------------------
# _subscribe / _unsubscribe — pure unit tests (sync, no I/O)
# ---------------------------------------------------------------------------

def test_subscribe_adds_single_var():
    subs: set[str] = set()
    bare_server()._handle_subscribe("Speed", subs)
    assert subs == {"Speed"}


def test_subscribe_all_adds_every_telemetry_var():
    subs: set[str] = set()
    bare_server()._handle_subscribe("all", subs)
    assert subs == set(TELEMETRY_VAR_NAMES)


def test_subscribe_comma_separated_adds_each_var():
    subs: set[str] = set()
    bare_server()._handle_subscribe("Speed,RPM,Gear", subs)
    assert subs == {"Speed", "RPM", "Gear"}


def test_subscribe_empty_string_does_nothing():
    subs: set[str] = set()
    bare_server()._handle_subscribe("", subs)
    assert subs == set()


def test_subscribe_is_idempotent():
    subs: set[str] = {"Speed"}
    bare_server()._handle_subscribe("Speed", subs)
    assert subs == {"Speed"}


def test_subscribe_all_on_non_empty_set_produces_full_set():
    subs: set[str] = {"Speed"}
    bare_server()._handle_subscribe("all", subs)
    assert subs == set(TELEMETRY_VAR_NAMES)


def test_unsubscribe_removes_single_var():
    subs: set[str] = {"Speed", "RPM"}
    bare_server()._handle_unsubscribe("Speed", subs)
    assert subs == {"RPM"}


def test_unsubscribe_all_clears_everything():
    subs: set[str] = {"Speed", "RPM", "Gear"}
    bare_server()._handle_unsubscribe("all", subs)
    assert subs == set()


def test_unsubscribe_comma_separated_removes_each_var():
    subs: set[str] = {"Speed", "RPM", "Gear"}
    bare_server()._handle_unsubscribe("Speed,RPM", subs)
    assert subs == {"Gear"}


def test_unsubscribe_nonexistent_var_is_safe():
    subs: set[str] = {"Speed"}
    bare_server()._handle_unsubscribe("RPM", subs)
    assert subs == {"Speed"}


def test_unsubscribe_empty_string_does_nothing():
    subs: set[str] = {"Speed"}
    bare_server()._handle_unsubscribe("", subs)
    assert subs == {"Speed"}


def test_unsubscribe_all_on_empty_set_is_safe():
    subs: set[str] = set()
    bare_server()._handle_unsubscribe("all", subs)
    assert subs == set()


def test_unsubscribe_all_then_subscribe_single():
    subs: set[str] = {"Speed", "RPM"}
    server = bare_server()
    server._handle_unsubscribe("all", subs)
    server._handle_subscribe("Gear", subs)
    assert subs == {"Gear"}


# ---------------------------------------------------------------------------
# _read_commands — unit tests (exercised directly, no telemetry loop)
# ---------------------------------------------------------------------------

async def test_sub_adds_single_var():
    ws = MockWebSocket(incoming=["sub Speed"])
    subs: set[str] = set()
    server, _ = make_server(FakeIRSDK())
    await server._read_commands(ws, IRacingClient(ir_sdk=FakeIRSDK()), subs)
    assert "Speed" in subs


async def test_sub_all_adds_every_known_var():
    ws = MockWebSocket(incoming=["sub all"])
    subs: set[str] = set()
    server, _ = make_server(FakeIRSDK())
    await server._read_commands(ws, IRacingClient(ir_sdk=FakeIRSDK()), subs)
    assert subs == set(TELEMETRY_VAR_NAMES)


async def test_sub_multiple_commands():
    ws = MockWebSocket(incoming=["sub Speed", "sub RPM", "sub Gear"])
    subs: set[str] = set()
    server, _ = make_server(FakeIRSDK())
    await server._read_commands(ws, IRacingClient(ir_sdk=FakeIRSDK()), subs)
    assert subs == {"Speed", "RPM", "Gear"}


async def test_unsub_removes_var():
    ws = MockWebSocket(incoming=["sub Speed", "sub RPM", "unsub Speed"])
    subs: set[str] = set()
    server, _ = make_server(FakeIRSDK())
    await server._read_commands(ws, IRacingClient(ir_sdk=FakeIRSDK()), subs)
    assert "Speed" not in subs
    assert "RPM" in subs


async def test_unsub_all_clears_subscriptions():
    ws = MockWebSocket(incoming=["sub all", "unsub all"])
    subs: set[str] = set()
    server, _ = make_server(FakeIRSDK())
    await server._read_commands(ws, IRacingClient(ir_sdk=FakeIRSDK()), subs)
    assert subs == set()


async def test_unsub_nonexistent_var_is_safe():
    ws = MockWebSocket(incoming=["unsub Speed"])
    subs: set[str] = set()
    server, _ = make_server(FakeIRSDK())
    await server._read_commands(ws, IRacingClient(ir_sdk=FakeIRSDK()), subs)  # must not raise
    assert subs == set()


async def test_sub_with_no_varname_ignored():
    ws = MockWebSocket(incoming=["sub"])
    subs: set[str] = set()
    server, _ = make_server(FakeIRSDK())
    await server._read_commands(ws, IRacingClient(ir_sdk=FakeIRSDK()), subs)
    assert subs == set()


async def test_unknown_command_ignored():
    ws = MockWebSocket(incoming=["list", "help Speed", "SUB Speed"])
    subs: set[str] = set()
    server, _ = make_server(FakeIRSDK())
    await server._read_commands(ws, IRacingClient(ir_sdk=FakeIRSDK()), subs)
    # Commands are case-insensitive for sub/unsub; "list"/"help" are unknown
    # "SUB Speed" normalized to lower → treated as sub
    assert "Speed" in subs
    assert len(subs) == 1


async def test_commands_are_case_insensitive():
    ws = MockWebSocket(incoming=["SUB Speed", "UNSUB Speed"])
    subs: set[str] = set()
    server, _ = make_server(FakeIRSDK())
    await server._read_commands(ws, IRacingClient(ir_sdk=FakeIRSDK()), subs)
    assert "Speed" not in subs


# ---------------------------------------------------------------------------
# read command — _handle_read and via _read_commands
# ---------------------------------------------------------------------------

async def test_read_returns_read_type_message():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["read Speed"])
    subs: set[str] = set()
    server, _ = make_server(fake)
    await server._read_commands(ws, client, subs)
    assert any(m["type"] == "read" for m in ws.outgoing)


async def test_read_payload_contains_requested_var():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["read Speed"])
    server, _ = make_server(fake)
    await server._read_commands(ws, client, set())
    read_msgs = [m for m in ws.outgoing if m["type"] == "read"]
    assert "Speed" in read_msgs[0]["data"]


async def test_read_payload_contains_correct_value():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["read Speed"])
    server, _ = make_server(fake)
    await server._read_commands(ws, client, set())
    read_msgs = [m for m in ws.outgoing if m["type"] == "read"]
    assert read_msgs[0]["data"]["Speed"] == pytest.approx(55.5)


async def test_read_comma_separated_returns_all_requested_vars():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["read Speed,RPM,Gear"])
    server, _ = make_server(fake)
    await server._read_commands(ws, client, set())
    read_msgs = [m for m in ws.outgoing if m["type"] == "read"]
    assert set(read_msgs[0]["data"].keys()) == {"Speed", "RPM", "Gear"}


async def test_read_all_returns_all_known_vars():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["read all"])
    server, _ = make_server(fake)
    await server._read_commands(ws, client, set())
    read_msgs = [m for m in ws.outgoing if m["type"] == "read"]
    assert len(read_msgs) == 1
    assert "Speed" in read_msgs[0]["data"]
    assert "RPM" in read_msgs[0]["data"]


async def test_read_with_no_varname_sends_nothing():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["read"])
    server, _ = make_server(fake)
    await server._read_commands(ws, client, set())
    assert not any(m["type"] == "read" for m in ws.outgoing)


async def test_read_does_not_affect_subscriptions():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["read Speed,RPM"])
    subs: set[str] = set()
    server, _ = make_server(fake)
    await server._read_commands(ws, client, subs)
    assert subs == set()


async def test_read_and_sub_are_independent():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["sub Gear", "read Speed,RPM"])
    subs: set[str] = set()
    server, _ = make_server(fake)
    await server._read_commands(ws, client, subs)
    assert subs == {"Gear"}
    read_msgs = [m for m in ws.outgoing if m["type"] == "read"]
    assert set(read_msgs[0]["data"].keys()) == {"Speed", "RPM"}


async def test_read_strips_whitespace_around_var_names():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["read Speed, RPM, Gear"])
    server, _ = make_server(fake)
    await server._read_commands(ws, client, set())
    read_msgs = [m for m in ws.outgoing if m["type"] == "read"]
    assert set(read_msgs[0]["data"].keys()) == {"Speed", "RPM", "Gear"}


# ---------------------------------------------------------------------------
# sessioninfo command
# ---------------------------------------------------------------------------

async def test_sessioninfo_returns_session_info_type():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["sessioninfo"])
    server, _ = make_server(fake)
    await server._read_commands(ws, client, set())
    assert any(m["type"] == "sessionInfo" for m in ws.outgoing)


async def test_sessioninfo_contains_weekend_info():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["sessioninfo"])
    server, _ = make_server(fake)
    await server._read_commands(ws, client, set())
    msg = next(m for m in ws.outgoing if m["type"] == "sessionInfo")
    assert "WeekendInfo" in msg["data"]


async def test_sessioninfo_contains_driver_info():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["sessioninfo"])
    server, _ = make_server(fake)
    await server._read_commands(ws, client, set())
    msg = next(m for m in ws.outgoing if m["type"] == "sessionInfo")
    assert "DriverInfo" in msg["data"]


async def test_sessioninfo_values_are_correct():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["sessioninfo"])
    server, _ = make_server(fake)
    await server._read_commands(ws, client, set())
    msg = next(m for m in ws.outgoing if m["type"] == "sessionInfo")
    assert msg["data"]["WeekendInfo"]["TrackDisplayName"] == "Sebring International Raceway"
    assert msg["data"]["DriverInfo"]["Drivers"][0]["UserName"] == "Test Driver"


async def test_sessioninfo_is_case_insensitive():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["SESSIONINFO"])
    server, _ = make_server(fake)
    await server._read_commands(ws, client, set())
    assert any(m["type"] == "sessionInfo" for m in ws.outgoing)


async def test_sessioninfo_does_not_affect_subscriptions():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["sessioninfo"])
    subs: set[str] = set()
    server, _ = make_server(fake)
    await server._read_commands(ws, client, subs)
    assert subs == set()


async def test_sessioninfo_sends_single_response():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    ws = MockWebSocket(incoming=["sessioninfo"])
    server, _ = make_server(fake)
    await server._read_commands(ws, client, set())
    session_msgs = [m for m in ws.outgoing if m["type"] == "sessionInfo"]
    assert len(session_msgs) == 1


# ---------------------------------------------------------------------------
# _telemetry_loop — unit tests
# ---------------------------------------------------------------------------

async def _run_loop_briefly(server, ws, client, subs, seconds=0.08):
    task = asyncio.create_task(server._telemetry_loop(ws, client, subs))
    await asyncio.sleep(seconds)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def test_no_telemetry_when_no_subscriptions():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    server, ws = make_server(fake)
    await _run_loop_briefly(server, ws, client, set())
    assert "telemetry" not in ws.message_types()


async def test_telemetry_sent_when_subscribed():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    server, ws = make_server(fake)
    await _run_loop_briefly(server, ws, client, {"Speed"})
    assert "telemetry" in ws.message_types()


async def test_telemetry_only_contains_subscribed_vars():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    server, ws = make_server(fake)
    await _run_loop_briefly(server, ws, client, {"Speed", "RPM"})
    telemetry_msgs = [m for m in ws.outgoing if m["type"] == "telemetry"]
    assert len(telemetry_msgs) > 0
    data = telemetry_msgs[0]["data"]
    assert set(data.keys()) == {"Speed", "RPM"}


async def test_telemetry_values_are_correct():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    server, ws = make_server(fake)
    await _run_loop_briefly(server, ws, client, {"Speed"})
    telemetry_msgs = [m for m in ws.outgoing if m["type"] == "telemetry"]
    assert telemetry_msgs[0]["data"]["Speed"] == pytest.approx(55.5)


async def test_disconnected_message_sent_on_iracing_drop():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    server, ws = make_server(fake)

    task = asyncio.create_task(server._telemetry_loop(ws, client, {"Speed"}))
    await asyncio.sleep(0.04)
    fake.set_connected(False)
    await asyncio.sleep(0.02)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert "disconnected" in ws.message_types()


async def test_disconnected_message_sent_exactly_once():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    server, ws = make_server(fake)

    task = asyncio.create_task(server._telemetry_loop(ws, client, {"Speed"}))
    await asyncio.sleep(0.04)
    fake.set_connected(False)
    await asyncio.sleep(0.05)  # several ticks while still disconnected
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert ws.message_types().count("disconnected") == 1


async def test_no_disconnected_message_if_never_connected():
    fake = FakeIRSDK(connected=False)
    client = IRacingClient(ir_sdk=fake)
    server, ws = make_server(fake)
    await _run_loop_briefly(server, ws, client, {"Speed"})
    assert "disconnected" not in ws.message_types()


async def test_no_telemetry_while_disconnected():
    fake = FakeIRSDK(connected=False)
    client = IRacingClient(ir_sdk=fake)
    server, ws = make_server(fake)
    await _run_loop_briefly(server, ws, client, {"Speed"})
    assert "telemetry" not in ws.message_types()


async def test_telemetry_resumes_after_iracing_reconnects():
    fake = FakeIRSDK(connected=False)
    client = IRacingClient(ir_sdk=fake)
    server, ws = make_server(fake)

    task = asyncio.create_task(server._telemetry_loop(ws, client, {"Speed"}))
    await asyncio.sleep(0.03)
    fake.set_connected(True)
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert "telemetry" in ws.message_types()


# ---------------------------------------------------------------------------
# handle_client — integration tests
# ---------------------------------------------------------------------------

async def test_sub_command_causes_telemetry_to_flow():
    fake = FakeIRSDK(connected=True)
    server, ws = make_server(fake, incoming=["sub Speed"], close_after=5)
    await asyncio.wait_for(server.handle_client(ws), timeout=2.0)
    telemetry_msgs = [m for m in ws.outgoing if m["type"] == "telemetry"]
    assert len(telemetry_msgs) > 0
    assert "Speed" in telemetry_msgs[0]["data"]


async def test_sub_all_causes_all_vars_in_telemetry():
    fake = FakeIRSDK(connected=True)
    server, ws = make_server(fake, incoming=["sub all"], close_after=3)
    await asyncio.wait_for(server.handle_client(ws), timeout=2.0)
    telemetry_msgs = [m for m in ws.outgoing if m["type"] == "telemetry"]
    assert len(telemetry_msgs) > 0
    data_keys = set(telemetry_msgs[0]["data"].keys())
    # All TELEMETRY_VARS that exist in FakeIRSDK's default data should appear
    assert "Speed" in data_keys
    assert "RPM" in data_keys


async def test_no_telemetry_without_sub_command():
    fake = FakeIRSDK(connected=True)
    server, ws = make_server(fake, incoming=[])
    await run_briefly(server, ws)
    assert "telemetry" not in ws.message_types()


async def test_shutdown_called_when_websocket_closes():
    fake = FakeIRSDK(connected=True)
    server, ws = make_server(fake, incoming=["sub Speed"], close_after=3)
    await asyncio.wait_for(server.handle_client(ws), timeout=2.0)
    assert fake.shutdown_call_count == 1


async def test_shutdown_called_on_task_cancel():
    fake = FakeIRSDK(connected=True)
    server, ws = make_server(fake)
    await run_briefly(server, ws)
    assert fake.shutdown_call_count == 1


async def test_startup_called_on_client_connect():
    fake = FakeIRSDK(connected=True)
    server, ws = make_server(fake)
    await run_briefly(server, ws)
    assert fake.startup_call_count >= 1
