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
)
import os
from PyQt5.QtGui import QIcon
from graph_module import GraphModule
from serialhander import SerialHandler
import serial.tools.list_ports
import threading
import glob
import pickle
from datetime import datetime
from PyQt5.QtCore import Qt
import time


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
        self.setWindowIcon(QIcon("90129757.jpg"))
        self.setGeometry(100, 100, 1800, 900)
        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)
        self.mdi_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi_area.setTabsClosable(True)

        self.layout = QVBoxLayout()
        self.toolbar = QHBoxLayout()
        self.footer = QStatusBar()
        self.layout.addLayout(self.toolbar)

        try:
            # Get a list of available serial ports
            available_ports = serial.tools.list_ports.comports()

            # Iterate through each available port and try to connect
            for port in available_ports:
                try:
                    print(f"Attempting to connect to {port.name}")
                    self.serialmonitor = SerialHandler("COM6", 9600, 1, .05) # be careful with the last parameter anything with .09 or lower is unstable
                    reading_thread = threading.Thread(target=self.serial_read_loop)
                    reading_thread.daemon = True
                    reading_thread.start()
                    #self.serialmonitor.data_changed.connect(self.update_all_graphs)
                    print(f"Connected to {port.name}")
                    break  # Break out of the loop if connection is successful
                except Exception as e:
                    print(f"Error connecting to {port.name}: {e}")

            else:
                print("No open serial ports found.")

        except Exception as e:
            print(f"Error: {e}")
        
        # I probably dont want to have a dataframe in here. Maybe try to create a call back in graph_module to regraph when the dataframe in serial changes
        # Regardless I dont have an elegant solution now.


        # ------------------------------
        # Adding Buttons to Layout and Window
        # ------------------------------

        self.graph_module_button = QPushButton("Add Graph Module")
        self.graph_module_button.setMaximumWidth(200)
        self.graph_module_button.clicked.connect(self.create_graph_module)

        self.save_dashboard_button = QPushButton("Save Dashboard")
        self.save_dashboard_button.setMaximumWidth(200)
        self.save_dashboard_button.clicked.connect(self.save_dashboard)
        
        self.stop_reading_button = QPushButton("Stop Serial Read")
        self.stop_reading_button.setMaximumWidth(200)
        self.stop_reading_button.clicked.connect(self.stop_serial_read)

        # Populate drop down window with available session objects
        for session in self.sessions:
            self.select_session_button.addItem(
                session["time"].strftime("%m/%d/%Y, %H:%M:%S")
            )
        # Add all buttons to the toolbar
        self.toolbar.addWidget(self.graph_module_button)
        self.toolbar.addWidget(self.save_dashboard_button)
        self.toolbar.addWidget(self.stop_reading_button)

        self.toolbar.addStretch(1)
        self.layout.addWidget(self.mdi_area)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)
      
    def find_available_serial_port(self):
        available_ports = list_ports.comports()
        for port in available_ports:
            if port.device.startswith("COM"):  #This using Windows convention, need to use /dev/tty if linux or mac
                return port.device
        return None

    def serial_read_loop(self):
        self.serialmonitor._read_data()

    def stop_serial_read(self):
        self.serialmonitor.stop_reading()
        reading_thread.stop()

    def update_all_graphs(self, new_data):
        for graphmodule in self.graph_modules:
            graphmodule.update_graph(new_data)

    def create_graph_module(self):
        """Upon a connection with a button, this will create a sub-window which is a container for a GraphModule (check class)
        This subwindow is added to the Multiple Document Interface which is the meat and potatoes of our application.
        """
        sub_window = QMdiSubWindow()
        threading.Thread(self.graph_modules.append(GraphModule(self.serialmonitor))).start()
        sub_window.setWidget(self.graph_modules[-1])
        sub_window.setGeometry(self.graph_modules[-1].geometry())
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def save_dashboard(self):
        """Upon a connection with a button, this will save the current state of the dashboard and dump it into a new pickle file which will be stored in the sessions folder."""
        data = {
            "pos": [],
            "size": [],
            "metadata": [],
            "csv": handler.get_names(),
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomDashboard()
    window.show()
    sys.exit(app.exec_())