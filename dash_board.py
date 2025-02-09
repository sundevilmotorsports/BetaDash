import sys
from PyQt5.QtWidgets import *
import os
from PyQt5.QtGui import QIcon
from graph_module import GraphModule
from gg_plot import ggPlot
from serialhander import SerialHandler
from report_card import ReportModule
from WheelViz import WheelViz
from rollPlot import rollPlot
from label_module import DataTypeDialog
from label_module import LabelModule
import serial.tools.list_ports
import threading
import glob
import pickle
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer
import time
import sqlite3
import qdarkstyle
from qdarkstyle.dark.palette import DarkPalette  # noqa: E402
from qdarkstyle.light.palette import LightPalette  # noqa: E402
from PyQt5.QtWidgets import QSizePolicy
import shutil

class CustomDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize and start application
        self.sessions = []
        self.graph_modules = []
        self.ggPlots = []
        self.video_modules = []

        self.new_session_data = {"pos": [], "size": [], "metadata": []}
        self.current_tab_index = 0

        # Create sessions and data folders if not present
        os.makedirs("sessions", exist_ok=True)
        os.makedirs("data", exist_ok=True)

        # Clean up and recreate a 'temp' folder
        temp_dir = os.path.join("sessions", "temp")
        shutil.rmtree(temp_dir, ignore_errors=True)  # remove old temp folder entirely
        os.makedirs(temp_dir, exist_ok=True)
        
        # Now read only the *real* session files from sessions/*.pkl,
        # ignoring any in sessions/temp/
        sessions = glob.glob("sessions/*.pkl")
        # Filter out anything in 'temp' subdirectory
        sessions = [f for f in sessions if "temp" not in f]
        
        self.sessions = []
        for file in sessions:
            session = pickle.load(open(file, "rb"))
            # Each original session file can remain in "filename" if you want
            session["filename"] = file
            self.sessions.append(session)

        # After loading sessions from disk, check if none exist


        # If you have a 'handler' variable referenced, make sure it's defined or remove this block
        # For clarity, removing references to 'handler.add_session(data)'
        # since 'handler' is not defined here. If you have a global 'handler', define it before use.
        # for file in data_files:
        #     data = pickle.load(open(file, "rb"))
        #     handler.add_session(data)

        self.setWindowTitle("Sun Devil Motorsports Beta Data Dashboard")
        # self.setStyleSheet("""QMainWindow::title {
        #                         color: purple;
        #                         background-color: #2D2D2D;
        #                         font-size: 30px;
        #                     }""")
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


        # Attempt to connect to a serial port
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
                self.serialmonitor = SerialHandler("null", 9600, 1, 0.1)
                self.reading_thread = threading.Thread(target=self.serial_read_loop)
                self.reading_thread.daemon = True
                self.reading_thread.start()
            '''

        except Exception as e:
            print(f"Error: {e}")

        # Buttons
        self.graph_module_button = QPushButton("Add Graph Module")
        self.graph_module_button.setMaximumWidth(200)
        self.graph_module_button.clicked.connect(self.create_graph_module)

        self.gg_plot_button = QPushButton("Add GG PLOT")
        self.gg_plot_button.setMaximumWidth(200)
        self.gg_plot_button.clicked.connect(self.create_gg_plt)

        self.ROLL_plot_button = QPushButton("Add Roll PLOT")
        self.ROLL_plot_button.setMaximumWidth(200)
        self.ROLL_plot_button.clicked.connect(self.create_roll_plt)

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

        # Replace the combo box and load session button with a QTabWidget
        self.tab_widget = QTabWidget()
        # Example: remove the border/pane line in a QTabWidget
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                /* Remove the pane (the area behind the tab bar) border */
                border: none;
                margin: 0px;
                padding: 0px;
            }
            QTabBar::tab {
                /* If you also want to remove the tab's borders (optional): */
                border: none;
                /* adjust the padding if needed */
                padding: 2px;
            }
        """)

        #self.tab_widget.setMaximumWidth(QMdiArea.width)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.tab_widget.tabCloseRequested.connect(self.close_session_tab)
        #self.tab_widget.currentChanged.connect(self.load_session_from_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.save_dashboard_button = QPushButton("Save Dashboard")
        self.save_dashboard_button.setMaximumWidth(200)
        self.save_dashboard_button.clicked.connect(self.save_dashboard)

        self.plus_button = QToolButton()
        self.plus_button.setText("+")
        # Place the button in the top-right corner of the tab bar
        self.tab_widget.setCornerWidget(self.plus_button, Qt.TopRightCorner)

        # Connect its clicked signal to the same "create_new_session" method
        self.plus_button.clicked.connect(self.create_new_session)


        # Add tab widget below toolbar
        self.layout.addWidget(self.tab_widget)


        # Add tabs for previously saved sessions
        for session in self.sessions:
            session_name = session["time"].strftime("%m/%d/%Y, %H:%M:%S")
            self.tab_widget.addTab(QWidget(), session_name)

        self.refresh_rate_label = QLabel("Hertz: ")
        self.refresh_rate_label.setStyleSheet("background-color: #455364;")
        self.serialmonitor.data_changed.connect(self.update_refresh_rate)

        self.toolbar.addWidget(self.graph_module_button)
        self.toolbar.addWidget(self.gg_plot_button)
        self.toolbar.addWidget(self.ROLL_plot_button)
        self.toolbar.addWidget(self.label_module_button)
        self.toolbar.addWidget(self.stop_reading_button)
        self.toolbar.addWidget(self.report_module_button)
        self.toolbar.addWidget(self.wheelviz_button)
        self.toolbar.addWidget(self.radio_button)
        self.toolbar.addWidget(self.write_sql_button)

        self.toolbar.addWidget(self.save_dashboard_button)
        self.toolbar.addStretch(1)
        self.toolbar.addWidget(self.refresh_rate_label)
        self.layout.addWidget(self.mdi_area)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        self.connection = None
        self.db_name = None

        if not self.sessions:
            self.create_new_session()


    def create_new_session(self):
        """
        Create a brand-new in-memory session, store it in sessions/temp/,
        and add a new tab for it.
        """
        new_session = {
            "pos": [],
            "size": [],
            "metadata": [],
            "time": datetime.now(),
        }
        # Generate a temp filename
        current_time = new_session["time"].strftime('%m-%d-%Y_%H_%M_%S')
        filename = f"sessions/temp/{current_time}.pkl"
        new_session["filename"] = filename

        # Write an empty session file right away (optional but keeps logic consistent)
        with open(filename, "wb") as f:
            pickle.dump(new_session, f)

        # Add to self.sessions list
        self.sessions.append(new_session)
        
        # Create a new tab in the QTabWidget
        tab_label = new_session["time"].strftime("%m/%d/%Y, %H:%M:%S")
        self.tab_widget.addTab(QWidget(), tab_label)

        # Switch to the newly added tab
        new_index = self.tab_widget.count() - 1
        self.tab_widget.setCurrentIndex(new_index)

    def on_tab_changed(self, new_index):
        old_index = self.current_tab_index

        # Save the old session
        if old_index != -1 and old_index < len(self.sessions) and old_index != new_index:
            self.save_session_data(old_index)

        # Clear subwindows
        for window in self.mdi_area.subWindowList():
            window.close()

        if new_index == -1:
            # Means there are no tabs at all, do nothing
            self.current_tab_index = -1
            return

        self.load_session_from_tab(new_index)
        self.current_tab_index = new_index

    def save_session_data(self, index):
        """
        Saves the subwindows of the MDI area into self.sessions[index-1],
        and pickles that to the existing .pkl file on disk.
        """
        if index < 0 or index >= len(self.sessions):
            return  # Out of range guard
        
        session_data = self.sessions[index]
        
        # Overwrite these fields with the current subwindows
        session_data["pos"].clear()
        session_data["size"].clear()
        session_data["metadata"].clear()

        # Gather subwindows
        for sub_window in self.mdi_area.subWindowList():
            pos = sub_window.pos()
            size = sub_window.size()
            widget = sub_window.widget()

            session_data["pos"].append((pos.x(), pos.y()))
            session_data["size"].append((size.width(), size.height()))
            
            # widget.get_info() must return a dict that at least has {"type": ...}
            session_data["metadata"].append(widget.get_info())

        # Optionally store a "time" or keep the original time.
        # session_data["time"] = datetime.now()
        
        # Now we must figure out which file it was originally loaded from 
        # (or create a new one). Suppose we keep a "filename" key in session_data:
        if "filename" in session_data:
            filename = session_data["filename"]
        else:
            # If for some reason it was never assigned, generate a new file
            # Or skip saving if you prefer
            current_time = session_data["time"].strftime('%m-%d-%Y_%H_%M_%S')
            filename = f"sessions/{current_time}.pkl"
            session_data["filename"] = filename

        # Write to .pkl
        pickle.dump(session_data, open(filename, "wb"))

    def load_session_from_tab(self, index):
        if index < 0 or index >= len(self.sessions):
            # Invalid index, do nothing
            return

        # Find the session that corresponds to this tab
        active_session = self.sessions[index]
        
        # Clear subwindows
        for window in self.mdi_area.subWindowList():
            window.close()

        #print("Loading session:", active_session)
        tab_amt = len(active_session["pos"])

        # Recreate subwindows for this session
        for i in range(tab_amt):
            metadata = active_session["metadata"][i]
            window_type = metadata.get('type', 'Unknown')
            pos = active_session["pos"][i]
            size = active_session["size"][i]

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
                report_module = ReportModule(self.serialmonitor)
                report_module.set_info(metadata)
                sub_window.setWidget(report_module)
            elif window_type == 'LabelModule':
                sub_window = QMdiSubWindow()
                sub_window.setAttribute(Qt.WA_DeleteOnClose)
                data_type = metadata.get('data_type', "Timestamp (ms)")
                label_module = LabelModule(self.serialmonitor, data_type)
                sub_window.setWidget(label_module)
            else:
                # Unknown type, skip
                continue

            self.mdi_area.addSubWindow(sub_window)
            sub_window.move(pos[0], pos[1])
            sub_window.resize(size[0], size[1])
            sub_window.show()

    def close_session_tab(self, index):
        # 1) Save that tab’s session data
        self.save_session_data(index)

        # 2) Remove the tab from the tab widget
        self.tab_widget.removeTab(index)

        # 3) Remove the corresponding session object from memory if desired
        if 0 <= index < len(self.sessions):
            del self.sessions[index]

        # 4) If no tabs remain, automatically create a new session/tab
        if self.tab_widget.count() == 0:
            self.create_new_session()

        # 5) Adjust current_tab_index if needed
        if index == self.current_tab_index:
            self.current_tab_index = -1


    def update_refresh_rate(self, update_data):
        rate = update_data["Refresh Rate"][-1]
        self.refresh_rate_label.setText(f"{rate:.1f}" + " Hz")

    def serial_read_loop(self):
        self.serialmonitor._read_data()

    def stop_serial_read(self):
        self.serialmonitor.stop_reading()
        if self.reading_thread.is_alive():
            self.reading_thread.join()

    def update_all_graphs(self, new_data):
        for graphmodule in self.graph_modules:
            graphmodule.update_graph(new_data)

    def create_graph_module(self):
        sub_window = QMdiSubWindow()
        new_module = GraphModule(self.serialmonitor)
        self.graph_modules.append(new_module)
        sub_window.setAttribute(Qt.WA_DeleteOnClose)
        sub_window.setWidget(new_module)
        sub_window.setGeometry(new_module.geometry())
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()
    def create_gg_plt(self):
        sub_window = QMdiSubWindow()
        new_module = ggPlot(self.serialmonitor)
        self.ggPlots.append(new_module)
        sub_window.setAttribute(Qt.WA_DeleteOnClose)
        sub_window.setWidget(new_module)
        sub_window.setGeometry(new_module.geometry())
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()
    def create_roll_plt(self):
        sub_window = QMdiSubWindow()
        new_module = rollPlot(self.serialmonitor)
        self.ggPlots.append(new_module)
        sub_window.setAttribute(Qt.WA_DeleteOnClose)
        sub_window.setWidget(new_module)
        sub_window.setGeometry(new_module.geometry())
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def create_label_module(self):
        dialog = DataTypeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selected_data_type, value, channel, channel_formula, channel_inputs = dialog.return_selected()
            sub_window = QMdiSubWindow()
            label_module = LabelModule(self.serialmonitor, selected_data_type, channel=channel, channel_formula=channel_formula, channel_inputs=channel_inputs)
            sub_window.setAttribute(Qt.WA_DeleteOnClose)
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
        sub_window.setAttribute(Qt.WA_DeleteOnClose)
        sub_window.setWidget(wheel_viz)
        sub_window.setGeometry(wheel_viz.geometry())
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def create_sql(self):
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.db_name = f"data/telemetry_data_{current_time}.db"
        self.connection = sqlite3.connect(self.db_name)
        cursor = self.connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_data (
            "Timestamp (ms)" REAL,
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
        """
        1) Save all current open tabs one last time into temp folder
        2) Move each session's .pkl from sessions/temp/ to sessions/
        3) Optionally re-load or rename them so they remain consistent
        """
        # First, save whichever session is currently open
        current_idx = self.tab_widget.currentIndex()
        if current_idx != -1:
            self.save_session_data(current_idx)

        # Move each session whose file is still in sessions/temp/
        for session in self.sessions:
            temp_file = session["filename"]
            if "sessions/temp/" in temp_file.replace("\\","/"):  # handle windows backslashes
                base_name = os.path.basename(temp_file)
                final_path = os.path.join("sessions", base_name)
                # Move the file
                shutil.move(temp_file, final_path)
                # Update the stored filename to the new location
                session["filename"] = final_path

        print("All temp sessions were moved into sessions/ folder.")
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(palette=DarkPalette))
    with open("resources/stylesheets/dark_styling.qss", "r") as f:
        app.setStyleSheet(app.styleSheet() + f.read())
    window = CustomDashboard()
    window.show()
    sys.exit(app.exec_())