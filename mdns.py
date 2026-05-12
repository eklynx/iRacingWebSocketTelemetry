import logging
import socket

from zeroconf import ServiceInfo
from zeroconf.asyncio import AsyncZeroconf

logger = logging.getLogger(__name__)

SERVICE_TYPE = "_iracingws._tcp.local."


def _local_ip() -> str:
    """Best-effort: find the outbound LAN IP rather than 127.0.0.1."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


class MDNSAdvertiser:
    """Registers and withdraws a Bonjour/mDNS service entry for the telemetry server."""

    def __init__(self, port: int, instance_name: str = socket.gethostname().split(".")[0]):
        self.port = port
        self.instance_name = instance_name
        self._zc: AsyncZeroconf | None = None
        self._info: ServiceInfo | None = None

    async def start(self) -> None:
        ip = _local_ip()
        self._info = ServiceInfo(
            SERVICE_TYPE,
            f"{self.instance_name}.{SERVICE_TYPE}",
            addresses=[socket.inet_aton(ip)],
            port=self.port,
            properties={"path": "/", "version": "1"},
        )
        self._zc = AsyncZeroconf()
        await self._zc.async_register_service(self._info)
        logger.info(
            "mDNS: '%s' advertised at ws://%s:%d  (type: %s)",
            self.instance_name,
            ip,
            self.port,
            SERVICE_TYPE,
        )

    async def stop(self) -> None:
        if self._zc is None:
            return
        if self._info is not None:
            await self._zc.async_unregister_service(self._info)
        await self._zc.async_close()
        self._zc = None
        logger.info("mDNS: service unregistered")
