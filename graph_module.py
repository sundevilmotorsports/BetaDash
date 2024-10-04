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
from PyQt5.QtGui import QColor, QPen, QFont
from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtGui
import pyqtgraph as pg
from collapsible_module import Collapsible
from pyqtgraph import PlotDataItem
import time
import numpy as np
import serialhander as SerialHandler

class GraphModule(QMainWindow):
    def __init__(self, serialhander : SerialHandler):
        super().__init__()
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
        self.layout.setContentsMargins(0, 0, 0, 0)
        sideBoxLayout = QVBoxLayout()
        self.plot_widget = pg.PlotWidget()
        #self.plot_widget.setBackground(QColor('lightgray'))
        self.pen = pg.mkPen(color='red', width=1)
        self.plot_widget.enableAutoRange(pg.ViewBox.XAxis, enable=False)
        #self.plot_widget.enableAutoRange(pg.ViewBox.YAxis, enable=False)

        self.serialhandler = serialhander
        self.serialhandler.data_changed.connect(self.update_graph)

        self.layout.addWidget(self.plot_widget)
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

        self.checkbox = QCheckBox("Toggle Crosshair")
        self.checkbox.setChecked(False)
        self.sidebox.addWidget(self.checkbox)
        self.crosshair_enable = False
        self.checkbox.stateChanged.connect(self.toggle)

        self.initialize_combo_boxes()

        self.graph_indice = 0
        self.x_axis_offset = 30
        self.y_axis_offset = 0
        self.end_offset = 0

        self.last_mouse_position = [0, 0]
        self.plot_widget.scene().sigMouseClicked.connect(self.mouseClicked)
        self.escalation_status = 0
        self.events = []
        self.event_markers = []
        
    def initCrosshair(self):
        if self.crosshair_enable:
            self.crosshair_v = pg.InfiniteLine(angle=90, movable=False)
            self.crosshair_h = pg.InfiniteLine(angle=0, movable=False)
            self.plot_widget.addItem(self.crosshair_v, ignoreBounds=True)
            self.plot_widget.addItem(self.crosshair_h, ignoreBounds=True)

            self.x_label = pg.TextItem("")
            self.y_label = pg.TextItem("")
            self.plot_widget.addItem(self.x_label)
            self.plot_widget.addItem(self.y_label)

            #self.proxy = pg.SignalProxy(self.plot_widget.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
            self.plot_widget.scene().sigMouseMoved.connect(self.mouseMoved)

    def removeCrosshair(self):
        try:
            self.plot_widget.removeItem(self.crosshair_h)
            self.plot_widget.removeItem(self.crosshair_v)
            self.plot_widget.removeItem(self.x_label)
            self.plot_widget.removeItem(self.y_label)
        except Exception as e:
            print(str(e))

    def mouseMoved(self, e):
        pos = e
        #pos = e[0]
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mousePoint = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            x_pos = mousePoint.x()
            y_pos = mousePoint.y()
            x_text = f"X: {x_pos:.2f}"  # Limiting digits to 2 decimal places
            y_text = f"Y: {y_pos:.2f}"  # Limiting digits to 2 decimal places
            self.x_label.setText(x_text)
            self.y_label.setText(y_text)
            label_color = pg.mkColor('g')
            self.x_label.setColor(label_color)
            self.y_label.setColor(label_color)
            self.x_label.setPos(x_pos, y_pos)
            self.y_label.setPos(x_pos, y_pos)
            self.crosshair_v.setPos(mousePoint.x())
            self.crosshair_h.setPos(mousePoint.y())
            self.last_mouse_position = [x_pos, y_pos]

    def toggle(self, state):
        if state == 0:
            self.crosshair_enable = False
            self.removeCrosshair()
            print("Checkbox is unchecked")
        else:
            self.crosshair_enable = True
            self.initCrosshair()
            print("Checkbox is checked")


    def mouseClicked(self, e):
        pos = e
        #pos = e[0]
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mousePoint = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            x_pos = mousePoint.x()
            #y_pos = mousePoint.y()

        self.escalation_status = self.escalation_status + 1
        if self.escalation_status == 2:
            self.events.append(int(x_pos))
            event_marker = pg.InfiniteLine(pos=x_pos, angle=90, movable=False)
            #event_marker.setPos(x_pos)
            self.plot_widget.addItem(event_marker, ignoreBounds=True)
            self.escalation_status = 0
            self.event_markers.append([event_marker, x_pos])


    def reset(self):
        self.pause_graph()
        self.set_active_data()
        self.plot_graph()

    def set_labels(self):
        x_label = self.x_combo.currentText()
        y_label = self.y_combo.currentText()
        self.plot_widget.clear()
        self.initCrosshair()
        font = QFont()
        font.setPointSize(12)
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
                print(new_data[x_column])
                x_values = np.asarray(new_data[x_column]).flatten() 
                y_values = np.asarray(new_data[y_column]).flatten()
                #x_values = new_data[x_column]
                #y_values = new_data[y_column]
                #self.plot_widget.clear()
                if x_values[-1] >= self.x_axis_offset+self.end_offset:
                    self.end_offset = x_values[-1]
                    self.plot_widget.clear()
                    if self.crosshair_enable:
                        self.removeCrosshair()
                        self.initCrosshair()
                    self.plot_widget.plot(x=x_values, y=y_values, pen=self.pen)
                    self.plot_widget.setXRange(max(0, x_values[-1]-100), x_values[-1]+self.x_axis_offset)
                    if self.crosshair_enable:
                        self.crosshair_h.setPos(self.last_mouse_position[1])
                        self.crosshair_v.setPos(self.last_mouse_position[0])
                        for event_marker in self.event_markers:
                            self.plot_widget.addItem(event_marker[0])
                            event_marker[0].setPos(event_marker[1])
                    #self.plot_widget.setYRange(min(y_values)-10, max(y_values)+100)
                else:
                    self.plot_widget.plot().setData(x=x_values, y=y_values, pen=self.pen)

            except Exception as e:
                if "X and Y arrays must be the same shape" in str(e):
                    print(str(e))
                    min_size = min(len(new_data[x_column]), len(new_data[y_column]))
                    x_values = np.asarray(new_data[x_column][:min_size]).flatten()
                    y_values = np.asarray(new_data[y_column][:min_size]).flatten()
                    self.plot_widget.plot().setData(x=x_values, y=y_values, pen=self.pen)
                    self.plot_widget.setXRange(max(0, x_values[-1]-100), x_values[-1]+10)
                else:
                    print("error", e)
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