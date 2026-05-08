from dataclasses import dataclass


@dataclass(frozen=True)
class SessionInfoVar:
    name: str
    description: str


SESSION_INFO_VARS: list[SessionInfoVar] = [
    SessionInfoVar("WeekendInfo",        "General weekend/event details (track, series, rules, weather config)"),
    SessionInfoVar("SessionInfo",        "Per-session descriptors (session type, laps, time limits, results so far)"),
    SessionInfoVar("DriverInfo",         "Full driver roster including car number, iRating, licence, and pit-crew info"),
    SessionInfoVar("QualifyResultsInfo", "Qualifying result order and lap times (populated after qual session)"),
    SessionInfoVar("CameraInfo",         "Available camera groups and their individual cameras"),
    SessionInfoVar("RadioInfo",          "Radio frequencies and transmitter/scanner assignments for each car"),
    SessionInfoVar("SplitTimeInfo",      "Sector split-time definitions (sector index, lap distance percentage)"),
]

SESSION_INFO_VAR_NAMES: tuple[str, ...] = tuple(v.name for v in SESSION_INFO_VARS)
SESSION_INFO_VAR_SET: frozenset[str] = frozenset(SESSION_INFO_VAR_NAMES)
SESSION_INFO_VAR_MAP: dict[str, SessionInfoVar] = {v.name: v for v in SESSION_INFO_VARS}
