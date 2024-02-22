import pandas as pd

class SerialHandler:
    def __init__(self, serial_port, baudrate):
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.serial = serial.Serial(self.serial_port, self.baudrate)
        self.data = {
            "Acceleration": {"X": [], "Y": [], "Z": []},
            "Angular Rate": {"X": [], "Y": [], "Z": []},
            "Speed": {"FL": [], "FR": [], "BL": [], "BR": []},
            "Brake Temperature": {"FL": [], "FR": [], "BL": [], "BR": []},
            "Ambient Temperature": {"FL": [], "FR": [], "BL": [], "BR": []},
            "Other": {"DRS Open/Close": [], "Steering Angle": [], "Throttle Input": [], "Battery Voltage": [], "DAQ Current Draw": []}
        }
    #main file should call this to retrieve data a it is updated via serial monitor and push that data to all graphs in dash
    def getData(column_name):
        return data[column_name]


    