import random
import string
from session_info_vars import SESSION_INFO_VAR_MAP
from telemetry_vars import TELEMETRY_VAR_MAP


class MockIRSDK:
    """Minimal irsdk.IRSDK stand-in for test mode."""

    def startup(self):
        return True

    def shutdown(self):
        pass

    def freeze_var_buffer_latest(self):
        pass

    def unfreeze_var_buffer_latest(self):
        pass

    @property
    def is_connected(self) -> bool:
        return True

    def __getitem__(self, key):
        telemetry_var = TELEMETRY_VAR_MAP[key]
        if telemetry_var is not None:
            match telemetry_var.type:
                case "bitfield":
                    return random.getrandbits(32)
                case "double"|"float":
                    return random.uniform(telemetry_var.min or 0.0, telemetry_var.max or 100.0)
                case "bool":
                    return random.randint(0, 1) == 1
                case "int":
                    return random.randint(telemetry_var.min or 0, telemetry_var.max or 50)
                case "string":
                    return ''.join(random.choices(string.ascii_letters, k=random.randint(6, 20)))
                case "int[64]":
                    arr = []
                    for i in range(64):
                        arr.append(random.uniform(telemetry_var.min or 0, telemetry_var.max or 50))
                    return arr
                case "float[64]" | "double[64]":
                    arr = []
                    for i in range(64):
                        arr.append(random.uniform(telemetry_var.min or 0.0, telemetry_var.max or 100.0))
                    return arr
                case "bool[64]":
                    arr = []
                    for i in range(64):
                        arr.append(random.randint(0, 1) == 1)
                    return arr
                case _:
                    return None

        session_var = SESSION_INFO_VAR_MAP[key]
        if session_var is not None:
            match session_var.name:
                case "WeekendInfo":
                    pass
                case "SessionInfo":
                    pass
                case "DriverInfo":
                    pass
                case "QualifyResultsInfo":
                    pass
                case "CameraInfo":
                    pass
                case "RadioInfo":
                    pass
                case "SplitTimeInfo":
                    pass
        return None


