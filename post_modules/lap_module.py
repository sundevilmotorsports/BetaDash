import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette, QFontMetrics, QStandardItem
from PyQt5.QtCore import Qt, QObject, QEvent
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from collapsible_module import Collapsible

class MplCanvas(FigureCanvasQTAgg):
    activeXY = [[], []]
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax1 = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)

class LapChooser(QWidget):
    def __init__(
        self,
        central_widget: QWidget,
        plot: Figure,
    ):
        super().__init__()
        self.central_widget = central_widget
        self.plot_widget = plot
        self.sidebox = QVBoxLayout()
        self.sidebox2 = QVBoxLayout()

        #self.plot_widget.fig.canvas.mpl_connect("button_press_event", self.on_click)

        self.sidebox.setAlignment(Qt.AlignTop)
        self.x_combo = QComboBox(self.central_widget)
        self.y_combo = QComboBox(self.central_widget)
        self.x_combo.currentIndexChanged.connect(self.plot_graph)
        self.y_combo.currentIndexChanged.connect(self.plot_graph)

        # creating dropdowns and updating dataset when changed
        self.x_set = QComboBox(self.central_widget)
        self.x_set.showEvent = lambda _: self.init_metadata()
        self.x_set.currentIndexChanged.connect(self.set_active_data)

        self.data = get_active_sessions()
        self.names = get_names()
        # Session returns array of active csvs, we only want the first as of now
        
        self.data = self.data[0].get_dataframe()
        self.lap_dataframes = {}
        self.plot_laps_dataframe = []

        for _, row in self.data.iterrows():
            lap_number = row['Lap (#)']
            
            if lap_number not in self.lap_dataframes:
                self.lap_dataframes[lap_number] = pd.DataFrame(columns=self.data.columns)

            self.lap_dataframes[lap_number] = pd.concat([self.lap_dataframes[lap_number], row.to_frame().transpose()], ignore_index=True)
        #max value for x axis i.e seconds
        self.max = 0
        for lap_number, lap_dataframe in self.lap_dataframes.items():
            min_seconds = lap_dataframe.iloc[:, 0].min()
            lap_dataframe.iloc[:, 0] -= min_seconds
            self.max = max(self.max, lap_dataframe.iloc[:, 0].max())
            '''
            print(f"DataFrame for Lap {lap_number}:\n")
            print(lap_dataframe)
            print("\n" + "="*50 + "\n")
            '''
        
        # checkable combo box addition from class defined below
        self.laps_combo = CheckableComboBox(self)
        self.laps_combo.setStyleSheet(
            "background-color: white; color: black; font-size: 14px;"
        )
        self.laps_combo.setFixedHeight(25)
        self.laps_combo.model().dataChanged.connect(self.manage_Laps)
        # array to hold every 'lap', just a placeholder to populate combobox
        self.lap_array = []
        for i in range(len(self.lap_dataframes)+5):#arbitrary +5 but i cant explain why the length is not actually the length one would think
            if self.lap_dataframes.get(i) is not None:
                self.lap_array.append(f"Lap {i}")
        
        print(self.lap_array)
        self.laps_combo.addItems(self.lap_array)
        
        # creates labels and adds comboboxes to select columns in the graph
        self.set_combo_box()
        self.sidebox.addWidget(QLabel("Select Dataset:"))
        self.sidebox.addWidget(self.x_set)
        self.sidebox.addWidget(QLabel("Select X Axis Column:"))
        self.sidebox.addWidget(self.x_combo)
        self.sidebox.addWidget(QLabel("Select Y Axis Column:"))
        self.sidebox.addWidget(self.y_combo)
        self.sidebox.addWidget(QLabel("Select Laps: "))
        self.sidebox.addWidget(self.laps_combo)

    def on_click(self, event):
        """On click function is called during a click, decides if it is a left click, and calls click_trim() to zoom the graph in/out"""
        if event.dblclick:
            if event.button is MouseButton.LEFT:
                self.left = True
            self.click_trim()
            self.left = False

    def clear_layout(self, layout):
        """Removes all items from the given layout"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def set_combo_box(self):
        """Populates ComboBoxes with all different columns within the active data"""           
        self.x_set.addItems(get_names())
        self.x_combo.clear()
        self.y_combo.clear()
        self.active_dataX = get_active_sessions()[
            self.x_set.currentIndex()
        ].get_dataframe()
        self.x_combo.addItems(self.active_dataX.columns.tolist())
        self.y_combo.addItems(self.active_dataX.columns.tolist())

    def init_combobox(self, xSet, xSelect, ySelect):
        """Sets the front-text of comboboxes within the sidebar to the currently selected column within the active dataset"""
        self.x_set.setCurrentText(xSet)
        self.x_combo.setCurrentText(xSelect)
        self.y_combo.setCurrentText(ySelect)

    def get_scroll_areas(self):
        """returns both sidebox layouts"""
        return self.sidebox, self.sidebox2

    def set_active_data(self):
        """Modifies self.active_dataX and sets it to the dataframe in which the "set x" value is. It then calls trim_graph() and plot_graph()."""
        self.x_combo.clear()
        self.y_combo.clear()

        self.init_metadata()

        self.active_dataX = get_active_sessions()[
            self.x_set.currentIndex()
        ].get_dataframe()
        self.x_combo.addItems(self.active_dataX.columns.tolist())
        self.y_combo.addItems(self.active_dataX.columns.tolist())
        self.trim_graph()
        self.plot_graph()

    def init_metadata(self):
        """This function simply populates some of the labels with the metadata from the chosen metadata data frame"""
        try:
            self.clear_layout(self.sidebox2)
            self.dataX = get_active_sessions()[
                self.x_set.currentIndex()
            ].get_metadata()

            self.sidebox2.addWidget(QLabel("Name: " + self.dataX["Name"]))
            self.sidebox2.addWidget(QLabel("Date: " + self.dataX["Date"]))
            self.sidebox2.addWidget(QLabel("Driver: " + self.dataX["Driver"]))
            self.sidebox2.addWidget(QLabel("Car: " + self.dataX["Car"]))
            self.sidebox2.addWidget(QLabel("Track: " + self.dataX["Track"]))
        except:
            print("Error initializing metadata")

    def trim_graph(self):        
        """Function that when called, will edit the bounds of the graph based on whether autofit is selected or not. Otherwise values in textboxes will be set to the bounds"""      
        #self._plot_ref.axes.set_xlim(0, self.max)
        self.plot_widget.draw()
  
    def plot_graph(self):
        """This plot_graph uses a global variable which is a list of dataframes corresponding to the laps taken by the car in the session selected.
            It simply clears the plot and plots every dataframe in self.plot_laps_dataframe that is edited by manage_Laps()
        """
        #self.x_data = self.active_dataX[self.selected_x]
        #self.y_data = self.active_dataX[self.selected_y]

        self.selected_x = self.x_combo.currentText()
        self.selected_y = self.y_combo.currentText()
        self.x_data = None
        self.y_data = None

        self.plot_widget.ax1.clear()
        #print(self.plot_laps_dataframe)

        for lap_number, lap_dataframe in enumerate(self.plot_laps_dataframe):
            if not lap_dataframe.empty and self.selected_x in lap_dataframe.columns and self.selected_y in lap_dataframe.columns:
                #print("lil something")
                self.x_data = lap_dataframe[self.selected_x]
                self.y_data = lap_dataframe[self.selected_y]
                self.plot_widget.ax1.plot(self.x_data, self.y_data, label=f"Lap {lap_dataframe['Lap (#)'][0]}")
            else:
                print("Either data frame is empty, or the selection for x and y axis are not valid")
        
        self.plot_widget.ax1.set_xlabel(self.selected_x)
        self.plot_widget.ax1.set_ylabel(self.selected_y)
        self.plot_widget.ax1.set_title(self.selected_x + " vs " + self.selected_y)
        self.plot_widget.ax1.grid()
        self.plot_widget.ax1.legend()
        self.plot_widget.ax1.set_xlim(0, self.max)
        self.trim_graph()
        self.plot_widget.draw()
    
    def manage_Laps(self):
        array_to_parse = self.laps_combo.currentData()
        selected_lap_numbers = [int(lap_string.split()[-1]) for lap_string in array_to_parse]
        #print(selected_lap_numbers)

        selected_lap_dataframes = [self.lap_dataframes[i] for i in selected_lap_numbers]
        #print(selected_lap_dataframes)
        self.plot_laps_dataframe = selected_lap_dataframes

        #print(self.plot_laps_dataframe)
        self.plot_graph()

    def get_info(self):
        """Returns value of self.x_set, the combobox for selecting the current dataset or csv. additionally it returns the current x and y columns"""
        return self.x_set.currentText(), self.selected_x, self.selected_y
        
       

class PostLapModule(QMainWindow):
    def __init__(self):
        super().__init__()
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
        self.plot_widget = MplCanvas()

        toolbar = NavigationToolbar(self.plot_widget, self)
        plot_layout = QVBoxLayout(graph_widget)
        plot_layout.addWidget(toolbar)
        plot_layout.addWidget(self.plot_widget)
        self.layout.addWidget(graph_widget)
        
        #array to store all laps graphed
        self.laps_arr = []
    
        self.setChooser = LapChooser(
            self.central_widget, self.plot_widget#, self.max_val
        )
        if self.setChooser not in self.laps_arr:
            self.laps_arr.append(self.setChooser)

        sidebox, sidebox1 = self.setChooser.get_scroll_areas()
        sideBoxLayout.addLayout(sidebox)
        sideBoxLayout.addLayout(sidebox1)

        #self.laps_combo.model().dataChanged.connect(self.manage_laps)

        self.reset_button = QPushButton("Reset", self.central_widget)
        self.reset_button.clicked.connect(self.reset)
        self.footer = QStatusBar()
        self.setStatusBar(self.footer)
        self.footer.addWidget(self.reset_button)
        
        collapsible_container = Collapsible()
        collapsible_container.setContentLayout(sideBoxLayout)
        self.layout.addWidget(collapsible_container)
    
    def reset(self):
        self.setChooser.set_active_data()
        self.setChooser.plot_laps_dataframe = {}
        self.setChooser.plot_graph()
    '''
    def play_graph(self):
        self.setChooser.play_graph()

    def pause_graph(self):
        self.setChooser.pause_graph()
    '''
    def get_info(self):
        """Getter that returns an array with the layouts of the sideboxes"""
        return self.setChooser.get_info()
      
    
    def get_graph_type():
        return "PostLapModule"