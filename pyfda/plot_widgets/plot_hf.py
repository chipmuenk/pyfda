# -*- coding: utf-8 -*-
"""
Plotting widget |H(f)|

Author: Christian Muenker 2015
"""
from __future__ import print_function, division, unicode_literals, absolute_import

from PyQt4 import QtGui
import numpy as np
import scipy.signal as sig
from matplotlib.patches import Rectangle
from matplotlib import rcParams
#import matplotlib.ticker

import pyfda.filterbroker as fb
import pyfda.pyfda_rc as rc
from pyfda.plot_widgets.plot_utils import MplWidget

class PlotHf(QtGui.QWidget):

# TODO: inset plot should have useful preset range, depending on filter type,
#       stop band or pass band should be selectable as well as lin / log scale
# TODO: position and size of inset plot should be selectable
# TODO: draw_phase is only triggered by clicking the button; when frequency range
#        is switched to +/- 1/2 the display doesn't follow


    def __init__(self, parent): 
        super(PlotHf, self).__init__(parent)

        modes = ['| H |', 're{H}', 'im{H}']
        self.cmbShowH = QtGui.QComboBox(self)
        self.cmbShowH.addItems(modes)
        self.cmbShowH.setObjectName("cmbUnitsH")
        self.cmbShowH.setToolTip("Show magnitude, real / imag. part of H or H \n"
        "without linear phase (acausal system).")
        self.cmbShowH.setCurrentIndex(0)

        self.lblIn = QtGui.QLabel("in")

        units = ['dB', 'V', 'W', 'Auto']
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

        #----------------------------------------------------------------------
        # mplwidget
        #----------------------------------------------------------------------
        self.mplwidget = MplWidget(self)

        self.mplwidget.layVMainMpl.addLayout(self.layHChkBoxes)

        self.setLayout(self.mplwidget.layVMainMpl)

        # make this the central widget, taking all available space:
#        self.setCentralWidget(self.mplwidget)


        self.init_axes()

        self.draw() # calculate and draw |H(f)|

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.cmbUnitsA.currentIndexChanged.connect(self.draw)
        self.cmbShowH.currentIndexChanged.connect(self.draw)

        self.chkLinphase.clicked.connect(self.draw)
        self.cmbInset.currentIndexChanged.connect(self.draw_inset)

        self.chkSpecs.clicked.connect(self.draw)
        self.chkPhase.clicked.connect(self.draw_phase)

#------------------------------------------------------------------------------
    def init_axes(self):
        """
        Initialize and clear the axes
        """
#        self.ax = self.mplwidget.ax
        self.ax = self.mplwidget.fig.add_subplot(111)
        self.ax.clear()

#------------------------------------------------------------------------------
    def plot_spec_limits(self, specAxes):
        """
        Plot the specifications limits (F_SB, A_SB, ...) as lines and as
        hatched areas.
        """

        def dB(lin):
            return 20 * np.log10(lin)

        def _plot_specs():
            # upper limits:
            ax.plot(F_lim_upl, A_lim_upl, F_lim_upc, A_lim_upc, F_lim_upr, A_lim_upr, **line_params)
            if A_lim_upl:
                ax.fill_between(F_lim_upl, max(A_lim_upl), A_lim_upl, **fill_params)
            if A_lim_upc:
                ax.fill_between(F_lim_upc, max(A_lim_upc), A_lim_upc, **fill_params)
            if A_lim_upr:
                ax.fill_between(F_lim_upr, max(A_lim_upr), A_lim_upr, **fill_params)
            # lower limits:
            ax.plot(F_lim_lol, A_lim_lol, F_lim_loc, A_lim_loc, F_lim_lor, A_lim_lor, **line_params)
            if A_lim_lol:
                ax.fill_between(F_lim_lol, min(A_lim_lol), A_lim_lol, **fill_params)
            if A_lim_loc:
                ax.fill_between(F_lim_loc, min(A_lim_loc), A_lim_loc, **fill_params)
            if A_lim_lor:
                ax.fill_between(F_lim_lor, min(A_lim_lor), A_lim_lor, **fill_params)


