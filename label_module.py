from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from serialhander import SerialHandler
from channel import MathChannelsDialog
import re
from sympy import sympify, lambdify
import numpy as np
from utils import Utils

class LabelModuleWorker(QThread):
    value_updated = pyqtSignal(float)

    def __init__(self, serialhandler, data_type, channel, channel_inputs):
        super().__init__()
        self.serialhandler = serialhandler
        self.data_type = data_type
        self.channel = channel
        self.channel_inputs = channel_inputs
        self.running = True
        self.serialhandler.data_changed.connect(self.process_data)

    @pyqtSlot(dict)
    def process_data(self, new_data):
        if not self.running:
            return

        try:
            if self.channel:
                column_data = []
                for name in self.channel_inputs:
                    column_data.append(np.asarray(new_data[name][-1]))
                latest_val = self.channel(*column_data)
            else:
                latest_val = float(new_data[self.data_type][-1])
            
            self.value_updated.emit(latest_val)
        except Exception as e:
            print(f"Error processing data: {e}")

    def stop(self):
        self.running = False
        self.serialhandler.data_changed.disconnect(self.process_data)
        self.quit()
        self.wait()

class MathChannelWorker(QThread):
    channel_created = pyqtSignal(object, list, list)

    def __init__(self, input_formulas):
        super().__init__()
        self.input_formulas = input_formulas
        self.running = True

    def run(self):
        lambda_func_list, unique_variables_list = self.create_lambda_with_variables(self.input_formulas)
        self.channel_created.emit(lambda_func_list, self.input_formulas, unique_variables_list)

    def create_lambda_with_variables(self, input_formulas):
        def replace_bracket(match):
            var_name = match.group(1)
            return variable_map[var_name]

        lambda_func_list = []
        unique_variables_list = []

        for formula in input_formulas:
            matches = re.findall(r'\[([^\]]+)\]', formula)
            unique_variables = list(set(matches))
            variable_map = {var: f"var_{i}" for i, var in enumerate(unique_variables)}
            modified_string = re.sub(r'\[([^\]]+)\]', replace_bracket, formula)

            sympy_expr = sympify(modified_string)
            lambda_func = lambdify(list(variable_map.values()), sympy_expr)

            lambda_func_list.append(lambda_func)
            unique_variables_list.append(unique_variables)

        return lambda_func_list, unique_variables_list
    
    def stop(self):
        self.quit()
        self.wait()

class DataTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Data Type")
        self.data_types = Utils.data_format

        self.layout = QVBoxLayout(self)
        self.label = QLabel("Choose a data type:")
        self.layout.addWidget(self.label)

        self.data_type_combo = QComboBox(self)
        self.data_type_combo.addItems(self.data_types)
        self.layout.addWidget(self.data_type_combo)
        self.data_type_combo.currentIndexChanged.connect(self.accept)

        self.or_label = QLabel("\nOR\n")
        self.layout.addWidget(self.or_label)

        self.math_channel_button = QPushButton("Select Math CHs")
        self.math_channel_button.clicked.connect(self.open_math_channel)
        self.math_channel_layout = QHBoxLayout()
        self.math_channel_layout.addWidget(self.math_channel_button)
        self.layout.addLayout(self.math_channel_layout)

        self.channel = None
        self.channel_formula = []
        self.channel_inputs = []
        self.channel_worker = None

    def return_selected(self):
        selected_text = self.data_type_combo.currentText()
        return selected_text, selected_text, self.channel, self.channel_formula, self.channel_inputs

    def open_math_channel(self):
        channel_dialog = MathChannelsDialog("label_module")
        if channel_dialog.exec() == QDialog.Accepted:
            self.channel_worker = MathChannelWorker(channel_dialog.return_formula())
            self.channel_worker.channel_created.connect(self.on_channel_created)
            self.channel_worker.start()

    def on_channel_created(self, channels, formulas, inputs):
        self.channel = channels[0]
        self.channel_formula = formulas[0]
        self.channel_inputs = inputs[0]
        self.accept()

    def closeEvent(self, event):
        if self.channel_worker and self.channel_worker.isRunning():
            self.channel_worker.quit()
            self.channel_worker.wait()

        event.accept()  
    
class LabelModule(QWidget):
    def __init__(self, serialhandler: SerialHandler, data_type: str, channel:str=None, channel_formula:list=None, channel_inputs:list=None):
        super().__init__()
        self.serialhandler = serialhandler
        self.data_type = data_type
        self.channel = channel
        self.channel_formula = channel_formula
        self.channel_inputs = channel_inputs

        self.setGeometry(200, 100, 400, 100)
        self.layout = QVBoxLayout(self)

        if self.channel_formula:
            self.data_type_label = QLabel(self.channel_formula)
        else:
            self.data_type_label = QLabel(self.data_type)

        self.data_type_label.setStyleSheet("font-size: 14px;")
        self.layout.addWidget(self.data_type_label)

        self.label = QLabel()
        self.label.setStyleSheet("font-size: 28px;")
        self.layout.addWidget(self.label)

        self.worker = LabelModuleWorker(serialhandler, data_type, channel, channel_inputs)
        self.worker.value_updated.connect(self.update_label)
        self.worker.start()

    @pyqtSlot(float)
    def update_label(self, latest_val):
        self.label.setText(f"{latest_val:.2f}")

    def get_info(self) -> dict:
        return {
            'type': 'LabelModule',
            'data_type': self.data_type
        }

    def set_info(self, info: dict):
        if 'data_type' in info:
            self.data_type = info['data_type']

    def closeEvent(self, event):
        try:
            self.serialhandler.data_changed.disconnect(self.update_label)
        except TypeError as e:
            print("Ran into error trying to exit", e)

        if hasattr(self, 'worker'):
            self.worker.stop()

        if hasattr(self, 'channel_worker') and self.channel_worker.isRunning():
            self.channel_worker.stop()

        event.accept()