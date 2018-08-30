import os
import sys
import math
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
qtxxxxfile = resource_path(os.path.join("Tool_Name", "Tool_Name.ui"))  # GUI layout file.
Ui_xxxx, QtBaseClass = uic.loadUiType(qtxxxxfile)


class Tool_Name_GUI(QWidget, Ui_xxxx):

    """Main GUI window."""

    def __init__(self, root, masterroot):
        QWidget.__init__(self)
        Ui_xxxx.__init__(self)
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

        self.buttonopen.clicked.connect(self.openfromfile)
        self.buttonsave.clicked.connect(self.savetofile)
        self.buttonclear.clicked.connect(self.clearalldata)
        self.buttonsettings.clicked.connect(self.settings)
        self.shortcut1 = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self)
        self.shortcut1.activated.connect(self.openfromfile)
        self.shortcut2 = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), self)
        self.shortcut2.activated.connect(self.savetofile)

    def init_after_launch(self):

        """Postpone part of the initialization process after the window is shown.
         Do not include this function in self.__init(). """

        self.databasepreview()

    def openfromfile(self):
        pass

    def savetofile(self):
        pass

    def settings(self):
        pass

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
            obj = Tool_Name_GUI(self.root, self.masterroot)
            self.root.setWidget(obj)
            self.root.showMaximized()
            self.root.show()
            self.addlog('-' * 160, "blue")
        else:
            pass

