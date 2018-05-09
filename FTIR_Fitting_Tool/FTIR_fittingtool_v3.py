import os
import sys
import time
import csv
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import traceback
import sys
from sys import platform as _platform

disableSQL = 0
try:
    import MySQLdb
    from .ftir_sql_browser import Get_Data
except Exception as e:
    disableSQL = 1
    print(e)
    print("Need to install mysql plugin, run: pip install mysqlclient.")

import configparser
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


__version__ = '3.02'
__emailaddress__ = "pman3@uic.edu"


def resource_path(relative_path):  # Define function to import external files when using PyInstaller.
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


qtFTIRfile = resource_path(os.path.join("FTIR_Fitting_Tool", "ftir_fittingtoolv3_ui.ui"))
Ui_FTIR, QtBaseClass = uic.loadUiType(qtFTIRfile)
qtloadstrufile = resource_path(os.path.join("FTIR_Fitting_Tool", "FTIR_loadstru.ui"))
Ui_loadstru, QtBaseClass = uic.loadUiType(qtloadstrufile)
qtsettingsfile = resource_path(os.path.join("FTIR_Fitting_Tool", "FTIR_settings.ui"))
Ui_settings_FTIR, QtBaseClass = uic.loadUiType(qtsettingsfile)
qthelpfile = resource_path(os.path.join("FTIR_Fitting_Tool", "FTIR_help.ui"))
Ui_help_FTIR, QtBaseClass = uic.loadUiType(qthelpfile)
qtMCTafile = resource_path(os.path.join("FTIR_Fitting_Tool", "FTIR_MCTa.ui"))
Ui_MCTa, QtBaseClass = uic.loadUiType(qtMCTafile)


