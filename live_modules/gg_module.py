from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QThread
from PyQt5.QtGui import QColor
import pyqtgraph as pg
import numpy as np
import time
import serialhander as SerialHandler

class GGModuleWorker(QThread):
    data_processed = pyqtSignal(np.ndarray, np.ndarray)

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
            time.sleep(0.001)

    @pyqtSlot(dict)
    def handle_data(self, new_data):
        try:
            x_values = np.asarray(new_data[self.x_column]).flatten()
            y_values = np.asarray(new_data[self.y_column]).flatten()

            x_values = x_values[-self.queue_size:] / 1000
            y_values = y_values[-self.queue_size:] / 1000

            if x_values.size > 1 and y_values.size > 1:
                self.data_processed.emit(x_values, y_values)
        except Exception as e:
            print(f"Error processing data: {e}")

    def update_queue_size(self, value):
        self.queue_size = value

    def stop(self):
        self.running = False
        self.wait()

class ggModule(QMainWindow):
    def __init__(self, serialhandler: SerialHandler):
        super().__init__()
        self.setWindowTitle("GG Module")
        self.setGeometry(100, 100, 1050, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("left", '<span style="color: gray; font-size: 18px">Y Acceleration (mG) </span>')
        self.plot_widget.setLabel("bottom", '<span style="color: gray; font-size: 18px">X Acceleration (mG) </span>')
        self.layout.addWidget(self.plot_widget)

        self.plotItem = pg.ScatterPlotItem(brush=QColor("red"))
        self.plot_widget.addItem(self.plotItem)

        self.crosshair_v = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('gray', width=1))
        self.crosshair_h = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('gray', width=1))
        self.plot_widget.addItem(self.crosshair_v, ignoreBounds=True)
        self.plot_widget.addItem(self.crosshair_h, ignoreBounds=True)

        self.queue_size_slider = QSlider(Qt.Horizontal)
        self.queue_size_slider.setRange(1, 300)
        self.queue_size_slider.setValue(300)
        self.queue_size_slider.valueChanged.connect(self.update_queue_size)

        self.queue_size_label = QLabel(f"Queue Size: {self.queue_size_slider.value()}")
        self.layout.addWidget(self.queue_size_label)
        self.layout.addWidget(self.queue_size_slider)

        self.worker = GGModuleWorker(serialhandler, "X Acceleration (mG)", "Y Acceleration (mG)")
        self.worker.data_processed.connect(self.update_graph)
        self.worker.start()

    def update_queue_size(self, value):
        self.queue_size_label.setText(f"Queue Size: {value}")
        self.worker.update_queue_size(value)

    @pyqtSlot(np.ndarray, np.ndarray)
    def update_graph(self, x_values, y_values):
        self.plotItem.setData(x_values, y_values)

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()
