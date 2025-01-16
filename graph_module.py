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
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_items = []
        self.plot_data_items = {}   
        self.line_colors = {}  # Store colors for each y_column
        self.plot_order = []

        self.rainbow_colors = [
            QColor("#FF0000"),  # Red
            QColor("#FF7F00"),  # Orange
            QColor("#FFFF00"),  # Yellow
            QColor("#00FF00"),  # Green
            QColor("#0000FF"),  # Blue
            QColor("#4B0082"),  # Indigo
            QColor("#8B00FF")   # Violet
        ]
        self.color_index = 0

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
        self.y_combo = CheckableComboBox()
        self.y_combo.model().dataChanged.connect(lambda: self.modifyPlots())
        self.y_combo.setFixedHeight(25)

        #self.x_combo.currentIndexChanged.connect(self.set_labels)
        #self.y_combo.currentIndexChanged.connect(self.set_labels)

        trim_upper = QHBoxLayout()
        trim_under = QHBoxLayout()
        self.trim_container = QVBoxLayout()

        self.selected_y_columns = None
        self.selected_x = None

        self.y_list_layout = QVBoxLayout()
        self.y_list_layout.setSpacing(2)  # Reduce vertical spacing
        self.y_list_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.sidebox.addLayout(self.y_list_layout)

        self.sidebox.addWidget(QLabel("Select X Axis Column:"))
        self.sidebox.addWidget(self.x_combo)
        self.sidebox.addWidget(QLabel("Select Y Axis Column:"))
        self.sidebox.addWidget(self.y_combo)
        self.sidebox.addLayout(self.trim_container)

        # Thickness slider
        self.thickness_slider = QSlider(Qt.Horizontal)
        self.thickness_slider.setRange(1, 10)  # Thickness range
        self.thickness_slider.setValue(1)  # Default thickness
        self.thickness_slider.valueChanged.connect(self.update_thickness)
        self.sidebox.addWidget(QLabel("Graph Thickness:"))
        self.sidebox.addWidget(self.thickness_slider)

        # Queue Size Slider
        self.queue_size_slider = QSlider(Qt.Horizontal)
        self.queue_size_slider.setRange(1, 300) 
        self.queue_size_slider.setValue(300)

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
        self.max_point = 300

        self.last_mouse_position = [0, 0]
        #self.plot_widget.scene().sigMouseClicked.connect(self.mouseClicked)
        self.escalation_status = 0
        self.events = []
        self.event_markers = []

    def destructor(self):
        if self._cleanup_done:
            return  # Skip cleanup if already done
        print("Destructor called, performing cleanup...")
        #self.reset_button.clicked.disconnect(self.reset)
        self.checkbox.stateChanged.disconnect(self.toggle)
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
            #self.initCrosshair()
            print("Checkbox is checked crosshair disabled rn")

    def gg_toggle(self):
        print("GG TOGGLE")
        if self.gg_enable == 1:
            self.gg_enable = False
        else:
            self.gg_enable = True
            self.x_combo.setCurrentIndex(1)
            self.y_combo.setCurrentIndex(2)
            self.plot_widget.clear()
            self.queue_size_slider.setValue(50)

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

    '''def set_labels(self):
        x_label = self.x_combo.currentText()
        y_label = self.y_combo.currentText()
        self.plot_widget.clear()
        self.initCrosshair()
        font = QFont()
        font.setPointSize(12)
        self.plot_widget.setLabel('bottom', text=x_label)
        self.plot_widget.setLabel('left', text=y_label)
    '''
        
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
            "Differential Speed (RPM)",
            "DRS Toggle",
            "Steering Angle (deg)",
            "Throttle Input",
            "Front Brake Pressure (BAR)" ,
            "Rear Brake Pressure (BAR)",
            "GPS Latitude (DD)",
            "GPS Longitude (DD)",
            "Battery Voltage (mV)",
            "Current Draw (mA)",
            "Front Right Shock Pot (mm)",
            "Front Left Shock Pot (mm)",
            "Back Right Shock Pot (mm)",
            "Back Left Shock Pot (mm)",
            "Lap Counter",
            "Refresh Rate"
        ]
        for column_name in column_names:
            self.x_combo.addItem(column_name)
            self.y_combo.addItem(column_name)

    @pyqtSlot(dict)
    def update_graph(self, new_data):
        x_column = self.x_combo.currentText()
        y_columns = list(self.plot_data_items.keys())
        queue_size = self.queue_size_slider.value()
        self.queue_size_label.setText(f"Queue Size: {queue_size}")

        if x_column not in new_data:
            print(f"X column '{x_column}' not found in data")
            return

        x_values = np.asarray(new_data[x_column]).flatten()
        x_values = x_values[-queue_size:]

        for y_column in y_columns:
            if y_column not in new_data:
                print(f"Y column '{y_column}' not found in data")
                continue

            y_values = np.asarray(new_data[y_column]).flatten()
            y_values = y_values[-queue_size:]

            # Synchronize lengths
            min_length = min(len(x_values), len(y_values))
            x_values_sync = x_values[-min_length:]
            y_values_sync = y_values[-min_length:]

            # Update existing plot data
            data_item = self.plot_data_items[y_column]['data_item']
            data_item.setData(x=x_values_sync, y=y_values_sync)

            # Optionally, update y-axis range if needed
            y_min, y_max = np.min(y_values_sync), np.max(y_values_sync)
            y_range = y_max - y_min
            y_pad = y_range * 0.05  # 5% padding
            plot_item = self.plot_data_items[y_column]['plot_item']
            plot_item.setYRange(y_min - y_pad, y_max + y_pad, padding=0)

        # Update x-axis range on the bottom plotif self.plot_items:
        if len(self.plot_items) > 0:
            x_min, x_max = x_values_sync[0], x_values_sync[-1]
            self.plot_items[-1].setXRange(x_min, x_max, padding=0)


    def modifyPlots(self):
        y_columns = self.y_combo.currentData()
        print("Selected Y columns:", y_columns)

        num_plots = len(y_columns)
        if num_plots == 0:
            if not hasattr(self, 'no_y_columns_printed') or not self.no_y_columns_printed:
                print("No Y-columns selected")
                self.no_y_columns_printed = True
            return
        else:
            self.no_y_columns_printed = False

        print("Before sorting:", y_columns)
        if not self.plot_order:
            self.plot_order = list(y_columns)       
        else:
            for col in y_columns:
                if col not in self.plot_order:
                    self.plot_order.append(col)    
        y_columns = [y for y in self.plot_order if y in y_columns]
        print("After sorting:", y_columns)

        # Remove any plots that are no longer selected
        for y_col in list(self.plot_data_items.keys()):
            if y_col not in y_columns:
                plot_item = self.plot_data_items[y_col]['plot_item']
                self.plot_widget.removeItem(plot_item)
                del self.plot_data_items[y_col]
                self.plot_items.remove(plot_item)
                if y_col in self.plot_order:
                    self.plot_order.remove(y_col)

        y_columns = [y for y in self.plot_order if y in y_columns]

        # Adjust plot positions
        for idx, y_column in enumerate(y_columns):
            if y_column in self.plot_data_items:
                # Update plot position
                plot_item = self.plot_data_items[y_column]['plot_item']
                self.plot_widget.ci.addItem(plot_item, row=idx, col=0)
            else:
                # Assign a rainbow color
                color = self.rainbow_colors[self.color_index % len(self.rainbow_colors)]
                self.color_index += 1

                plot_item = self.plot_widget.addPlot(row=idx, col=0)
                data_item = plot_item.plot(pen=pg.mkPen(color=color, width=1))
                self.plot_data_items[y_column] = {'plot_item': plot_item, 'data_item': data_item}
                self.plot_items.append(plot_item)
                self.line_colors[y_column] = color
                # Add y_column to plot_order if not already there
                if y_column not in self.plot_order:
                    self.plot_order.append(y_column)

        if len(self.plot_items) > 0:
            bottom_plot = self.plot_items[-1]
            for plot_item in self.plot_items[:-1]:
                plot_item.setXLink(bottom_plot)

        self.update_axes_visibility()
        self.update_graph(self.serialhandler.data)

        # Clear existing widgets in y_list_layout
        for i in reversed(range(self.y_list_layout.count())):
            item = self.y_list_layout.takeAt(i)
            w = item.widget()
            if w:
                w.deleteLater()

        for y_col in y_columns:
            h_layout = QHBoxLayout()
            label = QLabel(y_col)
            color_btn = QPushButton()
            color_btn.setFixedSize(20,20)
            c = self.line_colors[y_col]
            color_btn.setStyleSheet(f"background-color: {c.name()}; border: 1px solid black;")
            color_btn.clicked.connect(lambda ch, yc=y_col: self.change_line_color(yc))
            h_layout.addWidget(color_btn)
            h_layout.addWidget(label)
            widget_container = QWidget()
            widget_container.setLayout(h_layout)
            self.y_list_layout.addWidget(widget_container)

        print("modifyPlots called")

    def update_axes_visibility(self):
        """
        This method ensures that only the bottom plot has a visible bottom axis,
        and all other plots have their bottom axis fully hidden.
        """
        if len(self.plot_items) == 0:
            return

        # Hide bottom axis on all but the bottom plot
        for plot_item in self.plot_items[:-1]:
            plot_item.showAxis("bottom", show=False)
            ax = plot_item.getAxis("bottom")
            # Remove any ticks or values
            ax.setStyle(showValues=False)
            ax.setTicks([])
            # Remove axis line
            ax.setPen(None)
            # Remove label
            plot_item.setLabel('bottom', "")

        # Show bottom axis on the bottom plot
        bottom_plot = self.plot_items[-1]
        bottom_plot.showAxis("bottom", show=True)
        ax = bottom_plot.getAxis("bottom")
        # Show values on the bottom plot
        ax.setStyle(showValues=True)
        # You can customize ticks if necessary, or leave defaults
        bottom_plot.setLabel('bottom', text=self.x_combo.currentText())

    def change_line_color(self, y_col):
        # Open color dialog and change line color
        new_color = QColorDialog.getColor(initial=self.line_colors[y_col], parent=self)
        if new_color.isValid():
            self.line_colors[y_col] = new_color
            data_item = self.plot_data_items[y_col]['data_item']
            data_item.setPen(pg.mkPen(color=new_color, width=self.thickness_slider.value()))
            self.refresh_y_list()


    def refresh_y_list(self):
        # Rebuilds the sidebar list without reprocessing plots
        for i in reversed(range(self.y_list_layout.count())):
            item = self.y_list_layout.takeAt(i)
            w = item.widget()
            if w:
                w.deleteLater()

        y_columns = list(self.plot_data_items.keys())
        for y_col in y_columns:
            h_layout = QHBoxLayout()
            label = QLabel(y_col)
            color_btn = QPushButton()
            color_btn.setFixedSize(20,20)
            c = self.line_colors[y_col]
            color_btn.setStyleSheet(f"background-color: {c.name()}; border: 1px solid black;")
            color_btn.clicked.connect(lambda ch, yc=y_col: self.change_line_color(yc))

            h_layout.addWidget(color_btn)
            h_layout.addWidget(label)
            container = QWidget()
            container.setLayout(h_layout)
            self.y_list_layout.addWidget(container)



    def get_info(self):
        """Returns a dictionary containing the state of the GraphModule."""
        return {
            'type': 'GraphModule',
            'x_axis': self.x_combo.currentText(),
            'y_axis': self.y_combo.currentData(),  # Use currentData() to get selected items
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
            # Set the check state of items
            for i in range(self.y_combo.model().rowCount()):
                item = self.y_combo.model().item(i)
                if item.data() in info['y_axis'] or item.text() in info['y_axis']:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
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