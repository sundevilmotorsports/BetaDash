import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal
import serial


class SerialHandler(QObject):
    data_changed = pyqtSignal(dict)
    def __init__(self, serial_port, baudrate):
        self.serial_port = serial_port #if windows should be a COM and then a number, usually COM3 or COM4, if linux/mac use '/dev/ttyUSB0' or such
        self.baudrate = baudrate
        self.serial = serial.Serial(self.serial_port, self.baudrate)
        self.data = {
            "Timestamp": [],
            "X Acceleration": [],
            "Y Acceleration": [],
            "Z Acceleration": [],
            "X Gyro": [],
            "Y Gyro": [],
            "Z Gyro": [],
            "Front Left Speed": [],
            "Front Left Brake Temp": [],
            "Front Left Ambient Temperature": [],
            "Front Right Speed": [],
            "Front Right Brake Temp": [],
            "Front Right Ambient Temperature": [],
            "Back Left Speed": [],
            "Back Left Brake Temp": [],
            "Back Left Ambient Temperature": [],
            "Back Right Speed": [],
            "Back Right Brake Temp": [],
            "Back Right Ambient Temperature": [],
            "DRS Toggle": [], 
            "Steering Angle": [], 
            "Throttle Input": [], 
            "Battery Voltage": [], 
            "DAQ Current Draw": []
        }
    
    def getData(self):
        return self.data

    def update_data(self, temp_data):
        for column_name, values in temp_data.items():
            if column_name in self.data:
                self.data[column_name].append(values)
            else:
                print("Invalid column name:", column_name)
        self.data_changed.emit(self.data)

    def _read_data(self):
        temp_data = {}
        #Should go for 6 iterations or two full updates / new lines into data
        for i in range(6):
            while True:
                line = self.serial.readline().decode().strip()
                #This is formatted that the while 
                if (line == "" or "IMU READ:" in line or "WHEEL READ:" in line or "DATALOGREAD:" in line):
                    break
                try:
                    key, value = line.split(":")
                except ValueError:
                    print("Error: Line does not contain expected key-value pair:", line)
                    continue  # Skip this line and proceed with the next one

                print("Key: " + key + ", value" + value)
                temp_data[key.strip()] = float(value.strip())
                self.update_data(temp_data)

        print(self.data)

    def clear_input_buffer(self):
        while self.serial.in_waiting > 0:
            self.serial.readline()
        print("Serial Input Buffer Cleared")
                


