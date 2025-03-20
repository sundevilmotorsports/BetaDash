import time
import matplotlib
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.backend_bases import MouseButton
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator, QPalette, QFontMetrics, QStandardItem
from PyQt5.QtCore import Qt, QObject, QEvent
from collapsible_module import Collapsible
from checkable_combo import CheckableComboBox
from post_modules.session import Session, SessionManager
from post_modules.timestamper import TimeStamper

# ------------------------------
# Custom Class for our GraphModule. By inheriting from it, we can create a custom canvas for Matplotlib within the PyQt application.
# Line outside the class tells the application that the backend for Matplotlib will use Qt5Agg,
# which is the backend that integrates Matplotlib with the PyQt5 framework. It tells Matplotlib
# to render plots using Qt for the graphical user interface.
# ------------------------------

matplotlib.use("Qt5Agg")

class MplCanvas(FigureCanvasQTAgg):
    activeXY = [[], []]

    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax1 = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)

# ------------------------------
# Custom class named DatasetChooser. This is the sidebar that provides functionality to select datasets,
# customize data visualization settings, and update and animate graphs using Matplotlib.
# It connects various widgets and signals to provide an interactive data visualization experience.
# ------------------------------
class DatasetChooser(QWidget):
    def __init__(self, central_widget: QWidget, plot: MplCanvas, timestamper: TimeStamper, session_manager : SessionManager):
        super().__init__()
        self.central_widget = central_widget
        self.plot_widget = plot
        self.session_manager = session_manager
        self.sidebox = QVBoxLayout()
        self.sidebox2 = QVBoxLayout()
        self.timestamper = timestamper
        #self.timestamper.slider.valueChanged.connect(lambda: self.trim_graph(source="slider"))

        self.sidebox.setContentsMargins(0, 0, 0, 0)
        self.sidebox2.setContentsMargins(0, 0, 0, 0)

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

        #integer validation for text boxes
        validator = QIntValidator()

        trim_under.addWidget(QLabel("Trim:"))
        self.begin_widget = QLineEdit()
        self.begin_widget.setValidator(validator)
        self.begin_widget.setFixedWidth(50)
        #self.begin_widget.textChanged.connect(lambda: self.trim_graph(source="begin_widget"))
        trim_under.addWidget(self.begin_widget)
        trim_under.addWidget(QLabel("≤ x ≤"))
        self.end_widget = QLineEdit()
        self.end_widget.setValidator(validator)
        self.end_widget.setFixedWidth(50)
        #self.end_widget.textChanged.connect(lambda: self.trim_graph(source="end_widget"))
        trim_under.addWidget(self.end_widget)
        self.trim_container.addLayout(trim_upper)
        self.trim_container.addLayout(trim_under)

        ### array for managing all connections that call to trim_graph
        self.connect_trim_connections()

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

        ### styling for matplotlib
        #plt.style.use('dark_background'), looks bad lmao

    def clear_layout(self, layout):
        """Removes all items from the given layout"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def set_combo_box(self):
        """Populates ComboBoxes with all different columns within the active data"""
        try:    
            names = self.session_manager.get_filenames()
            data = self.session_manager.active_sessions
            self.x_set.addItems(names)
            self.x_combo.clear()
            self.y_combo.clear()
            self.active_dataX = data[0].data
            self.x_combo.addItems(self.active_dataX.columns.tolist())
            self.y_combo.addItems(self.active_dataX.columns.tolist())
        except:
            print("Error setting combo box")

    def init_combobox(self, xSet, xSelect, ySelect):
        """Sets the front-text of comboboxes within the sidebar to the currently selected column within the active dataset"""
        self.x_set.setCurrentText(xSet)
        self.x_combo.setCurrentText(xSelect)
        self.y_combo.setCurrentText(ySelect)

    def get_scroll_areas(self):
        """returns both sidebox layouts"""
        return self.sidebox, self.sidebox2

    def get_scroll_areas_without_trim(self):
        """returns both sidebox layouts"""
        tempSidebox1 = self.sidebox
        tempSidebox2 = self.sidebox2
        tempSidebox1.removeItem(self.trim_container)
        tempSidebox2.removeItem(self.trim_container)
        return self.sidebox, self.sidebox2

    def set_active_data(self):
        """Modifies self.active_dataX and sets it to the dataframe in which the "set x" value is. It then calls trim_graph() and plot_graph()."""
        self.x_combo.clear()
        self.y_combo.clear()

        self.init_metadata()

        self.active_dataX = self.session_manager.active_sessions[self.x_set.currentIndex()].data
        self.x_combo.addItems(self.active_dataX.columns.tolist())
        self.y_combo.addItems(self.active_dataX.columns.tolist())
        ###TAKE NOTE THE NEXT 3 LINES CALL trim_graph 3 TIMES, don't think we want from a performance and maintenance perspective
        self.begin_widget.setText(str(self.active_dataX[self.selected_x].iloc[0]))
        self.end_widget.setText(str(self.active_dataX[self.selected_x].iloc[-1]))
        self.timestamper.set_init_time(self.active_dataX[self.selected_x].iloc[0])
        self.timestamper.set_max_time(self.active_dataX[self.selected_x].iloc[-1])
        self.trim_graph()
        self.plot_graph()

    def init_metadata(self):
        """This function simply populates some of the labels with the metadata from the chosen metadata data frame"""
        try:
            self.clear_layout(self.sidebox2)
            self.dataX = self.session_manager.active_sessions[self.x_set.currentIndex()]

            self.sidebox2.addWidget(QLabel("Name: " + self.dataX.name))
            self.sidebox2.addWidget(QLabel("Date: " + self.dataX.date))
            self.sidebox2.addWidget(QLabel("Driver: " + self.dataX.driver))
            self.sidebox2.addWidget(QLabel("Car: " + self.dataX.car))
            self.sidebox2.addWidget(QLabel("Track: " + self.dataX.track))
        except:
            print("Error initializing metadata")

    def trim_graph(self):        
        """Function that when called, will edit the bounds of the graph based on whether autofit is selected or not. Otherwise values in textboxes will be set to the bounds"""
        # print("normal trim or end or begin")
        
        self.disconnect_trim_connections()

        if self.begin_widget.text() == "" or self.end_widget.text() == "":
            return
               
        self.begin = int(self.begin_widget.text())
        self.end = float(self.end_widget.text())
        #self.begin_widget.setEnabled(True)
        #self.end_widget.setEnabled(True)

        self.timestamper.set_init_time(self.begin)
        #self.timestamper.set_max_time(self.end)
        self.begin_widget.setText(str(int(self.begin)))
        self.end_widget.setText(str(int(self.end))) 
        # Check if _plot_ref is not None and has valid axes
        self.plot_widget.ax1.set_xlim(self.begin, self.end)
        self.plot_widget.draw()
        
        self.connect_trim_connections()
        
    def slider_trim_graph(self):
        # print("slider trim")
        
        self.disconnect_trim_connections()

        self.begin = float(self.timestamper.slider.value() * (self.timestamper.max_time / 100))
        self.end = float(self.begin + 100)
        self.timestamper.set_init_time(self.begin)
        #self.timestamper.set_max_time(self.end)
        self.begin_widget.setText(str(int(self.begin)))
        self.end_widget.setText(str(int(self.end)))
        self.plot_widget.ax1.set_xlim(self.begin, self.end)
        self.plot_widget.draw()
        
        self.connect_trim_connections()

    def plot_graph(self):
        """When called, this function is responsible for updating and redrawing a graph with user-selected data and settings.
        It then 'draws' the graph, meaning it is an update to the appearance of a graph rather than a creation of a new plot. The performance
        difference could be negligible here. More importantly, limit every possible call to redraw the graph as much as one can
        """
        try:
            self.selected_x = self.x_combo.currentText()
            self.selected_y_columns = self.y_combo.currentData()
            
            if not isinstance(self.selected_y_columns, list):
                self.selected_y_columns = [self.selected_y_columns]

            # Extract the selected columns from self.active_dataX
            y_data = self.active_dataX[self.selected_y_columns]

            self.plot_widget.ax1.clear()
            # print(self.selected_y_columns)
            for col in self.selected_y_columns:
                self.plot_widget.ax1.plot(self.active_dataX[self.selected_x], self.active_dataX[col], label=col)
                
            self.plot_widget.ax1.set_xlabel(self.selected_x)
            self.plot_widget.ax1.set_ylabel(", ".join(self.selected_y_columns))
            self.plot_widget.ax1.set_title(self.selected_x + " vs " + ", ".join(self.selected_y_columns))
            self.plot_widget.ax1.grid()
            if not y_data.empty:
                self.plot_widget.ax1.legend(loc='lower left')
            self.plot_widget.ax1.set_xlim(self.begin, self.end)
            self.plot_widget.draw()
        except Exception as e:
            print("Error plotting graph: " + str(e))

    def play_graph(self):
        """Animating of graph is simply a function animation where the timestamper sends a new integer value. Usually one more than last time, it is fed into the animate() function where the xlimits are simply updated to fit the new timestamper value"""
        try:
            if hasattr(self, "ani") and self.ani.event_source != None:
                self.ani.resume()
                return
            self.ani = animation.FuncAnimation(
                self.plot_widget.fig,
                self.animate,
                frames=self.timestamper.time_generator,
                interval=100,
                repeat=True,
                save_count=50,
                cache_frame_data=True,
            )
            self.plot_widget.draw()
        except Exception as e:
            #self.plot_graph()
            print("Error re-drawing graph: " + str(e))
       

    def animate(self, timestamp):
        """Helper for the animation, adds new data points to X and Y data lists, clears the existing plot, and then re-plots the updated data with new labels, a title, and a grid.
        WARNING: use of plot() could be better than draw(), but we made it necessary that the function will use plot() because of adding to the active x and y datasets
        """
        ###allows modifying of labels without calling trim graph
        ##### also i wanted to move this into play_graph() but didnt work so its here.
        # print("timestamp fed into animate: " + str(timestamp))
        
        self.disconnect_trim_connections()
        
        self.plot_widget.ax1.set_xlim(max(1, timestamp - 100), max(2, timestamp))
        #print("xlim min: " + str(max(1, timestamp - 100)) + "; xlim max: " + str(max(2, timestamp)))
        self.begin_widget.setText(str(int(self.plot_widget.ax1.get_xlim()[0])))
        self.end_widget.setText(str(int(self.plot_widget.ax1.get_xlim()[1])))

        self.connect_trim_connections()
    
    def pause_graph(self):
        """Pauses the graph animation"""
        try:
            self.ani.pause()
        except Exception as e:
            print("Error pausing graph " + str(e))
        ###Need to re-establish connections after pause
        
        self.disconnect_trim_connections()
        self.connect_trim_connections()


    def disconnect_trim_connections(self):
        """Disconnects connections to trim_graph."""
        try:
            self.begin_widget.textChanged.disconnect(self.trim_graph)
            self.end_widget.textChanged.disconnect(self.trim_graph)
            self.timestamper.slider.valueChanged.disconnect(self.slider_trim_graph)
            self.trim_connections = []
        except Exception as e:
            pass
            # print("Error disconnecting from trim_graph " + str(e))

    def connect_trim_connections(self):
        """Reconnects connections to trim_graph."""
        self.trim_connections = []
        self.trim_connections.append(self.begin_widget.textChanged.connect(self.trim_graph))
        self.trim_connections.append(self.end_widget.textChanged.connect(self.trim_graph))
        self.trim_connections.append(self.timestamper.slider.valueChanged.connect(self.slider_trim_graph))

    def get_info(self):
        """Returns value of self.x_set, the combobox for selecting the current dataset or csv. additionally it returns the current x and y columns"""
        return self.x_set.currentText(), self.selected_x, self.selected_y_columns


# ------------------------------
# This class creates a graphical application with a main window that allows users to add and configure multiple datasets for plotting.
# This is what is shown in the GUI from the main file: dash_board.py. It encapsulates everything described in this file up until this point.
# ------------------------------
class PostGraphModule(QMainWindow):
    def __init__(self, timestamper, session_manager):
        super().__init__()
        self.data_set = []
        self.session_manager = session_manager
        self.setWindowTitle("Module")
        self.setGeometry(100, 100, 950, 600)
        self.menubar = self.menuBar()
        self.menubar.setStyleSheet(
            "background-color: #333; color: white; font-size: 14px;"
        )
        self.menubar.setStyleSheet("QMenu::item:selected { background-color: #555; }")
        self.menubar.setStyleSheet("QMenu::item:pressed { background-color: #777; }")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        sideBoxLayout = QVBoxLayout()
        graph_widget = QWidget()
        self.plot_widget = MplCanvas()
        self.plot_widget.fig.tight_layout()
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        #toolbar = NavigationToolbar(self.plot_widget, self)
        plot_layout = QVBoxLayout(graph_widget)
        #plot_layout.addWidget(toolbar)
        plot_layout.addWidget(self.plot_widget)
        plot_layout.setContentsMargins(0,0,0,0)
        self.layout.addWidget(graph_widget)

        self.timestamper = timestamper
        self.setChooser = DatasetChooser(self.central_widget, self.plot_widget, self.timestamper, self.session_manager)
        sidebox, sidebox1 = self.setChooser.get_scroll_areas()
        self.data_set.append(self.setChooser)
        sideBoxLayout.addLayout(sidebox)
        sideBoxLayout.addLayout(sidebox1)

        #self.add_dataset_button = QPushButton("Add Dataset", self.central_widget)
        #self.add_dataset_button.clicked.connect(self.add_dataset)
        self.reset_button = QPushButton("Reset")
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
        sideBoxLayout.addWidget(self.reset_button)

    def reset(self):
        self.pause_graph()
        self.setChooser.set_active_data()
        self.setChooser.plot_graph()

    def play(self):
        self.setChooser.play_graph()

    def pause(self):
        self.setChooser.pause_graph()

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
        return "PostGraphModule"