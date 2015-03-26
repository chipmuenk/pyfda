# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os

from PyQt4 import QtGui
#from PyQt4.QtGui import QSizePolicy
#from PyQt4.QtCore import QSize

import numpy as np
import scipy.signal as sig

# import modules from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb
from plot_widgets.plot_utils import MplWidget#, MyMplToolbar, MplCanvas

"""
QMainWindow is a class that understands GUI elements like a toolbar, statusbar,
central widget, docking areas. QWidget is just a raw widget.
When you want to have a main window for you project, use QMainWindow.

If you want to create a dialog box (modal dialog), use QWidget, or,
more preferably, QDialog
"""

class PlotHf(QtGui.QMainWindow):
# TODO: spec limits are not hatched in Python 3, it seems dict "fill_params"
#           is not recognized
# TODO: inset plot cannot be zoomed independently from main window
# TODO: inset plot should have useful preset range, depending on filter type,
#       stop band or pass band should be selectable as well as lin / log scale
# TODO: position and size of inset plot should be selectable
# TODO: unit of phase should be derived from phase widget

    def __init__(self, parent = None, DEBUG = False): # default parent = None -> top Window
        super(PlotHf, self).__init__(parent) # initialize QWidget base class
#        QtGui.QMainWindow.__init__(self) # alternative syntax

        self.DEBUG = DEBUG

        modes = ["| H |", "re{H}", "im{H}"]
        self.cmbShowH = QtGui.QComboBox(self)
        self.cmbShowH.addItems(modes)
        self.cmbShowH.setObjectName("cmbUnitsH")
        self.cmbShowH.setToolTip("Show magnitude, real or imag. part of H.")
        self.cmbShowH.setCurrentIndex(0)

        self.lblIn = QtGui.QLabel("in")

        units = ["dB", "V", "W"]
        self.cmbUnitsA = QtGui.QComboBox(self)
        self.cmbUnitsA.addItems(units)
        self.cmbUnitsA.setObjectName("cmbUnitsA")
        self.cmbUnitsA.setToolTip("Set unit for y-axis:\n"
        "dB is attenuation (positive values)\nV and W are less than 1.")
        self.cmbUnitsA.setCurrentIndex(0)


        self.lblLinphase = QtGui.QLabel("Linphase")
        self.chkLinphase = QtGui.QCheckBox()
        self.chkLinphase.setToolTip("Remove linear phase according to filter order.\n"
           "Attention: this may make little sense for a non-linear phase filter.")

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


        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addStretch(10)
        self.layHChkBoxes.addWidget(self.cmbShowH)
        self.layHChkBoxes.addWidget(self.lblIn)
        self.layHChkBoxes.addWidget(self.cmbUnitsA)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.lblLinphase)
        self.layHChkBoxes.addWidget(self.chkLinphase)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.lblInset)
        self.layHChkBoxes.addWidget(self.chkInset)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.lblSpecs)
        self.layHChkBoxes.addWidget(self.chkSpecs)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.lblPhase)
        self.layHChkBoxes.addWidget(self.chkPhase)
        self.layHChkBoxes.addStretch(10)

        self.mplwidget = MplWidget()
#        self.mplwidget.setParent(self)

        self.mplwidget.layVMainMpl.addLayout(self.layHChkBoxes)
#        self.mplwidget.layVMainMpl1.addWidget(self.mplwidget)

        self.mplwidget.setFocus()
        # make this the central widget, taking all available space:
        self.setCentralWidget(self.mplwidget)

#        self.setLayout(self.layHChkBoxes)
        self.ax = self.mplwidget.fig.add_subplot(111)

        self.draw() # calculate and draw |H(f)|

#        #=============================================
#        # Signals & Slots
#        #=============================================
        self.cmbUnitsA.currentIndexChanged.connect(self.draw)
        self.cmbShowH.currentIndexChanged.connect(self.draw)

        self.chkLinphase.clicked.connect(self.draw)
        self.chkInset.clicked.connect(self.draw_inset)
        self.chkSpecs.clicked.connect(self.draw)
        self.chkPhase.clicked.connect(self.draw_phase)

    def plotSpecLimits(self, specAxes):
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

        if self.unitA == 'V':
            dBMul = 20.
        elif self.unitA == 'W':
            dBMul = 10.

        if self.unitA == 'dB':
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
        self.unitA = self.cmbUnitsA.currentText()

        # Linphase settings only makes sense for amplitude plot
        self.chkLinphase.setCheckable(self.unitA == 'V')
        self.chkLinphase.setEnabled(self.unitA == 'V')
        self.lblLinphase.setEnabled(self.unitA == 'V')

        self.specs = self.chkSpecs.isChecked()
        self.inset = self.chkInset.isChecked()
        self.phase = self.chkPhase.isChecked()
        self.linphase = self.chkLinphase.isChecked()


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

        f_lim = fb.rcFDA['freqSpecsRange']
        wholeF = fb.rcFDA['freqSpecsRangeType'] != 'half'

