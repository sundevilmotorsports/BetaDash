from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QThread
from PyQt5.QtGui import QColor, QFont
import pyqtgraph as pg
import numpy as np
import numpy
import time
import serialhander as SerialHandler

class RGModuleWorker(QThread):
    data_processed = pyqtSignal(np.ndarray, np.ndarray, float)

    def __init__(self, serialhandler, x_column, y_column, queue_size=300):
        super().__init__()
        self.serialhandler = serialhandler
        self.x_column = x_column
        self.y_column = y_column
        self.queue_size = queue_size
        self.running = True
        self.serialhandler.data_changed.connect(self.handle_data)

    def run(self):
        while self.running:
            time.sleep(.001)

    @pyqtSlot(dict)
    def handle_data(self, new_data):
        try:
            x_values = np.asarray(new_data[self.x_column]).flatten()
            y_values = np.asarray(new_data[self.y_column]).flatten()

            x_values = x_values[-self.queue_size:] / 1000
            y_values = y_values[-self.queue_size:] / 1000

            if x_values.size > 1 and y_values.size > 1:
                coe = numpy.polyfit(x_values, y_values, 1)
                roll_gradient_value = coe[0]
                self.data_processed.emit(x_values, y_values, roll_gradient_value)
        except Exception as e:
            print(f"Error processing data: {e}")

    def stop(self):
        self.running = False
        self.wait()

class rgModule(QMainWindow):
    def __init__(self, serialhandler: SerialHandler):
        super().__init__()
        self.setWindowTitle("RG Module")
        self.setGeometry(100, 100, 1050, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("left", '<span style="color: gray; font-size: 18px">Roll Angle (Deg) </span>')
        self.plot_widget.setLabel("bottom", '<span style="color: gray; font-size: 18px">Lateral Accel (g) </span>')
        self.layout.addWidget(self.plot_widget)

        self.plotItem = None
        self.lineItem = None

        self.roll_gradient_text = pg.TextItem(text="Roll Gradient: N/A", anchor=(0, 0), color='gray')
        self.roll_gradient_text.setFont(QFont("Arial", 14))
        self.plot_widget.addItem(self.roll_gradient_text)
        self.roll_gradient_text.setPos(0.5, 0.5)

        self.queue_size_slider = QSlider(Qt.Horizontal)
        self.queue_size_slider.setRange(1, 300)
        self.queue_size_slider.setValue(300)

        self.queue_size_label = QLabel(f"Queue Size: {self.queue_size_slider.value()}")
        self.layout.addWidget(self.queue_size_label)
        self.layout.addWidget(self.queue_size_slider)

        self.worker = RGModuleWorker(serialhandler, "X Acceleration (mG)", "Y Gyro (mdps)")
        self.worker.data_processed.connect(self.update_graph)
        self.worker.start()

        self.queue_size_slider.valueChanged.connect(self.update_queue_size)

    def update_queue_size(self, value):
        self.queue_size_label.setText(f"Queue Size: {value}")
        self.worker.queue_size = value

    @pyqtSlot(np.ndarray, np.ndarray, float)
    def update_graph(self, x_values, y_values, roll_gradient_value):
        if self.plotItem:
            self.plot_widget.removeItem(self.plotItem)
        if self.lineItem:
            self.plot_widget.removeItem(self.lineItem)

        self.plotItem = pg.ScatterPlotItem(x_values, y_values, brush=QColor("red"))
        self.plot_widget.addItem(self.plotItem)

        poly = numpy.poly1d(numpy.polyfit(x_values, y_values, 1))
        self.lineItem = self.plot_widget.plot(x_values, poly(x_values), pen='r')
        self.roll_gradient_text.setText(f"Roll Gradient: {roll_gradient_value:.4f}")

        if x_values.size > 0 and y_values.size > 0:
            self.roll_gradient_text.setPos(min(x_values), max(y_values))

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()
