import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal
import serial
import time
import random
from collections import deque
import polars as pl
from serial import SerialException
import sqlite3
import binascii

class SerialHandler(QObject):
    data_changed = pyqtSignal(dict)
    def __init__(self, serial_port: str, baudrate: int, samplerate: int, buffertime: float):
        super().__init__()
        self.serial_port : str = serial_port #if windows should be a COM and then a number, usually COM3 or COM4, if linux/mac use '/dev/ttyUSB0' or such
        self.baudrate : int = baudrate
        if not self.serial_port == "null":
            self.serial : serial.Serial = serial.Serial(self.serial_port, self.baudrate)
            time.sleep(1)
            if not (self.serial.in_waiting > 0):
                raise SerialException("Serial port transmits no data")
                print("here")
        self.is_reading : bool = True ## very important for killing thread when we want to
        self.sample_rate : int = samplerate ## Hz
        self.buffer_time : float = buffertime ## seconds
        self.last_read_time : float = time.time() ## used for measure buffer
        self.start_time = time.time()
        self.last_time = self.start_time
        self.data_queue : dict[str, deque[float]] = {}
        self.window_size = 20
        self.hertz_rates = [] 
        self.hertz_rate_sum = 0  
        self.data : dict[str, list[float]] = {
            "Timestamp (ms)": [],
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
            "Differential Speed (RPM)": [],
            "DRS Toggle": [],
            "Steering Angle (deg)": [],
            "Throttle Input": [],
            "Front Brake Pressure (BAR)" : [],
            "Rear Brake Pressure (BAR)": [],
            "GPS Latitude (DD)": [],
            "GPS Longitude (DD)": [],
            "Battery Voltage (mV)": [],
            "Current Draw (mA)": [],
            "Front Right Shock Pot (mm)": [],
            "Front Left Shock Pot (mm)": [],
            "Back Right Shock Pot (mm)": [],
            "Back Left Shock Pot (mm)": [],
            "Lap Counter": [],
            "Refresh Rate": []
        }
        self.temp_data : dict[str, float]= {
            "Timestamp (ms)": 0,
            "X Acceleration (mG)": 0,
            "Y Acceleration (mG)": 0,
            "Z Acceleration (mG)": 0,
            "X Gyro (mdps)": 0,
            "Y Gyro (mdps)": 0,
            "Z Gyro (mdps)": 0,
            "Front Left Speed (mph)": 0,
            "Front Left Brake Temp (C)": 0,
            "Front Left Ambient Temperature (C)": 0,
            "Front Right Speed (mph)": 0,
            "Front Right Brake Temp (C)": 0,
            "Front Right Ambient Temperature (C)": 0,
            "Back Left Speed (mph)": 0,
            "Back Left Brake Temp (C)": 0,
            "Back Left Ambient Temperature (C)": 0,
            "Back Right Speed (mph)": 0,
            "Back Right Brake Temp (C)": 0,
            "Back Right Ambient Temperature (C)": 0,
            "Differential Speed (RPM)": 0,
            "DRS Toggle": 0,
            "Steering Angle (deg)": 0,
            "Throttle Input": 0,
            "Front Brake Pressure (BAR)" : 0,
            "Rear Brake Pressure (BAR)": 0,
            "GPS Latitude (DD)": 0,
            "GPS Longitude (DD)": 0,
            "Battery Voltage (mV)": 0,
            "Current Draw (mA)": 0,
            "Front Right Shock Pot (mm)": 0,
            "Front Left Shock Pot (mm)": 0,
            "Back Right Shock Pot (mm)": 0,
            "Back Left Shock Pot (mm)": 0,
            "Lap Counter": 0,
            "Refresh Rate": 0
            }
        #self.data = pl.DataFrame({col: pl.Series([], pl.Int64) for col in self.columns})
        
        for column_name in self.data.keys():
            self.data_queue[column_name] = deque(maxlen=1000)
    
    def set_sample_rate(self, rate):
        self.sample_rate = rate

    def set_buffer_time(self, time):
        self.buffer_time = time
    
    def getData(self, column_name):
        return self.data[column_name]

    def update_data(self, temp_data : dict[str, float], last_read_time : float) -> None:
        #Serves two purposes, add temp_data to data repository (self.data) and emit the newly acquired data which will call update_graph in graph_module
        for column_name, values in temp_data.items():
            if column_name in self.data:
                #print(values)
                self.data_queue[column_name].append(values)
                self.data[column_name].append(values)
            else:
                print("Invalid column name:", column_name)
        #print("current time: ", time.time())
        if (time.time() - self.last_read_time >= self.buffer_time):
            self.data_changed.emit(self.data_queue)
            #print(self.data_queue)
            self.last_read_time = time.time()
            #print("data changed emitted")

    def _read_data(self) -> None: 
        mode = None
        hertz_count = 0
        hertz_rate_sum = 0
        hertz_rolling_average = 0
        if self.serial_port == "null":
            #print("Testing handler is reading")
            while self.is_reading:
                self.clear_temp_data()
                self.temp_data["Timestamp (ms)"] = time.time() - self.start_time
                self.temp_data["X Acceleration (mG)"] = random.random()
                self.temp_data["Y Acceleration (mG)"]= random.random() 
                self.temp_data["Z Acceleration (mG)"]= random.random()    
                self.temp_data["X Gyro (mdps)"]= random.random()
                self.temp_data["Y Gyro (mdps)"]= random.random()  
                self.temp_data["Z Gyro (mdps)"]= random.random()  
                self.temp_data["Front Left Speed (mph)"]= random.random() 
                self.temp_data["Front Left Brake Temp (C)"] = random.random()  
                self.temp_data["Front Left Ambient Temperature (C)"]= random.random()
                self.temp_data["Front Right Speed (mph)"]= random.random()
                self.temp_data["Front Right Brake Temp (C)"]= random.random()
                self.temp_data["Front Right Ambient Temperature (C)"]= random.random() 
                self.temp_data["Back Left Speed (mph)"]= random.random()
                self.temp_data["Back Left Brake Temp (C)"]= random.random() 
                self.temp_data["Back Left Ambient Temperature (C)"]= random.random() 
                self.temp_data["Back Right Speed (mph)"]= random.random() 
                self.temp_data["Back Right Brake Temp (C)"]= random.random()
                self.temp_data["Back Right Ambient Temperature (C)"]= random.random() 
                self.temp_data["Differential Speed (RPM)"] = random.random()
                self.temp_data["DRS Toggle"] = random.random()
                self.temp_data["Steering Angle (deg)"] = random.random()
                self.temp_data["Throttle Input"] = random.random()
                self.temp_data["Front Brake Pressure (BAR)"] = random.random()
                self.temp_data["Rear Brake Pressure (BAR)"] = random.random()
                self.temp_data["GPS Latitude (DD)"] = random.random()
                self.temp_data["GPS Longitude (DD)"] = random.random()
                self.temp_data["Battery Voltage (mV)"] = random.random()
                self.temp_data["Current Draw (mA)"] = random.random()
                self.temp_data["Front Right Shock Pot (mm)"] = (random.random() - .5) * 2
                self.temp_data["Front Left Shock Pot (mm)"] =(random.random() - .5) * 2
                self.temp_data["Back Right Shock Pot (mm)"] = (random.random() - .5) * 2
                self.temp_data["Back Left Shock Pot (mm)"] = (random.random() - .5) * 2
                self.temp_data["Lap Counter"] = random.random()  
                time.sleep(.1) ## Controls Fake Data Refresh Rate
                current_time = time.time()
                hertz_rate = 1 / (current_time - self.last_time)
                #print(f"Update rate: {hertz_rate:.2f} Hz")
                self.temp_data["Refresh Rate"] = self.update_hertz(hertz_rate)
                self.last_time = current_time
                ### Last things last
                self.update_data(self.temp_data, self.last_read_time)
        else:
            count = 0
            print("Real handler is reading")
            while self.is_reading:
                self.clear_temp_data()
                try:
                    line = self.serial.readline().decode().strip()
                    print(line)
                    try:
                        mode = int(line[0])
                        data = line.split(',')
                        data = [float(value) for value in data]
                        print(data)
                    except Exception as e:
                        print("Error in decoding : ", str(e))
                    match(mode):
                        case 0:
                            self.temp_data["Timestamp (ms)"] = data[1]
                            self.temp_data["X Acceleration (mG)"] = data[2]
                            self.temp_data["Y Acceleration (mG)"]= data[3] 
                            self.temp_data["Z Acceleration (mG)"]= data[4]    
                            self.temp_data["X Gyro (mdps)"]= data[5]
                            self.temp_data["Y Gyro (mdps)"]= data[6]  
                            self.temp_data["Z Gyro (mdps)"]= data[7]  
                            self.temp_data["Front Left Speed (mph)"]= data[8] 
                            self.temp_data["Front Left Brake Temp (C)"] = data[9]  
                            self.temp_data["Front Left Ambient Temperature (C)"]= data[10]
                            self.temp_data["Front Right Speed (mph)"]= data[11]
                            self.temp_data["Front Right Brake Temp (C)"]= data[12]
                            self.temp_data["Front Right Ambient Temperature (C)"]= data[13] 
                            self.temp_data["Back Left Speed (mph)"]= data[14]
                            self.temp_data["Back Left Brake Temp (C)"]= data[15] 
                            self.temp_data["Back Left Ambient Temperature (C)"]= data[16] 
                            self.temp_data["Back Right Speed (mph)"]= data[17] 
                            self.temp_data["Back Right Brake Temp (C)"]= data[18]
                            self.temp_data["Back Right Ambient Temperature (C)"]= data[19] 
                            self.temp_data["Differential Speed (RPM)"] = data[20]
                            self.temp_data["DRS Toggle"] = data[21]
                            self.temp_data["Steering Angle (deg)"] = data[22]
                            self.temp_data["Throttle Input"] = data[23]
                            self.temp_data["Front Brake Pressure (BAR)"] = data[24]
                            self.temp_data["Rear Brake Pressure (BAR)"] = data[25]
                            self.temp_data["GPS Latitude (DD)"] = data[26]
                            self.temp_data["GPS Longitude (DD)"] = data[27]
                            self.temp_data["Battery Voltage (mV)"] = data[28]
                            self.temp_data["Current Draw (mA)"] = data[29]
                            self.temp_data["Front Right Shock Pot (mm)"] = data[30]
                            self.temp_data["Front Left Shock Pot (mm)"] = data[31]
                            self.temp_data["Back Right Shock Pot (mm)"] = data[32]
                            self.temp_data["Back Left Shock Pot (mm)"] = data[33]
                            #self.temp_data["Lap Counter"] = data[34]
                            #print("no error")
                        case 1:
                            self.temp_data["Timestamp (ms)"] = data[1]
                            self.temp_data["X Acceleration (mG)"] = data[2]
                            self.temp_data["Y Acceleration (mG)"]= data[3] 
                            self.temp_data["Z Acceleration (mG)"]= data[4]    
                            self.temp_data["X Gyro (mdps)"]= data[5]
                            self.temp_data["Y Gyro (mdps)"]= data[6]  
                            self.temp_data["Z Gyro (mdps)"]= data[7]  
                            self.temp_data["Front Left Speed (mph)"]= data[8] 
                            self.temp_data["Front Right Speed (mph)"]= data[9]
                            self.temp_data["Back Left Speed (mph)"]= data[10]
                            self.temp_data["Back Right Speed (mph)"]= data[11]  
                            self.temp_data["Differential Speed (RPM)"] = data[12]
                            self.temp_data["DRS Toggle"] = data[13]
                            self.temp_data["Steering Angle (deg)"] = data[14]
                            self.temp_data["Throttle Input"] = data[15]
                            self.temp_data["Front Brake Pressure (BAR)"] = data[16]
                            self.temp_data["Rear Brake Pressure (BAR)"] = data[17]
                            self.temp_data["GPS Latitude (DD)"] = data[18]
                            self.temp_data["GPS Longitude (DD)"] = data[19]
                            self.temp_data["Front Right Shock Pot (mm)"] = data[20]
                            self.temp_data["Front Left Shock Pot (mm)"] = data[21]
                            self.temp_data["Back Right Shock Pot (mm)"] = data[22]
                            self.temp_data["Back Left Shock Pot (mm)"] = data[23]
                        case 2:
                            self.temp_data["Timestamp (ms)"] = data[1]
                            self.temp_data["X Acceleration (mG)"] = data[2]
                            self.temp_data["Y Acceleration (mG)"]= data[3]  
                            self.temp_data["Front Left Speed (mph)"]= data[4] 
                            self.temp_data["Front Right Shock Pot (mm)"] = data[5]
                            self.temp_data["Front Left Shock Pot (mm)"] = data[6]
                            self.temp_data["Back Right Shock Pot (mm)"] = data[7]
                            self.temp_data["Back Left Shock Pot (mm)"] = data[8]
                        case 3:
                            self.temp_data["Timestamp (ms)"] = data[1]
                            self.temp_data["X Acceleration (mG)"] = data[2]
                            self.temp_data["Y Acceleration (mG)"]= data[3]       
                            self.temp_data["Front Left Speed (mph)"]= data[4] 
                            self.temp_data["Back Left Speed (mph)"]= data[5]
                            self.temp_data["Back Right Speed (mph)"]= data[6]  
                            self.temp_data["Differential Speed (RPM)"] = data[7]
                            self.temp_data["DRS Toggle"] = data[8]
                            self.temp_data["Steering Angle (deg)"] = data[9]
                            self.temp_data["Throttle Input"] = data[10]
                            self.temp_data["Front Brake Pressure (BAR)"] = data[11]
                            self.temp_data["Rear Brake Pressure (BAR)"] = data[12]
                            self.temp_data["Front Right Shock Pot (mm)"] = data[13]
                            self.temp_data["Front Left Shock Pot (mm)"] = data[14]
                            self.temp_data["Back Right Shock Pot (mm)"] = data[15]
                            self.temp_data["Back Left Shock Pot (mm)"] = data[16]
                        case 4:
                            self.temp_data["Timestamp (ms)"] = data[1]
                            self.temp_data["X Acceleration (mG)"] = data[2]
                            self.temp_data["Y Acceleration (mG)"]= data[3] 
                            self.temp_data["Front Left Speed (mph)"]= data[4] 
                            self.temp_data["Front Right Speed (mph)"]= data[5]
                            self.temp_data["Back Left Speed (mph)"]= data[6]
                            self.temp_data["Back Right Speed (mph)"]= data[7] 
                            self.temp_data["Differential Speed (RPM)"] = data[8]
                            self.temp_data["Steering Angle (deg)"] = data[9]
                            self.temp_data["Throttle Input"] = data[10]
                            self.temp_data["Front Brake Pressure (BAR)"] = data[11]
                            self.temp_data["Rear Brake Pressure (BAR)"] = data[12]
                        case _:
                            print("SERIALHANDLER IS FAILING ON ALL PROPORTIONS")
                    current_time = time.time()
                    hertz_rate = 1 / (current_time - self.last_time)
                    #print(f"Update rate: {hertz_rate:.2f} Hz")
                    if hertz_rate < 50:
                        hertz_count += 1
                        hertz_rate_sum += hertz_rate
                        #hertz_rolling_average = hertz_rate_sum / hertz_count
                    self.temp_data["Refresh Rate"] = self.update_hertz(hertz_rate)
                    self.last_time = current_time
                    ### Last Things last
                    self.update_data(self.temp_data, self.last_read_time)
                except Exception as e:
                    print("Error in reading line from serial: ", str(e))

    def update_hertz(self, hertz_rate):
        if hertz_rate < 50:
            self.hertz_rates.append(hertz_rate)
            self.hertz_rate_sum += hertz_rate
            if len(self.hertz_rates) > self.window_size:
                oldest_rate = self.hertz_rates.pop(0)
                self.hertz_rate_sum -= oldest_rate
        
            hertz_rolling_average = self.hertz_rate_sum / len(self.hertz_rates)
            return hertz_rolling_average
        return None

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

    def clear_temp_data(self):
        self.temp_data : dict[str, float]= {
            "Timestamp (ms)": 0,
            "X Acceleration (mG)": 0,
            "Y Acceleration (mG)": 0,
            "Z Acceleration (mG)": 0,
            "X Gyro (mdps)": 0,
            "Y Gyro (mdps)": 0,
            "Z Gyro (mdps)": 0,
            "Front Left Speed (mph)": 0,
            "Front Left Brake Temp (C)": 0,
            "Front Left Ambient Temperature (C)": 0,
            "Front Right Speed (mph)": 0,
            "Front Right Brake Temp (C)": 0,
            "Front Right Ambient Temperature (C)": 0,
            "Back Left Speed (mph)": 0,
            "Back Left Brake Temp (C)": 0,
            "Back Left Ambient Temperature (C)": 0,
            "Back Right Speed (mph)": 0,
            "Back Right Brake Temp (C)": 0,
            "Back Right Ambient Temperature (C)": 0,
            "Differential Speed (RPM)": 0,
            "DRS Toggle": 0,
            "Steering Angle (deg)": 0,
            "Throttle Input": 0,
            "Front Brake Pressure (BAR)" : 0,
            "Rear Brake Pressure (BAR)": 0,
            "GPS Latitude (DD)": 0,
            "GPS Longitude (DD)": 0,
            "Battery Voltage (mV)": 0,
            "Current Draw (mA)": 0,
            "Front Right Shock Pot (mm)": 0,
            "Front Left Shock Pot (mm)": 0,
            "Back Right Shock Pot (mm)": 0,
            "Back Left Shock Pot (mm)": 0,
            "Lap Counter": 0,
            "Refresh Rate": 0
            }

    def clear_data(self):
        self.data : dict[str, list[float]] = {
            "Timestamp (ms)": [],
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
            "Differential Speed (RPM)": [],
            "DRS Toggle": [],
            "Steering Angle (deg)": [],
            "Throttle Input": [],
            "Front Brake Pressure (BAR)" : [],
            "Rear Brake Pressure (BAR)": [],
            "GPS Latitude (DD)": [],
            "GPS Longitude (DD)": [],
            "Battery Voltage (mV)": [],
            "Current Draw (mA)": [],
            "Front Right Shock Pot (mm)": [],
            "Front Left Shock Pot (mm)": [],
            "Back Right Shock Pot (mm)": [],
            "Back Left Shock Pot (mm)": [],
            "Lap Counter": [],
            "Refresh Rate": []
        }
        
    def insert_data_to_db(self, db_name : str):
        connection = sqlite3.connect(db_name)
        cursor = connection.cursor()
        num_rows = len(next(iter(self.data.values()))) 

        for i in range(num_rows):
            row = [self.data[key][i] for key in self.data.keys()]
            cursor.execute('''
                INSERT INTO telemetry_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', row)
        
        connection.commit()
        self.clear_data()
                