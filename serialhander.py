import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal
import serial
import time
import random
from collections import deque
import polars as pl

class SerialHandler(QObject):
    data_changed = pyqtSignal(dict)
    def __init__(self, serial_port, baudrate, samplerate, buffertime):
        super().__init__()
        self.serial_port = serial_port #if windows should be a COM and then a number, usually COM3 or COM4, if linux/mac use '/dev/ttyUSB0' or such
        self.baudrate = baudrate
        if not self.serial_port == "null":
            self.serial = serial.Serial(self.serial_port, self.baudrate)
            time.sleep(.2)
            if not (self.serial.in_waiting > 0):
                raise SerialException("Serial port transmits no data")
                print("here")
        self.is_reading = True ## very important for killing thread when we want to
        self.sample_rate = samplerate ## Hz
        self.buffer_time = buffertime ## seconds
        self.last_read_time = time.time() ## used for measure buffer
        self.data_queue = {}
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
        #self.data = pl.DataFrame({col: pl.Series([], pl.Int64) for col in self.columns})
        
        for column_name in self.data.keys():
            self.data_queue[column_name] = deque(maxlen=100)
    
    def set_sample_rate(self, rate):
        self.sample_rate = rate

    def set_buffer_time(self, time):
        self.buffer_time = time
    
    def getData(self, column_name):
        return self.data[column_name]

    def update_data(self, temp_data, last_read_time):
        #Serves two purposes, add temp_data to data repository (self.data) and emit the newly acquired data which will call update_graph in graph_module
        for column_name, values in temp_data.items():
            if column_name in self.data:
                print(values)
                self.data_queue[column_name].append(values[0])
                '''
                if len(self.data[column_name]) >= 100:
                    self.data[column_name].pop(0)
                
                self.data[column_name].append(values)
                '''
            else:
                print("Invalid column name:", column_name)
        #print("current time: ", time.time())
        if (time.time() - self.last_read_time >= self.buffer_time):
            self.data_changed.emit(self.data_queue)
            self.last_read_time = time.time()
            print("data changed emitted")

    def _read_data(self):
        #Should go for 6 iterations or two full updates / new lines into data
        count = 0
        if self.serial_port == "null":
            print("Testing handler is reading")
            count = 0
            while self.is_reading:
                temp_data = {
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
                "Steering Angle": [],
                "Throttle Input": []}
                temp_data["Timestamp (s)"].append(count)
                count = count+1
                temp_data["X Acceleration (mG)"].append(random.random())
                temp_data["Y Acceleration (mG)"].append(random.random()) 
                temp_data["Z Acceleration (mG)"].append(random.random())    
                temp_data["X Gyro (mdps)"].append(random.random())
                temp_data["Y Gyro (mdps)"].append(random.random())  
                temp_data["Z Gyro (mdps)"].append(random.random())  
                temp_data["Front Left Speed (mph)"].append(random.random()) 
                temp_data["Front Left Brake Temp (C)"].append(random.random())  
                temp_data["Front Left Ambient Temperature (C)"].append(random.random())
                temp_data["Front Right Speed (mph)"].append(random.random())
                temp_data["Front Right Brake Temp (C)"].append(random.random())
                temp_data["Front Right Ambient Temperature (C)"].append(random.random()) 
                temp_data["Back Left Speed (mph)"].append(random.random())
                temp_data["Back Left Brake Temp (C)"].append(random.random()) 
                temp_data["Back Left Ambient Temperature (C)"].append(random.random()) 
                temp_data["Back Right Speed (mph)"].append(random.random()) 
                temp_data["Back Right Brake Temp (C)"].append(random.random())
                temp_data["Back Right Ambient Temperature (C)"].append(random.random()) 
                temp_data["Steering Angle"].append(random.random()) 
                temp_data["Throttle Input"].append(random.random())  
                print("temp_data updated")
                time.sleep(.1)
                self.update_data(temp_data, self.last_read_time)
        else:
            count = 0
            print("Real handler is reading")
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
                    try:
                        temp_data[key.strip()] = float(value.strip())
                    except:
                        pass
                    #self.last_read_time = time.time()
                    self.update_data(temp_data, self.last_read_time)
                    #print("update_data called", " lastreadtime: ", self.last_read_time)

    def emit_data_changed(self):
        print("Emitting data has changed to all instances of graph_module.py with latest data:", self.data)
        self.data_changed.emit(self.data)

    def stop_reading(self):
        print("Serial Reading is Stopping")
        self.is_reading = False
        self.serial.close()

    def clear_input_buffer(self):
        while self.serial.in_waiting > 0:
            self.serial.readline()
        print("Serial Input Buffer Cleared")
                