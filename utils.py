from dataclasses import dataclass, field
class Utils:
        data_format = [
            "Timestamp (ms)",
            "X Acceleration (mG)",
            "Y Acceleration (mG)",
            "Z Acceleration (mG)",
            "X Gyro (mdps)",
            "Y Gyro (mdps)",
            "Z Gyro (mdps)",
            "Front Left Speed (mph)",
            "Front Left Brake Temp (C)",
            "Front Left Ambient Temperature (C)",
            "Front Right Speed (mph)",
            "Front Right Brake Temp (C)",
            "Front Right Ambient Temperature (C)",
            "Back Left Speed (mph)",
            "Back Left Brake Temp (C)",
            "Back Left Ambient Temperature (C)",
            "Back Right Speed (mph)",
            "Back Right Brake Temp (C)",
            "Back Right Ambient Temperature (C)",
            "Differential Speed (RPM)",
            "DRS Toggle",
            "Steering Angle (deg)",
            "Throttle Input",
            "Front Brake Pressure (BAR)" ,
            "Rear Brake Pressure (BAR)",
            "GPS Latitude (DD)",
            "GPS Longitude (DD)",
            "Battery Voltage (mV)",
            "Current Draw (mA)",
            "Front Right Shock Pot (mm)",
            "Front Left Shock Pot (mm)",
            "Back Right Shock Pot (mm)",
            "Back Left Shock Pot (mm)",
            "Lap Counter",
            "Refresh Rate"
        ]

        telemetry_format = [
            "Mode",
            "Timestamp (ms)",
            "X Acceleration (mG)",
            "Y Acceleration (mG)",
            "Z Acceleration (mG)",
            "X Gyro (mdps)",
            "Y Gyro (mdps)",
            "Z Gyro (mdps)",
            "Front Left Speed (mph)",
            "Front Left Brake Temp (C)",
            "Front Left Ambient Temperature (C)",
            "Front Right Speed (mph)",
            "Front Right Brake Temp (C)",
            "Front Right Ambient Temperature (C)",
            "Back Left Speed (mph)",
            "Back Left Brake Temp (C)",
            "Back Left Ambient Temperature (C)",
            "Back Right Speed (mph)",
            "Back Right Brake Temp (C)",
            "Back Right Ambient Temperature (C)",
            "Differential Speed (RPM)",
            "DRS Toggle",
            "Steering Angle (deg)",
            "Throttle Input",
            "Front Brake Pressure (BAR)" ,
            "Rear Brake Pressure (BAR)",
            "GPS Latitude (DD)",
            "GPS Longitude (DD)",
            "Battery Voltage (mV)",
            "Current Draw (mA)",
            "Front Right Shock Pot (mm)",
            "Front Left Shock Pot (mm)",
            "Back Right Shock Pot (mm)",
            "Back Left Shock Pot (mm)"
        ]

        timing_data_format = [
            "Mode",
            "Gate Number",
            "Starting Year",
            "Starting Month",
            "Starting Day",
            "Starting Hour",
            "Starting Minute",
            "Starting Second",
            "Starting Millis",
            "Now Millis",
            "Now Millis Minus Starting Millis"
        ]

@dataclass
class LapTimer:
    Gate_Number : int
    Starting_Year : int
    Starting_Month : int
    Starting_Day : int
    Starting_Hour : int
    Starting_Minute : int
    Starting_Second : int
    Starting_Millis : int
    Converted_Starting_Time : int
    Now_Millis : int
    Now_Millis_Minus_Starting_Millis : int
    Prev_Now_Millis : int
    Prev_Now_Millis_Minus_Starting_Millis : int

@dataclass
class ModuleInfo:
    moduleType : str
    pos : tuple[int, int]
    size : tuple[int, int]
    info : dict