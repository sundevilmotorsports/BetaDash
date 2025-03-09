# General Imports
import sys
import os
import serial.tools.list_ports
import threading
import glob
import pickle
import time
import sqlite3
import shutil
from datetime import datetime
# PyQT Imports
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer, QThread
from PyQt5.QtWidgets import QSizePolicy
from pyqtswitch import PyQtSwitch
# Live Module Imports
from serialhander import SerialHandler
from live_modules.graph_module import GraphModule
from live_modules.gg_module import ggModule
from live_modules.rg_module import rgModule
from live_modules.report_card import ReportModule
from live_modules.WheelViz import WheelViz
from live_modules.label_module import DataTypeDialog
from live_modules.label_module import LabelModule
from live_modules.lap_module import LapModule
# Post Module Imports
from post_modules.csv_import import CSVImport
from post_modules.graph_module import PostGraphModule
from post_modules.video_module import PostVideoPlayer
from post_modules.timestamper import TimeStamper
from post_modules.lap_module import PostLapModule
from post_modules.session import Session, SessionManager
# Styling Imports
import qdarkstyle
from qdarkstyle.dark.palette import DarkPalette  # noqa: E402
from qdarkstyle.light.palette import LightPalette  # noqa: E402
# Util Import
from utils import ModuleInfo

