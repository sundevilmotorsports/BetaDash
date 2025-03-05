import time
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QSlider

class TimeStamper:
    def __init__(self, init_time=0, max_time=1200, slider=None):
        # Initialize the TimeStamper with an initial timestamp of 630.
        self.time_stamp = init_time
        self.max_time = max_time
        # Create a list to store callback functions that observe changes to the timestamp.
        self._observers = []
        self.slider = slider

        self.slider = QSlider(Qt.Horizontal)

        self.slider.valueChanged.connect(self.slider_moved)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)

    def slider_moved(self, position):
        print(position)
        self.time_stamp = position * (self.max_time / 100)

    def set_init_time(self, init):
        self.time_stamp = init

    def set_max_time(self, max_time):
        self.max_time = max_time

    def time_generator(self):
        while self.time_stamp < int(self.max_time):
            self.time_stamp += 1
            if self.time_stamp > self.max_time:
                self.time_stamp = 0
                print("Yielding frame value:", self.time_stamp)
                yield self.time_stamp
                break
            if self.slider is not None:
                self.slider.setValue(int(self.time_stamp / (self.max_time / 100)))
            print("Yielding frame value:", self.time_stamp)
            yield self.time_stamp