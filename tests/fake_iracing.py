"""
Fake iRacing SDK (drop-in replacement for irsdk.IRSDK) for use in tests.
"""

DEFAULT_SESSION_INFO = {
    "WeekendInfo": {
        "TrackName": "sebring international raceway",
        "TrackDisplayName": "Sebring International Raceway",
        "TrackCity": "Sebring",
        "TrackCountry": "USA",
        "TrackLength": "5.95 km",
        "EventType": "Test",
        "Category": "Road",
    },
    "SessionInfo": {
        "Sessions": [
            {
                "SessionNum": 0,
                "SessionType": "Practice",
                "SessionName": "PRACTICE",
                "SessionLaps": "unlimited",
            }
        ]
    },
    "DriverInfo": {
        "DriverCarIdx": 0,
        "DriverUserID": 12345,
        "Drivers": [
            {
                "CarIdx": 0,
                "UserName": "Test Driver",
                "CarScreenName": "Dallara F3",
                "IRating": 1000,
                "CarNumber": "0",
            }
        ],
    },
}

DEFAULT_TELEMETRY = {
    "Speed": 55.5,
    "RPM": 4200.0,
    "Gear": 4,
    "Throttle": 0.72,
    "Brake": 0.0,
    "Clutch": 1.0,
    "Lap": 3,
    "LapCurrentLapTime": 42.1,
    "LapBestLapTime": 89.3,
    "LapLastLapTime": 90.1,
    "FuelLevel": 30.5,
    "FuelUsePerHour": 2.1,
    "OilTemp": 95.0,
    "WaterTemp": 82.0,
    "SteeringWheelAngle": -0.05,
    "VelocityX": 15.4,
    "VelocityY": 0.0,
    "VelocityZ": -0.1,
    "IsOnTrack": True,
    "IsInGarage": False,
    "PlayerCarPosition": 1,
}


class FakeIRSDK:
    """Mimics the public API of irsdk.IRSDK for testing purposes."""

    def __init__(
        self,
        connected: bool = True,
        telemetry_data: dict | None = None,
        session_info_data: dict | None = None,
        fail_startup: bool = False,
    ):
        self._connected = connected
        self._data = {
            **(DEFAULT_TELEMETRY if telemetry_data is None else telemetry_data),
            **(DEFAULT_SESSION_INFO if session_info_data is None else session_info_data),
        }
        self._fail_startup = fail_startup

        self.startup_call_count = 0
        self.shutdown_call_count = 0
        self.freeze_call_count = 0
        self.unfreeze_call_count = 0

    # --- irsdk.IRSDK public API ---

    def startup(self, test_file=None, dump_to=None) -> bool:
        self.startup_call_count += 1
        if self._fail_startup:
            return False
        return self._connected

    def shutdown(self) -> None:
        self.shutdown_call_count += 1
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def __getitem__(self, key: str):
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]

    def freeze_var_buffer_latest(self) -> None:
        self.freeze_call_count += 1

    def unfreeze_var_buffer(self) -> None:
        self.unfreeze_call_count += 1

    # --- Test helpers ---

    def set_connected(self, connected: bool) -> None:
        self._connected = connected

    def set_telemetry(self, key: str, value) -> None:
        self._data[key] = value
