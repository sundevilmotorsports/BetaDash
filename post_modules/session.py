import pandas as pd
import pickle
from dataclasses import dataclass

@dataclass
class Session:
    date : str
    time : str
    driver : str
    car : str
    track : str
    data : pd.DataFrame

class SessionManager():
    pass

# Array that holds different sessions accessible by the day it occurred
active_sessions = []

class Session():
    def __init__(self, data: pd.DataFrame, metadata: pd.DataFrame):
        # Data frame for the raw data from the box
        self.logger_data = data
        # Data frame with the corresponding metadata
        self.logger_metadata = metadata

    def get_dataframe(self):
        return self.logger_data

    def get_metadata(self):
        return self.logger_metadata

    def get_lap_value(self):
        return self.logger_metadata.get('Lap')

    def get_time_value(self):
        return self.logger_metadata.get('Time')

def add_session(new_session):
    active_sessions.append(new_session)
    print("add session new")
    print(new_session.get_metadata()["Name"])

def get_names():
    """Returns an array with the strings of the "Name" column within the Metadata Dataframe for each session in the dashboard"""
    return [session.get_metadata()["Name"] for session in active_sessions]

def get_active_sessions():
    """Getter for the active_sessions array"""
    return active_sessions

def set_session(df, time, lap, name, date, driver, car, track):
    new_metadata = {
        'Date': date,
        'Driver': driver,
        'Car': car,
        'Track': track,
        'Name': name,
        'Time': time,
        'Lap': lap,
    }
    new_session = Session(df, new_metadata)
    with open(f"data/{name}.pkl", "wb") as f:
        pickle.dump(new_session, f)
    return new_session
