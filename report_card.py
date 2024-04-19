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
        
        self.peak_braking = QLabel("Peak Braking (mG): ")
        self.container.addWidget(self.peak_braking)
        
        self.peak_cornering = QLabel("Peak Cornering (mG): ")
        self.container.addWidget(self.peak_cornering)
        
        self.max_fl_wheel_rpm = QLabel("Max FL Wheel RPM: ")
        self.container.addWidget(self.max_fl_wheel_rpm)
        
        self.max_fl_rotor_temp = QLabel("Max FL Rotor Temperature (C): ")
        self.container.addWidget(self.max_fl_rotor_temp)
        
        self.max_fr_wheel_rpm = QLabel("Max FR Wheel RPM: ")
        self.container.addWidget(self.max_fr_wheel_rpm)
        
        self.max_fr_rotor_temp = QLabel("Max FR Rotor Temperature (C): ")
        self.container.addWidget(self.max_fr_rotor_temp)
        
        self.fr_shock_travel = QLabel("FR Shock Travel Range (mm): ")
        self.container.addWidget(self.fr_shock_travel)
        
        self.fl_shock_travel = QLabel("FL Shock Travel Range (mm): ")
        self.container.addWidget(self.fl_shock_travel)
        
        self.rl_shock_travel = QLabel("RL Shock Travel Range (mm): ")
        self.container.addWidget(self.rl_shock_travel)
        
        self.rr_shock_travel = QLabel("RR Shock Travel Range (mm): ")
        self.container.addWidget(self.rr_shock_travel)

        self.layout.addLayout(self.container)

    @pyqtSlot(dict)
    def update_card(self, new_data):
        #print(new_data)
        self.len_run.setText("Length of Run (s): " + str(new_data["Timestamp (s)"][-1])[1:-1])
