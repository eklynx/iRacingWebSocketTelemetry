import pytest

from iracing_client import IRacingClient, SESSION_INFO_VARS
from telemetry_vars import TELEMETRY_VARS, TELEMETRY_VAR_NAMES, TelemetryVar
from tests.fake_iracing import FakeIRSDK, DEFAULT_SESSION_INFO


def make_client(connected=True, **kwargs) -> IRacingClient:
    return IRacingClient(ir_sdk=FakeIRSDK(connected=connected, **kwargs))


# --- TelemetryVar struct ---

def test_telemetry_var_has_name():
    v = TelemetryVar(name="Speed", type="float", description="Speed (m/s)")
    assert v.name == "Speed"


def test_telemetry_var_has_type():
    v = TelemetryVar(name="Speed", type="float", description="Speed (m/s)")
    assert v.type == "float"


def test_telemetry_var_has_description():
    v = TelemetryVar(name="Speed", type="float", description="Speed (m/s)")
    assert v.description == "Speed (m/s)"


def test_telemetry_var_is_immutable():
    v = TelemetryVar(name="Speed", type="float", description="Speed (m/s)")
    with pytest.raises((AttributeError, TypeError)):
        v.name = "RPM"  # type: ignore[misc]


def test_telemetry_vars_list_is_non_empty():
    assert len(TELEMETRY_VARS) > 0


def test_every_telemetry_var_entry_is_telemetry_var_instance():
    assert all(isinstance(v, TelemetryVar) for v in TELEMETRY_VARS)


def test_every_telemetry_var_has_non_empty_fields():
    for v in TELEMETRY_VARS:
        assert v.name, f"{v} has empty name"
        assert v.type, f"{v} has empty type"
        assert v.description, f"{v} has empty description"


def test_telemetry_var_types_are_valid():
    valid_types = {"float", "double", "int", "bool", "bitfield"}
    for v in TELEMETRY_VARS:
        assert v.type in valid_types, f"{v.name} has unknown type '{v.type}'"


def test_telemetry_var_names_matches_list():
    assert TELEMETRY_VAR_NAMES == tuple(v.name for v in TELEMETRY_VARS)


def test_telemetry_var_names_are_unique():
    assert len(TELEMETRY_VAR_NAMES) == len(set(TELEMETRY_VAR_NAMES))


# --- startup ---

def test_startup_returns_true_when_iracing_running():
    client = make_client(connected=True)
    assert client.startup() is True


def test_startup_returns_false_when_iracing_not_running():
    client = make_client(connected=False)
    assert client.startup() is False


def test_startup_returns_false_on_sdk_failure():
    client = make_client(fail_startup=True)
    assert client.startup() is False


def test_startup_swallows_exception_from_sdk():
    class BrokenSDK:
        is_connected = False
        def startup(self, **_): raise OSError("no shared memory")
        def shutdown(self): pass
        def __getitem__(self, key): return None

    client = IRacingClient(ir_sdk=BrokenSDK())
    assert client.startup() is False


# --- is_connected ---

def test_is_connected_true_when_sdk_connected():
    assert make_client(connected=True).is_connected is True


def test_is_connected_false_when_sdk_not_connected():
    assert make_client(connected=False).is_connected is False


def test_is_connected_reflects_runtime_state_change():
    fake = FakeIRSDK(connected=True)
    client = IRacingClient(ir_sdk=fake)
    assert client.is_connected is True
    fake.set_connected(False)
    assert client.is_connected is False


# --- shutdown ---

def test_shutdown_delegates_to_sdk():
    fake = FakeIRSDK()
    client = IRacingClient(ir_sdk=fake)
    client.shutdown()
    assert fake.shutdown_call_count == 1


def test_shutdown_is_safe_when_sdk_raises():
    class BrokenShutdownSDK:
        is_connected = True
        def startup(self, **_): return True
        def shutdown(self): raise RuntimeError("already shut down")
        def __getitem__(self, key): return None

    client = IRacingClient(ir_sdk=BrokenShutdownSDK())
    client.shutdown()  # must not propagate


