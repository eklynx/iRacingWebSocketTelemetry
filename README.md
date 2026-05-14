# iRacing WebSocket Telemetry

A WebSocket server that bridges [iRacing](https://www.iracing.com/) live telemetry to any WebSocket client. Clients subscribe to the specific variables they need and receive JSON updates at up to 60 Hz. The server advertises itself via mDNS so clients can find it without hardcoding an IP address.

This project is designed to allow other devices to be able to have live access to telemetry values, such as an iPad or smartphone.

A combination of human and Agentic AI coding was used in the development of this project. A human has reviewed all AI-generated code in the main source code (not in tests as of yet). 

## Features

- **Subscription model** — clients subscribe to individual telemetry variables; only the requested data is sent each tick
- **One-shot reads** — request a snapshot of any variable(s) without subscribing
- **mDNS auto-discovery** — the server registers `_iracingws._tcp.local.` for automatic discovery on the local network
- **Test mode** — allows for development on machines without iRacing installed, including on MacOS or Windows
- **Performance metrics** — metrics accessible over WebSocket connection

## Requirements

| Requirement | Notes                                                     |
|---|-----------------------------------------------------------|
| Python 3.12+ | Uses `match` statements and `frozenset` type hints        |
| [pyirsdk](https://github.com/kutu/pyirsdk) | for live usage, install to connect to iRacing's telemetry |
| websockets | used for websocket server support                         |
| zeroconf | used for mDNS discovery                                   |

Install Python dependencies (excluding pyirsdk):

```bash
pip install -r requirements.txt
```

On the Windows machine running iRacing, also install pyirsdk:

```bash
pip install pyirsdk
```

## Usage

```
python main.py [--test] [--rate RATE] [--port PORT]
```

| Flag | Default | Description                                                 |
|---|---|-------------------------------------------------------------|
| `--test` | off | Run with a mock iRacing backend — no real iRacing required. |
| `--rate RATE` | `60` | Telemetry update rate in updates per second                 |
| `--port PORT` | `8765` | WebSocket server port                                       |

### Examples

```bash
# Normal operation (Windows + iRacing running)
python main.py

# Development / testing mode using mock service
python main.py --test

# Reduce subscription rate to 10 Hz
python main.py --rate 10

# Use a custom port
python main.py --port 9000
```

The server listens on `0.0.0.0:8765` by default and logs connection events to stdout.

## WebSocket Protocol

Connect to `ws://<host>:8765`. All messages are UTF-8 text.

### Client → Server commands

| Command | Syntax | Description                                         |
|---|---|-----------------------------------------------------|
| `status` | `status` | Request current iRacing connection status           |
| `sub` | `sub <var>[,<var>...]` | Subscribe to one or more telemetry variables        |
| `sub all` | `sub all` | Subscribe to every available variable               |
| `unsub` | `unsub <var>[,<var>...]` | Unsubscribe from one or more variables              |
| `unsub all` | `unsub all` | Clear all subscriptions                             |
| `read` | `read <var>[,<var>...]` | One-shot read — response sent once, no subscription |
| `read all` | `read all` | One-shot read of all variables                      |
| `sessioninfo` | `sessioninfo` | Request session/weekend/driver metadata             |
| `metrics` | `metrics` | Request server performance metrics                  |
| `ping` | `ping` | Alive check                                         |

### Server → Client messages

All server messages are JSON objects with a `type` field.

**Connection status:**
```json
{ "type": "status", "connected": true }
```


**Telemetry subscription** (sent every tick including all active subscriptions):
```json
{
  "type": "telemetry",
  "data": {
    "Speed": 42.3,
    "RPM": 7500.0,
    "Gear": 4,
    ...
  }
}
```

** `read` response:**
```json
{ 
  "type": "read",
  "data": { 
    "Throttle": 0.87, 
    "Brake": 0.0, 
    ... 
  }
}
```

**Session info response:**
```json
{
  "type": "sessionInfo",
  "data": {
    "WeekendInfo": {...},
    "DriverInfo": {...}
  }
}
```

**Ping response:**
```json
{ "type": "pong" }
```

**Performance metrics:**
```json
{
  "type": "metrics",
  "data": {
    "loop": {
      "time": { "min_ms": 0.1, "max_ms": 3.2, "mean_ms": 0.4, "p50_ms": 0.3, "p90_ms": 0.8, "p95_ms": 0.9, "samples": 3600 },
      "get_count": 3600,
      "skip_count": 0,
      "get_vs_skip": 1.0,
      "max_get_streak": 3600
    },
    "var_get": {
      "time": { "min_ms": 0.01, "max_ms": 0.5, "mean_ms": 0.05, "p50_ms": 0.04, "p90_ms": 0.1, "p95_ms": 0.12, "samples": 3600 }
    }
  }
}
```

## Telemetry Variables

Over 150 variables are available, grouped by category:

| Category | Example variables |
|---|---|
| Environment | `AirTemp`, `TrackTemp`, `WindVel`, `FogLevel`, `RelativeHumidity` |
| Driver inputs | `Throttle`, `Brake`, `Clutch`, `SteeringWheelAngle`, `Gear` |
| Engine / powertrain | `RPM`, `FuelLevel`, `FuelLevelPct`, `OilTemp`, `WaterTemp`, `Voltage` |
| Vehicle dynamics | `Speed`, `LatAccel`, `LongAccel`, `Yaw`, `Pitch`, `Roll`, `Lat`, `Lon` |
| Lap / timing | `Lap`, `LapCurrentLapTime`, `LapBestLapTime`, `LapDeltaToBestLap`, `LapDistPct` |
| Session | `SessionTime`, `SessionTimeRemain`, `SessionLapsRemain`, `SessionFlags` |
| Car status | `IsOnTrack`, `OnPitRoad`, `IsInGarage`, `PlayerCarPosition` |
| Pit service | `PitRepairLeft`, `PitSvFuel`, `PitSvLFP`, `PitSvRFP` |
| Tyre data (per corner) | `LFpressure`, `RFtempCL`, `RRwearM`, `LRshockVel`, … |
| In-car adjustments | `dcBrakeBias`, `dcTractionControl`, `dcABS`, `dcDiffEntry` |
| Per-car arrays (64 slots) | `CarIdxPosition`, `CarIdxLap`, `CarIdxLapDistPct`, `CarIdxRPM` |
| Camera / replay | `CamCarIdx`, `IsReplayPlaying`, `ReplayPlaySpeed` |
| Performance | `FrameRate`, `CpuUsageBG`, `IsDiskLoggingActive` |

See [`telemetry_vars.py`](telemetry_vars.py) for the full list with types and descriptions.  If the value is not available, it will come back as None

## mDNS Discovery

When the server starts it registers a mDNS service of type `_iracingws._tcp.local.` using the machine's hostname as the instance name. Clients on the same LAN can discover the server without knowing its IP address.

## Metrics
### `telemetry_loop`
| Metric name      | Scope   | Description                                                                                                                                                            |
|------------------|---------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `get_count`      | Session | Server checks to see if it's time to send telemetry once every 10 ms.  This is a count of how many times that loop has determined it's time to send updated telemetry. |
| `skip_count`     | Session | For the same telemetry check, this is how many times it's determined it's not yet time to send.                                                                        |
| `get_vs_skip`    | Session | This is the ration of gets vs skips. This is useful for determining if the rate is exceding the ability to get new values                                              |
| `max_get_streak` | Server  | The highest count of how many gets in a row have happend for a session.  If this starts climing, the telemetry loop is not able to keep up with the requested rate     |
| `time`           | Server  | How long a telemetry update takes in milliseconds.  `samples` is the sample window for percentage metrics.                                                             |

### `var_get`
| Metric name      | Scope   | Description                                                                                                                                                                                   |
|------------------|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `time`           | Server  | How long in milliseconds each individual variable get takes from the iRacing client (both in telemetry updates and individual reads).  `samples` is the sample window for percentage metrics. |


## Test Mode

The command line parameter `--test` injects a `MockIRSDK` instance that generates random but type-correct values for every telemetry variable. This lets you develop and test clients on macOS or Linux without iRacing. TODO: instructions on how to overide the random values given by default.

Mock values respect the `min`/`max` ranges defined in `telemetry_vars.py` where applicable.

## Project Structure

```
main.py                     CLI entry point, argument parsing
server.py                   Async WebSocket server and per-client telemetry loop
iracing_client.py           Thin wrapper around pyirsdk
telemetry_vars.py           Catalogue of all telemetry variable definitions
session_info_vars.py        Session/weekend/driver variable definitions
mdns.py                     mDNS service registration via zeroconf
metrics.py                  Metrics tracking
mock/                       Files related to the mock iRacing client
  mock_irsdk.py             Drop-in irsdk.IRSDK replacement
tests/                      Test suite
  test_server.py            Server integration tests
  test_iracing_client.py    IRacingClient unit tests
  test_mdns.py              mDNS advertiser tests
  fake_iracing.py           Helpers for test fixtures
```

## Running Tests

```bash
pytest
```

Tests use `pytest-asyncio` and do not require iRacing or a Windows host.

__NOTE:__ All tests have so far been developed by Agentic AI, trust at own risk. It will be analyzed/refactored/added to/ improved in future commits.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
