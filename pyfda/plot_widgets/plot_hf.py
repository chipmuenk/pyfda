# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
The ``Plot_Hf`` class constructs the widget to plot the magnitude
frequency response \|H(f)\| of the filter either in linear or logarithmic
scale. Optionally, the magnitude specifications and the phase 
can be overlayed.
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import logging
logger = logging.getLogger(__name__)

from ..compat import (QCheckBox, QWidget, QComboBox, QLabel, QHBoxLayout, QFrame, 
                      pyqtSlot, pyqtSignal)

import numpy as np
from matplotlib.patches import Rectangle
from matplotlib import rcParams
#import matplotlib.ticker

import pyfda.filterbroker as fb
from pyfda.pyfda_rc import params
from pyfda.plot_widgets.mpl_widget import MplWidget
from pyfda.pyfda_lib import calc_Hcomplex

class Plot_Hf(QWidget):
    """
    Widget for plotting \|H(f)\|, frequency specs and the phase
    """
    # incoming, connected in sender widget (locally connected to self.process_sig_rx() )
    sig_rx = pyqtSignal(object)

    def __init__(self, parent): 
        super(Plot_Hf, self).__init__(parent)
        self.data_changed = True   # flag whether plot needs to be updated
        self.ui_changed = True   # flag whether plot needs to be updated        
        self.needs_redraw = True # flag whether plot needs to be redrawn
        self.tool_tip = "Magnitude and phase frequency response"
        self.tab_label = "|H(f)|"
        self._construct_ui()