class FIT_FTIR:
    def __init__(self, root, temp, wavenumbers, transmissions, subd, layertype_list, entry_x_list, entry_d_list,
                 checklayer_list, scalefactor, angle, CdTe_offset, HgTe_offset, subtype, fittype, blindcal,
                 progress_callback=None, wn_callback=None):
        self.root = root
        self.temp = temp
        self.wns = wavenumbers
        self.trans = transmissions
        self.subd = subd
        self.layertype_list, self.entry_x_list, self.entry_d_list, self.checklayer_list \
            = layertype_list, entry_x_list, entry_d_list, checklayer_list
        self.scalefactor = scalefactor
        self.angle = angle
        self.CdTe_offset = CdTe_offset
        self.HgTe_offset = HgTe_offset
        self.subtype = subtype
        self.fittingtype = fittype
        self.listbox = self.root.listbox
        self.progressbar = self.root.progressbar
        self.FTIRplot = self.root.FTIRplot
        self.absorptionplot = self.root.absorptionplot
        self.canvas = self.root.mplplot
        self.blindcal = blindcal
        self.status2 = self.root.status2
        self.progress_callback = progress_callback
        self.wn_callback = wn_callback
        self.warningcolor1 = self.root.warningcolor1
        self.warningcolor2 = self.root.warningcolor2
        self.warningcolor3 = self.root.warningcolor3

        self.n_list = []
        self.k_list = []
        self.etas_list = []
        self.etap_list = []
        self.deltas_list = []
        self.deltap_list = []
        self.matrixs_list = []
        self.matrixp_list = []

        self.transs = []
        self.peakvalues = []

        self.alphaMCT = 0
        self.alphaCT = 0

        self.basek = 0
        self.ab = 0
        self.reflections = []
        self.absorptions = []

        self.load_n_file()

        self.adjust_d_on_temp()

        self.cal_crossover_a()

        if self.fittingtype in [1, 2, 8]:
            self.show_fringes()
        else:
            pass

    def load_n_file(self):

        """Load all material refractive index data."""

        reference_info = [("ZnSe_n.csv", "wl_n_ZnSe", "n_ZnSe"),
                          ("ZnSe_k.csv", "wl_k_ZnSe", "k_ZnSe"),
                          ("BaF2_n.csv", "wl_n_BaF2", "n_BaF2"),
                          ("BaF2_k.csv", "wl_k_BaF2", "k_BaF2"),
                          ("Ge_n_293K.csv", "wl_n_Ge", "n_Ge"),
                          ("Ge_k.csv", "wl_k_Ge", "k_Ge"),
                          ("ZnS_n.csv", "wl_n_ZnS", "n_ZnS"),
                          ("ZnS_k.csv", "wl_k_ZnS", "k_ZnS"),
                          ("Si3N4_n.csv", "wl_n_Si3N4", "n_Si3N4"),
                          ("Si3N4_k.csv", "wl_k_Si3N4", "k_Si3N4"),
                          ("ZnSe_k_ideal.csv", "wl_k_i_ZnSe", "k_i_ZnSe"),
                          ("BaF2_k_ideal.csv", "wl_k_i_BaF2", "k_i_BaF2"),
                          ("ZnS_k_ideal.csv", "wl_k_i_ZnS", "k_i_ZnS"),
                          ("SiO_n.csv", "wl_n_SiO", "n_SiO"),
                          ("PbTe_n.csv", "wl_n_PbTe", "n_PbTe"),
                          ("Al_n.csv", "wl_n_Al", "n_Al"),
                          ("Si_k.csv", "wl_k_Si", "k_Si")]

        for (file_name, x_data, y_data) in reference_info:
            setattr(self, x_data, [])
            setattr(self, y_data, [])
            try:
                with open(resource_path(os.path.join("Refractive_Index", file_name)), 'r') as f:
                    reader = csv.reader(f, delimiter=',')
                    for row in reader:
                        try:
                            getattr(self, x_data).append(float(row[0]))
                            getattr(self, y_data).append(float(row[1]))
                        except ValueError:
                            pass
            except Exception as e:
                self.addlog("Critical error! {} contains invalid character.".format(file_name), self.warningcolor1)

    def adjust_d_on_temp(self):

        """Layer Thicknesses change with temperature. This function modify thickness based on T. """

        for i in range(0, len(self.layertype_list)):
            if self.layertype_list[i] == "ZnSe":
                self.entry_d_list[i] = self.entry_d_list[i] * (1 + 7.6E-6 * (self.temp - 300))
            elif self.layertype_list[i] == "BaF2":
                self.entry_d_list[i] = self.entry_d_list[i] * (1 + 18.1E-6 * (self.temp - 300))
            elif self.layertype_list[i] == "Ge":
                self.entry_d_list[i] = self.entry_d_list[i] * (1 + 5.9E-6 * (self.temp - 300))
            elif self.layertype_list[i] == "ZnS":
                self.entry_d_list[i] = self.entry_d_list[i] * (1 + 6.5E-6 * (self.temp - 300))
            elif self.layertype_list[i] == "Si3N4":
                self.entry_d_list[i] = self.entry_d_list[i] * (1 + 2.52E-6 * (self.temp - 300))

    def cal_crossover_a(self):

        """Used to find the crossover point of absorption curve (Crossover of intrinsic and Urbach tail).
        Since self.T0 and self.beta are adjusted based on real data, so it's tricky to find the crossover point. """

        self.crossover_xs = []
        self.crossover_as = []

        for x in np.arange(0, 1, 0.001):
            self.T0 = 61.9  # Initial parameter is 81.9. Adjusted.
            self.W = self.T0 + self.temp
            self.E0 = -0.3424 + 1.838 * x + 0.148 * x * x * x * x
            self.sigma = 3.267E4 * (1 + x)
            self.alpha0 = np.exp(53.61 * x - 18.88)
            self.beta = 3.109E5 * np.sqrt((1 + x) / self.W)  # Initial parameter is 2.109E5. Adjusted.
            self.Eg = self.E0 + (6.29E-2 + 7.68E-4 * self.temp) * ((1 - 2.14 * x) / (1 + x))

            fitsuccess = 0

            for E in np.arange(0.05, 0.8, 0.001):
                ab1 = self.alpha0 * np.exp(self.sigma * (E - self.E0) / self.W)
                if E >= self.Eg:
                    ab2 = self.beta * np.sqrt(E - self.Eg)
                else:
                    ab2 = 0

                if (ab1 - ab2) <= 10 and ab1 > 500:
                    self.crossover_xs.append(x)
                    self.crossover_as.append(ab1)
                    fitsuccess = 1
                    break

            if fitsuccess == 0:
                if x < 0.5:
                    self.crossover_xs.append(x)
                    self.crossover_as.append(1200)
                else:
                    self.crossover_xs.append(x)
                    self.crossover_as.append(500)

        # print(self.crossover_xs)
        # print(self.crossover_as)

    def cal_initialpara(self, x):

        """Initilize all parameters based on composition x."""

        # for n
        self.A1 = 13.173 - 9.852 * x + 2.909 * x * x + 0.0001 * (300 - self.temp)
        self.B1 = 0.83 - 0.246 * x - 0.0961 * x * x + 8 * 0.00001 * (300 - self.temp)
        self.C1 = 6.706 - 14.437 * x + 8.531 * x * x + 7 * 0.00001 * (300 - self.temp)
        self.D1 = 1.953 * 0.00001 - 0.00128 * x + 1.853 * 0.00001 * x * x

        # for k
        self.T0 = 61.9  # Initial parameter is 81.9. Adjusted.
        self.W = self.T0 + self.temp
        self.E0 = -0.3424 + 1.838 * x + 0.148 * x * x * x * x
        self.sigma = 3.267E4 * (1 + x)
        self.alpha0 = np.exp(53.61 * x - 18.88)
        self.beta = 3.109E5 * np.sqrt((1 + x) / self.W)  # Initial parameter is 2.109E5. Adjusted.
        self.Eg = self.E0 + (6.29E-2 + 7.68E-4 * self.temp) * ((1 - 2.14 * x) / (1 + x))

        for i in range(0, len(self.crossover_xs) - 1):
            if self.crossover_xs[i + 1] > x >= self.crossover_xs[i]:
                self.crossover_a = self.crossover_as[i]
                break

    def cal_n(self, lamda, material):

        """Calculate n based on the type of material at a certain lamda."""

        if material == "CdTe" or material == "MCT" or material == "SL":
            if lamda < 1.4 * self.C1:
                lamda = 1.4 * self.C1

            n = np.sqrt(self.A1 + self.B1 / (1 - (self.C1 / lamda) * (self.C1 / lamda)) + self.D1 * lamda * lamda)
            return n

        elif material == "Si":
            n = np.sqrt(11.67316 + 1 / lamda / lamda + 0.004482633 / (lamda * lamda - 1.108205 * 1.108205))
            return n

        elif material == "Air":
            n = 1
            return n

        else:
            n = getattr(self, "n_{}".format(material))[getattr(self, "wl_n_{}".format(material)).index(
                min(getattr(self, "wl_n_{}".format(material)), key=lambda x: abs(x - lamda)))]

            if material == "ZnSe":
                if self.temp >= 275:
                    n = n * (1 + 6.26E-5 * (self.temp - 300))
                else:
                    n = n * (1 + 6.26E-5 * (275 - 300))
                    if self.temp >= 225:
                        n = n * (1 + 5.99E-5 * (self.temp - 275))
                    else:
                        n = n * (1 + 5.99E-5 * (225 - 275))
                        if self.temp >= 160:
                            n = n * (1 + 5.72E-5 * (self.temp - 225))
                        else:
                            n = n * (1 + 5.72E-5 * (160 - 225))
                            if self.temp >= 100:
                                n = n * (1 + 5.29E-5 * (self.temp - 160))
                            else:
                                n = n * (1 + 5.29E-5 * (100 - 160))
                                n = n * (1 + 4.68E-5 * (self.temp - 160))

            elif material == "BaF2":
                if self.temp >= 275:
                    n = n * (1 - 1.64E-5 * (self.temp - 300))
                else:
                    n = n * (1 - 1.64E-5 * (275 - 300))
                    if self.temp >= 225:
                        n = n * (1 - 1.5E-5 * (self.temp - 275))
                    else:
                        n = n * (1 - 1.5E-5 * (225 - 275))
                        if self.temp >= 160:
                            n = n * (1 - 1.37E-5 * (self.temp - 225))
                        else:
                            n = n * (1 - 1.37E-5 * (160 - 225))
                            if self.temp >= 100:
                                n = n * (1 - 9.95E-6 * (self.temp - 160))
                            else:
                                n = n * (1 - 9.95E-6 * (100 - 160))
                                n = n * (1 - 8.91E-6 * (self.temp - 160))

            elif material == "Ge":
                if self.temp >= 275:
                    n = n * (1 + 4.25E-5 * (self.temp - 300))
                else:
                    n = n * (1 + 4.25E-5 * (275 - 300))
                    if self.temp >= 225:
                        n = n * (1 + 3.87E-5 * (self.temp - 275))
                    else:
                        n = n * (1 + 3.87E-5 * (225 - 275))
                        if self.temp >= 160:
                            n = n * (1 + 3.45E-5 * (self.temp - 225))
                        else:
                            n = n * (1 + 3.45E-5 * (160 - 225))
                            if self.temp >= 100:
                                n = n * (1 + 3.30E-5 * (self.temp - 160))
                            else:
                                n = n * (1 + 3.30E-5 * (100 - 160))
                                n = n * (1 + 2.21E-5 * (self.temp - 160))

            elif material == "ZnS":
                n = n * (1 + 5.43E-5 * (self.temp - 300))

            elif material == "Si3N4":
                n = n * (1 + 2.5E-5 * (self.temp - 300))
        return n

    def cal_k(self, lamda, material):

        """Calculate k based on the type of material at a certain lamda."""

        k = 0
        if material == "CdTe":
            return 0
        elif material == "MCT" or material == "SL":
            E = 4.13566743 * 3 / 10 / lamda
            ab1 = self.alpha0 * np.exp(self.sigma * (E - self.E0) / self.W)
            if E >= self.Eg:
                ab2 = self.beta * np.sqrt(E - self.Eg)
            else:
                ab2 = 0

            if ab1 < self.crossover_a and ab2 < self.crossover_a:
                return ab1 / 4 / np.pi * lamda / 10000
            else:
                if ab2 != 0:
                    return ab2 / 4 / np.pi * lamda / 10000
                else:
                    return ab1 / 4 / np.pi * lamda / 10000

        elif material in ["ZnSe", "BaF2", "Ge", "ZnS", "Si3N4"]:
            if self.fittingtype in [8, 9, 10]:  # Use ideal k files.
                if material == "Ge":
                    return 0
                elif material == "Si3N4":
                    return getattr(self, "k_{}".format(material))[getattr(self, "wl_k_{}".format(material)).index(
                        min(getattr(self, "wl_k_{}".format(material)), key=lambda x: abs(x - lamda)))]
                else:
                    return getattr(self, "k_i_{}".format(material))[getattr(self, "wl_k_i_{}".format(material)).index(
                        min(getattr(self, "wl_k_i_{}".format(material)), key=lambda x: abs(x - lamda)))]
            else:
                return getattr(self, "k_{}".format(material))[getattr(self, "wl_k_{}".format(material)).index(
                    min(getattr(self, "wl_k_{}".format(material)), key=lambda x: abs(x - lamda)))]

        elif material == "Si":
            if self.fittingtype in [8, 9, 10]:  # Use ideal k files.
                return 0
            else:
                return getattr(self, "k_{}".format(material))[getattr(self, "wl_k_{}".format(material)).index(
                    min(getattr(self, "wl_k_{}".format(material)), key=lambda x: abs(x - lamda)))]

        elif material == "Air":
            return 0

        else:
            return 0

    def show_fringes(self):

        """Calculate fringes knowing the range of wavenumbers. """

        self.peakvalues = []
        self.reflections = []
        self.absorptions = []
        numbercount = 0
        for wn in self.wns:
            self.lamda = 10000 / float(wn)
            self.E = 4.13566743 * 3 / 10 / self.lamda
            self.peakvalues.append(self.cal_fringes_single(self.lamda)[0])
            self.reflections.append(self.cal_fringes_single(self.lamda)[1])
            self.absorptions.append(self.cal_fringes_single(self.lamda)[2])

            if self.fittingtype != 1:
                numbercount += 1
                if numbercount == 5 or numbercount == 10 or numbercount == 15 or numbercount == 20:
                    percentage = (wn - self.wns[0]) / (self.wns[len(self.wns) - 1] - self.wns[0]) * 100
                    self.progress_callback.emit(percentage)
                    self.wn_callback.emit(wn)
                    if self.root.abortmission == 1:
                        try:
                            self.fitline.pop(0).remove()
                        except (AttributeError, IndexError) as error:
                            pass
                        return
                    if numbercount == 20:
                        if self.blindcal == 0:
                            try:
                                self.fitline.pop(0).remove()
                            except (AttributeError, IndexError) as error:
                                pass
                            self.fitline = self.FTIRplot.plot(self.wns[0:len(self.peakvalues)], self.peakvalues, 'r')
                            self.canvas.draw()

                        numbercount = 0
        if self.fittingtype != 1 and self.blindcal == 0:
            try:
                self.fitline.pop(0).remove()
            except (AttributeError, IndexError) as error:
                pass

    def cal_fringes_single(self, lamda):

        """Calculate the transmission/reflection/absorption at a certain lamda. """

        self.n_list = []
        self.k_list = []
        self.etas_list = []
        self.etap_list = []
        self.deltas_list = []
        self.deltap_list = []
        self.matrixs_list = []
        self.matrixp_list = []

        self.allresult = []

        self.eta0s = np.cos(self.angle)
        self.eta0p = 1 / np.cos(self.angle)

        for i in range(0, len(self.layertype_list)):
            if self.layertype_list[i] == "CdTe":
                self.cal_initialpara(1)
            elif self.layertype_list[i] == "MCT" or self.layertype_list[i] == "SL":
                self.cal_initialpara(self.entry_x_list[i])
            n = self.cal_n(lamda, self.layertype_list[i])
            k = self.cal_k(lamda, self.layertype_list[i])
            self.n_list.append(n)
            self.k_list.append(k)
            etas = np.sqrt((n - 1j * k) * (n - 1j * k) - np.sin(self.angle) * np.sin(self.angle))
            etap = (n - 1j * k) * (n - 1j * k) / etas
            deltas = 2 * np.pi / lamda * self.entry_d_list[i] * etas
            deltap = 2 * np.pi / lamda * self.entry_d_list[i] * etas
            self.etas_list.append(etas)
            self.etap_list.append(etap)
            self.deltas_list.append(deltas)
            self.deltap_list.append(deltap)

        if self.subtype == 1:
            self.nsub = np.sqrt(11.67316 + 1 / lamda / lamda + 0.004482633 / (lamda * lamda - 1.108205 * 1.108205))
        elif self.subtype == 2:
            self.nsub = np.sqrt(5.68 + 1.53 * lamda * lamda / (lamda * lamda - 0.366))
        elif self.subtype == 3:
            self.nsub = 1
        self.etasubs = np.sqrt(self.nsub * self.nsub - np.sin(self.angle) * np.sin(self.angle))
        self.etasubp = self.nsub * self.nsub / self.etasubs

        for i in range(0, len(self.layertype_list)):
            matrixs = np.matrix([[np.cos(self.deltas_list[len(self.layertype_list) - i - 1]),
                                  1j * np.sin(self.deltas_list[len(self.layertype_list) - i - 1]) / self.etas_list[
                                      len(self.layertype_list) - i - 1]],
                                 [1j * self.etas_list[len(self.layertype_list) - i - 1] * np.sin(
                                     self.deltas_list[len(self.layertype_list) - i - 1]),
                                  np.cos(self.deltas_list[len(self.layertype_list) - i - 1])]])
            matrixp = np.matrix([[np.cos(self.deltap_list[len(self.layertype_list) - i - 1]),
                                  1j * np.sin(self.deltap_list[len(self.layertype_list) - i - 1]) / self.etap_list[
                                      len(self.layertype_list) - i - 1]],
                                 [1j * self.etap_list[len(self.layertype_list) - i - 1] * np.sin(
                                     self.deltap_list[len(self.layertype_list) - i - 1]),
                                  np.cos(self.deltap_list[len(self.layertype_list) - i - 1])]])

            self.matrixs_list.append(matrixs)
            self.matrixp_list.append(matrixp)

        submatrixs = np.array([[1], [self.etasubs]])
        submatrixs.reshape(2, 1)
        submatrixp = np.array([[1], [self.etasubp]])
        submatrixp.reshape(2, 1)

        products = self.matrixs_list[0]

        for i in range(1, len(self.matrixs_list)):
            products = np.dot(products, self.matrixs_list[i])

        products = np.dot(products, submatrixs)
        Bs = products.item(0)
        Cs = products.item(1)

        productp = self.matrixp_list[0]

        for i in range(1, len(self.matrixp_list)):
            productp = np.dot(productp, self.matrixp_list[i])

        productp = np.dot(productp, submatrixp)

        Bp = productp.item(0)
        Cp = productp.item(1)

        Zs = self.eta0s * Bs + Cs
        Zp = self.eta0p * Bp + Cp
        Z2s = self.eta0s * Bs - Cs
        Z2p = self.eta0p * Bp - Cp

        Ztops = Bs * (Cs.conjugate()) - self.etasubs
        Ztopp = Bp * (Cp.conjugate()) - self.etasubp

        Ts = 4 * self.eta0s * self.etasubs / Zs / Zs.conjugate()
        Tp = 4 * self.eta0p * self.etasubp / Zp / Zp.conjugate()

        Rs = Z2s / Zs * ((Z2s / Zs).conjugate())
        Rp = Z2p / Zp * ((Z2p / Zp).conjugate())

        As = 4 * self.eta0s * Ztops.real / Zs / Zs.conjugate()
        Ap = 4 * self.eta0p * Ztopp.real / Zp / Zp.conjugate()

        transmission = (Ts + Tp) / 2 * 100 * self.scalefactor
        reflection = (Rs + Rp) / 2 * 100 * 1 + (Ts + Tp) / 2 * 100 * (1 - self.scalefactor)
        absorption = (As + Ap) / 2 * 100 * 1

        self.allresult.append(float(np.real(transmission)))
        self.allresult.append(float(np.real(reflection)))
        self.allresult.append(float(np.real(absorption)))

        return self.allresult

    def cal_absorption(self):

        """Calculate the absorption coefficient curve."""

        basek = 0
        numbercount = 0
        numbercount2 = 0
        self.eta0s = np.cos(self.angle)
        self.eta0p = 1 / np.cos(self.angle)
        self.absorptions = []

        for wn in range(0, len(self.wns)):

            lamda = 10000 / self.wns[wn]
            trans = self.trans[wn]  # Here trans can also represent reflection/abosrption. Diff. is self.fittype.
            numbercount += 1
            if numbercount == 3:
                percentage = (self.wns[wn] - self.wns[0]) / (self.wns[len(self.wns) - 1] - self.wns[0]) * 100
                self.progress_callback.emit(percentage)
                self.wn_callback.emit(self.wns[wn])
                numbercount = 0

            delta = 10
            fitsuccess = 0

            if self.subtype == 1:
                self.nsub = np.sqrt(11.67316 + 1 / lamda / lamda + 0.004482633 / (lamda * lamda - 1.108205 * 1.108205))
            elif self.subtype == 2:
                self.nsub = np.sqrt(5.68 + 1.53 * lamda * lamda / (lamda * lamda - 0.366))
            elif self.subtype == 3:
                self.nsub = 1
            self.etasubs = np.sqrt(self.nsub * self.nsub - np.sin(self.angle) * np.sin(self.angle))
            self.etasubp = self.nsub * self.nsub / self.etasubs

            self.n_list = []
            self.k_list = []
            self.etas_list = []
            self.etap_list = []
            self.deltas_list = []
            self.deltap_list = []
            self.ablayers = []

            for l_index in range(0, len(self.layertype_list)):
                if self.layertype_list[l_index] == "CdTe":
                    self.cal_initialpara(1)
                elif self.layertype_list[l_index] == "MCT" or self.layertype_list[l_index] == "SL":
                    self.cal_initialpara(self.entry_x_list[l_index])
                n = self.cal_n(lamda, self.layertype_list[l_index])
                k = 0
                self.n_list.append(n)
                self.k_list.append(k)
                etas = np.sqrt((n - 1j * k) * (n - 1j * k) - np.sin(self.angle) * np.sin(self.angle))
                etap = (n - 1j * k) * (n - 1j * k) / etas
                deltas = 2 * np.pi / lamda * self.entry_d_list[l_index] * etas
                deltap = 2 * np.pi / lamda * self.entry_d_list[l_index] * etas
                self.etas_list.append(etas)
                self.etap_list.append(etap)
                self.deltas_list.append(deltas)
                self.deltap_list.append(deltap)

                if self.checklayer_list[l_index] == 1:
                    self.ablayers.append(l_index)

            for k_test in np.arange(0, 1, 0.001):
                self.matrixs_list = []
                self.matrixp_list = []

                for ab_index in range(0, len(self.ablayers)):
                    n = self.n_list[self.ablayers[ab_index]]
                    k = k_test
                    self.k_list[self.ablayers[ab_index]] = k
                    etas = np.sqrt((n - 1j * k) * (n - 1j * k) - np.sin(self.angle) * np.sin(self.angle))
                    etap = (n - 1j * k) * (n - 1j * k) / etas
                    deltas = 2 * np.pi / lamda * self.entry_d_list[self.ablayers[ab_index]] * etas
                    deltap = 2 * np.pi / lamda * self.entry_d_list[self.ablayers[ab_index]] * etas
                    self.etas_list[self.ablayers[ab_index]] = etas
                    self.etap_list[self.ablayers[ab_index]] = etap
                    self.deltas_list[self.ablayers[ab_index]] = deltas
                    self.deltap_list[self.ablayers[ab_index]] = deltap

                for l in range(0, len(self.layertype_list)):
                    matrixs = np.matrix([[np.cos(self.deltas_list[len(self.layertype_list) - l - 1]),
                                          1j * np.sin(self.deltas_list[len(self.layertype_list) - l - 1]) /
                                          self.etas_list[
                                              len(self.layertype_list) - l - 1]],
                                         [1j * self.etas_list[len(self.layertype_list) - l - 1] * np.sin(
                                             self.deltas_list[len(self.layertype_list) - l - 1]),
                                          np.cos(self.deltas_list[len(self.layertype_list) - l - 1])]])
                    matrixp = np.matrix([[np.cos(self.deltap_list[len(self.layertype_list) - l - 1]),
                                          1j * np.sin(self.deltap_list[len(self.layertype_list) - l - 1]) /
                                          self.etap_list[
                                              len(self.layertype_list) - l - 1]],
                                         [1j * self.etap_list[len(self.layertype_list) - l - 1] * np.sin(
                                             self.deltap_list[len(self.layertype_list) - l - 1]),
                                          np.cos(self.deltap_list[len(self.layertype_list) - l - 1])]])

                    self.matrixs_list.append(matrixs)
                    self.matrixp_list.append(matrixp)

                submatrixs = np.array([[1], [self.etasubs]])
                submatrixs.reshape(2, 1)
                submatrixp = np.array([[1], [self.etasubp]])
                submatrixp.reshape(2, 1)

                products = self.matrixs_list[0]

                for s in range(1, len(self.matrixs_list)):
                    products = np.dot(products, self.matrixs_list[s])

                products = np.dot(products, submatrixs)
                Bs = products.item(0)
                Cs = products.item(1)

                productp = self.matrixp_list[0]

                for p in range(1, len(self.matrixp_list)):
                    productp = np.dot(productp, self.matrixp_list[p])

                productp = np.dot(productp, submatrixp)

                Bp = productp.item(0)
                Cp = productp.item(1)

                Zs = self.eta0s * Bs + Cs
                Zp = self.eta0p * Bp + Cp
                Z2s = self.eta0s * Bs - Cs
                Z2p = self.eta0p * Bp - Cp

                Ztops = Bs * (Cs.conjugate()) - self.etasubs
                Ztopp = Bp * (Cp.conjugate()) - self.etasubp

                Ts = 4 * self.eta0s * self.etasubs / Zs / Zs.conjugate()
                Tp = 4 * self.eta0p * self.etasubp / Zp / Zp.conjugate()

                Rs = Z2s / Zs * ((Z2s / Zs).conjugate())
                Rp = Z2p / Zp * ((Z2p / Zp).conjugate())

                As = 4 * self.eta0s * Ztops.real / Zs / Zs.conjugate()
                Ap = 4 * self.eta0p * Ztopp.real / Zp / Zp.conjugate()
                if self.fittingtype in [4, 6, 10]:  # Absorption
                    peakvalue = (As + Ap) / 2 * 100 * 1
                elif self.fittingtype in [3, 5, 9]:  # Reflection
                    peakvalue = (Rs + Rp) / 2 * 100 * 1 + (Ts + Tp) / 2 * 100 * (1 - self.scalefactor)
                else:
                    peakvalue = (Ts + Tp) / 2 * 100 * self.scalefactor

                if abs(peakvalue - trans) <= delta:
                    fitsuccess = 1
                    delta = abs(peakvalue - trans)
                    basek = k_test

            if fitsuccess == 1:
                if self.fittingtype in [5, 6, 7, 8, 9, 10]:
                    self.absorptions.append(basek)
                else:
                    ab = 4 * np.pi * basek / lamda * 10000
                    self.absorptions.append(ab)
            else:
                self.addlog('Fitting failed at wavenumber = {}cm-1'.format(self.wns[wn]))
                self.absorptions.append(0)

            numbercount2 += 1
            if numbercount2 == 5:
                if self.root.abortmission == 1:
                    try:
                        self.fitline_absorption.pop(0).remove()
                    except (AttributeError, IndexError) as error:
                        pass
                    return "ABORT"

                if self.blindcal == 0:
                    try:
                        self.fitline_absorption.pop(0).remove()
                    except (AttributeError, IndexError) as error:
                        pass

                    self.fitline_absorption = self.absorptionplot.plot(self.wns[0: len(self.absorptions)],
                                                                       self.absorptions,
                                                                       'r',
                                                                       label='Calculated Absorption')
                    self.canvas.draw()
                numbercount2 = 0

        if self.blindcal == 0:
            try:
                self.fitline_absorption.pop(0).remove()
            except (AttributeError, IndexError) as error:
                pass

        return self.absorptions

    def cal_absorption_single(self, wn):

        """Calculate the absorption coefficient at a certain wavenumber."""

        basek = 0
        wn_index = 0

        self.eta0s = np.cos(self.angle)
        self.eta0p = 1 / np.cos(self.angle)

        while True:
            if self.wns[wn_index + 1] > wn >= self.wns[wn_index]:
                break
            else:
                wn_index += 1

        lamda = 10000 / self.wns[wn_index]
        trans = self.trans[wn_index]

        delta = 10
        fitsuccess = 0

        for k_test in np.arange(0, 1, 0.001):

            self.n_list = []
            self.k_list = []
            self.etas_list = []
            self.etap_list = []
            self.deltas_list = []
            self.deltap_list = []
            self.matrixs_list = []
            self.matrixp_list = []

            for i in range(0, len(self.layertype_list)):
                if self.layertype_list[i] == "CdTe":
                    self.cal_initialpara(1)
                elif self.layertype_list[i] == "MCT" or self.layertype_list[i] == "SL":
                    self.cal_initialpara(self.entry_x_list[i])
                n = self.cal_n(lamda, self.layertype_list[i])
                if self.checklayer_list[i] == 0:
                    k = 0
                else:
                    k = k_test
                self.n_list.append(n)
                self.k_list.append(k)
                etas = np.sqrt((n - 1j * k) * (n - 1j * k) - np.sin(self.angle) * np.sin(self.angle))
                etap = (n - 1j * k) * (n - 1j * k) / etas
                deltas = 2 * np.pi / lamda * self.entry_d_list[i] * etas
                deltap = 2 * np.pi / lamda * self.entry_d_list[i] * etas
                self.etas_list.append(etas)
                self.etap_list.append(etap)
                self.deltas_list.append(deltas)
                self.deltap_list.append(deltap)

            if self.subtype == 1:
                self.nsub = np.sqrt(
                    11.67316 + 1 / lamda / lamda + 0.004482633 / (lamda * lamda - 1.108205 * 1.108205))
            elif self.subtype == 2:
                self.nsub = np.sqrt(5.68 + 1.53 * lamda * lamda / (lamda * lamda - 0.366))
            elif self.subtype == 3:
                self.nsub = 1
            self.etasubs = np.sqrt(self.nsub * self.nsub - np.sin(self.angle) * np.sin(self.angle))
            self.etasubp = self.nsub * self.nsub / self.etasubs

            for i in range(0, len(self.layertype_list)):
                matrixs = np.matrix([[np.cos(self.deltas_list[len(self.layertype_list) - i - 1]),
                                      1j * np.sin(self.deltas_list[len(self.layertype_list) - i - 1]) /
                                      self.etas_list[
                                          len(self.layertype_list) - i - 1]],
                                     [1j * self.etas_list[len(self.layertype_list) - i - 1] * np.sin(
                                         self.deltas_list[len(self.layertype_list) - i - 1]),
                                      np.cos(self.deltas_list[len(self.layertype_list) - i - 1])]])
                matrixp = np.matrix([[np.cos(self.deltap_list[len(self.layertype_list) - i - 1]),
                                      1j * np.sin(self.deltap_list[len(self.layertype_list) - i - 1]) /
                                      self.etap_list[
                                          len(self.layertype_list) - i - 1]],
                                     [1j * self.etap_list[len(self.layertype_list) - i - 1] * np.sin(
                                         self.deltap_list[len(self.layertype_list) - i - 1]),
                                      np.cos(self.deltap_list[len(self.layertype_list) - i - 1])]])

                self.matrixs_list.append(matrixs)
                self.matrixp_list.append(matrixp)

            submatrixs = np.array([[1], [self.etasubs]])
            submatrixs.reshape(2, 1)
            submatrixp = np.array([[1], [self.etasubp]])
            submatrixp.reshape(2, 1)

            products = self.matrixs_list[0]

            for i in range(1, len(self.matrixs_list)):
                products = np.dot(products, self.matrixs_list[i])

            products = np.dot(products, submatrixs)
            Bs = products.item(0)
            Cs = products.item(1)

            productp = self.matrixp_list[0]

            for i in range(1, len(self.matrixp_list)):
                productp = np.dot(productp, self.matrixp_list[i])

            productp = np.dot(productp, submatrixp)

            Bp = productp.item(0)
            Cp = productp.item(1)

            Zs = self.eta0s * Bs + Cs
            Zp = self.eta0p * Bp + Cp
            Z2s = self.eta0s * Bs - Cs
            Z2p = self.eta0p * Bp - Cp

            Ztops = Bs * (Cs.conjugate()) - self.etasubs
            Ztopp = Bp * (Cp.conjugate()) - self.etasubp

            Ts = 4 * self.eta0s * self.etasubs / Zs / Zs.conjugate()
            Tp = 4 * self.eta0p * self.etasubp / Zp / Zp.conjugate()

            Rs = Z2s / Zs * ((Z2s / Zs).conjugate())
            Rp = Z2p / Zp * ((Z2p / Zp).conjugate())

            As = 4 * self.eta0s * Ztops.real / Zs / Zs.conjugate()
            Ap = 4 * self.eta0p * Ztopp.real / Zp / Zp.conjugate()
            if self.fittingtype in [4, 6, 10]:  # Absorption
                peakvalue = (As + Ap) / 2 * 100 * 1
            elif self.fittingtype in [3, 5, 9]:  # Reflection
                peakvalue = (Rs + Rp) / 2 * 100 * 1 + (Ts + Tp) / 2 * 100 * (1 - self.scalefactor)
            else:
                peakvalue = (Ts + Tp) / 2 * 100 * self.scalefactor

            if abs(peakvalue - trans) <= delta:
                fitsuccess = 1
                delta = abs(peakvalue - trans)
                basek = k_test

        if fitsuccess == 1:
            if self.fittingtype in [5, 6, 7, 8, 9, 10]:
                return basek
            else:
                ab = 4 * np.pi * basek / lamda * 10000
                return ab
        else:
            self.addlog('Fitting failed at wavenumber = {}cm-1'.format(wn))
            return 0

    def returntrans(self):
        return self.transs

    def returnpeakvalues(self):
        return self.peakvalues

    def returnreflections(self):
        return self.reflections

    def returnabsorptions(self):
        return self.absorptions

    def addlog(self, string, fg="default", bg="default"):
            item = QListWidgetItem(string)
            if fg is not "default":
                item.setForeground(QColor(fg))
            if bg is not "default":
                item.setBackground(QColor(bg))
            self.listbox.addItem(item)
            self.listbox.scrollToItem(item)
            self.listbox.show()


