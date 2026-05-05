import argparse
import asyncio
import logging
import platform
import sys

from iracing_client import IRacingClient
from server import TelemetryServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def main():
    parser = argparse.ArgumentParser(description="iRacing WebSocket telemetry server")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run with a mock iRacing backend (no real iRacing required)",
    )
    args = parser.parse_args()

    if not args.test and platform.system() != "Windows":
        print("Error: iRacing only runs on Windows. Use --test to run in test mode.")
        sys.exit(1)

    if args.test:
        from mock_irsdk import MockIRSDK
        ir_client_factory = lambda: IRacingClient(ir_sdk=MockIRSDK())
    else:
        ir_client_factory = None

    server = TelemetryServer(host="0.0.0.0", port=8765, ir_client_factory=ir_client_factory)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Shutting down.")


if __name__ == "__main__":
    main()
