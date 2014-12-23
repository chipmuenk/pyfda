# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals 
import sys, os
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
# import databroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import databroker as db

from plotUtils import MplWidget#, MyMplToolbar, MplCanvas 

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
        

        self.lblLog = QtGui.QLabel("Log. y-scale")        
        self.btnLog = QtGui.QCheckBox()
        self.btnLog.setChecked(True)
        self.lblInset = QtGui.QLabel("Show Inset")
        self.btnInset = QtGui.QCheckBox()
        self.lblSpecs = QtGui.QLabel("Show Specs")
        self.btnSpecs = QtGui.QCheckBox()
        self.btnSpecs.setChecked(False)

        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addStretch(10)
        self.hbox.addWidget(self.lblLog)
        self.hbox.addWidget(self.btnLog)
        self.hbox.addStretch(1)
        self.hbox.addWidget(self.lblInset)
        self.hbox.addWidget(self.btnInset)
        self.hbox.addStretch(1)
        self.hbox.addWidget(self.lblSpecs)
        self.hbox.addWidget(self.btnSpecs)
        self.hbox.addStretch(10)
    
        self.mplwidget = MplWidget()
#        self.mplwidget.setParent(self)
        
        self.mplwidget.vbox.addLayout(self.hbox)
#        self.mplwidget.vbox1.addWidget(self.mplwidget)    
       
        self.mplwidget.setFocus()
        # make this the central widget, taking all available space:
        self.setCentralWidget(self.mplwidget)
        
#        self.setLayout(self.hbox)
        
        self.draw() # calculate and draw |H(f)|
        
#        #=============================================
#        # Signals & Slots
#        #=============================================          
        self.btnLog.clicked.connect(lambda:self.draw())
        self.btnInset.clicked.connect(lambda:self.draw())
        self.btnSpecs.clicked.connect(lambda:self.draw())

    def plotSpecs(self, specAxes, specLog):
        """
        Plot the corners of the filter specifications when the corresponding
        check box is selected.
        """
        ax = specAxes
        F_max = self.f_S/2
        if specLog:
            if db.gD["curFilter"]["ft"] == "FIR":
                A_DB_max = self.A_pb # 20*log10(1+del_DB)
            else: # IIR log
                A_DB_max = 0
            A_DB_min = -self.A_pb # 20*log10(1-del_DB)
            A_sb = -self.A_sb
            A_sbx = A_sb - 10
        else:
            if db.gD["curFilter"]["ft"] == 'FIR':
                A_DB_max = 10**(self.A_pb/20)# 1 + del_DB 
            else:
                A_DB_max = 1
            A_DB_min = 10**(-self.A_pb/20) #1 - del_DB
            A_sb = 10**(-self.A_sb/20)
            A_sbx = A_sb / 5
        
        if db.gD["curFilter"]["rt"] == "LP" or db.gD["curFilter"]["rt"] == "BS":
            F_0 = 0
            F_1 = db.gD['curSpecs']['F_pb'] / self.f_S
            F_2 = db.gD['curSpecs']['F_sb'] / self.f_S
            F_3 = db.gD['curSpecs']['F_sb2'] / self.f_S
            F_4 = db.gD['curSpecs']['F_pb2'] / self.f_S
            F_5 = F_max

        elif db.gD["curFilter"]["rt"] in {"HP", "BP"}:
            F_0 = F_max
            F_1 = db.gD['curSpecs']['F_sb'] / self.f_S
            F_2 = db.gD['curSpecs']['F_pb'] / self.f_S
            F_3 = db.gD['curSpecs']['F_pb2'] / self.f_S
            F_4 = db.gD['curSpecs']['F_sb2'] / self.f_S
            F_5 = 0

        if db.gD["curFilter"]["rt"] in {'LP', 'HP', 'BS'}:
            ax.plot([F_0, F_1],[A_DB_min, A_DB_min], 'b--') # PB
            ax.plot([F_0, F_2],[A_DB_max, A_DB_max], 'b--') # PB
            ax.plot([F_1, F_1],[A_DB_min, A_DB_min-10],'b--')# PB limit
            ax.plot([F_2, F_2],[A_DB_max, A_sb],'b--') # SB limit
            
            if db.gD["curFilter"]["rt"] in {"LP", "HP"}:
                ax.plot([F_2, F_5],[A_sb, A_sb],'b--') # SB
            else: # "BS"
                ax.plot([F_2, F_3],[A_sb, A_sb],'b--') # SB
                ax.plot([F_3, F_3],[A_DB_max, A_sb],'b--') # limit SB
                ax.plot([F_3, F_5],[A_DB_max, A_DB_max], 'b--') # PB  
                ax.plot([F_4, F_5],[A_DB_min, A_DB_min], 'b--') # PB
                ax.plot([F_4, F_4],[A_DB_min, A_DB_min-10],'b--')# lim. PB

        if db.gD["curFilter"]["rt"] == "BP":
            ax.plot([0, F_1],[A_sb, A_sb], 'b--') # SB
            ax.plot([F_1, F_1],[A_sb, A_DB_max], 'b--') # SB
            ax.plot([F_2, F_2],[A_sb-10, A_DB_min],'b--')# PB-limit
            ax.plot([F_2, F_3],[A_DB_min, A_DB_min],'b--') # PB
            ax.plot([F_1, F_4],[A_DB_max, A_DB_max],'b--') # PB
            ax.plot([F_3, F_3],[A_sbx, A_DB_min],'b--') # PB
            ax.plot([F_4, F_4],[A_sb, A_DB_max],'b--') # PB           
            ax.plot([F_4, F_max],[A_sb, A_sb], 'b--') # lower PB-limit  
            
    def draw(self):
        """ 
        Re-calculate |H(f)| and draw the figure
        """
        self.log = self.btnLog.isChecked()
        self.specs = self.btnSpecs.isChecked()
        self.inset = self.btnInset.isChecked()
        
