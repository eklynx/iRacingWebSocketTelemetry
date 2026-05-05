from dataclasses import dataclass


@dataclass(frozen=True)
class TelemetryVar:
    name: str
    type: str         # "float" | "double" | "int" | "bool" | "bitfield"
    description: str


# ---------------------------------------------------------------------------
# Always-available vars (live and/or disk)
# ---------------------------------------------------------------------------
TELEMETRY_VARS: list[TelemetryVar] = [
    # Environment
    TelemetryVar("AirDensity",                       "float",    "Density of air at start/finish line (kg/m^3)"),
    TelemetryVar("AirPressure",                      "float",    "Pressure of air at start/finish line (Hg)"),
    TelemetryVar("AirTemp",                          "float",    "Temperature of air at start/finish line (C)"),
    TelemetryVar("Alt",                              "float",    "Altitude in meters (m)"),
    TelemetryVar("FogLevel",                         "float",    "Fog level (%)"),
    TelemetryVar("RelativeHumidity",                 "float",    "Relative humidity (%)"),
    TelemetryVar("Skies",                            "int",      "Skies (0=clear 1=partly cloudy 2=mostly cloudy 3=overcast)"),
    TelemetryVar("TrackTemp",                        "float",    "Temperature of track at start/finish line (C)"),
    TelemetryVar("TrackTempCrew",                    "float",    "Temperature of track measured by crew around track (C)"),
    TelemetryVar("WeatherType",                      "int",      "Weather type (0=constant 1=dynamic)"),
    TelemetryVar("WindDir",                          "float",    "Wind direction at start/finish line (rad)"),
    TelemetryVar("WindVel",                          "float",    "Wind velocity at start/finish line (m/s)"),

    # Driver inputs
    TelemetryVar("Brake",                            "float",    "Brake pedal position (0=released 1=max pedal force)"),
    TelemetryVar("BrakeRaw",                         "float",    "Raw brake input (0=released 1=max pedal force)"),
    TelemetryVar("Clutch",                           "float",    "Clutch pedal position (0=disengaged 1=fully engaged)"),
    TelemetryVar("Throttle",                         "float",    "Throttle pedal position (0=off throttle 1=full throttle)"),
    TelemetryVar("ThrottleRaw",                      "float",    "Raw throttle input (0=off throttle 1=full throttle)"),
    TelemetryVar("SteeringWheelAngle",               "float",    "Steering wheel angle (rad)"),
    TelemetryVar("SteeringWheelAngleMax",            "float",    "Steering wheel maximum angle (rad)"),
    TelemetryVar("SteeringWheelPctDamper",           "float",    "Force feedback percent max damping (%)"),
    TelemetryVar("SteeringWheelPctTorque",           "float",    "Force feedback percent max torque on steering shaft unsigned (%)"),
    TelemetryVar("SteeringWheelPctTorqueSign",       "float",    "Force feedback percent max torque on steering shaft signed (%)"),
    TelemetryVar("SteeringWheelPctTorqueSignStops",  "float",    "Force feedback percent max torque on steering shaft signed stops (%)"),
    TelemetryVar("SteeringWheelPeakForceNm",         "float",    "Peak torque mapping to direct input units for FFB (N*m)"),
    TelemetryVar("SteeringWheelTorque",              "float",    "Output torque on steering shaft (N*m)"),

    # Engine / powertrain
    TelemetryVar("RPM",                              "float",    "Engine rpm (revs/min)"),
    TelemetryVar("Gear",                             "int",      "Current gear (-1=reverse 0=neutral 1..n=forward)"),
    TelemetryVar("FuelLevel",                        "float",    "Liters of fuel remaining (l)"),
    TelemetryVar("FuelLevelPct",                     "float",    "Percent fuel remaining (%)"),
    TelemetryVar("FuelPress",                        "float",    "Engine fuel pressure (bar)"),
    TelemetryVar("FuelUsePerHour",                   "float",    "Engine fuel used instantaneous (kg/h)"),
    TelemetryVar("ManifoldPress",                    "float",    "Engine manifold pressure (bar)"),
    TelemetryVar("OilLevel",                         "float",    "Engine oil level (l)"),
    TelemetryVar("OilPress",                         "float",    "Engine oil pressure (bar)"),
    TelemetryVar("OilTemp",                          "float",    "Engine oil temperature (C)"),
    TelemetryVar("ShiftGrindRPM",                    "float",    "RPM of shifter grinding noise (RPM)"),
    TelemetryVar("ShiftIndicatorPct",                "float",    "DEPRECATED: use DriverCarSLBlinkRPM instead (%)"),
    TelemetryVar("ShiftPowerPct",                    "float",    "Friction torque applied to gears when shifting or grinding (%)"),
    TelemetryVar("Voltage",                          "float",    "Engine voltage (V)"),
    TelemetryVar("WaterLevel",                       "float",    "Engine coolant level (l)"),
    TelemetryVar("WaterTemp",                        "float",    "Engine coolant temperature (C)"),
    TelemetryVar("EngineWarnings",                   "bitfield", "Bitfield for warning lights (irsdk_EngineWarnings)"),

    # Vehicle dynamics
    TelemetryVar("Speed",                            "float",    "GPS vehicle speed (m/s)"),
    TelemetryVar("VelocityX",                        "float",    "X (lateral) velocity (m/s)"),
    TelemetryVar("VelocityY",                        "float",    "Y (vertical) velocity (m/s)"),
    TelemetryVar("VelocityZ",                        "float",    "Z (longitudinal) velocity (m/s)"),
    TelemetryVar("LatAccel",                         "float",    "Lateral acceleration including gravity (m/s^2)"),
    TelemetryVar("LongAccel",                        "float",    "Longitudinal acceleration including gravity (m/s^2)"),
    TelemetryVar("VertAccel",                        "float",    "Vertical acceleration including gravity (m/s^2)"),
    TelemetryVar("Pitch",                            "float",    "Pitch orientation (rad)"),
    TelemetryVar("PitchRate",                        "float",    "Pitch rate (rad/s)"),
    TelemetryVar("Roll",                             "float",    "Roll orientation (rad)"),
    TelemetryVar("RollRate",                         "float",    "Roll rate (rad/s)"),
    TelemetryVar("Yaw",                              "float",    "Yaw orientation (rad)"),
    TelemetryVar("YawNorth",                         "float",    "Yaw orientation relative to north (rad)"),
    TelemetryVar("YawRate",                          "float",    "Yaw rate (rad/s)"),
    TelemetryVar("Lat",                              "double",   "Latitude in decimal degrees"),
    TelemetryVar("Lon",                              "double",   "Longitude in decimal degrees"),

    # Lap / timing
    TelemetryVar("Lap",                              "int",      "Lap count"),
    TelemetryVar("LapBestLap",                       "int",      "Players best lap number"),
    TelemetryVar("LapBestLapTime",                   "float",    "Players best lap time (s)"),
    TelemetryVar("LapBestNLapLap",                   "int",      "Player last lap in best N average lap time"),
    TelemetryVar("LapBestNLapTime",                  "float",    "Player best N average lap time (s)"),
    TelemetryVar("LapCurrentLapTime",                "float",    "Estimate of players current lap time as shown in F3 box (s)"),
    TelemetryVar("LapDeltaToBestLap",                "float",    "Delta time for best lap (s)"),
    TelemetryVar("LapDeltaToBestLap_DD",             "float",    "Rate of change of delta time for best lap (s/s)"),
    TelemetryVar("LapDeltaToBestLap_OK",             "bool",     "Delta time for best lap is valid"),
    TelemetryVar("LapDeltaToOptimalLap",             "float",    "Delta time for optimal lap (s)"),
    TelemetryVar("LapDeltaToOptimalLap_DD",          "float",    "Rate of change of delta time for optimal lap (s/s)"),
    TelemetryVar("LapDeltaToOptimalLap_OK",          "bool",     "Delta time for optimal lap is valid"),
    TelemetryVar("LapDeltaToSessionBestLap",         "float",    "Delta time for session best lap (s)"),
    TelemetryVar("LapDeltaToSessionBestLap_DD",      "float",    "Rate of change of delta time for session best lap (s/s)"),
    TelemetryVar("LapDeltaToSessionBestLap_OK",      "bool",     "Delta time for session best lap is valid"),
    TelemetryVar("LapDeltaToSessionLastlLap",        "float",    "Delta time for session last lap (s)"),
    TelemetryVar("LapDeltaToSessionLastlLap_DD",     "float",    "Rate of change of delta time for session last lap (s/s)"),
    TelemetryVar("LapDeltaToSessionLastlLap_OK",     "bool",     "Delta time for session last lap is valid"),
    TelemetryVar("LapDeltaToSessionOptimalLap",      "float",    "Delta time for session optimal lap (s)"),
    TelemetryVar("LapDeltaToSessionOptimalLap_DD",   "float",    "Rate of change of delta time for session optimal lap (s/s)"),
    TelemetryVar("LapDeltaToSessionOptimalLap_OK",   "bool",     "Delta time for session optimal lap is valid"),
    TelemetryVar("LapDist",                          "float",    "Meters traveled from S/F this lap (m)"),
    TelemetryVar("LapDistPct",                       "float",    "Percentage distance around lap (%)"),
    TelemetryVar("LapLasNLapSeq",                    "int",      "Player number of consecutive clean laps completed for N average"),
    TelemetryVar("LapLastLapTime",                   "float",    "Players last lap time (s)"),
    TelemetryVar("LapLastNLapTime",                  "float",    "Player last N average lap time (s)"),

    # Session
    TelemetryVar("SessionFlags",                     "bitfield", "Session flags (irsdk_Flags)"),
    TelemetryVar("SessionLapsRemain",                "int",      "Laps left until session ends"),
    TelemetryVar("SessionNum",                       "int",      "Session number"),
    TelemetryVar("SessionState",                     "int",      "Session state (irsdk_SessionState)"),
    TelemetryVar("SessionTime",                      "double",   "Seconds since session start (s)"),
    TelemetryVar("SessionTimeRemain",                "double",   "Seconds left until session ends (s)"),
    TelemetryVar("SessionUniqueID",                  "int",      "Session ID"),
    TelemetryVar("RaceLaps",                         "int",      "Laps completed in race"),

    # Car / player status
    TelemetryVar("IsOnTrack",                        "bool",     "1=Car on track physics running with player in car"),
    TelemetryVar("IsOnTrackCar",                     "bool",     "1=Car on track physics running"),
    TelemetryVar("IsInGarage",                       "bool",     "1=Car in garage physics running"),
    TelemetryVar("OnPitRoad",                        "bool",     "1=Player car is on pit road between the cones"),
    TelemetryVar("PlayerCarClassPosition",           "int",      "Players class position in race"),
    TelemetryVar("PlayerCarPosition",                "int",      "Players position in race"),
    TelemetryVar("EnterExitReset",                   "int",      "Action the reset key will take (0=enter 1=exit 2=reset)"),
    TelemetryVar("DriverMarker",                     "bool",     "Driver activated flag"),

    # Pit service
    TelemetryVar("PitOptRepairLeft",                 "float",    "Time left for optional repairs if repairs are active (s)"),
    TelemetryVar("PitRepairLeft",                    "float",    "Time left for mandatory pit repairs if repairs are active (s)"),
    TelemetryVar("PitSvFlags",                       "bitfield", "Bitfield of pit service checkboxes (irsdk_PitSvFlags)"),
    TelemetryVar("PitSvFuel",                        "float",    "Pit service fuel add amount (l)"),
    TelemetryVar("PitSvLFP",                         "float",    "Pit service left front tire pressure (kPa)"),
    TelemetryVar("PitSvLRP",                         "float",    "Pit service left rear tire pressure (kPa)"),
    TelemetryVar("PitSvRFP",                         "float",    "Pit service right front tire pressure (kPa)"),
    TelemetryVar("PitSvRRP",                         "float",    "Pit service right rear tire pressure (kPa)"),

    # Camera / replay
    TelemetryVar("CamCameraNumber",                  "int",      "Active camera number"),
    TelemetryVar("CamCameraState",                   "bitfield", "State of camera system (irsdk_CameraState)"),
    TelemetryVar("CamCarIdx",                        "int",      "Active camera's focus car index"),
    TelemetryVar("CamGroupNumber",                   "int",      "Active camera group number"),
    TelemetryVar("IsReplayPlaying",                  "bool",     "1=replay is playing"),
    TelemetryVar("ReplayFrameNum",                   "int",      "Integer replay frame number (60 per second)"),
    TelemetryVar("ReplayFrameNumEnd",                "int",      "Integer replay frame number from end of tape"),
    TelemetryVar("ReplayPlaySlowMotion",             "bool",     "1=replay is in slow motion"),
    TelemetryVar("ReplayPlaySpeed",                  "int",      "Replay playback speed"),
    TelemetryVar("ReplaySessionNum",                 "int",      "Replay session number"),
    TelemetryVar("ReplaySessionTime",                "double",   "Seconds since replay session start (s)"),

    # Radio / comms
    TelemetryVar("RadioTransmitCarIdx",              "int",      "Car index of the current person speaking on the radio"),
    TelemetryVar("RadioTransmitFrequencyIdx",        "int",      "Frequency index of the current person speaking on the radio"),
    TelemetryVar("RadioTransmitRadioIdx",            "int",      "Radio index of the current person speaking on the radio"),

    # Team / DC
    TelemetryVar("DCDriversSoFar",                   "int",      "Number of team drivers who have run a stint"),
    TelemetryVar("DCLapStatus",                      "int",      "Status of driver change lap requirements"),

    # Performance
    TelemetryVar("CpuUsageBG",                       "float",    "Percent of available time background thread took with 1 sec avg (%)"),
    TelemetryVar("DisplayUnits",                     "int",      "Default units for user interface (0=English 1=metric)"),
    TelemetryVar("FrameRate",                        "float",    "Average frames per second (fps)"),
    TelemetryVar("IsDiskLoggingActive",              "bool",     "1=disk based telemetry file is being written"),
    TelemetryVar("IsDiskLoggingEnabled",             "bool",     "1=disk based telemetry is turned on"),

    # ---------------------------------------------------------------------------
    # Optional vars — only present when the car implements the sensor
    # ---------------------------------------------------------------------------

    # Chassis ride heights / shocks
    TelemetryVar("CFrideHeight",                     "float",    "Centre-front ride height (m)"),
    TelemetryVar("CFshockDefl",                      "float",    "Centre-front shock deflection (m)"),
    TelemetryVar("CFshockVel",                       "float",    "Centre-front shock velocity (m/s)"),
    TelemetryVar("CFSRrideHeight",                   "float",    "Centre-front/side-rear ride height (m)"),
    TelemetryVar("CRrideHeight",                     "float",    "Centre-rear ride height (m)"),
    TelemetryVar("CRshockDefl",                      "float",    "Centre-rear shock deflection (m)"),
    TelemetryVar("CRshockVel",                       "float",    "Centre-rear shock velocity (m/s)"),

    # In-car driver controls (dc*)
    TelemetryVar("dcABS",                            "float",    "In car ABS adjustment"),
    TelemetryVar("dcAntiRollFront",                  "float",    "In car front anti-roll bar adjustment"),
    TelemetryVar("dcAntiRollRear",                   "float",    "In car rear anti-roll bar adjustment"),
    TelemetryVar("dcBoostLevel",                     "float",    "In car boost level adjustment"),
    TelemetryVar("dcBrakeBias",                      "float",    "In car brake bias adjustment"),
    TelemetryVar("dcDiffEntry",                      "float",    "In car differential entry adjustment"),
    TelemetryVar("dcDiffExit",                       "float",    "In car differential exit adjustment"),
    TelemetryVar("dcDiffMiddle",                     "float",    "In car differential middle adjustment"),
    TelemetryVar("dcEngineBraking",                  "float",    "In car engine braking adjustment"),
    TelemetryVar("dcEnginePower",                    "float",    "In car engine power adjustment"),
    TelemetryVar("dcFuelMixture",                    "float",    "In car fuel mixture adjustment"),
    TelemetryVar("dcRevLimiter",                     "float",    "In car rev limiter adjustment"),
    TelemetryVar("dcThrottleShape",                  "float",    "In car throttle shape adjustment"),
    TelemetryVar("dcTractionControl",                "float",    "In car traction control adjustment"),
    TelemetryVar("dcTractionControl2",               "float",    "In car traction control 2 adjustment"),
    TelemetryVar("dcTractionControlToggle",          "bool",     "In car traction control active"),
    TelemetryVar("dcWeightJackerLeft",               "float",    "In car left weight jacker adjustment"),
    TelemetryVar("dcWeightJackerRight",              "float",    "In car right weight jacker adjustment"),
    TelemetryVar("dcWingFront",                      "float",    "In car front wing adjustment"),
    TelemetryVar("dcWingRear",                       "float",    "In car rear wing adjustment"),

    # Pitstop adjustments (dp*)
    TelemetryVar("dpFNOMKnobSetting",                "float",    "Pitstop front flap adjustment"),
    TelemetryVar("dpFUFangleIndex",                  "float",    "Pitstop front upper flap adjustment"),
    TelemetryVar("dpFWingAngle",                     "float",    "Pitstop front wing angle adjustment"),
    TelemetryVar("dpFWingIndex",                     "float",    "Pitstop front wing index adjustment"),
    TelemetryVar("dpLrWedgeAdj",                     "float",    "Pitstop left-rear spring offset adjustment"),
    TelemetryVar("dpPSSetting",                      "float",    "Pitstop power steering adjustment"),
    TelemetryVar("dpQtape",                          "float",    "Pitstop q-tape adjustment"),
    TelemetryVar("dpRBarSetting",                    "float",    "Pitstop rear bar adjustment"),
    TelemetryVar("dpRFTruckarmP1Dz",                 "float",    "Pitstop RF truck-arm P1 Dz adjustment"),
    TelemetryVar("dpRRDamperPerchOffsetm",           "float",    "Pitstop right-rear damper perch offset adjustment"),
    TelemetryVar("dpRrPerchOffsetm",                 "float",    "Pitstop right-rear spring offset adjustment"),
    TelemetryVar("dpRrWedgeAdj",                     "float",    "Pitstop right-rear wedge adjustment"),
    TelemetryVar("dpRWingAngle",                     "float",    "Pitstop rear wing angle adjustment"),
    TelemetryVar("dpRWingIndex",                     "float",    "Pitstop rear wing index adjustment"),
    TelemetryVar("dpRWingSetting",                   "float",    "Pitstop rear wing setting adjustment"),
    TelemetryVar("dpTruckarmP1Dz",                   "float",    "Pitstop truck-arm P1 Dz adjustment"),
    TelemetryVar("dpWedgeAdj",                       "float",    "Pitstop wedge adjustment"),

    # Left-front tyre / wheel
    TelemetryVar("LFbrakeLinePress",                 "float",    "LF brake line pressure (bar)"),
    TelemetryVar("LFcoldPressure",                   "float",    "LF tire cold pressure as set in garage (kPa)"),
    TelemetryVar("LFpressure",                       "float",    "LF tire pressure (kPa)"),
    TelemetryVar("LFrideHeight",                     "float",    "LF ride height (m)"),
    TelemetryVar("LFshockDefl",                      "float",    "LF shock deflection (m)"),
    TelemetryVar("LFshockVel",                       "float",    "LF shock velocity (m/s)"),
    TelemetryVar("LFspeed",                          "float",    "LF wheel speed (m/s)"),
    TelemetryVar("LFtempCL",                         "float",    "LF tire left carcass temperature (C)"),
    TelemetryVar("LFtempCM",                         "float",    "LF tire middle carcass temperature (C)"),
    TelemetryVar("LFtempCR",                         "float",    "LF tire right carcass temperature (C)"),
    TelemetryVar("LFtempL",                          "float",    "LF tire left surface temperature (C)"),
    TelemetryVar("LFtempM",                          "float",    "LF tire middle surface temperature (C)"),
    TelemetryVar("LFtempR",                          "float",    "LF tire right surface temperature (C)"),
    TelemetryVar("LFwearL",                          "float",    "LF tire left percent tread remaining (%)"),
    TelemetryVar("LFwearM",                          "float",    "LF tire middle percent tread remaining (%)"),
    TelemetryVar("LFwearR",                          "float",    "LF tire right percent tread remaining (%)"),

    # Left-rear tyre / wheel
    TelemetryVar("LRbrakeLinePress",                 "float",    "LR brake line pressure (bar)"),
    TelemetryVar("LRcoldPressure",                   "float",    "LR tire cold pressure as set in garage (kPa)"),
    TelemetryVar("LRpressure",                       "float",    "LR tire pressure (kPa)"),
    TelemetryVar("LRrideHeight",                     "float",    "LR ride height (m)"),
    TelemetryVar("LRshockDefl",                      "float",    "LR shock deflection (m)"),
    TelemetryVar("LRshockVel",                       "float",    "LR shock velocity (m/s)"),
    TelemetryVar("LRspeed",                          "float",    "LR wheel speed (m/s)"),
    TelemetryVar("LRtempCL",                         "float",    "LR tire left carcass temperature (C)"),
    TelemetryVar("LRtempCM",                         "float",    "LR tire middle carcass temperature (C)"),
    TelemetryVar("LRtempCR",                         "float",    "LR tire right carcass temperature (C)"),
    TelemetryVar("LRtempL",                          "float",    "LR tire left surface temperature (C)"),
    TelemetryVar("LRtempM",                          "float",    "LR tire middle surface temperature (C)"),
    TelemetryVar("LRtempR",                          "float",    "LR tire right surface temperature (C)"),
    TelemetryVar("LRwearL",                          "float",    "LR tire left percent tread remaining (%)"),
    TelemetryVar("LRwearM",                          "float",    "LR tire middle percent tread remaining (%)"),
    TelemetryVar("LRwearR",                          "float",    "LR tire right percent tread remaining (%)"),

    # Right-front tyre / wheel
    TelemetryVar("RFbrakeLinePress",                 "float",    "RF brake line pressure (bar)"),
    TelemetryVar("RFcoldPressure",                   "float",    "RF tire cold pressure as set in garage (kPa)"),
    TelemetryVar("RFpressure",                       "float",    "RF tire pressure (kPa)"),
    TelemetryVar("RFrideHeight",                     "float",    "RF ride height (m)"),
    TelemetryVar("RFshockDefl",                      "float",    "RF shock deflection (m)"),
    TelemetryVar("RFshockVel",                       "float",    "RF shock velocity (m/s)"),
    TelemetryVar("RFspeed",                          "float",    "RF wheel speed (m/s)"),
    TelemetryVar("RFtempCL",                         "float",    "RF tire left carcass temperature (C)"),
    TelemetryVar("RFtempCM",                         "float",    "RF tire middle carcass temperature (C)"),
    TelemetryVar("RFtempCR",                         "float",    "RF tire right carcass temperature (C)"),
    TelemetryVar("RFtempL",                          "float",    "RF tire left surface temperature (C)"),
    TelemetryVar("RFtempM",                          "float",    "RF tire middle surface temperature (C)"),
    TelemetryVar("RFtempR",                          "float",    "RF tire right surface temperature (C)"),
    TelemetryVar("RFwearL",                          "float",    "RF tire left percent tread remaining (%)"),
    TelemetryVar("RFwearM",                          "float",    "RF tire middle percent tread remaining (%)"),
    TelemetryVar("RFwearR",                          "float",    "RF tire right percent tread remaining (%)"),

    # Right-rear tyre / wheel
    TelemetryVar("RRbrakeLinePress",                 "float",    "RR brake line pressure (bar)"),
    TelemetryVar("RRcoldPressure",                   "float",    "RR tire cold pressure as set in garage (kPa)"),
    TelemetryVar("RRpressure",                       "float",    "RR tire pressure (kPa)"),
    TelemetryVar("RRrideHeight",                     "float",    "RR ride height (m)"),
    TelemetryVar("RRshockDefl",                      "float",    "RR shock deflection (m)"),
    TelemetryVar("RRshockVel",                       "float",    "RR shock velocity (m/s)"),
    TelemetryVar("RRspeed",                          "float",    "RR wheel speed (m/s)"),
    TelemetryVar("RRtempCL",                         "float",    "RR tire left carcass temperature (C)"),
    TelemetryVar("RRtempCM",                         "float",    "RR tire middle carcass temperature (C)"),
    TelemetryVar("RRtempCR",                         "float",    "RR tire right carcass temperature (C)"),
    TelemetryVar("RRtempL",                          "float",    "RR tire left surface temperature (C)"),
    TelemetryVar("RRtempM",                          "float",    "RR tire middle surface temperature (C)"),
    TelemetryVar("RRtempR",                          "float",    "RR tire right surface temperature (C)"),
    TelemetryVar("RRwearL",                          "float",    "RR tire left percent tread remaining (%)"),
    TelemetryVar("RRwearM",                          "float",    "RR tire middle percent tread remaining (%)"),
    TelemetryVar("RRwearR",                          "float",    "RR tire right percent tread remaining (%)"),

    # ---------------------------------------------------------------------------
    # Per-car array vars — indexed by car index (up to 64 entries)
    # ---------------------------------------------------------------------------
    TelemetryVar("CarIdxClassPosition",              "int",      "Cars class position in race by car index"),
    TelemetryVar("CarIdxEstTime",                    "float",    "Estimated time to reach current location on track by car index (s)"),
    TelemetryVar("CarIdxF2Time",                     "float",    "Race time behind leader or fastest lap time otherwise by car index (s)"),
    TelemetryVar("CarIdxGear",                       "int",      "Current gear by car index (-1=reverse 0=neutral 1..n=forward)"),
    TelemetryVar("CarIdxLap",                        "int",      "Lap count by car index"),
    TelemetryVar("CarIdxLapDistPct",                 "float",    "Percentage distance around lap by car index (%)"),
    TelemetryVar("CarIdxOnPitRoad",                  "bool",     "On pit road between the cones by car index"),
    TelemetryVar("CarIdxPosition",                   "int",      "Cars position in race by car index"),
    TelemetryVar("CarIdxRPM",                        "float",    "Engine rpm by car index (revs/min)"),
    TelemetryVar("CarIdxSteer",                      "float",    "Steering wheel angle by car index (rad)"),
    TelemetryVar("CarIdxTrackSurface",               "int",      "Track surface type by car index (irsdk_TrkLoc)"),
]

# Derived conveniences used throughout the codebase.
TELEMETRY_VAR_NAMES: tuple[str, ...] = tuple(v.name for v in TELEMETRY_VARS)
TELEMETRY_VAR_SET: frozenset[str] = frozenset(TELEMETRY_VAR_NAMES)
