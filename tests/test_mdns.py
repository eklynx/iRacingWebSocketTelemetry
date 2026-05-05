import asyncio
import socket
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mdns import MDNSAdvertiser, SERVICE_TYPE, _local_ip


# ---------------------------------------------------------------------------
# _local_ip
# ---------------------------------------------------------------------------

def test_local_ip_returns_string():
    ip = _local_ip()
    assert isinstance(ip, str)
    assert len(ip) > 0


def test_local_ip_fallback_on_error():
    with patch("socket.socket") as mock_sock_cls:
        mock_sock_cls.return_value.__enter__ = MagicMock()
        mock_sock_cls.return_value.connect = MagicMock(side_effect=OSError("no network"))
        # Instantiated directly (not as context manager) in _local_ip
        instance = MagicMock()
        instance.connect.side_effect = OSError("no network")
        mock_sock_cls.return_value = instance
        ip = _local_ip()
    assert ip == "127.0.0.1"


# ---------------------------------------------------------------------------
# MDNSAdvertiser
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_zeroconf():
    """Patches AsyncZeroconf so no real mDNS traffic is generated."""
    with patch("mdns.AsyncZeroconf") as cls:
        instance = AsyncMock()
        cls.return_value = instance
        yield instance


async def test_start_registers_service(mock_zeroconf):
    adv = MDNSAdvertiser(port=8765)
    await adv.start()
    mock_zeroconf.async_register_service.assert_awaited_once()


async def test_start_uses_correct_service_type(mock_zeroconf):
    adv = MDNSAdvertiser(port=8765)
    await adv.start()
    info = mock_zeroconf.async_register_service.call_args[0][0]
    assert info.type == SERVICE_TYPE


async def test_start_uses_configured_port(mock_zeroconf):
    adv = MDNSAdvertiser(port=9999)
    await adv.start()
    info = mock_zeroconf.async_register_service.call_args[0][0]
    assert info.port == 9999


async def test_start_instance_name_appears_in_service_name(mock_zeroconf):
    adv = MDNSAdvertiser(port=8765, instance_name="My Telemetry")
    await adv.start()
    info = mock_zeroconf.async_register_service.call_args[0][0]
    assert "My Telemetry" in info.name


async def test_start_encodes_valid_ip_address(mock_zeroconf):
    adv = MDNSAdvertiser(port=8765)
    await adv.start()
    info = mock_zeroconf.async_register_service.call_args[0][0]
    # addresses is a list of packed 4-byte strings; decode back and validate
    assert len(info.addresses) == 1
    ip = socket.inet_ntoa(info.addresses[0])
    parts = ip.split(".")
    assert len(parts) == 4


async def test_stop_unregisters_service(mock_zeroconf):
    adv = MDNSAdvertiser(port=8765)
    await adv.start()
    await adv.stop()
    mock_zeroconf.async_unregister_service.assert_awaited_once()
    mock_zeroconf.async_close.assert_awaited_once()


async def test_stop_before_start_is_safe():
    adv = MDNSAdvertiser(port=8765)
    await adv.stop()  # must not raise


async def test_stop_clears_internal_state(mock_zeroconf):
    adv = MDNSAdvertiser(port=8765)
    await adv.start()
    await adv.stop()
    assert adv._zc is None


# ---------------------------------------------------------------------------
# TelemetryServer integration
# ---------------------------------------------------------------------------

async def test_server_starts_mdns_when_flag_true():
    from iracing_client import IRacingClient
    from server import TelemetryServer
    from tests.fake_iracing import FakeIRSDK

    with patch("server.MDNSAdvertiser") as MockAdv:
        instance = AsyncMock()
        MockAdv.return_value = instance

        server = TelemetryServer(
            ir_client_factory=lambda: IRacingClient(ir_sdk=FakeIRSDK()),
            advertise_mdns=True,
        )
        task = asyncio.create_task(server.start())
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass

        MockAdv.assert_called_once_with(port=server.port)
        instance.start.assert_awaited_once()
        instance.stop.assert_awaited_once()


async def test_server_skips_mdns_when_flag_false():
    from iracing_client import IRacingClient
    from server import TelemetryServer
    from tests.fake_iracing import FakeIRSDK

    with patch("server.MDNSAdvertiser") as MockAdv:
        server = TelemetryServer(
            ir_client_factory=lambda: IRacingClient(ir_sdk=FakeIRSDK()),
            advertise_mdns=False,
        )
        task = asyncio.create_task(server.start())
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass

        MockAdv.assert_not_called()