class cal_MCT_a:
    def __init__(self, x, wavenumbers, temperature, fittype):
        self.x = float(x)
        self.wavenumbers = wavenumbers
        self.absorptions = []
        self.T = temperature
        self.fittype = fittype

        if self.fittype == "Chu":
            self.a0 = np.exp(-18.5 + 45.68 * self.x)
            self.E0 = -0.355 + 1.77 * self.x
            self.ag = -65 + 1.88 * self.T + (8694 - 10.31 * self.T) * self.x
            self.Eg = -0.295 + 1.87 * self.x - 0.28 * self.x * self.x + \
                      (
                                  6 - 14 * self.x + 3 * self.x * self.x) * 0.0001 * self.T + 0.35 * self.x * self.x * self.x * self.x
            self.delta_kT = (np.log(self.ag) - np.log(self.a0)) / (self.Eg - self.E0)
            self.beta = -1 + 0.083 * self.T + (21 - 0.13 * self.T) * self.x
        elif self.fittype == "Schacham and Finkman":
            self.a0 = np.exp(-18.88 + 53.61 * self.x)
            self.E0 = -0.3424 + 1.838 * self.x + 0.148 * self.x * self.x * self.x * self.x
            self.Eg = self.E0 + (0.0629 + 0.000768 * self.T) * (1 - 2.14 * self.x) / (1 + self.x)
            self.delta_kT = 32670 * (1 + self.x) / (self.T + 81.9)
            self.beta = 210900 * np.sqrt((1 + self.x) / (81.9 + self.T))
        elif self.fittype == "Yong":
            self.W = 0.013  # not sure
            self.A = 1 / np.power(10, 17)  # not sure
            self.P = 8 / np.power(10, 8)
            self.s = np.sqrt(2 * self.P * self.P / 3)
            self.B = self.A / np.power(np.pi, 2) / np.power(self.s, 3)
            self.E0 = -0.295 + 1.87 * self.x - 0.28 * self.x * self.x + \
                      (
                                  6 - 14 * self.x + 3 * self.x * self.x) * 0.0001 * self.T + 0.35 * self.x * self.x * self.x * self.x

            # print(self.E0)
            # Here E0 is the same equation as Eg in Chu's fomula.
            self.Eg = self.E0 - self.W / 2
            self.b = self.Eg / 2

        self.ab = 0

        self.cal_all()

    def cal_Urbach(self, energy):
        if self.fittype == "Chu" or self.fittype == "Schacham and Finkman":
            self.ab = self.a0 * np.exp(self.delta_kT * (energy - self.E0))
        elif self.fittype == "Yong":
            self.ab = self.B / self.E0 * \
                      ((self.W / 2 + self.b) * np.sqrt((self.W / 2 + self.b) * (self.W / 2 + self.b) - self.b * self.b)
                       + 1 / 8 * (self.W / 2 + 2 * self.b) * np.sqrt((self.W / 2 + 2 * self.b) * (
                                          self.W / 2 + 2 * self.b) - 4 * self.b * self.b)) * np.exp(energy / self.W)

        return self.ab

    def cal_Kane(self, energy):
        if self.fittype == "Chu":
            self.ab = self.ag * np.exp(np.sqrt(self.beta * (energy - self.Eg)))
        elif self.fittype == "Schacham and Finkman":
            self.ab = self.beta * np.sqrt(energy - self.Eg)
        elif self.fittype == "Yong":
            self.ab = self.B / energy * ((energy - self.Eg + self.b) * np.sqrt(
                (energy - self.Eg + self.b) * (energy - self.Eg + self.b) - self.b * self.b)
                                         + 1 / 8 * (energy - self.Eg + 2 * self.b) * np.sqrt(
                        (energy - self.Eg + 2 * self.b) * (energy - self.Eg + 2 * self.b) - 4 * self.b * self.b))
        return self.ab

    def cal_all(self):
        self.absorptions = []
        for wavenumber in self.wavenumbers:
            wl = 10000 / wavenumber
            E = 4.13566743 * 3 / 10 / wl  # Here E is in unit of eV.
            if self.fittype == "Chu" or self.fittype == "Schacham and Finkman":
                if E <= self.Eg:
                    self.absorptions.append(self.cal_Urbach(E))
                else:
                    self.absorptions.append(self.cal_Kane(E))
            if self.fittype == "Yong":
                if E <= self.Eg + self.W / 2:
                    self.absorptions.append(self.cal_Urbach(E))
                else:
                    self.absorptions.append(self.cal_Kane(E))

    def return_absorptions(self):
        return self.absorptions


