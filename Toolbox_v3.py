import os
import sys
import math
from random import randint
from sys import platform as _platform
from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import *

modulelist = ["module_name_short", "MCT", "growthtemp", "database", "ln2", "XRD", "ftir", "kp", 'grade']
moduleavailable = ["1_is_avalable", 1, 1, 1, 1, 1, 1, 1, 1]
thisversion = 0

# All modules below can be successfully imported only if you have them in your file directory
# AND ALL STANDARD PACKAGES REQUIED FOR EACH MODULE ARE PRE_INSTALLED!
# If you are not sure what package need to be installed before running, remove the "try...except..." method for
# the specific module below, and the error message telling you what you are missing should pop up.
try:
    import MCT_calculator_class_v3
    from MCT_calculator_class_v3 import *
    thisversion += float(MCT_calculator_class_v3.__version__)
except ModuleNotFoundError:
    moduleavailable[1] = 0
try:
    import growthtempcalculator_class_v3
    from growthtempcalculator_class_v3 import *

    thisversion += float(growthtempcalculator_class_v3.__version__)
except ModuleNotFoundError:
    moduleavailable[2] = 0
try:
    import MBEdatabase_class_v3
    from MBEdatabase_class_v3 import *

    thisversion += float(MBEdatabase_class_v3.__version__)
except ModuleNotFoundError:
    moduleavailable[3] = 0
try:
    import LN2order_class_v3
    from LN2order_class_v3 import *

    thisversion += float(LN2order_class_v3.__version__)
except ModuleNotFoundError:
    moduleavailable[4] = 0
try:
    import XRD_analyzer_class_v3
    from XRD_analyzer_class_v3 import *

    thisversion += float(XRD_analyzer_class_v3.__version__)
except ModuleNotFoundError:
    moduleavailable[5] = 0
try:
    import FTIR_fittingtool_v3
    from FTIR_fittingtool_v3 import *

    thisversion += float(FTIR_fittingtool_v3.__version__)
except ModuleNotFoundError:
    moduleavailable[6] = 0
try:
    import Kp_method_v3
    from Kp_method_v3 import *

    thisversion += float(Kp_method_v3.__version__)
except ModuleNotFoundError:
    moduleavailable[7] = 0
try:
    import Grade_Analyzer_GUI_v3
    from Grade_Analyzer_GUI_v3 import *

    thisversion += float(Grade_Analyzer_GUI_v3.__version__)
except ModuleNotFoundError:
    moduleavailable[8] = 0

__version__ = 3.0 + thisversion / 10
__emailaddress__ = "pman3@uic.edu"

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))  # Change the working directory to current directory.
qtmainfile = "mainwindow.ui"  # GUI layout file.
Ui_main, QtBaseClass = uic.loadUiType(qtmainfile)
qtwelcomefile = "welcome.ui"
Ui_welcome, QtBaseClass = uic.loadUiType(qtwelcomefile)
qthelpfile = "help.ui"
Ui_help, QtBaseClass = uic.loadUiType(qthelpfile)
qtguessfile = "guessnumbers.ui"
Ui_guess, QtBaseClass = uic.loadUiType(qtguessfile)

class welcome_GUI(QWidget, Ui_welcome):

    """Main FTIR fitting tool window."""

    def __init__(self):
        QWidget.__init__(self)
        Ui_welcome.__init__(self)
        self.setupUi(self)


class help_GUI(QWidget, Ui_help):

    """Main FTIR fitting tool window."""

    def __init__(self):
        QWidget.__init__(self)
        Ui_help.__init__(self)
        self.setupUi(self)


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
        self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Enter), self)
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
            self.number = randint(0, math.pow(10, self.digit)-1)
            self.numberstring = "%0{}d".format(self.digit) % self.number
            for i in range(0, self.digit):
                for j in range(0, self.digit):
                    if j != i:
                        if self.numberstring[j] == self.numberstring[i]:
                            oknumber = 0
            if oknumber == 1:
                break


