import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from utils import LapTimer


class CustomDropList(QListWidget):
    def __init__(self):
        super(CustomDropList, self).__init__()
        self.setAcceptDrops(True)
        self.itemMoved = False

    def dropEvent(self, event):
        super().dropEvent(event)
        self.itemMoved = True

class LapModule(QMainWindow):
    def __init__(self, serialhandler):
        super().__init__()
        self.setWindowTitle("Lap Module")
        self.setGeometry(100, 100, 650, 400)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.main_layout.addLayout(self.layout)

        self.left = QVBoxLayout()
        self.middle = QVBoxLayout()
        self.right = QVBoxLayout()

        self.left.addWidget(QLabel("Lap Timers on Track: "))
        self.middle.addWidget(QLabel("Recent Timestamp: "))
        self.right.addWidget(QLabel("Time Difference: "))
    
        self.lap_timers = {}
        self.lap_timers_list = CustomDropList()
        self.lap_timers_list.setDragEnabled(True)
        self.lap_timers_list.setDragDropOverwriteMode(False)
        self.lap_timers_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lap_timers_list.setDefaultDropAction(Qt.MoveAction)
        self.left.addWidget(self.lap_timers_list)

        self.lap_timers_list.model().rowsMoved.connect(self.update_lists)

        self.lap_global_data_list = QListWidget()
        self.middle.addWidget(self.lap_global_data_list)

        self.lap_relative_data_list = QListWidget()
        self.right.addWidget(self.lap_relative_data_list)

        self.lap_time_label = QLabel("Lap Time: 0.000")
        self.main_layout.addWidget(self.lap_time_label)

        self.zero_button = QPushButton("Zero Out Values")
        self.zero_button.setMaximumWidth(200)
        self.zero_button.clicked.connect(self.zero_out_values)
        self.main_layout.addWidget(self.zero_button)

        self.layout.addLayout(self.left)
        self.layout.addLayout(self.middle)
        self.layout.addLayout(self.right)

        self.serialhandler = serialhandler
        self.serialhandler.timing_data_changed.connect(self.update)

        self.starting_year = None
        self.starting_month = None
        self.starting_day = None
        self.starting_hour = None
        self.starting_minute = None
        self.starting_sec = None
        self.starting_millis = None

    @pyqtSlot(dict)
    def update(self, lap_data):
        if lap_data['Gate Number'][-1] not in self.lap_timers:
            self.lap_timers[lap_data["Gate Number"][-1]] = LapTimer(
                Gate_Number = lap_data["Gate Number"][-1],
                Starting_Year = lap_data["Starting Year"][-1],
                Starting_Month = lap_data["Starting Month"][-1],
                Starting_Day = lap_data["Starting Day"][-1],
                Starting_Hour = lap_data["Starting Hour"][-1],
                Starting_Minute = lap_data["Starting Minute"][-1],
                Starting_Second = lap_data["Starting Second"][-1],
                Starting_Millis = lap_data["Starting Millis"][-1],
                Now_Millis = lap_data["Now Millis"][-1],
                Now_Millis_Minus_Starting_Millis = lap_data["Now Millis Minus Starting Millis"][-1],
                Prev_Now_Millis = 0,
                Prev_Now_Millis_Minus_Starting_Millis=0
            )
            self.lap_timers_list.addItem("Lap Timer - Gate Number: " + str(lap_data['Gate Number'][-1]))
        else:
            self.lap_timers[lap_data["Gate Number"][-1]].Prev_Now_Millis = self.lap_timers[lap_data["Gate Number"][-1]].Now_Millis
            self.lap_timers[lap_data["Gate Number"][-1]].Prev_Now_Millis_Minus_Starting_Millis = self.lap_timers[lap_data["Gate Number"][-1]].Now_Millis_Minus_Starting_Millis
            self.lap_timers[lap_data["Gate Number"][-1]].Now_Millis = lap_data["Now Millis"][-1]
            self.lap_timers[lap_data["Gate Number"][-1]].Now_Millis_Minus_Starting_Millis = lap_data["Now Millis Minus Starting Millis"][-1]

        self.update_lists()

    def update_lists(self):
        items = [self.lap_timers_list.item(x).text() for x in range(self.lap_timers_list.count())]
        self.lap_global_data_list.clear()
        self.lap_relative_data_list.clear()

        for index, item in enumerate(items):
            gate_number = int(item.split(":")[-1].strip())
            if gate_number in self.lap_timers:
                val = str(round(self.lap_timers[gate_number].Now_Millis, 3))
                self.lap_global_data_list.addItem(val)
        
        self.zero_index_item_index = None

        for index, item in enumerate(items):
            gate_number = int(item.split(":")[-1].strip())
            if gate_number in self.lap_timers and index == 0:
                self.lap_relative_data_list.addItem(str(0))
                self.zero_index_item_index = gate_number
            elif gate_number in self.lap_timers and index != 0:
                val = str(round(self.lap_timers[gate_number].Now_Millis - self.lap_timers[self.zero_index_item_index].Now_Millis, 3))
                self.lap_relative_data_list.addItem(val)

        if self.zero_index_item_index is not None and self.lap_timers[self.zero_index_item_index].Prev_Now_Millis != 0:
            lap_time = round(self.lap_timers[self.zero_index_item_index].Now_Millis - self.lap_timers[self.zero_index_item_index].Prev_Now_Millis, 3)
            self.lap_time_label.setText(f"Lap Time: {lap_time}")

    def zero_out_values(self):
        for gate_number in self.lap_timers:
            self.lap_timers[gate_number].Now_Millis = 0
            self.lap_timers[gate_number].Now_Millis_Minus_Starting_Millis = 0
            self.lap_timers[gate_number].Prev_Now_Millis = 0
            self.lap_timers[gate_number].Prev_Now_Millis_Minus_Starting_Millis = 0

        self.update_lists()
        self.lap_time_label.setText("Lap Time: 0.000")