# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
import sys
# import EITHER PyQt4 OR PySide, depending on your system:
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import SIGNAL, SLOT  
#from PySide.QtCore import *
#from PySide.QtGui import *

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

#import numpy as np
#import scipy.signal as sig

import plotHf

N_FFT = 2048 # FFT length for freqz
#

class plotAll(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        tab_widget = QtGui.QTabWidget()
        self.coeffs = ([1,1,1],[3,0,2])
        self.pltPhi = plotHf.plotHf()
        self.pltHf = plotHf.plotHf()
        tab_widget.addTab(self.pltHf, '|H(f)|')
        tab_widget.addTab(self.pltPhi, 'phi(f)')
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(tab_widget)
        
        self.setLayout(vbox)
        
    def update(self, coeffs):
        """ Update all subplots with new coefficients"""
        self.coeffs = coeffs
        self.pltHf.update(self.coeffs)
        self.pltPhi.update(self.coeffs)        

class createMPLCanvas(QtGui.QWidget):
    def __init__(self):
        super(createMPLCanvas, self).__init__() 
        parent = super(createMPLCanvas, self).__init__() 
        # Create the mpl Figure and FigCanvas objects. 
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.fig = Figure((5.0, 4.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(parent)
        
        self.axes = self.fig.add_subplot(111)
        
        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        
        # Other GUI controls: SIGNAL definitions and connections to SLOTS
        # 
       
#        self.butDraw = QtGui.QPushButton("&Draw")
#        self.connect(self.butDraw, SIGNAL('clicked()'), self.redraw)
#    
#        self.cboxGrid = QtGui.QCheckBox("Show &Grid")
#        self.cboxGrid.setChecked(True)  
#        self.connect(self.cboxGrid, SIGNAL('stateChanged(int)'), self.redraw)
#        # self.cb_grid.clicked.connect(self.redraw) 
#        # passes unwanted clicked bool argument, use following
#        self.cboxGrid.clicked.connect(lambda: self.redraw())
#        
#        lblLw = QtGui.QLabel('Line width:')
        self.sldLw = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.sldLw.setRange(1, 5)
        self.sldLw.setValue(2)
        self.sldLw.setTracking(True)
        self.sldLw.setTickPosition(QtGui.QSlider.NoTicks)
    #        self.connect(self.sldLw, SIGNAL('valueChanged(int)'), self.redraw)
        self.sldLw.valueChanged.connect(lambda: parent.redraw())
       
#        #=============================================
#        # Layout with box sizers
#        #=============================================
#          
#        hbox1 = QtGui.QHBoxLayout()            
#        for w in [self.butDraw, self.cboxGrid, lblLw, self.sldLw]:
#            hbox1.addWidget(w)
#            hbox1.setAlignment(w, QtCore.Qt.AlignVCenter)
            
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.sldLw)
#        vbox.addLayout(hbox1)         
        self.setLayout(vbox)
    

    
def main():
    app = QtGui.QApplication(sys.argv)
    form = plotAll()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
