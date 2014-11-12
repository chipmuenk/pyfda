# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
import sys
# import EITHER PyQt4 OR PySide, depending on your system
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import SIGNAL, SLOT  
#from PySide.QtCore import *
#from PySide.QtGui import *

import matplotlib as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import numpy as np
import scipy.signal as sig

import plotAll

N_FFT = 2048 # FFT length for freqz
       
        
class plotHf(QtGui.QWidget):

    def __init__(self, coeffs = ([1,1,1],[3,0,0])):        
        parent = super(plotHf, self).__init__() 
#    def __init__(self, parent=None):      
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle('Plot H(f)')
        print 'plotter_Hf.__init__()'
        self.A_SB = 60   # min. Sperrdämpfung im Stoppband in dB (= min. y-Wert des Plots)
#        plotAll.createMPLCanvas(parent)   
        self.myCanv = plotHf.createMPLCanvas(self)   
        self.update(coeffs)

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
        self.butDraw = QtGui.QPushButton("&Draw")
        self.connect(self.butDraw, SIGNAL('clicked()'), self.update)

        self.cboxGrid = QtGui.QCheckBox("Show &Grid")
        self.cboxGrid.setChecked(True)  
#        self.connect(self.cboxGrid, SIGNAL('stateChanged(int)'), self.redraw)
        # self.cb_grid.clicked.connect(self.redraw) 
        # passes unwanted clicked bool argument, use following
        self.cboxGrid.clicked.connect(lambda: self.redraw())
        
        lblLw = QtGui.QLabel('Line width:')
        self.sldLw = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.sldLw.setRange(1, 5)
        self.sldLw.setValue(2)
        self.sldLw.setTracking(True)
        self.sldLw.setTickPosition(QtGui.QSlider.NoTicks)
#        self.connect(self.sldLw, SIGNAL('valueChanged(int)'), self.redraw)
        self.sldLw.valueChanged.connect(lambda: self.redraw())       

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
            
    def update(self, coeffs = (1,1)):
        """ Re-calculates |H(f)| and updates the figure
        """
        print coeffs
        self.bb = coeffs[0]
        self.aa = coeffs[1]
        [W,H] = sig.freqz(self.bb, self.aa, N_FFT) # calculate H(W) for W = 0 ... pi
        print 'redraw.plotted!', self.bb
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
        plt.artist.setp(self.pltPlt, linewidth = self.sldLw.value())
        self.pltFig.tight_layout()
        self.pltCanv.draw()
  
    
def main():
    app = QtGui.QApplication(sys.argv)
    form = plotHf()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