class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sun Devil Motorsports Beta Data Dashboard")
        self.setWindowIcon(QIcon("resources/90129757.jpg"))
        self.setGeometry(100, 100, 1800, 900)
        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)
        self.mdi_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi_area.setTabsClosable(True)

        # Establish Tabs and Temp Folder If So, Load Saved Tabs
        self.tabs: list[list[ModuleInfo]] = []
        os.makedirs("tabs", exist_ok=True)
        
        temp_dir = os.path.join("tabs", "temp")
        shutil.rmtree(temp_dir, ignore_errors=True)
        os.makedirs(temp_dir, exist_ok=True)

        self.load_saved_tabs()

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
        #     QTabWidget::pane {
        #         border: none;
        #         margin: 0px;
        #         padding: 0px;
        #     }
        #     QTabBar::tab {
        #         border: none;
        #         padding: 2px;
        #     }
        # """)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        self.current_tab_index = -1

        self.plus_button = QToolButton()
        self.plus_button.setText("+")
        self.plus_button.clicked.connect(self.create_new_tab)
        self.tab_widget.setCornerWidget(self.plus_button, Qt.TopRightCorner)

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
        except Exception as e:
            print(f"Error: {e}")

        self.add_live_modules()
        self.layout.addWidget(self.tab_widget)
        self.layout.addWidget(self.mdi_area)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        if not self.tabs:
            self.create_new_tab()
        else:
            for tab in self.tabs:
                self.add_tab_from_modules(tab)

        self.session_manager = SessionManager()
        self.dash_saved = False
        self.save_path = None

        # SQL DEPRECATION
        # self.connection = None
        # self.db_name = None

        # ------------------------------
        # POST DATA MODULES + FUNCTIONALITY
        # ------------------------------

        # Footer for Pause/Play Multimedia
        # self.footer = QStatusBar()
        # self.slider_label = QLabel("Slider Value: ")
        # self.timestamper = TimeStamper()
        # self.timestamper.slider.valueChanged.connect(self.update_slider_label)
        # # self.setStatusBar(self.footer)
        # self.play_button = QPushButton("Play")
        # self.play_button.clicked.connect(self.play)
        # self.pause_button = QPushButton("Pause")
        # self.pause_button.clicked.connect(self.pause)

        # self.footer.addWidget(self.play_button)
        # self.footer.addWidget(self.pause_button)
        # self.footer.addPermanentWidget(self.slider_label)
        # self.footer.addPermanentWidget(self.timestamper.slider)

    def slider_moved(self, position):
        print(position)
        self.timestamper.time_stamp = position * (self.timestamper.max_time / 100)

    def play(self):
        for module in self.graph_modules:
            module.play_graph()
        for module in self.video_modules:
            module.play()
            # time.sleep(1)

    def pause(self):
        for module in self.graph_modules:
            module.pause_graph()
        for module in self.video_modules:
            module.pause()
            # time.sleep(1)

    def update_slider_label(self, value):
        value = int(value * (self.timestamper.max_time / 100))
        # self.slider_label.setText(f"Slider Value: {value}")

    def load_saved_tabs(self):
        for file in glob.glob("tabs/*.pkl"):
            if "temp" not in file:
                with open(file, "rb") as f:
                    try:
                        tab_data = pickle.load(f)
                        if isinstance(tab_data, list) and all(isinstance(mod, ModuleInfo) for mod in tab_data):
                            self.tabs.append(tab_data)
                    except Exception as e:
                        print(f"Error loading tab from {file}: {e}")

    def create_new_tab(self):
        if self.current_tab_index != -1:
            self.save_tab_data(self.current_tab_index)

        new_tab: list[ModuleInfo] = []

        current_time = datetime.now().strftime('%m-%d-%Y_%H_%M_%S')
        filename = f"tabs/temp/{current_time}.pkl"
        self.tabs.append(new_tab)
        self.add_tab_from_modules(new_tab)

        for window in self.mdi_area.subWindowList():
            window.close()

        self.save_tab_data(len(self.tabs) - 1)
        self.current_tab_index = self.tab_widget.currentIndex() # update this shii

    def add_tab_from_modules(self, tab_modules: list[ModuleInfo]):
        tab_index = self.tab_widget.addTab(QWidget(), f"Tab {self.tab_widget.count() + 1}")
        self.tab_widget.setCurrentIndex(tab_index)

        for module_info in tab_modules:
            self.add_module_to_mdi(module_info)

    def add_module_to_mdi(self, module_info):
        sub_window = QMdiSubWindow()
        sub_window.setAttribute(Qt.WA_DeleteOnClose)

        if module_info.moduleType == 'GraphModule':
            widget = GraphModule(self.serialmonitor)
        elif module_info.moduleType == 'WheelViz':
            widget = WheelViz(self.serialmonitor)
        elif module_info.moduleType == 'ReportModule':
            widget = ReportModule(self.serialmonitor)
        elif module_info.moduleType == 'LabelModule':
            widget = LabelModule(self.serialmonitor, module_info.info.get('data_type', "Timestamp (ms)"))
        else:
            return 

        widget.set_info(module_info.info)
        sub_window.setWidget(widget)

        self.mdi_area.addSubWindow(sub_window)
        sub_window.move(*module_info.pos)
        sub_window.resize(*module_info.size)
        sub_window.show()

    def save_tab_data(self, index):
        if index < 0 or index >= len(self.tabs):
            print("Cringle in save tab data")
            return

        current_tab = []
        # current_temp_index = self.current_tab_index
        # self.tab_widget.setCurrentIndex(index)
        for sub_window in self.mdi_area.subWindowList():
            widget = sub_window.widget()
            if hasattr(widget, "get_info"):
                module_info = ModuleInfo(
                    moduleType=type(widget).__name__,
                    pos=(sub_window.x(), sub_window.y()),
                    size=(sub_window.width(), sub_window.height()),
                    info=widget.get_info(),
                )
                current_tab.append(module_info)

        self.tabs[index] = current_tab

        filename = f"tabs/temp/tab_{index}.pkl"
        with open(filename, "wb") as f:
            pickle.dump(current_tab, f)

    def load_tab_data(self, index):
        if index < 0 or index >= len(self.tabs):
            return

        for module_info in self.tabs[index]:
            self.add_module_to_mdi(module_info)

    def on_tab_changed(self, new_index):
        print("tab changed")
        if self.current_tab_index != -1:
            self.save_tab_data(self.current_tab_index)

        for window in self.mdi_area.subWindowList():
            window.close()

        if 0 <= new_index < len(self.tabs):
            self.load_tab_data(new_index)

        self.current_tab_index = new_index

    def close_tab(self, index):
        if 0 <= index < len(self.tabs):
            self.save_tab_data(index)
            del self.tabs[index]

        self.tab_widget.removeTab(index)

        if self.tab_widget.count() == 0:
            self.create_new_tab()

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

    def switch_toggled(self, f):
        self.clear_layout(self.toolbar)
        if f:
            self.add_post_modules()
        else:  
            self.add_live_modules()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                layout.removeWidget(widget)
            else:
                layout.removeItem(item)
        
        layout.update()

    def add_live_modules(self):
        # Buttons
        self.graph_module_button = QPushButton("Add Graph Module")
        self.graph_module_button.setMaximumWidth(200)
        self.graph_module_button.clicked.connect(self.create_graph_module)

        self.gg_plot_button = QPushButton("Add GG Module")
        self.gg_plot_button.setMaximumWidth(200)
        self.gg_plot_button.clicked.connect(self.create_gg_module)

        self.ROLL_plot_button = QPushButton("Add RG Module")
        self.ROLL_plot_button.setMaximumWidth(200)
        self.ROLL_plot_button.clicked.connect(self.create_rg_module)

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

        self.lap_module_button = QPushButton("Add Lap Module")
        self.lap_module_button.setMaximumWidth(200)
        self.lap_module_button.clicked.connect(self.create_lap_module)

        # self.radio_button = QRadioButton("USE SQL")
        # self.radio_button.setChecked(False)
        # self.radio_button.clicked.connect(self.create_sql)
        # self.radio_button.clicked.connect(self.toggle_db_write)

        # self.write_sql_button = QPushButton("Write Data to DB")
        # self.write_sql_button.setDisabled(True)
        # self.write_sql_button.setMaximumWidth(200)
        # self.write_sql_button.clicked.connect(self.write_sql)

        self.save_dashboard_button = QPushButton("Save Dashboard")
        self.save_dashboard_button.setMaximumWidth(200)
        self.save_dashboard_button.clicked.connect(self.save_dashboard)

        self.load_dashboard_button = QPushButton("Load Dashboard")
        self.load_dashboard_button.setMaximumWidth(200)
        self.load_dashboard_button.clicked.connect(self.load_dashboard)

        self.refresh_rate_label = QLabel("Hertz: ")
        self.refresh_rate_label.setStyleSheet("background-color: #455364;")
        self.serialmonitor.data_changed.connect(self.update_refresh_rate)

        # Create PyQt Switch to switch between live and post data
        self.switch = PyQtSwitch()
        # self.switch.setAnimation(True)
        self.switch.setChecked(False)
        self.switch.toggled.connect(self.switch_toggled)
        # switch.setCircleDiameter(40)
        self.switch_label = QLabel("Live Data")

        self.toolbar.addWidget(self.switch_label)
        self.toolbar.addWidget(self.switch)
        self.toolbar.addWidget(self.graph_module_button)
        self.toolbar.addWidget(self.gg_plot_button)
        self.toolbar.addWidget(self.ROLL_plot_button)
        self.toolbar.addWidget(self.label_module_button)
        self.toolbar.addWidget(self.stop_reading_button)
        self.toolbar.addWidget(self.report_module_button)
        self.toolbar.addWidget(self.wheelviz_button)
        self.toolbar.addWidget(self.lap_module_button)
        # self.toolbar.addWidget(self.radio_button)
        # self.toolbar.addWidget(self.write_sql_button)
        self.toolbar.addWidget(self.save_dashboard_button)
        self.toolbar.addWidget(self.load_dashboard_button)
        self.toolbar.addStretch(1)
        self.toolbar.addWidget(self.refresh_rate_label)

        self.setStatusBar(None)
    
    def add_post_modules(self):
        self.post_camera_module_button = QPushButton("Add Camera")
        self.post_camera_module_button.setMaximumWidth(200)
        self.post_camera_module_button.clicked.connect(self.create_post_camera_module)

        self.post_graph_module_button = QPushButton("Add Post Graph Module")
        self.post_graph_module_button.setMaximumWidth(200)
        self.post_graph_module_button.clicked.connect(self.create_post_graph_module)

        self.post_lap_button = QPushButton("Add Post Lap Module")
        self.post_lap_button.setMaximumWidth(200)
        self.post_lap_button.clicked.connect(self.create_post_lap_module)

        self.add_csv_button = QPushButton("Add CSV File")
        self.add_csv_button.setMaximumWidth(200)
        self.add_csv_button.clicked.connect(self.introduce_csv_importer)

        self.select_session_button = QComboBox()
        self.select_session_button.setMaximumWidth(200)
        self.select_session_button.setPlaceholderText("Select Session")
        # self.select_session_button.currentIndexChanged.connect(self.update_session)

        self.save_dashboard_button = QPushButton("Save Dashboard")
        self.save_dashboard_button.setMaximumWidth(200)
        self.save_dashboard_button.clicked.connect(self.save_dashboard)

        self.load_dashboard_button = QPushButton("Load Dashboard")
        self.load_dashboard_button.setMaximumWidth(200)
        self.load_dashboard_button.clicked.connect(self.load_dashboard)

        self.refresh_rate_label = QLabel("Hertz: ")
        self.refresh_rate_label.setStyleSheet("background-color: #455364;")
        self.serialmonitor.data_changed.connect(self.update_refresh_rate)

        # Populate drop down window with available session objects
        for session in self.session_manager.get_active_sessions():
            self.select_session_button.addItem(
                session["time"].strftime("%m/%d/%Y, %H:%M:%S")
            )

        # Create PyQt Switch to switch between live and post data
        self.switch = PyQtSwitch()
        self.switch.setChecked(True)
        self.switch.toggled.connect(self.switch_toggled)
        # self.switch.setAnimation(True)
        # switch.setCircleDiameter(40)
        self.switch_label = QLabel("Post Data")

        self.toolbar.addWidget(self.switch_label)
        self.toolbar.addWidget(self.switch)
        self.toolbar.addWidget(self.post_camera_module_button)
        self.toolbar.addWidget(self.post_graph_module_button)
        self.toolbar.addWidget(self.post_lap_button)
        self.toolbar.addWidget(self.add_csv_button)
        self.toolbar.addWidget(self.save_dashboard_button)
        self.toolbar.addWidget(self.load_dashboard_button)
        self.toolbar.addWidget(self.select_session_button)
        self.toolbar.addStretch(1)
        self.toolbar.addWidget(self.refresh_rate_label)

        self.footer = QStatusBar()
        self.slider_label = QLabel("Slider Value: ")
        self.timestamper = TimeStamper()
        self.timestamper.slider.valueChanged.connect(self.update_slider_label)
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play)
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause)

        self.footer.addWidget(self.play_button)
        self.footer.addWidget(self.pause_button)
        self.footer.addWidget(self.slider_label)
        self.footer.addWidget(self.timestamper.slider)

        self.setStatusBar(self.footer)

    def create_graph_module(self):
        sub_window = QMdiSubWindow()
        new_module = GraphModule(self.serialmonitor)
        # self.graph_modules.append(new_module)
        sub_window.setAttribute(Qt.WA_DeleteOnClose)
        sub_window.setWidget(new_module)
        sub_window.setGeometry(new_module.geometry())
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def create_gg_module(self):
        sub_window = QMdiSubWindow()
        new_module = ggModule(self.serialmonitor)
        sub_window.setAttribute(Qt.WA_DeleteOnClose)
        sub_window.setWidget(new_module)
        sub_window.setGeometry(new_module.geometry())
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def create_rg_module(self):
        sub_window = QMdiSubWindow()
        new_module = rgModule(self.serialmonitor)
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

    def create_lap_module(self):
        sub_window = QMdiSubWindow()
        lap = LapModule(self.serialmonitor)
        sub_window.setAttribute(Qt.WA_DeleteOnClose)
        sub_window.setWidget(lap)
        sub_window.setGeometry(lap.geometry())
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def create_post_camera_module(self):
        """Upon a connection with a button, this will create a sub-window which is a container for a VideoPlayer (check class).
        This subwindow is added to the Multiple Document Interface which is the meat and potatoes of our application.
        """
        sub_window = QMdiSubWindow()
        self.video_modules.append(PostVideoPlayer(timestamper=self.timestamper))
        self.video_modules[-1].setWindowIcon(QIcon("90129757.jpg"))
        sub_window.setWidget(self.video_modules[-1])
        sub_window.setGeometry(self.video_modules[-1].geometry())
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def create_post_graph_module(self):
        """Upon a connection with a button, this will create a sub-window which is a container for a GraphModule (check class)
        This subwindow is added to the Multiple Document Interface which is the meat and potatoes of our application.
        """
        sub_window = QMdiSubWindow()
        self.graph_modules.append(PostGraphModule(timestamper=self.timestamper))
        sub_window.setWidget(self.graph_modules[-1])
        sub_window.setGeometry(self.graph_modules[-1].geometry())
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def create_post_lap_module(self):
        sub_window = QMdiSubWindow()
        sub_window.setWindowTitle("Lap Module")
        lap_module = PostLapModule()
        sub_window.setWidget(lap_module)
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def introduce_csv_importer(self):
        """Upon a connection with a button, this will open a file dialog which allows a user to select a csv file of their choosing.
        This file will be imported using our CSVImporter class and added to a set of active sessions
        """
        filename = QFileDialog.getOpenFileName(None, "Open CSV File", "CSVs", filter="CSV Files(*.csv)")
        if filename[0] == "":
            return
        importer = CSVImport(filename[0])
        importer.exec()
        self.select_session_button.clear()
        self.active_data = self.session_manager.get_active_sessions()[0].data

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
        if self.save_path:
            with open(self.save_path, "wb") as f:
                pickle.dump(self.tabs, f)
            print(f"Dashboard saved: {self.save_path}")
        else:
            date_str = datetime.now().strftime('%m-%d-%Y')
            dash_number = 1
            while True:
                self.save_path = f"tabs/dashboard_{date_str}_dash{dash_number}.pkl"
                if not os.path.exists(self.save_path):
                    break
                dash_number += 1

            with open(self.save_path, "wb") as f:
                pickle.dump(self.tabs, f)

            self.dash_saved = True
            print(f"Dashboard saved: {self.save_path}")

    def load_dashboard(self):
        filename, _ = QFileDialog.getOpenFileName(None, "Open Dash File", "tabs", filter="Pickle Files (dashboard*.pkl)")
        try:
            with open(filename, "rb") as f:
                saved_tabs = pickle.load(f)

            self.tab_widget.clear()
            self.tabs: list[list[ModuleInfo]] = []
            self.current_tab_index = -1
            self.tab_widget.currentChanged.disconnect(self.on_tab_changed)

            for tab_modules in saved_tabs:
                self.tabs.append(tab_modules)
                self.add_tab_from_modules(tab_modules)

            if self.tabs:
                self.tab_widget.setCurrentIndex(0)
                self.on_tab_changed(0)

            self.tab_widget.currentChanged.connect(self.on_tab_changed)
        except Exception as e:
            print("lmao lil bro: ", e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(palette=DarkPalette))
    with open("resources/stylesheets/dark_styling.qss", "r") as f:
        app.setStyleSheet(app.styleSheet() + f.read())
    window = Dashboard()
    window.show()
    sys.exit(app.exec_())