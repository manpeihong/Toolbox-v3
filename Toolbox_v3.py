import os
import sys
import time
import math
import traceback
import configparser
import matplotlib

matplotlib.use("TkAgg")  # This needs to happen before import any other things from matplotlib.
from random import randint
from sys import platform as _platform
import io
from PyQt5 import *
from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from Modules import modules  # Names of all existing modules are stored in a separate file called "Modules.py".

import importlib

__thisversion__ = 0
darkthemeavailable = 1

try:
    import qdarkstyle
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    darkthemeavailable = 0

__version__ = "3.1"
__emailaddress__ = "pman3@uic.edu"


def resource_path(relative_path):  # Define function to import external files when using PyInstaller.
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


qtmainfile = resource_path("mainwindow.ui")  # GUI layout file.
Ui_main, QtBaseClass = uic.loadUiType(qtmainfile)
qtwelcomefile = resource_path("welcome.ui")
Ui_welcome, QtBaseClass = uic.loadUiType(qtwelcomefile)
qthelpfile = resource_path("help.ui")
Ui_help, QtBaseClass = uic.loadUiType(qthelpfile)
qtsettingsfile = resource_path("settings.ui")
Ui_settings, QtBaseClass = uic.loadUiType(qtsettingsfile)
qtguessfile = resource_path("guessnumbers.ui")
Ui_guess, QtBaseClass = uic.loadUiType(qtguessfile)

config = configparser.ConfigParser()
config.read(resource_path('configuration.ini'))
colortheme = int(config["Settings"]["colortheme"])
window_start_view = int(config["Settings"]["window_start_view"])

if darkthemeavailable == 1:
    if colortheme == 1:
        plt.rcParams.update({
            "lines.color": "white",
            "patch.edgecolor": "white",
            "text.color": "white",
            "axes.facecolor": "#31363b",
            "axes.edgecolor": "lightgray",
            "axes.labelcolor": "white",
            "xtick.color": "white",
            "ytick.color": "white",
            "grid.color": "lightgray",
            "figure.facecolor": "#31363b",
            "figure.edgecolor": "#31363b",
            "savefig.facecolor": "#31363b",
            "savefig.edgecolor": "#31363b"})
    elif colortheme == 2:
        plt.style.use('dark_background')  # Default Matplotlib theme.


class welcome_GUI(QWidget, Ui_welcome):
    """Welcome window."""

    def __init__(self):
        QWidget.__init__(self)
        Ui_welcome.__init__(self)
        self.setupUi(self)


class help_GUI(QWidget, Ui_help):
    """Documentation window."""

    def __init__(self):
        QWidget.__init__(self)
        Ui_help.__init__(self)
        self.setupUi(self)

        self.currentindex = 0
        self.numberofpages = 0

        self.stackedWidget.removeWidget(self.page_2)
        self.stackedWidget.setCurrentIndex(self.currentindex)

        self.shortcut1 = QShortcut(QtGui.QKeySequence(Qt.Key_Right), self)
        self.shortcut1.activated.connect(self.next)
        self.shortcut2 = QShortcut(QtGui.QKeySequence(Qt.Key_Left), self)
        self.shortcut2.activated.connect(self.previous)

        if colortheme + darkthemeavailable < 2:
            logo = QPixmap(resource_path('Images/toolbox_b.png'))
        else:
            logo = QPixmap(resource_path('Images/toolbox_w.png'))
        logo = logo.scaled(180, 60, transformMode=Qt.SmoothTransformation)
        self.lb_logo.setPixmap(logo)

        self.textEdit.setStyleSheet("background: rgba(0,0,255,0%)")

        self.load_all_help_files()

    def load_all_help_files(self):
        for module_name, window_type, module_title in modules:
            folder_name = ""
            for i in range(0, len(module_name)):
                if module_name[i] == ".":
                    folder_name = module_name[0:i]
                    break
            try:
                path = resource_path(os.path.join(folder_name, "help.txt"))
                textbox = QTextEdit()
                textbox.setStyleSheet("background: rgba(0,0,255,0%)")
                textbox.setReadOnly(True)
                f = open(path, "r", encoding='utf-8')
                text = f.readlines()
                for line in text:
                    textbox.append(line)
                f.close()
                textbox.verticalScrollBar().setValue(300)
                self.stackedWidget.addWidget(textbox)
                self.numberofpages += 1
            except FileNotFoundError:
                pass

    def next(self):
        if self.currentindex < self.numberofpages:
            self.currentindex += 1
            self.stackedWidget.setCurrentIndex(self.currentindex)

    def previous(self):
        if self.currentindex > 0:
            self.currentindex -= 1
            self.stackedWidget.setCurrentIndex(self.currentindex)