# --- get_telemetry ---

def test_get_telemetry_returns_dict():
    result = make_client().get_telemetry()
    assert isinstance(result, dict)


def test_get_telemetry_contains_known_vars():
    result = make_client().get_telemetry()
    assert "Speed" in result
    assert "RPM" in result
    assert "Gear" in result


def test_get_telemetry_values_match_sdk():
    fake = FakeIRSDK(telemetry_data={"Speed": 123.4, "RPM": 9999.0, "Gear": 6})
    client = IRacingClient(ir_sdk=fake)
    result = client.get_telemetry()
    assert result["Speed"] == pytest.approx(123.4)
    assert result["RPM"] == pytest.approx(9999.0)
    assert result["Gear"] == 6


def test_get_telemetry_skips_missing_vars():
    # FakeIRSDK only has the vars in its data dict; unknown vars raise KeyError.
    fake = FakeIRSDK(telemetry_data={"Speed": 10.0})
    client = IRacingClient(ir_sdk=fake)
    result = client.get_telemetry()
    assert "Speed" in result
    # All other TELEMETRY_VARS not in the data dict should simply be absent.
    for var in TELEMETRY_VAR_NAMES:
        if var != "Speed":
            assert var not in result


def test_get_telemetry_only_reads_requested_vars():
    result = make_client().get_telemetry(var_names=frozenset({"Speed", "RPM"}))
    assert set(result.keys()) == {"Speed", "RPM"}


def test_get_telemetry_with_empty_var_names_returns_empty():
    result = make_client().get_telemetry(var_names=frozenset())
    assert result == {}


def test_get_telemetry_none_var_names_reads_all():
    result = make_client().get_telemetry(var_names=None)
    assert "Speed" in result
    assert "RPM" in result


def test_get_telemetry_calls_freeze_unfreeze():
    fake = FakeIRSDK()
    client = IRacingClient(ir_sdk=fake)
    client.get_telemetry()
    assert fake.freeze_call_count == 1
    assert fake.unfreeze_call_count == 1


def test_get_telemetry_unfreeze_called_even_on_error():
    class RaisesOnRead(FakeIRSDK):
        def __getitem__(self, key):
            raise RuntimeError("read error")

    fake = RaisesOnRead()
    client = IRacingClient(ir_sdk=fake)
    result = client.get_telemetry()
    assert fake.unfreeze_call_count == 1
    assert result == {}


# --- get_session_info ---

def test_get_session_info_returns_dict():
    result = make_client().get_session_info()
    assert isinstance(result, dict)


def test_get_session_info_contains_weekend_info():
    result = make_client().get_session_info()
    assert "WeekendInfo" in result


def test_get_session_info_contains_session_info():
    result = make_client().get_session_info()
    assert "SessionInfo" in result


def test_get_session_info_contains_driver_info():
    result = make_client().get_session_info()
    assert "DriverInfo" in result


def test_get_session_info_values_match_sdk():
    result = make_client().get_session_info()
    assert result["WeekendInfo"]["TrackDisplayName"] == "Sebring International Raceway"
    assert result["DriverInfo"]["Drivers"][0]["UserName"] == "Test Driver"


def test_get_session_info_skips_missing_vars():
    # FakeIRSDK built with empty session_info_data — none of SESSION_INFO_VARS present
    fake = FakeIRSDK(telemetry_data={}, session_info_data={})
    client = IRacingClient(ir_sdk=fake)
    result = client.get_session_info()
    assert result == {}


def test_get_session_info_does_not_use_freeze_unfreeze():
    fake = FakeIRSDK()
    client = IRacingClient(ir_sdk=fake)
    client.get_session_info()
    assert fake.freeze_call_count == 0
    assert fake.unfreeze_call_count == 0
