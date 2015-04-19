# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
from PyQt4 import QtGui #, QtCore

#from PyQt4.QtGui import QSizePolicy
#from PyQt4.QtCore import QSize

#import matplotlib as plt
#from matplotlib.figure import Figure

import numpy as np
import scipy.signal as sig

if __name__ == "__main__": # relative import if this file is run as __main__
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import filterbroker as fb

from plot_widgets.plot_utils import MplWidget#, MplCanvas

"""
QMainWindow is a class that understands GUI elements like a toolbar, statusbar,
central widget, docking areas. QWidget is just a raw widget.
When you want to have a main window for you project, use QMainWindow.

If you want to create a dialog box (modal dialog), use QWidget, or,
more preferably, QDialog
"""

class PlotPhi(QtGui.QMainWindow):

    def __init__(self, parent = None, DEBUG = False): # default parent = None -> top Window
        super(PlotPhi, self).__init__(parent) # initialize QWidget base class

        self.DEBUG = DEBUG

        self.cmbUnitsPhi = QtGui.QComboBox(self)
        units = ["rad", "rad/pi",  "deg"]
        scales = [1.,   1./ np.pi, 180./np.pi]
        for unit, scale in zip(units, scales):
            self.cmbUnitsPhi.addItem(unit, scale)
        self.cmbUnitsPhi.setObjectName("cmbUnitsA")
        self.cmbUnitsPhi.setToolTip("Set unit for phase.")
        self.cmbUnitsPhi.setCurrentIndex(0)
        
        """EDIT WinMic"""
        self.cmbUnitsPhi.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        """END"""

        self.lblWrap = QtGui.QLabel("Wrapped Phase")
        self.btnWrap = QtGui.QCheckBox()
        self.btnWrap.setChecked(False)
        self.btnWrap.setToolTip("Plot phase wrapped to +/- pi")
        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addStretch(10)
        self.layHChkBoxes.addWidget(self.cmbUnitsPhi)
        self.layHChkBoxes.addWidget(self.lblWrap)
        self.layHChkBoxes.addWidget(self.btnWrap)
        self.layHChkBoxes.addStretch(10)

        self.mplwidget = MplWidget()
#        self.mplwidget.setParent(self)

        self.mplwidget.layVMainMpl.addLayout(self.layHChkBoxes)

#        self.mplwidget.setFocus()
        # make this the central widget, taking all available space:
        self.setCentralWidget(self.mplwidget)
        
        self.initAxes()

        self.draw() # calculate and draw phi(f)

#        #=============================================
#        # Signals & Slots
#        #=============================================
#        self.mplwidget.sldLw.valueChanged.connect(lambda:self.draw())
        self.btnWrap.clicked.connect(self.draw)
        self.cmbUnitsPhi.currentIndexChanged.connect(self.draw)
        
    def initAxes(self):
        """Initialize and clear the axes
        """
#        self.ax = self.mplwidget.ax
        self.ax = self.mplwidget.fig.add_subplot(111)
        self.ax.clear()
        self.ax.hold(False)
        
    def draw(self):
        if self.mplwidget.mplToolbar.enable_update:
            self.draw_phi()

    def draw_phi(self):
        """
        Re-calculate phi(f) and draw the figure
        """

        self.unitPhi = self.cmbUnitsPhi.currentText()

        if np.ndim(fb.fil[0]['coeffs']) == 1: # FIR
            self.bb = fb.fil[0]['coeffs']
            self.aa = 1.
        else: # IIR
            self.bb = fb.fil[0]['coeffs'][0]
            self.aa = fb.fil[0]['coeffs'][1]

        if self.DEBUG:
            print("--- plotPhi.draw() ---")
            print("b,a = ", self.bb, self.aa)

        wholeF = fb.rcFDA['freqSpecsRangeType'] != 'half'
        f_S = fb.fil[0]['f_S']

        [W,H] = sig.freqz(self.bb, self.aa, worN = fb.gD['N_FFT'],
                        whole = wholeF)

        F = W / (2 * np.pi) * f_S

        if fb.rcFDA['freqSpecsRangeType'] == 'sym':
            H = np.fft.fftshift(H)
            F = F - f_S / 2.

#        scale = self.cmbUnitsPhi.itemData(self.cmbUnitsPhi.currentIndex())
        y_str = r'$\angle H(\mathrm{e}^{\mathrm{j} \Omega})$'
        if self.unitPhi == 'rad':
            y_str += ' in rad ' + r'$\rightarrow $'
            scale = 1.
        elif self.unitPhi == 'rad/pi':
            y_str += ' in rad' + r'$ / \pi \;\rightarrow $'
            scale = 1./ np.pi
        else:
            y_str += ' in deg ' + r'$\rightarrow $'
            scale = 180./np.pi
        fb.rcFDA['plt_phiLabel'] = y_str
        fb.rcFDA['plt_phiUnit'] = self.unitPhi

        if self.btnWrap.isChecked():
            phi_plt = np.angle(H) * scale
        else:
            phi_plt = np.unwrap(np.angle(H)) * scale

        self.ax.clear()
        #---------------------------------------------------------
        line_phi, = self.ax.plot(F, phi_plt, lw = fb.gD['rc']['lw'])
        #---------------------------------------------------------

        self.ax.set_title(r'Phase Frequency Response')
        self.ax.set_xlabel(fb.rcFDA['plt_fLabel'])
        self.ax.set_ylabel(y_str)
        self.ax.set_xlim(fb.rcFDA['freqSpecsRange'])

        self.mplwidget.redraw()

#------------------------------------------------------------------------------

def main():
    app = QtGui.QApplication(sys.argv)
    form = PlotPhi()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
