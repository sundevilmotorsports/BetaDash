import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QMdiArea,
    QVBoxLayout,
    QHBoxLayout,
    QStatusBar,
    QWidget,
    QPushButton,
    QComboBox,
    QFileDialog,
    QMdiSubWindow,
    QSlider,
    QLabel,
    QTextEdit,
    QRadioButton,
    QDockWidget,
    QDialog
)
import os
from PyQt5.QtGui import QIcon
from graph_module import GraphModule
from serialhander import SerialHandler
from report_card import ReportModule
from WheelViz import WheelViz
from label_module import DataTypeDialog
from label_module import LabelModule
import serial.tools.list_ports
import threading
import glob
import pickle
from datetime import datetime
from PyQt5.QtCore import (
    Qt,
)
import time
import sqlite3
import qdarkstyle
from qdarkstyle.dark.palette import DarkPalette  # noqa: E402
from qdarkstyle.light.palette import LightPalette  # noqa: E402

class CustomDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize and start application

        # ------------------------------
        # Pickle Implementation
        # Object Serialization
        # ------------------------------

        # Loads established pickle files within /sessions folder
        # Appends loaded files encapsulated within a 'Session' object and adds to sessions array of 'Session' objects stored in file
        self.sessions = []
        self.graph_modules = []
        self.video_modules = []
        #create sessions and data folder is not there already
        os.makedirs("sessions", exist_ok=True)
        os.makedirs("data", exist_ok=True)

        sessions = glob.glob(f"sessions/*.pkl")
        data = glob.glob(f"data/*.pkl")
        for file in sessions:
            session = pickle.load(open(file, "rb"))
            self.sessions.append(session)

        # Appends loaded files into
        for file in data:
            data = pickle.load(open(file, "rb"))
            handler.add_session(data)

        # ------------------------------
        # Window Implementation
        #      ____________
        #     /            \  <- PyQT House
        #    /              \
        #   |   __________   |
        #   |  |pyqtgraph |  |
        #   |  |__________|  |
        #   |                |
        #   |________________|
        # ------------------------------

        self.setWindowTitle("Sun Devil Motorsports Beta Data Dashboard")
        self.setWindowIcon(QIcon("resources/90129757.jpg"))
        self.setGeometry(100, 100, 1800, 900)
        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)
        self.mdi_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi_area.setTabsClosable(True)

        self.layout = QVBoxLayout()
        self.toolbar = QHBoxLayout()
        self.layout.addLayout(self.toolbar)

        #added self. before all reading_thread
        try:
            # Get a list of available serial ports
            while True:
                available_ports = serial.tools.list_ports.comports()
                port_vec = []
                num = -1
                print("1: Fake Data")
                port_vec.append("null")
                for i, port in enumerate(available_ports):
                    print(i + 2, ": ",port.name, "\t", port.description)
                    port_vec.append(port.name)

                try:
                    num = int(input("Choose an port number from list above: "))
                    if num < 0:
                        raise ValueError("input must be greater than 0")

                    self.serialmonitor = SerialHandler(port_vec[num-1], 9600, 1, .02)
                    self.reading_thread = threading.Thread(target=self.serial_read_loop)
                    self.reading_thread.daemon = True
                    self.reading_thread.start()
                    print(f"Connected to {port_vec[num-1]}")
                    break
                except Exception as e:
                    print(f"Error connecting to port index {num-1}: {e}")
                    
            # Iterate through each available port and try to connect
            '''
            for port in available_ports:
                try:
                    print(f"Attempt to connect to {port.name}? [y/n]")
                    if input() == 'y':
                        self.serialmonitor = SerialHandler(port.name, 9600, 1, .02)
                        self.reading_thread = threading.Thread(target=self.serial_read_loop)
                        self.reading_thread.daemon = True
                        self.reading_thread.start()
                        #self.serialmonitor.data_changed.connect(self.update_all_graphs)
                        print(f"Connected to {port.name}")
                        break  # Break out of the loop if connection is successful
                except Exception as e:
                    print(f"Error connecting to {port.name}: {e}")
            else:
                print("No open serial ports found. Starting testing SerialHandler")
                self.serialmonitor = SerialHandler("null", 9600, 1, .1)
                self.reading_thread = threading.Thread(target=self.serial_read_loop)
                self.reading_thread.daemon = True
                self.reading_thread.start()
            '''

        except Exception as e:
            print(f"Error: {e}")

        # ------------------------------
        # Adding Buttons to Layout and Window
        # ------------------------------

        self.graph_module_button = QPushButton("Add Graph Module")
        self.graph_module_button.setMaximumWidth(200)
        self.graph_module_button.clicked.connect(self.create_graph_module)

        self.label_module_button = QPushButton("Add Label Module")
        self.label_module_button.setMaximumWidth(200)
        self.label_module_button.clicked.connect(self.create_label_module)
        
        self.stop_reading_button = QPushButton("Stop Serial Read")
        self.stop_reading_button.setMaximumWidth(200)
        self.stop_reading_button.clicked.connect(self.stop_serial_read)

        self.report_module_button = QPushButton("Add Report Card")
        self.report_module_button.setMaximumWidth(200)
        self.report_module_button.clicked.connect(self.create_report_module)

        self.wheelviz_button = QPushButton("Add WheelViz")
        self.wheelviz_button.setMaximumWidth(200)
        self.wheelviz_button.clicked.connect(self.add_wheelviz)

        self.radio_button = QRadioButton("USE SQL")
        self.radio_button.setChecked(False)
        self.radio_button.clicked.connect(self.create_sql)
        self.radio_button.clicked.connect(self.toggle_db_write)

        self.write_sql_button = QPushButton("Write Data to DB")
        self.write_sql_button.setDisabled(True)
        self.write_sql_button.setMaximumWidth(200)
        self.write_sql_button.clicked.connect(self.write_sql)

        self.save_dashboard_button = QPushButton("Save Dashboard")
        self.save_dashboard_button.setMaximumWidth(200)
        self.save_dashboard_button.clicked.connect(self.save_dashboard)

        self.select_session_button = QComboBox()
        self.select_session_button.setMaximumWidth(200)
        # Populate drop down window with available session objects
        for session in self.sessions:
            self.select_session_button.addItem(
                session["time"].strftime("%m/%d/%Y, %H:%M:%S")
            )

        self.load_session_button = QPushButton("Load Session")
        self.load_session_button.setMaximumWidth(200)
        self.load_session_button.clicked.connect(self.update_session)

        # Populate drop down window with available session objects
        for session in self.sessions:
            self.select_session_button.addItem(
                session["time"].strftime("%m/%d/%Y, %H:%M:%S")
            )

        self.refresh_rate_label = QLabel("Hertz: ")
        self.refresh_rate_label.setStyleSheet("background-color: #455364;")
        self.serialmonitor.data_changed.connect(self.update_refresh_rate)

        self.toolbar.addWidget(self.graph_module_button)
        self.toolbar.addWidget(self.label_module_button)
        self.toolbar.addWidget(self.stop_reading_button)
        self.toolbar.addWidget(self.report_module_button)
        self.toolbar.addWidget(self.wheelviz_button)
        self.toolbar.addWidget(self.radio_button)
        self.toolbar.addWidget(self.write_sql_button)
        self.toolbar.addWidget(self.save_dashboard_button)
        self.toolbar.addWidget(self.load_session_button)
        self.toolbar.addWidget(self.select_session_button)
        self.toolbar.addStretch(1)
        self.toolbar.addWidget(self.refresh_rate_label)
        self.layout.addWidget(self.mdi_area)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        ### SQL Implementation - partly lmao
        self.connection = None
        self.db_name = None

    def update_refresh_rate(self, update_data):
        rate = update_data["Refresh Rate"][-1]
        self.refresh_rate_label.setText(f"{rate:.1f}" + " Hz")

    def serial_read_loop(self):
        self.serialmonitor._read_data()

    #def stop_serial_read(self):
    #    self.serialmonitor.stop_reading()
    #    reading_thread.stop()
    
    #fixed? stop serial button
    def stop_serial_read(self):
        self.serialmonitor.stop_reading()
        if self.reading_thread.is_alive():  # Check if the thread is running
            self.reading_thread.join()  # Properly join the thread instead of stopping it abruptly


    def update_all_graphs(self, new_data):
        for graphmodule in self.graph_modules:
            graphmodule.update_graph(new_data)

    def create_graph_module(self):
        """Upon a connection with a button, this will create a sub-window which is a container for a GraphModule (check class)
        This subwindow is added to the Multiple Document Interface which is the meat and potatoes of our application.
        """
        sub_window = QMdiSubWindow()
        threading.Thread(self.graph_modules.append(GraphModule(self.serialmonitor))).start()
        sub_window.setAttribute(Qt.WA_DeleteOnClose)
        sub_window.setWidget(self.graph_modules[-1])
        sub_window.setGeometry(self.graph_modules[-1].geometry())
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def create_label_module(self):
        dialog = DataTypeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selected_data_type, value = dialog.return_selected()
            sub_window = QMdiSubWindow()
            label_module = LabelModule(self.serialmonitor, selected_data_type)
            #sub_window.setAttribute(Qt.WA_DeleteOnClose)
            sub_window.setWidget(label_module)
            sub_window.setGeometry(label_module.geometry())
            self.mdi_area.addSubWindow(sub_window)
            sub_window.show()

    def create_report_module(self):
        sub_window = QMdiSubWindow()
        report_card = ReportModule(self.serialmonitor)
        sub_window.setAttribute(Qt.WA_DeleteOnClose)
        sub_window.setWidget(report_card)
        sub_window.setGeometry(report_card.geometry())
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def add_wheelviz(self):
        sub_window = QMdiSubWindow()
        wheel_viz = WheelViz(self.serialmonitor)
        #sub_window.setStyleSheet("QMdiSubWindow { background-color: lightblue; }"
        #                         "QMdiSubWindow::title { background-color: darkblue; color: black; }")
        sub_window.setAttribute(Qt.WA_DeleteOnClose)
        sub_window.setWidget(wheel_viz)
        sub_window.setGeometry(wheel_viz.geometry())
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def create_sql(self):
        ### SQL Implementation
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')  # output: "2024-10-09_14-30-45"
        self.db_name = f"data/telemetry_data_{current_time}.db"
        self.connection = sqlite3.connect(self.db_name)
        cursor = self.connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_data (
            "Timestamp (s)" REAL,
            "X Acceleration (mG)" REAL,
            "Y Acceleration (mG)" REAL,
            "Z Acceleration (mG)" REAL,
            "X Gyro (mdps)" REAL,
            "Y Gyro (mdps)" REAL,
            "Z Gyro (mdps)" REAL,
            "Front Left Speed (mph)" REAL,
            "Front Left Brake Temp (C)" REAL,
            "Front Left Ambient Temperature (C)" REAL,
            "Front Right Speed (mph)" REAL,
            "Front Right Brake Temp (C)" REAL,
            "Front Right Ambient Temperature (C)" REAL,
            "Back Left Speed (mph)" REAL,
            "Back Left Brake Temp (C)" REAL,
            "Back Left Ambient Temperature (C)" REAL,
            "Back Right Speed (mph)" REAL,
            "Back Right Brake Temp (C)" REAL,
            "Back Right Ambient Temperature (C)" REAL,
            "Differential Speed (RPM)" REAL,
            "DRS Toggle" REAL,
            "Steering Angle (deg)" REAL,
            "Throttle Input" REAL,
            "Front Brake Pressure (BAR)" REAL,
            "Rear Brake Pressure (BAR)" REAL,
            "GPS Latitude (DD)" REAL,
            "GPS Longitude (DD)" REAL,
            "Battery Voltage (mV)" REAL,
            "Current Draw (mA)" REAL,
            "Front Right Shock Pot (mm)" REAL,
            "Front Left Shock Pot (mm)" REAL,
            "Rear Right Shock Pot (mm)" REAL,
            "Rear Left Shock Pot (mm)" REAL,
            "Lap Counter" INTEGER)
        ''')
        self.connection.commit()
        self.radio_button.clicked.disconnect(self.create_sql)
        self.connection.close()

    def write_sql(self):    
        self.write_sql_button.setDisabled(True)
        self.serialmonitor.insert_data_to_db(self.db_name)
        print("WRITTEN TO SQL")
        self.write_sql_button.setDisabled(False)
        
    def toggle_db_write(self):
        if self.radio_button.isChecked():
            self.write_sql_button.setDisabled(False)
        else:
            self.write_sql_button.setDisabled(True)

    def save_dashboard(self):
        """Save the current state of the dashboard and dump it into a new pickle file."""
        data = {
            "pos": [],
            "size": [],
            "metadata": [],
            "time": datetime.now(),
        }
        for tab in self.mdi_area.subWindowList():
            widget = tab.widget()
            pos = tab.pos()
            size = tab.size()
            print(f"Saving subwindow: {widget}, Position: {pos}, Size: {size}")
            data["pos"].append((tab.pos().x(), tab.pos().y()))
            data["size"].append((tab.size().width(), tab.size().height()))
            data["metadata"].append(tab.widget().get_info())
        pickle.dump(
            data,
            open(f"sessions/{datetime.now().strftime('%m-%d-%Y, %H_%M_%S')}.pkl", "wb"),
        )
        self.select_session_button.addItem(data["time"].strftime("%m/%d/%Y, %H:%M:%S"))
        self.sessions.append(data)

    def update_session(self):
        """Load a selected session from the dropdown."""
        index = self.select_session_button.currentIndex()
        if index < 0 or index >= len(self.sessions):
            return  # Invalid index
        active_session = self.sessions[index]
        tab_amt = len(active_session["pos"])
        print(active_session)
        # Remove existing subwindows
        for window in self.mdi_area.subWindowList():
            window.close()
        # Recreate subwindows
        for i in range(tab_amt):
            metadata = active_session["metadata"][i]
            window_type = metadata.get('type', 'Unknown')
            pos = active_session["pos"][i]
            size = active_session["size"][i]
            print(f"Restoring window {i}: type={window_type}, Position={pos}, Size={size}")
            if window_type == 'GraphModule':
                sub_window = QMdiSubWindow()
                sub_window.setAttribute(Qt.WA_DeleteOnClose)
                graph_module = GraphModule(self.serialmonitor)
                graph_module.set_info(metadata)
                sub_window.setWidget(graph_module)
            elif window_type == 'WheelViz':
                sub_window = QMdiSubWindow()
                sub_window.setAttribute(Qt.WA_DeleteOnClose)
                wheel_viz = WheelViz(self.serialmonitor)
                wheel_viz.set_info(metadata)
                sub_window.setWidget(wheel_viz)
            elif window_type == 'ReportModule':
                sub_window = QMdiSubWindow()
                sub_window.setAttribute(Qt.WA_DeleteOnClose)
                report_card = ReportModule(self.serialmonitor)
                report_card.set_info(metadata)
                sub_window.setWidget(report_card)
            else:
                continue  # Unknown window type, skip
            self.mdi_area.addSubWindow(sub_window)
            sub_window.move(pos[0], pos[1])
            sub_window.resize(size[0], size[1])
            sub_window.show()

    '''
    def save_dashboard(self):
        """Upon a connection with a button, this will save the current state of the dashboard and dump it into a new pickle file which will be stored in the sessions folder."""
        data = {
            "pos": [],
            "size": [],
            "metadata": [],
            "time": datetime.now(),
        }
        for tab in self.mdi_area.subWindowList():
            # TAKE NOTE: SOME ERRORS OCCUR HERE WHEN SWITCHING ACTIVE SESSIONS. I GOT AN ERROR BUT STRUGGLED TO REPLICATE IT.
            # TRY TO DEBUG IN FUTURE.
            data["pos"].append((tab.pos().x(), tab.pos().y()))
            data["size"].append((tab.size().width(), tab.size().height()))
            data["metadata"].append(tab.widget().get_info())
        pickle.dump(
            data,
            open(f"sessions/{datetime.now().strftime('%m-%d-%Y, %H_%M_%S')}.pkl", "wb"),
        )
        self.select_session_button.addItem(data["time"].strftime("%m/%d/%Y, %H:%M:%S"))
        self.sessions.append(data)

    def update_session(self):
        """Upon a connection with a combobox, this will allow the user to select a different active session. This change will be repr"""
        active_session = self.sessions[self.select_session_button.currentIndex()]
        # active_session = handler.get_active_sessions[self.select_session_button.currentIndex()]
        tab_amt = len(active_session["pos"])
        print(active_session)
        for window in self.mdi_area.subWindowList():
            self.mdi_area.removeSubWindow(window)
        print(len(self.mdi_area.subWindowList()))
        for tab in range(tab_amt):
            self.create_graph_module()
        for i, tab in enumerate(self.mdi_area.subWindowList()):
            tab.move(active_session["pos"][i][0], active_session["pos"][i][1])
            tab.resize(active_session["size"][i][0], active_session["size"][i][1])
            if (tab.widget().get_graph_type() == "GraphModule"):
                tab.widget().init_combobox(
                    active_session["metadata"][i][0][0],
                    active_session["metadata"][i][0][1],
                    active_session["metadata"][i][0][2],
                )
            else:
                #implement for lap module, should be able to show the different laps from when saved
                tab.widget().init_combobox(
                    active_session["metadata"][i][0][0],
                    active_session["metadata"][i][0][1],
                    active_session["metadata"][i][0][2],
                )
    '''
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(palette=DarkPalette))
    with open("stylesheets/dark_styling.qss", "r") as f:
        app.setStyleSheet(app.styleSheet() + f.read())
    window = CustomDashboard()
    window.show()
    sys.exit(app.exec_())