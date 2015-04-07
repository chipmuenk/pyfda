# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
# import EITHER PyQt4 OR PySide, depending on your system:
from PyQt4 import QtGui #, QtCore
#from PySide.QtCore import *
#from PySide.QtGui import *


#import numpy as np
#import scipy.signal as sig
if __name__ == "__main__": # relative import if this file is run as __main__
    cwd=os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

from plot_widgets import plot_hf, plot_phi, plot_pz, plot_tau_g, plot_impz


class PlotAll(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.pltHf = plot_hf.PlotHf()
        self.pltPhi = plot_phi.PlotPhi()
        self.pltPZ = plot_pz.PlotPZ()
        self.pltTauG = plot_tau_g.PlotTauG()
        self.pltImpz = plot_impz.PlotImpz()

        self.initUI()

    def initUI(self):
        """ Initialize UI with tabbed subplots """
        tabWidget = QtGui.QTabWidget()
        tabWidget.addTab(self.pltHf, '|H(f)|')
        tabWidget.addTab(self.pltPhi, 'phi(f)')
        tabWidget.addTab(self.pltPZ, 'P/Z')
        tabWidget.addTab(self.pltTauG, 'tau_g')
        tabWidget.addTab(self.pltImpz, 'h[n]')


#        butDraw = QtGui.QPushButton("&No Function")
#        butDraw.clicked.connect(self.redrawAll)

#        hbox = QtGui.QHBoxLayout()
#        hbox.addWidget(butDraw)
#        hbox.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        layVMain = QtGui.QVBoxLayout()
        layVMain.addWidget(tabWidget)
#
        self.setLayout(layVMain)


    def updateAll(self):
        """ Update and redraw all subplots with new filter data"""
        self.pltHf.draw()
        self.pltPhi.draw()
        self.pltPZ.draw()
        self.pltTauG.draw()
        self.pltImpz.draw()


#        self.redrawAll()

#    def redrawAll(self):
#        """ Redraw all subplots"""
#        self.pltHf.redraw()
#        self.pltPhi.redraw()

#------------------------------------------------------------------------

def main():
    app = QtGui.QApplication(sys.argv)
    form = PlotAll()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
