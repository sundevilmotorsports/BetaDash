import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal
import serial


class SerialHandler(QObject):
    data_changed = pyqtSignal(dict)
    def __init__(self, serial_port, baudrate):
        super().__init__()
        self.serial_port = serial_port #if windows should be a COM and then a number, usually COM3 or COM4, if linux/mac use '/dev/ttyUSB0' or such
        self.baudrate = baudrate
        self.serial = serial.Serial(self.serial_port, self.baudrate)
        self.is_reading = True ## very important for killing thread when we want to
        self.data = {
            "Timestamp (s)": [],
            "X Acceleration (mG)": [],
            "Y Acceleration (mG)": [],
            "Z Acceleration (mG)": [],
            "X Gyro (mdps)": [],
            "Y Gyro (mdps)": [],
            "Z Gyro (mdps)": [],
            "Front Left Speed (mph)": [],
            "Front Left Brake Temp (C)": [],
            "Front Left Ambient Temperature (C)": [],
            "Front Right Speed (mph)": [],
            "Front Right Brake Temp (C)": [],
            "Front Right Ambient Temperature (C)": [],
            "Back Left Speed (mph)": [],
            "Back Left Brake Temp (C)": [],
            "Back Left Ambient Temperature (C)": [],
            "Back Right Speed (mph)": [],
            "Back Right Brake Temp (C)": [],
            "Back Right Ambient Temperature (C)": [],
            "DRS Toggle": [], 
            "Steering Angle": [], 
            "Throttle Input": [], 
            "Battery Voltage": [], 
            "DAQ Current Draw": []
        }
    
    def getData(self, column_name):
        return self.data[column_name]

    def update_data(self, temp_data):
        #Serves two purposes, add temp_data to data repository (self.data) and emit the newly acquired data which will call update_graph in graph_module
        for column_name, values in temp_data.items():
            if column_name in self.data:
                self.data[column_name].append(values)
            else:
                print("Invalid column name:", column_name)
        
        self.data_changed.emit(temp_data)

    def _read_data(self):
        #Should go for 6 iterations or two full updates / new lines into data
        while self.is_reading:
            temp_data = {}
            line = self.serial.readline().decode().strip()
            #This is formatted that the while 
            if (line == "" or "IMU READ:" in line or "WHEEL READ:" in line or "DATALOGREAD:" in line):
                pass
            else:
                try:
                    key, value = line.split(":")
                except ValueError:
                    print("Error: Line does not contain expected key-value pair:", line)
                    continue  # Skip this line and proceed with the next one

                print("Key: " + key + ", value" + value)
                temp_data[key.strip()] = float(value.strip())
                self.update_data(temp_data)

        #print(self.data)

    def stop_reading(self):
        print("Serial Reading is Stopping")
        self.is_reading = False

    def clear_input_buffer(self):
        while self.serial.in_waiting > 0:
            self.serial.readline()
        print("Serial Input Buffer Cleared")
                