#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the navigation toolbar and from sig_rx
        """
        logger.debug("Processing {0} | needs_draw = {1}, visible = {2}"\
                     .format(dict_sig, self.data_changed, self.isVisible()))
        if self.isVisible():
            if 'data_changed' in dict_sig or 'specs_changed' in dict_sig\
                    or 'home' in dict_sig or self.data_changed:
                self.draw()
                self.data_changed = False
                self.view_changed = False
                self.ui_changed = False
            if 'view_changed' in dict_sig or self.view_changed:
                self.update_view()
                self.view_changed = False
                self.ui_changed = False               
            if 'ui_changed' in dict_sig and dict_sig['ui_changed'] == 'resized'\
                    or self.ui_changed:
                self.redraw()
                self.ui_changed = False
        else: 
            if 'data_changed' in dict_sig or 'specs_changed' in dict_sig:
                self.data_changed = True
            if 'ui_changed' in dict_sig and dict_sig['ui_changed'] == 'resized':
                self.ui_changed = True
            if 'view_changed' in dict_sig:
                self.view_changed = True


    def _construct_ui(self):
        """
        Define and construct the subwidgets
        """
        modes = ['| H |', 're{H}', 'im{H}']
        self.cmbShowH = QComboBox(self)
        self.cmbShowH.addItems(modes)
        self.cmbShowH.setObjectName("cmbUnitsH")
        self.cmbShowH.setToolTip("Show magnitude, real / imag. part of H or H \n"
        "without linear phase (acausal system).")
        self.cmbShowH.setCurrentIndex(0)

        self.lblIn = QLabel("in", self)

        units = ['dB', 'V', 'W', 'Auto']
        self.cmbUnitsA = QComboBox(self)
        self.cmbUnitsA.addItems(units)
        self.cmbUnitsA.setObjectName("cmbUnitsA")
        self.cmbUnitsA.setToolTip("<span>Set unit for y-axis:\n"
        "dB is attenuation (positive values), V and W are gain (less than 1).</span>")
        self.cmbUnitsA.setCurrentIndex(0)

        self.cmbShowH.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbUnitsA.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.chkLinphase = QCheckBox("Zero phase", self)
        self.chkLinphase.setToolTip("<span>Subtract linear phase according to filter order.\n"
           "Attention: this makes no sense for a non-linear phase system!</span>")

        self.lblInset = QLabel("Inset", self)
        self.cmbInset = QComboBox(self)
        self.cmbInset.addItems(['off', 'edit', 'fixed'])
        self.cmbInset.setObjectName("cmbInset")
        self.cmbInset.setToolTip("Display/edit second inset plot")
        self.cmbInset.setCurrentIndex(0)
        self.inset_idx = 0 # store previous index for comparison

        self.chkSpecs = QCheckBox("Show Specs", self)
        self.chkSpecs.setChecked(False)
        self.chkSpecs.setToolTip("Display filter specs as hatched regions")

        self.chkPhase = QCheckBox("Phase", self)
        self.chkPhase.setToolTip("Overlay phase")

        #----------------------------------------------------------------------
        #               ### frmControls ###
        #
        # This widget encompasses all control subwidgets
        #----------------------------------------------------------------------
        layHControls = QHBoxLayout()
        layHControls.addStretch(10)
        layHControls.addWidget(self.cmbShowH)
        layHControls.addWidget(self.lblIn)
        layHControls.addWidget(self.cmbUnitsA)
        layHControls.addStretch(1)
        layHControls.addWidget(self.chkLinphase)
        layHControls.addStretch(1)
        layHControls.addWidget(self.lblInset)
        layHControls.addWidget(self.cmbInset)
        layHControls.addStretch(1)
        layHControls.addWidget(self.chkSpecs)
        layHControls.addStretch(1)
        layHControls.addWidget(self.chkPhase)
        layHControls.addStretch(10)

        self.frmControls = QFrame(self)
        self.frmControls.setObjectName("frmControls")
        self.frmControls.setLayout(layHControls)

        #----------------------------------------------------------------------
        #               ### mplwidget ###
        #
        # main widget, encompassing the other widgets 
        #----------------------------------------------------------------------  
        self.mplwidget = MplWidget(self)
        self.mplwidget.layVMainMpl.addWidget(self.frmControls)
        self.mplwidget.layVMainMpl.setContentsMargins(*params['wdg_margins'])
        self.setLayout(self.mplwidget.layVMainMpl)

        self.init_axes()

        self.draw() # calculate and draw |H(f)|

        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.cmbUnitsA.currentIndexChanged.connect(self.draw)
        self.cmbShowH.currentIndexChanged.connect(self.draw)

        self.chkLinphase.clicked.connect(self.draw)
        self.cmbInset.currentIndexChanged.connect(self.draw_inset)

        self.chkSpecs.clicked.connect(self.draw)
        self.chkPhase.clicked.connect(self.draw)

        self.mplwidget.mplToolbar.sig_tx.connect(self.process_sig_rx)
                
#------------------------------------------------------------------------------
    def init_axes(self):
        """
        Initialize and clear the axes
        """
#        self.ax = self.mplwidget.ax
        self.ax = self.mplwidget.fig.add_subplot(111)
        self.ax.clear()
        self.ax.get_xaxis().tick_bottom() # remove axis ticks on top
        self.ax.get_yaxis().tick_left() # remove axis ticks right

#------------------------------------------------------------------------------
    def plot_spec_limits(self, ax):
        """
        Plot the specifications limits (F_SB, A_SB, ...) as hatched areas with borders.
        """
        hatch = params['mpl_hatch']
        hatch_borders = params['mpl_hatch_border']

        def dB(lin):
            return 20 * np.log10(lin)

        def _plot_specs():
            # upper limits:
            ax.plot(F_lim_upl, A_lim_upl, F_lim_upc, A_lim_upc, F_lim_upr, A_lim_upr, **hatch_borders)
            if A_lim_upl:
                ax.fill_between(F_lim_upl, max(A_lim_upl), A_lim_upl, **hatch)
            if A_lim_upc:
                ax.fill_between(F_lim_upc, max(A_lim_upc), A_lim_upc, **hatch)
            if A_lim_upr:
                ax.fill_between(F_lim_upr, max(A_lim_upr), A_lim_upr, **hatch)
            # lower limits:
            ax.plot(F_lim_lol, A_lim_lol, F_lim_loc, A_lim_loc, F_lim_lor, A_lim_lor, **hatch_borders)
            if A_lim_lol:
                ax.fill_between(F_lim_lol, min(A_lim_lol), A_lim_lol, **hatch)
            if A_lim_loc:
                ax.fill_between(F_lim_loc, min(A_lim_loc), A_lim_loc, **hatch)
            if A_lim_lor:
                ax.fill_between(F_lim_lor, min(A_lim_lor), A_lim_lor, **hatch)

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
            A_PB2_min = (1 - self.A_PB2)**exp
            A_PB_minx = min(A_PB_min, A_PB2_min) / 1.05
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

        if fb.fil[0]['rt'] == 'BP':
            F_lim_upl = [0,    F_SB, F_SB]
            A_lim_upl = [A_SB, A_SB, A_SB_maxx]

            F_lim_upc = [F_PB,      F_PB,     F_PB2,    F_PB2]
            A_lim_upc = [A_PB_maxx, A_PB_max, A_PB_max, A_PB_maxx]
            F_lim_loc = F_lim_upc
            A_lim_loc = [A_PB_minx, A_PB_min, A_PB_min, A_PB_minx]

            F_lim_upr = [F_SB2,    F_SB2, F_max]
            A_lim_upr = [A_SB_maxx, A_SB2, A_SB2]

        if fb.fil[0]['rt'] == 'HIL':
            F_lim_upc = [F_PB,      F_PB,     F_PB2,    F_PB2]
            A_lim_upc = [A_PB_maxx, A_PB_max, A_PB_max, A_PB_maxx]

            F_lim_loc = F_lim_upc
            A_lim_loc = [A_PB_minx, A_PB_min, A_PB_min, A_PB_minx]

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
                    self.plot_spec_limits(self.ax_i)
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
    def draw_phase(self, ax):
        """
        Draw phase on second y-axis in the axes system passed as the argument
        """
        try:
            self.mplwidget.fig.delaxes(self.ax_p)
        except (KeyError, AttributeError):
            pass

        if self.chkPhase.isChecked():
            self.ax_p = ax.twinx() # second axes system with same x-axis for phase
            self.ax_p.is_twin = True # mark this as 'twin' to suppress second grid in mpl_widget
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
                               'g-.', label = "Phase")
        #-----------------------------------------------------------
            self.ax_p.set_ylabel(phi_str)
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
#        else:
#            try:
#                self.mplwidget.fig.delaxes(self.ax_p)
#            except (KeyError, AttributeError):
#                pass
#        self.draw()

#------------------------------------------------------------------------------
    def calc_hf(self):
        """
        (Re-)Calculate the complex frequency response H(f)
        """

        # calculate H_cmplx(W) (complex) for W = 0 ... 2 pi:
        self.W, self.H_cmplx = calc_Hcomplex(fb.fil[0], params['N_FFT'], True)

#------------------------------------------------------------------------------
    def draw(self):
        """
        Re-calculate \|H(f)\| and draw the figure
        """
        self.calc_hf()
        self.update_view()

#------------------------------------------------------------------------------
    def update_view(self):
        """
        Draw the figure with new limits, scale etc without recalculating H(f)
        """
        # Get corners for spec display from the parameters of the target specs subwidget       
        try:
            param_list = fb.fil_tree[fb.fil[0]['rt']][fb.fil[0]['ft']]\
                                    [fb.fil[0]['fc']][fb.fil[0]['fo']]['tspecs'][1]['amp']
        except KeyError:
            param_list = []

        SB = [l for l in param_list if 'A_SB' in l]
        PB = [l for l in param_list if 'A_PB' in l]
        
        if SB:
            A_min = min([fb.fil[0][l] for l in SB])
        else:
            A_min = 5e-4

        if PB:
            A_max = max([fb.fil[0][l] for l in PB])
        else:
            A_max = 1

        if np.all(self.W) is None: # H(f) has not been calculated yet
            self.calc_hf()

        if self.cmbUnitsA.currentText() == 'Auto':
            self.unitA = fb.fil[0]['amp_specs_unit']
        else:
            self.unitA = self.cmbUnitsA.currentText()

        # Linphase settings only makes sense for amplitude plot
        self.chkLinphase.setCheckable(self.unitA == 'V')
        self.chkLinphase.setEnabled(self.unitA == 'V')

        self.specs = self.chkSpecs.isChecked()
        self.linphase = self.chkLinphase.isChecked()

        self.f_S  = fb.fil[0]['f_S']
        self.F_PB = fb.fil[0]['F_PB'] * self.f_S
        self.F_SB = fb.fil[0]['F_SB'] * self.f_S

        self.A_PB  = fb.fil[0]['A_PB']
        self.A_PB2 = fb.fil[0]['A_PB2']
        self.A_SB  = fb.fil[0]['A_SB']
        self.A_SB2 = fb.fil[0]['A_SB2']

        f_lim = fb.fil[0]['freqSpecsRange']

        #========= select frequency range to be displayed =====================
        #=== shift, scale and select: W -> F, H_cplx -> H_c
        self.F = self.W / (2 * np.pi) * self.f_S

        if fb.fil[0]['freqSpecsRangeType'] == 'sym':
            # shift H and F by f_S/2
            self.H_c = np.fft.fftshift(self.H_cmplx)
            self.F -= self.f_S/2.
        elif fb.fil[0]['freqSpecsRangeType'] == 'half':
            # only use the first half of H and F
            self.H_c = self.H_cmplx[0:params['N_FFT']//2]
            self.F = self.F[0:params['N_FFT']//2]
        else: # fb.fil[0]['freqSpecsRangeType'] == 'whole'
            # use H and F as calculated
            self.H_c = self.H_cmplx
            
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

        #================ Main Plotting Routine =========================
        #===  clear the axes and (re)draw the plot (if selectable)
        if self.ax.get_navigate():

            if self.unitA == 'dB':
                A_lim = [20*np.log10(A_min) -10, 20*np.log10(1+A_max) +1]
                self.H_plt = 20*np.log10(abs(H))
                H_str += ' in dB ' + r'$\rightarrow$'
            elif self.unitA == 'V': #  'lin'
                A_lim = [0, (1.05 + A_max)]
                self.H_plt = H
                H_str +=' in V ' + r'$\rightarrow $'
                self.ax.axhline(linewidth=1, color='k') # horizontal line at 0
            else: # unit is W
                A_lim = [0, (1.03 + A_max)**2.]
                self.H_plt = H * H.conj()
                H_str += ' in W ' + r'$\rightarrow $'

            #-----------------------------------------------------------
            self.ax.clear()
            self.ax.plot(self.F, self.H_plt, label = 'H(f)')
            # TODO: self.draw_inset() # this gives an infinite recursion
            self.draw_phase(self.ax)
            #-----------------------------------------------------------
            
            #============= Set Limits and draw specs =========================
            if self.specs: 
                self.plot_spec_limits(self.ax)

            #     self.ax_bounds = [self.ax.get_ybound()[0], self.ax.get_ybound()[1]]#, self.ax.get]
            self.ax.set_xlim(f_lim)
            self.ax.set_ylim(A_lim)

            self.ax.set_title(r'Magnitude Frequency Response')
            self.ax.set_xlabel(fb.fil[0]['plt_fLabel'])
            self.ax.set_ylabel(H_str)

        self.redraw()
        
#------------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the canvas when e.g. the canvas size has changed
        """
        self.mplwidget.redraw()

#------------------------------------------------------------------------------

def main():
    import sys
    from ..compat import QApplication
    
    app = QApplication(sys.argv)
    mainw = Plot_Hf(None)
    app.setActiveWindow(mainw) 
    mainw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
