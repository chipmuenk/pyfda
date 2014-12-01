# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
import sys
# import EITHER PyQt4 OR PySide, depending on your system
from PyQt4 import QtGui, QtCore
#from PySide.QtCore import *
#from PySide.QtGui import *

#import matplotlib as plt
#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
#from matplotlib.figure import Figure

import numpy as np
import scipy.signal as sig
from plotUtils import MplCanvas, MplWidget, MplWidget2


N_FFT = 2048 # FFT length for freqz
 
DEBUG = True      
        
class PlotHf(QtGui.QMainWindow):

    def __init__(self):        
        super(PlotHf, self).__init__() # initialize QWidget base class
#        QtGui.QMainWindow.__init__(self) # create main window from base class
        
        self.coeffs = ([1,1,1],[3,0,0]) # dummy definition for notch filter
        self.A_SB = 60   # min. Sperrdämpfung im Stoppband in dB (= min. y-Wert des Plots)
      
        self.mplwidget = MplCanvas()
#       self.mplwidget = MplWidget2()
        
        self.mplwidget.setFocus()
        self.setCentralWidget(self.mplwidget)
        
      
        
        self.update(self.coeffs)
#        self.plot(self.mplwidget.axes)

#        plotAll.createMPLCanvas(parent)   


#        self.setLayout(plotUtils.CreateMPLCanvas().vbox) 
##       self.pltCanv.setParent(self)
##        self.pltCanv.setParent(plotUtils.CreateMPLCanvas())
##        self.pltCanv = FigureCanvas(self.pltFig)



        
#        self.setLayout(self.myCanv.vbox)

#        #=============================================
#        # Signals & Slots
#        #=============================================          
#        self.butDraw.clicked.connect(lambda: self.update(self.coeffs))
#        self.cboxGrid.clicked.connect(self.redraw)
#        self.sldLw.valueChanged.connect(self.redraw)  
            
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
        mpl = self.mplwidget.ax
        mpl.clear()
        mpl.plot(F,20*np.log10(abs(H)) )#, lw = self.sldLw.value())
        mpl.axis([0, 0.5, -self.A_SB-10, 2])
        mpl.set_title(r'Betragsfrequenzgang')
        mpl.set_xlabel(r'$F\; \rightarrow $')    
        mpl.set_ylabel(r'$|H(\mathrm{e}^{\mathrm{j} \Omega})|\; \rightarrow $')    
 
        self.mplwidget.figure.tight_layout()  
        self.mplwidget.redrawPlt()
        
    def redraw(self):
        """
        Redraw the figure with new properties (grid, linewidth)
        """
#        self.mplwidget.axes.grid(self.cboxGrid.isChecked())
#        plt.artist.setp(self.pltPlt, linewidth = self.sldLw.value()/5.)
        self.mplwidget.figure.tight_layout()
        self.mplwidget.redrawPlt()

#------------------------------------------------------------------------------  
    
def main():
    app = QtGui.QApplication(sys.argv)
    form = PlotHf()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
