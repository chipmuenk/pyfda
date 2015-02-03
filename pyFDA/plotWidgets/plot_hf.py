# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals 
import sys, os

from PyQt4 import QtGui
from PyQt4.QtGui import QSizePolicy
from PyQt4.QtCore import QSize

#import matplotlib as plt
#from matplotlib.figure import Figure

import numpy as np
import scipy.signal as sig
# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb

from plot_utils import MplWidget#, MyMplToolbar, MplCanvas 


"""
QMainWindow is a class that understands GUI elements like a toolbar, statusbar,
central widget, docking areas. QWidget is just a raw widget.
When you want to have a main window for you project, use QMainWindow.

If you want to create a dialog box (modal dialog), use QWidget, or, 
more preferably, QDialog   
"""       
    
class PlotHf(QtGui.QMainWindow):

    def __init__(self, parent = None, DEBUG = False): # default parent = None -> top Window 
        super(PlotHf, self).__init__(parent) # initialize QWidget base class
#        QtGui.QMainWindow.__init__(self) # alternative syntax

        self.DEBUG = DEBUG        

        self.lblLog = QtGui.QLabel("Log. y-scale")        
        self.btnLog = QtGui.QCheckBox()
        self.btnLog.setChecked(True)
        
        self.lblInset = QtGui.QLabel("Inset")
        self.btnInset = QtGui.QCheckBox()
        self.btnInset.setToolTip("Display second zoomed plot")
        
        self.lblSpecs = QtGui.QLabel("Show Specs")
        self.btnSpecs = QtGui.QCheckBox()
        self.btnSpecs.setChecked(False)
        self.btnSpecs.setToolTip("Display filter specs as hatched regions")
        
        self.lblPhase = QtGui.QLabel("Phase")
        self.btnPhase = QtGui.QCheckBox()
        self.btnPhase.setToolTip("Overlay phase")


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
        self.hbox.addStretch(1)
        self.hbox.addWidget(self.lblPhase)
        self.hbox.addWidget(self.btnPhase)
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
        self.btnPhase.clicked.connect(lambda:self.draw())

    def plotSpecLimits(self, specAxes, specLog):
        """
        Plot the specifications limits 
        """
#        fc = (0.8,0.8,0.8) # color for shaded areas
        fill_params = {"color":"none","hatch":"/", "edgecolor":"k", "lw":0.0}
        ax = specAxes
        ymax = ax.get_ylim()[1]
        F_max = self.f_S/2
        if specLog:
            if fb.gD['selFilter']['ft'] == "FIR":
                A_PB_max = self.A_PB # 20*log10(1+del_DB)
            else: # IIR log
                A_PB_max = 0
            A_PB_min = -self.A_PB
            A_PB_minx = A_PB_min - 10# 20*log10(1-del_DB)
            A_SB = -self.A_SB
            A_SBx = A_SB - 10
        else:
            if fb.gD['selFilter']['ft'] == 'FIR':
                A_PB_max = 10**(self.A_PB/20)# 1 + del_DB 
            else:
                A_PB_max = 1
            A_PB_min = 10**(-self.A_PB/20) #1 - del_DB
            A_PB_minx = A_PB_min / 2
            A_SB = 10**(-self.A_SB/20)
            A_SBx = A_SB / 5
        
        F_PB = self.F_PB
        F_SB = fb.gD['selFilter']['F_SB'] * self.f_S
        F_SB2 = fb.gD['selFilter']['F_SB2'] * self.f_S
        F_PB2 = fb.gD['selFilter']['F_PB2'] * self.f_S

        if fb.gD['selFilter']['rt'] == 'LP':
            # upper limits:            
            ax.plot([0, F_SB, F_SB, F_max],
                    [A_PB_max, A_PB_max, A_SB, A_SB], 'b--')
            ax.fill_between([0, F_SB, F_SB, F_max], ymax,
                    [A_PB_max, A_PB_max, A_SB, A_SB], **fill_params)                    
            # lower limits:
            ax.plot([0, F_PB, F_PB],[A_PB_min, A_PB_min, A_PB_minx], 'b--')
            ax.fill_between([0, F_PB, F_PB], A_PB_minx,
                            [A_PB_min, A_PB_min, A_PB_minx], **fill_params)
       
        if fb.gD['selFilter']['rt'] == 'HP':
            # upper limits:
            ax.plot([0, F_SB, F_SB, F_max],
                    [A_SB, A_SB, A_PB_max, A_PB_max], 'b--')
            ax.fill_between([0, F_SB, F_SB, F_max], 10,
                    [A_SB, A_SB, A_PB_max, A_PB_max], **fill_params)
            # lower limits:
            ax.plot([F_PB, F_PB, F_max],[A_PB_minx, A_PB_min, A_PB_min], 'b--')
            ax.fill_between([F_PB, F_PB, F_max], A_PB_minx,
                            [A_PB_minx, A_PB_min, A_PB_min], **fill_params)
            
        if fb.gD['selFilter']['rt'] == 'BS':
            # lower limits left:            
            ax.plot([0, F_PB, F_PB],[A_PB_min, A_PB_min, A_PB_minx], 'b--')
            ax.fill_between([0, F_PB, F_PB], A_PB_minx,
                            [A_PB_min, A_PB_min, A_PB_minx], **fill_params)

            # upper limits:            
            ax.plot([0, F_SB, F_SB, F_SB2, F_SB2, F_max],
                    [A_PB_max, A_PB_max, A_SB, A_SB, A_PB_max, A_PB_max], 'b--')
            ax.fill_between([0, F_SB, F_SB, F_SB2, F_SB2, F_max], 10,
                    [A_PB_max, A_PB_max, A_SB, A_SB, A_PB_max, A_PB_max], 
                        **fill_params)

            # lower limits right:            
            ax.plot([F_PB2, F_PB2, F_max],[A_PB_minx, A_PB_min, A_PB_min],'b--')    
            ax.fill_between([F_PB2, F_PB2, F_max], A_PB_minx,
                            [A_PB_minx, A_PB_min, A_PB_min], **fill_params)    
            

        if fb.gD['selFilter']['rt'] == "BP":
            # upper limits:
            ax.plot([0,    F_SB,  F_SB,      F_SB2,      F_SB2,  F_max],
                    [A_SB, A_SB, A_PB_max, A_PB_max, A_SB, A_SB], 'b--')
            ax.fill_between([0, F_SB, F_SB, F_SB2, F_SB2, F_max], 10,
                    [A_SB, A_SB, A_PB_max, A_PB_max, A_SB, A_SB],**fill_params)
            # lower limits:
            ax.plot([F_PB, F_PB, F_PB2, F_PB2], 
                    [A_PB_minx, A_PB_min, A_PB_min, A_PB_minx], 'b--' )
            ax.fill_between([F_PB, F_PB, F_PB2, F_PB2], A_PB_minx,
                    [A_PB_minx, A_PB_min, A_PB_min, A_PB_minx], **fill_params)       
            
    def draw(self):
        """ 
        Re-calculate |H(f)| and draw the figure
        """
        self.log = self.btnLog.isChecked()
        self.specs = self.btnSpecs.isChecked()
        self.inset = self.btnInset.isChecked()
        self.phase = self.btnPhase.isChecked()
        
