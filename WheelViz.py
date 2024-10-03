import sys
from PyQt5.QtWidgets import (
    QMainWindow,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QStatusBar,
    QCheckBox,
    QApplication
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QTransform, QFont, QBrush, QColor
import pyqtgraph as pg
from pyqtgraph import ImageView
import numpy as np
from serialhander import SerialHandler

class WheelViz(QMainWindow):
    def __init__(self, serialhandler : SerialHandler):
        super().__init__()
        self.setWindowTitle("WheelViz")
        #self.setGeometry(0, 0, 275, 350)
        self.menubar = self.menuBar()
        self.menubar.setStyleSheet(
            "background-color: #333; color: white; font-size: 14px;"
        )
        self.menubar.setStyleSheet("QMenu::item:selected { background-color: #555; }")
        self.menubar.setStyleSheet("QMenu::item:pressed { background-color: #777; }")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background-color: black;")


        self.layout = QHBoxLayout(self.central_widget)
        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()
        #adams
        self.left2_layout = QVBoxLayout()
        self.right2_layout = QVBoxLayout()

        self.serialhander = serialhandler
        self.serialhander.data_changed.connect(self.update_bars)

        self.label = QLabel("Car Visualization")
        self.label.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel(self)
        image = QImage("resources/th-1942171566.jpg")
        pixmap = QPixmap("resources/th-1942171566.jpg")
        transformed_pixmap = pixmap.transformed(QTransform().rotate(270))
        self.image_label.setPixmap(transformed_pixmap)

        self.layout.addLayout(self.left2_layout)
        self.layout.addLayout(self.left_layout)
        self.layout.addWidget(self.image_label)
        self.layout.addLayout(self.right_layout)
        self.layout.addLayout(self.right2_layout)

        self.plot_widget_left_front = pg.PlotWidget()
        self.plot_widget_left_front.setMaximumWidth(100)
        self.plot_widget_left_front.getAxis("bottom").setStyle(showValues=False)
        self.plot_widget_left_front.setYRange(0,1)

        self.plot_widget_left_rear = pg.PlotWidget()
        self.plot_widget_left_rear.setMaximumWidth(100)
        self.plot_widget_left_rear.getAxis("bottom").setStyle(showValues=False)
        self.plot_widget_left_rear.setYRange(0,1)

        self.plot_widget_right_front = pg.PlotWidget()
        self.plot_widget_right_front.setMaximumWidth(100)
        self.plot_widget_right_front.getAxis("bottom").setStyle(showValues=False)
        self.plot_widget_right_front.setYRange(0,1)

        self.plot_widget_right_rear = pg.PlotWidget()
        self.plot_widget_right_rear.setMaximumWidth(100)
        self.plot_widget_right_rear.getAxis("bottom").setStyle(showValues=False)
        self.plot_widget_right_rear.setYRange(0,1)

        #adams
        self.plot_widget_left_front_temp = pg.PlotWidget()
        self.plot_widget_left_front_temp.setMaximumWidth(100)
        self.plot_widget_left_front_temp.getAxis("bottom").setStyle(showValues=False)
        self.plot_widget_left_front_temp.setYRange(0,1)

        self.plot_widget_left_rear_temp = pg.PlotWidget()
        self.plot_widget_left_rear_temp.setMaximumWidth(100)
        self.plot_widget_left_rear_temp.getAxis("bottom").setStyle(showValues=False)
        self.plot_widget_left_rear_temp.setYRange(0,1)

        self.plot_widget_right_front_temp = pg.PlotWidget()
        self.plot_widget_right_front_temp.setMaximumWidth(100)
        self.plot_widget_right_front_temp.getAxis("bottom").setStyle(showValues=False)
        self.plot_widget_right_front_temp.setYRange(0,1)

        self.plot_widget_right_rear_temp = pg.PlotWidget()
        self.plot_widget_right_rear_temp.setMaximumWidth(100)
        self.plot_widget_right_rear_temp.getAxis("bottom").setStyle(showValues=False)
        self.plot_widget_right_rear_temp.setYRange(0,1)

        #self.layout.addLayout(self.left_layout)
        self.left_layout.addWidget(self.plot_widget_left_front)
        self.left_layout.addWidget(self.plot_widget_left_rear)
        self.right_layout.addWidget(self.plot_widget_right_front)
        self.right_layout.addWidget(self.plot_widget_right_rear)

        #self.layout.addLayout(self.left2_layout)
        self.left2_layout.addWidget(self.plot_widget_left_front_temp)
        self.left2_layout.addWidget(self.plot_widget_left_rear_temp)
        self.right2_layout.addWidget(self.plot_widget_right_front_temp)
        self.right2_layout.addWidget(self.plot_widget_right_rear_temp)

        lf_data = [1]
        lr_data = [1]
        rf_data = [1]  
        rr_data = [1] 

        lf_temp_data = [1]
        lr_temp_data = [1]
        rf_temp_data = [1]  
        rr_temp_data = [1] 

        self.lf_bar = pg.BarGraphItem(x=[0], height=lf_data, width=0.6, brush='w')
        self.lr_bar = pg.BarGraphItem(x=[0], height=lr_data, width=0.6, brush='w')
        self.rf_bar = pg.BarGraphItem(x=[0], height=rf_data, width=0.6, brush='w')
        self.rr_bar = pg.BarGraphItem(x=[0], height=rr_data, width=0.6, brush='w')

        self.lf_temp_bar = pg.BarGraphItem(x=[0], height=lf_data, width=0.6, brush='w')
        self.lr_temp_bar = pg.BarGraphItem(x=[0], height=lr_data, width=0.6, brush='w')
        self.rf_temp_bar = pg.BarGraphItem(x=[0], height=rf_data, width=0.6, brush='w')
        self.rr_temp_bar = pg.BarGraphItem(x=[0], height=rr_data, width=0.6, brush='w')

        self.plot_widget_left_front.addItem(self.lf_bar)
        self.plot_widget_left_rear.addItem(self.lr_bar)
        self.plot_widget_right_front.addItem(self.rf_bar)
        self.plot_widget_right_rear.addItem(self.rr_bar)

        self.plot_widget_left_front_temp.addItem(self.lf_temp_bar)
        self.plot_widget_left_rear_temp.addItem(self.lr_temp_bar)
        self.plot_widget_right_front_temp.addItem(self.rf_temp_bar)
        self.plot_widget_right_rear_temp.addItem(self.rr_temp_bar)

        self.last_lf_data = 0
        self.last_lr_data = 0
        self.last_rf_data = 0
        self.last_rr_data = 0

        self.last_lf_temp_data = 0
        self.last_lr_temp_data = 0
        self.last_rf_temp_data = 0
        self.last_rr_temp_data = 0

    def get_color_from_normalized_value(self, normalized_value):
        """Interpolate color between green and red based on the normalized value (0 to 1)."""
        # Ensure the value is between 0 and 1 (though it's already normalized)
        normalized_value = max(0, min(normalized_value, 1))

        # Interpolating between green (0, 255, 0) and red (255, 0, 0)
        red = int(255 * normalized_value)
        green = int(255 * (1 - normalized_value))
        return QColor(red, green, 0)

    @pyqtSlot(dict)
    def update_bars(self, new_data):
        lf_data = new_data["Front Left Speed (mph)"][-1]
        lr_data = new_data["Back Left Speed (mph)"][-1]
        rf_data = new_data["Front Right Speed (mph)"][-1]
        rr_data = new_data["Back Right Speed (mph)"][-1]

        lf_temp_data = new_data["Front Left Brake Temp (C)"][-1]
        lr_temp_data = new_data["Back Left Brake Temp (C)"][-1]
        rf_temp_data = new_data["Front Right Brake Temp (C)"][-1]
        rr_temp_data = new_data["Back Right Brake Temp (C)"][-1]

        if lf_data > self.last_lf_data:
            #self.lf_bar.setColor("green")
            self.lf_bar.setOpts(height=lf_data, brush=QBrush(QColor("green")))
        else:
            self.lf_bar.setOpts(height=lf_data, brush=QBrush(QColor("red")))
        if lr_data > self.last_lr_data:
            self.lr_bar.setOpts(height=lr_data, brush=QBrush(QColor("green")))
        else:
            self.lr_bar.setOpts(height=lr_data, brush=QBrush(QColor("red")))
        if rf_data > self.last_rf_data:
            self.rf_bar.setOpts(height=rf_data, brush=QBrush(QColor("green")))
        else:
            self.rf_bar.setOpts(height=rf_data, brush=QBrush(QColor("red")))
        if rr_data > self.last_rr_data:
            self.rr_bar.setOpts(height=rr_data, brush=QBrush(QColor("green")))
        else:
            self.rr_bar.setOpts(height=rr_data, brush=QBrush(QColor("red")))



        lf_temp_color = self.get_color_from_normalized_value(lf_temp_data)
        self.lf_temp_bar.setOpts(height=lf_temp_data, brush=QBrush(lf_temp_color))

        lr_temp_color = self.get_color_from_normalized_value(lr_temp_data)
        self.lr_temp_bar.setOpts(height=lr_temp_data, brush=QBrush(lr_temp_color))

        rf_temp_color = self.get_color_from_normalized_value(rf_temp_data)
        self.rf_temp_bar.setOpts(height=rf_temp_data, brush=QBrush(rf_temp_color))

        rr_temp_color = self.get_color_from_normalized_value(rr_temp_data)
        self.rr_temp_bar.setOpts(height=rr_temp_data, brush=QBrush(rr_temp_color))

        self.last_lf_data = lf_data
        self.last_lr_data = lr_data
        self.last_rf_data = rf_data
        self.last_rr_data = rr_data

        self.last_lf_temp_data = lf_temp_data
        self.last_lr_temp_data = lr_temp_data
        self.last_rf_temp_data = rf_temp_data
        self.last_rr_temp_data = rr_temp_data