#        self.coeffs = db.gD['coeffs']# coeffs
        self.bb = db.gD['coeffs'][0]
        self.aa = db.gD['coeffs'][1]
        
        self.f_S = db.gD['curSpecs']['fS']
        self.f_S = 1
        self.F_pb = db.gD['curSpecs']['F_pb'] / self.f_S
        self.F_sb = db.gD['curSpecs']['F_sb'] / self.f_S
        
        self.A_pb = db.gD['curSpecs']['A_pb']
        self.A_sb = db.gD['curSpecs']['A_sb']


        if DEBUG:
            print("--- plotHf.draw() --- ") 
            print("b, a = ", self.bb, self.aa)

        # calculate |H(W)| for W = 0 ... pi:
        [W,H] = sig.freqz(self.bb, self.aa, worN = db.gD['N_FFT'])
        F = W / (2 * np.pi)

        # clear the axes and (re)draw the plot
        #
        fig = self.mplwidget.fig
        ax = self.mplwidget.ax# fig.add_axes([.1,.1,.8,.8])#  ax = fig.add_axes([.1,.1,.8,.8])
        ax.clear()
        
        #================ Main Plotting Routine =========================
        
        if self.log:
            ax.plot(F,20*np.log10(abs(H)), lw = db.gD['rc']['lw'])

            ax.set_ylabel(r'$|H(\mathrm{e}^{\mathrm{j} \Omega})| \;$'+
                        r'$\mathrm{[dB]} \; \rightarrow $')

        else: #  'lin'
            ax.plot(F,abs(H), lw = db.gD['rc']['lw'])

            ax.set_ylabel(r'$|H(\mathrm{e}^{\mathrm{j} \Omega})| \;$'+
                        r'$\rightarrow $')

        if self.specs: self.plotSpecs(specAxes = ax, specLog = self.log)
            
        if self.log:
            ax.axis([0, 0.5, -self.A_sb -10, self.A_pb +1] )
        else:
            ax.axis([0, 0.5, 10**((-self.A_sb-10)/20), 10**((self.A_pb+1)/20)])
 
        ax.set_title(r'Betragsfrequenzgang')
        ax.set_xlabel(r'$F\; \rightarrow $') 
        
        # ---------- Inset Plot -------------------------------------------
        if self.inset:
            ax1 = fig.add_axes([0.65, 0.61, .3, .3]);  # x,y,dx,dy
#            ax1 = zoomed_inset_axes(ax, 6, loc=1) # zoom = 6
            ax1.clear() # clear old plot and specs
            if self.specs: self.plotSpecs(specAxes = ax1, specLog = self.log)
            if self.log:
                ax1.plot(F,20*np.log10(abs(H)), lw = db.gD['rc']['lw'])
            else:
                ax1.plot(F,abs(H), lw = db.gD['rc']['lw'])
#            ax1.set_xlim(0, self.F_pb)
#            ax1.set_ylim(-self.A_pb, self.A_pb) 


        else:
            try:
                for ax in fig.axes:
                    print(ax.label)
                fig.delaxes(ax1)
            except UnboundLocalError:
                pass
            
        self.mplwidget.redraw()
        
#------------------------------------------------------------------------------  
    
def main():
    app = QtGui.QApplication(sys.argv)
    form = PlotHf()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