class ThreadSignals(QObject):

    """Defines the signals available from a running worker thread."""

    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)
    wn = pyqtSignal(int)


class Worker(QRunnable):

    """
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    """

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = ThreadSignals()

        # Add the callback to our kwargs
        kwargs['progress_callback'] = self.signals.progress
        kwargs['wn_callback'] = self.signals.wn

    @pyqtSlot()
    def run(self):

        """Initialise the runner function with passed args, kwargs."""

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


class PlotCanvas(FigureCanvas):

    def __init__(self, root, width, height, xlowcut, xhighcut, y1lowcut, y1highcut, y2lowcut, y2highcut):
        self.fig = Figure(figsize=(width, height), dpi=100)
        self.fig.subplots_adjust(left=0.08, bottom=0.12, right=0.92, top=0.95)
        self.plot = self.fig.add_subplot(111)
        self.plot.set_xlabel('Wavenumbers ($cm^{-1}$)')
        self.plot.set_ylabel('Transmission (%)')
        self.plot.set_xlim([xlowcut, xhighcut])
        self.plot.set_ylim([y1lowcut, y1highcut])
        self.plot.grid(True)
        self.vline = self.plot.axvline(x=400, visible=True, color='k', linewidth=1)
        self.hline = self.plot.axhline(y=0, visible=True, color='k', linewidth=1)
        self.dot = self.plot.plot(0, 0, marker='o', color='r')

        FigureCanvas.__init__(self, self.fig)

        self.absorptionplot = self.plot.twinx()
        self.absorptionplot.set_ylabel('Absorption Coefficient ($cm^{-1}$)')
        self.absorptionplot.set_ylim([y2lowcut, y2highcut])

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Preferred,
                                   QSizePolicy.Preferred)
        FigureCanvas.updateGeometry(self)


class loadstru(QDialog, Ui_loadstru):

    """Load existing layer structure."""

    def __init__(self, root, filelist):
        QDialog.__init__(self, root)
        Ui_loadstru.__init__(self)
        self.setupUi(self)
        self.filelist = filelist
        self.index1 = self.filelist.index("nBn_with_SL_barrier_PM")
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


class FTIRsettings(QDialog, Ui_settings_FTIR):

    """Optinal settings for customized result."""

    def __init__(self, root, temp, angle, blindcal, showr, showa, useidealk, datatype, calk):
        QDialog.__init__(self, root)
        Ui_settings_FTIR.__init__(self)
        self.setupUi(self)
        self.root = root
        self.Temp = temp
        self.angle = angle
        self.blindcal = blindcal
        self.displayreflection = showr
        self.displayabsorption = showa
        self.use_ideal_k = useidealk
        self.data_loaded = datatype
        self.cal_k_instead = calk
        self.datalist = ["Transmission data", "Reflection data", "Absorption data"]
        self.index1 = 0
        self.config = configparser.ConfigParser()
        self.config.read(resource_path(os.path.join("FTIR_Fitting_Tool", 'configuration.ini')))

        self.dataoption.addItems(self.datalist)
        self.dataoption.setCurrentIndex(self.data_loaded)
        self.dataoption.currentIndexChanged.connect(self.selectionchange)

        self.entry_s1.setText(str(temp))
        self.entry_s1.setValidator(QDoubleValidator(0.00, 500.00, 2))
        self.entry_22.setText(str(angle))
        self.entry_22.setValidator(QDoubleValidator(0.00, 100.00, 2))
        if self.blindcal == 1:
            self.checkboxblindcal.setChecked(True)

        if self.displayreflection == 1:
            self.checkboxr.setChecked(True)

        if self.displayabsorption == 1:
            self.checkboxa.setChecked(True)

        if self.use_ideal_k == 1:
            self.checkboxi.setChecked(True)

        if self.cal_k_instead == 1:
            self.checkboxk.setChecked(True)

        self.resultbox.accepted.connect(self.buttonOkayfuncton)
        self.resultbox.rejected.connect(self.buttonCancelfuncton)
        self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Enter), self)
        self.shortcut.activated.connect(self.buttonOkayfuncton)

    def buttonOkayfuncton(self):
        self.Temp = float(self.entry_s1.text())
        self.angle = float(self.entry_22.text())

        if self.checkboxblindcal.isChecked() is True:
            self.blindcal = 1
        else:
            self.blindcal = 0
        if self.checkboxr.isChecked() is True:
            self.displayreflection = 1
        else:
            self.displayreflection = 0
        if self.checkboxa.isChecked() is True:
            self.displayabsorption = 1
        else:
            self.displayabsorption = 0
        if self.checkboxi.isChecked() is True:
            self.use_ideal_k = 1
        else:
            self.use_ideal_k = 0
        if self.checkboxk.isChecked() is True:
            self.cal_k_instead = 1
            self.root.buttoncal.setText("Cal k")
        else:
            self.cal_k_instead = 0
            self.root.buttoncal.setText("Cal (\u03B1)")
        self.data_loaded = self.index1

        if self.checkbox_rem.isChecked() is True:
            cfgfile = open(resource_path(os.path.join("FTIR_Fitting_Tool", 'configuration.ini')), 'w')
            self.config.set("Settings", "blindcalculation", str(self.blindcal))
            self.config.set("Settings", "showreflection", str(self.displayreflection))
            self.config.set("Settings", "showabsorption", str(self.displayabsorption))
            self.config.set("Settings", "data_loaded", str(self.data_loaded))
            self.config.set("Settings", "cal_k_instead", str(self.cal_k_instead))
            self.config.set("Settings", "use_ideal_k", str(self.use_ideal_k))

            self.config.write(cfgfile)
            cfgfile.close()

    def buttonCancelfuncton(self):
        pass

    def selectionchange(self, i):
        self.index1 = i


class FTIRMCTa(QDialog, Ui_MCTa):

    """Calculate MCT absorption."""

    def __init__(self, root):
        QDialog.__init__(self, root)
        Ui_MCTa.__init__(self)
        self.setupUi(self)
        self.index1 = 0
        self.method = 0
        self.x = 0.21
        self.saveornot = 0
        self.methodlist = ["Chu", "Schacham and Finkman", "Yong"]

        self.entry_x.setText(str(self.x))
        self.entry_x.setValidator(QDoubleValidator(0.000, 1.000, 3))
        self.methodnamegetoption.addItems(self.methodlist)
        self.methodnamegetoption.setCurrentIndex(self.method)
        self.methodnamegetoption.currentIndexChanged.connect(self.selectionchange)
        self.resultbox.accepted.connect(self.buttonOkayfuncton)
        self.resultbox.rejected.connect(self.buttonCancelfuncton)
        self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Enter), self)
        self.shortcut.activated.connect(self.buttonOkayfuncton)

    def buttonOkayfuncton(self):
        self.method = self.index1
        self.x = float(self.entry_x.text())
        if self.checksave.isChecked() is True:
            self.saveornot = 1

    def buttonCancelfuncton(self):
        pass

    def selectionchange(self, i):
        self.index1 = i


class FTIRhelp(QDialog, Ui_help_FTIR):

    """Help window with update logs."""

    def __init__(self, root):
        QDialog.__init__(self, root)
        Ui_help_FTIR.__init__(self)
        self.setupUi(self)


