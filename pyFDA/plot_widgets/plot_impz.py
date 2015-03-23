# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os

from PyQt4 import QtGui
#from PyQt4.QtGui import QSizePolicy
#from PyQt4.QtCore import QSize

#import matplotlib as plt
#from matplotlib.figure import Figure

import numpy as np
import scipy.signal as sig
# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb
import pyfda_lib as pylib


from plot_widgets.plot_utils import MplWidget#, MyMplToolbar, MplCanvas


"""
QMainWindow is a class that understands GUI elements like a toolbar, statusbar,
central widget, docking areas. QWidget is just a raw widget.
When you want to have a main window for you project, use QMainWindow.

If you want to create a dialog box (modal dialog), use QWidget, or,
more preferably, QDialog
"""

class PlotImpz(QtGui.QMainWindow):

    def __init__(self, parent = None, DEBUG = False): # default parent = None -> top Window
        super(PlotImpz, self).__init__(parent) # initialize QWidget base class
#        QtGui.QMainWindow.__init__(self) # alternative syntax

        self.DEBUG = DEBUG

        modes = ["lin", "log"]
        self.cmbShowH = QtGui.QComboBox(self)
        self.cmbShowH.addItems(modes)
        self.cmbShowH.setObjectName("cmbUnitsH")
        self.cmbShowH.setToolTip("Show lin. or log. impulse response.")
        self.cmbShowH.setCurrentIndex(0)

#        self.lblIn = QtGui.QLabel("in")
#
#        units = ["dB", "V", "W"]
#        self.cmbUnitsA = QtGui.QComboBox(self)
#        self.cmbUnitsA.addItems(units)
#        self.cmbUnitsA.setObjectName("cmbUnitsA")
#        self.cmbUnitsA.setToolTip("Set unit for y-axis:\n"
#        "dB is attenuation (positive values)\nV and W are less than 1.")
#        self.cmbUnitsA.setCurrentIndex(0)
        

        self.lblStep = QtGui.QLabel("Step Response")
        self.chkStep = QtGui.QCheckBox()
        self.chkStep.setChecked(False)
        self.chkStep.setToolTip("Show step response instead of impulse response.")
        
        self.lblLockZoom = QtGui.QLabel("Lock Zoom")
        self.chkLockZoom = QtGui.QCheckBox()
        self.chkLockZoom.setChecked(False)
        self.chkLockZoom.setToolTip("Lock zoom to current setting.")


        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addStretch(10)
        self.layHChkBoxes.addWidget(self.cmbShowH)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.lblStep)
        self.layHChkBoxes.addWidget(self.chkStep)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.lblLockZoom)
        self.layHChkBoxes.addWidget(self.chkLockZoom)
#        self.layHChkBoxes.addStretch(1)
#        self.layHChkBoxes.addWidget(self.lblPhase)
#        self.layHChkBoxes.addWidget(self.chkPhase)
        self.layHChkBoxes.addStretch(10)

        self.mplwidget = MplWidget()
#        self.mplwidget.setParent(self)

        self.mplwidget.layVMainMpl.addLayout(self.layHChkBoxes)
#        self.mplwidget.layVMainMpl1.addWidget(self.mplwidget)

        self.mplwidget.setFocus()
        # make this the central widget, taking all available space:
        self.setCentralWidget(self.mplwidget)

#        self.setLayout(self.layHChkBoxes)

        self.draw() # calculate and draw |H(f)|

#        #=============================================
#        # Signals & Slots
#        #=============================================
#        self.cmbUnitsA.currentIndexChanged.connect(self.draw)
        self.cmbShowH.currentIndexChanged.connect(self.draw)

        self.chkStep.clicked.connect(self.draw)



    def draw(self):
        """
        Re-calculate |H(f)| and draw the figure
        """
        modeH = self.cmbShowH.currentText()
        step = self.chkStep.isChecked()
               
#        if np.ndim(fb.fil[0]['coeffs']) == 1: # FIR

        self.bb = fb.fil[0]['coeffs'][0]
        self.aa = fb.fil[0]['coeffs'][1]

        self.f_S  = fb.fil[0]['f_S']
        self.F_PB = fb.fil[0]['F_PB'] * self.f_S
        self.F_SB = fb.fil[0]['F_SB'] * self.f_S

        self.A_PB  = fb.fil[0]['A_PB']
        self.A_PB2 = fb.fil[0]['A_PB2']
        self.A_SB  = fb.fil[0]['A_SB']
        self.A_SB2 = fb.fil[0]['A_SB2']

        if self.DEBUG:
            print("--- plotHf.draw() --- ")
            print("b, a = ", self.bb, self.aa)

        # calculate |H(W)| for W = 0 ... pi:
        [h,t] = pylib.impz(self.bb, self.aa, self.f_S, step = step)
            
        if step:
            title_str = r'Step Response'
            H_str = r'$h_{\epsilon}[n]$'
        else:
            title_str = r'Impulse Response'
            H_str = r'$h[n]$'
        bottom = 0
            
#        if self.cmbShowH.currentIndex() > 0: # log. response
        if self.cmbShowH.currentText() == 'log':
            H_str = r'$\log$ ' + H_str + ' in dB'
            h = np.maximum(20 * np.log10(abs(h)), -80)
            bottom = -80

        if self.mplwidget.plt_lim == [] or not self.chkLockZoom.isChecked():
            print(self.mplwidget.plt_lim)
            print(self.chkLockZoom.isChecked())            
            t_lim = [min(t), max(t)]
            y_lim = [min(h), max(h)]
            self.mplwidget.plt_lim = t_lim + y_lim
        
        # clear the axes and (re)draw the plot
        #
        fig = self.mplwidget.fig
        ax = fig.add_subplot(111)
        ax.clear()

        #================ Main Plotting Routine =========================
        [ml, sl, bl] = ax.stem(t, h, bottom = bottom)
        

#        fig.setp(ml, 'markerfacecolor', 'r', 'markersize', 8)
 #       ax.setp(sl, lw = fb.gD['rc']['lw'])
        print(self.mplwidget.plt_lim)
        ax.axis(self.mplwidget.plt_lim)


        ax.set_title(title_str)
        ax.set_xlabel(fb.fil[0]['plt_tLabel'])
        ax.set_ylabel(H_str + r'$\rightarrow $')


        self.mplwidget.redraw()

#------------------------------------------------------------------------------

def main():
    app = QtGui.QApplication(sys.argv)
    form = PlotImpz()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
