import pandas as pd
import numpy as np
import matplotlib
from scipy.interpolate import PchipInterpolator
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

        # Metadata labels
        self.name_label   = QLabel("Name: ")
        self.date_label   = QLabel("Date: ")
        self.driver_label = QLabel("Driver: ")
        self.car_label    = QLabel("Car: ")
        self.track_label  = QLabel("Track: ")
        for w in (self.name_label, self.date_label,
                  self.driver_label, self.car_label, self.track_label):
            self.sidebox.addWidget(w)
        self.sidebox.addWidget(self.reset_button)

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
        elif func == "Pitch Gradient":
            self.pitch_gradient()
        elif func == "Steering Input":
            self.steering_input()
        elif func == "Throttle Position":
            self.throttle_position()
        elif func == "Understeer Gradient":
            self.understeer_gradient()
        elif func == "Wheel Speed":
            self.wheel_speed()
        self.canvas.draw()

    def reset(self):
        """Reload data and re-run the current function."""
        self.set_active_data()

    def brake_bias(self):
        """Calculate and plot brake bias over time, then show average."""
        df = self.active_dataX
        t = self._col(df, ['time (s)', 'TS', 'Unnamed: 0', 'Time (s)'])
        f = self._col(df, ['f brake pressure (bar)', 'F_BRAKEPRESSURE', 'LR brake line pressure (bar)'])
        r = self._col(df, ['r brake pressure (bar)', 'R_BRAKEPRESSURE', 'RR brake line pressure (bar)'])
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
        t = self._col(df, ['time (s)', 'TS', 'Unnamed: 0', 'Time (s)'])
        f = self._col(df, ['f brake pressure (bar)', 'F_BRAKEPRESSURE', 'LR brake line pressure (bar)'])
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
        t_col = self._col(df, ['time (s)', 'TS', 'Unnamed: 0', 'Time (s)'])
        adc_col = self._col(df, ['throttle load (adc)', 'THROTTLE_LOAD', 'Throttle (%)'])
        fb_col = self._col(df, ['f brake pressure (bar)', 'F_BRAKEPRESSURE', 'LR brake line pressure (bar)'])

        # Validate columns
        if not all(c in df.columns for c in (t_col, adc_col, fb_col)):
            QMessageBox.critical(self, "Data Error",
                                 f"Missing one of required columns: {t_col}, {adc_col}, {fb_col}")
            return

        time_data = df[t_col]
        tp_load   = df[adc_col]
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

    def pitch_gradient(self):
        df = self.active_dataX
        p_col = self._col(df, ['xgyro (mdps)', 'IMU_X_GYRO'])
        g_col = self._col(df, ['longitudinal accel (mG)', 'IMU_X_ACCEL', 'Longitudinal Acceleration (g)'])

        if not all(c in df.columns for c in (p_col, g_col)):
            QMessageBox.critical(self, "Data Error",
                                 f"Missing columns: {p_col}, {g_col}")
            return

        pitch = df[p_col].to_numpy()
        longg = df[g_col].to_numpy()

        # Subsampling: step = 100 ms / 2.4 ms ≈ 41.67 → round to 42 samples
        step = int(round(100.0 / 2.4))
        indices = np.arange(0, len(pitch), step)

        subsampled_pitch = pitch[indices]
        subsampled_longg = longg[indices]

        # Scatter plot
        self.ax1.scatter(subsampled_longg, subsampled_pitch, s=10)
        self.ax1.set(xlabel="Longitudinal Acceleration (mG)",
                     ylabel="Pitch Angle (xgyro, mdps)",
                     title="Pitch Gradient: Pitch Angle vs. Longitudinal Acceleration")
        self.ax1.grid(True)
        self.ax1.legend(["Subsampled Data"], loc="best")

    def steering_input(self):
        df = self.active_dataX
        t_col = self._col(df, ['time (s)', 'TS', 'Unnamed: 0', 'Time (s)'])
        s_col = self._col(df, ['steering (degrees)', 'STEERING', 'Steering Angle (rad)'])

        # Validate columns
        if not all(c in df.columns for c in (t_col, s_col)):
            QMessageBox.critical(self, "Data Error",
                                 f"Missing columns: {t_col}, {s_col}")
            return

        time_data = df[t_col]
        raw_steer  = df[s_col]

        is_adc = 'adc' in s_col.lower() or s_col.upper() == 'STEERING'
        if is_adc:
            # Convert ADC (0–1023) to degrees: map 0→–124°, 1023→+124°
            steering = (raw_steer / 1023.0) * 248.0 - 124.0
        else:
            steering = raw_steer

        # Plot
        self.ax1.plot(time_data, steering, linewidth=1.5)
        self.ax1.set(xlabel="Time (s)",
                     ylabel="Steering Angle (°, +Right / -Left)",
                     title="Steering Input Over Time")
        self.ax1.grid(True)

        # Stretch x-axis
        self.ax1.set_xlim(time_data.min(), time_data.max())
        self.ax1.set_xticks(np.linspace(time_data.min(),
                                         time_data.max(), 10))

        # ± full steering lock at ±124°
        self.ax1.set_ylim(-124, 124)
        self.ax1.set_yticks(np.arange(-124, 125, 31))

        self.ax1.legend(["Steering Angle"], loc="best")

    def throttle_position(self):
        df = self.active_dataX
        t_col  = self._col(df, ['time (s)', 'TS', 'Unnamed: 0', 'Time (s)'])
        adc_col = self._col(df, ['throttle load (adc)', 'THROTTLE_LOAD', 'Throttle (%)'])

        # Validate presence
        if t_col not in df.columns or adc_col not in df.columns:
            QMessageBox.critical(self, "Data Error",
                f"Missing '{adc_col}' or '{t_col}' column for Throttle Position.")
            return

        time_data = df[t_col].to_numpy()
        raw_adc   = df[adc_col].to_numpy()

        # Convert ADC (0–1023) to percent
        thr_pct = 100.0 * raw_adc / 1023.0

        # Plot
        self.ax1.plot(time_data, thr_pct, linewidth=1.5)
        self.ax1.set(xlabel="Time (s)",
                     ylabel="Throttle Position (%)",
                     title="Throttle Position Over Time")
        self.ax1.grid(True)
        self.ax1.legend(["Throttle Position (%)"], loc="best")

    def understeer_gradient(self):
        """
        % Understeer_Gradient - Interpolates wheel displacement vs. steering angle
        % using live data columns. Supports steering in degrees or raw ADC.
        """
        df = self.active_dataX

        # Resolve columns
        steer_col = self._col(df, [
            'steering (degrees)',  # explicit degrees
            'STEERING',            # uppercase ADC
            'steering (adc)',      # explicit ADC
        ])
        left_col  = self._col(df, ['fl displacement (mm)', 'FLSHOCK'])
        right_col = self._col(df, ['fr displacement (mm)', 'FRSHOCK'])
        if not all((steer_col, left_col, right_col)):
            QMessageBox.critical(self, "Data Error",
                "Understeer Gradient needs steering, FL displacement, and FR displacement columns.")
            return

        raw_steer = df[steer_col].to_numpy()
        left      = df[left_col].to_numpy()
        right     = df[right_col].to_numpy()

        # Determine if steering is ADC: column name contains 'adc' or is exactly 'STEERING'
        is_adc = 'adc' in steer_col.lower() or steer_col.upper() == 'STEERING'
        if is_adc:
            # Convert ADC (0–1023) to degrees: map 0→–124°, 1023→+124°
            steer = (raw_steer / 1023.0) * 248.0 - 124.0
        else:
            steer = raw_steer

        # Drop NaNs
        valid = ~np.isnan(steer) & ~np.isnan(left) & ~np.isnan(right)
        steer = steer[valid]
        left  = left[valid]
        right = right[valid]

        # Sort & unique
        idx = np.argsort(steer)
        steer, left, right = steer[idx], left[idx], right[idx]
        _, uniq = np.unique(steer, return_index=True)
        steer, left, right = steer[uniq], left[uniq], right[uniq]

        # Dense steering range in degrees
        s_dense = np.linspace(steer.min(), steer.max(), 500)

        # PCHIP interpolation
        p_left  = PchipInterpolator(steer, left)(s_dense)
        p_right = PchipInterpolator(steer, right)(s_dense)
        p_avg   = 0.5 * (p_left + p_right)

        # Plot
        self.ax1.plot(s_dense, p_left,  '.', linewidth=1.5, label='FL Disp (mm)')
        self.ax1.plot(s_dense, p_right, '.', linewidth=1.5, label='FR Disp (mm)')
        self.ax1.plot(s_dense, p_avg,   '-', linewidth=2,  label='Avg Disp (mm)')

        self.ax1.set(
            xlabel="Steering Angle (°)",
            ylabel="Wheel Displacement (mm)",
            title="Understeer Gradient: Disp vs Steering"
        )
        self.ax1.grid(True)
        self.ax1.legend(loc="best")


    def wheel_speed(self):
        df = self.active_dataX
        t_col  = self._col(df, ['time (s)', 'TS', 'Unnamed: 0', 'Time (s)'])
        fl_col = self._col(df, ['fl wheel speed (rpm)', 'FLW_RPM'])
        fr_col = self._col(df, ['fr wheel speed (rpm)', 'FRW_RPM'])
        rl_col = self._col(df, ['rl wheel speed (rpm)', 'RLW_RPM'])
        rr_col = self._col(df, ['rr wheel speed (rpm)', 'RRW_RPM'])

        # Validate presence
        for c in (t_col, fl_col, fr_col, rl_col, rr_col):
            if c not in df.columns:
                QMessageBox.critical(self, "Data Error",
                    f"Missing column '{c}' for Wheel Speed.")
                return

        time_data = df[t_col].to_numpy()
        fl = df[fl_col].to_numpy()
        fr = df[fr_col].to_numpy()
        rl = df[rl_col].to_numpy()
        rr = df[rr_col].to_numpy()

        # Validate lengths
        n = len(time_data)
        if not all(len(arr) == n for arr in (fl, fr, rl, rr)):
            QMessageBox.critical(self, "Data Error",
                "Wheel speed and time columns must all have the same length.")
            return

        # Plot each channel
        self.ax1.plot(time_data, fl, linewidth=1.5, label='Front Left')
        self.ax1.plot(time_data, fr, linewidth=1.5, label='Front Right')
        self.ax1.plot(time_data, rl, linewidth=1.5, label='Rear Left')
        self.ax1.plot(time_data, rr, linewidth=1.5, label='Rear Right')

        self.ax1.set(xlabel="Time (s)",
                     ylabel="Wheel Speed (rpm)",
                     title="Wheel Speeds Over Time")
        self.ax1.grid(True)
        self.ax1.legend(loc="best")

        # Stretch x-axis
        self.ax1.set_xlim(time_data.min(), time_data.max())
        self.ax1.set_xticks(
            np.linspace(time_data.min(), time_data.max(), 10)
        )

    def _col(self, df: pd.DataFrame, candidates: list) -> str:
        for name in candidates:
            if name in df.columns:
                return name
        return None

    def _filter_xy(self, x: pd.Series, y: pd.Series, y_name: str) -> (pd.Series, pd.Series):
        mask = ~((x == 0) & (y == 0))
        if 'gps' not in y_name.lower():
            mask &= x.abs() <= 1e7
            mask &= y.abs() <= 1e7
        return x[mask], y[mask]

    def get_info(self):
        return {
            'type': "SuspensionSuite",
            'dataset': self.dataset_combo.currentText(),
            'function': self.function_combo.currentText()
        }

    def set_info(self, info):
        if 'function' in info:
            self.function_combo.setCurrentText(info['function'])
        if 'dataset' in info:
            self.dataset_combo.setCurrentText(info['dataset'])
        self.update_function()
