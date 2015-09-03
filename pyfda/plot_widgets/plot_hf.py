# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals, absolute_import

from PyQt4 import QtGui
import numpy as np
import scipy.signal as sig
from matplotlib.patches import Rectangle
#import matplotlib.ticker

# add path to libraries one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    import sys, os
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import pyfda.filterbroker as fb
from pyfda.plot_widgets.plot_utils import MplWidget

class PlotHf(QtGui.QMainWindow):

# TODO: inset plot should have useful preset range, depending on filter type,
#       stop band or pass band should be selectable as well as lin / log scale
# TODO: position and size of inset plot should be selectable


    def __init__(self, parent = None, DEBUG = False): # default parent = None -> top Window
        super(PlotHf, self).__init__(parent) # initialize QWidget base class
#        QtGui.QMainWindow.__init__(self) # alternative syntax

        self.DEBUG = DEBUG

        modes = ['| H |', 're{H}', 'im{H}']
        self.cmbShowH = QtGui.QComboBox(self)
        self.cmbShowH.addItems(modes)
        self.cmbShowH.setObjectName("cmbUnitsH")
        self.cmbShowH.setToolTip("Show magnitude, real / imag. part of H or H \n"
        "without linear phase (acausal system).")
        self.cmbShowH.setCurrentIndex(0)

        self.lblIn = QtGui.QLabel("in")

        units = ["dB", "V", "W"]
        self.cmbUnitsA = QtGui.QComboBox(self)
        self.cmbUnitsA.addItems(units)
        self.cmbUnitsA.setObjectName("cmbUnitsA")
        self.cmbUnitsA.setToolTip("Set unit for y-axis:\n"
        "dB is attenuation (positive values)\nV and W are less than 1.")
        self.cmbUnitsA.setCurrentIndex(0)

        self.cmbShowH.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbUnitsA.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        self.lblLinphase = QtGui.QLabel("Acausal system")
        self.chkLinphase = QtGui.QCheckBox()
        self.chkLinphase.setToolTip("Remove linear phase according to filter order.\n"
           "Attention: this makes no sense for a non-linear phase system!")

        self.lblInset = QtGui.QLabel("Inset")

        self.cmbInset = QtGui.QComboBox(self)
        self.cmbInset.addItems(['off', 'edit', 'fixed'])
        self.cmbInset.setObjectName("cmbInset")
        self.cmbInset.setToolTip("Display/edit second inset plot")
        self.cmbInset.setCurrentIndex(0)
        self.inset_idx = 0 # store previous index for comparison

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
        self.layHChkBoxes.addWidget(self.cmbInset)
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

#        self.mplwidget.setFocus()
        # make this the central widget, taking all available space:
        self.setCentralWidget(self.mplwidget)

        self.initAxes()

        self.draw() # calculate and draw |H(f)|

#        #=============================================
#        # Signals & Slots
#        #=============================================
        self.cmbUnitsA.currentIndexChanged.connect(self.draw)
        self.cmbShowH.currentIndexChanged.connect(self.draw)

        self.chkLinphase.clicked.connect(self.draw)
        self.cmbInset.currentIndexChanged.connect(self.draw_inset)

        self.chkSpecs.clicked.connect(self.draw)
        self.chkPhase.clicked.connect(self.draw_phase)

    def initAxes(self):
        """Initialize and clear the axes
        """
#        self.ax = self.mplwidget.ax
        self.ax = self.mplwidget.fig.add_subplot(111)
        self.ax.clear()

    def plotSpecLimits(self, specAxes):
        """
        Plot the specifications limits (F_SB, A_SB, ...) as lines and as
        hatched areas.
        """
#        fc = (0.8,0.8,0.8) # color for shaded areas
        fill_params = {'facecolor':'none','hatch':'/', 'edgecolor':'k', 'lw':0.0}
        line_params = {'linewidth':1.0, 'color':'blue', 'linestyle':'--'}
        ax = specAxes

        # extract from filterTree the parameters that are actually used
