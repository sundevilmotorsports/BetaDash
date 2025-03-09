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
    def __init__(self):
        self.active_sessions : list(Session) = []

    def get_metadata(self, session : Session): # Returns string of meta data
        return "Date: " + session.date + " , Time: " + session.time + " , Driver: " + session.driver + " , Car: " + session.car + " , Track: " + session.track

    def load_session(self, metadata_filename, data_filename):
        metadata_df = pd.read_csv(metadata_filename)
        data_df = pd.read_csv(data_filename)

        session_ = Session(
            date=metadata_df['date'],
            time=metadata_df['time'],
            driver=metadata_df['driver'],
            car=metadata_df['track'],
            data=data_df.to_dict('dict')
        )

        self.active_sessions.append(session_)

    def get_active_sessions(self):
        return self.active_sessions


       
