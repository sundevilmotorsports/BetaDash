from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QPointF, QThread
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

class MathChannelWorker(QThread):
    channel_created = pyqtSignal(object, list, list)

    def __init__(self, input_formulas):
        super().__init__()
        self.input_formulas = input_formulas
        self.running = True

    def run(self):
        lambda_func_list, unique_variables_list = self.create_lambda_with_variables(self.input_formulas)
        self.channel_created.emit(lambda_func_list, self.input_formulas, unique_variables_list)
        # self.stop()

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

        return lambda_func_list, unique_variables_list
    
    def stop(self):
        self.quit()
        self.wait()

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
        self.setWindowTitle(" Graph Module")
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

        self.layout.addWidget(self.plot_widget)
        self.sidebox = QVBoxLayout()
        self.sidebox2 = QVBoxLayout()

        self.sidebox.setAlignment(Qt.AlignTop)
        self.x_combo = QComboBox()
        self.y_combo = CheckableComboBox()
        self.y_combo.model().dataChanged.connect(lambda: self.modify_plots([],[],[]))
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

        self.initialize_combo_boxes()

        self.last_mouse_position = [0, 0]
        #self.plot_widget.scene().sigMouseClicked.connect(self.mouseClicked)
        self.escalation_status = 0
        self.events = []
        self.event_markers = []

        # Put Last to Avoid Errors regarding updating graphs
        self.serialhandler = serialhandler
        self.serialhandler.data_changed.connect(self.update_graph)

    def destructor(self):
        if self._cleanup_done:
            return  # Skip cleanup if already done
        #print("Destructor called, performing cleanup...")
        self.serialhandler.data_changed.disconnect(self.update_graph)
        try:
            self.plot_widget.scene().sigMouseMoved.disconnect(self.mouseMoved)
            self.plot_widget.scene().sigMouseClicked.disconnect(self.mouseClicked)
        except:
            pass

        del (self.central_widget, self.layout, self.plot_widget, 
            self.pen, self.sidebox, self.sidebox2, self.x_combo, self.y_combo,  self.selected_y_columns, 
            self.selected_x,self.last_mouse_position, self.escalation_status,
            self.events, self.event_markers, self.serialhandler)
        self._cleanup_done = True
        #print("Cleanup complete.")

    # def open_math_channel(self):
    #     channel_dialog = MathChannelsDialog("graph_module")
    #     if channel_dialog.exec() == QDialog.Accepted:
    #         self.modify_plots(True, channel_dialog.return_formula())

    def open_math_channel(self):
        channel_dialog = MathChannelsDialog("graph_module")
        if channel_dialog.exec() == QDialog.Accepted:
            self.channel_worker = MathChannelWorker(channel_dialog.return_formula())
            self.channel_worker.channel_created.connect(self.on_channel_created)
            self.channel_worker.start()

    def on_channel_created(self, lambda_func_list, input_formulas, unique_variables_list):
        self.modify_plots(lambda_func_list, input_formulas, unique_variables_list)
            
    def open_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid(): 
            self.pen.setColor(color)
        
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
        # try:
            x_column = self.x_combo.currentText()
            y_columns = self.y_combo.currentData()
            queue_size = self.queue_size_slider.value()
            self.queue_size_label.setText(f"Queue Size: {queue_size}")

            x_values = np.asarray(new_data[x_column]).flatten()
            x_values = x_values[-queue_size:]

            for index, x in enumerate(x_values):
                if(x == 0):
                    # print("Zero x NOT ALLOWED BOZO")
                    np.delete(x_values, index)

            for plot_item in self.plot_items.values():
                if not isinstance(plot_item.y_column, list): # if y_column is a list in the plot item object then its a math channel
                    y_values = np.asarray(new_data[plot_item.y_column]).flatten()
                    y_values = y_values[-queue_size:]
                    plot_item.data_item.setData(x=x_values, y=y_values)
                else:
                    func = plot_item.math_ch
                    column_data = []
                    for name in plot_item.y_column:
                        # print(name, "→", new_data[name], "(type:", type(new_data[name]), ", ndim:", getattr(new_data[name], 'ndim', None), ")") 
                        column_data.append(np.asarray(list(new_data[name])[-queue_size:]))
                    # column_data = [np.asarray(new_data[name])[-queue_size:] for name in plot_item.y_column]
                    if column_data:
                        plot_item.data_item.setData(x=x_values, y=func(*column_data))
                    else:
                        y_values = [func(*column_data) for x in x_values]
                        plot_item.data_item.setData(x=x_values, y=y_values) 
        # except Exception as e:
        #     print("Ploting error: ", e)

    def modify_plots(self, lambda_func_list : list, input_formulas : list, unique_variables_list : list):
        y_columns = self.y_combo.currentData()
        func_list, func_list_str, input_variables_list = lambda_func_list, input_formulas, unique_variables_list

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
                if self.plot_items[y_col].plot_item:
                    # Update existing plot
                    plot_item = self.plot_items[y_col]
                    row_idx = list(self.plot_items.keys()).index(y_col) 
                    #plot_item.data_item.getViewBox().enableAutoRange(axis='x', enable=True)
                    self.plot_widget.ci.addItem(plot_item.plot_item, row=row_idx, col=0)
                    #plot_item.data_item.getViewBox().autoRange()
                else:
                    plot_item = pg.PlotItem()
                    row_idx = list(self.plot_items.keys()).index(y_col) 
                    self.plot_widget.ci.addItem(plot_item, row=row_idx, col=0)
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
        return {
            'type': 'GraphModule',
            'x_axis': self.x_combo.currentText(),
            'plot_items': {
                key: {
                    'y_column': item.y_column,
                    'line_color': item.line_color.name(),
                    'label_item': item.label_item.toPlainText() if item.label_item is not None else None,
                    'x_column_data': item.data_item.getData()[0], 
                    'y_column_data': item.data_item.getData()[1],
                }
                for key, item in self.plot_items.items()
            },
            'queue_size': self.queue_size_slider.value(),
        }

    def set_info(self, info):
        if 'x_axis' in info:
            self.initialize_combo_boxes()
            index = self.x_combo.findText(info['x_axis'])
            self.x_combo.setCurrentIndex(index)

        if 'plot_items' in info:
            self.plot_items = {}
            y_columns = [item.get('y_column') for _, item in info['plot_items'].items()]
            for key, item in info['plot_items'].items():
                if isinstance(item, dict):
                    last_row = len(self.plot_items)
                    plot = self.plot_widget.addPlot(row=last_row, col=0)
                    color = QColor(item.get('line_color'))
                    # x_data = item.get('x_column_data', [])
                    # y_data = item.get('y_column_data', [])
                    data_item = plot.plot(pen=pg.mkPen(color=color, width=1))

                    self.plot_items[key] = PlotItem(
                        plot_item=plot, 
                        data_item=data_item,
                        y_column=item.get('y_column'),
                        line_color=QColor(item.get('line_color')),
                        label_item=item.get('label_item', None),
                        math_ch=None,
                        math_ch_str=None,
                    )
                else:
                    print(f"Warning: Unexpected data format in plot_items: {key} -> {item}")

            self.y_combo.setCurrentItems(y_columns)
            self.modify_plots([], [], [])
        if 'queue_size' in info:
            self.queue_size_slider.setValue(info['queue_size'])

    def get_graph_type(self):
        return "GraphModule"
    
    def closeEvent(self, event):
        ## This is a function override, be very careful
        self.destructor() # destructor for all local variables in the class
        event.accept() # This is the function to actually close the window