#        myParams = fb.filTree[rt][ft][dm][fo]['par']
#        freqParams = [l for l in myParams if l[0] == 'F']

        if fb.fil[0]['ft'] == "FIR":
            A_PB_max = self.A_PB # 20*log10(1+del_PB)
            A_PB2_max = self.A_PB2
        else: # IIR log
            A_PB_max = A_PB2_max = 0

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

        y_min =  A_PB_minx
        y_max = ax.get_ylim()[1]

        F_lim_lor = []
        A_lim_lor = []

        if fb.fil[0]['rt'] == 'LP':
            F_lim_up = [0,        F_SB,     F_SB, F_max]
            A_lim_up = [A_PB_max, A_PB_max, A_SB, A_SB]
            F_lim_lo = [0,        F_PB,     F_PB]
            A_lim_lo = [A_PB_min, A_PB_min, A_PB_minx]

        if fb.fil[0]['rt'] == 'HP':
            F_lim_up = [0,    F_SB, F_SB,     F_max]
            A_lim_up = [A_SB, A_SB, A_PB_max, A_PB_max]
            F_lim_lo = [F_PB,      F_PB,     F_max]
            A_lim_lo = [A_PB_minx, A_PB_min, A_PB_min]

        if fb.fil[0]['rt'] == 'BS':
            F_lim_up = [0,        F_SB,     F_SB, F_SB2, F_SB2,     F_max]
            A_lim_up = [A_PB_max, A_PB_max, A_SB, A_SB,  A_PB2_max, A_PB2_max]
            # lower limits left:
            F_lim_lo = [0,        F_PB,     F_PB]
            A_lim_lo = [A_PB_min, A_PB_min, A_PB_minx]
            # lower limits right:
            F_lim_lor = [F_PB2, F_PB2, F_max]
            A_lim_lor = [A_PB_minx, A_PB2_min, A_PB2_min]

        if fb.fil[0]['rt'] in {"BP", "HIL"}:
            F_lim_up = [0,    F_SB, F_SB,     F_SB2,    F_SB2, F_max]
            A_lim_up = [A_SB, A_SB, A_PB_max, A_PB_max, A_SB2, A_SB2]
            F_lim_lo = [F_PB,      F_PB,     F_PB2,    F_PB2]
            A_lim_lo = [A_PB_minx, A_PB_min, A_PB_min, A_PB_minx]

        F_lim_up = np.array(F_lim_up)
        F_lim_lo = np.array(F_lim_lo)
        F_lim_lor = np.array(F_lim_lor)

        # upper limits:
        ax.plot(F_lim_up, A_lim_up, **line_params)
        ax.fill_between(F_lim_up, y_max, A_lim_up, **fill_params)
        # lower limits:
        ax.plot(F_lim_lo, A_lim_lo, F_lim_lor, A_lim_lor, **line_params)
        ax.fill_between(F_lim_lo, y_min, A_lim_lo, **fill_params)
        ax.fill_between(F_lim_lor, y_min, A_lim_lor, **fill_params)

        if fb.fil[0]['freqSpecsRangeType'] != 'half': # frequency axis +/- f_S/2
            # plot limits for other half of the spectrum
            if fb.fil[0]['freqSpecsRangeType'] == 'sym': # frequency axis +/- f_S/2
                F_lim_up = -F_lim_up
                F_lim_lo = -F_lim_lo
                F_lim_lor = -F_lim_lor
            else: # -> 'whole'
                F_lim_up = self.f_S - F_lim_up
                F_lim_lo = self.f_S - F_lim_lo
                F_lim_lor = self.f_S - F_lim_lor
            # upper limits:
            ax.plot(F_lim_up, A_lim_up, **line_params)
            ax.fill_between(F_lim_up, y_max, A_lim_up, **fill_params)
            # lower limits:
            ax.plot(F_lim_lo, A_lim_lo, F_lim_lor, A_lim_lor, **line_params)
            ax.fill_between(F_lim_lo, y_min, A_lim_lo, **fill_params)
            ax.fill_between(F_lim_lor, y_min, A_lim_lor, **fill_params)

    def draw(self):
        if self.mplwidget.mplToolbar.enable_update:
            self.draw_hf()

    def draw_hf(self):
        """
        Re-calculate |H(f)| and draw the figure
        """
        self.unitA = self.cmbUnitsA.currentText()

        # Linphase settings only makes sense for amplitude plot
        self.chkLinphase.setCheckable(self.unitA == 'V')
        self.chkLinphase.setEnabled(self.unitA == 'V')
        self.lblLinphase.setEnabled(self.unitA == 'V')

        self.specs = self.chkSpecs.isChecked()
        self.phase = self.chkPhase.isChecked()
        self.linphase = self.chkLinphase.isChecked()

        self.bb = fb.fil[0]['ba'][0]
        self.aa = fb.fil[0]['ba'][1]

        self.f_S  = fb.fil[0]['f_S']
        self.F_PB = fb.fil[0]['F_PB'] * self.f_S
        self.F_SB = fb.fil[0]['F_SB'] * self.f_S

        self.A_PB  = fb.fil[0]['A_PB']
        self.A_PB2 = fb.fil[0]['A_PB2']
        self.A_SB  = fb.fil[0]['A_SB']
        self.A_SB2 = fb.fil[0]['A_SB2']

        f_lim = fb.fil[0]['freqSpecsRange']
        wholeF = fb.fil[0]['freqSpecsRangeType'] != 'half'


        if self.DEBUG:
            print("--- plotHf.draw() --- ")
            print("b, a = ", self.bb, self.aa)

        # calculate H_c(W) (complex) for W = 0 ... pi:
        [W, self.H_c] = sig.freqz(self.bb, self.aa, worN = fb.gD['N_FFT'],
            whole = wholeF)
        self.F = W / (2 * np.pi) * self.f_S

        if fb.fil[0]['freqSpecsRangeType'] == 'sym':
            self.H_c = np.fft.fftshift(self.H_c)
            self.F = self.F - self.f_S/2.

        if self.linphase: # remove the linear phase
            self.H_c = self.H_c * np.exp(1j * W * fb.fil[0]["N"]/2.)

        if self.cmbShowH.currentIndex() == 0: # show magnitude of H
            H = abs(self.H_c)
            H_str = r'$|H(\mathrm{e}^{\mathrm{j} \Omega})|$'
        elif self.cmbShowH.currentIndex() == 1: # show real part of H
            H = self.H_c.real
            H_str = r'$\Re \{H(\mathrm{e}^{\mathrm{j} \Omega})\}$'
        else:  # show imag. part of H
            H = self.H_c.imag
            H_str = r'$\Im \{H(\mathrm{e}^{\mathrm{j} \Omega})\}$'


        # clear the axes and (re)draw the plot
        #
        if self.ax.get_navigate():

            self.ax.clear()

            #================ Main Plotting Routine =========================

            if self.unitA == 'dB':
                A_lim = [-self.A_SB -10, self.A_PB +1]
                self.H_plt = 20*np.log10(abs(H))
                H_str += ' in dB ' + r'$\rightarrow$'
            elif self.unitA == 'V': #  'lin'
                A_lim = [10**((-self.A_SB-10)/20), 10**((self.A_PB+1)/20)]
                self.H_plt = H
                H_str +=' in V ' + r'$\rightarrow $'
                self.ax.axhline(linewidth=1, color='k') # horizontal line at 0
            else: # unit is W
                A_lim = [10**((-self.A_SB-10)/10), 10**((self.A_PB+0.5)/10)]
                self.H_plt = H * H.conj()
                H_str += ' in W ' + r'$\rightarrow $'

            plt_lim = f_lim + A_lim

            #-----------------------------------------------------------
            self.ax.plot(self.F, self.H_plt, lw = fb.gD['rc']['lw'], label = 'H(f)')
            #-----------------------------------------------------------
            self.ax_bounds = [self.ax.get_ybound()[0], self.ax.get_ybound()[1]]#, self.ax.get]

            self.ax.axis(plt_lim)

            if self.specs: self.plotSpecLimits(specAxes = self.ax)

            self.ax.set_title(r'Magnitude Frequency Response')
            self.ax.set_xlabel(fb.fil[0]['plt_fLabel'])
            self.ax.set_ylabel(H_str)

        self.mplwidget.redraw()

    def draw_phase(self):
        self.phase = self.chkPhase.isChecked()
        if self.phase:
            self.ax_p = self.ax.twinx() # second axes system with same x-axis for phase

            phi_str = r'$\angle H(\mathrm{e}^{\mathrm{j} \Omega})$'
            if fb.fil[0]['plt_phiUnit'] == 'rad':
                phi_str += ' in rad ' + r'$\rightarrow $'
                scale = 1.
            elif fb.fil[0]['plt_phiUnit'] == 'rad/pi':
                phi_str += ' in rad' + r'$ / \pi \;\rightarrow $'
                scale = 1./ np.pi
            else:
                phi_str += ' in deg ' + r'$\rightarrow $'
                scale = 180./np.pi
        #-----------------------------------------------------------
            self.ax_p.plot(self.F,np.unwrap(np.angle(self.H_c))*scale,
                               'b--', lw = fb.gD['rc']['lw'], label = "Phase")
        #-----------------------------------------------------------
            self.ax_p.set_ylabel(phi_str, color='blue')
            nbins = len(self.ax.get_yticks()) # number of ticks on main y-axis
            # http://stackoverflow.com/questions/28692608/align-grid-lines-on-two-plots
            # http://stackoverflow.com/questions/3654619/matplotlib-multiple-y-axes-grid-lines-applied-to-both
            # http://stackoverflow.com/questions/20243683/matplotlib-align-twinx-tick-marks
            # manual setting:
            #self.ax_p.set_yticks( np.linspace(self.ax_p.get_ylim()[0],self.ax_p.get_ylim()[1],nbins) )
            #ax1.set_yticks(np.linspace(ax1.get_ybound()[0], ax1.get_ybound()[1], 5))
            #ax2.set_yticks(np.linspace(ax2.get_ybound()[0], ax2.get_ybound()[1], 5))
            #http://stackoverflow.com/questions/3654619/matplotlib-multiple-y-axes-grid-lines-applied-to-both
            
            # use helper functions from matplotlib.ticker:
            #   MaxNLocator: set no more than nbins + 1 ticks
            #self.ax_p.yaxis.set_major_locator( matplotlib.ticker.MaxNLocator(nbins = nbins) )
            # further options: integer = False,
            #                   prune = [‘lower’ | ‘upper’ | ‘both’ | None] Remove edge ticks
            #   AutoLocator:
            #self.ax_p.yaxis.set_major_locator( matplotlib.ticker.AutoLocator() )
            #   LinearLocator:
            #self.ax_p.yaxis.set_major_locator( matplotlib.ticker.LinearLocator(numticks = nbins -1 ) )

