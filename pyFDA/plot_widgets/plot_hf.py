# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals 
import sys, os

from PyQt4 import QtGui
#from PyQt4.QtGui import QSizePolicy
#from PyQt4.QtCore import QSize

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
        
        units = ["dB", "V", "W"] 
        self.comboUnitsA = QtGui.QComboBox(self)
        self.comboUnitsA.addItems(units)
        self.comboUnitsA.setObjectName("comboUnitsA")
        self.comboUnitsA.setToolTip("Set unit for y-axis:\n"
        "dB is attenuation (positive values)\nV and W are less than 1.")
        self.comboUnitsA.setCurrentIndex(0)
        
        self.lblLinphase = QtGui.QLabel("Linphase")
        self.chkLinphase = QtGui.QCheckBox()
        self.chkLinphase.setToolTip("Plot H(f) of acausal linphase system.")
        
        self.lblInset = QtGui.QLabel("Inset")
        self.chkInset = QtGui.QCheckBox()
        self.chkInset.setToolTip("Display second zoomed plot")
        
        self.lblSpecs = QtGui.QLabel("Show Specs")
        self.chkSpecs = QtGui.QCheckBox()
        self.chkSpecs.setChecked(False)
        self.chkSpecs.setToolTip("Display filter specs as hatched regions")
        
        self.lblPhase = QtGui.QLabel("Phase")
        self.chkPhase = QtGui.QCheckBox()
        self.chkPhase.setToolTip("Overlay phase")


        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addStretch(10)
        self.hbox.addWidget(self.comboUnitsA)
        self.hbox.addStretch(1)
        self.hbox.addWidget(self.lblLinphase)
        self.hbox.addWidget(self.chkLinphase)
        self.hbox.addStretch(1)
        self.hbox.addWidget(self.lblInset)
        self.hbox.addWidget(self.chkInset)
        self.hbox.addStretch(1)
        self.hbox.addWidget(self.lblSpecs)
        self.hbox.addWidget(self.chkSpecs)
        self.hbox.addStretch(1)
        self.hbox.addWidget(self.lblPhase)
        self.hbox.addWidget(self.chkPhase)
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
        self.comboUnitsA.currentIndexChanged.connect(lambda:self.draw())

        self.chkLinphase.clicked.connect(lambda:self.draw())
        self.chkInset.clicked.connect(lambda:self.draw())
        self.chkSpecs.clicked.connect(lambda:self.draw())
        self.chkPhase.clicked.connect(lambda:self.draw())

    def plotSpecLimits(self, specAxes, unitA):
        """
        Plot the specifications limits 
        """
#        fc = (0.8,0.8,0.8) # color for shaded areas
        fill_params = {"color":"none","hatch":"/", "edgecolor":"k", "lw":0.0}
        ax = specAxes
        ymax = ax.get_ylim()[1]

        # extract from filterTree the parameters that are actually used        
