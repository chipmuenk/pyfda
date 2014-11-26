# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
import sys
# import EITHER PyQt4 OR PySide, depending on your system
from PyQt4 import QtGui, QtCore
#from PySide.QtCore import *
#from PySide.QtGui import *

import matplotlib as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import numpy as np
import scipy.signal as sig
import plotAll
#import _plotUtils

import plotAll

N_FFT = 2048 # FFT length for freqz
 
DEBUG = True      
        
class PlotHf(QtGui.QWidget):
#class plotHf(plotAll.plotAll):

    def __init__(self):        
        parent = super(PlotHf, self).__init__() 
        
        self.coeffs = ([1,1,1],[3,0,0]) # dummy definition for notch filter
        
#    def __init__(self, parent=None):      
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle('Plot H(f)')
        self.A_SB = 60   # min. Sperrdämpfung im Stoppband in dB (= min. y-Wert des Plots)
#        plotAll.createMPLCanvas(parent)   
        self.myCanv = PlotHf.createMPLCanvas(self)  
#        self.myCanv = _plotUtils.createMPLCanvas()           
        self.update(self.coeffs)

    def createMPLCanvas(self):
   
        # Create the mpl Figure and FigCanvas objects. 
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.pltFig = Figure((5.0, 4.0), dpi=self.dpi)
        self.pltCanv = FigureCanvas(self.pltFig)
        self.pltCanv.setParent(self)
        
        self.pltAxes = self.pltFig.add_subplot(111)
        
        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.pltCanv, self)
        
        # SIGNAL & SLOTS
        # 
        self.butDraw = QtGui.QPushButton("&Redraw")
        self.butDraw.clicked.connect(self.redraw)
        

        self.cboxGrid = QtGui.QCheckBox("&Grid")
        self.cboxGrid.setChecked(True)  
        # Attention: passes unwanted clicked bool argument:
        self.cboxGrid.clicked.connect(self.redraw)
        
        lblLw = QtGui.QLabel('Line width:')
        self.sldLw = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.sldLw.setRange(1, 10)
        self.sldLw.setValue(5)
        self.sldLw.setTracking(True)
        self.sldLw.setTickPosition(QtGui.QSlider.NoTicks)
        self.sldLw.valueChanged.connect(self.redraw)  

        #=============================================
        # Layout with box sizers
        #=============================================
          
        hbox1 = QtGui.QHBoxLayout()            
        for w in [self.butDraw, self.cboxGrid, lblLw, self.sldLw]:
            hbox1.addWidget(w)
            hbox1.setAlignment(w, QtCore.Qt.AlignVCenter)
            
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.pltCanv)
        vbox.addLayout(hbox1)         
        self.setLayout(vbox)
            
    def update(self, coeffs):
        """ 
        Re-calculate |H(f)| and update the figure
        """
        self.coeffs = coeffs
        self.bb = self.coeffs[0]
        self.aa = self.coeffs[1]
        [W,H] = sig.freqz(self.bb, self.aa, N_FFT) # calculate H(W) for W = 0 ... pi
        print 
        if DEBUG:
            print("-------------------------")
            print("plotHf.update() ") 
            print("-------------------------")
            print("b,a = ", self.bb, self.aa)
        F = W / (2 * np.pi)

        # clear the axes and redraw the plot
        #
        self.pltAxes.clear()        
        self.pltAxes.axis([0, 0.5, -self.A_SB-10, 2])

        self.pltPlt, = self.pltAxes.plot(F,20*np.log10(abs(H)),
                       lw = self.sldLw.value())
        self.pltAxes.set_xlabel(r'$F\; \rightarrow $')                       
        self.pltAxes.set_ylabel(r'$|H(\mathrm{e}^{\mathrm{j} \Omega})|\; \rightarrow $')
        self.pltAxes.set_title(r'Betragsfrequenzgang')
        self.redraw()
        
    def redraw(self):
        """
        Redraw the figure with new properties (grid, linewidth)
        """
        self.pltAxes.grid(self.cboxGrid.isChecked())
        plt.artist.setp(self.pltPlt, linewidth = self.sldLw.value()/5.)
        self.pltFig.tight_layout()
        self.pltCanv.draw()

#------------------------------------------------------------------------------  
    
def main():
    app = QtGui.QApplication(sys.argv)
    form = PlotHf()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