#        fc = (0.8,0.8,0.8) # color for shaded areas
        fill_params = {'facecolor':'none','hatch':'/', 'edgecolor':rcParams['figure.edgecolor'], 'lw':0.0}
        line_params = {'linewidth':1.0, 'color':'blue', 'linestyle':'--'}
        ax = specAxes

        if self.unitA == 'V':
            exp = 1.
        elif self.unitA == 'W':
            exp = 2.

        if self.unitA == 'dB':
            if fb.fil[0]['ft'] == "FIR":
                A_PB_max  = dB(1 + self.A_PB)
                A_PB2_max = dB(1 + self.A_PB2)
            else: # IIR dB
                A_PB_max = A_PB2_max = 0

            A_PB_min  = dB(1 - self.A_PB)
            A_PB2_min = dB(1 - self.A_PB2)
            A_PB_minx = min(A_PB_min, A_PB2_min) - 5
            A_PB_maxx = max(A_PB_max, A_PB2_max) + 5

            A_SB  = dB(self.A_SB)
            A_SB2 = dB(self.A_SB2)
            A_SB_maxx = max(A_SB, A_SB2) + 10
        else: # 'V' or 'W'
            if fb.fil[0]['ft'] == "FIR":
                A_PB_max  = (1 + self.A_PB)**exp
                A_PB2_max = (1 + self.A_PB2)**exp
            else: # IIR lin
                A_PB_max = A_PB2_max = 1

            A_PB_min  = (1 - self.A_PB)**exp
            A_PB2_min = (1 - self.A_PB)**exp
            A_PB_minx = A_PB_min  / 1.05
            A_PB_maxx = max(A_PB_max, A_PB2_max) * 1.05

            A_SB  = self.A_SB ** exp
            A_SB2 = self.A_SB2 ** exp
            A_SB_maxx = A_PB_min / 10.

        F_max = self.f_S/2
        F_PB  = self.F_PB
        F_SB  = fb.fil[0]['F_SB'] * self.f_S
        F_SB2 = fb.fil[0]['F_SB2'] * self.f_S
        F_PB2 = fb.fil[0]['F_PB2'] * self.f_S

        F_lim_upl = F_lim_lol = [] # left side limits, lower and upper
        A_lim_upl = A_lim_lol = []

        F_lim_upc = F_lim_loc = [] # center limits, lower and upper
        A_lim_upc = A_lim_loc = []

        F_lim_upr = F_lim_lor = [] # right side limits, lower and upper
        A_lim_upr = A_lim_lor = []

        if fb.fil[0]['rt'] == 'LP':
            F_lim_upl = [0,        F_PB,     F_PB]
            A_lim_upl = [A_PB_max, A_PB_max, A_PB_maxx]
            F_lim_lol = F_lim_upl
            A_lim_lol = [A_PB_min, A_PB_min, A_PB_minx]

            F_lim_upr = [F_SB,     F_SB, F_max]
            A_lim_upr = [A_SB_maxx, A_SB, A_SB]

        if fb.fil[0]['rt'] == 'HP':
            F_lim_upl = [0,    F_SB, F_SB]
            A_lim_upl = [A_SB, A_SB, A_SB_maxx]

            F_lim_upr = [F_PB,      F_PB,     F_max]
            A_lim_upr = [A_PB_maxx, A_PB_max, A_PB_max]
            F_lim_lor = F_lim_upr
            A_lim_lor = [A_PB_minx, A_PB_min, A_PB_min]

        if fb.fil[0]['rt'] == 'BS':
            F_lim_upl = [0,        F_PB,     F_PB]
            A_lim_upl = [A_PB_max, A_PB_max, A_PB_maxx]
            F_lim_lol = F_lim_upl
            A_lim_lol = [A_PB_min, A_PB_min, A_PB_minx]

            F_lim_upc = [F_SB, F_SB, F_SB2, F_SB2]
            A_lim_upc = [A_SB_maxx, A_SB, A_SB,  A_SB_maxx]

            F_lim_upr = [F_PB2, F_PB2, F_max]
            A_lim_upr = [A_PB_maxx, A_PB2_max, A_PB2_max]
            F_lim_lor = F_lim_upr
            A_lim_lor = [A_PB_minx, A_PB2_min, A_PB2_min]

        if fb.fil[0]['rt'] in {"BP", "HIL"}:
            F_lim_upl = [0,    F_SB, F_SB]
            A_lim_upl = [A_SB, A_SB, A_SB_maxx]

            F_lim_upc = [F_PB,      F_PB,     F_PB2,    F_PB2]
            A_lim_upc = [A_PB_maxx, A_PB_max, A_PB_max, A_PB_maxx]
            F_lim_loc = F_lim_upc
            A_lim_loc = [A_PB_minx, A_PB_min, A_PB_min, A_PB_minx]

            F_lim_upr = [F_SB2,    F_SB2, F_max]
            A_lim_upr = [A_SB_maxx, A_SB2, A_SB2]

        F_lim_upr = np.array(F_lim_upr)
        F_lim_lor = np.array(F_lim_lor)
        F_lim_upl = np.array(F_lim_upl)
        F_lim_lol = np.array(F_lim_lol)
        F_lim_upc = np.array(F_lim_upc)
        F_lim_loc = np.array(F_lim_loc)

        _plot_specs() # plot specs in the range 0 ... f_S/2

        if fb.fil[0]['freqSpecsRangeType'] != 'half':
            # add plot limits for other half of the spectrum
            if fb.fil[0]['freqSpecsRangeType'] == 'sym': # frequency axis +/- f_S/2
                F_lim_upl = -F_lim_upl
                F_lim_lol = -F_lim_lol
                F_lim_upc = -F_lim_upc
                F_lim_loc = -F_lim_loc
                F_lim_upr = -F_lim_upr
                F_lim_lor = -F_lim_lor
            else: # -> 'whole'
                F_lim_upl = self.f_S - F_lim_upl
                F_lim_lol = self.f_S - F_lim_lol
                F_lim_upc = self.f_S - F_lim_upc
                F_lim_loc = self.f_S - F_lim_loc
                F_lim_upr = self.f_S - F_lim_upr
                F_lim_lor = self.f_S - F_lim_lor

            _plot_specs()

