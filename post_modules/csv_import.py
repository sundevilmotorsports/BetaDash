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
    def __init__(self, filename: str):
        super().__init__()

        self.df: pd.DataFrame = pd.read_csv(filename)

        columns = list(self.df.columns)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setWindowTitle("Import CSV file")
        self.setWindowIcon(QIcon("90129757.jpg"))

        # get headers
        col_select_layout: QGridLayout = QGridLayout()
        self.combo_time = QComboBox()
        self.combo_time.addItems(columns)

        #check for laps column
        self.checkbox = QCheckBox("Enable if CSV contains lap counter, then choose appropriate column:", self)
        self.checkbox.stateChanged.connect(self.toggle_combobox_state)
        self.combo_lap = QComboBox()
        self.combo_lap.setEnabled(False)
        self.combo_lap.addItems(columns)

        # session details
        session_details_layout: QVBoxLayout = QVBoxLayout()
        self.edit_name = QLineEdit(
            filename[filename.rfind("/") + 1 : filename.rfind(".")]
        )
        self.edit_date = QLineEdit(str(date.today()))
        self.edit_driver = QLineEdit("Driver")
        self.edit_car = QLineEdit("Car")
        self.edit_track = QLineEdit("Track Name")
        self.timestamp_column = QLineEdit("Time (s)")
        session_details_layout.addWidget(self.edit_name)
        session_details_layout.addWidget(self.edit_date)
        session_details_layout.addWidget(self.edit_driver)
        session_details_layout.addWidget(self.edit_car)
        session_details_layout.addWidget(self.edit_track)
        session_details_layout.addWidget(self.timestamp_column)
        session_details_layout.addWidget(QLabel("Select a column which indicates a timestamp:"))
        session_details_layout.addWidget(self.combo_time)
        #session_details_layout.addWidget(QLabel("Enable if CSV contains lap counter, then choose appropriate column: "))
        session_details_layout.addWidget(self.checkbox)
        session_details_layout.addWidget(self.combo_lap)

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

    def toggle_combobox_state(self):
        if self.checkbox.isChecked():
            self.combo_lap.setEnabled(True)
        else:
            self.combo_lap.setEnabled(False)

    def cancel(self):
        self.done(0)

    def accept(self):
        time_column_name = self.combo_time.currentText()
        column_to_move = self.df.pop(time_column_name)
        self.df.insert(0, time_column_name, column_to_move)

        print(self.df)

        if (self.checkbox.isChecked()):
            lap_column_name = self.combo_lap.currentText()
        else:
            lap_column_name = ''

        name = self.edit_name.text()
        date = self.edit_date.text()
        driver = self.edit_driver.text()
        car = self.edit_car.text()
        track = self.edit_track.text()
        #set_session(df, time, lap, name, date, driver, car, track):
        new_session = set_session(
            self.df,
            time_column_name,
            lap_column_name,
            name,
            date,
            driver,
            car,
            track,
        )
        add_session(new_session)

        self.done(1)
        self.hide()
