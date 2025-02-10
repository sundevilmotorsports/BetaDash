from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QDialog, QComboBox, QPushButton
)
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QFont
from serialhander import SerialHandler
from channel import MathChannelsDialog
import re
from sympy import symbols, sympify, lambdify
import numpy as np
from utils import Utils


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
        self.math_channel_layout.setContentsMargins(0, 0, 0, 0)
        self.math_channel_layout.setStretch(1, 1)
        self.layout.addLayout(self.math_channel_layout)

        # self.other_label = QLabel("\n")
        # self.layout.addWidget(self.other_label)

        # self.ok_button = QPushButton("OK")
        # self.ok_button.clicked.connect(self.accept)
        # self.layout.addWidget(self.ok_button)

        self.channel = None
        self.channel_formula = []
        self.channel_inputs = []

    def return_selected(self):
        selected_text = self.data_type_combo.currentText()
        return selected_text, selected_text, self.channel, self.channel_formula, self.channel_inputs

    def open_math_channel(self):
        channel_dialog = MathChannelsDialog("label_module")
        if channel_dialog.exec() == QDialog.Accepted:
            self.channel = channel_dialog.return_formula()
            self.channel, self.channel_formula, self.channel_inputs = self.create_lambda_with_variables(self.channel)
            # convert from list of size 1 to just func
            if len(self.channel) >= 1:
                self.channel = self.channel[0]
                self.channel_formula = self.channel_formula[0]
                self.channel_inputs = self.channel_inputs[0]
            self.accept()
       
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
        return lambda_func_list, input_formulas, unique_variables_list

class LabelModule(QWidget):
    def __init__(self, serialhandler: SerialHandler, data_type: str, channel:str = None, channel_formula:list = None, channel_inputs:list = None):
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
            self.data_type_label.setStyleSheet("font-size: 14px;")
            self.layout.addWidget(self.data_type_label)
        else:
            self.data_type_label = QLabel(self.data_type)
            self.data_type_label.setStyleSheet("font-size: 14px;")
            self.layout.addWidget(self.data_type_label)

        self.label = QLabel()
        self.label.setStyleSheet("font-size: 28px;")
        self.layout.addWidget(self.label)
        
        self.serialhandler.data_changed.connect(self.update_label)

    @pyqtSlot(dict)
    def update_label(self, new_data: dict):
        if self.channel:
            column_data = [np.asarray(new_data[name][-1]) for name in self.channel_inputs]
            latest_val = self.channel(*column_data)
            self.label.setText(f"{latest_val:.2f}")
        else:
            latest_val = new_data[self.data_type][-1]
            self.label.setText(f"{latest_val:.2f}")

    def get_info(self) -> dict:
        """
        Returns a dictionary describing the current state,
        so the dashboard can save/restore it.
        """
        return {
            'type': 'LabelModule',      # to identify the module type
            'data_type': self.data_type
            # If you also want position/size:
            # 'pos': (self.x(), self.y()),
            # 'size': (self.width(), self.height())
        }

    def set_info(self, info: dict):
        """
        Takes a state dictionary (like one generated by get_info)
        and applies it to this LabelModule, so it restores its state.
        """
        if 'data_type' in info:
            self.data_type = info['data_type']

        # If you also store geometry, you can restore it:
        # if 'pos' in info and len(info['pos']) == 2:
        #     self.move(info['pos'][0], info['pos'][1])
        # if 'size' in info and len(info['size']) == 2:
        #     self.resize(info['size'][0], info['size'][1])

        # Optionally trigger a label update if your data already exists
        self.update_label(self.serialhandler.data)
