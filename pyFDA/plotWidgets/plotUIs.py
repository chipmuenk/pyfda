# -*- coding: utf-8 -*-
"""
Construct Tabbed Widget with different Plots

Edited by Christian Münker, 2014
"""
import sys
# import EITHER PyQt4 OR PySide, depending on your system:
from PyQt4 import QtGui, QtCore  
#from PySide.QtCore import *
#from PySide.QtGui import *

#import matplotlib
#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
#from matplotlib.figure import Figure

#import numpy as np
#import scipy.signal as sig

import plotHf


class PlotUIs(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.coeffs = ([1,1,1],[3,0,2])
        self.N_FFT = 2048 # FFT length for freqz
        
        self.pltPhi = plotHf.PlotHf()
        self.pltHf = plotHf.PlotHf()
        
        self.initUI()
        
    def initUI(self):
        """ Initialize UI with tabbed subplots """
        tab_widget = QtGui.QTabWidget()
        tab_widget.addTab(self.pltHf, '|H(f)|')
        tab_widget.addTab(self.pltPhi, 'phi(f)')
        
        butDraw = QtGui.QPushButton("&Redraw All")
        butDraw.clicked.connect(self.redrawAll)
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(butDraw)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(tab_widget)
        vbox.addLayout(hbox)
        
        self.setLayout(vbox)
        
    def update(self, coeffs):
        """ Update and redraw all subplots with new coefficients"""
        self.coeffs = coeffs
        self.pltHf.update(self.coeffs)
        self.pltPhi.update(self.coeffs)
        self.redrawAll()

    def redrawAll(self):
        """ Redraw all subplots"""
        self.pltHf.redraw()
        self.pltPhi.redraw()             

#------------------------------------------------------------------------
    
def main():
    app = QtGui.QApplication(sys.argv)
    form = PlotUIs()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
