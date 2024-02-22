import time
import pyqtgraph as pg
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator, QPalette, QFontMetrics, QStandardItem
from PyQt5.QtCore import Qt, QObject, QEvent

from collapsible_module import Collapsible


# ------------------------------
# Custom Class for our GraphModule. By inheriting from it, we can create a custom canvas for Matplotlib within the PyQt application.
# Line outside the class tells the application that the backend for Matplotlib will use Qt5Agg,
# which is the backend that integrates Matplotlib with the PyQt5 framework. It tells Matplotlib
# to render plots using Qt for the graphical user interface.
# ------------------------------

# ------------------------------
# Custom class named DatasetChooser. This is the sidebar that provides functionality to select datasets,
# customize data visualization settings, and update and animate graphs using Matplotlib.
# It connects various widgets and signals to provide an interactive data visualization experience.
# ------------------------------
class LiveGraph(QWidget):
    def __init__(
        self,
        central_widget: QWidget,
        plot : pg,
    ):
        super().__init__()
        self.central_widget = central_widget
        self.plot_widget = plot
        self.sidebox = QVBoxLayout()
        self.sidebox2 = QVBoxLayout()

        self.left = False

        self.sidebox.setAlignment(Qt.AlignTop)
        self.x_combo = QComboBox(self.central_widget)
        self.y_combo = CheckableComboBox(self)
        self.y_combo.setFixedHeight(25)
        self.x_combo.currentIndexChanged.connect(self.plot_graph)
        self.y_combo.model().dataChanged.connect(self.plot_graph)

        # creating dropdowns and updating dataset when changed
        self.x_set = QComboBox(self.central_widget)
        self.x_set.showEvent = lambda _: self.init_metadata()
        self.x_set.currentIndexChanged.connect(self.set_active_data)

        # creates labels and textboxes for editing graph limits and trims
        trim_upper = QHBoxLayout()
        trim_under = QHBoxLayout()
        self.trim_container = QVBoxLayout()

        self.selected_y_columns = None
        self.selected_x = None

        # creates labels and adds comboboxes to select columns in the graph
        self.set_combo_box()
        self.sidebox.addWidget(QLabel("Select Dataset:"))
        self.sidebox.addWidget(self.x_set)
        self.sidebox.addWidget(QLabel("Select X Axis Column:"))
        self.sidebox.addWidget(self.x_combo)
        self.sidebox.addWidget(QLabel("Select Y Axis Column:"))
        self.sidebox.addWidget(self.y_combo)
        self.sidebox.addLayout(self.trim_container)

        self.sidebox2.setAlignment(Qt.AlignTop)

# ------------------------------
# This class creates a graphical application with a main window that allows users to add and configure multiple datasets for plotting.
# This is what is shown in the GUI from the main file: dash_board.py. It encapsulates everything described in this file up until this point.
# ------------------------------


class GraphModule(QMainWindow):
    def __init__(self, timestamper=None):
        super().__init__()
        self.data_set = []
        self.setWindowTitle("Module")
        self.setGeometry(100, 100, 1050, 600)
        self.menubar = self.menuBar()
        self.menubar.setStyleSheet(
            "background-color: #333; color: white; font-size: 14px;"
        )
        self.menubar.setStyleSheet("QMenu::item:selected { background-color: #555; }")
        self.menubar.setStyleSheet("QMenu::item:pressed { background-color: #777; }")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)
        sideBoxLayout = QVBoxLayout()
        graph_widget = QWidget()
        self.plot_widget = pg.PlotWidget()

        toolbar = NavigationToolbar(self.plot_widget, self)
        plot_layout = QVBoxLayout(graph_widget)
        #plot_layout.addWidget(toolbar)
        plot_layout.addWidget(self.plot_widget)
        self.layout.addWidget(graph_widget)

        self.timestamper = timestamper
        self.setChooser = LiveGraph(
            self.central_widget, self.plot_widget, timestamper
        )
        sidebox, sidebox1 = self.setChooser.get_scroll_areas()
        self.data_set.append(self.setChooser)
        sideBoxLayout.addLayout(sidebox)
        sideBoxLayout.addLayout(sidebox1)

        #self.add_dataset_button = QPushButton("Add Dataset", self.central_widget)
        #self.add_dataset_button.clicked.connect(self.add_dataset)
        self.reset_button = QPushButton("Reset", self.central_widget)
        self.reset_button.clicked.connect(self.reset)
        self.footer = QStatusBar()
        self.setStatusBar(self.footer)
        self.footer.addWidget(self.reset_button)
        #sideBoxLayout.addWidget(self.add_dataset_button)

        collapsible_container = Collapsible()
        collapsible_container.setContentLayout(sideBoxLayout)
        self.layout.addWidget(collapsible_container)
        # self.layout.addLayout(sideBoxLayout)

        # self.plot_button.clicked.connect(self.plot_graph)

    def reset(self):
        self.pause_graph()
        self.setChooser.set_active_data()
        self.setChooser.plot_graph()

    def add_dataset(self):
        """Deprecated function"""
        setChooser = DatasetChooser(
            self.central_widget, self.plot_widget, self.timestamper
        )
        self.data_set.append(setChooser)
        sideBoxLayout = QVBoxLayout()
        sidebox, sidebox1 = setChooser.get_scroll_areas_without_trim()
        sideBoxLayout.addLayout(sidebox)
        sideBoxLayout.addLayout(sidebox1)
        #sideBoxLayout.insertWidget(-1, self.add_dataset_button)
        # self.layout.addLayout(sideBoxLayout)
        collapsible_container = Collapsible()
        collapsible_container.setContentLayout(sideBoxLayout)
        self.layout.addWidget(collapsible_container)

    def get_info(self):
        """Getter that returns an array with the layouts of the sideboxes"""
        info = []
        for i in self.data_set:
            info.append(i.get_info())
        return info

    def init_combobox(self, xSet, xSelect, ySelect):
        """Sets the front-text comboboxes within the sidebar to the currently selected column within the active dataset"""
        for dataset in self.data_set:
            dataset.init_combobox(xSet, xSelect, ySelect)

    def get_graph_type(self):
        return "GraphModule"