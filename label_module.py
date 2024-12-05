from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class DataTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Data Type")
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Choose a data type:")
        self.layout.addWidget(self.label)
        self.data_type_combo = QComboBox(self)
        self.data_types = {
            "Timestamp (s)": 0,
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
            "Front Brake Pressure (BAR)": 0,
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
        self.data_type_combo.addItems(self.data_types.keys())
        self.layout.addWidget(self.data_type_combo)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

    def return_selected(self):
        selected_text = self.data_type_combo.currentText()
        return selected_text, self.data_types[selected_text]


class LabelModule(QWidget):
    def __init__(self, serialhandler, data_type):
        super().__init__()
        self.setGeometry(200, 100, 400, 100)
        self.serialhandler = serialhandler
        self.data_type = data_type
        self.layout = QVBoxLayout(self)
        self.label = QLabel()
        self.label.setStyleSheet("""font-size: 28px;""")
        self.layout.addWidget(self.label)
        self.serialhandler.data_changed.connect(self.update_label)

    @pyqtSlot(dict)
    def update_label(self, new_data):
        data = f"{new_data[self.data_type][-1]:.2f}"
        self.label.setText(f"{self.data_type}: {data}")