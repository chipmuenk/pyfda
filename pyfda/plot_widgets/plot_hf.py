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
from pyfda.libs.compat import (QCheckBox, QWidget, QComboBox, QLabel, QLineEdit,
                               QFrame, QHBoxLayout, QGridLayout, pyqtSlot, pyqtSignal)
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib import rcParams
import matplotlib.ticker as ticker
from matplotlib.ticker import AutoMinorLocator

import pyfda.filterbroker as fb
from pyfda.pyfda_rc import params
from pyfda.plot_widgets.mpl_widget import MplWidget
from pyfda.libs.pyfda_lib import calc_Hcomplex, pprint_log, safe_eval, to_html
from pyfda.libs.pyfda_qt_lib import PushButton, qtext_width, qcmb_box_populate

import logging
logger = logging.getLogger(__name__)
classes = {'Plot_Hf': '|H(f)|'}  #: Dict containing class name : display name


class Plot_Hf(QWidget):
    """
    Widget for plotting \|H(f)\|, frequency specs and the phase
    """
    # incoming, connected in sender widget (locally connected to self.process_sig_rx() )
    sig_rx = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.needs_calc = True  # flag whether plot needs to be updated
        self.needs_draw = True  # flag whether plot needs to be redrawn
        self.tool_tip = "Magnitude and phase frequency response"
        self.tab_label = "|H(f)|"

        self.log_bottom = -80
        self.lin_neg_bottom = -10

        self.cmb_units_a_items = [
            "<span>Set unit for y-axis</span>",
            ("Auto", "Auto", "Use same setting as in Ripple specifications"),
            ("dB", "dB", "Attenuation in dB"),
            ("V", "V", "Linear gain"),
            ("W", "W", "Power gain")
        ]
        self.cmb_units_a_default = "auto"  # default setting

        self._construct_ui()

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the navigation toolbar and from sig_rx
        """
        # logger.debug("SIG_RX - needs_calc = {0}, vis = {1}\n{2}"\
        #              .format(self.needs_calc, self.isVisible(), pprint_log(dict_sig)))

        if self.isVisible():
            if 'data_changed' in dict_sig or 'specs_changed' in dict_sig\
                    or ('mpl_toolbar' in dict_sig and dict_sig['mpl_toolbar'] == 'home')\
                         or self.needs_calc:
                self.draw()
                self.needs_calc = False
                self.needs_draw = False
            if 'view_changed' in dict_sig or self.needs_draw:
                self.update_view()
                self.needs_draw = False
            elif 'mpl_toolbar' in dict_sig and dict_sig['mpl_toolbar'] == 'ui_level':
                self.frmControls.setVisible(dict_sig['value'] == 0)

        else:
            if 'data_changed' in dict_sig or 'specs_changed' in dict_sig:
                self.needs_calc = True
            if 'view_changed' in dict_sig:
                self.needs_draw = True

    def _construct_ui(self):
        """
        Define and construct the subwidgets
        """
        self.lbl_show_H_abs = QLabel(to_html('| H | ', frmt='b'))
        self.chk_show_H_abs = QCheckBox(self)
        self.chk_show_H_abs.setChecked(True)
        self.chk_show_H_abs.setToolTip("Show magnitude of H(F)")
        self.lbl_show_H_re = QLabel(to_html('re{H}&nbsp;', frmt='b'))
        self.chk_show_H_re = QCheckBox(self)
        self.chk_show_H_re.setToolTip("Show real part of H(F)")
        self.lbl_show_H_im = QLabel(to_html('im{H}', frmt='b'))
        self.chk_show_H_im = QCheckBox(self)
        self.chk_show_H_im.setToolTip("Show imaginary part of H(F)")

        layG_show_H = QGridLayout()
        layG_show_H.addWidget(self.lbl_show_H_abs, 0, 0)
        layG_show_H.addWidget(self.chk_show_H_abs, 0, 1)
        layG_show_H.addWidget(self.lbl_show_H_re, 1, 0)
        layG_show_H.addWidget(self.chk_show_H_re, 1, 1)
        layG_show_H.addWidget(self.lbl_show_H_im, 2, 0)
        layG_show_H.addWidget(self.chk_show_H_im, 2, 1)
        layG_show_H.setContentsMargins(0,0,10,0)
        layG_show_H.setSpacing(0)

        self.lblIn = QLabel(to_html("Unit:", frmt="b"), self)

        self.cmb_units_a = QComboBox(self)
        qcmb_box_populate(self.cmb_units_a, self.cmb_units_a_items,
                          self.cmb_units_a_default)
        self.cmb_units_a.setObjectName("cmbUnitsA")

        self.lbl_log_bottom = QLabel(to_html("min =", 'bi'), self)
        self.led_log_bottom = QLineEdit(self)
        self.led_log_bottom.setText(str(self.log_bottom))
        self.led_log_bottom.setMaximumWidth(qtext_width(N_x=8))
        self.led_log_bottom.setToolTip(
            "<span>Minimum display value for dB. scale.</span>")
        self.lbl_log_unit = QLabel("dB", self)

        self.cmb_units_a.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.but_zerophase = PushButton(" Zero phase ", checked=False)
        self.but_zerophase.setToolTip(
            "<span>Remove linear phase calculated from filter order.\n"
            "Attention: This makes no sense for a non-linear phase system!</span>")

        self.lblInset = QLabel(to_html("Inset", "bi"), self)
        self.cmbInset = QComboBox(self)
        self.cmbInset.addItems(['off', 'edit', 'fixed'])
        self.cmbInset.setObjectName("cmbInset")
        self.cmbInset.setToolTip("Display/edit second inset plot")
        self.cmbInset.setCurrentIndex(0)
        self.inset_idx = 0  # store previous index for comparison

        self.but_specs = PushButton("Specs ", checked=False)
        self.but_specs.setToolTip("Display filter specs as hatched regions")

        self.but_phase = PushButton("Phase ", checked=False)
        self.but_phase.setToolTip("Overlay phase")

        self.but_align = PushButton("Align", checked=True)
        self.but_align.setToolTip(
            "<span>Try to align gridlines for magnitude and phase "
            "(doesn't work in all cases).</span>")
        self.but_align.setVisible(self.but_phase.isChecked())

        # ----------------------------------------------------------------------
        #               ### frmControls ###
        #
        # This widget encompasses all control subwidgets
        # ----------------------------------------------------------------------
        layHControls = QHBoxLayout()
        layHControls.addLayout(layG_show_H)
        layHControls.addWidget(self.lblIn)
        layHControls.addWidget(self.cmb_units_a)
        layHControls.addStretch(1)
        layHControls.addWidget(self.lbl_log_bottom)
        layHControls.addWidget(self.led_log_bottom)
        layHControls.addWidget(self.lbl_log_unit)
        layHControls.addStretch(1)
        layHControls.addWidget(self.but_zerophase)
        layHControls.addStretch(1)
        layHControls.addWidget(self.lblInset)
        layHControls.addWidget(self.cmbInset)
        layHControls.addStretch(1)
        layHControls.addWidget(self.but_specs)
        layHControls.addStretch(1)
        layHControls.addWidget(self.but_phase)
        layHControls.addWidget(self.but_align)
        layHControls.addStretch(10)

        self.frmControls = QFrame(self)
        self.frmControls.setObjectName("frmControls")
        self.frmControls.setLayout(layHControls)

        # ----------------------------------------------------------------------
        #               ### mplwidget ###
        #
        # main widget, encompassing the other widgets
        # ----------------------------------------------------------------------
        self.mplwidget = MplWidget(self)
        self.mplwidget.layVMainMpl.addWidget(self.frmControls)
        self.mplwidget.layVMainMpl.setContentsMargins(*params['mpl_margins'])
        self.mplwidget.mplToolbar.a_he.setEnabled(True)
        self.mplwidget.mplToolbar.a_he.info = "manual/plot_hf.html"
        self.mplwidget.mplToolbar.a_ui.setEnabled(True)
        self.mplwidget.mplToolbar.a_ui_num_levels = 2
        self.setLayout(self.mplwidget.layVMainMpl)

        self.init_axes()

        self.draw()  # calculate and draw |H(f)|

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.cmb_units_a.currentIndexChanged.connect(self.draw)
        self.led_log_bottom.editingFinished.connect(self.update_view)
        self.chk_show_H_abs.clicked.connect(self.draw)
        self.chk_show_H_re.clicked.connect(self.draw)
        self.chk_show_H_im.clicked.connect(self.draw)

        self.but_zerophase.clicked.connect(self.draw)
        self.cmbInset.currentIndexChanged.connect(self.draw_inset)

        self.but_specs.clicked.connect(self.draw)
        self.but_phase.clicked.connect(self.draw)
        self.but_align.clicked.connect(self.draw)

        self.mplwidget.mplToolbar.sig_tx.connect(self.process_sig_rx)

# ------------------------------------------------------------------------------
    def init_axes(self):
        """
        Initialize and clear the axes (this is run only once)
        """
        if len(self.mplwidget.fig.get_axes()) == 0:  # empty figure, no axes
            self.ax = self.mplwidget.fig.subplots()
        self.ax.xaxis.tick_bottom()  # remove axis ticks on top
        self.ax.yaxis.tick_left()  # remove axis ticks right

# ------------------------------------------------------------------------------
    def align_y_axes(self, ax1, ax2):
        """ Sets tick marks of twinx axes to line up with total number of
            ax1 tick marks
            """
        ax1_ylims = ax1.get_ybound()
        # collect only visible ticks
        ax1_yticks = [t for t in ax1.get_yticks() if t >= ax1_ylims[0] and t <= ax1_ylims[1]]
        ax1_nticks = len(ax1_yticks)
        ax1_ydelta_lim = ax1_ylims[1] - ax1_ylims[0]  # span of limits
        ax1_ydelta_vis = ax1_yticks[-1] - ax1_yticks[0]  # delta of max. and min tick
        ax1_yoffset = ax1_yticks[0]-ax1_ylims[0] # offset between lower limit and first tick

        # calculate scale of Delta Limits / Delta Ticks
        ax1_scale = ax1_ydelta_lim / ax1_ydelta_vis

        ax2_ylims = ax2.get_ybound()
        ax2_yticks = ax2.get_yticks()
        ax2_nticks = len(ax2_yticks)
        #ax2_ydelta_lim = ax2_ylims[1] - ax2_ylims[0]
        ax2_ydelta_vis = ax2_yticks[-1] - ax2_yticks[0]
        ax2_ydelta_lim = ax2_ydelta_vis * ax1_scale
        ax2_scale = ax2_ydelta_lim / ax2_ydelta_vis
        # calculate new offset between lower limit and first tick
        ax2_yoffset = ax1_yoffset * ax2_ydelta_lim / ax1_ydelta_lim
        # logger.warning("ax2: delta_vis: {0}, scale: {1}, offset: {2}"
        #                .format(ax2_ydelta_vis, ax2_scale, ax2_yoffset))
        # logger.warning("Ticks: {0} # {1}".format(ax1_nticks, ax2_nticks))

        ax2.set_yticks(np.linspace(ax2_yticks[0],
                                   (ax2_yticks[1]-ax2_yticks[0]),
                                   ax1_nticks))
        # logger.warning("ax2[0]={0} | ax2[1]={1} ax2[-1]={2}".format(ax2_yticks[0],
        #                            ax2_yticks[1], ax2_yticks[-1]))
        ax2_lim0 = ax2_yticks[0] - ax2_yoffset
        ax2.set_ybound(ax2_lim0, ax2_lim0 + ax2_ydelta_lim)

# =============================================================================
#             # https://stackoverflow.com/questions/26752464/how-do-i-align-gridlines-for-two-y-axis-scales-using-matplotlib
#             # works, but both axes have ugly numbers
#             nticks = 11
#             ax.yaxis.set_major_locator(ticker.LinearLocator(nticks))
#             self.ax_p.yaxis.set_major_locator(ticker.LinearLocator(nticks))
# # =============================================================================
# =============================================================================
#             # https://stackoverflow.com/questions/45037386/trouble-aligning-ticks-for-matplotlib-twinx-axes
#             # works, but second axis has ugly numbering
#             l_H = ax.get_ylim()
#             l_p = self.ax_p.get_ylim()
#             f = lambda x : l_p[0]+(x-l_H[0])/(l_H[1]-l_H[0])*(l_p[1]-l_p[0])
#             ticks = f(ax.get_yticks())
#             self.ax_p.yaxis.set_major_locator(ticker.FixedLocator(ticks))
#
# =============================================================================

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

        F_max = self.f_max/2
        F_PB  = self.F_PB
        F_SB  = fb.fil[0]['F_SB'] * self.f_max
        F_SB2 = fb.fil[0]['F_SB2'] * self.f_max
        F_PB2 = fb.fil[0]['F_PB2'] * self.f_max

        F_lim_upl = F_lim_lol = []  # left side limits, lower and upper
        A_lim_upl = A_lim_lol = []

        F_lim_upc = F_lim_loc = []  # center limits, lower and upper
        A_lim_upc = A_lim_loc = []

        F_lim_upr = F_lim_lor = []  # right side limits, lower and upper
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

        _plot_specs()  # plot specs in the range 0 ... f_S/2

        if fb.fil[0]['freqSpecsRangeType'] != 'half':
            # add plot limits for other half of the spectrum
            if fb.fil[0]['freqSpecsRangeType'] == 'sym':  # frequency axis +/- f_S/2
                F_lim_upl = -F_lim_upl
                F_lim_lol = -F_lim_lol
                F_lim_upc = -F_lim_upc
                F_lim_loc = -F_lim_loc
                F_lim_upr = -F_lim_upr
                F_lim_lor = -F_lim_lor
            else: # -> 'whole'
                F_lim_upl = self.f_max - F_lim_upl
                F_lim_lol = self.f_max - F_lim_lol
                F_lim_upc = self.f_max - F_lim_upc
                F_lim_loc = self.f_max - F_lim_loc
                F_lim_upr = self.f_max - F_lim_upr
                F_lim_lor = self.f_max - F_lim_lor

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
                self.ax_i.clear()  # clear old plot and specs

                # draw an opaque background with the extent of the inset plot:
#                self.ax_i.patch.set_facecolor('green') # without label area
#                self.mplwidget.fig.patch.set_facecolor('green') # whole figure
                extent = self.mplwidget.get_full_extent(self.ax_i, pad=0.0)
                # Transform this back to figure coordinates - otherwise, it
                #  won't behave correctly when the size of the plot is changed:
                extent = extent.transformed(self.mplwidget.fig.transFigure.inverted())
                rect = Rectangle((extent.xmin, extent.ymin), extent.width,
                        extent.height, facecolor=rcParams['figure.facecolor'], edgecolor='none',
                        transform=self.mplwidget.fig.transFigure, zorder=-1)
                self.ax_i.patches.append(rect)

                self.ax_i.set_xlim(fb.fil[0]['freqSpecsRange'])
                if self.chk_show_H_abs.isChecked():
                    self.ax_i.plot(self.F, self.H_plt_abs)
                if self.chk_show_H_re.isChecked():
                    self.ax_i.plot(self.F, self.H_plt_re)
                if self.chk_show_H_im.isChecked():
                    self.ax_i.plot(self.F, self.H_plt_im)

            if self.cmbInset.currentIndex() == 1: # edit / navigate inset
                self.ax_i.set_navigate(True)
                self.ax.set_navigate(False)
                if self.but_specs.isChecked():
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

        self.inset_idx = self.cmbInset.currentIndex()  # update index
        self.draw()

# ------------------------------------------------------------------------------
    def draw_phase(self, ax):
        """
        Draw phase on second y-axis in the axes system passed as the argument
        """
        if hasattr(self, 'ax_p'):
            self.mplwidget.fig.delaxes(self.ax_p)
            del self.ax_p
        # try:
        #     self.mplwidget.fig.delaxes(self.ax_p)
        # except (KeyError, AttributeError):
        #     pass

        if self.but_phase.isChecked():
            self.ax_p = ax.twinx()  # second axes system with same x-axis for phase
            self.ax_p.is_twin = True  # mark this as 'twin' to suppress second grid in mpl_widget
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
        # -----------------------------------------------------------
            self.ax_p.plot(self.F, np.unwrap(phi)*scale,
                           'g-.', label=r"$\angle\,H(F)$")
        # -----------------------------------------------------------
            self.ax_p.set_ylabel(phi_str)

#------------------------------------------------------------------------------
    def calc_hf(self):
        """
        (Re-)Calculate the complex frequency response H_cmplx(W) (complex)
        for W = 0 ... 2 pi:
        """
        self.W, self.H_cmplx = calc_Hcomplex(fb.fil[0], params['N_FFT'], True)

#------------------------------------------------------------------------------
    def draw(self):
        """
        Re-calculate \|H(f)\| and draw the figure
        """
        self.but_align.setVisible(self.but_phase.isChecked())
        self.calc_hf()
        self.update_view()

#------------------------------------------------------------------------------
    def update_view(self):
        """
        Draw the figure with new limits, scale etc without recalculating H(f)
        """
        # suppress "divide by zero in log10" warnings
        old_settings_seterr = np.seterr()
        np.seterr(divide='ignore')

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

        if np.all(self.W) is None:  # H(f) has not been calculated yet
            self.calc_hf()

        if self.cmb_units_a.currentText() == 'Auto':
            self.unitA = fb.fil[0]['amp_specs_unit']
        else:
            self.unitA = self.cmb_units_a.currentText()

        # only display log bottom widget for unit dB
        self.lbl_log_bottom.setVisible(self.unitA == 'dB')
        self.led_log_bottom.setVisible(self.unitA == 'dB')
        self.lbl_log_unit.setVisible(self.unitA == 'dB')

        # Linphase settings only makes sense for amplitude plot and
        # for plottin real/imag. part of H, not its magnitude
        self.but_zerophase.setCheckable(self.unitA == 'V')
        self.but_zerophase.setEnabled(self.unitA == 'V')

        self.specs = self.but_specs.isChecked()

        self.f_max = fb.fil[0]['f_max']

        self.F_PB = fb.fil[0]['F_PB'] * self.f_max
        self.f_maxB = fb.fil[0]['F_SB'] * self.f_max

        self.A_PB  = fb.fil[0]['A_PB']
        self.A_PB2 = fb.fil[0]['A_PB2']
        self.A_SB  = fb.fil[0]['A_SB']
        self.A_SB2 = fb.fil[0]['A_SB2']

        f_lim = fb.fil[0]['freqSpecsRange']

        # ========= select frequency range to be displayed =====================
        # === shift, scale and select: W -> F, H_cplx -> H_c
        self.F = self.W / (2 * np.pi) * self.f_max

        if fb.fil[0]['freqSpecsRangeType'] == 'sym':
            # shift H and F by f_S/2
            self.H_c = np.fft.fftshift(self.H_cmplx)
            self.F -= self.f_max/2.
        elif fb.fil[0]['freqSpecsRangeType'] == 'half':
            # only use the first half of H and F
            self.H_c = self.H_cmplx[0:params['N_FFT']//2]
            self.F = self.F[0:params['N_FFT']//2]
        else:  # fb.fil[0]['freqSpecsRangeType'] == 'whole'
            # use H and F as calculated
            self.H_c = self.H_cmplx

        # remove linear phase if button is checked
        if self.but_zerophase.isChecked():
            self.H_c = self.H_c * np.exp(1j * self.W[0:len(self.F)] * fb.fil[0]["N"]/2.)

        H_str = r'$H(\mathrm{e}^{\mathrm{j} \Omega})$'

        # ================ Main Plotting Routine =========================
        # ===  clear the axes and (re)draw the plot (if selectable)
        if self.ax.get_navigate():
            #-----------------------------------------------------------
            self.ax.clear()
            # Select abs / real / imaginary part and scale according to selected unit
            if self.chk_show_H_abs.isChecked():
                if self.unitA == 'dB':
                    self.H_plt_abs = np.maximum(20*np.log10(np.abs(self.H_c)), self.log_bottom)
                elif self.unitA == 'V':
                    self.H_plt_abs = np.abs(self.H_c)
                elif self.unitA == 'W':
                    self.H_plt_abs =  np.abs(self.H_c) * np.abs(self.H_c)
                self.ax.plot(self.F, self.H_plt_abs, label = '$|H(f)|$')
            if self.chk_show_H_re.isChecked():
                if self.unitA == 'dB':
                    self.H_plt_re = np.maximum(20*np.log10(np.abs(self.H_c.real)), self.log_bottom)
                elif self.unitA == 'V':
                    self.H_plt_re = self.H_c.real
                elif self.unitA == 'W':
                    self.H_plt_re =  self.H_c.real * self.H_c.real
                self.ax.plot(self.F, self.H_plt_re, label = r'$\Re\{H(F)\}$')
            if self.chk_show_H_im.isChecked():
                if self.unitA == 'dB':
                    self.H_plt_im = np.maximum(20*np.log10(np.abs(self.H_c.imag)), self.log_bottom)
                elif self.unitA == 'V':
                    self.H_plt_im = self.H_c.imag
                elif self.unitA == 'W':
                    self.H_plt_im =  self.H_c.imag * self.H_c.imag
                self.ax.plot(self.F, self.H_plt_im, label = r'$\Im\{H(F)\}$')

            # calculate limits for selected curves depending on selected unit
            if self.unitA == 'dB':
                self.log_bottom = safe_eval(
                    self.led_log_bottom.text(), self.log_bottom,
                    return_type='float', sign='neg')
                self.led_log_bottom.setText(str(self.log_bottom))
                A_lim = [self.log_bottom, 2]
                H_str += ' in dB ' + r'$\rightarrow$'

            elif self.unitA == 'V':  #  'lin'
                A_min = 0
                if self.chk_show_H_re.isChecked():  # H can be less than zero
                    A_min = min(A_min, np.nanmin(self.H_plt_re[np.isfinite(self.H_c)]))
                if self.chk_show_H_im.isChecked():  # H can be less than zero
                    A_min = min(A_min, np.nanmin(self.H_plt_im[np.isfinite(self.H_c)]))

                A_min = max(A_min, self.lin_neg_bottom)
                A_lim = [A_min, (1.05 + A_max)]
                H_str +=' in V ' + r'$\rightarrow $'
                self.ax.axhline(linewidth=1, color='k') # horizontal line at 0

            else: # unit is W
                A_lim = [0, (1.03 + A_max)**2.]
                H_str += ' in W ' + r'$\rightarrow $'

            # TODO: self.draw_inset() # this gives an infinite recursion
            self.draw_phase(self.ax)
            #-----------------------------------------------------------

            #============= Set Limits and draw specs =========================
            if self.but_specs.isChecked():
                self.plot_spec_limits(self.ax)

            #     self.ax_bounds = [self.ax.get_ybound()[0], self.ax.get_ybound()[1]]#, self.ax.get]
            self.ax.set_xlim(f_lim)
            self.ax.set_ylim(A_lim)
            # logger.warning("set limits")

            self.ax.set_xlabel(fb.fil[0]['plt_fLabel'])
            self.ax.set_ylabel(H_str)

            title_str = ""
            if self.chk_show_H_abs.isChecked():
                title_str = "Magnitude "
            elif self.chk_show_H_re.isChecked() or self.chk_show_H_im.isChecked():
                title_str = "Amplitude "
            if self.but_phase.isChecked():
                if title_str != "":
                    title_str += "and Phase "
                else:
                    title_str += "Phase "
            if title_str != "":
                self.ax.set_title(f'{title_str}Frequency Response')

            self.ax.xaxis.set_minor_locator(AutoMinorLocator()) # enable minor ticks
            self.ax.yaxis.set_minor_locator(AutoMinorLocator()) # enable minor ticks

            if hasattr(self, "ax_p"):  # if phase is visible, add label to legend
                lines, labels = self.ax.get_legend_handles_labels()
                lines2, labels2 = self.ax_p.get_legend_handles_labels()
                self.ax.legend(lines + lines2, labels + labels2, loc='best',
                               fontsize='small', fancybox=True, framealpha=0.7)
            # only show legend if at least one label is visible
            elif self.ax.get_legend_handles_labels()[1]:
                self.ax.legend(loc='best', fontsize='small', fancybox=True,
                               framealpha=0.7)

            np.seterr(**old_settings_seterr)

        self.redraw()

#------------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the canvas when e.g. the canvas size has changed
        """
        if hasattr(self, 'ax_p') and self.but_align.isChecked():
            # Align gridlines between H(f) and phi nicely
            self.align_y_axes(self.ax, self.ax_p)
        self.mplwidget.redraw()
        #logger.warning("redraw")

#------------------------------------------------------------------------------

if __name__ == "__main__":
    """ Run widget standalone with `python -m pyfda.plot_widgets.plot_hf`"""
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = Plot_Hf()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
