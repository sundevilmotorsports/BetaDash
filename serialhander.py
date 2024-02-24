import pandas as pd

import serial


class SerialHandler:
    def __init__(self, serial_port, baudrate):
        self.serial_port = serial_port #if windows should be a COM and then a number, usually COM3 or COM4, if linux/mac use '/dev/ttyUSB0' or such
        self.baudrate = baudrate
        self.serial = serial.Serial(self.serial_port, self.baudrate)
        '''
        self.data = {
            "Acceleration": {"X": [], "Y": [], "Z": []},
            "Angular Rate": {"X": [], "Y": [], "Z": []},
            "Speed": {"FL": [], "FR": [], "BL": [], "BR": []},
            "Brake Temperature": {"FL": [], "FR": [], "BL": [], "BR": []},
            "Ambient Temperature": {"FL": [], "FR": [], "BL": [], "BR": []},
            "Other": {"DRS Open/Close": [], "Steering Angle": [], "Throttle Input": [], "Battery Voltage": [], "DAQ Current Draw": []}
        }
        '''
        data = {
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
    #main file should call this to retrieve data a it is updated via serial monitor and push that data to all graphs in dash
    def getData(column_name):
        return data[column_name]

    def update_data(self, column_name, value):
        if column_name in self.data:
            self.data[column_name].append(value)
        else:
            print("Invalid column name.")
    '''
    def start_reading(self):
        self.reading_thread = threading.Thread(target=self._read_data)
        self.reading_thread.start()
    '''
    def _read_data(self):
        temp_data = {}
        #Should go for 6 iterations or two full updates / new lines into data
        for i in range(6):
            while True:
                line = self.serial.readline().decode().strip()
                #This is formatted that the while 
                if (line == "" or line == "IMU READ" or line == "WHEEL READ" or line == "DATALOGREAD"):
                    break
                key, value = line.split(":")
                temp_data[key.strip()] = value.strip()
                self.update_data(temp_data)

    def clear_input_buffer(self):
        while self.serial.in_waiting > 0:
            self.serial.readline()
        print("Serial Input Buffer Cleared")
                