#------------------------------------------------------------------------------
    def draw_inset(self):
        """
        Construct / destruct second axes for an inset second plot
        """
        # TODO:  try   ax1 = zoomed_inset_axes(ax, 6, loc=1) # zoom = 6
        # TODO: choose size & position of inset, maybe dependent on filter type
        #        or specs (i.e. where is passband etc.)

# DEBUG
#            print(self.cmbInset.currentIndex(), self.mplwidget.fig.axes) # list of axes in Figure
#            for ax in self.mplwidget.fig.axes:
#                print(ax)
#                print("cmbInset, inset_idx:",self.cmbInset.currentIndex(), self.inset_idx)

        if self.cmbInset.currentIndex() > 0:
            if self.inset_idx == 0:
                # Inset was turned off before, create a new one
                #  Add an axes at position rect [left, bottom, width, height]:
                self.ax_i = self.mplwidget.fig.add_axes([0.65, 0.61, .3, .3])
                self.ax_i.clear() # clear old plot and specs

                # draw an opaque background with the extent of the inset plot:
#                self.ax_i.patch.set_facecolor('green') # without label area
#                self.mplwidget.fig.patch.set_facecolor('green') # whole figure
                extent = self.mplwidget.get_full_extent(self.ax_i, pad = 0.0)
                # Transform this back to figure coordinates - otherwise, it
                #  won't behave correctly when the size of the plot is changed:
                extent = extent.transformed(self.mplwidget.fig.transFigure.inverted())
                rect = Rectangle((extent.xmin, extent.ymin), extent.width,
                        extent.height, facecolor=rcParams['figure.facecolor'], edgecolor='none',
                        transform=self.mplwidget.fig.transFigure, zorder=-1)
                self.ax_i.patches.append(rect)

                self.ax_i.set_xlim(fb.fil[0]['freqSpecsRange'])
                self.ax_i.plot(self.F, self.H_plt)

            if self.cmbInset.currentIndex() == 1: # edit / navigate inset
                self.ax_i.set_navigate(True)
                self.ax.set_navigate(False)
                if self.specs:
                    self.plot_spec_limits(specAxes = self.ax_i)
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
    def draw_phase(self):
        if self.chkPhase.isChecked():
            self.ax_p = self.ax.twinx() # second axes system with same x-axis for phase
#
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
                
            # replace nan and inf by finite values, otherwise np.unwrap yields
            # an array full of nans
            phi = np.angle(np.nan_to_num(self.H_c)) 
        #-----------------------------------------------------------
            self.ax_p.plot(self.F,np.unwrap(phi)*scale,
                               'b--', label = "Phase")
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

#------------------------------------------------------------------------------

    def calc_hf(self):
        """
        (Re-)Calculate the complex frequency response H(f)
        """

