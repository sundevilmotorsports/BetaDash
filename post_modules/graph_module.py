import time
import matplotlib
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from collapsible_module import Collapsible
from checkable_combo import CheckableComboBox
from post_modules.session import Session, SessionManager
from post_modules.timestamper import TimeStamper
#import mpl_interactions.ipyplot as iplt

# Set the Matplotlib backend to Qt5Agg for PyQt5
matplotlib.use("Qt5Agg")

class PostGraphModule(QMainWindow):
    activeXY = [[], []]  # Retained from original MplCanvas

    def __init__(self, timestamper: TimeStamper, session_manager: SessionManager):
        super().__init__()
        self.timestamper = timestamper
        self.session_manager = session_manager

        self.setWindowTitle(" Post Graph Module")
        self.setGeometry(100, 100, 950, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.layout_main = QHBoxLayout()
        self.layout.addLayout(self.layout_main)

        self.fig = Figure()
        self.ax1 = self.fig.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.fig.tight_layout()

        graph_widget = QWidget()
        plot_layout = QVBoxLayout(graph_widget)
        plot_layout.addWidget(self.canvas)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        self.layout_main.addWidget(graph_widget)

        self.sidebox = QVBoxLayout()
        self.sidebox2 = QVBoxLayout()
        self.sidebox.setContentsMargins(0, 0, 0, 0)
        self.sidebox2.setContentsMargins(0, 0, 0, 0)
        self.sidebox.setAlignment(Qt.AlignTop)

        self.dataset_combo = QComboBox()
        # self.dataset_combo.showEvent = lambda _: self.init_metadata()
        self.dataset_combo.currentIndexChanged.connect(self.set_active_data)

        self.x_combo = QComboBox()
        self.x_combo.currentIndexChanged.connect(self.plot_graph)

        self.y_combo = CheckableComboBox(self)
        self.y_combo.setFixedHeight(25)
        self.y_combo.model().dataChanged.connect(self.plot_graph)

        self.sidebox.addWidget(QLabel("Select Dataset:"))
        self.sidebox.addWidget(self.dataset_combo)
        self.sidebox.addWidget(QLabel("Select X Axis Column:"))
        self.sidebox.addWidget(self.x_combo)
        self.sidebox.addWidget(QLabel("Select Y Axis Column:"))
        self.sidebox.addWidget(self.y_combo)

        sideBoxLayout = QVBoxLayout()
        sideBoxLayout.addLayout(self.sidebox)
        sideBoxLayout.addLayout(self.sidebox2)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setMaximumWidth(150)
        self.reset_button.clicked.connect(self.reset)
        sideBoxLayout.addWidget(self.reset_button)

        self.slider_container = QHBoxLayout()
        self.slider_label = QLabel("0: ")
        self.slider_label.setFixedWidth(50)
        self.slider_container.addWidget(self.slider_label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setTickInterval(1)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.valueChanged.connect(self.update_graph_trim)
        self.slider_container.addWidget(self.slider)

        self.window_size_label = QLabel("Adjust Window Size")
        self.sidebox2.addWidget(self.window_size_label)

        self.window_slider = QSlider(Qt.Horizontal)
        self.window_slider.setTickInterval(1)
        self.window_slider.setTickPosition(QSlider.TicksBelow)
        self.window_slider.valueChanged.connect(self.update_graph_trim)
        self.sidebox2.addWidget(self.window_slider)

        self.name_label = QLabel("Name: ")
        self.date_label = QLabel("Date: ")
        self.driver_label = QLabel("Driver: ")
        self.car_label = QLabel("Car: ")
        self.track_label = QLabel("Track: ")

        self.sidebox2.addWidget(self.name_label)
        self.sidebox2.addWidget(self.date_label)
        self.sidebox2.addWidget(self.driver_label)
        self.sidebox2.addWidget(self.car_label)
        self.sidebox2.addWidget(self.track_label)

        self.collapsible_container = Collapsible()
        self.collapsible_container.setContentLayout(sideBoxLayout)
        self.layout_main.addWidget(self.collapsible_container)

        self.bottom_layout = QVBoxLayout()
        self.bottom_layout.addLayout(self.slider_container)
        self.sidebox2.addWidget(self.reset_button)

        self.layout.addLayout(self.bottom_layout)

        # Additional attributes
        self.selected_y_columns = None
        self.selected_x = None
        self.active_dataX = None
        self.ani = None  

        # Initialize combo boxes
        self.set_combo_box()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def set_combo_box(self):
        try:
            names = self.session_manager.get_filenames()
            data = self.session_manager.active_sessions
            self.dataset_combo.clear()
            self.dataset_combo.addItems(names)
            self.x_combo.clear()
            self.y_combo.clear()
            self.active_dataX = data[self.dataset_combo.currentIndex()].data
            self.x_combo.addItems(self.active_dataX.columns.tolist())
            self.y_combo.addItems(self.active_dataX.columns.tolist())
        except Exception as e:
            print("Error setting combo box: ", e)

    def set_active_data(self):
        """Updates the active dataset and repopulates column selections"""
        self.x_combo.clear()
        self.y_combo.clear()
        try:
            self.active_dataX = self.session_manager.active_sessions[self.dataset_combo.currentIndex()].data
            self.x_combo.addItems(self.active_dataX.columns.tolist())
            self.y_combo.addItems(self.active_dataX.columns.tolist())
            
            dataX = self.session_manager.active_sessions[self.dataset_combo.currentIndex()]
            self.name_label.setText(f"Name: {dataX.name}")
            self.date_label.setText(f"Date: {dataX.date}")
            self.driver_label.setText(f"Driver: {dataX.driver}")
            self.car_label.setText(f"Car: {dataX.car}")
            self.track_label.setText(f"Track: {dataX.track}")

            self.timestamper.set_init_time(self.active_dataX[self.x_combo.currentText()].iloc[0])
            self.timestamper.set_max_time(self.active_dataX[self.x_combo.currentText()].iloc[-1])
            x_values = self.active_dataX[self.selected_x].values
            self.slider.setMinimum(int(x_values.min()))
            self.slider.setMaximum(int(x_values.count() - self.window_slider.value() / 2))
            self.slider.setValue(int(self.slider.maximum() / 2))
            self.window_slider.setMinimum(1)
            self.window_slider.setMaximum(int(x_values.count()))
            self.plot_graph()
        except Exception as e:
            print("Error in set_active_data: ", e)

    def update_graph_trim(self, value):
        slider_val = self.slider.value()
        window_val = self.window_slider.value()
        x_min = slider_val - window_val / 2
        x_max = slider_val + window_val / 2

        if x_min == x_max:
            x_max += 1

        self.ax1.set_xlim(x_min, x_max)
        self.canvas.draw()
        self.slider_label.setText(str(slider_val))

    def plot_graph(self):
        """Clears and redraws the graph using the selected x and y columns"""
        try:
            self.selected_x = self.x_combo.currentText()
            self.selected_y_columns = self.y_combo.currentData()

            y_data = self.active_dataX[self.selected_y_columns]
            x_data = self.active_dataX[self.selected_x]

            self.slider.setMinimum(int(x_data.min()))
            self.slider.setMaximum(int(x_data.max() - self.window_slider.value() / 2))
            self.slider.setValue(int(self.slider.maximum() / 2))
            self.window_slider.setMaximum(int(x_data.count()))

            self.ax1.clear()
            for col in self.selected_y_columns:
                self.ax1.plot(x_data, self.active_dataX[col], label=col)
            self.ax1.set_xlabel(self.selected_x)
            self.ax1.set_ylabel(", ".join(self.selected_y_columns))
            self.ax1.set_title(self.selected_x + " vs " + ", ".join(self.selected_y_columns))
            self.ax1.grid()
            if not y_data.empty:
                self.ax1.legend(loc='lower left')
            self.canvas.draw()
        except Exception as e:
            print("Error plotting graph: ", e)

    def play_graph(self):
        """Starts or resumes graph animation using a timestamp generator from the timestamper"""
        try:
            if self.ani is not None and self.ani.event_source is not None:
                self.ani.resume()
                return
            self.ani = animation.FuncAnimation(
                self.fig,
                self.animate,
                frames=self.timestamper.time_generator,
                interval=100,
                repeat=True,
                save_count=50,
                cache_frame_data=True,
            )
            self.canvas.draw()
        except Exception as e:
            print("Error re-drawing graph: ", e)

    def animate(self, timestamp):
        """Animation callback that updates the x-axis limits based on the current timestamp"""
        self.ax1.set_xlim(max(1, timestamp - 100), max(2, timestamp))

    def pause_graph(self):
        """Pauses the animation if it is running"""
        try:
            if self.ani is not None:
                self.ani.pause()
        except Exception as e:
            print("Error pausing graph: ", e)

    def reset(self):
        """Resets the graph by pausing the animation, reloading data, and re-plotting"""
        self.pause_graph()
        self.set_active_data()
        self.plot_graph()

    def play(self):
        """Interface method to start playing the graph animation"""
        self.play_graph()

    def pause(self):
        """Interface method to pause the graph animation"""
        self.pause_graph()

    def clamp(value, min_value, max_value):
        return max(min_value, min(value, max_value))

    def get_info(self):
        return {
            'type': "PostGraphModule",
            'x_axis': self.x_combo.currentText(),
            'y_axis': self.y_combo.currentData(),
            'window_slider': self.window_slider.value(),
            'slider': self.slider.value(),
        }

    def set_info(self, info):
        if 'x_axis' in info:
            index = self.x_combo.findText(info['x_axis'])
            self.x_combo.setCurrentIndex(index)

        if 'y_axis' in info:
            self.y_combo.setCurrentItems(info['y_axis'])

        if 'window_slider' in info:
            self.window_slider.setValue(info['window_slider'])

        if 'slider' in info:
            self.slider.setValue(info['slider'])
        
        self.plot_graph()

    
