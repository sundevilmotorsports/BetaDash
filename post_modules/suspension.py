import pandas as pd
import numpy as np
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QLabel, QPushButton, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from collapsible_module import Collapsible
from post_modules.session import SessionManager

# Use Qt5Agg backend
matplotlib.use("Qt5Agg")

class SuspensionSuite(QMainWindow):
    def __init__(self, session_manager: SessionManager):
        super().__init__()
        self.session_manager = session_manager

        # Window setup
        self.setWindowTitle("Suspension Suite")
        self.setGeometry(100, 100, 950, 600)

        # Central widget & layouts
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.layout_main = QHBoxLayout()
        self.layout.addLayout(self.layout_main)

        # Matplotlib figure & canvas
        self.fig = Figure()
        self.ax1 = self.fig.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.fig.tight_layout()

        graph_widget = QWidget()
        plot_layout = QVBoxLayout(graph_widget)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.addWidget(self.canvas)
        self.layout_main.addWidget(graph_widget)

        # Side panel
        self.sidebox = QVBoxLayout()
        self.sidebox.setContentsMargins(0, 0, 0, 0)
        self.sidebox.setAlignment(Qt.AlignTop)

        # Dataset selector
        self.dataset_combo = QComboBox()
        self.dataset_combo.currentIndexChanged.connect(self.set_active_data)
        self.sidebox.addWidget(QLabel("Select Dataset:"))
        self.sidebox.addWidget(self.dataset_combo)

        # Function selector
        self.function_combo = QComboBox()
        functions = ["None", "Brake Bias", "Brake Plot", "Coasting",
                     "Pitch Gradient", "Steering Input", "Throttle Position",
                     "Understeer Gradient", "Wheel Speed"]
        self.function_combo.addItems(functions)
        self.function_combo.currentIndexChanged.connect(self.update_function)
        self.sidebox.addWidget(QLabel("Select Function:"))
        self.sidebox.addWidget(self.function_combo)

        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.setMaximumWidth(150)
        self.reset_button.clicked.connect(self.reset)
        self.sidebox.addWidget(self.reset_button)

        # Metadata labels
        self.name_label   = QLabel("Name: ")
        self.date_label   = QLabel("Date: ")
        self.driver_label = QLabel("Driver: ")
        self.car_label    = QLabel("Car: ")
        self.track_label  = QLabel("Track: ")
        for w in (self.name_label, self.date_label,
                  self.driver_label, self.car_label, self.track_label):
            self.sidebox.addWidget(w)

        # Collapsible container
        self.collapsible = Collapsible()
        self.collapsible.setContentLayout(self.sidebox)
        self.layout_main.addWidget(self.collapsible)

        # Load initial datasets
        self.set_combo_box()

    def set_combo_box(self):
        try:
            names = self.session_manager.get_filenames()
            sessions = self.session_manager.active_sessions
            self.dataset_combo.clear()
            self.dataset_combo.addItems(names)
            # pre-load first
            self.active_dataX = sessions[0].data
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load datasets:\n{e}")

    def set_active_data(self):
        try:
            idx = self.dataset_combo.currentIndex()
            sess = self.session_manager.active_sessions[idx]
            self.active_dataX = sess.data
            # update metadata
            self.name_label.setText(f"Name: {sess.name}")
            self.date_label.setText(f"Date: {sess.date}")
            self.driver_label.setText(f"Driver: {sess.driver}")
            self.car_label.setText(f"Car: {sess.car}")
            self.track_label.setText(f"Track: {sess.track}")
            # refresh plot
            self.update_function()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to switch dataset:\n{e}")

    def update_function(self):
        """Clear axes, dispatch to the selected function, redraw."""
        self.ax1.clear()
        func = self.function_combo.currentText()
        if func == "Brake Bias":
            self.brake_bias()
        elif func == "Brake Plot":
            self.brake_plot()
        elif func == "Coasting":
            self.coasting()
        # else: leave blank for future functions
        self.canvas.draw()

    def reset(self):
        """Reload data and re-run the current function."""
        self.set_active_data()

    def brake_bias(self):
        """Calculate and plot brake bias over time, then show average."""
        df = self.active_dataX
        t, f, r = 'time (s)', 'f brake pressure (bar)', 'r brake pressure (bar)'
        if not all(c in df.columns for c in (t, f, r)):
            QMessageBox.critical(self, "Data Error",
                                 "Required columns missing for Brake Bias.")
            return

        time_data = df[t]
        front = df[f]
        rear  = df[r]
        total = front.add(rear).mask(lambda x: x == 0)
        bias  = front.div(total)
        avg   = bias.mean(skipna=True)

        self.ax1.plot(time_data, bias, linewidth=1.5)
        self.ax1.set(xlabel="Time (s)",
                     ylabel="Brake Bias",
                     title="Brake Bias Over Time")
        self.ax1.grid(True)
        self.ax1.set_ylim(0, 1)
        self.ax1.legend(["Brake Bias"], loc="best")

        QMessageBox.information(self, "Average Brake Bias",
                                f"{avg:.3f}")

    def brake_plot(self):
        """Plot front brake pressure over time, with stretched x-axis."""
        df = self.active_dataX
        t, f = 'time (s)', 'f brake pressure (bar)'
        if not all(c in df.columns for c in (t, f)):
            QMessageBox.critical(self, "Data Error",
                                 "Required columns missing for Brake Plot.")
            return

        time_data   = df[t]
        front_brake = df[f]

        self.ax1.plot(time_data, front_brake, linewidth=1.5)
        self.ax1.set(xlabel="Time (s)",
                     ylabel="Front Brake Pressure (bar)",
                     title="Front Brake Pressure Over Time")
        self.ax1.grid(True)
        self.ax1.legend(["Front Brake Pressure"], loc="best")
        # stretch x-axis
        self.ax1.set_xlim(time_data.min(), time_data.max())
        self.ax1.set_xticks(
            np.linspace(time_data.min(), time_data.max(), 15)
        )

    def coasting(self):
        """Plot when the vehicle is coasting (throttle load <5% & front brake <6 bar) over time."""
        df = self.active_dataX
        t_col  = 'time (s)'
        tp_col = 'throttle load (adc)'       # updated column name
        fb_col = 'f brake pressure (bar)'

        # Validate columns
        if not all(c in df.columns for c in (t_col, tp_col, fb_col)):
            QMessageBox.critical(self, "Data Error",
                                 f"Missing one of required columns: {t_col}, {tp_col}, {fb_col}")
            return

        time_data = df[t_col]
        tp_load   = df[tp_col]
        fb        = df[fb_col]
        # Depending on your ADC range, you might need to convert to %.
        # If ADC is 0–1023 mapping 0–100%, then:
        coasting_vals = (tp_load < 0.05 * 1023) & (fb < 6)

        self.ax1.plot(time_data, coasting_vals.astype(int), linewidth=1.5)
        self.ax1.set(xlabel="Time (s)",
                     ylabel="Coasting (1 = True, 0 = False)",
                     title="Coasting Condition Over Time")
        self.ax1.grid(True)
        self.ax1.legend(["Coasting"], loc="best")

        # Stretch x-axis
        self.ax1.set_xlim(time_data.min(), time_data.max())
        self.ax1.set_xticks(np.linspace(time_data.min(),
                                         time_data.max(), 10))

    def get_info(self):
        return {
            'type': "SuspensionSuite",
            'function': self.function_combo.currentText()
        }

    def set_info(self, info):
        if 'function' in info:
            self.function_combo.setCurrentText(info['function'])
        self.update_function()
