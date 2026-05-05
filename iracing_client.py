try:
    import irsdk as _irsdk_module
    _IRSDK_AVAILABLE = True
except ImportError:
    _irsdk_module = None
    _IRSDK_AVAILABLE = False

from telemetry_vars import TELEMETRY_VAR_NAMES  # noqa: E402
from session_info_vars import SESSION_INFO_VAR_NAMES


class IRacingClient:
    def __init__(self, ir_sdk=None):
        if ir_sdk is None:
            if not _IRSDK_AVAILABLE:
                raise RuntimeError(
                    "pyirsdk is not installed. "
                    "Pass an ir_sdk object or install pyirsdk (Windows only)."
                )
            ir_sdk = _irsdk_module.IRSDK()
        self._ir = ir_sdk

    def startup(self) -> bool:
        try:
            result = self._ir.startup()
            return bool(result)
        except Exception:
            return False

    def shutdown(self) -> None:
        try:
            self._ir.shutdown()
        except Exception:
            pass

    @property
    def is_connected(self) -> bool:
        return bool(self._ir.is_connected)

    def get_session_info(self) -> dict:
        data = {}
        for var in SESSION_INFO_VAR_NAMES:
            try:
                val = self._ir[var]
                if val is not None:
                    data[var] = val
            except Exception:
                pass
        return data

    def get_telemetry(self, var_names: frozenset[str] | None = None) -> dict:
        target = var_names if var_names is not None else frozenset(TELEMETRY_VAR_NAMES)
        data = {}
        has_freeze = hasattr(self._ir, "freeze_var_buffer_latest")
        if has_freeze:
            self._ir.freeze_var_buffer_latest()
        try:
            for var in target:
                try:
                    val = self._ir[var]
                    data[var] = _serialize(val)
                except Exception:
                    pass
        finally:
            if has_freeze:
                self._ir.unfreeze_var_buffer_latest()
        return data


def _serialize(val):
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float, str)):
        return val
    try:
        return float(val)
    except (TypeError, ValueError):
        return str(val)