#            self.ax_p.locator_params(axis = 'y', nbins = nbins)
#
#            self.ax_p.set_yticks(np.linspace(self.ax_p.get_ybound()[0],
#                                             self.ax_p.get_ybound()[1],
#                                             len(self.ax.get_yticks())-1))

            #N = source_ax.xaxis.get_major_ticks()
            #target_ax.xaxis.set_major_locator(LinearLocator(N))
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
        # TODO: choose size & position of inset, maybe dependent on filter type
        #        or specs (i.e. where is passband etc.)
        if self.DEBUG:
            print(self.cmbInset.currentIndex(), self.mplwidget.fig.axes) # list of axes in Figure
            for ax in self.mplwidget.fig.axes:
                print(ax)
                print("cmbInset, inset_idx:",self.cmbInset.currentIndex(), self.inset_idx)
        if self.cmbInset.currentIndex() > 0:
            if self.inset_idx == 0:
                # Inset was turned off before, create a new one
                #  Add an axes at position rect [left, bottom, width, height]:
                self.ax_i = self.mplwidget.fig.add_axes([0.65, 0.61, .3, .3])
                self.ax_i.clear() # clear old plot and specs

                # draw an opaque background with the extent of the inset plot:
#                self.ax_i.patch.set_facecolor('green') # without label area
#                self.mplwidget.fig.patch.set_facecolor('green') # whole figure
                extent = self.mplwidget.full_extent(self.ax_i, pad = 0.0)
                # Transform this back to figure coordinates - otherwise, it
                #  won't behave correctly when the size of the plot is changed:
                extent = extent.transformed(self.mplwidget.fig.transFigure.inverted())
                rect = Rectangle((extent.xmin, extent.ymin), extent.width,
                        extent.height, facecolor=(1.0,1.0,1.0), edgecolor='none',
                        transform=self.mplwidget.fig.transFigure, zorder=-1)
                self.ax_i.patches.append(rect)

                self.ax_i.set_xlim(fb.fil[0]['freqSpecsRange'])
                self.ax_i.plot(self.F, self.H_plt, lw = fb.gD['rc']['lw'])

            if self.cmbInset.currentIndex() == 1: # edit / navigate inset
                self.ax_i.set_navigate(True)
                self.ax.set_navigate(False)
                if self.specs:
                    self.plotSpecLimits(specAxes = self.ax_i)
            else: # edit / navigate main plot
                self.ax_i.set_navigate(False)
                self.ax.set_navigate(True)
        else:  # inset has been turned off, delete it
            self.ax.set_navigate(True)
            try:
                #remove ax_i from the figure
                self.mplwidget.fig.delaxes(self.ax_i)
            except AttributeError:
                pass

        self.inset_idx = self.cmbInset.currentIndex() # update index
        self.draw()


#------------------------------------------------------------------------------

def main():
    app = QtGui.QApplication(sys.argv)
    form = PlotHf()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
