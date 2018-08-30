import os
import sys
import math
from shutil import copyfile
import fileinput
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
qttoolfile = resource_path(os.path.join("Tool_Creator", "Tool_Creator.ui"))  # GUI layout file.
Ui_tool, QtBaseClass = uic.loadUiType(qttoolfile)


class Tool_Creator_GUI(QWidget, Ui_tool):

    """Main GUI window."""

    def __init__(self, root, masterroot):
        QWidget.__init__(self)
        Ui_tool.__init__(self)
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

        self.buttoncreate.clicked.connect(self.create_tool)
        self.buttonclear.clicked.connect(self.clearalldata)

        preview1 = QPixmap(resource_path('Tool_Creator/1.png'))
        # preview1 = preview1.scaled(480, 300, transformMode=Qt.SmoothTransformation)
        self.lb1.setPixmap(preview1)
        self.lb = QLabel()
        self.lb1.setScaledContents(True)
        self.lb1.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        preview2 = QPixmap(resource_path('Tool_Creator/2.png'))
        # preview2 = preview2.scaled(480, 300, transformMode=Qt.SmoothTransformation)
        self.lb2.setPixmap(preview2)
        self.lb2.setScaledContents(True)
        self.lb2.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

    def init_after_launch(self):

        """Postpone part of the initialization process after the window is shown.
         Do not include this function in self.__init(). """

        self.databasepreview()

    def create_tool(self):
        name = self.lb_name.text()
        description = self.lb_des.text()
        author = self.lb_author.text()
        email = self.lb_email.text()

        def createornotfunc():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)

            msg.setText('Create a new tool named "{}"?'.format(name))
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)

            result = msg.exec_()
            if result == QMessageBox.Ok:
                return 1
            else:
                return 0

        clearornot = createornotfunc()
        if clearornot == 0:
            return

        if name[-1] == " ":
            self.addlog("Please remove any blank space at the end of tool name.", self.warningcolor2)
            return

        name_underscore = name.replace(" ", "_")
        name_no_space = name.replace(" ", "")
        base_path = os.path.abspath(".")
        try:
            os.mkdir(os.path.join(base_path, name_underscore))
        except FileExistsError:
            self.addlog('Tool "{}"already exists.'.format(name), self.warningcolor1)

        for ext in ["ui", "py"]:
            source = resource_path(os.path.join("Tool_Creator", "example.{}".format(ext)))
            dst = resource_path(os.path.join(name_underscore, "{}.{}".format(name_underscore, ext)))
            copyfile(source, dst)

        source = resource_path(os.path.join("Tool_Creator", "example.txt"))
        dst = resource_path(os.path.join(name_underscore, "help.txt"))
        copyfile(source, dst)

        source = resource_path(os.path.join("Tool_Creator", "__init__.py"))
        dst = resource_path(os.path.join(name_underscore, "__init__.py"))
        copyfile(source, dst)

        new_module = '("{}.{}", "{}_GUI", "{}")'.format(name_underscore, name_underscore, name_underscore, name)

        # Modify Modules.py
        with open(os.path.join(base_path, "Modules.py")) as f:
            lines = f.readlines()

        with open(os.path.join(base_path, "Modules.py"), "w") as f:
            last_line = 0
            for i, line in enumerate(lines):
                if "Tool_Creator" in line:
                    last_line = i

            lines.insert(last_line, "    " + new_module + ",\n")
            # f.write("\n".join(lines))
            f.write("".join(lines))

        # Define the functon to replace strings in files.
        def replaceAll(file, searchExp, replaceExp):
            for line in fileinput.input(file, inplace=1):
                line = line.replace(searchExp, replaceExp)
                sys.stdout.write(line)

        # Modify the main python file
        py_file_path = resource_path(os.path.join("{}".format(name_underscore), "{}.py".format(name_underscore)))

        replaceAll(py_file_path, "xxxx", "{}".format(name_no_space))
        replaceAll(py_file_path, "Tool_Name", "{}".format(name_underscore))

        # Modify the help.txt file
        txt_file_path = resource_path(os.path.join("{}".format(name_underscore), "help.txt"))

        replaceAll(txt_file_path,"Tool_Name", "{}".format(name))
        replaceAll(txt_file_path,"Author_Name", "{}".format(author))
        replaceAll(txt_file_path,"Email_Address", "{}".format(email))
        replaceAll(txt_file_path,"Description", "{}".format(description))

        self.addlog("Successfully created a new tool: {}! "
                    "Please restart the program in order to see the new tool".format(name), self.warningcolor3)

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
            obj = Tool_Creator_GUI(self.root, self.masterroot)
            self.root.setWidget(obj)
            self.root.showMaximized()
            self.root.show()
            self.addlog('-' * 160, "blue")
        else:
            pass