#        self.coeffs = fb.gD['coeffs']# coeffs
        self.bb = fb.gD['coeffs'][0]
        self.aa = fb.gD['coeffs'][1]
        
        self.f_S = fb.gD['selFilter']['f_S']
#        self.f_S = 1
        self.F_PB = fb.gD['selFilter']['F_PB'] * self.f_S
        self.F_SB = fb.gD['selFilter']['F_SB'] * self.f_S
        
        self.A_PB = fb.gD['selFilter']['A_PB']
        self.A_SB = fb.gD['selFilter']['A_SB']


        if self.DEBUG:
            print("--- plotHf.draw() --- ") 
            print("b, a = ", self.bb, self.aa)

        # calculate |H(W)| for W = 0 ... pi:
        [W,H] = sig.freqz(self.bb, self.aa, worN = fb.gD['N_FFT'])
        F = W / (2 * np.pi) * self.f_S

        # clear the axes and (re)draw the plot
        #
        fig = self.mplwidget.fig
        ax = self.mplwidget.ax# fig.add_axes([.1,.1,.8,.8])#  ax = fig.add_axes([.1,.1,.8,.8])
#        ax2= self.mplwidget.ax2
        ax.clear()
        
        #================ Main Plotting Routine =========================
        
        if self.log:
            ax.plot(F,20*np.log10(abs(H)), lw = fb.gD['rc']['lw'])

            ax.set_ylabel(r'$|H(\mathrm{e}^{\mathrm{j} \Omega})|$'+ ' in dB ' +
                        r'$\rightarrow$')

        else: #  'lin'
            ax.plot(F,abs(H), lw = fb.gD['rc']['lw'])

            ax.set_ylabel(r'$|H(\mathrm{e}^{\mathrm{j} \Omega})| \;$'+
                        r'$\rightarrow $')

        if self.specs: self.plotSpecLimits(specAxes = ax, specLog = self.log)
            
        if self.log:
            ax.axis([0, self.f_S/2., -self.A_SB -10, self.A_PB +1] )
        else:
            ax.axis([0, self.f_S/2., 10**((-self.A_SB-10)/20), 10**((self.A_PB+1)/20)])
        if self.phase:
            ax.plot(F,np.angle(H), lw = fb.gD['rc']['lw'])
            pass
 
        ax.set_title(r'Magnitude Frequency Response')
#        ax.set_xlabel(r'$F\; \rightarrow $') 
        ax.set_xlabel(fb.gD['selFilter']['plt_fLabel']) 
        
        # ---------- Inset Plot -------------------------------------------
        if self.inset:
            ax_i = fig.add_axes([0.65, 0.61, .3, .3]);  # x,y,dx,dy
#            ax1 = zoomed_inset_axes(ax, 6, loc=1) # zoom = 6
            ax_i.clear() # clear old plot and specs
            if self.specs: self.plotSpecs(specAxes = ax_i, specLog = self.log)
            if self.log:
                ax_i.plot(F,20*np.log10(abs(H)), lw = fb.gD['rc']['lw'])
            else:
                ax_i.plot(F,abs(H), lw = fb.gD['rc']['lw'])
#            ax1.set_xlim(0, self.F_PB)
#            ax1.set_ylim(-self.A_PB, self.A_PB) 


        else:
            try:
#                for ax in fig.axes:
#                    fig.delaxes(ax)
                fig.delaxes(ax_i)
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
