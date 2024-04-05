from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QStatusBar
)
from PyQt5.QtCore import Qt, pyqtSlot
import pyqtgraph as pg
from collapsible_module import Collapsible
from pyqtgraph import PlotDataItem
import time

class GraphModule(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data_set = []
        self.setWindowTitle("Graph Module")
        self.setGeometry(100, 100, 1050, 600)
        self.menubar = self.menuBar()
        self.menubar.setStyleSheet(
            "background-color: #333; color: white; font-size: 14px;"
        )
        self.menubar.setStyleSheet("QMenu::item:selected { background-color: #555; }")
        self.menubar.setStyleSheet("QMenu::item:pressed { background-color: #777; }")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)
        sideBoxLayout = QVBoxLayout()
        graph_widget = QWidget()
        self.plot_widget = pg.PlotWidget()

        plot_layout = QVBoxLayout(graph_widget)
        plot_layout.addWidget(self.plot_widget)
        self.layout.addWidget(graph_widget)

        self.sidebox = QVBoxLayout()
        self.sidebox2 = QVBoxLayout()

        self.left = False

        self.sidebox.setAlignment(Qt.AlignTop)
        self.x_combo = QComboBox(self.central_widget)
        self.y_combo = QComboBox(self.central_widget)
        self.y_combo.setFixedHeight(25)

        self.x_combo.currentIndexChanged.connect(self.set_labels)
        self.y_combo.currentIndexChanged.connect(self.set_labels)

        trim_upper = QHBoxLayout()
        trim_under = QHBoxLayout()
        self.trim_container = QVBoxLayout()

        self.selected_y_columns = None
        self.selected_x = None

        self.sidebox.addWidget(QLabel("Select X Axis Column:"))
        self.sidebox.addWidget(self.x_combo)
        self.sidebox.addWidget(QLabel("Select Y Axis Column:"))
        self.sidebox.addWidget(self.y_combo)
        self.sidebox.addLayout(self.trim_container)

        self.sidebox2.setAlignment(Qt.AlignTop)

        sideBoxLayout = QVBoxLayout()
        sideBoxLayout.addLayout(self.sidebox)
        sideBoxLayout.addLayout(self.sidebox2)
        
        #self.layout.addLayout(self.sidebox)

        self.reset_button = QPushButton("Reset", self.central_widget)
        self.reset_button.clicked.connect(self.reset)
        self.footer = QStatusBar()
        self.setStatusBar(self.footer)
        self.footer.addWidget(self.reset_button)

        collapsible_container = Collapsible()
        collapsible_container.setContentLayout(sideBoxLayout)
        self.layout.addWidget(collapsible_container)

        self.initialize_combo_boxes()

        self.graph_indice = 0


    def reset(self):
        self.pause_graph()
        self.set_active_data()
        self.plot_graph()

    def set_labels(self):
        x_label = self.x_combo.currentText()
        y_label = self.y_combo.currentText()
        self.plot_widget.clear()
        self.plot_widget.setLabel('bottom', text=x_label)
        self.plot_widget.setLabel('left', text=y_label)
        
    def initialize_combo_boxes(self):
        # Clear existing items from combo boxes
        self.x_combo.clear()
        self.y_combo.clear()

        # Hardcoded list of column names
        column_names = [
            "Timestamp (s)",
            "X Acceleration (mG)",
            "Y Acceleration (mG)",
            "Z Acceleration (mG)",
            "X Gyro (mdps)",
            "Y Gyro (mdps)",
            "Z Gyro (mdps)",
            "Front Left Speed (mph)",
            "Front Left Brake Temp (C)",
            "Front Left Ambient Temperature (C)",
            "Front Right Speed (mph)",
            "Front Right Brake Temp (C)",
            "Front Right Ambient Temperature (C)",
            "Back Left Speed (mph)",
            "Back Left Brake Temp (C)",
            "Back Left Ambient Temperature (C)",
            "Back Right Speed (mph)",
            "Back Right Brake Temp (C)",
            "Back Right Ambient Temperature (C)",
            "DRS Toggle", 
            "Steering Angle", 
            "Throttle Input", 
            "Battery Voltage (V)", 
            "DAQ Current Draw (A)"
        ]
        for column_name in column_names:
            self.x_combo.addItem(column_name)
            self.y_combo.addItem(column_name)

    @pyqtSlot(dict)
    def update_graph(self, new_data):
        x_column = self.x_combo.currentText()
        y_column = self.y_combo.currentText()
        
        if x_column in new_data and y_column in new_data:
            try:
                self.plot_widget.plot().setData(x=new_data[x_column], y=new_data[y_column])
                start_index = self.graph_indice
                for i in range(start_index, len(new_data[x_column])):
                    #x_value = new_data[x_column][i]
                    self.plot_widget.setXRange(max(0, new_data[x_column][i]-30), new_data[x_column][i])
                    time.sleep(.1)
                self.graph_indice = start_index
            except Exception as e:
                if "X and Y arrays must be the same shape" in str(e):
                    min_size = min(len(new_data[x_column]), len(new_data[y_column]))
                    x_values = new_data[x_column][:min_size]
                    y_values = new_data[y_column][:min_size]
                    self.plot_widget.plot().setData(x=x_values, y=y_values)
                else:
                    print(e)
        else:
            print("Not able to plot")


    def plot_graph(self):
        pass

    def get_info(self):
        """Getter that returns an array with the layouts of the sideboxes"""
        info = []
        for i in self.data_set:
            info.append(i.get_info())
        return info

    def get_graph_type(self):
        return "GraphModule"