#        self.wholeF = fb.rcFDA['freqSpecsRangeWhole']
#        if self.wholeF:
#            f_lim = [0, self.f_S]
#        elif self.wholeF == 'sym':
#            f_lim = [-self.f_S/2, self.f_S/2]
#        else:
#            f_lim = [0, self.f_S/2]



        if self.DEBUG:
            print("--- plotHf.draw() --- ")
            print("b, a = ", self.bb, self.aa)

        # calculate H_c(W) (complex) for W = 0 ... pi:
        [W, self.H_c] = sig.freqz(self.bb, self.aa, worN = fb.gD['N_FFT'],
            whole = wholeF)
        self.F = W / (2 * np.pi) * self.f_S

        if fb.rcFDA['freqSpecsRangeType'] == 'sym':
            self.H_c = np.fft.fftshift(self.H_c)
            self.F = self.F - self.f_S/2.

        if self.linphase: # remove the linear phase
            H = self.H_c * np.exp(1j * W * fb.fil[0]["N"]/2.)

        if self.cmbShowH.currentIndex() == 1: # show real part of H
            H = self.H_c.real
            H_str = r'$\Re \{H(\mathrm{e}^{\mathrm{j} \Omega})\}$'
        elif self.cmbShowH.currentIndex() == 2: # show imag. part of H
            H = self.H_c.imag
            H_str = r'$\Im \{H(\mathrm{e}^{\mathrm{j} \Omega})\}$'
        else: # show magnitude of H
            H = abs(self.H_c)
            H_str = r'$|H(\mathrm{e}^{\mathrm{j} \Omega})|$'

        # clear the axes and (re)draw the plot
        #
        self.ax.clear()

        #================ Main Plotting Routine =========================

        if self.unitA == 'dB':
            A_lim = [-self.A_SB -10, self.A_PB +1]
            self.H_plt = 20*np.log10(abs(H))
            self.ax.set_ylabel(H_str + ' in dB ' + r'$\rightarrow$')

        elif self.unitA == 'V': #  'lin'
            A_lim = [10**((-self.A_SB-10)/20), 10**((self.A_PB+1)/20)]
            self.H_plt = H
            self.ax.set_ylabel(H_str +' in V ' + r'$\rightarrow $')
        else: # unit is W
            A_lim = [10**((-self.A_SB-10)/10), 10**((self.A_PB+0.5)/10)]
            self.H_plt = H * H
            self.ax.set_ylabel(H_str + ' in W ' + r'$\rightarrow $')

        plt_lim = f_lim + A_lim

        #-----------------------------------------------------------
        self.ax.plot(self.F, self.H_plt, lw = fb.gD['rc']['lw'])
        #-----------------------------------------------------------
        self.ax_bounds = [self.ax.get_ybound()[0], self.ax.get_ybound()[1]]#, self.ax.get] 

        self.ax.axis(plt_lim)

        if self.specs: self.plotSpecLimits(specAxes = self.ax)

        self.ax.set_title(r'Magnitude Frequency Response')
        self.ax.set_xlabel(fb.rcFDA['plt_fLabel'])

        self.mplwidget.redraw()

    def draw_phase(self):
        self.phase = self.chkPhase.isChecked()
        if self.phase:
            self.ax_p = self.ax.twinx() # second axes system with same x-axis for phase

            phi_str = r'$\angle H(\mathrm{e}^{\mathrm{j} \Omega})$'
            if fb.rcFDA['plt_phiUnit'] == 'rad':
                phi_str += ' in rad ' + r'$\rightarrow $'
                scale = 1.
            elif fb.rcFDA['plt_phiUnit'] == 'rad/pi':
                phi_str += ' in rad' + r'$ / \pi \;\rightarrow $'
                scale = 1./ np.pi
            else:
                phi_str += ' in deg ' + r'$\rightarrow $'
                scale = 180./np.pi
    
            self.ax_p.plot(self.F,np.unwrap(np.angle(self.H_c))*scale,
                               'b--', lw = fb.gD['rc']['lw'])
            self.ax_p.set_ylabel(phi_str, color='blue')
#            nbins = len(self.ax.get_yticks())
#            self.ax_p.locator_params(axis = 'y', nbins = nbins)
#
#            self.ax_p.set_yticks(np.linspace(self.ax_p.get_ybound()[0], 
#                                             self.ax_p.get_ybound()[1],  
#                                             len(self.ax.get_yticks())-1))
            
        else:
            try:
                self.mplwidget.fig.delaxes(self.ax_p)
            except (KeyError, AttributeError):
                pass
        self.draw()

    def draw_inset(self):
        """
        Construct / destruct second axes for an inset second plot
        """
        # TODO:  try   ax1 = zoomed_inset_axes(ax, 6, loc=1) # zoom = 6
        # TODO: use sca(a) # Set the current axes to be a and return a
        self.inset = self.chkInset.isChecked()
        if self.DEBUG:
            print(self.mplwidget.fig.axes) # list of axes in Figure
            for ax in self.mplwidget.fig.axes:
                print(ax)

        if self.inset:
            #  Add an axes at position rect [left, bottom, width, height]:
            self.ax_i = self.mplwidget.fig.add_axes([0.65, 0.61, .3, .3])
            self.ax_i.clear() # clear old plot and specs
            if self.specs:
                self.plotSpecLimits(specAxes = self.ax_i)
            self.ax_i.plot(self.F, self.H_plt, lw = fb.gD['rc']['lw'])
        else:
            try:
                #remove ax_i from the figure and update the current axes
                self.mplwidget.fig.delaxes(self.ax_i)
            except AttributeError:
                pass
        self.draw()
#        self.mplwidget.redraw()

#------------------------------------------------------------------------------

def main():
    app = QtGui.QApplication(sys.argv)
    form = PlotHf()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
