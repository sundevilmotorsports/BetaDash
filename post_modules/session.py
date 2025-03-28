import pandas as pd
import pickle
from dataclasses import dataclass
import glob
import threading

@dataclass
class Session:
    name : str
    date : str
    time : str
    driver : str
    car : str
    track : str
    timestamp : str
    lap_counter : str
    data : pd.DataFrame

class SessionManager():
    def __init__(self):
        self.active_sessions : list(Session) = []

        thread = threading.Thread(target=self.load_csvs)
        thread.start()

    def get_metadata(self, session : Session): # Returns string of meta data
        return "Name: " + session.name + ", Date: " + session.date + " , Time: " + session.time + " , Driver: " + session.driver + " , Car: " + session.car + " , Track: " + session.track

    def load_session(self, data_filename : str):
        data_df = pd.read_csv(data_filename)
        data_df = data_df.round(5) # 5 decimal point precision
        metadata = data_filename.replace(".csv", "").split("\\")[-1].split("_")

        timestamp_col = "null"
        lap_col = "null"
        for col in data_df.columns:
            if "time" in col.lower():
                timestamp_col = col
                break

        for col in data_df.columns:
            if "lap" in col.lower():
                lap_col = col
                break

        if len(metadata) != 6:
            session_ = Session(
                name="null",
                date="null",
                time="null",
                driver="null",
                car="null",
                track="null",
                timestamp=timestamp_col,
                lap_counter=lap_col,
                data=data_df
            )
            print("Filename Format is Incorrect, Unable to read Metadata")
        else:
            session_ = Session(
                name=metadata[0],
                date=metadata[1],
                time=metadata[2],
                driver=metadata[3],
                car=metadata[4],
                track=metadata[5],
                timestamp=timestamp_col,
                lap_counter=lap_col,
                data=data_df
            )

        self.active_sessions.append(session_)

    def get_active_sessions(self):
        return self.active_sessions

    def get_filenames(self):
        return [_session.name for _session in self.active_sessions]

    def load_csvs(self):
        csv_files = glob.glob("CSVs/*.csv")
        print("Importing CSVs")
        for file in csv_files:
            self.load_session(file)  # trying to remove csv directory, in case i need later.split("/")[-1]
        print("Done Importing CSVs")