class FTIR_fittingtool_GUI_v3(QWidget, Ui_FTIR):

    """Main FTIR fitting tool window."""

    def __init__(self, root, masterroot):
        QWidget.__init__(self)
        Ui_FTIR.__init__(self)
        self.setupUi(self)
        self.root = root
        self.masterroot = masterroot
        self.listbox = self.masterroot.listbox
        self.statusbar = self.masterroot.statusbar
        self.status1 = self.masterroot.status1
        self.status2 = self.masterroot.status2
        self.progressbar = self.masterroot.progressbar
        self.wavenumbers = []
        self.wavenumbers_cut = []
        self.transmissions = []
        self.trans_cut = []
        self.absorptions = []
        self.filename = ''
        self.numberofdata = 0
        self.numberofdata2 = 0
        self.colororders = ['blue', 'green', 'cyan', 'magenta', 'yellow', 'orange']
        self.colororders2 = ['red', 'green', 'cyan', 'magenta', 'yellow', 'orange', 'red', 'green', 'cyan', 'magenta',
                             'yellow', 'black']
        self.intial_thicknesses_or_not = 1
        self.entry_d_list_initial = []
        self.peakvalues_fit = []
        self.MSE = 0
        self.smallest_MSE = 100000000
        self.best_CdTe_offset = 0
        self.best_HgTe_offset = 0

        self.trans = 0
        self.wavenumber = 0
        self.wavelength = 0
        self.energy = 0
        self.composition = 0
        self.Temp = 300
        self.angle = 0
        self.lowercut = 400
        self.highercut = 6000
        self.transcut = 70
        self.transcutlow = 0
        self.y2_cut = 12000
        self.xclick = 0
        self.positiony = 0

        self.fitline_data = None
        self.fitline_data_ab = None
        self.fitline_trans = None
        self.fitline_reflect = None
        self.fitline_absorb = None
        self.fitline_absorb_MCT = None

        self.osdir = os.path.dirname(os.path.abspath(__file__))
        self.totaltime = 0
        self.programbusy = 0
        self.needmorehelp = 0
        self.abortmission = 0
        self.progress_var = 0
        self.wn_beingcalculated = 0

        self.config = configparser.ConfigParser()
        self.config.read(resource_path(os.path.join("FTIR_Fitting_Tool", 'configuration.ini')))

        self.blindcal = int(self.config["Settings"]["blindcalculation"])
        self.displayreflection = int(self.config["Settings"]["showreflection"])
        self.displayabsorption = int(self.config["Settings"]["showabsorption"])
        self.data_loaded = int(self.config["Settings"]["data_loaded"])
        self.cal_k_instead = int(self.config["Settings"]["cal_k_instead"])
        self.use_ideal_k = int(self.config["Settings"]["use_ideal_k"])

        self.warningcolor1 = 'red'
        self.warningcolor2 = 'orange'
        self.warningcolor3 = 'royalblue'
        self.highcolor = self.warningcolor3
        self.lowcolor = self.highcolor

        self.buttoncal.setText("Cal (\u03B1)")
        if self.cal_k_instead == 1:
            self.buttoncal.setText("Cal k")
        if disableSQL == 1:
            self.buttonsql.setEnabled(False)
        self.buttonmct.setText("MCT \u03B1")
        self.buttonsettings.clicked.connect(self.settings)
        self.buttonload.clicked.connect(self.load_structure)
        self.buttonclear.clicked.connect(self.clearalldata)
        self.buttonsave2.clicked.connect(self.save_structure)
        self.buttonopen.clicked.connect(self.openfromfile)
        self.buttonsql.clicked.connect(self.openfromsql)
        self.buttonsave.clicked.connect(self.savetofile)
        self.buttonmct.clicked.connect(self.cal_MCT_absorption)
        self.buttonshowtrans.clicked.connect(self.show_fringes)
        self.buttonfringes.clicked.connect(self.fit_fringes)
        self.buttoncal.clicked.connect(self.cal_absorption)
        self.buttonabort.clicked.connect(self.Abort_mission)
        self.shortcut0 = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+P"), self)
        self.shortcut0.activated.connect(self.help)
        self.shortcut1 = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self)
        self.shortcut1.activated.connect(self.openfromfile)
        self.shortcut2 = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+L"), self)
        self.shortcut2.activated.connect(self.load_structure)
        self.shortcut3 = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+A"), self)
        self.shortcut3.activated.connect(self.cal_absorption)
        self.shortcut4 = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+F"), self)
        self.shortcut4.activated.connect(self.fit_fringes)
        self.shortcut5 = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), self)
        self.shortcut5.activated.connect(self.show_fringes)

        self.button31.clicked.connect(self.getbutton31)
        self.button32.clicked.connect(self.getbutton32)
        self.button33.clicked.connect(self.getbutton33)
        self.button332.clicked.connect(self.getbutton332)
        self.button34.clicked.connect(self.zoomall)
        self.button35.clicked.connect(self.CUT)
        self.button_21.clicked.connect(self.setoffsets)

        self.mplplot = PlotCanvas(self.frame1, 7, 3.8, self.lowercut, self.highercut,
                                  self.transcutlow, self.transcut, 0, self.y2_cut)
        self.FTIRfigure = self.mplplot.fig
        self.FTIRplot = self.mplplot.plot
        self.absorptionplot = self.mplplot.absorptionplot
        self.vline = self.mplplot.vline
        self.hline = self.mplplot.hline
        self.dot = self.mplplot.dot
        self.frame1_layout.addWidget(self.mplplot)
        self.mplplot.show()
        self.mplplot.mpl_connect('button_press_event', self.onpick)

        self.lb_layer.setText('﻿       Layers\u2193')
        self.lb_x.setText('x\u2193')
        self.lb_d.setText('d(\u03BCm)\u2193')

        self.available_materials = ["CdTe", "MCT", "SL", "Si", "ZnSe", "BaF2", "Ge", "ZnS", "Si3N4", "Air",
                                    "SiO", "PbTe", "Al"]
        self.available_subs = ["Si", "CdZnTe", "Air"]

        self.layernumber = 0
        self.subtype = 1

        self.suboption = QComboBox()
        self.suboption.addItems(self.available_subs)
        self.suboption.setCurrentIndex(self.subtype - 1)

        self.entry_x_0 = QLineEdit()
        self.entry_x_0.setReadOnly(True)
        self.entry_x_0.setText("1")
        self.entry_d_0 = QLineEdit()
        self.entry_d_0.setValidator(QDoubleValidator(0.00, 1000, 2))
        self.entry_d_0.setText("500")
        self.checksub = QCheckBox()
        self.checksub.setChecked(True)

        self.layeroption1, self.layeroption2, self.layeroption3, self.layeroption4, self.layeroption5, \
        self.layeroption6, self.layeroption7, self.layeroption8, self.layeroption9, self.layeroption10, \
        self.layeroption11, self.layeroption12, self.layeroption13, self.layeroption14, self.layeroption15, \
        self.layeroption16, self.layeroption17, self.layeroption18, self.layeroption19, self.layeroption20, \
        self.layeroption21, self.layeroption22, self.layeroption23 \
            = QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), \
              QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), \
              QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox(), QComboBox()
        self.entry_x_1, self.entry_x_2, self.entry_x_3, self.entry_x_4, self.entry_x_5, \
        self.entry_x_6, self.entry_x_7, self.entry_x_8, self.entry_x_9, self.entry_x_10, \
        self.entry_x_11, self.entry_x_12, self.entry_x_13, self.entry_x_14, self.entry_x_15, \
        self.entry_x_16, self.entry_x_17, self.entry_x_18, self.entry_x_19, self.entry_x_20, \
        self.entry_x_21, self.entry_x_22, self.entry_x_23 \
            = QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), \
              QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), \
              QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit()
        self.entry_d_1, self.entry_d_2, self.entry_d_3, self.entry_d_4, self.entry_d_5, \
        self.entry_d_6, self.entry_d_7, self.entry_d_8, self.entry_d_9, self.entry_d_10, \
        self.entry_d_11, self.entry_d_12, self.entry_d_13, self.entry_d_14, self.entry_d_15, \
        self.entry_d_16, self.entry_d_17, self.entry_d_18, self.entry_d_19, self.entry_d_20, \
        self.entry_d_21, self.entry_d_22, self.entry_d_23 \
            = QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), \
              QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), \
              QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit()
        self.checklayer1, self.checklayer2, self.checklayer3, self.checklayer4, self.checklayer5, \
        self.checklayer6, self.checklayer7, self.checklayer8, self.checklayer9, self.checklayer10, \
        self.checklayer11, self.checklayer12, self.checklayer13, self.checklayer14, self.checklayer15, \
        self.checklayer16, self.checklayer17, self.checklayer18, self.checklayer19, self.checklayer20, \
        self.checklayer21, self.checklayer22, self.checklayer23 \
            = QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), \
              QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), \
              QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox(), QCheckBox()

        for layer in range(1, 24):
            getattr(self, "layeroption{}".format(layer)).addItems(self.available_materials)
            if layer == 1:
                getattr(self, "layeroption{}".format(layer)).setCurrentIndex(0)
                getattr(self, "entry_x_{}".format(layer)).setText("1.00")
            else:
                getattr(self, "layeroption{}".format(layer)).setCurrentIndex(1)
                getattr(self, "entry_x_{}".format(layer)).setText("0.30")

            getattr(self, "entry_x_{}".format(layer)).setValidator(QDoubleValidator(0.00, 1, 3))

            getattr(self, "entry_d_{}".format(layer)).setValidator(QDoubleValidator(0.00, 20, 3))
            getattr(self, "entry_d_{}".format(layer)).setText("0.00")

            getattr(self, "checklayer{}".format(layer)).setChecked(True)

        self.buttonaddlayer.clicked.connect(self.add_layer_on_top)

        self.buttonabort.hide()
        self.buttonabort.setStyleSheet('QPushButton {color: red;}')
        self.grid22.addWidget(self.suboption, 27, 0)
        self.grid22.addWidget(self.entry_x_0, 27, 1)
        self.grid22.addWidget(self.entry_d_0, 27, 2)
        self.grid22.addWidget(self.checksub, 27, 3)
        self.grid22.addWidget(self.buttonaddlayer, 1, 0, 1, 4)
        self.threadpool = QThreadPool()

    def getbutton31(self):
        self.entry_31.setText("%.2f" % self.xclick)

    def getbutton32(self):
        self.entry_32.setText("%.2f" % self.xclick)

    def getbutton33(self):
        self.entry_33.setText("%.2f" % self.positiony)

    def getbutton332(self):
        self.entry_332.setText("%.2f" % self.positiony)

    def CUT(self):
        self.lowercut = float(self.entry_31.text())
        self.highercut = float(self.entry_32.text())
        self.transcutlow = float(self.entry_33.text())
        self.transcut = float(self.entry_332.text())
        self.y2_cut = float(self.entry_y2.text())
        self.FTIRplot.set_xlim([self.lowercut, self.highercut])
        self.FTIRplot.set_ylim([self.transcutlow, self.transcut])
        self.absorptionplot.set_ylim([0, self.y2_cut])
        self.mplplot.draw()

    def zoomall(self):
        self.entry_31.setText("400")
        self.entry_32.setText("6000")
        self.entry_33.setText("0")
        self.entry_332.setText("70")
        self.entry_y2.setText("12000")
        self.wavenumbers_cut = self.wavenumbers
        self.trans_cut = self.transmissions
        self.CUT()

    def setoffsets(self):

        """Adjust layer thicknesses using CdTe/HgTe offset. Only the layers with check marks will be changed. """

        if self.intial_thicknesses_or_not == 1:
            self.entry_d_list_initial = []

            for i in range(1, self.layernumber + 1):
                self.entry_d_list_initial.append(float(getattr(self, "entry_d_{}".format(i)).text()))
            self.intial_thicknesses_or_not = 0

        for i in range(1, self.layernumber + 1):
            if getattr(self, "checklayer{}".format(i)).isChecked() is True:
                if self.available_materials[getattr(self, "layeroption{}".format(i)).currentIndex()] == "CdTe":
                    new_d = self.entry_d_list_initial[i - 1] * (1 + 0.01 * float(self.entry_23.text()))
                    getattr(self, "entry_d_{}".format(i)).setText("{0:.2f}".format(new_d))
                elif self.available_materials[getattr(self, "layeroption{}".format(i)).currentIndex()] == "MCT" \
                        or self.available_materials[getattr(self, "layeroption{}".format(i)).currentIndex()] == "SL":
                    new_d = self.entry_d_list_initial[i - 1] * float(getattr(self, "entry_x_{}".format(i)).text()) \
                            * (1 + 0.01 * float(self.entry_23.text())) \
                            + self.entry_d_list_initial[i - 1] * (
                                        1 - float(getattr(self, "entry_x_{}".format(i)).text())) \
                            * (1 + 0.01 * float(self.entry_24.text()))
                    getattr(self, "entry_d_{}".format(i)).setText("{0:.2f}".format(new_d))

    def add_layer_on_top(self, layernum=None, x="default", d="default", check="default"):
        if self.layernumber > 22:
            self.buttonaddlayer.setEnabled(False)
            return
        self.layernumber += 1
        self.grid22.addWidget(getattr(self, "layeroption{}".format(self.layernumber)), 27 - self.layernumber, 0)
        self.grid22.addWidget(getattr(self, "entry_x_{}".format(self.layernumber)), 27 - self.layernumber, 1)
        self.grid22.addWidget(getattr(self, "entry_d_{}".format(self.layernumber)), 27 - self.layernumber, 2)
        self.grid22.addWidget(getattr(self, "checklayer{}".format(self.layernumber)), 27 - self.layernumber, 3)

        if layernum is not False:   #? If no argument passed to func, this argument will be changed to False? Why?
            getattr(self, "layeroption{}".format(self.layernumber)).setCurrentIndex(self.available_materials.index(layernum))
        if x is not "default":
            getattr(self, "entry_x_{}".format(self.layernumber)).setText(str(x))
        if d is not "default":
            getattr(self, "entry_d_{}".format(self.layernumber)).setText(str(d))
        if check is not "default":
            #if check == "1":
            getattr(self, "checklayer{}".format(self.layernumber)).setChecked(check)

    def getlayerstructure(self):
        self.layertype_list, self.entry_x_list, self.entry_d_list, self.checklayer_list = [], [], [], []

        for i in range(1, self.layernumber + 1):
            self.layertype_list.append(self.available_materials[getattr(self, "layeroption{}".format(i)).currentIndex()])
            self.entry_x_list.append(float(getattr(self, "entry_x_{}".format(i)).text()))
            self.entry_d_list.append(float(getattr(self, "entry_d_{}".format(i)).text()))
            if getattr(self, "checklayer{}".format(i)).isChecked() is True:
                self.checklayer_list.append(1)
            else:
                self.checklayer_list.append(0)

        self.subtype = self.suboption.currentIndex() + 1

    def try_remove_fitline(self, thefitline):

        """Remove an existing line."""

        try:
            thefitline.pop(0).remove()
        except (AttributeError, IndexError) as error:
            pass

    def plot_and_show(self, theplot, fitline, remove_fitline_or_not, x, y, color, thelabel, ylabel, legend_or_not,
                      legend_location):

        """Plot a new line on the subplot, and show it."""

        if remove_fitline_or_not == 1:
            self.try_remove_fitline(fitline)
        fitline = theplot.plot(x, y, color, label=thelabel)
        theplot.set_ylabel(ylabel)

        if theplot == self.absorptionplot and self.cal_k_instead == 1:
            self.y2_cut = 0.6
            self.entry_y2.setText(float(self.y2_cut))
            theplot.set_ylim([0, self.y2_cut])

        if legend_or_not == 1:
            legend = theplot.legend(loc=legend_location, shadow=True)
            frame = legend.get_frame()

            # Set the fontsize
            for label in legend.get_texts():
                label.set_fontsize('medium')

            for label in legend.get_lines():
                label.set_linewidth(1.5)

        self.mplplot.draw()
        return fitline

    def help(self):
        if self.needmorehelp == 0:
            self.addlog('-' * 160, "blue")
            self.addlog("FTIR fitting tool, with customization of layer structures. v{}. ".format(__version__),
                        self.warningcolor3)
            self.addlog('Open a FTIR .csv file --> Customize your layer structure on the right. '
                        'You can load or save a structure from file.')
            self.addlog('--> Click "Show Trans" to see the result. ')
            self.addlog('--> Click "Set" to apply CdTe/HgTe offsets to the layer thicknesses. '
                        'Note! Only the layers with check marks will be changed accordingly. ')
            self.addlog('You can do calculation using "Blind calculation" from "Settings" menu. It\'s usually faster.')

            if _platform == "darwin":
                self.addlog('For more help and information, press ⌘+P again.', self.warningcolor3)
            elif _platform == "win32" or _platform == "win64" or _platform == "linux" or _platform == "linux2":
                self.addlog('For more help and information, press Ctrl+P again.', self.warningcolor3)
            self.addlog('-' * 160, "blue")

            self.needmorehelp = 1

        elif self.needmorehelp == 1:
            window_help = FTIRhelp(self)
            window_help.show()

    def settings(self):

        """Cutomized Settings. """

        window_settings_FTIR = FTIRsettings(self, self.Temp, self.angle, self.blindcal, self.displayreflection,
                                   self.displayabsorption, self.use_ideal_k, self.data_loaded, self.cal_k_instead)
        window_settings_FTIR.show()

        yesorno = window_settings_FTIR.exec_()  # Crucial to capture the result. 1 for Yes and 0 for No.

        if yesorno == 1:
            self.Temp = window_settings_FTIR.Temp
            self.angle = window_settings_FTIR.angle
            self.blindcal = window_settings_FTIR.blindcal
            self.displayreflection = window_settings_FTIR.displayreflection
            self.displayabsorption = window_settings_FTIR.displayabsorption
            self.data_loaded = window_settings_FTIR.data_loaded
            self.cal_k_instead = window_settings_FTIR.cal_k_instead
            self.use_ideal_k = window_settings_FTIR.use_ideal_k

    def openfromfile(self):

        """Open a FTIR transmission .csv file. """

        if self.programbusy == 1:
            return

        if self.numberofdata >= 6 or self.numberofdata2 >= 6:
            self.addlog('Cannot add more data file.', self.warningcolor1)
            return

        self.wavenumbers = []
        self.transmissions = []
        self.absorptions = []

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

        self.filepath.setText(self.filename)
        if self.filename[0:3] == 'Abs':
            with open(file[0], 'r') as f:
                reader = csv.reader(f, delimiter=',')
                for row in reader:
                    try:
                        self.wavenumbers.append(float(row[0]))
                        self.absorptions.append(float(row[1]))
                    except ValueError:
                        pass
            f.close()

            self.fitline_data_ab = self.plot_and_show(self.absorptionplot, self.fitline_data_ab, 0,
                                                      self.wavenumbers, self.absorptions,
                                                      self.colororders2[self.numberofdata2], self.filename,
                                                      'Absorption Coefficient ($cm^{-1}$)', 1, 'upper right')

            self.addlog('Added data {} ({})'.format(self.filename, self.colororders2[self.numberofdata2]))
            self.numberofdata2 += 1

        else:
            with open(file[0], 'r') as f:
                reader = csv.reader(f, delimiter=',')
                for row in reader:
                    try:
                        self.wavenumbers.append(float(row[0]))
                        self.transmissions.append(float(row[1]))
                    except ValueError:
                        pass
            f.close()

            self.fitline_data = self.plot_and_show(self.FTIRplot, self.fitline_data, 0, self.wavenumbers,
                                                   self.transmissions, self.colororders[self.numberofdata],
                                                   self.filename, 'Transmission (%)', 1, 'upper right')

            self.addlog('Added data {} ({})'.format(self.filename, self.colororders[self.numberofdata]))
            self.numberofdata += 1

        if len(self.wavenumbers) == 5810:
            self.addlog('Sample is probably characterized at EPIR.')
        elif len(self.wavenumbers) == 1946:
            self.addlog('Sample is probably characterized at UIC.')
        self.addlog('Hint: To display absorption coefficient at any point instantly, '
                    'a layer structure must be created or loaded first.', self.warningcolor3)

    def openfromsql(self):

        """Open from sql database. Only works at UIC. """

        if self.programbusy == 1:
            return

        if self.numberofdata >= 6:
            self.addlog('Cannot add more data file.', self.warningcolor1)
            return

        Get_Data(self, self.addsqldata)

    def addsqldata(self, meta_data, data):
        if not meta_data or not data or len(data) == 0:
            return
        if not data[0]:
            self.addlog("Empty input! Make sure background file is selected.", self.warningcolor1)
            return
        self.wavenumbers = data[0]
        self.transmissions = np.array(data[1]) * 100
        my_label = meta_data["sample_name"] + ' at T=' + str(
            meta_data["temperature_in_k"]) + ' K'  # "date(time)", "bias_in_v", "time(time)"

        self.filepath.setText(my_label)

        self.fitline_data = self.plot_and_show(self.FTIRplot, self.fitline_data, 0, self.wavenumbers,
                                               self.transmissions, self.colororders[self.numberofdata],
                                               my_label, 'Transmission (%)', 1, 'upper right')

        self.addlog('Added data {} ({})'.format(self.filename, self.colororders[self.numberofdata]))
        self.numberofdata += 1

    def savetofile(self):

        """Save calculated Transmission/Reflection/Absorption to file."""

        if self.programbusy == 1:
            return

        if self.peakvalues_fit == []:
            self.addlog("There is nothing to save. ", self.warningcolor2)
            return

        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        saveascsv = dlg.getSaveFileName(self, 'Save file', self.osdir, "CSV files (*.CSV *.csv)")

        if saveascsv[0] == "":
            return

        f = open(saveascsv[0], "w")
        if self.displayreflection == 1 or self.displayabsorption == 1:
            f.write("wn,T,R,A\n")

            for i in range(0, len(self.wavenumbers_cut)):
                f.write("{0:.6e},{1:.6e},{2:.6e},{3:.6e}\n".format(self.wavenumbers_cut[i], self.peakvalues_fit[i],
                                                                   self.reflections_fit[i], self.absorptions_fit[i]))
        else:
            f.write("wn,T\n")

            for i in range(0, len(self.wavenumbers_cut)):
                f.write("{0:.6e},{1:.6e}\n".format(self.wavenumbers_cut[i], self.peakvalues_fit[i]))

        f.close()

        self.addlog('Saved the file to: {}'.format(saveascsv[0]))

    def load_structure(self):

        """Load existing heterojunction structures (.csv files.)"""

        if self.programbusy == 1:
            return

        def loadornotfunc():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)

            msg.setText("A structure can only be loaded on bare substrate. Clear everything to proceed?")
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)

            result = msg.exec_()
            if result == QMessageBox.Ok:
                return 1
            else:
                return 0

        if self.layernumber != 0:
            loadornot = loadornotfunc()
            if loadornot == 1:
                self.clearalldata()
                return  # There should't be anything after self.clearalldata because the mainwindow widget has changed.
            else:
                return

        self.structure_dir = resource_path("Preload_Structure")

        filelist = []
        for item in os.listdir(self.structure_dir):
            if item[-4:None] == ".CSV" or item[-4:None] == ".csv":
                filelist.append(item[0:-4])

        if filelist == []:
            self.addlog('No structure is found. Check if "Preload_Structure" folder exists.', self.warningcolor1)
            return

        filelist = sorted(filelist)

        window_load = loadstru(self, filelist)
        window_load.show()

        yesorno = window_load.exec_()   # Crucial to capture the result. 1 for Yes and 0 for No.

        result = window_load.result
        if result >= 0:
            self.layernumber = 0

            self.Structurename = filelist[result] + ".CSV"
            filename = self.structure_dir + "/" + self.Structurename

            layerlist = []
            xlist = []
            dlist = []
            checklist = []

            with open(filename, 'r') as f:
                reader = csv.reader(f, delimiter=',')
                for row in reader:
                    try:
                        layerlist.append(row[0])
                        xlist.append(float(row[1]))
                        dlist.append(float(row[2]))
                        checklist.append(int(row[3]))
                    except ValueError:
                        pass

            for i in range(0, len(layerlist)):
                if layerlist[i] in self.available_materials:
                    self.add_layer_on_top(layerlist[i], xlist[i], dlist[i], checklist[i])
                else:
                    self.addlog("Invalid Structure file.", self.warningcolor1)
                    return

            self.addlog('Loaded Structure {}.'.format(self.Structurename[0:-4]))
            return
        else:
            pass

    def save_structure(self):

        """Save the customized structure to file. This is the best way to create structure files."""

        if self.layernumber == 0:
            self.addlog("There is nothing to save.", self.warningcolor2)
            return

        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        saveascsv = dlg.getSaveFileName(self, 'Save file', self.osdir, "CSV files (*.CSV *.csv)")

        if saveascsv[0] == "":
            return

        f = open(saveascsv[0], "w")

        self.getlayerstructure()

        for i in range(0, len(self.layertype_list)):
            f.write("{},{},{},{}\n".format(self.layertype_list[i], self.entry_x_list[i], self.entry_d_list[i],
                                           int(self.checklayer_list[i])))

        f.close()

        self.addlog('Saved the Structure to: {}'.format(saveascsv[0]))

    def cal_MCT_absorption(self):

        """Calculate MCT absorption using various method. """

        if self.programbusy == 1:
            return
        window_MCT_FTIR = FTIRMCTa(self)
        window_MCT_FTIR.show()

        yesorno = window_MCT_FTIR.exec_()  # Crucial to capture the result. 1 for Yes and 0 for No.

        if yesorno == 1:
            comp = window_MCT_FTIR.x
            method = window_MCT_FTIR.method
            saveornot = window_MCT_FTIR.saveornot

            methodlist = ["Chu", "Schacham and Finkman", "Yong"]

            if self.wavenumbers == []:
                self.wavenumbers_MCT = []
                addon = 0
                while addon <= 6000:
                    self.wavenumbers_MCT.append(400 + addon)
                    addon += 5
            else:
                self.wavenumbers_MCT = self.wavenumbers

            fitobject = cal_MCT_a(comp, self.wavenumbers_MCT, self.Temp, methodlist[method])

            self.absorptions = fitobject.return_absorptions()

            self.try_remove_fitline(self.fitline_absorb_MCT)
            self.fitline_absorb_MCT = self.plot_and_show(self.absorptionplot, self.fitline_absorb_MCT, 0,
                                                         self.wavenumbers_MCT, self.absorptions,
                                                         self.colororders2[self.numberofdata2], '',
                                                         'Absorption Coefficient ($cm^{-1}$)', 0, 'upper right')

            self.addlog("Showing MCT abosorption curve "
                        "for x = {} at {}K using {}'s formula. ({})".format(comp, self.Temp,
                                                                            methodlist[method],
                                                                            self.colororders2[self.numberofdata2]))
            self.numberofdata2 += 1

            if saveornot == 1:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)

                msg.setText("Save the result as a .csv file?")
                msg.setWindowTitle("Save?")
                msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)

                result = msg.exec_()
                if result == QMessageBox.Ok:
                    dlg = QFileDialog()
                    dlg.setFileMode(QFileDialog.AnyFile)
                    saveascsv = dlg.getSaveFileName(self, 'Save file', self.osdir, "CSV files (*.CSV *.csv)")

                    if saveascsv[0] == "":
                        return
                    f = open(saveascsv[0], "w")
                    for i in range(0, len(self.wavenumbers)):
                        f.write("{0:.6e},{1:.6e}\n".format(self.wavenumbers_MCT[i], self.absorptions[i]))
                    f.close()

                    self.addlog('Saved the file to: {}'.format(saveascsv[0]))
                else:
                    return
        else:
            return

    def show_fringes(self):

        """Show the calculated fringes curve based the structure and parameters provided. """

        if self.programbusy == 1:
            self.addlog("Another mission is in process.", self.warningcolor2)
            return

        if self.layernumber == 0:
            self.addlog("Please create or load a layer structure first.", self.warningcolor2)
            return

        self.getlayerstructure()

        self.wavenumbers_cut = []
        self.trans_cut = []

        addon = 0
        if self.wavenumbers == [] and self.transmissions == []:
            while addon < 5500:
                self.wavenumbers_cut.append(500 + addon)
                self.trans_cut.append(0)
                addon += 10
        for i in range(0, len(self.wavenumbers)):
            if float(self.entry_32.text()) > float(self.wavenumbers[i]) > float(self.entry_31.text()):
                self.wavenumbers_cut.append(float(self.wavenumbers[i]))
                self.trans_cut.append(float(self.transmissions[i]))

        self.try_remove_fitline(self.fitline_trans)
        self.try_remove_fitline(self.fitline_reflect)
        self.try_remove_fitline(self.fitline_absorb)

        self.addprogressbar()
        self.trackwavenumber()
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.recurring_timer)
        self.timer.start()

        if self.use_ideal_k == 0:
            self.fittype = 2
        else:
            self.fittype = 8

        # Pass the function to execute
        worker = Worker(self.execute_show_fringes)  # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.process_queue_show_fringes)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress)
        worker.signals.wn.connect(self.progress_wn)

        # Execute
        self.threadpool.start(worker)

    def execute_show_fringes(self, progress_callback, wn_callback):
        fitobject = FIT_FTIR(self, self.Temp, self.wavenumbers_cut, self.trans_cut, float(self.entry_d_0.text()),
                                  self.layertype_list, self.entry_x_list, self.entry_d_list, self.checklayer_list,
                                  float(self.entry_21.text()), self.angle, float(self.entry_23.text()),
                                  float(self.entry_24.text()), self.subtype, self.fittype, self.blindcal,
                             progress_callback, wn_callback)

        if self.abortmission == 1:
            return "ABORT"
        peakvalues_fit = fitobject.returnpeakvalues()
        reflections_fit = fitobject.returnreflections()
        absorptions_fit = fitobject.returnabsorptions()

        result = [peakvalues_fit, reflections_fit, absorptions_fit]
        return result

    def process_queue_show_fringes(self, result):

        """Receive result for self.show_fringes()."""

        if result == "ABORT":
            self.addlog("Mission aborted.", self.warningcolor2)
            return

        self.peakvalues_fit = result[0]
        self.reflections_fit = result[1]
        self.absorptions_fit = result[2]

        if self.displayreflection == 0:
            self.fitline_trans = self.plot_and_show(self.FTIRplot, self.fitline_trans, 0, self.wavenumbers_cut,
                                                    self.peakvalues_fit, 'r', '', 'Transmission (%)', 0,
                                                    'upper right')
        else:
            self.fitline_trans = self.plot_and_show(self.FTIRplot, self.fitline_trans, 0, self.wavenumbers_cut,
                                                    self.peakvalues_fit, 'g', '', 'Transmission (%)', 0,
                                                    'upper right')

        if self.displayreflection == 1 and self.displayabsorption == 0:
            self.fitline_reflect = self.plot_and_show(self.FTIRplot, self.fitline_reflect, 0, self.wavenumbers_cut,
                                                      self.reflections_fit, 'r', '', 'Transmission/Reflection (%)',
                                                      0, 'upper right')
            self.addlog('Showing calculated transmission/reflection curve at {}K! '
                        'Total time: {:.1f}s.'.format(self.Temp, self.totaltime))

        elif self.displayreflection == 0 and self.displayabsorption == 1:
            self.fitline_absorb = self.plot_and_show(self.FTIRplot, self.fitline_absorb, 0, self.wavenumbers_cut,
                                                     self.absorptions_fit, 'purple', '',
                                                     'Transmission/Absorption (%)', 0, 'upper right')
            self.addlog('Showing calculated transmission/absorption curve at {}K! '
                        'Total time: {:.1f}s.'.format(self.Temp, self.totaltime))

        elif self.displayreflection == 1 and self.displayabsorption == 1:
            self.fitline_reflect = self.plot_and_show(self.FTIRplot, self.fitline_reflect, 0, self.wavenumbers_cut,
                                                      self.reflections_fit, 'r', '', 'Transmission/Reflection (%)',
                                                      0, 'upper right')
            self.fitline_absorb = self.plot_and_show(self.FTIRplot, self.fitline_absorb, 0, self.wavenumbers_cut,
                                                     self.absorptions_fit, 'purple', '',
                                                     'Transmission/Reflection/Absorption (%)', 0, 'upper right')
            self.addlog('Showing calculated transmission/reflection/absorption curve at {}K! '
                        'Total time: {:.1f}s.'.format(self.Temp, self.totaltime))
        else:
            self.addlog('Showing calculated transmission curve at {}K! '
                        'Total time: {:.1f}s.'.format(self.Temp, self.totaltime))

    def fit_fringes(self):

        """Find the best CdTe/HgTe offsets to fit the fringes. """

        if self.programbusy == 1:
            self.addlog("Another mission is in process.", self.warningcolor2)
            return

        if self.layernumber == 0:
            self.addlog("Please create or load a layer structure first.", self.warningcolor2)
            return

        self.getlayerstructure()

        self.wavenumbers_cut = []
        self.trans_cut = []

        if float(self.entry_32.text()) > 5000:
            self.addlog('Please choose the cut range of fringes.', self.warningcolor2)
            return

        for i in range(0, len(self.wavenumbers)):
            if float(self.entry_32.text()) > float(self.wavenumbers[i]) > float(self.entry_31.text()):
                self.wavenumbers_cut.append(float(self.wavenumbers[i]))
                self.trans_cut.append(float(self.transmissions[i]))

        if self.intial_thicknesses_or_not == 1:
            self.entry_d_list_initial = []

            for i in range(1, self.layernumber + 1):
                self.entry_d_list_initial.append(float(getattr(self, "entry_d_{}".format(i)).text()))
            self.intial_thicknesses_or_not = 0

        self.try_remove_fitline(self.fitline_trans)

        self.addlog('-' * 160, "blue")
        self.addlog("Fitting fringes in process. Please wait...")

        self.addprogressbar()
        self.trackwavenumber()
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.recurring_timer)
        self.timer.start()

        if self.use_ideal_k == 0:
            self.fittype = 2
        else:
            self.fittype = 8

        # Pass the function to execute
        worker = Worker(self.execute_fit_fringes)  # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.process_queue_fit_fringes)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress)
        worker.signals.wn.connect(self.progress_wn)

        # Execute
        self.threadpool.start(worker)

    def execute_fit_fringes(self, progress_callback, wn_callback):
        self.status2.setText(self.text2)
        CdTe_fitrange = 10
        HgTe_fitrange = 5
        self.inital_CdTe = float(self.entry_23.text())
        self.inital_HgTe = float(self.entry_24.text())
        for CdTe_offset in np.arange(self.inital_CdTe - CdTe_fitrange, self.inital_CdTe + CdTe_fitrange, 1):
            for HgTe_offset in np.arange(self.inital_HgTe - HgTe_fitrange, self.inital_HgTe + HgTe_fitrange, 1):
                percentage = (CdTe_offset - self.inital_CdTe + CdTe_fitrange) / CdTe_fitrange / 2 * 100 \
                             + (HgTe_offset - self.inital_HgTe + HgTe_fitrange) / HgTe_fitrange / 2 / CdTe_fitrange \
                             / 2 * 100
                progress_callback.emit(percentage)
                for i in range(0, self.layernumber):
                    if int(self.checklayer_list[i]) == 1:
                        if self.layertype_list[i] == "CdTe":
                            new_d = float(self.entry_d_list_initial[i]) * (1 + 0.01 * CdTe_offset)
                            self.entry_d_list[i] = new_d
                        elif self.layertype_list[i] == "MCT" or self.layertype_list[i] == "SL":
                            new_d = float(self.entry_d_list_initial[i]) * float(self.entry_x_list[i]) * (
                                    1 + 0.01 * CdTe_offset) \
                                    + float(self.entry_d_list_initial[i]) * (1 - float(self.entry_x_list[i])) * (
                                            1 + 0.01 * HgTe_offset)
                            self.entry_d_list[i] = new_d

                fitobject = FIT_FTIR(self, self.Temp, self.wavenumbers_cut, self.trans_cut,
                                     float(self.entry_d_0.text()),
                                     self.layertype_list, self.entry_x_list, self.entry_d_list, self.checklayer_list,
                                     float(self.entry_21.text()), self.angle, float(self.entry_23.text()),
                                     float(self.entry_24.text()), self.subtype, 1, self.blindcal)

                if self.abortmission == 1:
                    try:
                        self.fitline2.pop(0).remove()
                    except (AttributeError, IndexError) as error:
                        pass
                    return "ABORT"

                self.peakvalues_fit = fitobject.returnpeakvalues()

                self.MSE = 0

                for i in range(0, len(self.trans_cut)):
                    self.MSE += (self.peakvalues_fit[i] - self.trans_cut[i]) * \
                                (self.peakvalues_fit[i] - self.trans_cut[i]) / len(self.trans_cut)

                if self.MSE <= self.smallest_MSE:
                    self.smallest_MSE = self.MSE
                    self.best_CdTe_offset = CdTe_offset
                    self.best_HgTe_offset = HgTe_offset

                    if self.blindcal == 0:
                        try:
                            self.fitline2.pop(0).remove()
                        except (AttributeError, IndexError) as error:
                            pass
                        self.fitline2 = self.FTIRplot.plot(self.wavenumbers_cut, self.peakvalues_fit, 'r')
                        self.mplplot.draw()

        result = [self.best_CdTe_offset, self.best_HgTe_offset, self.smallest_MSE]

        return result

    def process_queue_fit_fringes(self, result):

        """Receive result for self.fit_fringes()."""

        if result == "ABORT":
            self.addlog("Mission aborted.", self.warningcolor2)
            return

        # Show result of the task if needed
        self.entry_23.setText('{0:.2f}'.format(result[0]))
        self.entry_24.setText('{0:.2f}'.format(result[1]))

        self.setoffsets()
        self.getlayerstructure()

        fitobject = FIT_FTIR(self, self.Temp, self.wavenumbers_cut, self.trans_cut, float(self.entry_d_0.text()),
                             self.layertype_list, self.entry_x_list, self.entry_d_list, self.checklayer_list,
                             float(self.entry_21.text()), self.angle, float(self.entry_23.text()),
                             float(self.entry_24.text()), self.subtype, 2, self.blindcal)

        self.peakvalues_fit = fitobject.returnpeakvalues()

        self.try_remove_fitline(self.fitline_trans)
        self.fitline_trans = self.plot_and_show(self.FTIRplot, self.fitline_trans, 0, self.wavenumbers_cut,
                                                self.peakvalues_fit, 'r', '', 'Transmission (%)', 0, 'upper right')

        self.addlog('Fitting fringes complete. Total time: {:.1f}s. MSE={}'.format(self.totaltime, result[2]))

    def cal_absorption(self):

        """Calculate the absorption coefficient as a function of wavenumebrs. """

        if self.programbusy == 1:
            self.addlog("Another mission is in process.", self.warningcolor2)
            return

        if self.layernumber == 0:
            self.addlog("Please create or load a layer structure first.", self.warningcolor2)
            return

        self.getlayerstructure()

        checktotal = 0
        ablayer = ""
        ab_x = ""
        for i in range(0, len(self.checklayer_list)):
            if checktotal == 0 and self.checklayer_list[i] == 1:
                ablayer = self.layertype_list[i]
                ab_x = self.entry_x_list[i]
            if self.checklayer_list[i] == 1:
                if self.layertype_list[i] != ablayer or self.entry_x_list[i] != ab_x:
                    self.addlog("The absorption layers need to have the same layer type and composition.",
                                self.warningcolor1)
                    return
            checktotal += self.checklayer_list[i]
        if checktotal == 0:
            self.addlog("Please choose which layer is the absorption layer.", self.warningcolor1)
            return

        self.wavenumbers_cut1 = []
        self.trans_cut1 = []

        for i in range(0, len(self.wavenumbers)):
            if float(self.entry_32.text()) >= float(self.wavenumbers[i]) >= float(self.entry_31.text()):
                self.wavenumbers_cut1.append(float(self.wavenumbers[i]))
                if self.transmissions[i] >= 0:
                    self.trans_cut1.append(float(self.transmissions[i]))
                else:
                    self.trans_cut1.append(0)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Do a rough calculation?")
        msg.setWindowTitle("Rough calculation")
        msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        result = msg.exec_()
        if result == QMessageBox.Ok:
            wavenumbers_cut_rough = []
            trans_cut_rough = []
            skipnumber = int(len(self.wavenumbers) / 200)
            index1 = 0
            while index1 in range(0, len(self.wavenumbers_cut1)):
                wavenumbers_cut_rough.append(self.wavenumbers_cut1[index1])
                trans_cut_rough.append(self.trans_cut1[index1])
                index1 += skipnumber
            self.wavenumbers_cut1 = wavenumbers_cut_rough
            self.trans_cut1 = trans_cut_rough
        else:
            pass

        self.addlog('-' * 160, "blue")
        if self.cal_k_instead == 1:
            self.addlog("k calculation in process. Please wait...")
        else:
            self.addlog("Absorption calculation in process. Please wait...")

        self.addprogressbar()
        self.trackwavenumber()
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.recurring_timer)
        self.timer.start()

        if int(self.data_loaded) == 0:
            if self.cal_k_instead == 0:
                self.fittype = 0
            else:
                self.fittype = 7
        else:
            if self.cal_k_instead == 0:
                self.fittype = int(self.data_loaded) + 2
            else:
                self.fittype = int(self.data_loaded) + 4

        if self.cal_k_instead == 1:
            self.y2_cut = 0.6
            self.entry_y2.setText(float(self.y2_cut))
            self.absorptionplot.set_ylim([0, self.y2_cut])
            self.absorptionplot.set_ylabel('k')

        # Pass the function to execute
        worker = Worker(self.execute_absorption)  # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.process_queue_absorption)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress)
        worker.signals.wn.connect(self.progress_wn)

        # Execute
        self.threadpool.start(worker)

    def execute_absorption(self, progress_callback, wn_callback):
        fitobject = FIT_FTIR(self, self.Temp, self.wavenumbers_cut1, self.trans_cut1, float(self.entry_d_0.text()),
                                  self.layertype_list, self.entry_x_list, self.entry_d_list, self.checklayer_list,
                                  float(self.entry_21.text()), self.angle, float(self.entry_23.text()),
                                  float(self.entry_24.text()), self.subtype, self.fittype, self.blindcal,
                             progress_callback, wn_callback)
        if self.abortmission == 1:
            return "ABORT"

        result = fitobject.cal_absorption()

        return result

    def process_queue_absorption(self, result):

        """receive result for self.cal_absorption()."""

        self.absorptions = result

        if result == "ABORT":
            self.addlog("Mission aborted.", self.warningcolor2)
            return

        self.try_remove_fitline(self.fitline_trans)
        self.try_remove_fitline(self.fitline_absorb)
        if self.cal_k_instead == 1:
            self.fitline_absorb = self.plot_and_show(self.absorptionplot, self.fitline_absorb, 0,
                                                     self.wavenumbers_cut1, self.absorptions,
                                                     self.colororders2[self.numberofdata2],
                                                     'Calculated k', 'k',
                                                     1, 'upper right')
        else:
            self.fitline_absorb = self.plot_and_show(self.absorptionplot, self.fitline_absorb, 0,
                                                     self.wavenumbers_cut1, self.absorptions,
                                                     self.colororders2[self.numberofdata2],
                                                     'Calculated Absorption', 'Absorption Coefficient ($cm^{-1}$)',
                                                     1, 'best')

        self.numberofdata2 += 1

        if self.cal_k_instead == 1:
            self.addlog('k calculation complete! Total time: {:.1f}s.'.format(self.totaltime))
        else:
            self.addlog('Absorption calculation complete! Total time: {:.1f}s.'.format(self.totaltime))

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Save the result as a .csv file?")
        msg.setWindowTitle("Save result")
        msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        result = msg.exec_()
        if result == QMessageBox.Ok:
            dlg = QFileDialog()
            dlg.setFileMode(QFileDialog.AnyFile)
            saveascsv = dlg.getSaveFileName(self, 'Save file', self.osdir, "CSV files (*.CSV *.csv)")

            if saveascsv[0] == "":
                return
            f = open(saveascsv[0], "w")

            for i in range(0, len(self.wavenumbers_cut1)):
                f.write("{0:.6e},{1:.6e}\n".format(self.wavenumbers_cut1[i], self.absorptions[i]))

            f.close()

            self.addlog('Saved the file to: {}'.format(saveascsv[0]))
        else:
            pass

    def onpick(self, event):

        """Define the behaviors when the mouse click on the graph. """

        self.xclick = event.xdata
        self.yclick = event.ydata
        self.vline.set_xdata(self.xclick)
        self.positiony = self.yclick / self.y2_cut * (self.transcut - self.transcutlow) + self.transcutlow
        self.hline.set_ydata(self.positiony)
        try:
            self.dot.pop(0).remove()
        except IndexError:
            if self.xclick is not None and self.yclick is not None:
                self.dot = self.FTIRplot.plot(self.xclick, self.positiony, marker='x', color='r')
            return
        if self.xclick is not None and self.yclick is not None:
            self.dot = self.FTIRplot.plot(self.xclick, self.positiony, marker='x', color='r')

        self.mplplot.draw()

        def find_x():  # Find x knowing cutoff energy E
            self.composition = 0
            Delta = 100
            while Delta > 0.0001:
                Delta = self.energy - (
                        (-.302 + 1.93 * self.composition +
                         5.35 * .0001 * self.Temp * (1 - 2 * self.composition) -
                         .81 * self.composition * self.composition +
                         .832 * self.composition * self.composition * self.composition) * 1000)
                self.composition += 0.00001

        if self.xclick is not None and self.yclick is not None:
            self.wavenumber = self.xclick
            self.trans = self.positiony
            self.wavelength = 10000 / self.wavenumber
            self.energy = 4.13566743 * 3 * 100 / self.wavelength
            find_x()
        else:
            self.trans = 0
            self.wavenumber = 0
            self.wavelength = 0
            self.energy = 0
            self.composition = 0

        self.lb_wn2.setText('{0:.4f}'.format(self.wavenumber))
        self.lb_wl2.setText('{0:.4f}'.format(self.wavelength))
        self.lb_e2.setText('{0:.4f}'.format(self.energy))
        self.lb_comp2.setText('{0:.4f}'.format(self.composition))

        if self.layernumber == 0:
            return

        self.getlayerstructure()

        checktotal = 0
        ablayer = ""
        ab_x = ""
        for i in range(0, len(self.checklayer_list)):
            if checktotal == 0 and self.checklayer_list[i] == 1:
                ablayer = self.layertype_list[i]
                ab_x = self.entry_x_list[i]
            if self.checklayer_list[i] == 1:
                if self.layertype_list[i] != ablayer or self.entry_x_list[i] != ab_x:
                    self.addlog("The absorption layers need to have the same layer type and composition.")
                    return
            checktotal += self.checklayer_list[i]
        if checktotal == 0:
            return

        fitobject = FIT_FTIR(self, self.Temp, self.wavenumbers, self.transmissions, float(self.entry_d_0.text()),
                             self.layertype_list, self.entry_x_list, self.entry_d_list, self.checklayer_list,
                             float(self.entry_21.text()), self.angle, float(self.entry_23.text()),
                             float(self.entry_24.text()), self.subtype, 0, self.blindcal)

        try:
            self.addlog('Absorption Coefficient: {}cm-1'.format(fitobject.cal_absorption_single(self.xclick)))
        except IndexError:
            pass

    def Abort_mission(self):
        self.abortmission = 1

    def recurring_timer(self):
        self.totaltime += 0.1

    def progress(self, n):
        self.progressbar.setValue(n)

    def progress_wn(self, n):
        self.status2.setText('WaveNum = {:.1f}cm-1'.format(n))

    def thread_complete(self):
        self.abortmission = 0
        self.timer.stop()
        self.totaltime = 0
        self.removeprogressbar()
        self.removewavenumber()

    def addprogressbar(self):
        self.status1.hide()
        self.progressbar.show()
        self.buttonabort.show()
        self.programbusy = 1

    def removeprogressbar(self):
        self.progressbar.setValue(0)
        self.progressbar.hide()
        self.buttonabort.hide()
        self.status1.show()
        self.programbusy = 0

    def trackwavenumber(self):
        self.text2 = self.status2.text()
        self.status2.setText('WaveNum = {:.1f}cm-1'.format(self.wn_beingcalculated))

    def removewavenumber(self):
        self.status2.setText(self.text2)
        self.wn_beingcalculated = 0

    def clearalldata(self):

        """Clear everything. """

        if self.programbusy == 1:
            self.addlog("Calculation in progress. Abort the mission before clear all data. ", self.warningcolor2)
            return

        def clearornotfunc():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)

            msg.setText("Clear everything (including all layer structures, data, settings and graphs)?")
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)

            result = msg.exec_()
            if result == QMessageBox.Ok:
                return 1
            else:
                return 0

        if self.layernumber != 0:
            clearornot = clearornotfunc()
            if clearornot == 1:
                for i in reversed(range(self.maingrid.count())):
                    self.maingrid.itemAt(i).widget().setParent(None)
                #self.__init__(self.root, self.masterroot)
                obj = FTIR_fittingtool_GUI_v3(self.root, self.masterroot)
                self.root.setWidget(obj)
                self.root.showMaximized()
                self.root.show()
                self.addlog('-' * 160, "blue")
            else:
                pass

    def addlog(self, string, fg="default", bg="default"):
            item = QListWidgetItem(string)
            if fg is not "default":
                item.setForeground(QColor(fg))
            if bg is not "default":
                item.setBackground(QColor(bg))
            self.listbox.addItem(item)
            self.listbox.scrollToItem(item)
            self.listbox.show()