class mainwindow(QMainWindow, Ui_main):

    """Optinal settings for customized result."""

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_main.__init__(self)
        self.setupUi(self)
        self.setStatusBar(self.statusbar)
        self.sub0 = QMdiSubWindow()
        self.sub1 = QMdiSubWindow()
        self.sub2 = QMdiSubWindow()
        self.sub3 = QMdiSubWindow()
        self.sub4 = QMdiSubWindow()
        self.sub5 = QMdiSubWindow()
        self.sub6 = QMdiSubWindow()
        self.sub7 = QMdiSubWindow()
        self.sub8 = QMdiSubWindow()
        self.sub9 = QMdiSubWindow()
        self.sub10 = QMdiSubWindow()
        self.sub11 = QMdiSubWindow()
        self.sub12 = QMdiSubWindow()
        self.sub13 = QMdiSubWindow()
        self.sub14 = QMdiSubWindow()
        self.sub15 = QMdiSubWindow()
        self.sub16 = QMdiSubWindow()
        self.sub17 = QMdiSubWindow()
        self.sub18 = QMdiSubWindow()
        self.sub19 = QMdiSubWindow()

        self.gui0 = welcome_GUI()
        self.sub0.setWidget(self.gui0)
        self.sub0.setWindowTitle("Welcome.")
        self.mdi.addSubWindow(self.sub0)
        self.sub0.showMaximized()
        self.sub0.show()

        self.numberofgui = 0

        self.initialmenuitems("help", 1)
        for i in range(1, len(modulelist)):
            self.initialmenuitems(modulelist[i], moduleavailable[i])

        if _platform == "darwin":
            self.status1.setText("﻿Welcome to the Toolbox. Press ⌘+M to see document/help.")
        self.status2.setText('v{}'.format(__version__))
        self.statusbar.addWidget(self.authorLabel)

        self.statusbar.addWidget(self.progressbar)
        self.progressbar.hide()
        self.statusbar.addWidget(self.status1)
        self.statusbar.addPermanentWidget(self.status2)

        self.authorLabel.mousePressEvent = self.addguess

    def initialmenuitems(self, item, available):
        if available == 1:
            try:
                getattr(self, "open{}".format(item)).triggered.connect(getattr(self, "add{}".format(item)))
            except AttributeError:
                getattr(self, "open{}".format(item)).setDisabled(True)
        else:
            getattr(self, "open{}".format(item)).setDisabled(True)

    def addhelp(self):
        self.numberofgui += 1
        gui = help_GUI()
        getattr(self, "sub{}".format(self.numberofgui)).setWidget(gui)
        getattr(self, "sub{}".format(self.numberofgui)).setWindowTitle("Document")
        self.mdi.addSubWindow(getattr(self, "sub{}".format(self.numberofgui)))
        getattr(self, "sub{}".format(self.numberofgui)).showMaximized()
        getattr(self, "sub{}".format(self.numberofgui)).show()

    def addguess(self, event):
        window = guessnumbers_GUI(self)
        window.show()
        window.exec_()

    def addftir(self):
        self.numberofgui += 1
        gui = FTIR_fittingtool_GUI_v3(getattr(self, "sub{}".format(self.numberofgui)), self)
        self.setupsubwindow(gui, "FTIR Fitting Tool", FTIR_fittingtool_v3.__version__)

        if _platform == "darwin":
            self.status1.setText("Welcome to FTIR Fitting Tool. Press ⌘+P for help.")
        else:
            self.status1.setText("Welcome to FTIR Fitting Tool. Press Ctrl+P for help.")

    def addkp(self):
        self.numberofgui += 1
        gui = Kp_method_GUI_v3(getattr(self, "sub{}".format(self.numberofgui)), self)
        self.setupsubwindow(gui, "Kp method", Kp_method_v3.__version__)

    def setupsubwindow(self, gui, name, version):
        getattr(self, "sub{}".format(self.numberofgui)).setWidget(gui)
        getattr(self, "sub{}".format(self.numberofgui)).setWindowTitle("{} v{}".format(name, version))
        self.mdi.addSubWindow(getattr(self, "sub{}".format(self.numberofgui)))
        getattr(self, "sub{}".format(self.numberofgui)).showMaximized()
        getattr(self, "sub{}".format(self.numberofgui)).show()

        self.addinitiallog(name)

    def addinitiallog(self, name):
        self.addlog('-' * 160, "blue")
        self.addlog('Welcome to {}'.format(name), "blue")
        self.addlog("This is the log file.", "blue")
        self.addlog('-' * 160, "blue")

    def addlog(self, string, fg="default", bg="default"):
            item = QListWidgetItem(string)
            if fg is not "default":
                item.setForeground(QColor(fg))
            if bg is not "default":
                item.setBackground(QColor(bg))
            self.listbox.addItem(item)
            self.listbox.scrollToItem(item)
            self.listbox.show()


def main():
    app = QApplication(sys.argv)
    window = mainwindow()
    window.setWindowTitle("Toolbox v{}".format(__version__))

    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()