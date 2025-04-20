from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QCheckBox, 
    QComboBox, QSpinBox, QTextEdit, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
import sys
import qdarkstyle
from qdarkstyle.dark.palette import DarkPalette  # noqa: E402
from qdarkstyle.light.palette import LightPalette  # noqa: E402
import pickle
from utils import Utils

class MathChannelsDialog(QDialog):
    def __init__(self, source : str):
        super().__init__()
        self.setWindowTitle("Math Channelz")
        self.setGeometry(100, 100, 1200, 800)
        self.source = source # details where the event is coming from
        main_layout = QHBoxLayout(self)

        self.failed_usage = False
        self.setStyleSheet(qdarkstyle.load_stylesheet(palette=LightPalette))
        with open("resources/stylesheets/light_styling.qss", "r") as f:
            self.setStyleSheet(self.styleSheet() + f.read())

        self.channel_parameters = {
            # "Temp1": {"name": "Temp1", "unit": "Celsius", "formula": "[X Acceleration (mG)] + 20", "checked": False},
            # "Temp2": {"name": "Temp2", "unit": "Celsius",  "formula": "[X Acceleration (mG)] + 30", "checked": False},
            # "Temp3": {"name": "Temp3", "unit": "Fahrenheit", "formula": "[X Acceleration (mG)] + 40", "checked": False},
        }
        self.constants = {
            # "KM2MI": {"name": "KM2MI", "value": 0.621371},
            # "MI2KM": {"name": "MI2KM", "value": 1.60934},
            # "KMH2MS": {"name": "KMH2MS", "value": 0.277778},
            # "MS2KMH": {"name": "MS2KMH", "value": 3.6},
            # "MI2FT": {"name": "MI2FT", "value": 5280.0},
            # "π": {"name": "π", "value": 3.14159},
            # "c": {"name": "speed of light", "value": 299792458} # m/s
        }

        # Saved Channelz
        general_group = QGroupBox("Saved Channels")
        general_layout = QHBoxLayout()
        general_channel_layout = QVBoxLayout()
        general_layout_container = QVBoxLayout()
        label = QLabel("Use Checkbox to Select Channels in Add to Graph")
        label.setStyleSheet("""
            QLabel {
                font-size: 12px;}
            """)
        general_layout_container.addWidget(label)
        general_layout_container.addLayout(general_layout)
        self.channels_list = QListWidget()
        for channel in self.channel_parameters.keys():
            self.channels_list.addItem(channel)
        general_channel_layout.addWidget(self.channels_list)
        button_layout = QHBoxLayout()
        self.insert_button = QPushButton("New")
        self.delete_button = QPushButton("Delete")

        self.active_channel_layout = QVBoxLayout()
        self.active_channel_layout.setAlignment(Qt.AlignTop)
        self.active_channel_layout.setContentsMargins(0, 0, 0, 0)
        self.active_channel_layout.setSpacing(0)
        # spacer = QSpacerItem(1, 4, QSizePolicy.Minimum, QSizePolicy.Fixed)
        # self.active_channel_layout.addSpacerItem(spacer)    
    
        button_layout.addWidget(self.insert_button)
        button_layout.addWidget(self.delete_button)
        general_layout.addLayout(self.active_channel_layout)
        general_layout.addLayout(general_channel_layout)
        general_layout_container.addLayout(button_layout)
        general_group.setLayout(general_layout_container)

        # Middle layout (Channel Parameters)
        parameters_group = QGroupBox("Channel parameters")
        parameters_layout = QVBoxLayout()
        parameters_layout.setAlignment(Qt.AlignTop)
        self.channel_name_label = QLabel("Channel name:")
        self.channel_name_edit = QLineEdit()
        # self.channel_plot_label = QLabel("Channel Applies To: ")
        # self.channel_plot_combo = QComboBox()
        # self.channel_plot_combo.addItem("None")
        self.unit_label = QLabel("Unit of measure:")
        self.unit_edit = QLineEdit()

        # Adding widgets to parameters_layout
        parameters_layout.addWidget(self.channel_name_label)
        parameters_layout.addWidget(self.channel_name_edit)
        # parameters_layout.addWidget(self.channel_plot_label)
        # parameters_layout.addWidget(self.channel_plot_combo)
        parameters_layout.addWidget(self.unit_label)
        parameters_layout.addWidget(self.unit_edit)
        parameters_group.setLayout(parameters_layout)

        column_names = Utils.data_format

        # Formula construction
        formula_group = QGroupBox("Formula construction")
        formula_layout = QHBoxLayout()

        # Constants Layout
        constants_layout = QVBoxLayout()
        constants_label = QLabel("Constants:")
        self.constants_list = QListWidget()
        for constant in self.constants.keys():
            self.constants_list.addItem(constant)
        self.variables_list = QListWidget()

        name_layout = QHBoxLayout()
        name_label = QLabel("Name: ")
        self.name_box = QLineEdit("Constant Name")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_box)

        value_layout = QHBoxLayout()
        value_label = QLabel("Value: ")
        self.value_box = QLineEdit("0")
        value_layout.addWidget(value_label)
        value_layout.addWidget(self.value_box)

        edit_constant_button_layout = QHBoxLayout()
        self.new_constant_button = QPushButton("New")
        self.delete_constant_button = QPushButton("Delete")
        self.add_constant_button = QPushButton("Add To Formula")
        edit_constant_button_layout.addWidget(self.new_constant_button)
        edit_constant_button_layout.addWidget(self.delete_constant_button)
        edit_constant_button_layout.addWidget(self.add_constant_button)

        ## Identifiers
        for item in column_names:
            self.variables_list.addItem(item)
        identifiers_label = QLabel("Identifiers:")
        symbols_layout = QVBoxLayout()

        self.add_identifier_button = QPushButton("Add To Formula")

        # # Symbols Layout
        # self.symbols_list = QListWidget()
        # for symbol in ["+", "-", "*", "/", "^", "(", ")"]:
        #     self.symbols_list.addItem(symbol)

        # Functions Layout
        functions_layout = QVBoxLayout()
        functions_layout.addWidget(QLabel("Functions: "))
        self.functions_list = QListWidget()
        for function in ["sqrt", "exp", "log", "ln", "sin", "cos", "tan", "asin", "acos", "atan"]:
            self.functions_list.addItem(function)
        self.add_function_button = QPushButton("Add to Formula")

        # Add Constants Layout
        constants_layout.addWidget(constants_label)
        constants_layout.addWidget(self.constants_list)
        constants_layout.addLayout(name_layout)
        constants_layout.addLayout(value_layout)
        constants_layout.addLayout(edit_constant_button_layout)
        constants_layout.addWidget(identifiers_label)
        constants_layout.addWidget(self.variables_list)
        constants_layout.addWidget(self.add_identifier_button)
        # Add to Symbols Layout
        # symbols_layout.addWidget(self.symbols_list)
        # Add to Functions Layout
        functions_layout.addWidget(self.functions_list)
        functions_layout.addWidget(self.add_function_button)

        formula_layout.addLayout(constants_layout)
        # formula_layout.addLayout(symbols_layout)
        formula_layout.addLayout(functions_layout)
        formula_group.setLayout(formula_layout)

        # Formula editor
        formula_editor_group = QGroupBox("Formula")
        formula_editor_layout = QVBoxLayout()
        self.formula_editor = QTextEdit()

        formula_editor_layout.addWidget(self.formula_editor)
        formula_editor_group.setLayout(formula_editor_layout)

        # Right buttons
        right_button_layout = QVBoxLayout()
        self.ok_button = QPushButton("Accept")
        self.cancel_button = QPushButton("Cancel")
        right_button_layout.addWidget(self.ok_button)
        right_button_layout.addWidget(self.cancel_button)
        
        top_layout = QHBoxLayout()
        top_layout.addWidget(general_group)
        top_layout.addWidget(parameters_group)

        middle_layout = QVBoxLayout()
        middle_layout.addLayout(top_layout)
        middle_layout.addWidget(formula_editor_group)

        end_layout = QVBoxLayout()
        end_layout.addWidget(formula_group)
        end_layout.addLayout(right_button_layout)

        main_layout.addLayout(middle_layout)
        main_layout.addLayout(end_layout)

        ## Connections
        self.add_identifier_button.clicked.connect(self.add_identifier)
        self.add_function_button.clicked.connect(self.add_function)
        self.delete_button.clicked.connect(self.delete_channel)
        self.constants_list.clicked.connect(self.update_constant_fields)
        self.insert_button.clicked.connect(self.insert_channel)
        self.channels_list.currentItemChanged.connect(self.load_channel_parameters)
        self.constants_list.itemClicked.connect(self.load_constant_parameters)
        self.delete_constant_button.clicked.connect(self.delete_constant)
        self.new_constant_button.clicked.connect(self.new_constant)
        self.add_constant_button.clicked.connect(self.add_constant)
        self.name_box.editingFinished.connect(self.save_constant_parameters)
        self.value_box.editingFinished.connect(self.save_constant_parameters)
        self.channel_name_edit.editingFinished.connect(self.save_channel_parameters)
        self.unit_edit.editingFinished.connect(self.save_channel_parameters)
        self.formula_editor.textChanged.connect(self.save_channel_parameters)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.close)

        ## Doing this last so no problems loading data   
        self.load_data()
        self.update_checkboxes()
    
        # self.autosave_timer = QTimer(self)
        # self.autosave_timer.setInterval(20_000)
        # self.autosave_timer.timeout.connect(self.save_channel_parameters)
        # self.autosave_timer.start()

    def refresh_channel_list(self):
        self.channels_list.clear()
        self.channels_list.addItems(self.channel_parameters.keys())
        self.update_checkboxes()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def update_checkboxes(self):
        # self.active_channel_layout.clear()
        self.clear_layout(self.active_channel_layout)
        for channel_name, params in self.channel_parameters.items():
            checkbox = QCheckBox("")
            checkbox.setChecked(params.get("checked", False))
            checkbox.stateChanged.connect(self.checkbox_changed)
            self.active_channel_layout.addWidget(checkbox)

    def checkbox_changed(self):
        for idx in range(self.active_channel_layout.count()):
            item = self.active_channel_layout.itemAt(idx)
            if widget := item.widget():
                if isinstance(widget, QCheckBox):
                    name = list(self.channel_parameters)[idx-1]
                    self.channel_parameters[name]["checked"] = widget.isChecked()
        self.store_data()

    def insert_channel(self):
        # channel_name = self.channel_name_edit.text().strip()
        # unit = self.unit_edit.text().strip()
        # formula = self.formula_editor.toPlainText()
        # if not channel_name:
        #     return
        temp_channel_name = "TEMP1"
        count = 1
        while 1:
            if temp_channel_name in self.channel_parameters.keys():
                temp_channel_name = temp_channel_name[:-1] + str(count)
                count+=1
            else:
                break

        self.channel_parameters[temp_channel_name] = {"name": temp_channel_name, "unit": "", "formula": "", "checked": False}
        self.channels_list.addItem(temp_channel_name)
        self.channel_name_edit.clear()
        self.unit_edit.clear()
        checkbox = QCheckBox("")
        checkbox.setChecked(False)
        self.active_channel_layout.addWidget(checkbox)
        self.refresh_channel_list()
        self.update_checkboxes()
        self.store_data()

    def delete_channel(self):
        item = self.channels_list.currentItem()
        if not item:
            return
        name = item.text()
        self.channels_list.takeItem(self.channels_list.row(item))
        self.channel_name_edit.clear()
        self.unit_edit.clear()

        self.channel_parameters.pop(name, None)
        self.refresh_channel_list()
        self.update_checkboxes()
        self.store_data()
            
    def update_constant_fields(self):
        selected_constant = self.constants_list.currentItem().text()
        if selected_constant in self.constants:
            constant = self.constants[selected_constant]
            self.name_box.setText(constant["name"])
            self.value_box.setText(str(constant["value"]))
        self.store_data()

    def load_channel_parameters(self, item):
        if not item:
            return
        channel_name = item.text()
        params = self.channel_parameters.get(channel_name, {})
        self.channel_name_edit.setText(params.get("name", ""))
        self.unit_edit.setText(params.get("unit", ""))
        self.formula_editor.setText(params.get("formula", ""))
        
    def save_channel_parameters(self):
        """Save edits made to the currently selected channel."""
        item = self.channels_list.currentItem()
        if not item:
            return

        old_key   = item.text()
        new_name  = self.channel_name_edit.text().strip() or old_key
        new_unit  = self.unit_edit.text().strip()
        new_form  = self.formula_editor.toPlainText().strip()
        # preserve its checked state
        checked   = self.channel_parameters.get(old_key, {}).get("checked", False)

        # if they renamed it, re‑key the dict & update the list item
        if new_name != old_key:
            data = self.channel_parameters.pop(old_key, None) or {}
            data.update(name=new_name, unit=new_unit, formula=new_form, checked=checked)
            self.channel_parameters[new_name] = data
            item.setText(new_name)
        else:
            # just update fields in place
            self.channel_parameters[old_key].update(
                name=new_name, unit=new_unit, formula=new_form, checked=checked
            )

        # refresh the checkboxes (so their labels stay in sync)
        self.update_checkboxes()
        # persist immediately
        self.store_data()

    def on_channel_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        if previous:
            old_key = previous.text()
            name    = self.channel_name_edit.text().strip()
            unit    = self.unit_edit.text().strip()
            formula = self.formula_editor.toPlainText().strip()
            if old_key:
                old_checked = self.channel_parameters.get(old_key, {}).get("checked", False)
                self.channel_parameters.pop(old_key, None)
                new_key = name or old_key
                self.channel_parameters[new_key] = {
                    "name": new_key,
                    "unit": unit,
                    "formula": formula,
                    "checked": old_checked
                }
                previous.setText(new_key)
        if current:
            self.load_channel_parameters(current)
        self.store_data()
    
    def load_constant_parameters(self, item):
        try:
            constant_name = item.text()
            constant = self.constants.get(constant_name, {})
            self.name_box.setText(str(constant["name"]))
            self.value_box.setText(str(constant["value"]))
        except Exception as e:
            print("Big Problems Running: ", str(e))

    def save_constant_parameters(self):
        item = self.constants_list.currentItem()
        if not item:
            return

        old_key = item.text()
        new_name = self.name_box.text().strip()
        try:
            new_value = float(self.value_box.text().strip())
        except ValueError:
            return

        if new_name and new_name != old_key:
            old = self.constants.pop(old_key, None)
            if old is not None:
                old["name"] = new_name
                old["value"] = new_value
                self.constants[new_name] = old
            item.setText(new_name)
        else:
            self.constants[old_key]["value"] = new_value

        self.store_data()

    def new_constant(self):
        try: 
            constant_name = self.name_box.text()
            constant_value = self.value_box.text()
            constant = {"name": constant_name, "value": float(constant_value)}
            self.constants[constant_name] = constant
            self.constants_list.addItem(constant["name"])
        except Exception as e:
            print("Big Problems Running: ", str(e))
        self.store_data()
        
    def delete_constant(self):
        try:
            selected_constant = self.constants_list.currentItem().text()
            if selected_constant in self.constants:
                del self.constants[selected_constant]
                row = self.constants_list.row(self.constants_list.currentItem())
                self.constants_list.takeItem(row)
                self.name_box.clear()
                self.value_box.clear()
        except Exception as e:
            print("Big Problems Running: ", str(e))
        self.store_data()

    def add_constant(self):
        try:
            constant_name = self.constants_list.currentItem().text()
            text = self.formula_editor.toPlainText() + constant_name
            self.formula_editor.setText(text)
        except Exception as e:
            print("Big Problems Running: ", str(e))
        self.store_data()

    def add_identifier(self):
        try:
            id_name = self.variables_list.currentItem().text()
            text = self.formula_editor.toPlainText() + "[" + id_name+ "]"
            self.formula_editor.setText(text)
        except Exception as e:
            print("Big Problems Running: ", str(e))
        self.store_data()
    
    def add_function(self):
        try:
            func_name = self.functions_list.currentItem().text()
            text = self.formula_editor.toPlainText() + func_name+ "()"
            self.formula_editor.setText(text)
        except Exception as e:
            print("Big Problems Running: ", str(e))
        self.store_data()

    def manage_checkbox(self):
        count = self.active_channels_layout.count()
        for i in range(count):
            item = self.active_channels_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for channel_name in self.channel_parameters:
            checkbox = QCheckBox(channel_name)
            self.active_channels_layout.addWidget(checkbox)
                
    def return_formula(self):
        if self.failed_usage:
            return []
        formulas = []          
        for idx, (channel, channel_data) in enumerate(self.channel_parameters.items()):
            formula = channel_data["formula"]
            for constant in self.constants.values():
                if constant["name"] in formula:
                    formula = formula.replace(constant["name"], str(constant["value"]))
            item = self.active_channel_layout.itemAt(idx).widget()
            if isinstance(item, QCheckBox) and item.isChecked():
                formulas.append(formula)
        #print(formulas)
        return formulas

    def store_data(self):
        data = {
            "channel_parameters": self.channel_parameters,
            "constants": self.constants
        }

        try:
            with open("data/channels.pkl", "wb") as file:
                pickle.dump(data, file)
        except Exception as e:
            print(str(e))

    def load_data(self):
        data = None
        error = None
        try:
            with open("data/channels.pkl", "rb") as file:
                data = pickle.load(file)
        except Exception as e:
            print(str(e))
            error = e

        if data is None:
            QMessageBox.critical(self, "Error", f"Failed to load data: {error}")
            return

        self.channel_parameters = {}
        for key, value in data.get("channel_parameters", {}).items():
            if isinstance(value, tuple):
                value = value[0]
            if isinstance(value, dict):
                self.channel_parameters[key] = value

        for key, value in data.get("constants", {}).items():
            if isinstance(value, tuple):
                value = value[0]
            if isinstance(value, dict):
                self.constants[key] = value

        # print(f"self.channel_parameters: {self.channel_parameters} (type: {type(self.channel_parameters)})")
        self.constants = data.get("constants", {})
        for constant in self.constants.keys():
            self.constants_list.addItem(constant)
        self.channels_list.clear()
        for channel in self.channel_parameters.keys():
            self.channels_list.addItem(channel)
        # self.formula_editor.setText(data.get("formula_editor_text", ""))
        # self.channel_name_edit.setText(data.get("channel_name", ""))
        # self.unit_edit.setText(data.get("unit", ""))
      
    def accept(self):
        self.result = self.return_formula()
        if (self.source == "label_module" and len(self.result) > 1):
            QMessageBox.warning(self, "Selection Error", "For Label Module you can only select one channel at a time.")
            return
        super().accept()

    def close(self):
        self.failed_usage = True
        super().accept()
