from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QStatusBar,
    QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSlot, QPointF
import serialhander as SerialHandler



class ReportModule(QMainWindow):
    def __init__(self, serialhander : SerialHandler):
        super().__init__()
        self.setWindowTitle("Report Card")
        self.setGeometry(0, 0, 275, 350)
        self.menubar = self.menuBar()
        self.menubar.setStyleSheet(
            "background-color: #333; color: white; font-size: 14px;"
        )
        self.menubar.setStyleSheet("QMenu::item:selected { background-color: #555; }")
        self.menubar.setStyleSheet("QMenu::item:pressed { background-color: #777; }")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)
        self.container = QVBoxLayout()

        self.serialhandler = serialhander
        self.serialhandler.data_changed.connect(self.update_card)

        self.len_run = QLabel("Length of Run (s): ")
        self.container.addWidget(self.len_run)

        self.peak_accel = QLabel("Peak Accel (mG): ")
        self.container.addWidget(self.peak_accel)
        self.max_accel = 0
        
        self.peak_braking = QLabel("Peak Braking (mG): ")
        self.container.addWidget(self.peak_braking)
        self.max_brake = 0
        
        self.peak_cornering = QLabel("Peak Cornering (mG): ")
        self.container.addWidget(self.peak_cornering)
        self.max_corner = 0
        
        self.max_fl_wheel_rpm = QLabel("Max FL Wheel RPM: ")
        self.container.addWidget(self.max_fl_wheel_rpm)
        self.max_fl_rpm = 0
        
        self.max_fl_rotor_temp = QLabel("Max FL Rotor Temperature (C): ")
        self.container.addWidget(self.max_fl_rotor_temp)
        self.max_fl_temp = 0
        
        self.max_fr_wheel_rpm = QLabel("Max FR Wheel RPM: ")
        self.container.addWidget(self.max_fr_wheel_rpm)
        self.max_fr_rpm = 0
        
        self.max_fr_rotor_temp = QLabel("Max FR Rotor Temperature (C): ")
        self.container.addWidget(self.max_fr_rotor_temp)
        self.max_fr_temp = 0
        
        self.fr_shock_travel = QLabel("FR Shock Travel Range (mm): ")
        self.container.addWidget(self.fr_shock_travel)
        self.fr_travel = 0
        
        self.fl_shock_travel = QLabel("FL Shock Travel Range (mm): ")
        self.container.addWidget(self.fl_shock_travel)
        self.fl_travel = 0
        
        self.rl_shock_travel = QLabel("RL Shock Travel Range (mm): ")
        self.container.addWidget(self.rl_shock_travel)
        self.rl_travel = 0
        
        self.rr_shock_travel = QLabel("RR Shock Travel Range (mm): ")
        self.container.addWidget(self.rr_shock_travel)
        self.rr_travel = 0

        self.layout.addLayout(self.container)

    @pyqtSlot(dict)
    def update_card(self, new_data):
        #print("card new data", new_data)
        self.len_run.setText("Length of Run (s): " + str(new_data["Timestamp (s)"][-1]))
        #print("max accel", self.max_accel)
        self.max_accel = max(self.max_accel, new_data["X Acceleration (mG)"][-1])
        #print("new data [-1]", new_data["X Acceleration (mG)"][-1])
        self.peak_accel.setText("Peak Accel (mG): " + str(self.max_accel)[0:7])

        self.max_brake = max(self.max_brake, new_data["Y Acceleration (mG)"][-1])
        self.peak_braking.setText("Peak Braking (mG): " + str(self.max_brake)[0:7])
        
        self.max_corner = max(self.max_corner, new_data["Z Acceleration (mG)"][-1])
        self.peak_cornering.setText("Peak Cornering (mG): " + str(self.max_corner)[0:7])

        self.max_fl_rpm = max(self.max_fl_rpm, new_data["Front Left Speed (mph)"][-1])
        self.max_fl_wheel_rpm.setText("Max FL Wheel RPM: " + str(self.max_fl_rpm)[0:7])
        #print("max fl temp", self.max_fl_temp)
        #print("fl brake temp", list(new_data["Front Left Brake Temp (C)"])[-1], " ", len(new_data["Front Left Brake Temp (C)"]))
        self.max_fl_temp = max(self.max_fl_temp, new_data["Front Left Brake Temp (C)"][-1])
        self.max_fl_rotor_temp.setText("Max FL Rotor Temperature (C): " + str(self.max_fl_temp)[0:7])

        self.max_fr_rpm = max(self.max_fr_rpm, new_data["Front Right Speed (mph)"][-1])
        self.max_fr_wheel_rpm.setText("Max FR Wheel RPM: " + str(self.max_fr_rpm)[0:7])

        self.max_fr_temp = max(self.max_fr_temp, new_data["Front Right Brake Temp (C)"][-1])
        self.max_fr_rotor_temp.setText("Max FR Rotor Temperature (C): " + str(self.max_fr_temp)[0:7])

        self.fl_travel = max(self.fl_travel, new_data["Front Left Shock Pot (mm)"][-1])
        self.fl_shock_travel.setText("Max FL Shock Pot (mm): " + str(self.fl_travel)[0:7])

        self.fr_travel = max(self.fr_travel, new_data["Front Right Shock Pot (mm)"][-1])
        self.fr_shock_travel.setText("Max FR Shock Pot (mm): " + str(self.fr_travel)[0:7])

        self.rl_travel = max(self.rl_travel, new_data["Rear Left Shock Pot (mm)"][-1])
        self.rl_shock_travel.setText("Max RL Shock Pot (mm): " + str(self.rl_travel)[0:7])

        self.rr_travel = max(self.rr_travel, new_data["Rear Right Shock Pot (mm)"][-1])
        self.rr_shock_travel.setText("Max RR Shock Pot (mm): " + str(self.rr_travel)[0:7])
