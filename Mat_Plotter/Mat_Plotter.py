import os
import sys
import math

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import AutoLocator, LinearLocator, LogLocator, MultipleLocator, AutoMinorLocator, FormatStrFormatter
import matplotlib.pyplot as plt
import matplotlib.font_manager

import numpy as np
import decimal
import csv
import configparser
from collections import OrderedDict
from sys import platform as _platform
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

__version__ = '1.0'


def resource_path(relative_path):  # Define function to import external files when using PyInstaller.
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


package_directory = os.path.dirname(os.path.abspath(__file__))
qtMatPlotterfile = resource_path(os.path.join("Mat_Plotter", "Mat_Plotter.ui"))  # GUI layout file.
Ui_MatPlotter, QtBaseClass = uic.loadUiType(qtMatPlotterfile)
qtsettingsfile = resource_path(os.path.join("Mat_Plotter", "Matplotter_settings.ui"))
Ui_settings_matplotter, QtBaseClass = uic.loadUiType(qtsettingsfile)
qtloadformatfile = resource_path(os.path.join("Mat_Plotter", "Matplotter_loadformat.ui"))
Ui_loadformat, QtBaseClass = uic.loadUiType(qtloadformatfile)
qtsaveformatfile = resource_path(os.path.join("Mat_Plotter", "Matplotter_saveformat.ui"))
Ui_saveformat, QtBaseClass = uic.loadUiType(qtsaveformatfile)


class PlotCanvas(FigureCanvas):
    def __init__(self, root, width, height):
        self.fig = Figure(figsize=(width, height), dpi=100)
        self.fig.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95)
        self.plot = self.fig.add_subplot(111)
        # self.plot.spines['left'].set_position('zero')
        # self.kpplot.spines['right'].set_color('none')
        # self.plot.spines['bottom'].set_position('zero')

        self.plot_twinx = self.plot.twinx()
        self.plot_twiny = self.plot.twiny()
        # self.plot_twinxy = self.plot.twinx().twiny()
        self.plot_twinx.get_yaxis().set_visible(False)
        self.plot_twiny.get_xaxis().set_visible(False)

        FigureCanvas.__init__(self, self.fig)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Preferred,
                                   QSizePolicy.Preferred)
        FigureCanvas.updateGeometry(self)


class PlotAndShow:

    """Plot a new line on the subplot, and show it."""

    def __init__(self, mplplot, theplot, fitline, add_to_previous, *args):
        self.mplplot = mplplot
        self.theplot = theplot
        self.fitline = fitline
        self.add_to_previous = add_to_previous
        self.x = args[0]
        self.y = args[1]
        self.color = args[2]
        self.title = args[3]
        self.xlabel = args[4]
        self.ylabel = args[5]
        self.legend_location = args[6]
        self.xlimit = args[7]
        self.ylimit = args[8]
        self.xtick = args[9]
        self.ytick = args[10]
        self.xtick_minor = args[11]
        self.ytick_minor = args[12]
        self.autolimit_x = args[13]
        self.autotick_x = args[14]
        self.autolimit_y = args[15]
        self.autotick_y = args[16]
        self.log_x = args[17]
        self.log_y = args[18]
        self.grid = args[19]
        self.linetype = args[20]

        if len(self.x) != len(self.y):
            return

        if not self.color:
            self.color = "blue"

        self.plot()

    def plot(self):
        if not self.add_to_previous:
            self.try_remove_fitline(self.fitline) # Currently does no work

        self.fitline = self.theplot.plot(self.x, self.y, self.linetype, color=self.color, label=self.title)

        if self.xlabel:
            self.theplot.set_xlabel(self.xlabel)
        if self.ylabel:
            self.theplot.set_ylabel(self.ylabel)

        if self.legend_location:
            legend = self.theplot.legend(loc=self.legend_location, shadow=True)
            frame = legend.get_frame()

            # Set the fontsize
            for label in legend.get_texts():
                label.set_fontsize('medium')

            for label in legend.get_lines():
                label.set_linewidth(1.5)

        # X and Y display range
        lim_x = [self.xlimit[0], self.xlimit[1]]
        lim_y = [self.ylimit[0], self.ylimit[1]]
        if len(self.x) > 1 and len(self.y) > 1:
            if self.autolimit_x:
                    lim_x = [min(self.x), max(self.x)]
            if self.autolimit_y:
                    lim_y = [min(self.y), max(self.y)]

        self.theplot.set_xlim(lim_x)
        self.theplot.set_ylim(lim_y)

        # X and Y ticks
        tick_x, tick_y = self.xtick, self.ytick

        if self.log_x:
            if lim_x[0] <= 0:
                lim_x[0] = 1
                self.theplot.set_xlim(lim_x)
            self.theplot.xaxis.set_major_locator(LogLocator(base=10, numticks=10))
        else:
            if self.autotick_x:
                self.theplot.xaxis.set_major_locator(AutoLocator())
            else:
                if (lim_x[1] - lim_x[0]) % tick_x == 0:
                    self.theplot.xaxis.set_ticks(np.arange(lim_x[0], lim_x[1] + tick_x, tick_x))
                else:
                    self.theplot.xaxis.set_ticks(np.arange(lim_x[0], lim_x[1], tick_x))

        if self.log_y:
            if lim_y[0] <= 0:
                lim_y[0] = 1
                self.theplot.set_ylim(lim_y)
            self.theplot.yaxis.set_major_locator(LogLocator(base=10, numticks=10))
        else:
            if self.autotick_y:
                self.theplot.yaxis.set_major_locator(AutoLocator())
            else:
                if (lim_y[1] - lim_y[0]) % tick_y == 0:
                    self.theplot.yaxis.set_ticks(np.arange(lim_y[0], lim_y[1] + tick_y, tick_y))
                else:
                    self.theplot.yaxis.set_ticks(np.arange(lim_y[0], lim_y[1], tick_y))

        self.theplot.xaxis.set_minor_locator(AutoMinorLocator(n=self.xtick_minor+1))
        self.theplot.yaxis.set_minor_locator(AutoMinorLocator(n=self.ytick_minor+1))

        if self.grid:
            self.theplot.grid(True)
        else:
            self.theplot.grid(False)

        # self.theplot.spines['left'].set_position('zero')
        # self.kpplot.spines['right'].set_color('none')
        # self.theplot.spines['bottom'].set_position('zero')

        self.mplplot.draw()
        # return fitline
    
    def add_element(self):
        self.vline = self.theplot.axvline(x=0, visible=True, color='k', linewidth=1)
        self.hline = self.theplot.axhline(y=0, visible=True, color='k', linewidth=1)
        self.dot = self.theplot.plot(0, 0, marker='o', color='r')

    def try_remove_fitline(self, thefitline):

        """Remove an existing line."""

        try:
            thefitline.pop(0).remove()
        except (AttributeError, IndexError) as error:
            pass