#        myParams = fb.filTree[rt][ft][dm][fo]['par']
#        freqParams = [l for l in myParams if l[0] == 'F']

        if fb.fil[0]['ft'] == "FIR":
            A_PB_max = self.A_PB # 20*log10(1+del_PB)
            A_PB2_max = self.A_PB2             
        else: # IIR log
            A_PB_max = 0
            
        if unitA == 'V':
            dBMul = 20.
        elif unitA == 'W':
            dBMul = 10.
            
        if unitA == 'dB':
            A_PB_min = -self.A_PB
            A_PB2_min = -self.A_PB2            
            A_PB_minx = min(A_PB_min, A_PB2_min) - 10# 20*log10(1-del_PB)
            A_SB = -self.A_SB
            A_SB2 = -self.A_SB2
            A_SBx = A_SB - 10
        else:
            A_PB_max = 10**(A_PB_max/dBMul)# 1 + del_PB
            A_PB2_max = 10**(A_PB2_max/dBMul)# 1 + del_PB 
            A_PB_min = 10**(-self.A_PB/dBMul) #1 - del_PB
            A_PB2_min = 10**(-self.A_PB2/dBMul) #1 - del_PB
            A_PB_minx = A_PB_min / 2
            A_SB = 10**(-self.A_SB/dBMul)
            A_SB2 = 10**(-self.A_SB2/dBMul)           
            A_SBx = A_SB / 5    

        F_max = self.f_S/2            
        F_PB = self.F_PB
        F_SB = fb.fil[0]['F_SB'] * self.f_S
        F_SB2 = fb.fil[0]['F_SB2'] * self.f_S
        F_PB2 = fb.fil[0]['F_PB2'] * self.f_S

        if fb.fil[0]['rt'] == 'LP':
            # upper limits:            
            ax.plot([0, F_SB, F_SB, F_max],
                    [A_PB_max, A_PB_max, A_SB, A_SB], 'b--')
            ax.fill_between([0, F_SB, F_SB, F_max], ymax,
                    [A_PB_max, A_PB_max, A_SB, A_SB], **fill_params)                    
            # lower limits:
            ax.plot([0, F_PB, F_PB],[A_PB_min, A_PB_min, A_PB_minx], 'b--')
            ax.fill_between([0, F_PB, F_PB], A_PB_minx,
                            [A_PB_min, A_PB_min, A_PB_minx], **fill_params)
       
        if fb.fil[0]['rt'] == 'HP':
            # upper limits:
            ax.plot([0, F_SB, F_SB, F_max],
                    [A_SB, A_SB, A_PB_max, A_PB_max], 'b--')
            ax.fill_between([0, F_SB, F_SB, F_max], 10,
                    [A_SB, A_SB, A_PB_max, A_PB_max], **fill_params)
            # lower limits:
            ax.plot([F_PB, F_PB, F_max],[A_PB_minx, A_PB_min, A_PB_min], 'b--')
            ax.fill_between([F_PB, F_PB, F_max], A_PB_minx,
                            [A_PB_minx, A_PB_min, A_PB_min], **fill_params)
            
        if fb.fil[0]['rt'] == 'BS':
            # lower limits left:            
            ax.plot([0, F_PB, F_PB],[A_PB_min, A_PB_min, A_PB_minx], 'b--')
            ax.fill_between([0, F_PB, F_PB], A_PB_minx,
                            [A_PB_min, A_PB_min, A_PB_minx], **fill_params)

            # upper limits:            
            ax.plot([0, F_SB, F_SB, F_SB2, F_SB2, F_max],
                    [A_PB_max, A_PB_max, A_SB, A_SB, A_PB2_max, A_PB2_max], 'b--')
            ax.fill_between([0, F_SB, F_SB, F_SB2, F_SB2, F_max], 10,
                    [A_PB_max, A_PB_max, A_SB, A_SB, A_PB2_max, A_PB2_max], 
                        **fill_params)

            # lower limits right:            
            ax.plot([F_PB2, F_PB2, F_max],[A_PB_minx, A_PB2_min, A_PB2_min],'b--')    
            ax.fill_between([F_PB2, F_PB2, F_max], A_PB_minx,
                            [A_PB_minx, A_PB2_min, A_PB2_min], **fill_params)    
            

        if fb.fil[0]['rt'] == "BP":
            # upper limits:
            ax.plot([0,    F_SB,  F_SB,      F_SB2,      F_SB2,  F_max],
                    [A_SB, A_SB, A_PB_max, A_PB_max, A_SB2, A_SB2], 'b--')
            ax.fill_between([0, F_SB, F_SB, F_SB2, F_SB2, F_max], 10,
                    [A_SB, A_SB, A_PB_max, A_PB_max, A_SB2, A_SB2],**fill_params)
            # lower limits:
            ax.plot([F_PB, F_PB, F_PB2, F_PB2], 
                    [A_PB_minx, A_PB_min, A_PB_min, A_PB_minx], 'b--' )
            ax.fill_between([F_PB, F_PB, F_PB2, F_PB2], A_PB_minx,
                    [A_PB_minx, A_PB_min, A_PB_min, A_PB_minx], **fill_params)       
            
    def draw(self):
        """ 
        Re-calculate |H(f)| and draw the figure
        """
        self.unitA = self.comboUnitsA.currentText()
        
        # Linphase settings only makes sense for amplitude plot
        self.chkLinphase.setCheckable(self.unitA == 'V')
        self.chkLinphase.setEnabled(self.unitA == 'V')
        self.lblLinphase.setEnabled(self.unitA == 'V')

        self.linphase = self.chkLinphase.isChecked()
        self.specs = self.chkSpecs.isChecked()
        self.inset = self.chkInset.isChecked()
        self.phase = self.chkPhase.isChecked()
        
        if np.ndim(fb.fil[0]['coeffs']) == 1: # FIR
            self.bb = fb.fil[0]['coeffs']
            self.aa = 1.
        else: # IIR
            self.bb = fb.fil[0]['coeffs'][0]
            self.aa = fb.fil[0]['coeffs'][1]
        
        self.f_S  = fb.fil[0]['f_S']
        self.F_PB = fb.fil[0]['F_PB'] * self.f_S
        self.F_SB = fb.fil[0]['F_SB'] * self.f_S
        
        self.A_PB  = fb.fil[0]['A_PB']
        self.A_PB2 = fb.fil[0]['A_PB2']
        self.A_SB  = fb.fil[0]['A_SB']
        self.A_SB2 = fb.fil[0]['A_SB2']

        if self.DEBUG:
            print("--- plotHf.draw() --- ") 
            print("b, a = ", self.bb, self.aa)

        # calculate |H(W)| for W = 0 ... pi:
        [W,H] = sig.freqz(self.bb, self.aa, worN = fb.gD['N_FFT'], 
            whole = fb.rcFDA['freqSpecsRangeWhole'])
        if self.linphase: # remove the linear phase
            H = H * np.exp(1j * W * fb.fil[0]["N"]/2.)

        F = W / (2 * np.pi) * self.f_S

        # clear the axes and (re)draw the plot
        #
        fig = self.mplwidget.fig
        ax = self.mplwidget.ax# fig.add_axes([.1,.1,.8,.8])#  ax = fig.add_axes([.1,.1,.8,.8])
