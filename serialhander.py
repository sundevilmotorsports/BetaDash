import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal
import serial
import time
import random
from collections import deque
from serial import SerialException
import sqlite3
import binascii
from utils import Utils

class SerialHandler(QObject):
    data_changed = pyqtSignal(dict)
    timing_data_changed = pyqtSignal(dict)
    def __init__(self, serial_port: str, baudrate: int, samplerate: int, buffertime: float):
        super().__init__()
        self.serial_port : str = serial_port #if windows should be a COM and then a number, usually COM3 or COM4, if linux/mac use '/dev/ttyUSB0' or such
        self.baudrate : int = baudrate
        self.serial = None
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
        self.starting_year = time.localtime().tm_year
        self.starting_month = time.localtime().tm_mon
        self.starting_day = time.localtime().tm_mday
        self.starting_hour = time.localtime().tm_hour
        self.starting_minute = time.localtime().tm_min
        self.starting_sec = time.localtime().tm_sec
        self.starting_millis = 0
        self.last_time = self.start_time
        self.data_queue : dict[str, deque[float]] = {}
        self.timing_data_queue : dict[str, deque[float]] = {}
        self.window_size = 20
        self.hertz_rates = [] 
        self.hertz_rate_sum = 0  
        self.lap_counter = 0
        self.data = {}
        for item in Utils.data_format:
            self.data[item] = []

        self.temp_data = {}
        for item in Utils.data_format:
            self.temp_data[item] = 0
        
        for column_name in self.data.keys():
            self.data_queue[column_name] = deque(maxlen=1000)

        self.timing_data = {}
        for item in Utils.timing_data_format:
            self.timing_data[item] = []

        self.temp_timing_data = {}
        for item in Utils.timing_data_format:
            self.temp_timing_data[item] = []

        for column_name in self.timing_data.keys():
            self.timing_data_queue[column_name] = deque(maxlen=1000)
    
    def set_sample_rate(self, rate):
        self.sample_rate = rate

    def set_buffer_time(self, time):
        self.buffer_time = time

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

    def update_timing_data(self, temp_timing_data : dict[str, float]) -> None:
        #Serves two purposes, add temp_data to data repository (self.data) and emit the newly acquired data which will call update_graph in graph_module
        for column_name, values in temp_timing_data.items():
            if column_name in self.timing_data:
                self.timing_data_queue[column_name].append(values)
                self.timing_data[column_name].append(values)
            else:
                print("Invalid column name:", column_name)

        self.timing_data_changed.emit(self.timing_data_queue)

    def _read_data(self) -> None: 
        mode = None
        hertz_count = 0
        hertz_rate_sum = 0
        hertz_rolling_average = 0
        lap_timer_count = 0
        if self.serial_port == "null":
            while self.is_reading:
                self.clear_temp_data()
                timestamp = time.time() - self.start_time
                self.temp_data["Timestamp (ms)"] = timestamp
                self.temp_data["X Acceleration (mG)"] = (random.random()-0.5)*2
                self.temp_data["Y Acceleration (mG)"]= (random.random()-0.5)*2
                self.temp_data["Z Acceleration (mG)"]= (random.random()-0.5)*2  
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
                self.temp_data["Lap Counter"] = self.lap_counter

                ### Fake Timing Gate
                if random.random() < .02:
                    lap_timer_count = (lap_timer_count + 1) % 5
                    self.temp_timing_data["Gate Number"] = lap_timer_count
                    self.temp_timing_data["Starting Year"] = self.starting_year
                    self.temp_timing_data["Starting Month"] = self.starting_month
                    self.temp_timing_data["Starting Day"] = self.starting_day
                    self.temp_timing_data["Starting Hour"] = self.starting_hour
                    self.temp_timing_data["Starting Minute"] = self.starting_minute
                    self.temp_timing_data["Starting Second"] = self.starting_sec
                    self.temp_timing_data["Starting Millis"] = self.starting_millis
                    self.temp_timing_data["Now Millis"] = timestamp
                    self.temp_timing_data["Now Millis Minus Starting Millis"] = timestamp - self.starting_millis
                    #print(self.temp_timing_data)
                    self.update_timing_data(self.temp_timing_data) 

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
                    #print(line)
                    try:
                        mode = int(line[0])
                        data = line.split(',')
                        data = [float(value) for value in data]
                        print(data)
                    except Exception as e:
                        print("Error in decoding : ", str(e))
                    match(mode):
                        case 0:
                            for index, item in enumerate(Utils.telemetry_format):
                                self.temp_data[item] = data[index]
                            self.temp_data["Lap Counter"] = self.lap_counter
                        case 1:
                            for index, item in enumerate(Utils.timing_data_format):
                                self.temp_timing_data[item] = data[index]
                            self.update_timing_data(self.temp_timing_data)
                        case _:
                            print("SERIALHANDLER IS FAILING ON ALL PROPORTIONS")
                    current_time = time.time()
                    if current_time - self.last_time != 0:
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
        return 0

    def stop_reading(self):
        print("Serial Reading is Stopping")
        self.is_reading = False
        if self.serial:
            self.serial.close()

    def clear_input_buffer(self):
        while self.serial.in_waiting > 0:
            self.serial.readline()
        print("Serial Input Buffer Cleared")

    def clear_temp_data(self):
        del self.temp_data
        self.temp_data = {}
        for item in Utils.data_format:
            self.temp_data[item] = 0

    def clear_data(self):
        del self.data
        self.data = {}
        for item in Utils.data_format:
            self.data[item] = []

    def increment_lap_counter(self):
        self.lap_counter += 1
        return self.lap_counter
        
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