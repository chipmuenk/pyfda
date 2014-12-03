# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
import sys
# import EITHER PyQt4 OR PySide, depending on your system
from PyQt4 import QtGui, QtCore

from PyQt4.QtGui import QSizePolicy
from PyQt4.QtCore import QSize
#from PySide.QtCore import *
#from PySide.QtGui import *

#import matplotlib as plt
#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
#from matplotlib.figure import Figure

import numpy as np
import scipy.signal as sig

import databroker as db
from plotUtils import MplCanvas, MplWidget


N_FFT = 2048 # FFT length for freqz
 
DEBUG = True   

"""
QMainWindow is a class that understands GUI elements like a toolbar, statusbar,
central widget, docking areas. QWidget is just a raw widget.
When you want to have a main window for you project, use QMainWindow.

If you want to create a dialog box (modal dialog), use QWidget, or, 
more preferably, QDialog   
"""       
    
class PlotHf(QtGui.QMainWindow):

    def __init__(self, parent = None): # default parent = None -> top Window 
        super(PlotHf, self).__init__(parent) # initialize QWidget base class
#        QtGui.QMainWindow.__init__(self) # alternative syntax
        
        self.A_SB = 60   # min. Sperrdämpfung im Stoppband in dB (= min. y-Wert des Plots)    
 
        self.mplwidget = MplWidget()
#        self.mplwidget.setParent(self)
        self.mplwidget.setFocus()
        # make this the central widget, taking all available space:
        self.setCentralWidget(self.mplwidget)
        
        self.draw()
        
#        #=============================================
#        # Signals & Slots
#        #=============================================          
#        self.mplCanv.butDraw.clicked.connect(lambda: self.draw(self.coeffs))
        self.mplwidget.sldLw.valueChanged.connect(lambda:self.draw())  
            
    def draw(self):
        """ 
        Re-calculate |H(f)| and draw the figure
        """
        self.coeffs = db.gD['coeffs']# coeffs
        self.bb = self.coeffs[0]
        self.aa = self.coeffs[1]
        [W,H] = sig.freqz(self.bb, self.aa, N_FFT) # calculate H(W) for W = 0 ... pi
        print 
        if DEBUG:
            print("-------------------------")
            print("plotHf.draw() ") 
            print("-------------------------")
            print("b,a = ", self.bb, self.aa)
        F = W / (2 * np.pi)

        # clear the axes and (re)draw the plot
        #
        mpl = self.mplwidget.ax
        mpl.clear()
        mpl.plot(F,20*np.log10(abs(H)), lw = self.mplwidget.sldLw.value()/5.)
        mpl.axis([0, 0.5, -self.A_SB-10, 2])
        mpl.set_title(r'Betragsfrequenzgang')
        mpl.set_xlabel(r'$F\; \rightarrow $')    
        mpl.set_ylabel(r'$|H(\mathrm{e}^{\mathrm{j} \Omega})|\; \rightarrow $')    
 
        self.mplwidget.redraw()
#        self.mplCanv.pltCanv.draw()
        
#------------------------------------------------------------------------------  
    
def main():
    app = QtGui.QApplication(sys.argv)
    form = PlotHf()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