class settings_GUI(QDialog, Ui_settings):
    """Choose the widgets to be included."""

    def __init__(self, root):
        QDialog.__init__(self, root)
        Ui_settings.__init__(self)
        self.setupUi(self)
        if _platform == "darwin":
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        x = app.desktop().screenGeometry().center().x()
        y = app.desktop().screenGeometry().center().y()
        self.move(x - self.geometry().width() // 2, y - self.geometry().height() // 2 - 100)

        self.status = []
        self.statuschanged = 0

        self.status.append(int(config["Settings"]["colortheme"]))
        self.status.append(int(config["Settings"]["window_start_view"]))

        self.themes = ["Classic", "Dark", "Pure Black"]
        self.choice_theme.addItems(self.themes)
        self.choice_theme.setCurrentIndex(int(config["Settings"]["colortheme"]))
        self.views = ["Full Screen", "Maximized", "Normal"]
        self.choice_views.addItems(self.views)
        self.choice_views.setCurrentIndex(int(config["Settings"]["window_start_view"]) - 1)

        self.resultbox.accepted.connect(self.buttonOkayfuncton)
        self.resultbox.rejected.connect(self.buttonCancelfuncton)
        self.shortcut = QShortcut(QtGui.QKeySequence(Qt.Key_Enter), self)
        self.shortcut.activated.connect(self.buttonOkayfuncton)

    def buttonOkayfuncton(self):
        cfgfile = open(resource_path('configuration.ini'), 'w')

        if self.choice_theme.currentIndex() != self.status[0] or self.choice_views.currentIndex() != self.status[1]:
            self.statuschanged = 1
        config.set("Settings", "colortheme", str(self.choice_theme.currentIndex()))
        config.set("Settings", "window_start_view", str(self.choice_views.currentIndex() + 1))
        config.write(cfgfile)
        cfgfile.close()

    def buttonCancelfuncton(self):
        pass


class guessnumbers_GUI(QDialog, Ui_guess):
    def __init__(self, root):
        QDialog.__init__(self, root)
        Ui_guess.__init__(self)
        self.setupUi(self)
        self.root = root
        self.listbox = self.root.listbox
        self.addlog = self.root.addlog
        self.digit = 4
        self.numberoftries = 10
        self.numberoftriesleft = self.numberoftries
        self.number = 0
        self.numberstring = ''
        self.myguess = ''
        self.As = 0
        self.Bs = 0
        self.exclude = []
        self.buttonstart.clicked.connect(self.startgame)
        self.buttonenter.clicked.connect(self.enternumber)
        self.shortcut = QShortcut(QtGui.QKeySequence(Qt.Key_Enter), self)
        self.shortcut.activated.connect(self.enternumber)

    def startgame(self):
        self.digit = int(self.entry_1.text())
        self.numberoftries = int(self.entry_2.text())
        self.numberoftriesleft = self.numberoftries
        self.randomnumber()
        self.addlog('Game begins!', 'orange')
        self.countdown.display(self.numberoftriesleft)
        self.buttonstart.setText("Restart")

    def enternumber(self):
        self.myguess = str(self.entry_3.text())
        self.As = 0
        self.Bs = 0
        self.exclude = []
        if len(self.numberstring) == 0:
            self.startgame()

        if len(self.myguess) != self.digit:
            self.addlog('Invalid input.')
            return
        for i in range(0, self.digit):
            if self.myguess[i] == self.numberstring[i]:
                self.As += 1
        if self.As == self.digit:
            self.numberoftriesleft -= 1
            self.countdown.display(self.numberoftriesleft)
            self.addlog('Bingo! The number is {}.'.format(self.numberstring), 'red')
            self.buttonstart.setText("Start")
            self.entry_3.setText("")
            self.numberstring = ''
            return
        for i in range(0, self.digit):
            for j in range(0, self.digit):
                if j not in self.exclude:
                    if self.myguess[j] == self.numberstring[i]:
                        self.Bs += 1
                        self.exclude.append(j)
                        break
        self.Bs -= self.As
        self.addlog('{}    {}A{}B'.format(self.myguess, self.As, self.Bs))
        self.numberoftriesleft -= 1
        self.countdown.display(self.numberoftriesleft)
        if self.numberoftriesleft <= 0:
            self.addlog('Game over! The number is {}'.format(self.numberstring), 'orange')
            self.numberstring = ''
            self.buttonstart.setText("Start")
        self.entry_3.setText("")

    def randomnumber(self):
        while True:
            oknumber = 1
            self.number = randint(0, math.pow(10, self.digit) - 1)
            self.numberstring = "%0{}d".format(self.digit) % self.number
            for i in range(0, self.digit):
                for j in range(0, self.digit):
                    if j != i:
                        if self.numberstring[j] == self.numberstring[i]:
                            oknumber = 0
            if oknumber == 1:
                break


class SystemTrayIcon(QSystemTrayIcon):
    """A system tray icon can be used to exit the program or show/minimized the window. """

    def __init__(self, icon, parent, window):
        QSystemTrayIcon.__init__(self, icon, parent)
        self.parent = parent
        self.window = window
        self.menu = QMenu()
        self.exitAction = self.menu.addAction("Exit")
        self.exitAction.triggered.connect(self.quitmainwindow)
        self.setContextMenu(self.menu)
        if _platform != "darwin":
            self.activated.connect(self.__icon_activated)

        self.window_showing = 1
        self.window_status = 1
        self.show()

    def quitmainwindow(self):
        self.hide()
        self.deleteLater()
        sys.exit()
        # self.parent.close()

    if _platform != "darwin":
        def __icon_activated(self, reason):
            if reason == QSystemTrayIcon.DoubleClick:
                if self.window_showing == 0:
                    if self.window_status == 1:
                        self.window.showFullScreen()
                    elif self.window_status == 2:
                        self.window.showMaximized()
                    else:
                        self.window.showNormal()
                    self.window_showing = 1
                elif self.window_showing == 1:
                    if self.window.isFullScreen():
                        self.window_status = 1
                    elif self.window.isMaximized():
                        self.window_status = 2
                    else:
                        self.window_status = 3
                    self.window.showMinimized()
                    self.window_showing = 0
                self.window.show()


class mainwindow(QMainWindow, Ui_main):
    """Main window of the Toolbox."""

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_main.__init__(self)
        self.setupUi(self)
        if colortheme == 2:
            self.setStyleSheet("background: rgba(0,0,0,100%) ")
        self.setWindowIcon(Icon)
        self.splitter.setSizes([800, 100])
        self.setStatusBar(self.statusbar)
        self.subwindowlist = []
        self.clipboard = QLabel()  # In order to transfer info between subwindows, create a null label as clipboard.
        self.clipboard.setParent(self)
        self.clipboard.hide()

        for i in range(0, 30):  # Set 30 subwindows max.
            sub = QMdiSubWindow()
            sub.setAttribute(Qt.WA_DeleteOnClose)  # Important for closing tabs properly.
            sub.setWindowIcon(QIcon())  # Remove the icon for each sub window.
            self.subwindowlist.append(sub)
        self.gui0 = welcome_GUI()
        self.subwindowlist[0].setWidget(self.gui0)
        self.subwindowlist[0].setWindowTitle("Welcome.")
        self.subwindowlist[0].aboutToActivate.connect(self.Normalstatus)
        self.mdi.addSubWindow(self.subwindowlist[0])
        self.subwindowlist[0].showMaximized()
        self.subwindowlist[0].show()

        self.numberofgui = 0

        self.initialmenuitems("help", 1)
        self.initialmenuitems("Settings", 1)

        self.status1.setText("﻿Welcome to the Toolbox. Press {}+M to see document/help.".format(Control_key))
        self.status2.setText('v{}'.format(__version__))
        self.statusbar.addWidget(self.authorLabel)

        self.statusbar.addWidget(self.progressbar)
        self.progressbar.hide()
        self.statusbar.addWidget(self.status1)
        self.statusbar.addPermanentWidget(self.status2)

        self.authorLabel.mousePressEvent = self.addguess

        self.shortcut0 = QShortcut(QtGui.QKeySequence(Qt.Key_Escape), self)
        self.shortcut0.activated.connect(self.quitfullscreen)

        self.trayIcon = None

    def closeEvent(self, event):
        """Make sure the system tray icon is destroyed correctly in Windows. """

        self.trayIcon.hide()
        self.trayIcon.deleteLater()
        event.accept()

    def initialmenuitems(self, item, available):
        if available == 1:
            try:
                getattr(self, "open{}".format(item)).triggered.connect(getattr(self, "add{}".format(item)))
            except AttributeError:
                getattr(self, "open{}".format(item)).setDisabled(True)
        else:
            getattr(self, "open{}".format(item)).setDisabled(True)

    def Load_Available_Modules(self):

        """Import all available modules into the mainwindow. This function is called in main()."""

        global __thisversion__, __version__  # allows access to global variable in this function

        keyboard_shortcut_index = 1
        first_non_module_action = self.menuAdd.actions()[0]  # We will put the new menu actions before this one
        module_index = -1
        for module_name, window_type, module_title in modules:
            try:
                module_index += 1
                lb01.setText("Loading {}".format(module_title))
                progressbar.setValue(module_index / len(modules) * 100)
                splash.update()
                app.processEvents()
                module = importlib.import_module(module_name)  # For example: import MCT_calculator_class_v3
                __thisversion__ += float(module.__version__)  # Toolbox version is the sum of its components
                # module_available.append( True )
                module_window = getattr(module, window_type)

                openAct = QAction(module_title, self)
                if keyboard_shortcut_index <= 9:
                    openAct.setShortcuts(QKeySequence("Ctrl+" + str(keyboard_shortcut_index)))
                else:
                    openAct.setShortcuts(QKeySequence("Alt+Ctrl+" + str(keyboard_shortcut_index - 9)))
                # openAct.setStatusTip( "Tool tip message" )
                openAct.triggered.connect(lambda ignore, module_version=module.__version__, module_window=module_window,
                                                 module_title=module_title: self.addModule(module_version,
                                                                                           module_window,
                                                                                           module_title))
                self.menuAdd.insertAction(first_non_module_action,
                                          openAct)  # insert openAct before first_non_module_action
            except Exception as e:
                # module_available.append( False )
                print(e)
                self.addlog("Loading module {} failed:  {}".format(module_title, str(e)))
                self.addlog('-' * 160)
                blank_action = QAction(module_title, self)
                blank_action.setDisabled(True)
                self.menuAdd.insertAction(first_non_module_action,
                                          blank_action)  # insert blank_action before first_non_module_action

            keyboard_shortcut_index += 1

        __version__ += "/" + "{:.2f}".format(__thisversion__)

    def addhelp(self):
        self.numberofgui += 1
        gui = help_GUI()
        self.subwindowlist[self.numberofgui].setWidget(gui)
        self.subwindowlist[self.numberofgui].setWindowTitle("Document")
        self.subwindowlist[self.numberofgui].aboutToActivate.connect(self.Normalstatus)
        self.mdi.addSubWindow(self.subwindowlist[self.numberofgui])
        self.subwindowlist[self.numberofgui].showMaximized()
        self.subwindowlist[self.numberofgui].show()

    def addSettings(self):

        """Customized Settings. """

        window_settings = settings_GUI(self)
        window_settings.show()

        yesorno = window_settings.exec_()  # Crucial to capture the result. 1 for Yes and 0 for No.
        if yesorno:
            pass

    def addguess(self, event):
        window = guessnumbers_GUI(self)
        window.show()
        window.exec_()

    def addModule(self, module_version, window_type, module_title):
        self.numberofgui += 1
        gui = window_type(self.subwindowlist[self.numberofgui], self)
        self.setupsubwindow(gui, module_title, module_version)

    def setupsubwindow(self, gui, name, version):
        self.subwindowlist[self.numberofgui].setWidget(gui)
        self.subwindowlist[self.numberofgui].setWindowTitle("{} v{}".format(name, version))

        if name == "FTIR Fitting Tool":
            self.subwindowlist[self.numberofgui].aboutToActivate.connect(self.FTIRstatus)
        else:
            self.subwindowlist[self.numberofgui].aboutToActivate.connect(self.Normalstatus)

        self.mdi.addSubWindow(self.subwindowlist[self.numberofgui])
        self.subwindowlist[self.numberofgui].showMaximized()
        self.subwindowlist[self.numberofgui].show()

        self.addinitiallog(name)

    def Normalstatus(self):
        self.status1.setText("﻿Welcome to the Toolbox. Press {}+M to see document/help.".format(Control_key))

    def FTIRstatus(self):
        self.status1.setText("Welcome to FTIR Fitting Tool. Press {}+P for help.".format(Control_key))

    def addinitiallog(self, name):
        self.addlog('-' * 160, "blue")
        self.addlog('Welcome to {}.'.format(name), "blue")
        self.addlog("This is the log file.", "blue")
        self.addlog('-' * 160, "blue")

    def quitfullscreen(self):
        if self.isFullScreen():
            self.showNormal()

    def addlog_with_button(self, string, buttontext, fg="default", bg="default"):

        """Add a line to the log file with some description and a button.
        This function will return the button so it can be click.connect to functions."""

        item = QListWidgetItem()
        # Create widget
        widget = QWidget()
        widgetText = QLabel("<font size=3>" + string + "</font>")
        if fg is not "default":
            widgetText.setForeground(QColor(fg))
        if bg is not "default":
            widgetText.setBackground(QColor(bg))
        widgetText.setFixedHeight(17)
        widgetText.setWindowFlags(Qt.FramelessWindowHint)
        widgetText.setAttribute(Qt.WA_TranslucentBackground)
        widgetButton = QPushButton(buttontext)
        widgetButton.setFixedHeight(17)
        widgetButton.setStyleSheet("padding: 1px;")
        widgetLayout = QHBoxLayout()
        widgetLayout.setContentsMargins(5, 0, 5, 0)
        widgetLayout.addWidget(widgetText)
        widgetLayout.addWidget(widgetButton)
        widgetLayout.addStretch()

        widgetLayout.setSizeConstraint(QLayout.SetFixedSize)
        widget.setLayout(widgetLayout)
        widget.setFixedHeight(17)
        widget.setWindowFlags(Qt.FramelessWindowHint)
        widget.setAttribute(Qt.WA_TranslucentBackground)
        item.setSizeHint(widget.sizeHint())

        # Add widget to QListWidget
        self.listbox.addItem(item)
        self.listbox.setItemWidget(item, widget)
        self.listbox.scrollToItem(item)
        self.listbox.show()

        return widgetButton

    def addlog(self, string, fg="default", bg="default"):

        """Add a simple text log to the log frame."""

        item = QListWidgetItem(string)
        if fg is not "default":
            item.setForeground(QColor(fg))
        if bg is not "default":
            item.setBackground(QColor(bg))
        self.listbox.addItem(item)
        self.listbox.scrollToItem(item)
        self.listbox.show()

        return item


def main():
    global Icon, Control_key, app, splash, lb01, progressbar
    app = QApplication(sys.argv)

    if _platform == "darwin":
        Icon = QIcon(resource_path('Images/icon.icns'))
        Control_key = "⌘"
    else:
        Icon = QIcon(resource_path('Images/icon.ico'))
        Control_key = "Ctrl"

    splash_pix = QPixmap(resource_path('Images/bg.png'))
    MPL_logo = QPixmap(resource_path('Images/MPL_UIC.png'))
    MPL_logo = MPL_logo.scaled(150, 46, transformMode=Qt.SmoothTransformation)
    logo = QPixmap(resource_path('Images/toolbox_w.png'))
    logo = logo.scaled(180, 60, transformMode=Qt.SmoothTransformation)

    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())

    vbox = QVBoxLayout()
    vbox.setContentsMargins(15, 130, 15, 0)
    font = QFont("Helvetica", 15)
    lb00 = QLabel()
    lb00.setAlignment(Qt.AlignCenter)
    lb00.setPixmap(logo)
    lb000 = QLabel("v{}".format(__version__[0:3]))
    lb000.setAlignment(Qt.AlignCenter)
    lb000.setFont(font)
    lb000.setStyleSheet('color: white')
    lb01 = QLabel("")
    lb01.setAlignment(Qt.AlignCenter)
    lb01.setStyleSheet('color: white')
    lb02 = QLabel()
    lb02.setAlignment(Qt.AlignCenter)
    lb02.setPixmap(MPL_logo)
    progressbar = QProgressBar()
    progressbar.setTextVisible(False)   # To remove weird text shown next to progressbar in Windows.
    vbox.addWidget(lb00)
    vbox.addWidget(lb000)
    vbox.addStretch()
    vbox.addWidget(lb02)
    vbox.addStretch()
    vbox.addWidget(lb01)
    vbox.addWidget(progressbar)
    splash.setLayout(vbox)

    splash.show()
    app.processEvents()

    window = mainwindow()
    window.Load_Available_Modules()     # This step takes long time. Until it is finished, the splash screen will be on.

    window.setWindowTitle("Toolbox v{}".format(__version__))
    window.status2.setText('v{}'.format(__version__))
    trayIcon = SystemTrayIcon(Icon, app, window)    # System Tray
    window.trayIcon = trayIcon

    if window_start_view == 1:
        window.showFullScreen()
    elif window_start_view == 2:
        window.showMaximized()
    else:
        window.showNormal()
    if colortheme + darkthemeavailable == 2 or colortheme + darkthemeavailable == 3:
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    splash.finish(window)
    window.show()

    # Override excepthook to prevent program crashing and create feekback log.
    def excepthook(excType, excValue, tracebackobj):
        """
        Global function to catch unhandled exceptions in main thread ONLY.

        @param excType exception type
        @param excValue exception value
        @param tracebackobj traceback object
        """
        separator = '-' * 80
        logFile = time.strftime("%m_%d_%Y_%H_%M_%S") + ".log"
        notice = \
            """An unhandled exception occurred. \n""" \
            """Please report the problem via email to <%s>.\n""" \
            """A log has been written to "%s".\n\nError information:\n""" % \
            (__emailaddress__, logFile)
        timeString = time.strftime("%m/%d/%Y, %H:%M:%S")

        tbinfofile = io.StringIO()
        traceback.print_tb(tracebackobj, None, tbinfofile)
        tbinfofile.seek(0)
        tbinfo = tbinfofile.read()
        errmsg = '%s: \n%s' % (str(excType), str(excValue))
        sections = [separator, timeString, separator, errmsg, separator, tbinfo]
        msg = '\n'.join(sections)
        try:
            f = open(logFile, "w")
            f.write(msg)
            f.write("Version: {}".format(__version__))
            f.close()
        except IOError:
            pass
        errorbox = QMessageBox()
        errorbox.setText(str(notice) + str(msg) + "Version: " + __version__)
        errorbox.exec_()

    sys.excepthook = excepthook

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