class loadformat(QDialog, Ui_loadformat):

    """Load existing recipe fractions."""

    def __init__(self, root, filelist):
        QDialog.__init__(self, root)
        Ui_loadformat.__init__(self)
        self.setupUi(self)
        self.filelist = filelist
        self.index1 = self.filelist.index("Default")
        self.result = -1

        self.struoption.addItems(self.filelist)
        self.struoption.setCurrentIndex(self.index1)
        self.struoption.currentIndexChanged.connect(self.selectionchange)
        self.resultbox.accepted.connect(self.buttonOkayfuncton)
        self.resultbox.rejected.connect(self.buttonCancelfuncton)
        self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Enter), self)
        self.shortcut.activated.connect(self.buttonOkayfuncton)

    def buttonOkayfuncton(self):
        self.result = self.index1

    def buttonCancelfuncton(self):
        self.result = -1

    def returnresult(self):
        return self.result

    def selectionchange(self, i):
        self.index1 = i


class saveformat(QDialog, Ui_saveformat):

    """Load existing recipe fractions."""

    def __init__(self, root, filelist):
        QDialog.__init__(self, root)
        Ui_saveformat.__init__(self)
        self.setupUi(self)
        self.filelist = filelist
        self.index1 = self.filelist.index("Default")
        self.result = -1

        self.struoption.addItems(self.filelist)
        self.struoption.setCurrentIndex(self.index1)
        self.struoption.currentIndexChanged.connect(self.selectionchange)
        self.resultbox.accepted.connect(self.buttonOkayfuncton)
        self.resultbox.rejected.connect(self.buttonCancelfuncton)
        self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Enter), self)
        self.shortcut.activated.connect(self.buttonOkayfuncton)

    def buttonOkayfuncton(self):
        if not self.entry_newformat.text():
            self.result = self.filelist[self.index1]
        else:
            self.result = self.entry_newformat.text()

    def buttonCancelfuncton(self):
        self.result = -1

    def returnresult(self):
        return self.result

    def selectionchange(self, i):
        self.index1 = i


class Matplottersettings(QDialog, Ui_settings_matplotter):

    """Optinal settings for customized result."""

    def __init__(self, root, dpi, colortheme):
        QDialog.__init__(self, root)
        Ui_settings_matplotter.__init__(self)
        self.setupUi(self)
        self.root = root
        self.dpi = dpi
        self.colortheme = colortheme
        self.index1 = 0
        self.themelist = ["white", "dark", "Black"]
        self.config = configparser.ConfigParser()
        self.config.read(resource_path(os.path.join("Mat_Plotter", 'configuration.ini')))

        self.themeoption.addItems(self.themelist)
        self.themeoption.setCurrentIndex(self.colortheme)
        self.themeoption.currentIndexChanged.connect(self.selectionchange)

        self.entry_dpi.setText(str(dpi))
        self.entry_dpi.setValidator(QIntValidator())

        self.resultbox.accepted.connect(self.buttonOkayfuncton)
        self.resultbox.rejected.connect(self.buttonCancelfuncton)
        self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Enter), self)
        self.shortcut.activated.connect(self.buttonOkayfuncton)

    def buttonOkayfuncton(self):
        self.dpi = int(self.entry_dpi.text())

        if self.checkbox_rem.isChecked() is True:
            cfgfile = open(resource_path(os.path.join("Mat_Plotter", 'configuration.ini')), 'w')
            self.config.set("Settings", "dpi", str(self.dpi))
            self.config.set("Settings", "colortheme", str(self.index1))

            self.config.write(cfgfile)
            cfgfile.close()

    def buttonCancelfuncton(self):
        pass

    def selectionchange(self, i):
        self.index1 = i


