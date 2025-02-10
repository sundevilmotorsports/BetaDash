from PyQt5.QtWidgets import *
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

class ggModule(QMainWindow):
    def __init__(self, serialhander : SerialHandler):
        super().__init__()
        self.setWindowTitle("GG Module")
        self.setGeometry(100, 100, 1050, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.plot_widget = pg.PlotWidget()
        '<span style="color: red; font-size: 18px">Y Acceleration (mG) </span>'
        self.plot_widget.setLabel("left",  '<span style="color: gray; font-size: 18px">Y Acceleration (mG) </span>')
        self.plot_widget.setLabel("bottom",  '<span style="color: gray; font-size: 18px">X Acceleration (mG) </span>')
        self.plotItem = pg.ScatterPlotItem(brush=QColor("red"))
        self.plot_widget.addItem(self.plotItem)
        self.crosshair_v = pg.InfiniteLine(angle=90, movable=False,pen=pg.mkPen('gray', width=1))
    
        self.crosshair_h = pg.InfiniteLine(angle=0, movable=False,pen=pg.mkPen('gray', width=1))
        self.plot_widget.addItem(self.crosshair_v, ignoreBounds=True)
        self.plot_widget.addItem(self.crosshair_h, ignoreBounds=True)

        self.serialhandler = serialhander
        self.serialhandler.data_changed.connect(self.update_graph)

        self.layout.addWidget(self.plot_widget)

        self.selected_y_columns = "Y Acceleration (mG)"
        self.selected_x = "X Acceleration (mG)"

        # Queue Size Slider
        self.queue_size_slider = QSlider(Qt.Horizontal)
        self.queue_size_slider.setRange(1, 300) 
        self.queue_size_slider.setValue(300)

        # Label for slider
        self.queue_size_label = QLabel(f"Queue Size: {self.queue_size_slider.value()}")
        self.layout.addWidget(self.queue_size_label)
        self.layout.addWidget(self.queue_size_slider)
        self.layout.setAlignment(self.queue_size_label,Qt.AlignBottom)
        self.layout.setAlignment(self.queue_size_label,Qt.AlignBottom)
 
    @pyqtSlot(dict)
    def update_graph(self, new_data):
        x_column = "X Acceleration (mG)"
        y_column =  "Y Acceleration (mG)"
        queue_size = self.queue_size_slider.value()
        self.queue_size_label.setText(f"Queue Size: {queue_size}")

        x_values = np.asarray(new_data[x_column]).flatten()
        y_values = np.asarray(new_data[y_column]).flatten()
        #self.plot_widget.clear()
        x_values = x_values[-queue_size:]
        y_values = y_values[-queue_size:]
        #self.plot_widget.plot().setData(x=x_values, y=y_values)
       
        # self.plot_widget.plot(x_values,y_values,symbol='o')
        # self.plot_widget.plot(title="PLotssss")
        self.plotItem.setData(x_values,y_values)