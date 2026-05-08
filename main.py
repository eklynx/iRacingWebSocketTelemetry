import argparse
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
        help="Run in test mode with a mock iRacing backend (no real iRacing required)",
    )
    parser.add_argument(
        "--rate",
        type=int,
        default=60,
        metavar="RATE",
        help="Telemetry update rate in updates per second (default: 60)",
    )
    args = parser.parse_args()

    if not args.test and platform.system() != "Windows":
        print("Error: iRacing only runs on Windows. Use --test to run in test mode.")
        sys.exit(1)

    if args.test:
        from mock.mock_irsdk import MockIRSDK
        ir_client_factory = lambda: IRacingClient(ir_sdk=MockIRSDK())
    else:
        ir_client_factory = None

    server = TelemetryServer(host="0.0.0.0", port=8765, ir_client_factory=ir_client_factory, update_interval=1.0 / args.rate)
    try:
        server.start()
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Shutting down.")


if __name__ == "__main__":
    main()
