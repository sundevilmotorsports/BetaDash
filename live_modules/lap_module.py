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
        self.setGeometry(100, 100, 650, 500)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        self.top_layout = QHBoxLayout()
        self.top_layout.setContentsMargins(0, 0, 0, 0)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.bottom_layout)

        self.left = QVBoxLayout()
        self.middle = QVBoxLayout()
        self.right = QVBoxLayout()
        self.extra_right = QVBoxLayout()

        self.bottom_left = QVBoxLayout()
        self.bottom_right = QVBoxLayout()
        self.bottom_right.setAlignment(Qt.AlignBottom)

        self.left.addWidget(QLabel("Lap Timers on Track: "))
        self.middle.addWidget(QLabel("Recent Timestamp: "))
        self.right.addWidget(QLabel("Time Difference: "))
        self.extra_right.addWidget(QLabel("Sector Times: "))
    
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

        self.lap_first_gate_diff_list = QListWidget()
        self.right.addWidget(self.lap_first_gate_diff_list)

        self.lap_relative_data_list = QListWidget()
        self.extra_right.addWidget(self.lap_relative_data_list)

        self.lap_time_list = QListWidget()
        self.lap_time_list.setMaximumWidth(200)
        font = QFont()
        font.setPointSize(16)
        self.lap_time_list.setFont(font)
        self.bottom_left.addWidget(QLabel("Lap Times: "))
        self.bottom_left.addWidget(self.lap_time_list)

        self.zero_button = QPushButton("Zero Out Values")
        self.zero_button.setMaximumWidth(200)
        self.zero_button.clicked.connect(self.zero_out_values)
        self.bottom_right.addWidget(self.zero_button)

        self.delete_button = QPushButton("Delete Selected Gate")
        self.delete_button.setMaximumWidth(200)
        self.delete_button.clicked.connect(self.delete_selected_gate)
        self.bottom_right.addWidget(self.delete_button)

        self.log_laps_button = QPushButton("Start Logging Laps")
        self.log_laps_button.setMaximumWidth(200)
        self.logging_laps_bool : bool = False
        self.log_laps_button.clicked.connect(self.handle_logging_laps)
        self.bottom_right.addWidget(self.log_laps_button)

        self.top_layout.addLayout(self.left)
        self.top_layout.addLayout(self.middle)
        self.top_layout.addLayout(self.right)
        self.top_layout.addLayout(self.extra_right)

        self.bottom_layout.addLayout(self.bottom_left)
        self.bottom_layout.addLayout(self.bottom_right)

        self.serialhandler = serialhandler
        self.serialhandler.timing_data_changed.connect(self.update)

        self.starting_year = None
        self.starting_month = None
        self.starting_day = None
        self.starting_hour = None
        self.starting_minute = None
        self.starting_sec = None
        self.starting_millis = None

        self.past_lap_time = 0
        self.lap_counter = 0

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
                Starting_Delta = lap_data["Starting Year"][-1] * 31557600000 + lap_data["Starting Month"][-1] * 2629800000 + lap_data["Starting Day"][-1] * 86400000 + lap_data["Starting Hour"][-1] * 3600000 + lap_data["Starting Minute"][-1] * 60000 + lap_data["Starting Second"][-1] * 1000 + lap_data["Starting Millis"][-1],
                Now_Millis = lap_data["Now Millis"][-1],
                Prev_Now_Millis = 0,
            )
            self.lap_timers_list.addItem("Gate Number: " + str(int(lap_data['Gate Number'][-1])))
        else:
            self.lap_timers[lap_data["Gate Number"][-1]].Gate_Number = lap_data["Gate Number"][-1]
            self.lap_timers[lap_data["Gate Number"][-1]].Starting_Year = lap_data["Starting Year"][-1]
            self.lap_timers[lap_data["Gate Number"][-1]].Starting_Month = lap_data["Starting Month"][-1]
            self.lap_timers[lap_data["Gate Number"][-1]].Starting_Day = lap_data["Starting Day"][-1]
            self.lap_timers[lap_data["Gate Number"][-1]].Starting_Hour = lap_data["Starting Hour"][-1]
            self.lap_timers[lap_data["Gate Number"][-1]].Starting_Minute = lap_data["Starting Minute"][-1]
            self.lap_timers[lap_data["Gate Number"][-1]].Starting_Second = lap_data["Starting Second"][-1]
            self.lap_timers[lap_data["Gate Number"][-1]].Starting_Millis = lap_data["Starting Millis"][-1]
            self.lap_timers[lap_data["Gate Number"][-1]].Starting_Delta = lap_data["Starting Year"][-1] * 31557600000 + lap_data["Starting Month"][-1] * 2629800000 + lap_data["Starting Day"][-1] * 86400000 + lap_data["Starting Hour"][-1] * 3600000 + lap_data["Starting Minute"][-1] * 60000 + lap_data["Starting Second"][-1] * 1000 + lap_data["Starting Millis"][-1]
            self.lap_timers[lap_data["Gate Number"][-1]].Now_Millis = lap_data["Now Millis"][-1] + self.lap_timers[lap_data["Gate Number"][-1]].Starting_Delta
            self.lap_timers[lap_data["Gate Number"][-1]].Prev_Now_Millis = self.lap_timers[lap_data["Gate Number"][-1]].Now_Millis

        self.update_lists()

    def update_lists(self):
        items = [self.lap_timers_list.item(x).text() for x in range(self.lap_timers_list.count())]
        time_diffs = [self.lap_first_gate_diff_list.item(x).text() for x in range(self.lap_first_gate_diff_list.count())]
        sector_times = [self.lap_relative_data_list.item(x).text() for x in range(self.lap_relative_data_list.count())]
        self.lap_global_data_list.clear()
        self.lap_first_gate_diff_list.clear()
        self.lap_relative_data_list.clear()

        first_gate_number = int(items[0].split(":")[-1].strip()) if items else None
        last_gate_number = int(items[len(items)-1].split(":")[-1].strip())
        first_starting_time = self.lap_timers[first_gate_number].Starting_Delta
    
        for index, item in enumerate(items):
            gate_number = int(item.split(":")[-1].strip())
            if gate_number in self.lap_timers:
                diff = first_starting_time - self.lap_timers[gate_number].Starting_Delta
                # print("diff: ", diff)
                now_millis = (self.lap_timers[gate_number].Now_Millis - diff)
                # print("now millis minus diff: ", self.lap_timers[gate_number].Converted_Starting_Time + self.lap_timers[gate_number].Now_Millis - diff)
                first_now_millis = (self.lap_timers[first_gate_number].Now_Millis)

                val = str(round((now_millis / 1000), 3))
                self.lap_global_data_list.addItem(val)

                first_gate_diff = round((now_millis - first_now_millis) / 1000, 3)
                self.lap_first_gate_diff_list.addItem(str(first_gate_diff))

                if index == 0:
                    length = len(self.lap_timers_list)
                    if length > 1:
                            shotgun_diff = first_starting_time - self.lap_timers[last_gate_number].Starting_Delta
                            final_sector_val = f"S{length}: " + str(round((now_millis - (self.lap_timers[last_gate_number].Now_Millis - shotgun_diff)) / 1000, 3))
                            
                    # self.lap_relative_data_list.addItem("-")
                    lap_time = round((first_now_millis - (self.lap_timers[first_gate_number].Prev_Now_Millis)) / 1000, 3) 
                    if(lap_time != 0):
                        if lap_time != self.past_lap_time:
                            self.past_lap_time = lap_time
                            self.lap_time_list.insertItem(0, str(lap_time))
                            if self.lap_timers_list.count() > 5:
                                self.list_widget.takeItem(self.list_widget.count() - 1)
                            if self.logging_laps_bool:
                                    self.serialhandler.increment_lap_counter()
                        else:
                            self.past_lap_time = lap_time
                else:
                    prev_gate_number = int(items[index - 1].split(":")[-1].strip())
                    if prev_gate_number in self.lap_timers:
                        shotgun_diff = first_starting_time - self.lap_timers[prev_gate_number].Starting_Delta
                        if index - 1 == 0:
                            val = f"S{index}: " + str(round((now_millis - (self.lap_timers[prev_gate_number].Now_Millis)) / 1000, 3))
                        else:
                            val = f"S{index}: " + str(round((now_millis - (self.lap_timers[prev_gate_number].Now_Millis - shotgun_diff)) / 1000, 3))
                        
                        self.lap_relative_data_list.addItem(val)
                        if final_sector_val:
                            self.lap_relative_data_list.addItem(final_sector_val)
                        
    def zero_out_values(self):
        for gate_number in self.lap_timers:
            self.lap_timers[gate_number].Now_Millis = 0
            self.lap_timers[gate_number].Now_Millis_Minus_Starting_Millis = 0
            self.lap_timers[gate_number].Prev_Now_Millis = 0
            self.lap_timers[gate_number].Prev_Now_Millis_Minus_Starting_Millis = 0

        self.update_lists()
        self.lap_time_label.setText("Lap Time: 0.000")

    def delete_selected_gate(self):
        selected_items = self.lap_timers_list.selectedItems()
        for item in selected_items:
            gate_number = int(item.text().split(":")[-1].strip())
            if gate_number in self.lap_timers:
                del self.lap_timers[gate_number]
            self.lap_timers_list.takeItem(self.lap_timers_list.row(item))
        self.update_lists()

    def handle_logging_laps(self):
        if self.logging_laps_bool:
            self.logging_laps_bool = False
            self.log_laps_button.setText("Start Logging Laps")
        else:
            self.logging_laps_bool = True
            self.log_laps_button.setText("Stop Logging Laps")

    def get_info(self):
        return {
            'type': "LapModule",
            'lap_timers': {
                key: {
                'Gate_Number': item.Gate_Number,
                'Starting_Year': item.Starting_Year,
                'Starting_Month': item.Starting_Month,
                'Starting_Day': item.Starting_Day,
                'Starting_Hour': item.Starting_Hour,
                'Starting_Minute': item.Starting_Minute,
                'Starting_Second': item.Starting_Second,
                'Starting_Millis': item.Starting_Millis,
                'Starting_Delta': item.Starting_Delta,
                'Now_Millis': item.Now_Millis,
                'Now_Millis_Minus_Starting_Millis': item.Now_Millis_Minus_Starting_Millis,
                'Prev_Now_Millis': item.Prev_Now_Millis,
                'Prev_Now_Millis_Minus_Starting_Millis': item.Prev_Now_Millis_Minus_Starting_Millis,
                }
                for key, item in self.lap_timers.items()
            },
            'lap_timers_list': [self.lap_timers_list.item(i).text() for i in range(self.lap_timers_list.count())],
            'logging_laps': self.logging_laps_bool,
        }

    def set_info(self, info):
        if 'lap_timers' in info:
            self.lap_timers_list.clear()
            for key, item in info['lap_timers'].items():
                self.lap_timers[key] = LapTimer(
                    Gate_Number=item["Gate_Number"],
                    Starting_Year=item["Starting_Year"],
                    Starting_Month=item["Starting_Month"],
                    Starting_Day=item["Starting_Day"],
                    Starting_Hour=item["Starting_Hour"],
                    Starting_Minute=item["Starting_Minute"],
                    Starting_Second=item["Starting_Second"],
                    Starting_Millis=item["Starting_Millis"],
                    Starting_Delta=item["Starting_Delta"],
                    Now_Millis=item["Now_Millis"],
                    Now_Millis_Minus_Starting_Millis=item["Now_Millis_Minus_Starting_Millis"],
                    Prev_Now_Millis=item["Prev_Now_Millis"],
                    Prev_Now_Millis_Minus_Starting_Millis=item["Prev_Now_Millis_Minus_Starting_Millis"]
                )
        if 'lap_timers_list' in info:
            self.lap_timers_list.clear()
            for gate_text in info['lap_timers_list']:
                self.lap_timers_list.addItem(gate_text)
                
        if 'logging_laps' in info:
            self.logging_laps_bool = info['logging_laps']

        self.update_lists()

