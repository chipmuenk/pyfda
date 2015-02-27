# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui #, QtCore

#from PyQt4.QtGui import QSizePolicy
#from PyQt4.QtCore import QSize

#import matplotlib as plt
#from matplotlib.figure import Figure

import numpy as np
import scipy.signal as sig

if __name__ == "__main__": # relative import if this file is run as __main__
    cwd=os.path.dirname(os.path.abspath(__file__))
    sys.path.append(cwd + '/..')

import filterbroker as fb
import pyFDA_lib

from plot_utils import MplWidget#, MplCanvas

DEBUG = True

"""
QMainWindow is a class that understands GUI elements like a toolbar, statusbar,
central widget, docking areas. QWidget is just a raw widget.
When you want to have a main window for you project, use QMainWindow.

If you want to create a dialog box (modal dialog), use QWidget, or,
more preferably, QDialog
"""

class PlotTauG(QtGui.QMainWindow):

    def __init__(self, parent = None, DEBUG = False): # default parent = None -> top Window
        super(PlotTauG, self).__init__(parent) # initialize QWidget base class
#        QtGui.QMainWindow.__init__(self) # alternative syntax

        self.DEBUG = DEBUG

#        self.cmbUnitsPhi = QtGui.QComboBox(self)
#        units = ["rad", "rad/pi", "deg"]
#        scales = [1., 1./ np.pi, 180./np.pi]
#        for unit, scale in zip(units, scales):
#            self.cmbUnitsPhi.addItem(unit, scale)
#        self.cmbUnitsPhi.setObjectName("cmbUnitsA")
#        self.cmbUnitsPhi.setToolTip("Set unit for phase.")
#        self.cmbUnitsPhi.setCurrentIndex(0)
#
#        self.lblWrap = QtGui.QLabel("Wrapped Phase")
#        self.btnWrap = QtGui.QCheckBox()
#        self.btnWrap.setChecked(False)
#        self.btnWrap.setToolTip("Plot phase wrapped to +/- pi")
        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addStretch(10)
#        self.layHChkBoxes.addWidget(self.cmbUnitsPhi)
#        self.layHChkBoxes.addWidget(self.lblWrap)
#        self.layHChkBoxes.addWidget(self.btnWrap)
#        self.layHChkBoxes.addStretch(10)

        self.mplwidget = MplWidget()
#        self.mplwidget.setParent(self)

        self.mplwidget.layVMainMpl.addLayout(self.layHChkBoxes)

        self.mplwidget.setFocus()
        # make this the central widget, taking all available space:
        self.setCentralWidget(self.mplwidget)

        self.draw() # calculate and draw phi(f)

#        #=============================================
#        # Signals & Slots
#        #=============================================
#        self.btnWrap.clicked.connect(self.draw)
#        self.cmbUnitsPhi.currentIndexChanged.connect(self.draw)

    def draw(self):
        """
        Draw group delay
        """
        if np.ndim(fb.fil[0]['coeffs']) == 1: # FIR
            bb = fb.fil[0]['coeffs']
            aa = 1.
        else: # IIR
            bb = fb.fil[0]['coeffs'][0]
            aa = fb.fil[0]['coeffs'][1]

#        scale = self.cmbUnitsPhi.itemData(self.cmbUnitsPhi.currentIndex())

        # clear the axes and (re)draw the plot
        #
        mpl = self.mplwidget.ax
        mpl.clear()

        [tau_g, w] = pyFDA_lib.grpdelay(bb,aa, fb.gD['N_FFT'],
                        whole = fb.rcFDA['freqSpecsRangeType']!= 'Half')#, Fs = f_S)
        mpl.plot(w / (2 * np.pi), tau_g, lw = fb.gD['rc']['lw'])
        mpl.axis(fb.rcFDA['freqSpecsRange'] + [max(min(tau_g)-0.5,0), max(tau_g) + 0.5])

#        if PLT_AUTOx: dsp.format_ticks('x',f_scale, N_F_str)

        mpl.set_title(r'Group Delay $ \tau_g$')
        mpl.set_xlabel(fb.fil[0]['plt_fLabel'])
        mpl.set_ylabel(r'$ \tau_g(\mathrm{e}^{\mathrm{j} \Omega}) / T_S \; \rightarrow $')
        mpl.axis(fb.rcFDA['freqSpecsRange'] + [max(min(tau_g)-0.5,0), max(tau_g) + 0.5])


        self.mplwidget.redraw()

#------------------------------------------------------------------------------

def main():
    app = QtGui.QApplication(sys.argv)
    form = PlotTauG()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
