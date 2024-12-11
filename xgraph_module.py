from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QStatusBar,
    QCheckBox,
    QSlider,
    QColorDialog,
)
from PyQt5.QtCore import Qt, pyqtSlot, QPointF
from PyQt5.QtGui import QColor, QPen, QFont, QPalette
from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtGui
import pyqtgraph as pg
from collapsible_module import Collapsible
from pyqtgraph import PlotDataItem
import time
import numpy as np
import serialhander as SerialHandler
from checkable_combo import CheckableComboBox

class GraphModule(QMainWindow):
    def __init__(self, serialhander : SerialHandler):
        super().__init__()
        self._cleanup_done = False
        self.setWindowTitle("Graph Module")
        self.setGeometry(100, 100, 1050, 600)
        #self.menubar = self.menuBar()
        #self.menubar.setStyleSheet(
        #    "background-color: #333; color: white; font-size: 14px;"
        #)
        #self.menubar.setStyleSheet("QMenu::item:selected { background-color: #555; }")
        #self.menubar.setStyleSheet("QMenu::item:pressed { background-color: #777; }")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.plot_widget = pg.PlotWidget()
        #self.plot_widget.setBackground(QColor('lightgray'))
        self.pen = pg.mkPen(color='red', width=1)
        #self.plot_widget.enableAutoRange(pg.ViewBox.XAxis, enable=False)
        #self.plot_widget.enableAutoRange(pg.ViewBox.YAxis, enable=False)

        self.serialhandler = serialhander
        self.serialhandler.data_changed.connect(self.update_graph)

        self.layout.addWidget(self.plot_widget)
        self.sidebox = QVBoxLayout()
        self.sidebox2 = QVBoxLayout()

        self.left = False

        self.sidebox.setAlignment(Qt.AlignTop)
        self.x_combo = QComboBox()
        self.y_combo = QComboBox()
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

        # Color dialog button
        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.open_color_dialog)
        self.sidebox.addWidget(self.color_button)

        # Thickness slider
        self.thickness_slider = QSlider(Qt.Horizontal)
        self.thickness_slider.setRange(1, 10)  # Thickness range
        self.thickness_slider.setValue(1)  # Default thickness
        self.thickness_slider.valueChanged.connect(self.update_thickness)
        self.sidebox.addWidget(QLabel("Graph Thickness:"))
        self.sidebox.addWidget(self.thickness_slider)

        # Queue Size Slider
        self.queue_size_slider = QSlider(Qt.Horizontal)
        self.queue_size_slider.setRange(1, 200) 
        self.queue_size_slider.setValue(200)

        # Label for slider
        self.queue_size_label = QLabel(f"Queue Size: {self.queue_size_slider.value()}")
        self.sidebox.addWidget(self.queue_size_label)
        self.sidebox.addWidget(self.queue_size_slider)

        self.sidebox2.setAlignment(Qt.AlignTop)

        self.sideBoxLayout = QVBoxLayout()
        self.sideBoxLayout.addLayout(self.sidebox)
        self.sideBoxLayout.addLayout(self.sidebox2)
        
        #self.layout.addLayout(self.sidebox)

        #self.reset_button = QPushButton("Reset")
        #self.reset_button.clicked.connect(self.reset)

        collapsible_container = Collapsible()
        collapsible_container.setContentLayout(self.sideBoxLayout)
        self.layout.addWidget(collapsible_container)

        self.checkbox = QCheckBox("Toggle Crosshair")
        self.checkbox.setChecked(False)
        self.sidebox.addWidget(self.checkbox)
        self.crosshair_enable = False
        self.checkbox.stateChanged.connect(self.toggle)

        self.checkbox_gg = QCheckBox("Toggle GvG Plot")
        self.checkbox_gg.setChecked(False)
        self.sidebox.addWidget(self.checkbox_gg)
        self.gg_enable = False
        self.checkbox_gg.stateChanged.connect(self.gg_toggle)

        self.initialize_combo_boxes()

        self.graph_indice = 0
        self.x_axis_offset = 30
        self.y_axis_offset = 0
        self.end_offset = 0

        self.graph_point_count = 0
        self.max_point = 200

        self.last_mouse_position = [0, 0]
        self.plot_widget.scene().sigMouseClicked.connect(self.mouseClicked)
        self.escalation_status = 0
        self.events = []
        self.event_markers = []

    def destructor(self):
        if self._cleanup_done:
            return  # Skip cleanup if already done
        print("Destructor called, performing cleanup...")
        #self.reset_button.clicked.disconnect(self.reset)
        self.checkbox.stateChanged.disconnect(self.toggle)
        self.x_combo.currentIndexChanged.disconnect(self.set_labels)
        self.y_combo.currentIndexChanged.disconnect(self.set_labels)
        self.serialhandler.data_changed.disconnect(self.update_graph)
        try:
            self.plot_widget.scene().sigMouseMoved.disconnect(self.mouseMoved)
            self.plot_widget.scene().sigMouseClicked.disconnect(self.mouseClicked)
        except:
            pass

        del (self.central_widget, self.layout, self.plot_widget, 
            self.pen, self.sidebox, self.sidebox2, self.x_combo, self.y_combo, 
            self.trim_container, self.selected_y_columns, self.selected_x,
            self.checkbox, self.crosshair_enable, 
            self.graph_indice, self.x_axis_offset, 
            self.y_axis_offset, self.end_offset, self.last_mouse_position, 
            self.escalation_status, self.events, self.event_markers, self.serialhandler)
        self._cleanup_done = True
        print("Cleanup complete.")

    def open_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.pen.setColor(color)

    def update_thickness(self, value):
        self.pen.setWidth(value)
        
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
            y_min, y_max = self.plot_widget.viewRange()[1]
            y_offset_multiplier = 0.05
            y_offset = (y_max - y_min) * y_offset_multiplier
            x_text = f"X: {x_pos:.2f}"  # Limiting digits to 2 decimal places
            y_text = f"Y: {y_pos:.2f}"  # Limiting digits to 2 decimal places
            self.x_label.setText(x_text)
            self.y_label.setText(y_text)
            label_color = pg.mkColor('g')
            self.x_label.setColor(label_color)
            self.y_label.setColor(label_color)
            self.x_label.setPos(x_pos, y_pos)
            self.y_label.setPos(x_pos, y_pos-y_offset)
            self.crosshair_v.setPos(x_pos)
            self.crosshair_h.setPos(y_pos)
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

    def gg_toggle(self):
        print("GG TOGGLE")
        if self.gg_enable == 1:
            self.gg_enable = False
        else:
            self.gg_enable = True
            self.x_combo.setCurrentIndex(1)
            self.y_combo.setCurrentIndex(2)
            self.plot_widget.clear()

    def mouseClicked(self, e):
        pos = e
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
        self.plot_widget.getPlotItem().getAxis("bottom").hide()
        
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
        queue_size = self.queue_size_slider.value()
        self.queue_size_label.setText(f"Queue Size: {queue_size}")
        
        if x_column in new_data and y_column in new_data:
            try:
                x_values = np.asarray(new_data[x_column]).flatten()
                y_values = np.asarray(new_data[y_column]).flatten()
                #self.plot_widget.clear()
                if self.gg_enable:
                    self.plot_widget.clear()
                    x_values = x_values[-15:]
                    y_values = y_values[-15:]
                else:
                    x_values = x_values[-queue_size:]
                    y_values = y_values[-queue_size:]
                if x_values[-1] >= self.x_axis_offset+self.end_offset - 10000000000: ## using temporarily, wanted graph to always plot, testing ranges
                    self.end_offset = x_values[-1]
                    self.plot_widget.clear()
                    if self.crosshair_enable:
                        self.removeCrosshair()
                        self.initCrosshair()
                    self.plot_widget.plot(x=x_values, y=y_values, pen=self.pen)
                    ## Setting Ranges
                    if self.gg_enable:
                        self.plot_widget.setXRange(0, 1)
                        self.plot_widget.setYRange(0, 1)
                    else:
                        #self.plot_widget.setXRange(max(0, x_values[-1]-self.queue_size_slider.value), x_values[-1]+self.x_axis_offset)
                        y_range = max(y_values) - min(y_values)
                        #self.plot_widget.setYRange(min(y_values) - y_range * .05, max(y_values) + y_range * .05)
                    self.graph_point_count+=1
                    if self.crosshair_enable:
                        self.crosshair_h.setPos(self.last_mouse_position[1])
                        self.crosshair_v.setPos(self.last_mouse_position[0])
                        for event_marker in self.event_markers:
                            self.plot_widget.addItem(event_marker[0])
                            event_marker[0].setPos(event_marker[1])
                else:
                    if self.gg_enable:
                        self.plot_widget.setXRange(0, 1)
                        self.plot_widget.setYRange(0, 1)
                    self.plot_widget.plot().setData(x=x_values, y=y_values, pen=self.pen)
                    self.graph_point_count+=1

            except Exception as e:
                if "X and Y arrays must be the same shape" in str(e):
                    print(str(e))
                    min_size = min(len(new_data[x_column]), len(new_data[y_column]))
                    x_values = np.asarray(new_data[x_column][:min_size]).flatten()
                    y_values = np.asarray(new_data[y_column][:min_size]).flatten()
                    self.plot_widget.plot().setData(x=x_values, y=y_values, pen=self.pen)
                    #self.plot_widget.setXRange(max(0, x_values[-1]-100), x_values[-1]+10)
                    self.graph_point_count+=1
                else:
                    print("error", e)
        else:
            print("Not able to plot")

    def get_info(self):
        """Returns a dictionary containing the state of the GraphModule."""
        return {
            'type': 'GraphModule',
            'x_axis': self.x_combo.currentText(),
            'y_axis': self.y_combo.currentText(),  # Use currentData() to get selected items
            'color': self.pen.color().name(),
            'thickness': self.pen.width(),
            'queue_size': self.queue_size_slider.value(),
            'crosshair_enabled': self.crosshair_enable,
            'gvg_enabled': self.gg_enable,
        }

    
    def set_info(self, info):
        """Sets the state of the GraphModule based on the provided info dictionary."""
        if 'x_axis' in info:
            index = self.x_combo.findText(info['x_axis'])
            if index >= 0:
                self.x_combo.setCurrentIndex(index)
            else:
                print(f"Warning: X axis '{info['x_axis']}' not found in combo box.")

        if 'y_axis' in info:
            index = self.y_combo.findText(info['y_axis'])
            if index >= 0:
                self.y_combo.setCurrentIndex(index)
            else:
                print(f"Warning: Y axis '{info['y_axis']}' not found in combo box.")
            # Update the display text
            #self.y_combo.updateText()
        if 'color' in info:
            color = QColor(info['color'])
            self.pen.setColor(color)
        if 'thickness' in info:
            self.pen.setWidth(info['thickness'])
            self.thickness_slider.setValue(info['thickness'])
        if 'queue_size' in info:
            self.queue_size_slider.setValue(info['queue_size'])
        if 'crosshair_enabled' in info:
            self.checkbox.setChecked(info['crosshair_enabled'])
        if 'gvg_enabled' in info:
            self.checkbox_gg.setChecked(info['gvg_enabled'])



    def get_graph_type(self):
        return "GraphModule"
    
    def closeEvent(self, event):
        ## This is a function override, be very careful
        self.destructor() # destructor for all local variables in the class
        event.accept() # This is the function to actually close the window