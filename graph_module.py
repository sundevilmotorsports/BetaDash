from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSlot, QPointF
from PyQt5.QtGui import QColor, QPen, QFont, QPalette
from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtGui
import pyqtgraph as pg
import time
import numpy as np
import re
import serialhander as SerialHandler
from collapsible_module import Collapsible
from pyqtgraph import PlotDataItem
from checkable_combo import CheckableComboBox
from channel import MathChannelsDialog
from sympy import symbols, sympify, lambdify
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict
from utils import Utils

@dataclass
class PlotItem:
    plot_item: pg.PlotItem
    data_item: pg.PlotDataItem
    y_column: str | List[str]
    line_color: QColor
    label_item: Optional[pg.TextItem] = field(default=None)
    math_ch: Optional[Callable] = field(default=None)
    math_ch_str: Optional[str] = field(default=None)

class GraphModule(QMainWindow):
    def __init__(self, serialhandler : SerialHandler):
        super().__init__()
        self._cleanup_done = False
        self.setWindowTitle("Graph Module")
        self.setGeometry(100, 100, 1050, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_items: Dict[str, PlotItem] = {} # {plot_item, data_item, y_column, line_color, math_ch, math_ch_str} FORMAT PAY ATTENTION, CHANGED FOR NOW, MAYBE PERMEANTELY

        self.math_channels = []

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
        self.pen = pg.mkPen(color='red', width=1)

        self.serialhandler = serialhandler
        self.serialhandler.data_changed.connect(self.update_graph)

        self.layout.addWidget(self.plot_widget)
        self.sidebox = QVBoxLayout()
        self.sidebox2 = QVBoxLayout()

        self.sidebox.setAlignment(Qt.AlignTop)
        self.x_combo = QComboBox()
        self.y_combo = CheckableComboBox()
        self.y_combo.model().dataChanged.connect(lambda: self.modify_plots(False, None))
        self.y_combo.setFixedHeight(25)

        #self.x_combo.currentIndexChanged.connect(self.set_labels)
        #self.y_combo.currentIndexChanged.connect(self.set_labels)

        self.selected_y_columns = None
        self.selected_x = None

        self.y_list_layout = QVBoxLayout()
        self.y_list_layout.setSpacing(2)
        self.y_list_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebox.addLayout(self.y_list_layout)

         # Math Channel
        self.math_channel_button = QPushButton("Select Math CHs")
        self.math_channel_button.clicked.connect(self.open_math_channel)
        self.math_channel_layout = QHBoxLayout()
        self.math_channel_layout.addWidget(self.math_channel_button)
        self.math_channel_layout.setContentsMargins(0, 0, 0, 0)
        self.math_channel_layout.setStretch(1, 1)

        self.sidebox.addWidget(QLabel("Select X Axis Column:"))
        self.sidebox.addWidget(self.x_combo)
        self.sidebox.addWidget(QLabel("Select Y Axis Column:"))
        self.sidebox.addWidget(self.y_combo)
        self.sidebox.addLayout(self.math_channel_layout)

        # Queue Size Slider
        self.queue_size_slider = QSlider(Qt.Horizontal)
        self.queue_size_slider.setRange(1, 1000) 
        self.queue_size_slider.setValue(300)

        # Label for slider
        self.queue_size_label = QLabel(f"Queue Size: {self.queue_size_slider.value()}")
        self.sidebox.addWidget(self.queue_size_label)
        self.sidebox.addWidget(self.queue_size_slider)

        self.sidebox2.setAlignment(Qt.AlignTop)

        self.sideBoxLayout = QVBoxLayout()
        self.sideBoxLayout.addLayout(self.sidebox)
        self.sideBoxLayout.addLayout(self.sidebox2)
        
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
        #print("Destructor called, performing cleanup...")
        self.checkbox.stateChanged.disconnect(self.toggle)
        self.serialhandler.data_changed.disconnect(self.update_graph)
        try:
            self.plot_widget.scene().sigMouseMoved.disconnect(self.mouseMoved)
            self.plot_widget.scene().sigMouseClicked.disconnect(self.mouseClicked)
        except:
            pass

        del (self.central_widget, self.layout, self.plot_widget, 
            self.pen, self.sidebox, self.sidebox2, self.x_combo, self.y_combo,  self.selected_y_columns, 
            self.selected_x, self.checkbox, self.crosshair_enable, self.graph_indice, self.x_axis_offset, 
            self.y_axis_offset, self.end_offset, self.last_mouse_position, self.escalation_status,
             self.events, self.event_markers, self.serialhandler)
        self._cleanup_done = True
        #print("Cleanup complete.")

    def open_math_channel(self):
        channel_dialog = MathChannelsDialog("graph_module")
        if channel_dialog.exec() == QDialog.Accepted:
            self.modify_plots(True, channel_dialog.return_formula())
       
    def create_lambda_with_variables(self, input_formulas):
        def replace_bracket(match):
            var_name = match.group(1)
            return variable_map[var_name]

        lambda_func_list = []
        unique_variables_list = []

        for formula in input_formulas:
            matches = re.findall(r'\[([^\]]+)\]', formula)
            unique_variables = list(set(matches))
            variable_map = {var: f"var_{i}" for i, var in enumerate(unique_variables)}
            modified_string = re.sub(r'\[([^\]]+)\]', replace_bracket, formula)
            sympy_expr = sympify(modified_string)
            lambda_func = lambdify(list(variable_map.values()), sympy_expr)
            lambda_func_list.append(lambda_func)
            unique_variables_list.append(unique_variables)
        return lambda_func_list, input_formulas, unique_variables_list
            
    def open_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid(): 
            self.pen.setColor(color)
        
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
        
    def initialize_combo_boxes(self):
        # Clear existing items from combo boxes
        self.x_combo.clear()
        self.y_combo.clear()

        # Hardcoded list of column names
        column_names = Utils.data_format
        for column_name in column_names:
            self.x_combo.addItem(column_name)
            self.y_combo.addItem(column_name)

    @pyqtSlot(dict)
    def update_graph(self, new_data):
        x_column = self.x_combo.currentText()
        y_columns = self.y_combo.currentData()
        queue_size = self.queue_size_slider.value()
        self.queue_size_label.setText(f"Queue Size: {queue_size}")

        x_values = np.asarray(new_data[x_column]).flatten()
        x_values = x_values[-queue_size:]

        for plot_item in self.plot_items.values():
            if not isinstance(plot_item.y_column, list):
                y_values = np.asarray(new_data[plot_item.y_column]).flatten()
                y_values = y_values[-queue_size:]

                plot_item.data_item.setData(x=x_values, y=y_values)
            else:
                func = plot_item.math_ch
                column_data = [np.asarray(new_data[name])[-queue_size:] for name in plot_item.y_column]
                plot_item.data_item.setData(x=x_values, y=func(*column_data))

    def modify_plots(self, update : bool, return_formulas : list):
        y_columns = self.y_combo.currentData()
        if update:
            func_list, func_list_str, input_variables_list = self.create_lambda_with_variables(return_formulas)
            self.math_channels = func_list_str
        else: 
            func_list, func_list_str, input_variables_list = [], [], []

        for name in list(self.plot_items.keys()):
            plot_item = self.plot_items[name]
            if (plot_item.math_ch is None and plot_item.y_column not in y_columns) or (plot_item.math_ch is not None and plot_item.math_ch_str not in self.math_channels):
                self.plot_widget.removeItem(plot_item.plot_item)
                del self.plot_items[name]
        
        self.plot_widget.update()
        self.plot_widget.clear()
        last_row = len(self.plot_items)
        for y_col in y_columns:
            if y_col in self.plot_items:
                # Update existing plot
                plot_item = self.plot_items[y_col]
                row_idx = list(self.plot_items.keys()).index(y_col) 
                #plot_item.data_item.getViewBox().enableAutoRange(axis='x', enable=True)
                self.plot_widget.ci.addItem(plot_item.plot_item, row=row_idx, col=0)
                #plot_item.data_item.getViewBox().autoRange()
            else:
                # Create new plot
                color = self.rainbow_colors[self.color_index % len(self.rainbow_colors)]
                self.color_index += 1
                plot = self.plot_widget.addPlot(row=last_row, col=0)
                data_item = plot.plot(pen=pg.mkPen(color=color, width=1))
                #data_item.getViewBox().enableAutoRange(axis='x', enable=True)

                # label_item = pg.TextItem(y_col, anchor=(.1, .4))
                # label_item.setFont(QFont("Arial", 10, QFont.Bold))
                # #label_item.setColor(color)
                # plot.addItem(label_item)

                self.plot_items[y_col] = PlotItem(
                    plot_item=plot,
                    data_item=data_item,
                    y_column=y_col,
                    line_color=color,
                    # label_item=label_item
                )
                last_row += 1

        for idx, (func, func_str, input_vars) in enumerate(zip(func_list, func_list_str, input_variables_list)):
            if func_str in self.plot_items:
                continue

            color = self.rainbow_colors[self.color_index % len(self.rainbow_colors)]
            self.color_index += 1
            plot = self.plot_widget.addPlot(row=len(self.plot_items) + idx, col=0)
            data_item = plot.plot(pen=pg.mkPen(color=color, width=1))

            # label_item = pg.TextItem(func_str, anchor=(.1, .4))
            # label_item.setFont(QFont("Arial", 10, QFont.Bold))
            # #label_item.setColor(color)
            # plot.addItem(label_item)

            self.plot_items[func_str] = PlotItem(
                plot_item=plot,
                data_item=data_item,
                y_column=input_vars,
                line_color=color,
                # label_item=label_item,
                math_ch=func,
                math_ch_str=func_str
            )

        if len(self.plot_items) > 1:
            bottom_plot = list(self.plot_items.values())[-1].plot_item
            for item in list(self.plot_items.values())[:-1]:
                item.plot_item.setXLink(bottom_plot)

        self.update_axes_visibility()
        self.refresh_y_list()

    def update_axes_visibility(self):
        """
        This method ensures that only the bottom plot has a visible bottom axis,
        and all other plots have their bottom axis fully hidden.
        """
        if len(self.plot_items) == 0:
            return

        plot_items = list(self.plot_items.values())

        # Hide bottom axis on all but the bottom plot
        for item in plot_items[:-1]:
            plot_item = item.plot_item
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
        bottom_plot = plot_items[-1].plot_item
        bottom_plot.showAxis("bottom", show=True)
        ax = bottom_plot.getAxis("bottom")
        # Show values on the bottom plot
        ax.setStyle(showValues=True)
        # You can customize ticks if necessary, or leave defaults
        bottom_plot.setLabel('bottom', text=self.x_combo.currentText())

    def change_line_color(self, item):
        # Open color dialog and change line color
        new_color = QColorDialog.getColor(initial=item.line_color, parent=self)
        if new_color.isValid():
            item.line_color = new_color
            data_item = item.data_item
            data_item.setPen(pg.mkPen(color=new_color, width=self.thickness_slider.value()))
            self.refresh_y_list()

    def refresh_y_list(self):
        # Clear existing widgets in the layout
        for i in reversed(range(self.y_list_layout.count())):
            item = self.y_list_layout.takeAt(i)
            w = item.widget()
            if w:
                w.deleteLater()

        for plot_item in self.plot_items.values():
            h_layout = QHBoxLayout()

            label_text = plot_item.math_ch_str if plot_item.math_ch else plot_item.y_column
            label = QLabel(str(label_text))
            label.setStyleSheet("font-size: 12px;")
            label.mousePressEvent = lambda event, itm=plot_item: self.show_full_label(itm)

            color_btn = QPushButton()
            color_btn.setFixedSize(20, 20)
            color_btn.setStyleSheet(f"background-color: {plot_item.line_color.name()}; border: 1px solid black;")
            color_btn.clicked.connect(lambda ch, itm=plot_item: self.change_line_color(itm)) 

            h_layout.addWidget(color_btn)
            h_layout.addWidget(label)

            widget_container = QWidget()
            widget_container.setLayout(h_layout)
            self.y_list_layout.addWidget(widget_container)

    def show_full_label(self, item):
        dialog = QDialog(self)
        dialog_layout = QVBoxLayout()
        full_label = QLabel(str(item.math_ch_str) if isinstance(item.y_column, list) else item.y_column)
        full_label.setStyleSheet("font-size: 30px;") 
        dialog_layout.addWidget(full_label)
        dialog.setLayout(dialog_layout)
        dialog.exec_()

    def get_info(self):
        """Returns a dictionary containing the state of the GraphModule."""
        return {
            'type': 'GraphModule',
            'x_axis': self.x_combo.currentText(),
            'y_axis': self.y_combo.currentData(),  # Use currentData() to get selected items
            'color': self.pen.color().name(),
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