class Mat_Plotter_GUI(QWidget, Ui_MatPlotter):

    """Main GUI window."""

    def __init__(self, root, masterroot):
        QWidget.__init__(self)
        Ui_MatPlotter.__init__(self)
        self.setupUi(self)
        self.root = root    # The mdi area to pack the QWidget
        self.masterroot = masterroot    # The mainwindow
        self.listbox = self.masterroot.listbox
        self.statusbar = self.masterroot.statusbar
        self.status1 = self.masterroot.status1
        self.status2 = self.masterroot.status2
        self.progressbar = self.masterroot.progressbar  # In case a progressbar is needed.
        self.addlog = self.masterroot.addlog    # Add log to the main UI frame.
        self.addlog_with_button = self.masterroot.addlog_with_button    # Add log with a button to the main UI frame.
        self.warningcolor1 = 'red'      # Three standard colors to show warnings in the log frame.
        self.warningcolor2 = 'orange'
        self.warningcolor3 = 'royalblue'
        self.osdir = os.path.dirname(os.path.abspath(__file__))
        self.config = configparser.ConfigParser()
        self.config.read(resource_path(os.path.join("Mat_Plotter", 'configuration.ini')))

        self.dpi = int(self.config["Settings"]["dpi"])
        self.colortheme = int(self.config["Settings"]["colortheme"])

        self.buttonsettings.clicked.connect(self.settings)
        self.buttondata.clicked.connect(self.openfromfile)
        self.buttonoutput.clicked.connect(self.output)
        self.buttonformat.clicked.connect(self.openformat)
        self.buttonsave.clicked.connect(self.saveformat)
        self.buttonclear.clicked.connect(self.clearalldata)
        self.buttonplot.clicked.connect(self.plot)
        self.buttonautolimit_x.clicked.connect(lambda: self.plot(limit_x=1))
        self.buttonautotick_x.clicked.connect(lambda: self.plot(tick_x=1))
        self.buttonautolimit_y.clicked.connect(lambda: self.plot(limit_y=1))
        self.buttonautotick_y.clicked.connect(lambda: self.plot(tick_y=1))

        self.entry_lower_x.textChanged.connect(lambda: self.undo_auto(limit_x=1))
        self.entry_upper_x.textChanged.connect(lambda: self.undo_auto(limit_x=1))
        self.entry_tick_x.textChanged.connect(lambda: self.undo_auto(tick_x=1))
        self.entry_lower_y.textChanged.connect(lambda: self.undo_auto(limit_y=1))
        self.entry_upper_y.textChanged.connect(lambda: self.undo_auto(limit_y=1))
        self.entry_tick_y.textChanged.connect(lambda: self.undo_auto(tick_y=1))
        self.entry_lower_x_2.textChanged.connect(lambda: self.undo_auto(limit_x=1))
        self.entry_upper_x_2.textChanged.connect(lambda: self.undo_auto(limit_x=1))
        self.entry_tick_x_2.textChanged.connect(lambda: self.undo_auto(tick_x=1))
        self.entry_lower_y_2.textChanged.connect(lambda: self.undo_auto(limit_y=1))
        self.entry_upper_y_2.textChanged.connect(lambda: self.undo_auto(limit_y=1))
        self.entry_tick_y_2.textChanged.connect(lambda: self.undo_auto(tick_y=1))

        self.autolimit_x = 1
        self.autotick_x = 0
        self.autolimit_y = 1
        self.autotick_y = 0

        self.shortcut1 = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+L"), self)
        self.shortcut1.activated.connect(self.openfromfile)
        self.shortcut2 = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), self)
        self.shortcut2.activated.connect(self.saveformat)
        self.shortcut3 = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self)
        self.shortcut3.activated.connect(self.output)
        self.shortcut4 = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Enter), self)
        self.shortcut4.activated.connect(self.plot)

        plt.rcParams['mathtext.rm'] = 'Bitstream Vera Sans'
        plt.rcParams['mathtext.it'] = 'Bitstream Vera Sans:italic'
        plt.rcParams['mathtext.bf'] = 'Bitstream Vera Sans:bold'
        self.mplplot = PlotCanvas(self.figure_frame, 7, 7)
        self.figure = self.mplplot.fig
        self.theplot = self.mplplot.plot
        self.plot_twinx = self.mplplot.plot_twinx
        self.plot_twiny = self.mplplot.plot_twiny
        self.figure_layout.addWidget(self.mplplot)
        self.update_figure_params(self.colortheme)

        self.fitline = []
        self.fitline_x = []
        self.fitline_y = []
        self.numberofdata = 0
        self.firsttimeplot = True
        self.checkplot_list, self.title_list, self.color_list, self.linetype_list, self.axis_list = [], [], [], [], []

        self.checkplot1, self.checkplot2, self.checkplot3, self.checkplot4, self.checkplot5, \
        self.checkplot6, self.checkplot7, self.checkplot8, self.checkplot9, self.checkplot10, \
        self.checkplot11, self.checkplot12, self.checkplot13, self.checkplot14, self.checkplot15, \
        self.checkplot16, self.checkplot17, self.checkplot18, self.checkplot19, self.checkplot20, \
        self.checkplot21, self.checkplot22, self.checkplot23 \
            = QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), \
              QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), \
              QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox()
        self.datasource1, self.datasource2, self.datasource3, self.datasource4, self.datasource5, \
        self.datasource6, self.datasource7, self.datasource8, self.datasource9, self.datasource10, \
        self.datasource11, self.datasource12, self.datasource13, self.datasource14, self.datasource15, \
        self.datasource16, self.datasource17, self.datasource18, self.datasource19, self.datasource20, \
        self.datasource21, self.datasource22, self.datasource23 \
            = QLabel(), QLabel(), QLabel(), QLabel(), QLabel(), QLabel(), QLabel(), QLabel(), \
              QLabel(), QLabel(), QLabel(), QLabel(), QLabel(), QLabel(), QLabel(), QLabel(), \
              QLabel(), QLabel(), QLabel(), QLabel(), QLabel(), QLabel(), QLabel()
        self.entry_title_1, self.entry_title_2, self.entry_title_3, self.entry_title_4, self.entry_title_5, \
        self.entry_title_6, self.entry_title_7, self.entry_title_8, self.entry_title_9, self.entry_title_10, \
        self.entry_title_11, self.entry_title_12, self.entry_title_13, self.entry_title_14, self.entry_title_15, \
        self.entry_title_16, self.entry_title_17, self.entry_title_18, self.entry_title_19, self.entry_title_20, \
        self.entry_title_21, self.entry_title_22, self.entry_title_23 \
            = QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), \
              QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), \
              QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit()
        self.coloroption1, self.coloroption2, self.coloroption3, self.coloroption4, self.coloroption5, \
        self.coloroption6, self.coloroption7, self.coloroption8, self.coloroption9, self.coloroption10, \
        self.coloroption11, self.coloroption12, self.coloroption13, self.coloroption14, self.coloroption15, \
        self.coloroption16, self.coloroption17, self.coloroption18, self.coloroption19, self.coloroption20, \
        self.coloroption21, self.coloroption22, self.coloroption23 \
            = QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), \
              QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), \
              QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox()
        self.linetypeoption1, self.linetypeoption2, self.linetypeoption3, self.linetypeoption4, self.linetypeoption5, \
        self.linetypeoption6, self.linetypeoption7, self.linetypeoption8, self.linetypeoption9, self.linetypeoption10, \
        self.linetypeoption11, self.linetypeoption12, self.linetypeoption13, self.linetypeoption14, self.linetypeoption15, \
        self.linetypeoption16, self.linetypeoption17, self.linetypeoption18, self.linetypeoption19, self.linetypeoption20, \
        self.linetypeoption21, self.linetypeoption22, self.linetypeoption23 \
            = QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), \
              QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), \
              QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox()
        self.axisoption1, self.axisoption2, self.axisoption3, self.axisoption4, self.axisoption5, \
        self.axisoption6, self.axisoption7, self.axisoption8, self.axisoption9, self.axisoption10, \
        self.axisoption11, self.axisoption12, self.axisoption13, self.axisoption14, self.axisoption15, \
        self.axisoption16, self.axisoption17, self.axisoption18, self.axisoption19, self.axisoption20, \
        self.axisoption21, self.axisoption22, self.axisoption23 \
            = QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), \
              QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), \
              QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox()

        self.available_colors = ['blue', 'red', 'orange', 'green', 'purple', 'yellow', 'pink', 'black', 'white']
        self.available_linetypes = ['-', '-.', ':']
        self.available_axis = ['Main', 'Second X', 'Second Y']
        for line in range(1, 24):
            getattr(self, "checkplot{}".format(line)).setChecked(True)
            getattr(self, "datasource{}".format(line)).setText("")
            getattr(self, "datasource{}".format(line)).setFixedWidth(130)
            getattr(self, "entry_title_{}".format(line)).setText("")
            getattr(self, "entry_title_{}".format(line)).setFixedWidth(130)
            getattr(self, "coloroption{}".format(line)).addItems(self.available_colors)
            getattr(self, "coloroption{}".format(line)).setCurrentIndex(0)
            getattr(self, "coloroption{}".format(line)).setFixedWidth(60)
            getattr(self, "linetypeoption{}".format(line)).addItems(self.available_linetypes)
            getattr(self, "linetypeoption{}".format(line)).setCurrentIndex(0)
            getattr(self, "linetypeoption{}".format(line)).setFixedWidth(30)
            getattr(self, "axisoption{}".format(line)).addItems(self.available_axis)
            getattr(self, "axisoption{}".format(line)).setCurrentIndex(0)
            getattr(self, "axisoption{}".format(line)).setFixedWidth(30)

        self.legend_location = 'upper right'
        self.legend_options = ['best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left',
                               'center right', 'lower center', 'upper center', 'center']
        self.legendoption.addItems(self.legend_options)
        self.legendoption.setCurrentIndex(0)

        self.font_options = ['Helvetica', 'Arial', 'Times New Roman', 'Cursive']
        self.font_options.extend(matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf'))
        self.fontoption.addItems(self.font_options)
        try:
            self.fontoption.setCurrentIndex(self.font_options.index("Helvetica"))
        except ValueError:
            self.fontoption.setCurrentIndex(0)

        self.Xs = []
        self.Ys = []

        self.format = ['6.4', '4.8', 'True', '0.08', '0.95', '0.1', '0.95', 'Wavenumber ($cm^{-1}$)',
                       'False', '1', '500', '400', '6000', 'Transmission (%)', 'False', '1', '10', '0',
                       '100', 'False', 'False', 'False', 'False', 'Wavenumber ($cm^{-1}$)', 'False', '1',
                       '500', '400', '6000', 'False', 'False', 'False', 'False', 'Transmission (%)',
                       'False', '1', '10', '0', '100', 'True', 'False', 'False', '1.5', 'best',
                       'Helvetica', '10', '10', '10']

    def init_after_launch(self):

        """Postpone part of the initialization process after the window is shown.
         Do not include this function in self.__init(). """

        pass

    def update_figure_params(self, colortheme):
        if colortheme == 0:
            for ax in [self.theplot, self.plot_twinx, self.plot_twiny]:
                ax.spines['bottom'].set_color('black')
                ax.spines['top'].set_color('black')
                ax.spines['left'].set_color('black')
                ax.spines['right'].set_color('black')
                ax.xaxis.label.set_color('black')
                ax.yaxis.label.set_color('black')
                ax.tick_params(axis='x', which='both', colors='black')
                ax.tick_params(axis='y', which='both', colors='black')
                ax.set_facecolor('white')
            self.figure.set_facecolor('white')
            plt.rcParams.update({
                "savefig.facecolor": "white",
                "savefig.edgecolor": "white"})

        elif colortheme == 1:
            for ax in [self.theplot, self.plot_twinx, self.plot_twiny]:
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white')
                ax.spines['left'].set_color('white')
                ax.spines['right'].set_color('white')
                ax.xaxis.label.set_color('white')
                ax.yaxis.label.set_color('white')
                ax.tick_params(axis='x', which='both', colors='white')
                ax.tick_params(axis='y', which='both', colors='white')
                ax.set_facecolor('#31363b')
            self.figure.set_facecolor('#31363b')
            plt.rcParams.update({
                "savefig.facecolor": "#31363b",
                "savefig.edgecolor": "#31363b"})

        elif colortheme == 2:
            plt.style.use('dark_background')  # Default Matplotlib theme.

        self.mplplot.draw()

    def vline(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.VLine)
        frame.setFrameShadow(QFrame.Sunken)
        return frame

    def openfromfile(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        file = dlg.getOpenFileName(self, 'Open file', self.osdir, "CSV files (*.CSV *.csv)")

        if file[0] == "":
            return

        self.filename = file[0]

        i = -1
        while self.filename[i] != '/':
            i -= 1
        self.filename = self.filename[i + 1:None]

        if self.filename[-4:None] != ".csv" and self.filename[-4:None] != ".CSV":
            self.addlog('{} format is not supported. Please select a .CSV file to open.'.format(self.filename[-4:None]),
                        self.warningcolor2)
            return
        # Deside how many data set are in this csv file.
        with open(file[0], 'r') as f:
            reader = csv.reader(f, delimiter=',')
            number_of_dataset = 0
            for row in reader:
                if len(row) < 2:
                    continue
                else:
                    number_of_dataset = len(row) - 1
                    break
        f.close()
        # Read the data for each data set
        list_of_titles = []
        for i in range(number_of_dataset):
            with open(file[0], 'r') as f:   # The file has to be opened and closed every time we read one dataset.
                reader = csv.reader(f, delimiter=',')
                X, Y = [], []
                for row in reader:
                    if len(row) < 2:
                        continue
                    try:
                        X.append(float(row[0]))
                        Y.append(float(row[i+1]))
                    except ValueError:
                        list_of_titles.append(row[i+1])
                self.Xs.append(X)
                self.Ys.append(Y)

                getattr(self, "datasource{}".format(self.numberofdata + 1)).setText(self.filename)
                if not list_of_titles:
                    if i != 0:
                        title = self.filename[:-4] + "({})".format(i)
                    else:
                        title = self.filename[:-4]
                else:
                    title = list_of_titles[-1]
                getattr(self, "entry_title_{}".format(self.numberofdata + 1)).setText(title)

                self.dataframe_layout.addWidget(getattr(self, "checkplot{}".format(self.numberofdata + 1)),
                                                self.numberofdata, 0)
                vl = self.vline()
                self.dataframe_layout.addWidget(vl, self.numberofdata, 1)
                self.dataframe_layout.addWidget(getattr(self, "datasource{}".format(self.numberofdata + 1)),
                                                self.numberofdata, 2)
                vl = self.vline()
                self.dataframe_layout.addWidget(vl, self.numberofdata, 3)
                label = QLabel("Name: ")
                label.setAlignment(Qt.AlignRight)
                label.setAlignment(Qt.AlignVCenter)
                self.dataframe_layout.addWidget(label, self.numberofdata, 4)
                self.dataframe_layout.addWidget(getattr(self, "entry_title_{}".format(self.numberofdata + 1)),
                                                self.numberofdata, 5)
                vl = self.vline()
                self.dataframe_layout.addWidget(vl, self.numberofdata, 6)
                label = QLabel("Color: ")
                label.setAlignment(Qt.AlignRight)
                label.setAlignment(Qt.AlignVCenter)
                self.dataframe_layout.addWidget(label, self.numberofdata, 7)
                self.dataframe_layout.addWidget(getattr(self, "coloroption{}".format(self.numberofdata + 1)),
                                                self.numberofdata, 8)
                vl = self.vline()
                self.dataframe_layout.addWidget(vl, self.numberofdata, 9)
                label = QLabel("Line Type: ")
                label.setAlignment(Qt.AlignRight)
                label.setAlignment(Qt.AlignVCenter)
                self.dataframe_layout.addWidget(label, self.numberofdata, 10)
                self.dataframe_layout.addWidget(getattr(self, "linetypeoption{}".format(self.numberofdata + 1)),
                                                self.numberofdata, 11)
                vl = self.vline()
                self.dataframe_layout.addWidget(vl, self.numberofdata, 12)
                label = QLabel("Axis: ")
                label.setAlignment(Qt.AlignRight)
                label.setAlignment(Qt.AlignVCenter)
                self.dataframe_layout.addWidget(label, self.numberofdata, 13)
                self.dataframe_layout.addWidget(getattr(self, "axisoption{}".format(self.numberofdata + 1)),
                                                self.numberofdata, 14)
                vl = self.vline()
                self.dataframe_layout.addWidget(vl, self.numberofdata, 15)

                self.addlog('Added data {}'.format(title))
                self.numberofdata += 1

            f.close()

    def output(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        file = dlg.getSaveFileName(self, 'Output figure', self.osdir, "PNG files (*.png)")

        if file[0] == "":
            return
        self.figure.savefig(file[0], dpi=self.dpi)

    def openformat(self):

        """Open existing format settings file. (.csv files.)"""

        self.format_dir = resource_path("Preload_Matplotter_Format")

        filelist = []
        for item in os.listdir(self.format_dir):
            if item[-4:None] == ".csv":
                filelist.append(item[0:-4])

        if filelist == []:
            self.addlog('No format file is found. Check if "Preload_Matplotter_Format" folder exists.',
                        self.warningcolor1)
            return

        filelist = sorted(filelist)

        window_load = loadformat(self, filelist)
        window_load.show()

        yesorno = window_load.exec_()  # Crucial to capture the result. 1 for Yes and 0 for No.

        result = window_load.result
        if result >= 0:
            self.formatname = filelist[result] + ".csv"

            filename = self.format_dir + "/" + self.formatname

            with open(filename, 'r') as f:
                reader = csv.reader(f, delimiter=',')
                for row in reader:
                    if len(row) < 2:
                        continue
                    try:
                        self.format = row
                    except ValueError:
                        pass
            f.close()

            self.applyformat()
            self.addlog('Loaded figure format: {}.'.format(self.formatname[0:-4]))
            return
        else:
            pass

    def applyformat(self):
        def bool_str(string):
            if string == "True":
                return True
            else:
                return False
        try:
            self.entry_ratio.setText("{},{}".format(self.format[0], self.format[1]))
            self.check_grid.setChecked(bool_str(self.format[2]))
            self.entry_margin_l.setText(self.format[3])
            self.entry_margin_r.setText(self.format[4])
            self.entry_margin_b.setText(self.format[5])
            self.entry_margin_t.setText(self.format[6])
            self.entry_title_x.setText(self.format[7])
            self.checkBox_logx.setChecked(bool_str(self.format[8]))
            self.entry_minor_x.setText(self.format[9])
            self.entry_tick_x.setText(self.format[10])
            self.entry_lower_x.setText(self.format[11])
            self.entry_upper_x.setText(self.format[12])
            self.entry_title_y.setText(self.format[13])
            self.checkBox_logy.setChecked(bool_str(self.format[14]))
            self.entry_minor_y.setText(self.format[15])
            self.entry_tick_y.setText(self.format[16])
            self.entry_lower_y.setText(self.format[17])
            self.entry_upper_y.setText(self.format[18])
            self.checkBox_tt.setChecked(bool_str(self.format[19]))
            self.checkBox_tl.setChecked(bool_str(self.format[20]))
            self.checkBox_samex.setChecked(bool_str(self.format[21]))
            self.checkBox_titlex.setChecked(bool_str(self.format[22]))
            self.entry_title_x_2.setText(self.format[23])
            self.checkBox_logx_2.setChecked(bool_str(self.format[24]))
            self.entry_minor_x_2.setText(self.format[25])
            self.entry_tick_x_2.setText(self.format[26])
            self.entry_lower_x_2.setText(self.format[27])
            self.entry_upper_x_2.setText(self.format[28])
            self.checkBox_rt.setChecked(bool_str(self.format[29]))
            self.checkBox_rl.setChecked(bool_str(self.format[30]))
            self.checkBox_samey.setChecked(bool_str(self.format[31]))
            self.checkBox_titley.setChecked(bool_str(self.format[32]))
            self.entry_title_y_2.setText(self.format[33])
            self.checkBox_logy_2.setChecked(bool_str(self.format[34]))
            self.entry_minor_y_2.setText(self.format[35])
            self.entry_tick_y_2.setText(self.format[36])
            self.entry_lower_y_2.setText(self.format[37])
            self.entry_upper_y_2.setText(self.format[38])
            self.checkBox_legend.setChecked(bool_str(self.format[39]))
            self.checkBox_legendshadow.setChecked(bool_str(self.format[40]))
            self.checkBox_legendframe.setChecked(bool_str(self.format[41]))
            self.entry_linewidth.setText(self.format[42])
            self.legendoption.setCurrentIndex(self.legend_options.index(self.format[43]))
            self.entry_legendfont.setText(self.format[44])
            self.entry_titlefont.setText(self.format[45])
            self.entry_tickfont.setText(self.format[46])
        except:
            self.addlog("Format file damaged.", self.warningcolor1)

    def getformat(self):

        def bool_checkbox(checkbox):
            if checkbox.isChecked():
                return "True"
            else:
                return "False"
        RatioParts = [str(s) for s in self.entry_ratio.text().split(',')]
        self.format[0] = RatioParts[0]
        self.format[1] = RatioParts[1]
        self.format[2] = bool_checkbox(self.check_grid)
        self.format[3] = self.entry_margin_l.text()
        self.format[4] = self.entry_margin_r.text()
        self.format[5] = self.entry_margin_b.text()
        self.format[6] = self.entry_margin_t.text()
        self.format[7] = self.entry_title_x.text()
        self.format[8] = bool_checkbox(self.checkBox_logx)
        self.format[9] = self.entry_minor_x.text()
        self.format[10] = self.entry_tick_x.text()
        self.format[11] = self.entry_lower_x.text()
        self.format[12] = self.entry_upper_x.text()
        self.format[13] = self.entry_title_y.text()
        self.format[14] = bool_checkbox(self.checkBox_logy)
        self.format[15] = self.entry_minor_y.text()
        self.format[16] = self.entry_tick_y.text()
        self.format[17] = self.entry_lower_y.text()
        self.format[18] = self.entry_upper_y.text()
        self.format[19] = bool_checkbox(self.checkBox_tt)
        self.format[20] = bool_checkbox(self.checkBox_tl)
        self.format[21] = bool_checkbox(self.checkBox_samex)
        self.format[22] = bool_checkbox(self.checkBox_titlex)
        self.format[23] = self.entry_title_x_2.text()
        self.format[24] = bool_checkbox(self.checkBox_logx_2)
        self.format[25] = self.entry_minor_x_2.text()
        self.format[26] = self.entry_tick_x_2.text()
        self.format[27] = self.entry_lower_x_2.text()
        self.format[28] = self.entry_upper_x_2.text()
        self.format[29] = bool_checkbox(self.checkBox_rt)
        self.format[30] = bool_checkbox(self.checkBox_rl)
        self.format[31] = bool_checkbox(self.checkBox_samey)
        self.format[32] = bool_checkbox(self.checkBox_titley)
        self.format[33] = self.entry_title_y_2.text()
        self.format[34] = bool_checkbox(self.checkBox_logy_2)
        self.format[35] = self.entry_minor_y_2.text()
        self.format[36] = self.entry_tick_y_2.text()
        self.format[37] = self.entry_lower_y_2.text()
        self.format[38] = self.entry_upper_y_2.text()
        self.format[39] = bool_checkbox(self.checkBox_legend)
        self.format[40] = bool_checkbox(self.checkBox_legendshadow)
        self.format[41] = bool_checkbox(self.checkBox_legendframe)
        self.format[42] = self.entry_linewidth.text()
        self.format[43] = self.legend_options[self.legendoption.currentIndex()]
        self.format[44] = self.entry_legendfont.text()
        self.format[45] = self.entry_titlefont.text()
        self.format[46] = self.entry_tickfont.text()

    def saveformat(self):

        """Save current format settings to file. (.csv files.)"""

        self.getformat()
        self.format_dir = resource_path("Preload_Matplotter_Format")

        filelist = []
        for item in os.listdir(self.format_dir):
            if item[-4:None] == ".csv":
                filelist.append(item[0:-4])

        if filelist == []:
            self.addlog('No format file is found. Check if "Preload_Matplotter_Format" folder exists.',
                        self.warningcolor1)
            return

        filelist = sorted(filelist)

        window_load = saveformat(self, filelist)
        window_load.show()

        yesorno = window_load.exec_()  # Crucial to capture the result. 1 for Yes and 0 for No.

        if yesorno:
            result = window_load.result
            self.formatname = result + ".csv"

            filename = self.format_dir + "/" + self.formatname

            with open(filename, 'w') as f:
                writer = csv.writer(f, delimiter=',')
                writer.writerow(self.format)
            f.close()

            self.applyformat()
            self.addlog('Saved figure format: {}.'.format(self.formatname[0:-4]))

    def settings(self):
        """Cutomized Settings. """

        window_settings = Matplottersettings(self, self.dpi, self.colortheme)
        window_settings.show()

        yesorno = window_settings.exec_()  # Crucial to capture the result. 1 for Yes and 0 for No.

        if yesorno == 1:
            self.dpi = window_settings.dpi
            self.colortheme = window_settings.index1
            self.update_figure_params(self.colortheme)
            self.plot()

    def undo_auto(self, limit_x=0, tick_x=0, limit_y=0, tick_y=0):
        if limit_x:
            self.autolimit_x = 0
        if tick_x:
            self.autotick_x = 0
        if limit_y:
            self.autolimit_y = 0
        if tick_y:
            self.autotick_y = 0

    def getdata(self):
        self.checkplot_list, self.title_list, self.color_list, self.linetype_list, self.axis_list = [], [], [], [], []

        for i in range(1, self.numberofdata + 1):
            self.checkplot_list.append(getattr(self, "checkplot{}".format(i)).isChecked())
            self.title_list.append(getattr(self, "entry_title_{}".format(i)).text())
            self.color_list.append(self.available_colors[getattr(self, "coloroption{}".format(i)).currentIndex()])
            self.linetype_list.append(self.available_linetypes[getattr(self, "linetypeoption{}".format(i)).currentIndex()])
            self.axis_list.append(self.available_axis[getattr(self, "axisoption{}".format(i)).currentIndex()])

    def plot(self, limit_x=0, tick_x=0, limit_y=0, tick_y=0):
        self.firsttimeplot = False

        # Modify font size
        for ax in [self.theplot, self.plot_twinx, self.plot_twiny]:
            for item in ([ax.title, ax.xaxis.label, ax.yaxis.label]):
                item.set_fontsize(int(self.entry_titlefont.text()))
                item.set_fontname(self.font_options[self.fontoption.currentIndex()])
            for item in (ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(int(self.entry_tickfont.text()))
                item.set_fontname(self.font_options[self.fontoption.currentIndex()])
        plt.rcParams['mathtext.rm'] = self.font_options[self.fontoption.currentIndex()]
        self.mplplot.draw()

        self.getdata()

        if len(self.Xs) == 0:
            return

        if limit_x:
            self.autolimit_x = 1
            min_x = min(self.Xs[0])
            max_x = max(self.Xs[0])
            min_x_2 = min(self.Xs[0])
            max_x_2 = max(self.Xs[0])
            for i, X in enumerate(self.Xs):
                if not self.checkplot_list[i]:
                    continue
                min_xs = min(self.Xs[i])
                max_xs = max(self.Xs[i])
                if self.axis_list[i] == 'Main' or self.axis_list[i] == 'Second Y':
                    if min_xs < min_x:
                        min_x = min_xs
                    if max_xs > max_x:
                        max_x = max_xs
                    self.entry_lower_x.setText(str(min_x))
                    self.entry_upper_x.setText(str(max_x))
                elif self.axis_list[i] == 'Second X':
                    if min_xs < min_x_2:
                        min_x_2 = min_xs
                    if max_xs > max_x_2:
                        max_x_2 = max_xs
                    self.entry_lower_x_2.setText(str(min_x))
                    self.entry_upper_x_2.setText(str(max_x))

        if tick_x:
            self.autotick_x = 1
        if limit_y:
            self.autolimit_y = 1
            min_y = min(self.Ys[0])
            max_y = max(self.Ys[0])
            min_y_2 = min(self.Ys[0])
            max_y_2 = max(self.Ys[0])
            for i, Y in enumerate(self.Ys):
                if not self.checkplot_list[i]:
                    continue
                min_ys = min(self.Ys[i])
                max_ys = max(self.Ys[i])
                if self.axis_list[i] == 'Main' or self.axis_list[i] == 'Second X':
                    if min_ys < min_y:
                        min_y = min_ys
                    if max_ys > max_y:
                        max_y = max_ys
                    self.entry_lower_y.setText(str(min_y))
                    self.entry_upper_y.setText(str(max_y))
                elif self.axis_list[i] == 'Second Y':
                    if min_ys < min_y_2:
                        min_y_2 = min_ys
                    if max_ys > max_y_2:
                        max_y_2 = max_ys
                    self.entry_lower_y_2.setText(str(min_y_2))
                    self.entry_upper_y_2.setText(str(max_y_2))
        if tick_y:
            self.autotick_y = 1

        self.figure.subplots_adjust(left=float(self.entry_margin_l.text()), bottom=float(self.entry_margin_b.text()),
                                    right=float(self.entry_margin_r.text()), top=float(self.entry_margin_t.text()))

        RatioParts = [float(s) for s in self.entry_ratio.text().split(',')]
        self.figure.set_size_inches(RatioParts[0], RatioParts[1], forward=True)

        # Remove all legend
        try:
            self.theplot.get_legend().remove()
        except AttributeError:
            pass
        # Remove all previous lines
        for i in range(len(self.fitline)):
            try:
                self.fitline[i].pop(0).remove()
            except (AttributeError, IndexError) as error:
                pass
        for i in range(len(self.fitline_x)):
            try:
                self.fitline_x[i].pop(0).remove()
            except (AttributeError, IndexError) as error:
                pass
        for i in range(len(self.fitline_y)):
            try:
                self.fitline_y[i].pop(0).remove()
            except (AttributeError, IndexError) as error:
                pass
        self.fitline = []
        self.fitline_x = []
        self.fitline_y = []

        # Plot All
        for i, X in enumerate(self.Xs):
            if not self.checkplot_list[i]:
                continue
            if self.axis_list[i] == 'Main':
                args = [X, self.Ys[i], self.color_list[i], self.title_list[i], self.entry_title_x.text(), self.entry_title_y.text(),
                        None, [float(self.entry_lower_x.text()), float(self.entry_upper_x.text())],
                        [float(self.entry_lower_y.text()), float(self.entry_upper_y.text())], float(self.entry_tick_x.text()),
                        float(self.entry_tick_y.text()), int(self.entry_minor_x.text()), int(self.entry_minor_y.text()),
                        self.autolimit_x, self.autotick_x, self.autolimit_y, self.autotick_y,
                        self.checkBox_logx.isChecked(), self.checkBox_logy.isChecked(),
                        self.check_grid.isChecked(), self.linetype_list[i]]

                Plot = PlotAndShow(self.mplplot, self.theplot, self.fitline, True, *args)
                self.fitline.append(Plot.fitline)

            elif self.axis_list[i] == 'Second X':
                if self.checkBox_samex.isChecked():
                    args = [X, self.Ys[i], self.color_list[i], self.title_list[i], self.entry_title_x.text(),
                            self.entry_title_y.text(),
                            None, [float(self.entry_lower_x.text()), float(self.entry_upper_x.text())],
                            [float(self.entry_lower_y.text()), float(self.entry_upper_y.text())],
                            float(self.entry_tick_x.text()),
                            float(self.entry_tick_y.text()), int(self.entry_minor_x.text()),
                            int(self.entry_minor_y.text()),
                            self.autolimit_x, self.autotick_x, self.autolimit_y, self.autotick_y,
                            self.checkBox_logx.isChecked(), self.checkBox_logy.isChecked(),
                            self.check_grid.isChecked(), self.linetype_list[i]]
                else:
                    args = [X, self.Ys[i], self.color_list[i], self.title_list[i], self.entry_title_x_2.text(),
                            self.entry_title_y.text(),
                            None, [float(self.entry_lower_x_2.text()), float(self.entry_upper_x_2.text())],
                            [float(self.entry_lower_y.text()), float(self.entry_upper_y.text())],
                            float(self.entry_tick_x_2.text()),
                            float(self.entry_tick_y.text()), int(self.entry_minor_x_2.text()), int(self.entry_minor_y.text()),
                            self.autolimit_x, self.autotick_x, self.autolimit_y, self.autotick_y,
                            self.checkBox_logx_2.isChecked(), self.checkBox_logy.isChecked(),
                            self.check_grid.isChecked(), self.linetype_list[i]]

                Plot = PlotAndShow(self.mplplot, self.plot_twiny, self.fitline, True, *args)
                self.fitline_y.append(Plot.fitline)
                self.plot_twiny.get_xaxis().set_visible(True)
                if self.checkBox_titlex.isChecked():
                    self.plot_twiny.xaxis.label.set_visible(True)
                    self.plot_twiny.set_xlabel(self.entry_title_x_2.text())
                else:
                    self.plot_twiny.xaxis.label.set_visible(False)

            elif self.axis_list[i] == 'Second Y':
                if self.checkBox_samey.isChecked():
                    args = [X, self.Ys[i], self.color_list[i], self.title_list[i], self.entry_title_x.text(),
                            self.entry_title_y.text(),
                            None, [float(self.entry_lower_x.text()), float(self.entry_upper_x.text())],
                            [float(self.entry_lower_y.text()), float(self.entry_upper_y.text())],
                            float(self.entry_tick_x.text()),
                            float(self.entry_tick_y.text()), int(self.entry_minor_x.text()),
                            int(self.entry_minor_y.text()),
                            self.autolimit_x, self.autotick_x, self.autolimit_y, self.autotick_y,
                            self.checkBox_logx.isChecked(), self.checkBox_logy.isChecked(),
                            self.check_grid.isChecked(), self.linetype_list[i]]
                else:
                    args = [X, self.Ys[i], self.color_list[i], self.title_list[i], self.entry_title_x.text(),
                            self.entry_title_y_2.text(),
                            None, [float(self.entry_lower_x.text()), float(self.entry_upper_x.text())],
                            [float(self.entry_lower_y_2.text()), float(self.entry_upper_y_2.text())],
                            float(self.entry_tick_x.text()),
                            float(self.entry_tick_y_2.text()), int(self.entry_minor_x.text()), int(self.entry_minor_y_2.text()),
                            self.autolimit_x, self.autotick_x, self.autolimit_y, self.autotick_y,
                            self.checkBox_logx.isChecked(), self.checkBox_logy_2.isChecked(),
                            self.check_grid.isChecked(), self.linetype_list[i]]

                Plot = PlotAndShow(self.mplplot, self.plot_twinx, self.fitline, True, *args)
                self.fitline_x.append(Plot.fitline)
                self.plot_twinx.get_yaxis().set_visible(True)
                if self.checkBox_titley.isChecked():
                    self.plot_twinx.yaxis.label.set_visible(True)
                    self.plot_twinx.set_ylabel(self.entry_title_y_2.text())
                else:
                    self.plot_twinx.yaxis.label.set_visible(False)

        if self.checkBox_legend.isChecked():
            self.legend_location = self.legend_options[self.legendoption.currentIndex()]
            lines, labels = self.theplot.get_legend_handles_labels()
            lines2, labels2 = self.plot_twinx.get_legend_handles_labels()
            lines3, labels3 = self.plot_twiny.get_legend_handles_labels()
            legend = self.theplot.legend(lines+lines2+lines3, labels+labels2+labels3, loc=self.legend_location,
                                         shadow=self.checkBox_legendshadow.isChecked(),
                                         frameon=self.checkBox_legendframe.isChecked())
            frame = legend.get_frame()
            frame.set_facecolor('none')
            # Set the font
            if self.colortheme == 0:
                legendcolor = 'black'
            else:
                legendcolor = 'white'
            for label in legend.get_texts():
                label.set_fontsize(int(self.entry_legendfont.text()))
                label.set_fontname(self.font_options[self.fontoption.currentIndex()])
                label.set_color(legendcolor)

            for label in legend.get_lines():
                label.set_linewidth(float(self.entry_linewidth.text()))

        self.theplot.tick_params(axis='both', which='both', labelleft='on', labelright='off', labeltop='off',
                                 labelbottom='on', direction='in')
        if self.checkBox_tt.isChecked():
            self.plot_twinx.xaxis.set_ticks_position('top')
        if self.checkBox_rt.isChecked():
            self.plot_twiny.yaxis.set_ticks_position('right')

        if self.checkBox_tl.isChecked():
            toplb = 'on'
        else:
            toplb = 'off'
        self.plot_twiny.tick_params(axis='both', which='both', labelleft='on', labelright='off', labeltop=toplb,
                                    labelbottom='off', direction='in')
        if self.checkBox_rl.isChecked():
            rightlb = 'on'
        else:
            rightlb = 'off'
        self.plot_twinx.tick_params(axis='both', which='both', labelleft='off', labelright=rightlb, labeltop='off',
                                    labelbottom='on', direction='in')

        self.mplplot.draw()

    def clearalldata(self):

        """Clear everything. """

        def clearornotfunc():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)

            msg.setText("Clear everything?")
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)

            result = msg.exec_()
            if result == QMessageBox.Ok:
                return 1
            else:
                return 0

        clearornot = clearornotfunc()
        if clearornot == 1:
            for i in reversed(range(self.maingrid.count())):
                self.maingrid.itemAt(i).widget().setParent(None)
            # self.__init__(self.root, self.masterroot)
            obj = Mat_Plotter_GUI(self.root, self.masterroot)
            self.root.setWidget(obj)
            self.root.showMaximized()
            self.root.show()
            self.addlog('-' * 160, "blue")
        else:
            pass

