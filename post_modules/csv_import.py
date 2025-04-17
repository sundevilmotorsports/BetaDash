from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from datetime import date
import pandas as pd
from post_modules.session import Session, SessionManager
import os
import re
import threading

class CSVImport(QDialog):
    def __init__(self, filename: str, session_manager: SessionManager):
        super().__init__()
        self.session_manager = session_manager
        self.filename = filename
        self.df: pd.DataFrame = pd.read_csv(filename)

        self.setWindowTitle("Import CSV file")
        self.setWindowIcon(QIcon("resources/90129757.jpg"))
        self.layout = QVBoxLayout(self)
        
        # --- Session Details Form ---
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        status, structure = self.parse_filename(self.filename)
        if status:
            name_val, date_val, time_val, driver_val, car_val, track_val = structure
        else:
            name_val, date_val, time_val, driver_val, car_val, track_val = (
                "File Name/Info", "YYYY-MM-DD", "HHMM", "Driver", "Car", "Track Name"
            )

        self.edit_name   = QLineEdit(name_val)
        self.edit_date   = QLineEdit(date_val)
        self.edit_time   = QLineEdit(time_val)
        self.edit_driver = QLineEdit(driver_val)
        self.edit_car    = QLineEdit(car_val)
        self.edit_track  = QLineEdit(track_val)

        form.addRow("Info / Filename:",    self.edit_name)
        form.addRow("Date (YYYY‑MM‑DD):",   self.edit_date)
        form.addRow("Time (HHMM):",        self.edit_time)
        form.addRow("Driver:",             self.edit_driver)
        form.addRow("Racecar:",            self.edit_car)
        form.addRow("Location / Track:",   self.edit_track)

        self.layout.addLayout(form)

        # --- Dialog Buttons ---
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.cancel)
        self.btn_import = QPushButton("Import")
        self.btn_import.setDefault(True)
        self.btn_import.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_import)

        self.layout.addLayout(btn_layout)

    def cancel(self):
        self.done(0)

    def accept(self):
        # find timestamp and lap columns
        timestamp_col = None
        lap_col = None
        for col in self.df.columns:
            if "time" in col.lower():
                timestamp_col = col
                break
        for col in self.df.columns:
            if "lap" in col.lower():
                lap_col = col
                break

        # reorder timestamp to front
        if timestamp_col is not None:
            col_data = self.df.pop(timestamp_col)
            self.df.insert(0, timestamp_col, col_data)

        # gather metadata
        name   = self.edit_name.text().strip()
        date_s = self.edit_date.text().strip()
        time_s = self.edit_time.text().strip()
        driver = self.edit_driver.text().strip()
        car    = self.edit_car.text().strip()
        track  = self.edit_track.text().strip()

        # create new session and append
        new_session = Session(
            name=name,
            date=date_s,
            time=time_s,
            driver=driver,
            car=car,
            track=track,
            timestamp=timestamp_col,
            lap_counter=lap_col,
            data=self.df
        )
        self.session_manager.active_sessions.append(new_session)

        # prepare save path
        csv_dir = os.path.join(os.getcwd(), "CSVs")
        os.makedirs(csv_dir, exist_ok=True)
        base_name = f"{name}_{date_s}_{time_s}_{driver}_{car}_{track}.csv"
        new_path = os.path.join(csv_dir, base_name)

        def save_csv(df, path):
            try:
                df.to_csv(path, index=False)
            except Exception as e:
                print(f"Error saving CSV in background: {e}")

        thread = threading.Thread(target=save_csv, args=(self.df.copy(), new_path), daemon=True)
        thread.start()

        self.done(1)
        self.close()

    def parse_filename(self, fname: str):
        try:
            base = os.path.basename(fname)
            name, ext = os.path.splitext(base)
            if ext.lower() != '.csv':
                return False, []

            parts = name.split('_')
            if len(parts) != 6:
                return False, []

            info, date_str, hour_str, driver, racecar, location = parts
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date_str):
                return False, []
            if not re.fullmatch(r'\d{4}', hour_str):
                return False, []

            time_str = hour_str[:2] + hour_str[2:]
            return True, [info, date_str, time_str, driver, racecar, location]

        except Exception:
            return False, []