#        whole = fb.fil[0]['freqSpecsRangeType'] != 'half'

        # calculate H_cplx(W) (complex) for W = 0 ... 2 pi:
        [self.W, self.H_cplx] = sig.freqz(fb.fil[0]['ba'][0], fb.fil[0]['ba'][1],
            worN = rc.params['N_FFT'], whole = True) # bb, aa, N_FFT, 0 ... 2 pi

#------------------------------------------------------------------------------
    def draw(self):
        """
        Re-calculate |H(f)| and draw the figure
        """
        if self.mplwidget.mplToolbar.enable_update:
            self.calc_hf()
            self.update_view()

#------------------------------------------------------------------------------
    def update_view(self):
        """
        Draw the figure with new limits, scale etc without recalculating H(f)
        """
        if np.all(self.W) is None: # H(f) has not been calculated yet
            self.calc_hf()

        if self.cmbUnitsA.currentText() == 'Auto':
            self.unitA = fb.fil[0]['amp_specs_unit']
        else:
            self.unitA = self.cmbUnitsA.currentText()

        # Linphase settings only makes sense for amplitude plot
        self.chkLinphase.setCheckable(self.unitA == 'V')
        self.chkLinphase.setEnabled(self.unitA == 'V')
        self.lblLinphase.setEnabled(self.unitA == 'V')

        self.specs = self.chkSpecs.isChecked()
        self.phase = self.chkPhase.isChecked()
        self.linphase = self.chkLinphase.isChecked()

        self.f_S  = fb.fil[0]['f_S']
        self.F_PB = fb.fil[0]['F_PB'] * self.f_S
        self.F_SB = fb.fil[0]['F_SB'] * self.f_S

        self.A_PB  = fb.fil[0]['A_PB']
        self.A_PB2 = fb.fil[0]['A_PB2']
        self.A_SB  = fb.fil[0]['A_SB']
        self.A_SB2 = fb.fil[0]['A_SB2']

        f_lim = fb.fil[0]['freqSpecsRange']

        # shift, scale and select frequency range to be displayed:
        # W -> F, H_cplx -> H_c
        self.H_c = self.H_cplx
        self.F = self.W / (2 * np.pi) * self.f_S

        if fb.fil[0]['freqSpecsRangeType'] == 'sym':
            self.H_c = np.fft.fftshift(self.H_cplx)
            self.F -= self.f_S/2.
        elif fb.fil[0]['freqSpecsRangeType'] == 'half':
            self.H_c = self.H_cplx[0:rc.params['N_FFT']//2]
            self.F = self.F[0:rc.params['N_FFT']//2]

        # now calculate mag / real / imaginary part of H_c:
        if self.linphase: # remove the linear phase
            self.H_c = self.H_c * np.exp(1j * self.W[0:len(self.F)] * fb.fil[0]["N"]/2.)

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
        if self.ax.get_navigate():

            self.ax.clear()

            #================ Main Plotting Routine =========================

            if self.unitA == 'dB':
                A_lim = [20*np.log10(self.A_SB) -10, 20*np.log10(1+self.A_PB) +1]
                self.H_plt = 20*np.log10(abs(H))
                H_str += ' in dB ' + r'$\rightarrow$'
            elif self.unitA == 'V': #  'lin'
                A_lim = [0, (self.A_PB+1)]
                self.H_plt = H
                H_str +=' in V ' + r'$\rightarrow $'
                self.ax.axhline(linewidth=1, color='k') # horizontal line at 0
            else: # unit is W
                A_lim = [0, (1 + self.A_PB)**2.]
                self.H_plt = H * H.conj()
                H_str += ' in W ' + r'$\rightarrow $'

            #-----------------------------------------------------------
            self.ax.plot(self.F, self.H_plt, label = 'H(f)')
            #-----------------------------------------------------------
       #     self.ax_bounds = [self.ax.get_ybound()[0], self.ax.get_ybound()[1]]#, self.ax.get]
            self.ax.set_xlim(f_lim)
            self.ax.set_ylim(A_lim)

            if self.specs: self.plot_spec_limits(specAxes = self.ax)

            self.ax.set_title(r'Magnitude Frequency Response')
            self.ax.set_xlabel(fb.fil[0]['plt_fLabel'])
            self.ax.set_ylabel(H_str)

        self.mplwidget.redraw()
        
       


#------------------------------------------------------------------------------

def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    mainw = PlotHf()
    app.setActiveWindow(mainw) 
    mainw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
