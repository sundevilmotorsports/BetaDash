from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from datetime import date
import pandas as pd
from post_modules.session import Session, SessionManager

# ------------------------------
# Custom class named CSVImport. This opens a new window which features a set of comboboxes and textboxes where the user can predefine
# the metadata that will be associated with the CSV that they are importing.
# ------------------------------

class CSVImport(QDialog):
    def __init__(self, filename: str, session_manager : SessionManager):
        super().__init__()
        self.session_manager = session_manager
        self.df: pd.DataFrame = pd.read_csv(filename)

        columns = list(self.df.columns)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setWindowTitle("Import CSV file")
        self.setWindowIcon(QIcon("resources/90129757.jpg"))

        # session details
        session_details_layout: QVBoxLayout = QVBoxLayout()
        self.edit_name = QLineEdit("File Name/Info")
        self.edit_date = QLineEdit(str(date.today()))
        self.edit_time = QLineEdit(str(date.time()))
        self.edit_driver = QLineEdit("Driver")
        self.edit_car = QLineEdit("Car")
        self.edit_track = QLineEdit("Track Name")
        session_details_layout.addWidget(self.edit_name)
        session_details_layout.addWidget(self.edit_date)
        session_details_layout.addWidget(self.edit_time)
        session_details_layout.addWidget(self.edit_driver)
        session_details_layout.addWidget(self.edit_car)
        session_details_layout.addWidget(self.edit_track)

        # dialog management
        mgmt_layout: QHBoxLayout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.cancel)
        self.btn_import = QPushButton("Import")
        self.btn_import.setDefault(True)
        self.btn_import.clicked.connect(self.accept)
        mgmt_layout.addWidget(self.btn_cancel)
        mgmt_layout.addWidget(self.btn_import)

        # self.layout.addLayout(col_select_layout)
        self.layout.addLayout(session_details_layout)
        self.layout.addLayout(mgmt_layout)

    def cancel(self):
        self.done(0)

    def accept(self):
        timestamp_col = None
        lap_col = None
        for col in data_df.columns:
            if "time" in col.lower():
                timestamp_col = col
                break

        for col in data_df.columns:
            if "lap" in col.lower():
                lap_col = col
                break
        
        if timestamp_col is not None:
            column_to_move = self.df.pop(timestamp_col)
            self.df.insert(0, time_column_name, column_to_move)

        name = self.edit_name.text()
        date = self.edit_date.text()
        time = self.edit_time.text()
        driver = self.edit_driver.text()
        car = self.edit_car.text()
        track = self.edit_track.text()
        new_session = Session(
            name=name,
            date=date,
            time=time,
            driver=driver,
            car=car,
            track=track,
            timestamp=timestamp_col,
            lap_counter=lap_col,
            data=self.df
            )

        self.session_manager.active_sessions.append(new_session)

        self.done(1)
        self.hide()
