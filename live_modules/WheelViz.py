import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QTransform, QFont, QBrush, QColor
import pyqtgraph as pg
from pyqtgraph import ImageView
import numpy as np
from serialhander import SerialHandler
from utils import ModuleInfo


class WheelViz(QWidget):
    def __init__(self, serialhandler : SerialHandler):
        super().__init__()
        self._cleanup_done = False
        self.setWindowTitle("Wheel Viz")
        self.setGeometry(0, 0, 700, 550)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout2 = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()  
        self.left2_layout = QVBoxLayout()
        self.right2_layout = QVBoxLayout()

        self.serialhander = serialhandler

        self.label = QLabel("Car Visualization")
        self.label.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel(self)
        image = QImage("resources/SDM25_TOP_VIEW_v0.1_KADEN.PNG")
        pixmap = QPixmap("resources/SDM25_TOP_VIEW_v0.1_KADEN.PNG")
        new_width = int(pixmap.width() * .1)
        new_height = int(pixmap.height() * .1)
        pixmap = pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        transformed_pixmap = pixmap.transformed(QTransform().rotate(0))
        self.image_label.setPixmap(transformed_pixmap)

        self.combo_layout = QHBoxLayout()
        self.front_left_combo = QComboBox()
        self.rear_left_combo = QComboBox()
        self.front_right_combo = QComboBox()
        self.rear_right_combo = QComboBox()
        self.front_left_combo.setMaximumSize(150, 30)
        self.rear_left_combo.setMaximumSize(150, 30)
        self.front_right_combo.setMaximumSize(150, 30)
        self.rear_right_combo.setMaximumSize(150, 30)
        self.combo_layout.addWidget(self.front_left_combo)
        self.combo_layout.addWidget(self.rear_left_combo)
        self.combo_layout.addSpacerItem(QSpacerItem(80, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.combo_layout.setStretch(2, 1)
        self.combo_layout.addWidget(self.front_right_combo)
        self.combo_layout.addWidget(self.rear_right_combo)
        self.layout.addLayout(self.combo_layout)
        self.layout.addLayout(self.layout2)

        self.data_options = [
            "Speed (mph)",
            "Brake Temp (C)",
            "Ambient Temperature (C)",
            "Shock Pot (mm)",
        ]

        self.front_left_combo.addItems(self.data_options)
        self.rear_left_combo.addItems(self.data_options)
        self.front_right_combo.addItems(self.data_options)
        self.rear_right_combo.addItems(self.data_options)

        self.layout2.addLayout(self.left_layout)
        self.layout2.addLayout(self.left2_layout)
        self.layout2.addWidget(self.image_label)
        self.layout2.addLayout(self.right_layout)
        self.layout2.addLayout(self.right2_layout)

        self.plot_widget_left_front = pg.PlotWidget()
        self.plot_widget_left_front.setMaximumWidth(100)
        self.plot_widget_left_front.getAxis("bottom").hide()
        self.plot_widget_left_front.getAxis('left').hide()
        self.plot_widget_left_front.setYRange(0,1)
       
        self.plot_widget_left_rear = pg.PlotWidget()
        self.plot_widget_left_rear.setMaximumWidth(100)
        self.plot_widget_left_rear.getAxis("bottom").hide()
        self.plot_widget_left_rear.getAxis("left").hide()
        self.plot_widget_left_rear.setYRange(0,1)

        self.plot_widget_right_front = pg.PlotWidget()
        self.plot_widget_right_front.setMaximumWidth(100)
        self.plot_widget_right_front.getAxis("bottom").hide()
        self.plot_widget_right_front.getAxis("left").hide()
        self.plot_widget_right_front.setYRange(0,1)

        self.plot_widget_right_rear = pg.PlotWidget()
        self.plot_widget_right_rear.setMaximumWidth(100)
        self.plot_widget_right_rear.getAxis("bottom").hide()
        self.plot_widget_right_rear.getAxis("left").hide()
        self.plot_widget_right_rear.setYRange(0,1)

        #adams
        self.plot_widget_left_front_temp = pg.PlotWidget()
        self.plot_widget_left_front_temp.setMaximumWidth(100)
        self.plot_widget_left_front_temp.getAxis("bottom").hide()
        self.plot_widget_left_front_temp.getAxis('left').hide()
        self.plot_widget_left_front_temp.setYRange(0,1)

        self.plot_widget_left_rear_temp = pg.PlotWidget()
        self.plot_widget_left_rear_temp.setMaximumWidth(100)
        self.plot_widget_left_rear_temp.getAxis("bottom").hide()
        self.plot_widget_left_rear_temp.getAxis('left').hide()
        self.plot_widget_left_rear_temp.setYRange(0,1)

        self.plot_widget_right_front_temp = pg.PlotWidget()
        self.plot_widget_right_front_temp.setMaximumWidth(100)
        self.plot_widget_right_front_temp.getAxis("bottom").hide()
        self.plot_widget_right_front_temp.getAxis('left').hide()
        self.plot_widget_right_front_temp.setYRange(0,1)

        self.plot_widget_right_rear_temp = pg.PlotWidget()
        self.plot_widget_right_rear_temp.setMaximumWidth(100)
        self.plot_widget_right_rear_temp.getAxis("bottom").hide()
        self.plot_widget_right_rear_temp.getAxis('left').hide()
        self.plot_widget_right_rear_temp.setYRange(0,1)

        self.left2_layout.addWidget(self.plot_widget_left_front_temp)
        self.left2_layout.addWidget(self.plot_widget_left_rear_temp)
        self.right2_layout.addWidget(self.plot_widget_right_front_temp)
        self.right2_layout.addWidget(self.plot_widget_right_rear_temp)

        self.left_layout.addWidget(self.plot_widget_left_front)
        self.left_layout.addWidget(self.plot_widget_left_rear)
        self.right_layout.addWidget(self.plot_widget_right_front)
        self.right_layout.addWidget(self.plot_widget_right_rear)
        
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

        lf_temp_data = [1]
        lr_temp_data = [1]
        rf_temp_data = [1]  
        rr_temp_data = [1] 
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

        font = QFont()
        font.setPointSize(16)
        font.setBold(True)

        self.left_upper_label = pg.TextItem("label", anchor=(.8, 0.5), color='w')
        self.plot_widget_left_front.addItem(self.left_upper_label)
        self.left_upper_label.setPos(0.2, 0.5)
        self.left_upper_label.setFont(font)

        self.left_lower_label = pg.TextItem("label", anchor=(.8, 0.5), color='w')
        self.plot_widget_left_rear.addItem(self.left_lower_label)
        self.left_lower_label.setPos(0.2, 0.5)
        self.left_lower_label.setFont(font)

        self.right_upper_label = pg.TextItem("label", anchor=(.8, 0.5), color='w')
        self.plot_widget_right_front.addItem(self.right_upper_label)
        self.right_upper_label.setPos(0.2, 0.5)
        self.right_upper_label.setFont(font)

        self.right_lower_label = pg.TextItem("label", anchor=(.8, 0.5), color='w')
        self.plot_widget_right_rear.addItem(self.right_lower_label)
        self.right_lower_label.setPos(0.2, 0.5)
        self.right_lower_label.setFont(font)

        self.left_upper_temp_label = pg.TextItem("label", anchor=(.8, 0.5), color='w')
        self.plot_widget_left_front_temp.addItem(self.left_upper_temp_label)
        self.left_upper_temp_label.setPos(0.2, 0.5)
        self.left_upper_temp_label.setFont(font)

        self.left_lower_temp_label = pg.TextItem("label", anchor=(.8, 0.5), color='w')
        self.plot_widget_left_rear_temp.addItem(self.left_lower_temp_label)
        self.left_lower_temp_label.setPos(0.2, 0.5)
        self.left_lower_temp_label.setFont(font)

        self.right_upper_temp_label = pg.TextItem("label", anchor=(.8, 0.5), color='w')
        self.plot_widget_right_front_temp.addItem(self.right_upper_temp_label)
        self.right_upper_temp_label.setPos(0.2, 0.5)
        self.right_upper_temp_label.setFont(font)

        self.right_lower_temp_label = pg.TextItem("label", anchor=(.8, 0.5), color='w')
        self.plot_widget_right_rear_temp.addItem(self.right_lower_temp_label)
        self.right_lower_temp_label.setPos(0.2, 0.5)
        self.right_lower_temp_label.setFont(font)

        self.last_lf_data = 0
        self.last_lr_data = 0
        self.last_rf_data = 0
        self.last_rr_data = 0
        self.last_lf_temp_data = 0
        self.last_lr_temp_data = 0
        self.last_rf_temp_data = 0
        self.last_rr_temp_data = 0
        self.serialhander.data_changed.connect(self.update_bars)

        self.last_lf_temp_data = 0
        self.last_lr_temp_data = 0
        self.last_rf_temp_data = 0
        self.last_rr_temp_data = 0
        # Delete some stuff
        del lf_data, rf_data, lr_data, rr_data, lf_temp_data, rf_temp_data, lr_temp_data, rr_temp_data


    def get_info(self):
        return ModuleInfo(
            moduleType="WheelViz",
            info={
            'front_left': self.front_left_combo.currentText(),
            'rear_left': self.rear_left_combo.currentText(),
            'front_right': self.front_right_combo.currentText(),
            'rear_right': self.rear_right_combo.currentText(),
            }
        )
    
    def set_info(self, info):
        if 'front_left' in info:
            index = self.front_left_combo.findText(info['front_left'])
            if index >= 0:
                self.front_left_combo.setCurrentIndex(index)
        if 'rear_left' in info:
            index = self.rear_left_combo.findText(info['rear_left'])
            if index >= 0:
                self.rear_left_combo.setCurrentIndex(index)
        if 'front_right' in info:
            index = self.front_right_combo.findText(info['front_right'])
            if index >= 0:
                self.front_right_combo.setCurrentIndex(index)
        if 'rear_right' in info:
            index = self.rear_right_combo.findText(info['rear_right'])
            if index >= 0:
                self.rear_right_combo.setCurrentIndex(index)

    def destructor(self):
            if self._cleanup_done:
                return  # Skip if cleanup is already done
            print("Destructor called, performing cleanup...")
            try:
                self.serialhander.data_changed.disconnect(self.update_bars)
            except (TypeError, AttributeError):
                print("Signal was already disconnected or not connected.")
            # Proceed with the rest of the cleanup
            del (self.layout, self.layout2, self.left_layout,   
                self.right_layout, self.left2_layout, self.right2_layout, self.label, 
                self.image_label, self.plot_widget_left_front, self.plot_widget_left_rear, 
                self.plot_widget_right_front, self.plot_widget_right_rear, 
                self.plot_widget_left_front_temp, self.plot_widget_left_rear_temp, 
                self.plot_widget_right_front_temp, self.plot_widget_right_rear_temp, 
                self.lf_bar, self.lr_bar, self.rf_bar, self.rr_bar, self.lf_temp_bar, 
                self.lr_temp_bar, self.rf_temp_bar, self.rr_temp_bar, self.left_upper_label, 
                self.left_lower_label, self.right_upper_label, self.right_lower_label, self.serialhander,
                self.last_lf_data, self.last_lr_data, self.last_rf_data, 
                self.last_rr_data, self.last_lf_temp_data, self.last_lr_temp_data, 
                self.last_rf_temp_data, self.last_rr_temp_data, self.left_upper_temp_label, 
                self.left_lower_temp_label, self.right_upper_temp_label, self.right_lower_temp_label)
            self._cleanup_done = True
            print("Cleanup complete.")


    def get_color_from_normalized_value(self, normalized_value):
        """Interpolate color between green and red based on the normalized value (0 to 1)."""
        # Ensure the value is between 0 and 1 (though it's already normalized)
        normalized_value = max(0, min(normalized_value, 1))

        # Interpolating between green (0, 255, 0) and red (255, 0, 0)
        red = int(255 * normalized_value)
        green = int(255 * (1 - normalized_value))
        return QColor(red, green, 300)

    @pyqtSlot(dict)
    def update_bars(self, new_data):
        l1_data_label = self.front_left_combo.currentText()
        l2_data_label = self.rear_left_combo.currentText()
        r1_data_label = self.front_right_combo.currentText()
        r2_data_label = self.rear_right_combo.currentText()

        ## I DONT LIKE THIS SOLUTION, FEELS VERY INEFFICIENT
        if l1_data_label == 'Shock Pot (mm)':
            self.plot_widget_left_front.setYRange(-1,1)
            self.plot_widget_left_rear.setYRange(-1,1)
        else:
            self.plot_widget_left_front.setYRange(0,1)
            self.plot_widget_left_rear.setYRange(0,1)
        if l2_data_label == 'Shock Pot (mm)':
            self.plot_widget_left_front_temp.setYRange(-1,1)
            self.plot_widget_left_rear_temp.setYRange(-1,1)
        else:
            self.plot_widget_left_front_temp.setYRange(0,1)
            self.plot_widget_left_rear_temp.setYRange(0,1)
        if r1_data_label == 'Shock Pot (mm)':
            self.plot_widget_right_front.setYRange(-1,1)
            self.plot_widget_right_rear.setYRange(-1,1)
        else:
            self.plot_widget_right_front.setYRange(0,1)
            self.plot_widget_right_rear.setYRange(0,1)
        if r2_data_label == 'Shock Pot (mm)':
            self.plot_widget_right_front_temp.setYRange(-1,1)
            self.plot_widget_right_rear_temp.setYRange(-1,1)
        else:
            self.plot_widget_right_front_temp.setYRange(0,1)
            self.plot_widget_right_rear_temp.setYRange(0,1)
        
        lf_data = new_data["Front Left " + l1_data_label][-1]
        lr_data = new_data["Back Left " + l1_data_label][-1]
        rf_data = new_data["Front Right " + r1_data_label][-1]
        rr_data = new_data["Back Right " + r1_data_label][-1]

        lf_temp_data = new_data["Front Left " + l2_data_label][-1]
        lr_temp_data = new_data["Back Left " + l2_data_label][-1]
        rf_temp_data = new_data["Front Right " + r2_data_label][-1]
        rr_temp_data = new_data["Back Right " + r2_data_label][-1]

        lf_color = self.get_color_from_normalized_value(lf_data)
        lf_temp_color = self.get_color_from_normalized_value(lf_temp_data)
        self.lf_bar.setOpts(height=lf_data, brush=QBrush(lf_color))
        self.lf_temp_bar.setOpts(height=lf_temp_data, brush=QBrush(lf_temp_color))

        lr_color = self.get_color_from_normalized_value(lr_data)
        lr_temp_color = self.get_color_from_normalized_value(lr_temp_data)
        self.lr_bar.setOpts(height=lr_data, brush=QBrush(lr_color))
        self.lr_temp_bar.setOpts(height=lr_temp_data, brush=QBrush(lr_temp_color))

        rf_color = self.get_color_from_normalized_value(rf_data)
        rf_temp_color = self.get_color_from_normalized_value(rf_temp_data)
        self.rf_bar.setOpts(height=rf_data, brush=QBrush(rf_color))
        self.rf_temp_bar.setOpts(height=rf_temp_data, brush=QBrush(rf_temp_color))

        rr_color = self.get_color_from_normalized_value(rr_data)
        rr_temp_color = self.get_color_from_normalized_value(rr_temp_data)
        self.rr_bar.setOpts(height=rr_data, brush=QBrush(rr_color))
        self.rr_temp_bar.setOpts(height=rr_temp_data, brush=QBrush(rr_temp_color))
        

        if l1_data_label == 'Speed (mph)':
            self.lf_bar.setOpts(height=lf_data, brush=(QBrush(QColor("green")) if (lf_data > self.last_lf_data) else QBrush(QColor("red"))))
            self.lr_bar.setOpts(height=lr_data, brush=(QBrush(QColor("green")) if (lr_data > self.last_lr_data) else QBrush(QColor("red"))))
        if l2_data_label == 'Speed (mph)':
            self.lf_temp_bar.setOpts(height=lf_temp_data, brush=(QBrush(QColor("green")) if (lf_data > self.last_lf_data) else QBrush(QColor("red")))) 
            self.lr_temp_bar.setOpts(height=lr_temp_data, brush=(QBrush(QColor("green")) if (lr_data > self.last_lr_data) else QBrush(QColor("red"))))
        if r1_data_label == 'Speed (mph)':
            self.rf_bar.setOpts(height=rf_data, brush=(QBrush(QColor("green")) if (rf_data > self.last_rf_data) else QBrush(QColor("red"))))
            self.rr_bar.setOpts(height=rr_data, brush=(QBrush(QColor("green")) if (rr_data > self.last_rr_data) else QBrush(QColor("red"))))
        if r2_data_label == 'Speed (mph)':
            self.rf_temp_bar.setOpts(height=rf_temp_data, brush=(QBrush(QColor("green")) if (rf_data > self.last_rf_data) else QBrush(QColor("red"))))
            self.rr_temp_bar.setOpts(height=rr_temp_data, brush=(QBrush(QColor("green")) if (rr_data > self.last_rr_data) else QBrush(QColor("red"))))

        self.last_lf_data = lf_data
        self.last_lr_data = lr_data
        self.last_rf_data = rf_data
        self.last_rr_data = rr_data

        self.left_upper_label.setText(str(f"{lf_data:.2f}"))
        self.left_lower_label.setText(str(f"{lr_data:.2f}"))
        self.right_upper_label.setText(str(f"{rf_data:.2f}"))
        self.right_lower_label.setText(str(f"{rr_data:.2f}"))

        self.left_upper_temp_label.setText(str(f"{lf_temp_data:.2f}"))
        self.left_lower_temp_label.setText(str(f"{lr_temp_data:.2f}"))
        self.right_upper_temp_label.setText(str(f"{rf_temp_data:.2f}"))
        self.right_lower_temp_label.setText(str(f"{rr_temp_data:.2f}"))

        self.last_lf_temp_data = lf_temp_data
        self.last_lr_temp_data = lr_temp_data
        self.last_rf_temp_data = rf_temp_data
        self.last_rr_temp_data = rr_temp_data

        del lf_data, rf_data, lr_data, rr_data, lf_temp_data, rf_temp_data, lr_temp_data, rr_temp_data

    def get_color_from_normalized_value(self, normalized_value):
        """Interpolate color between green and red based on the normalized value (0 to 1)."""
        # Ensure the value is between 0 and 1 (though it's already normalized)
        normalized_value = max(0, min(abs(normalized_value), 1))
        # Interpolating between green (0, 255, 0) and red (255, 0, 0)
        red = int(255 * abs(normalized_value))
        green = int(255 * (1 - abs(normalized_value)))
        return QColor(red, green, 0)

    def closeEvent(self, event):
        ## This is a function override, be very careful
        self.destructor() # destructor for all local variables in the class
        event.accept() # This is the function to actually close the window
        