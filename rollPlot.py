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
import numpy
class rollPlot(QMainWindow):
    def __init__(self, serialhander : SerialHandler):
        super().__init__()
        self._cleanup_done = False
        self.setWindowTitle("GG Plot")
        self.setGeometry(100, 100, 1050, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.plot_widget = pg.PlotWidget()
        '<span style="color: red; font-size: 18px">Y Acceleration (mG) </span>'
        self.plot_widget.setLabel("left",  '<span style="color: white; font-size: 18px">Roll Angle (Deg) </span>')
        self.plot_widget.setLabel("bottom",  '<span style="color: white; font-size: 18px">Lateral Accel (g) </span>')
        self.plot_widget.setWindowTitle("GG Plot")
        self.plotItem = pg.ScatterPlotItem(brush=QColor("red"))
        self.plot_widget.addItem(self.plotItem)

        
    
        

        

        self.serialhandler = serialhander
        self.serialhandler.data_changed.connect(self.update_graph)

        self.layout.addWidget(self.plot_widget)
        

        

        self.selected_y_columns = "Y Gyro (mdps)"
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

        

        # self.sideBoxLayout = QVBoxLayout()
        # self.sideBoxLayout.addLayout(self.sidebox)
        # self.sideBoxLayout.addLayout(self.sidebox2)
        
        #self.layout.addLayout(self.sidebox)

        #self.reset_button = QPushButton("Reset")
        #self.reset_button.clicked.connect(self.reset)

       

        self.graph_indice = 0
        self.x_axis_offset = 30
        self.y_axis_offset = 0
        self.end_offset = 0

        self.graph_point_count = 0
        self.max_point = 300
 

    @pyqtSlot(dict)
    def update_graph(self, new_data):
        self.plot_widget.clear()
        x_column = "X Acceleration (mG)"
        y_column =  "Y Gyro (mdps)"
        queue_size = self.queue_size_slider.value()
        self.queue_size_label.setText(f"Queue Size: {queue_size}")

        x_values = np.asarray(new_data[x_column]).flatten()
        y_values = np.asarray(new_data[y_column]).flatten()
        #self.plot_widget.clear()
        x_values = x_values[-queue_size:] / 1000
        y_values = y_values[-queue_size:] / 1000
        scatter = pg.ScatterPlotItem(x_values,y_values,brush=QColor("red"))
        self.plot_widget.addItem(scatter)
        
        coe = numpy.polyfit(x_values,y_values,1)
        poly = numpy.poly1d(coe)
        
        #self.plot_widget.plot().setData(x=x_values, y=y_values)
       
        # self.plot_widget.plot(x_values,y_values,symbol='o')
        # self.plot_widget.plot(title="PLotssss")
        

        
        
        self.arrY = [poly(x) for x in x_values]
    
        self.plot_widget.plot(x_values,self.arrY,pen='r')
       
           
        
 
    

    
    



    
    