#        ax2= self.mplwidget.ax2
        ax.clear()
        
        #================ Main Plotting Routine =========================
        
        if self.unitA == 'dB':
            ax.plot(F,20*np.log10(abs(H)), lw = fb.gD['rc']['lw'])

            ax.set_ylabel(r'$|H(\mathrm{e}^{\mathrm{j} \Omega})|$'+ ' in dB ' +
                        r'$\rightarrow$')
            ax.axis([0, self.f_S/2., -self.A_SB -10, self.A_PB +1] )

        elif self.unitA == 'V': #  'lin'
            if self.linphase:
                ax.plot(F, H.real, lw = fb.gD['rc']['lw'])
    
                ax.set_ylabel(r'$H(\mathrm{e}^{\mathrm{j} \Omega})$'+' in V '+
                            r'$\rightarrow $')
                ax.axis([0, self.f_S/2., 10**((-self.A_SB-10)/20), 10**((self.A_PB+1)/20)])
            else:
                ax.plot(F,abs(H), lw = fb.gD['rc']['lw'])
    
                ax.set_ylabel(r'$|H(\mathrm{e}^{\mathrm{j}\Omega})|$'+' in V '+
                            r'$\rightarrow $')
                ax.axis([0, self.f_S/2., 10**((-self.A_SB-10)/20), 10**((self.A_PB+1)/20)])
                
        else:
            ax.plot(F,abs(H)*abs(H), lw = fb.gD['rc']['lw'])

            ax.set_ylabel(r'$|H(\mathrm{e}^{\mathrm{j} \Omega})|$'+ ' in W ' +
                        r'$\rightarrow $')
            ax.axis([0, self.f_S/2., 10**((-self.A_SB-10)/10), 10**((self.A_PB+1)/10)])

        if self.specs: self.plotSpecLimits(specAxes = ax, unitA = self.unitA)
            
        if self.phase:
            if self.linphase:
                ax.plot(F,np.angle(H), lw = fb.gD['rc']['lw'])                
            else:
                ax.plot(F,np.unwrap(np.angle(H)), lw = fb.gD['rc']['lw'])                

 
        ax.set_title(r'Magnitude Frequency Response')
        ax.set_xlabel(fb.fil[0]['plt_fLabel']) 
        
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
