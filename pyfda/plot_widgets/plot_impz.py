# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for plotting impulse and general transient responses
"""
# import time
from pyfda.libs.compat import QWidget, pyqtSignal, QTabWidget, QVBoxLayout

import numpy as np
from numpy import pi
import scipy.signal as sig
from scipy.special import sinc, diric
import matplotlib.patches as mpl_patches
# import matplotlib.lines as lines
from matplotlib.ticker import AutoMinorLocator

import pyfda.filterbroker as fb
import pyfda.libs.pyfda_fix_lib as fx
from pyfda.libs.pyfda_sig_lib import angle_zero
from pyfda.libs.pyfda_lib import (
    to_html, safe_eval, pprint_log, np_type, calc_ssb_spectrum,
    rect_bl, sawtooth_bl, triang_bl, comb_bl, calc_Hcomplex, safe_numexpr_eval)
from pyfda.libs.pyfda_qt_lib import (qget_cmb_box, qset_cmb_box, qstyle_widget,
                                     qcmb_box_add_item, qcmb_box_del_item)
from pyfda.pyfda_rc import params  # FMT string for QLineEdit fields, e.g. '{:.3g}'
from pyfda.plot_widgets.mpl_widget import MplWidget, stems, scatter

from pyfda.plot_widgets.plot_impz_ui import PlotImpz_UI

import logging
logger = logging.getLogger(__name__)

# TODO: "Home" calls redraw for botb mpl widgets
# TODO: changing the view on some widgets redraws h[n] unncessarily
# TODO: Single-sided and double-sided spectra of pulses are identical - ok?

classes = {'Plot_Impz': 'y[n] / Y(f)'}  #: Dict containing class name : display name


class Plot_Impz(QWidget):
    """
    Construct a widget for plotting impulse and general transient responses
    """
    # incoming
    sig_rx = pyqtSignal(object)
    # outgoing, e.g. when stimulus has been calculated
    sig_tx = pyqtSignal(object)
    # outgoing to local fft window
    # sig_tx_fft = pyqtSignal(object)

    def __init__(self, parent):
        super(Plot_Impz, self).__init__(parent)

        self.ACTIVE_3D = False
        self.ui = PlotImpz_UI(self)  # create the UI part with buttons etc.

        # initial settings
        self.needs_calc = True   # flag whether plots need to be recalculated
        self.needs_redraw = [True] * 2  # flag which plot needs to be redrawn
        self.error = False
        # initial setting for fixpoint simulation:
        self.fx_sim = qget_cmb_box(self.ui.cmb_sim_select, data=False) == 'Fixpoint'
        self.fx_sim_old = self.fx_sim
        self.tool_tip = "Impulse / transient response and their spectra"
        self.tab_label = "y[n]"
        self.active_tab = 0  # index for active tab
        # markersize=None, markeredgewidth=None, markeredgecolor=None,
        # markerfacecolor=None, markerfacecoloralt='none', fillstyle=None,
        self.fmt_mkr_size = 8
        self.fmt_plot_resp = {'color': 'red', 'linewidth': 2, 'alpha': 0.5}
        self.fmt_mkr_resp = {'marker': 'o', 'color': 'red', 'alpha': 0.5,
                             'ms': self.fmt_mkr_size}
        self.fmt_plot_stim = {'color': 'blue', 'linewidth': 2, 'alpha': 0.5}
        self.fmt_mkr_stim = {'marker': 's', 'color': 'blue', 'alpha': 0.5,
                             'ms': self.fmt_mkr_size}
        self.fmt_plot_stmq = {'color': 'darkgreen', 'linewidth': 2, 'alpha': 0.5}
        self.fmt_mkr_stmq = {'marker': 'D', 'color': 'darkgreen', 'alpha': 0.5,
                             'ms': self.fmt_mkr_size}

        # self.fmt_stem_stim = params['mpl_stimuli']

        self._construct_UI()

        # --------------------------------------------
        # initialize routines and settings
        self.fx_select()    # initialize fixpoint or float simulation
        self.impz()  # initial calculation of stimulus and response and drawing

    def _construct_UI(self):
        """
        Create the top level UI of the widget, consisting of matplotlib widget
        and control frame.
        """
        # ----------------------------------------------------------------------
        # Define MplWidget for TIME domain plots
        # ----------------------------------------------------------------------
        self.mplwidget_t = MplWidget(self)
        self.mplwidget_t.setObjectName("mplwidget_t1")
        self.mplwidget_t.layVMainMpl.addWidget(self.ui.wdg_ctrl_time)
        self.mplwidget_t.layVMainMpl.setContentsMargins(*params['wdg_margins'])
        self.mplwidget_t.mplToolbar.a_he.setEnabled(True)
        self.mplwidget_t.mplToolbar.a_he.info = "manual/plot_impz.html"

        # ----------------------------------------------------------------------
        # Define MplWidget for FREQUENCY domain plots
        # ----------------------------------------------------------------------
        self.mplwidget_f = MplWidget(self)
        self.mplwidget_f.setObjectName("mplwidget_f1")
        self.mplwidget_f.layVMainMpl.addWidget(self.ui.wdg_ctrl_freq)
        self.mplwidget_f.layVMainMpl.setContentsMargins(*params['wdg_margins'])
        self.mplwidget_f.mplToolbar.a_he.setEnabled(True)
        self.mplwidget_f.mplToolbar.a_he.info = "manual/plot_impz.html"

        # ----------------------------------------------------------------------
        # Tabbed layout with vertical tabs
        # ----------------------------------------------------------------------
        self.tabWidget = QTabWidget(self)
        self.tabWidget.addTab(self.mplwidget_t, "Time")
        self.tabWidget.setTabToolTip(0, "Impulse and transient response of filter")
        self.tabWidget.addTab(self.mplwidget_f, "Frequency")
        self.tabWidget.setTabToolTip(
            1, "Spectral representation of impulse or transient response")
        self.tabWidget.setTabPosition(QTabWidget.West)

        # list with tabWidgets
        self.tab_mplwidgets = ["mplwidget_t", "mplwidget_f"]

        layVMain = QVBoxLayout()
        layVMain.addWidget(self.tabWidget)
        layVMain.addWidget(self.ui.wdg_ctrl_stim)
        layVMain.addWidget(self.ui.wdg_ctrl_run)
        layVMain.setContentsMargins(*params['wdg_margins'])  # (left, top, right, bottom)

        self.setLayout(layVMain)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        # connect UI to widgets and signals upstream:
        self.ui.sig_tx.connect(self.process_sig_rx)

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # --- run control ---
        self.ui.cmb_sim_select.currentIndexChanged.connect(self.impz)
        self.ui.but_run.clicked.connect(self.impz)
        self.ui.but_auto_run.clicked.connect(self.calc_auto)
        self.ui.but_fx_scale.clicked.connect(self.draw)

        # --- time domain plotting ---
        self.ui.cmb_plt_time_resp.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_time_stim.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_time_stmq.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_time_spgr.currentIndexChanged.connect(self._spgr_cmb)
        self.ui.chk_log_time.clicked.connect(self.draw)
        self.ui.led_log_bottom_time.editingFinished.connect(self.draw)
        self.ui.chk_log_spgr_time.clicked.connect(self.draw)
        self.ui.led_time_nfft_spgr.editingFinished.connect(self._spgr_ui2params)
        self.ui.led_time_ovlp_spgr.editingFinished.connect(self._spgr_ui2params)
        self.ui.cmb_mode_spgr_time.currentIndexChanged.connect(self.draw)
        self.ui.chk_byfs_spgr_time.clicked.connect(self.draw)
        self.ui.chk_fx_limits.clicked.connect(self.draw)
        self.ui.chk_win_time.clicked.connect(self.draw)
        # --- frequency domain plotting ---
        self.ui.cmb_plt_freq_resp.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_freq_stim.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_freq_stmq.currentIndexChanged.connect(self.draw)
        self.ui.chk_Hf.clicked.connect(self.draw)
        self.ui.cmb_freq_display.currentIndexChanged.connect(self.draw)
        self.ui.chk_log_freq.clicked.connect(self.draw)
        self.ui.led_log_bottom_freq.editingFinished.connect(self.draw)
        self.ui.chk_freq_norm_impz.clicked.connect(self.draw)
        self.ui.chk_show_info_freq.clicked.connect(self.draw)
        # self.ui.chk_win_freq.clicked.connect(self.draw)

        self.mplwidget_t.mplToolbar.sig_tx.connect(self.process_sig_rx)
        self.mplwidget_f.mplToolbar.sig_tx.connect(self.process_sig_rx)

        # When user has selected a different tab, trigger a recalculation of current tab
        self.tabWidget.currentChanged.connect(self.draw)  # passes number of active tab

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from
        - the navigation toolbars (time and freq.)
        - local widgets (impz_ui) and
        - plot_tab_widgets() (global signals)
        """

        logger.warning("PROCESS_SIG_RX - needs_calc: {0} | vis: {1}\n{2}"
                     .format(self.needs_calc, self.isVisible(), pprint_log(dict_sig)))

        if dict_sig['sender'] == __name__:
            logger.debug("Stopped infinite loop:\n{0}".format(pprint_log(dict_sig)))
            return

        self.error = False

        if 'fx_sim' in dict_sig:
            if dict_sig['fx_sim'] == 'specs_changed':
                self.needs_calc = True
                self.error = False
                qstyle_widget(self.ui.but_run, "changed")
                if self.isVisible():
                    self.impz()

            elif dict_sig['fx_sim'] == 'get_stimulus':
                """
                - Select Fixpoint mode
                - Calculate stimuli, quantize and pass to dict_sig with
                  `'fx_sim': 'send_stimulus'` and `'fx_stimulus': <quant stimulus array>`.
                  Stimuli are scaled with the input fractional word length, i.e.
                  with 2**WF (input) to obtain integer values
                  """
                # always require recalculation when triggered externally
                self.needs_calc = True
                self.needs_redraw = [True] * 2
                self.error = False
                qstyle_widget(self.ui.but_run, "changed")
                self.fx_select("Fixpoint")
                if self.isVisible():
                    self.calc_stimulus()

            elif dict_sig['fx_sim'] == 'set_results':
                """
                - Check whether floating stimuli are complex and set flag correspondingly
                - Convert simulation results to integer and transfer them to the plotting
                  routine in `self.draw_response_fx()`
                """
                logger.debug("Received fixpoint results.")
                self.cmplx = np.any(np.iscomplex(self.x))
                self.ui.lbl_stim_cmplx_warn.setVisible(self.cmplx)
                self.draw_response_fx(dict_sig=dict_sig)

            elif dict_sig['fx_sim'] == 'error':
                self.needs_calc = True
                self.error = True
                qstyle_widget(self.ui.but_run, "error")
                return

            elif not dict_sig['fx_sim']:
                logger.error('Missing value for key "fx_sim".')

            else:
                logger.error('Unknown value "{0}" for "fx_sim" key\n'
                             '\treceived from "{1}"'.format(dict_sig['fx_sim'],
                                                            dict_sig['sender']))

        # --- widget is visible, handle all signals except 'fx_sim' -----------
        elif self.isVisible():  # all signals except 'fx_sim'
            if 'data_changed' in dict_sig or 'specs_changed' in dict_sig\
                    or self.needs_calc:
                # update number of data points in impz_ui and FFT window
                # needed when e.g. FIR filter order has been changed, requiring
                # a different number of data points for simulation. Don't emit a signal.
                self.ui.update_N(emit=False)
                self.needs_calc = True
                qstyle_widget(self.ui.but_run, "changed")
                self.impz()

            elif 'view_changed' in dict_sig:
                if dict_sig['view_changed'] == 'f_S':
                    self.ui.recalc_freqs()
                    self.draw()
                else:
                    self.draw()  # TODO:  redundant??

            elif 'ui_changed' in dict_sig:
                # exclude those ui elements  / events that don't require a recalculation
                # of stimulus and response
                if dict_sig['ui_changed'] in {'resized', 'tab'}:
                    pass
                else:  # all the other ui elements are treated here
                    self.needs_calc = True
                    qstyle_widget(self.ui.but_run, "changed")
                    self.impz()

            elif 'home' in dict_sig:
                self.redraw()
                # self.tabWidget.currentWidget().redraw()
                # redraw method of current mplwidget, always redraws tab 0
                self.needs_redraw[self.tabWidget.currentIndex()] = False

        else:  # invisible
            if 'data_changed' in dict_sig or 'specs_changed' in dict_sig:
                self.needs_calc = True

            elif 'view_changed' in dict_sig:
                # update frequency related widgets (visible or not)
                if dict_sig['view_changed'] == 'f_S':
                    self.ui.recalc_freqs()
            elif 'ui_changed' in dict_sig:
                self.needs_redraw = [True] * 2

#            elif 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'get_stimulus':
#                    self.needs_calc = True # always recalculate when triggered externally
#                    qstyle_widget(self.ui.but_run, "changed")
#                    self.fx_select("Fixpoint")

# =============================================================================
# Simulation: Calculate stimulus, response and draw them
# =============================================================================
    def calc_auto(self, autorun=None):
        """
        Triggered when checkbox "Autorun" is clicked.
        Enable or disable the "Run" button depending on the setting of the
        checkbox.
        When checkbox is checked (`autorun == True` passed via signal-
        slot connection), automatically run `impz()`.
        """

        self.ui.but_run.setEnabled(not autorun)
        if autorun:
            self.impz()

    def impz(self, arg=None):
        """
        Triggered by:
            - construct_UI()  [Initialization]
            - Pressing "Run" button, passing button state as a boolean
            - Activating "Autorun" via `self.calc_auto()`
            - 'fx_sim' : 'specs_changed'
            -
        Calculate response and redraw it.

        Stimulus and response are only calculated if `self.needs_calc == True`.
        """
        # allow scaling the frequency response from pure impulse (no DC, no noise)
        self.ui.chk_freq_norm_impz.setEnabled(
            (self.ui.noi == 0 or self.ui.cmbNoise.currentText() == 'None')
            and self.ui.DC == 0)

        self.fx_select()  # check for fixpoint setting and update if needed
        if type(arg) == bool:  # but_run has been pressed
            self.needs_calc = True  # force recalculation when but_run is pressed
        elif not self.ui.but_auto_run.isChecked():
            return

        if self.needs_calc:
            logger.debug("Calc impz started!")
            if self.fx_sim:  # start a fixpoint simulation
                self.sig_tx.emit({'sender': __name__, 'fx_sim': 'init'})
                return

            self.calc_stimulus()
            self.calc_response()

            if self.error:
                return

            self.needs_calc = False
            self.needs_redraw = [True] * 2

        if self.needs_redraw[self.tabWidget.currentIndex()]:
            logger.debug("Redraw impz started!")
            self.draw()
            self.needs_redraw[self.tabWidget.currentIndex()] = False

        qstyle_widget(self.ui.but_run, "normal")

# =============================================================================

    def fx_select(self, fx=None):
        """
        Select between fixpoint and floating point simulation.
        Parameter `fx` can be:

        - str "Fixpoint" or "Float" when called directly

        - int 0 or 1 when triggered by changing the index of combobox
          `self.ui.cmb_sim_select` (signal-slot-connection)

        In both cases, the index of the combobox is updated according to the
        passed argument. If the index has been changed since last time,
        `self.needs_calc` is set to True and the run button is set to "changed".

        When fixpoint simulation is selected, all corresponding widgets are made
        visible. `self.fx_sim` is set to True.

        If `self.fx_sim` has changed, `self.needs_calc` is set to True.
        """
        logger.debug("start fx_select")

        if fx in {0, 1}:  # connected to index change of combo box
            pass
        elif fx in {"Float", "Fixpoint"}:  # direct function call
            qset_cmb_box(self.ui.cmb_sim_select, fx)
        elif fx is None:
            pass
        else:
            logger.error('Unknown argument "{0}".'.format(fx))
            return

        self.fx_sim = qget_cmb_box(self.ui.cmb_sim_select, data=False) == 'Fixpoint'

        self.ui.cmb_plt_freq_stmq.setVisible(self.fx_sim)
        self.ui.lbl_plt_freq_stmq.setVisible(self.fx_sim)
        self.ui.cmb_plt_time_stmq.setVisible(self.fx_sim)
        self.ui.lbl_plt_time_stmq.setVisible(self.fx_sim)
        self.ui.but_fx_scale.setVisible(self.fx_sim)
        self.ui.chk_fx_limits.setVisible(self.fx_sim)

        if self.fx_sim:
            qcmb_box_add_item(self.ui.cmb_plt_time_spgr, ["xqn", "x_q[n]", ""])
        else:
            qcmb_box_del_item(self.ui.cmb_plt_time_spgr, "x_q[n]")

        if self.fx_sim != self.fx_sim_old:
            qstyle_widget(self.ui.but_run, "changed")
            # even if nothing else has changed, stimulus and response must be recalculated
            self.needs_calc = True

        self.fx_sim_old = self.fx_sim

# ------------------------------------------------------------------------------
    def calc_stimulus(self):
        """
        (Re-)calculate stimulus `self.x`
        """
        self.n = np.arange(self.ui.N_end)
        phi1 = self.ui.phi1 / 180 * pi
        phi2 = self.ui.phi2 / 180 * pi
        # T_S = fb.fil[0]['T_S']
        # calculate index from T1 entry for creating stimulus vectors, shifted
        # by T1. Limit the value to N_end - 1.
        self.T1_int = min(int(np.round(self.ui.T1)), self.ui.N_end-1)

        # calculate stimuli x[n] ==============================================
        self.H_str = ''
        self.title_str = ""

        if self.ui.stim == "none":
            self.x = np.zeros(self.ui.N_end)
            self.title_str = r'Zero Input System Response'
            self.H_str = r'$h_0[n]$'  # default

        elif self.ui.stim == "dirac":
            if np_type(self.ui.A1) == complex:
                A_type = complex
            else:
                A_type = float

            self.x = np.zeros(self.ui.N_end, dtype=A_type)
            self.x[self.T1_int] = self.ui.A1  # create dirac impulse as input signal
            self.title_str = r'Impulse Response'
            self.H_str = r'$h[n]$'  # default

        elif self.ui.stim == "sinc":
            self.x =\
                self.ui.A1 * sinc(2 * (self.n - self.ui.N//2 - self.ui.T1) * self.ui.f1)\
                + self.ui.A2 * sinc(2 * (self.n - self.ui.N//2 - self.ui.T2) * self.ui.f2)
            self.title_str += r'Sinc Impulse '

        elif self.ui.stim == "gauss":
            self.x = self.ui.A1 * sig.gausspulse((self.n - self.ui.N//2 - self.ui.T1),
                                                 fc=self.ui.f1, bw=self.ui.BW1) +\
                self.ui.A2 * sig.gausspulse((self.n - self.ui.N//2 - self.ui.T2),
                                            fc=self.ui.f2, bw=self.ui.BW2)
            self.title_str += r'Gaussian Impulse '

        elif self.ui.stim == "rect":
            n_start = int(np.floor((self.ui.N - self.ui.TW1)/2 - self.ui.T1))
            n_min = max(n_start, 0)
            n_max = min(n_start + self.ui.TW1, self.ui.N)
            self.title_str += r'Rect Impulse '
            self.x = self.ui.A1 * np.where((self.n > n_min) & (self.n <= n_max), 1, 0)

        # ----------------------------------------------------------------------
        elif self.ui.stim == "step":
            self.x = self.ui.A1 * np.ones(self.ui.N_end)  # create step function
            self.x[0:self.T1_int].fill(0)
            if self.ui.chk_step_err.isChecked():
                self.title_str = r'Settling Error'
                self.H_str = r'$h_{\epsilon, \infty} - h_{\epsilon}[n]$'
            else:
                self.title_str = r'Step Response'
                self.H_str = r'$h_{\epsilon}[n]$'

        # ----------------------------------------------------------------------
        elif self.ui.stim == "cos":
            self.x = self.ui.A1 * np.cos(2*pi * self.n * self.ui.f1 + phi1) +\
                self.ui.A2 * np.cos(2*pi * self.n * self.ui.f2 + phi2)
            self.title_str += r'Cosine Signal'

        elif self.ui.stim == "sine":
            self.x = self.ui.A1 * np.sin(2*pi * self.n * self.ui.f1 + phi1) +\
                self.ui.A2 * np.sin(2*pi * self.n * self.ui.f2 + phi2)
            self.title_str += r'Sinusoidal Signal '

        elif self.ui.stim == "exp":
            self.x = self.ui.A1 * np.exp(1j * (2 * pi * self.n * self.ui.f1 + phi1)) +\
                self.ui.A2 * np.exp(1j * (2 * pi * self.n * self.ui.f2 + phi2))
            self.title_str += r'Complex Exponential Signal '

        elif self.ui.stim == "diric":
            self.x = self.ui.A1 * diric((4 * pi * (self.n-self.ui.T1)
                                        * self.ui.f1 + phi1*2) / self.ui.TW1, self.ui.TW1)
            self.title_str += r'Periodic Sinc Signal'

        # ----------------------------------------------------------------------
        elif self.ui.stim == "chirp":
            if True:  # sig.chirp is buggy, T_sim cannot be larger than T_end
                T_end = self.ui.N_end
            else:
                T_end = self.ui.T2
            self.x = self.ui.A1 * sig.chirp(self.n, self.ui.f1, T_end, self.ui.f2,
                                            method=self.ui.chirp_type, phi=phi1)
            self.title_str += self.ui.chirp_type + ' Chirp Signal'

        # ----------------------------------------------------------------------
        elif self.ui.stim == "triang":
            if self.ui.chk_stim_bl.isChecked():
                self.x = self.ui.A1 * triang_bl(2*pi * self.n * self.ui.f1 + phi1)
                self.title_str += r'Bandlim. Triangular Signal'
            else:
                self.x = self.ui.A1 * sig.sawtooth(2*pi * self.n * self.ui.f1 + phi1,
                                                   width=0.5)
                self.title_str += r'Triangular Signal'

        elif self.ui.stim == "saw":
            if self.ui.chk_stim_bl.isChecked():
                self.x = self.ui.A1 * sawtooth_bl(2*pi * self.n * self.ui.f1 + phi1)
                self.title_str += r'Bandlim. Sawtooth Signal'
            else:
                self.x = self.ui.A1 * sig.sawtooth(2*pi * self.n * self.ui.f1 + phi1)
                self.title_str += r'Sawtooth Signal'

        elif self.ui.stim == "square":
            if self.ui.chk_stim_bl.isChecked():
                self.x = self.ui.A1 * rect_bl(2*pi * self.n * self.ui.f1 + phi1,
                                              duty=self.ui.stim_par1)
                self.title_str += r'Bandlimited Rect. Signal'
            else:
                self.x = self.ui.A1 * sig.square(2*pi * self.n * self.ui.f1 + phi1,
                                                 duty=self.ui.stim_par1)
                self.title_str += r'Rect. Signal'

        elif self.ui.stim == "comb":
            self.x = self.ui.A1 * comb_bl(2*pi * self.n * self.ui.f1 + phi1)
            self.title_str += r'Bandlim. Comb Signal'

        # ----------------------------------------------------------------------
        elif self.ui.stim == "am":
            self.x = self.ui.A1 * np.sin(2*pi * self.n * self.ui.f1 + phi1)\
                * self.ui.A2 * np.sin(2*pi * self.n * self.ui.f2 + phi2)
            self.title_str += r'AM Signal $A_1 \sin(2 \pi n f_1 + \varphi_1)\
                                \cdot A_2 \sin(2 \pi n f_2 + \varphi_2)$'
        elif self.ui.stim == "pmfm":
            self.x = self.ui.A1 * np.sin(2*pi * self.n * self.ui.f1 + phi1 +
                                         self.ui.A2 * np.sin(2*pi * self.n * self.ui.f2
                                                             + phi2))
            self.title_str += r'PM / FM Signal $A_1 \sin(2 \pi n f_1 +\
                            \varphi_1 + A_2 \sin(2 \pi n f_2 + \varphi_2))$'
        elif self.ui.stim == "formula":
            param_dict = {"A1": self.ui.A1, "A2": self.ui.A2,
                          "f1": self.ui.f1, "f2": self.ui.f2,
                          "phi1": self.ui.phi1, "phi2": self.ui.phi2,
                          "BW1": self.ui.BW1, "BW2": self.ui.BW2,
                          "f_S": fb.fil[0]['f_S'], "n": self.n}

            self.x = safe_numexpr_eval(self.ui.stim_formula, (self.ui.N_end,), param_dict)
            self.title_str += r'Formula Defined Signal'
        else:
            logger.error('Unknown stimulus format "{0}"'.format(self.ui.stim))
            return

        # ----------------------------------------------------------------------
        # Add noise to stimulus
        noi = 0
        if self.ui.noise == "none":
            pass
        elif self.ui.noise == "gauss":
            noi = self.ui.noi * np.random.randn(len(self.x))
            self.title_str += r' + Gaussian Noise'
        elif self.ui.noise == "uniform":
            noi = self.ui.noi * (np.random.rand(len(self.x))-0.5)
            self.title_str += r' + Uniform Noise'
        elif self.ui.noise == "prbs":
            noi = self.ui.noi * 2 * (np.random.randint(0, 2, len(self.x))-0.5)
            self.title_str += r' + PRBS Noise'
        elif self.ui.noise == "mls":
            # max_len_seq returns `sequence, state`. The state is not stored here,
            # hence, an identical sequence is created every time.
            noi = self.ui.noi * 2 * (sig.max_len_seq(int(np.ceil(np.log2(len(self.x)))),
                                        length=len(self.x), state=None)[0] - 0.5)
            self.title_str += r' + max. length sequence'
        elif self.ui.noise == "brownian":
            # brownian noise
            noi = np.cumsum(self.ui.noi * np.random.randn(len(self.x)))
            self.title_str += r' + Brownian Noise'
        else:
            logger.error('Unknown kind of noise "{}"'.format(self.ui.noise))
        if type(self.ui.noi) == complex:
            self.x = self.x.astype(complex) + noi
        else:
            self.x += noi
        # Add DC to stimulus when visible / enabled
        if self.ui.ledDC.isVisible:
            if type(self.ui.DC) == complex:
                self.x = self.x.astype(complex) + self.ui.DC
            else:
                self.x += self.ui.DC
            if self.ui.DC != 0:
                self.title_str += r' + DC'

        if self.fx_sim:
            self.title_str = r'$Fixpoint$ ' + self.title_str
            # setup quantizer for input quantization:
            self.q_i = fx.Fixed(fb.fil[0]['fxqc']['QI'])
            self.q_i.setQobj({'frmt': 'dec'})  # always use integer decimal format
            if np.any(np.iscomplex(self.x)):
                logger.warning(
                    "Complex stimulus: Only its real part will be processed by the "
                    "fixpoint filter!")

            self.x_q = self.q_i.fixp(self.x.real)

            self.sig_tx.emit(
                {'sender': __name__, 'fx_sim': 'send_stimulus',
                 'fx_stimulus': np.round(self.x_q * (1 << self.q_i.WF)).astype(int)})
            logger.debug("fx stimulus sent")

        self.needs_redraw[:] = [True] * 2

    # ------------------------------------------------------------------------------
    def calc_response(self):
        """
        (Re-)calculate ideal filter response `self.y` from stimulus `self.x` and
        the filter coefficients using `lfilter()`, `sosfilt()` or `filtfilt()`.

        Set the flag `self.cmplx` when response `self.y` or stimulus `self.x`
        are complex and make warning field visible.
        """

        self.bb = np.asarray(fb.fil[0]['ba'][0])
        self.aa = np.asarray(fb.fil[0]['ba'][1])
        if min(len(self.aa), len(self.bb)) < 2:
            logger.error('No proper filter coefficients: len(a), len(b) < 2 !')
            return

        logger.debug("Coefficient area = {0}".format(np.sum(np.abs(self.bb))))

        sos = np.asarray(fb.fil[0]['sos'])
        antiCausal = 'zpkA' in fb.fil[0]

        if len(sos) > 0 and not antiCausal:  # has second order sections and is causal
            y = sig.sosfilt(sos, self.x)
        elif antiCausal:
            y = sig.filtfilt(self.bb, self.aa, self.x, -1, None)
        else:  # no second order sections or antiCausals for current filter
            y = sig.lfilter(self.bb, self.aa, self.x)

        if self.ui.stim == "Step" and self.ui.chk_step_err.isChecked():
            dc = sig.freqz(self.bb, self.aa, [0])  # DC response of the system
            # subtract DC (final) value from response
            y[self.T1_int:] = y[self.T1_int:] - abs(dc[1])

        self.y = np.real_if_close(y, tol=1e3)  # tol specified in multiples of machine eps

        self.needs_redraw[:] = [True] * 2

        # Calculate imag. and real components from response
        self.cmplx = bool(np.any(np.iscomplex(self.y)) or np.any(np.iscomplex(self.x)))
        self.ui.lbl_stim_cmplx_warn.setVisible(self.cmplx)

    # ------------------------------------------------------------------------------
    def draw_response_fx(self, dict_sig=None):
        """
        Get Fixpoint results and plot them
        """
        if self.needs_calc:
            self.needs_redraw = [True] * 2
            # t_draw_start = time.process_time()
            self.y = np.asarray(dict_sig['fx_results'])
            if self.y is None:
                qstyle_widget(self.ui.but_run, "error")
                self.needs_calc = True
            else:
                self.needs_calc = False

                self.draw()
                qstyle_widget(self.ui.but_run, "normal")

                self.sig_tx.emit({'sender': __name__, 'fx_sim': 'finish'})

    # ------------------------------------------------------------------------
    def calc_fft(self):
        """
        (Re-)calculate FFTs of stimulus `self.X`, quantized stimulus `self.X_q`
        and response `self.Y` using the window function from `self.ui.win_dict['win']`.
        """
        # calculate FFT of stimulus / response
        N = self.ui.N
        win = self.ui.qfft_win_select.get_window(N) / self.ui.win_dict['cgain']
        if self.x is None:
            self.X = np.zeros(N)  # dummy result
            logger.warning("Stimulus is 'None', FFT cannot be calculated.")
        elif len(self.x) < self.ui.N_end:
            self.X = np.zeros(N)  # dummy result
            logger.warning(
                "Length of stimulus is {0} < N = {1}, FFT cannot be calculated."
                .format(len(self.x), self.ui.N_end))
        else:
            # multiply the  time signal with window function
            x_win = self.x[self.ui.N_start:self.ui.N_end] * win
            # calculate absolute value and scale by N_FFT
            self.X = np.fft.fft(x_win) / self.ui.N
            # self.X[0] = self.X[0] * np.sqrt(2) # correct value at DC

            if self.fx_sim:
                # same for fixpoint simulation
                x_q_win = self.q_i.fixp(self.x[self.ui.N_start:self.ui.N_end])\
                    * win
                self.X_q = np.fft.fft(x_q_win) / self.ui.N
                # self.X_q[0] = self.X_q[0] * np.sqrt(2) # correct value at DC

        if self.y is None or len(self.y) < self.ui.N_end:
            self.Y = np.zeros(self.ui.N_end-self.ui.N_start)  # dummy result
            if self.y is None:
                logger.warning("Transient response is 'None', FFT cannot be calculated.")
            else:
                logger.warning(
                    "Length of transient response is {0} < N = {1}, FFT cannot be "
                    "calculated.".format(len(self.y), self.ui.N_end))
        else:
            y_win = self.y[self.ui.N_start:self.ui.N_end] * win
            self.Y = np.fft.fft(y_win) / self.ui.N
            # self.Y[0] = self.Y[0] * np.sqrt(2) # correct value at DC

#        if self.ui.chk_win_freq.isChecked():
#            self.Win = np.abs(np.fft.fft(win)) / self.ui.N

        self.needs_redraw[1] = True   # redraw of frequency widget needed

###############################################################################
#        PLOTTING
###############################################################################

    def draw(self, arg=None):
        """
        (Re-)draw the figure without recalculation. When triggered by a signal-
        slot connection from a button, combobox etc., arg is a boolean or an
        integer representing the state of the widget. In this case,
        `needs_redraw` is set to True.
        """
        if type(arg) is not None:
            self.needs_redraw = [True] * 2

        if not hasattr(self, 'cmplx'):  # has response been calculated yet?
            logger.error("Response should have been calculated by now!")
            return

        if fb.fil[0]['freq_specs_unit'] == 'k':
            f_unit = ''
            t_unit = ''
            self.ui.lblFreq1.setText(self.ui.txtFreq1_k)
            self.ui.lblFreq2.setText(self.ui.txtFreq2_k)
        else:
            f_unit = fb.fil[0]['plt_fUnit']
            t_unit = fb.fil[0]['plt_tUnit'].replace(r"$\mu$", "&mu;")
            self.ui.lblFreq1.setText(self.ui.txtFreq1_f)
            self.ui.lblFreq2.setText(self.ui.txtFreq2_f)

        if f_unit in {"f_S", "f_Ny"}:
            unit_frmt = "i"  # italic
        else:
            unit_frmt = None  # don't print units like kHz in italic

        self.ui.lblFreqUnit1.setText(to_html(f_unit, frmt=unit_frmt))
        self.ui.lblFreqUnit2.setText(to_html(f_unit, frmt=unit_frmt))
        self.ui.lbl_TU1.setText(to_html(t_unit, frmt=unit_frmt))
        self.ui.lbl_TU2.setText(to_html(t_unit, frmt=unit_frmt))

        self.scale_i = self.scale_o = 1
        self.fx_min = -1.
        self.fx_max = 1.
        if self.fx_sim:  # fixpoint simulation enabled -> scale stimulus and response
            try:
                if self.ui.but_fx_scale.isChecked():
                    # display stimulus and response as integer values:
                    # - multiply stimulus by 2 ** WF
                    # - display response unscaled
                    self.scale_i = 1 << fb.fil[0]['fxqc']['QI']['WF']
                    self.fx_min = - (1 << fb.fil[0]['fxqc']['QO']['W']-1)
                    self.fx_max = -self.fx_min - 1
                else:
                    # display values scaled as "real world values"
                    self.scale_o = 1. / (1 << fb.fil[0]['fxqc']['QO']['WF'])
                    self.fx_min = -(1 << fb.fil[0]['fxqc']['QO']['WI'])
                    self.fx_max = -self.fx_min - self.scale_o

            except AttributeError as e:
                logger.error("Attribute error: {0}".format(e))
            except TypeError as e:
                logger.error(
                    "Type error: 'fxqc_dict'={0},\n{1}".format(fb.fil[0]['fxqc'], e))
            except ValueError as e:
                logger.error("Value error: {0}".format(e))

        idx = self.tabWidget.currentIndex()

        if idx == 0 and self.needs_redraw[0]:
            self.draw_time()
        elif idx == 1 and self.needs_redraw[1]:
            self.draw_freq()

    # ------------------------------------------------------------------------
    def _spgr_ui2params(self):
        """
        Update overlap and nfft parameters for spectrogram from UI
        """
        time_nfft_spgr = safe_eval(self.ui.led_time_nfft_spgr.text(),
                                   self.ui.time_nfft_spgr, return_type='int', sign='pos')
        if time_nfft_spgr <= self.ui.time_ovlp_spgr:
            logger.warning("N_FFT must be larger than N_OVLP!")
        else:
            self.ui.time_nfft_spgr = time_nfft_spgr
        self.ui.led_time_nfft_spgr.setText(str(self.ui.time_nfft_spgr))

        time_ovlp_spgr = safe_eval(self.ui.led_time_ovlp_spgr.text(),
                                   self.ui.time_ovlp_spgr, return_type='int',
                                   sign='poszero')
        if time_ovlp_spgr >= self.ui.time_nfft_spgr:
            logger.warning("N_OVLP must be less than N_FFT!")
        else:
            self.ui.time_ovlp_spgr = time_ovlp_spgr
        self.ui.led_time_ovlp_spgr.setText(str(self.ui.time_ovlp_spgr))

        self.draw()

# ----------------------------------------------------------------------------
    def _spgr_cmb(self):
        """
        Update spectrogram ui when signal selection combobox has been changed
        """
        spgr_en = qget_cmb_box(self.ui.cmb_plt_time_spgr) != 'none'

        self.ui.chk_log_spgr_time.setVisible(spgr_en)
        self.ui.lbl_time_nfft_spgr.setVisible(spgr_en)
        self.ui.led_time_nfft_spgr.setVisible(spgr_en)
        self.ui.lbl_time_ovlp_spgr.setVisible(spgr_en)
        self.ui.led_time_ovlp_spgr.setVisible(spgr_en)
        self.ui.cmb_mode_spgr_time.setVisible(spgr_en)
        self.ui.lbl_byfs_spgr_time.setVisible(spgr_en)
        self.ui.chk_byfs_spgr_time.setVisible(spgr_en)

        self.draw()

    # ------------------------------------------------------------------------
    def _log_mode_time(self):
        """
        Select / deselect log. mode for time domain and update self.ui.bottom_t
        """
        if qget_cmb_box(self.ui.cmb_mode_spgr_time) in {'phase', 'angle'}:
            # must be linear if mode is 'angle' or 'phase'
            self.ui.chk_log_spgr_time.setChecked(False)
            self.ui.chk_log_spgr_time.setEnabled(False)
        else:
            self.ui.chk_log_spgr_time.setEnabled(True)

        log = self.ui.chk_log_time.isChecked() or\
            (self.ui.chk_log_spgr_time.isChecked() and self.spgr)
        self.ui.lbl_log_bottom_time.setVisible(log)
        self.ui.led_log_bottom_time.setVisible(log)
        if log:
            self.ui.bottom_t = safe_eval(self.ui.led_log_bottom_time.text(),
                                         self.ui.bottom_t, return_type='float')
            self.ui.led_log_bottom_time.setText(str(self.ui.bottom_t))
        else:
            self.ui.bottom_t = 0

    # ------------------------------------------------------------------------
    def _log_mode_freq(self):
        """
        Select / deselect log. mode for frequency domain and update
        self.ui.bottom_f
        """

        log = self.ui.chk_log_freq.isChecked()
        self.ui.lbl_log_bottom_freq.setVisible(log)
        self.ui.led_log_bottom_freq.setVisible(log)
        if log:
            self.ui.bottom_f = safe_eval(self.ui.led_log_bottom_freq.text(),
                                         self.ui.bottom_f, return_type='float',
                                         sign='neg')
            self.ui.led_log_bottom_freq.setText(str(self.ui.bottom_f))
        else:
            self.ui.bottom_f = 0

    # ------------------------------------------------------------------------
    def draw_data(self, plt_style, ax, x, y, bottom=0, label='',
                  plt_fmt={}, mkr_fmt={}, **args):
        """
        Plot x, y data (numpy arrays with equal length) in a plot style defined
        by `plt_style`.

        Parameters
        ----------
        plt_style : str
            one of "line", "stem", "steps", "dots"
        ax : matplotlib axis
            Handle to the axis where signal is to be plotted
        x : array-like
            x-axis: time or frequency data
        y : array-like
            y-data
        bottom : float
            Bottom line for stem plot. The default is 0.
        label : str
            Plot label
        plt_fmt : dict
            Line styles (color, linewidth etc.) for plotting (default: None).
        mkr_fmt : dict
            Marker styles
        args : dictionary with additional keys and values. As they might not be
            compatible with every plot style, they have to be added individually

        Returns
        -------
        handle : Handle to plot

        """
        # plot lines
        if plt_fmt is None:
            plt_fmt = {}
        if plt_style == "line":
            handle, = ax.plot(x, y, label=label, **plt_fmt)
        elif plt_style == "stem":
            handle = stems(x, y, ax=ax, bottom=bottom, label=label, mkr_fmt=mkr_fmt,
                           **plt_fmt)
        elif plt_style == "steps":
            handle, = ax.plot(x, y, drawstyle='steps-mid', label=label, **plt_fmt)
        elif plt_style == "dots":
            handle = scatter(x, y, ax=ax, label=label, mkr_fmt=mkr_fmt)
        else:
            handle = []

        # plot markers (and "dots" as well)
        if mkr_fmt and plt_style not in {'stem', 'dots'}:
            handle_mkr = scatter(x, y, ax=ax, mkr_fmt=mkr_fmt)
            # join handles to plot them on top of each other in the legend
            handle = (handle, handle_mkr)
        return handle

    # ================ Plotting routine time domain =========================
    def _init_axes_time(self):
        """
        Clear and initialize the axes of the time domain matplotlib widgets
        """
        self.t = self.n * fb.fil[0]['T_S']

        self.plt_time_resp = qget_cmb_box(self.ui.cmb_plt_time_resp).replace("*", "")
        self.plt_time_stim = qget_cmb_box(self.ui.cmb_plt_time_stim).replace("*", "")
        self.plt_time_stmq = qget_cmb_box(self.ui.cmb_plt_time_stmq).replace("*", "")
        self.plt_time_spgr = qget_cmb_box(self.ui.cmb_plt_time_spgr)
        self.spgr = self.plt_time_spgr != "none"

        self.plt_time_enabled = self.plt_time_resp != "none"\
            or self.plt_time_stim != "none"\
            or (self.plt_time_stmq != "none" and self.fx_sim)

        self.mplwidget_t.fig.clf()  # clear figure with axes

        num_subplots = max(int(self.plt_time_enabled) + self.cmplx + self.spgr, 1)

        # return a one-dimensional list with num_subplots axes
        self.axes_time = self.mplwidget_t.fig.subplots(
            nrows=num_subplots, ncols=1, sharex=True, squeeze=False)[:, 0]

        self.ax_r = self.axes_time[0]
        self.ax_r.cla()

        if self.cmplx:
            self.ax_i = self.axes_time[1]
            self.ax_i.cla()
            self.mplwidget_t.fig.align_ylabels()

        if self.spgr:
            self.ax_s = self.axes_time[-1]  # assign last axis

        if self.ACTIVE_3D:  # not implemented / tested yet
            self.ax3d = self.mplwidget_t.fig.add_subplot(111, projection='3d')

        for ax in self.axes_time:
            ax.xaxis.tick_bottom()  # remove axis ticks on top
            ax.yaxis.tick_left()  # remove axis ticks right
            ax.xaxis.set_minor_locator(AutoMinorLocator())  # enable minor ticks
            ax.yaxis.set_minor_locator(AutoMinorLocator())

    # ------------------------------------------------------------------------
    def draw_time(self):
        """
        (Re-)draw the time domain mplwidget
        """
        if self.y is None:  # safety net for empty responses
            for ax in self.mplwidget_t.fig.get_axes():  # remove all axes
                self.mplwidget_t.fig.delaxes(ax)
            return

        self._init_axes_time()
        self._log_mode_time()

        # '$h... = some impulse response, don't change
        if not self.H_str or self.H_str[1] != 'h':
            self.H_str = ''
            if qget_cmb_box(self.ui.cmb_plt_time_stim) != "none":
                self.H_str += r'$x$, '
            if qget_cmb_box(self.ui.cmb_plt_time_stmq) != "none" and self.fx_sim:
                self.H_str += r'$x_Q$, '
            if qget_cmb_box(self.ui.cmb_plt_time_resp) != "none":
                self.H_str += r'$y$'
            self.H_str = self.H_str.rstrip(', ')

        if "*" in qget_cmb_box(self.ui.cmb_plt_time_stim):
            fmt_mkr_stim = self.fmt_mkr_stim
        else:
            fmt_mkr_stim = {'marker': ''}

        if "*" in qget_cmb_box(self.ui.cmb_plt_time_stmq):
            fmt_mkr_stmq = self.fmt_mkr_stmq
        else:
            fmt_mkr_stmq = {'marker': ''}

        if "*" in qget_cmb_box(self.ui.cmb_plt_time_resp):
            fmt_mkr_resp = self.fmt_mkr_resp
        else:
            fmt_mkr_resp = {'marker': ''}

        # fixpoint simulation enabled -> scale stimulus and response
        if self.fx_sim:
            x_q = self.x_q * self.scale_i
            if self.ui.chk_log_time.isChecked():
                x_q = np.maximum(20 * np.log10(abs(x_q)), self.ui.bottom_t)

            logger.debug("self.scale I:{0} O:{1}".format(self.scale_i, self.scale_o))
        else:
            x_q = None

        x = self.x * self.scale_i
        y = self.y * self.scale_o
        win = self.ui.qfft_win_select.get_window(self.ui.N)
        if self.cmplx:
            x_r = x.real
            x_i = x.imag
            y_r = y.real
            y_i = y.imag
            lbl_x_r = "$x_r[n]$"
            lbl_x_i = "$x_i[n]$"
            lbl_y_r = "$y_r[n]$"
            lbl_y_i = "$y_i[n]$"
        else:
            x_r = x.real
            x_i = None
            y_r = y
            y_i = None
            lbl_x_r = "$x[n]$"
            lbl_y_r = "$y[n]$"

        # log. scale for stimulus / response time domain:
        if self.ui.chk_log_time.isChecked():
            bottom_t = self.ui.bottom_t
            win = np.maximum(20 * np.log10(
                abs(self.ui.qfft_win_select.get_window(self.ui.N))), self.ui.bottom_t)
            x_r = np.maximum(20 * np.log10(abs(x_r)), self.ui.bottom_t)
            y_r = np.maximum(20 * np.log10(abs(y_r)), self.ui.bottom_t)

            if self.cmplx:
                x_i = np.maximum(20 * np.log10(abs(x_i)), self.ui.bottom_t)
                y_i = np.maximum(20 * np.log10(abs(y_i)), self.ui.bottom_t)
                H_i_str = r'$|\Im\{$' + self.H_str + r'$\}|$' + ' in dBV'
                H_str =   r'$|\Re\{$' + self.H_str + r'$\}|$' + ' in dBV'
            else:
                H_str = '$|$' + self.H_str + '$|$ in dBV'

            fx_min = 20*np.log10(abs(self.fx_min))
            fx_max = fx_min
        else:
            bottom_t = 0
            fx_max = self.fx_max
            fx_min = self.fx_min
            if self.cmplx:
                H_i_str = r'$\Im\{$' + self.H_str + r'$\}$ in V'
                H_str = r'$\Re\{$' + self.H_str + r'$\}$ in V'
            else:
                H_str = self.H_str + ' in V'

        if self.ui.chk_fx_limits.isChecked() and self.fx_sim:
            self.ax_r.axhline(fx_max, 0, 1, color='k', linestyle='--')
            self.ax_r.axhline(fx_min, 0, 1, color='k', linestyle='--')

        h_r = []  # plot handles (real part)
        h_i = []  # plot handles (imag. part)
        l_r = []  # labels (real part)
        l_i = []  # labels (imag. part)

        # --------------- Stimulus plot --------------------------------------
        if self.plt_time_stim != "none":
            h_r.append(self.draw_data(
                self.plt_time_stim, self.ax_r, self.t[self.ui.N_start:],
                x_r[self.ui.N_start:], label=lbl_x_r, bottom=bottom_t,
                plt_fmt=self.fmt_plot_stim, mkr_fmt=fmt_mkr_stim))
            l_r += [lbl_x_r]

        # -------------- Stimulus <q> plot ------------------------------------
        if x_q is not None and self.plt_time_stmq != "none":
            h_r.append(self.draw_data(
                self.plt_time_stmq, self.ax_r, self.t[self.ui.N_start:],
                x_q[self.ui.N_start:], label='$x_q[n]$', bottom=bottom_t,
                plt_fmt=self.fmt_plot_stmq, mkr_fmt=fmt_mkr_stmq))
            l_r += ['$x_q[n]$']
        # --------------- Response plot ----------------------------------
        if self.plt_time_resp != "none":
            h_r.append(self.draw_data(
                self.plt_time_resp, self.ax_r, self.t[self.ui.N_start:],
                y_r[self.ui.N_start:], label=lbl_y_r, bottom=bottom_t,
                plt_fmt=self.fmt_plot_resp, mkr_fmt=fmt_mkr_resp))
            l_r += [lbl_y_r]
        # --------------- Window plot ----------------------------------
        if self.ui.chk_win_time.isChecked():
            h_r.append(self.ax_r.plot(
                self.t[self.ui.N_start:], win, c="gray",
                label=self.ui.win_dict['cur_win_name'])[0])
            l_r += [self.ui.win_dict['cur_win_name']]
        # --------------- LEGEND (real part) ----------------------------------
        if self.plt_time_enabled:
            self.ax_r.legend(h_r, l_r, loc='best', fontsize='small', fancybox=True,
                             framealpha=0.7)

        # --------------- Complex response ----------------------------------
        if self.cmplx:
            if self.plt_time_stim != "none":
                # --- imag. part of stimulus -----
                h_i.append(self.draw_data(
                    self.plt_time_stim, self.ax_i, self.t[self.ui.N_start:],
                    x_i[self.ui.N_start:], label=lbl_x_i, bottom=bottom_t,
                    plt_fmt=self.fmt_plot_stim, mkr_fmt=fmt_mkr_stim))
                l_i += [lbl_x_i]

            if self.plt_time_resp != "none":
                # --- imag. part of response -----
                h_i.append(self.draw_data(
                    self.plt_time_resp, self.ax_i, self.t[self.ui.N_start:],
                    y_i[self.ui.N_start:], label=lbl_y_i, bottom=bottom_t,
                    plt_fmt=self.fmt_plot_resp, mkr_fmt=fmt_mkr_resp))
                l_i += [lbl_y_i]

            # --- labels and markers -----
            # plt.setp(ax_r.get_xticklabels(), visible=False)
            # is shorter but imports matplotlib, set property directly instead:
            [label.set_visible(False) for label in self.ax_r.get_xticklabels()]
            # self.ax_r.set_ylabel(H_str + r'$\rightarrow $') # common x-axis

            self.ax_i.set_ylabel(H_i_str + r'$\rightarrow $')
            self.ax_i.legend(h_i, l_i, loc='best', fontsize='small', fancybox=True,
                             framealpha=0.7)
        # else:
#            self.ax_r.set_xlabel(fb.fil[0]['plt_tLabel'])
        self.ax_r.set_ylabel(H_str + r'$\rightarrow $')

        # --------------- Spectrogram -----------------------------------------
        if self.spgr:
            if 2 * self.ui.time_nfft_spgr - self.ui.time_ovlp_spgr > self.ui.N:
                logger.warning(
                    "Only one segment is calculated since 2 NFFT - N_OVLP = {0} > N = {1}"
                    .format(2 * self.ui.time_nfft_spgr - self.ui.time_ovlp_spgr,
                            self.ui.N))
            if self.ui.time_nfft_spgr > self.ui.N:
                logger.warning(
                    "NFFT per segment = {0} is larger than number N of data points {1}, "
                    "setting NFFT = N.".format(self.ui.time_nfft_spgr, self.ui.N))
                self.ui.time_nfft_spgr = self.ui.N
            if self.ui.time_ovlp_spgr >= self.ui.time_nfft_spgr:
                logger.warning("N_OVLP must be less than NFFT, setting N_OVLP = 0.")
                self.ui.time_ovlp_spgr = 0

            self.ui.led_time_nfft_spgr.setText(str(self.ui.time_nfft_spgr))
            self.ui.led_time_ovlp_spgr.setText(str(self.ui.time_ovlp_spgr))

            if self.plt_time_spgr == "xn":
                s = x[self.ui.N_start:]
                sig_lbl = 'X'
            elif self.plt_time_spgr == "xqn":
                s = self.x_q[self.ui.N_start:]
                sig_lbl = 'X_Q'
            elif self.plt_time_spgr == "yn":
                s = y[self.ui.N_start:]
                sig_lbl = 'Y'
            else:
                s = None
                sig_lbl = 'None'
            spgr_args = r"$({0}, {1})$".format(fb.fil[0]['plt_tLabel'][1],
                                               fb.fil[0]['plt_fLabel'][1])
            # ------ onesided / twosided ------------
            if fb.fil[0]['freqSpecsRangeType'] == 'half':
                sides = 'onesided'
            else:
                sides = 'twosided'

            # ------- Unit / Mode ----------------------
            mode = qget_cmb_box(self.ui.cmb_mode_spgr_time, data=True)
            self.ui.lbl_byfs_spgr_time.setVisible(mode == 'psd')
            self.ui.chk_byfs_spgr_time.setVisible(mode == 'psd')
            spgr_pre = ""
            dB_scale = 20  # default log scale for magnitude in dB
            if self.ui.chk_log_spgr_time.isChecked():
                dB_unit = "dB"
            else:
                dB_unit = ""
            if mode == "psd":
                spgr_symb = r"$S_{{{0}}}$".format(sig_lbl.lower()+sig_lbl.lower())
                dB_scale = 10  # log scale for PSD
            elif mode in {"magnitude", "complex"}:
                # "complex" cannot be plotted directly
                spgr_pre = r"|"
                spgr_symb = "${0}$".format(sig_lbl)
                spgr_unit = r"| in {0}V".format(dB_unit)

            elif mode in {"angle", "phase"}:
                spgr_unit = r" in rad"
                spgr_symb = "${0}$".format(sig_lbl)
                spgr_pre = r"$\angle$"
            else:
                logger.warning("Unknown spectrogram mode {0}, falling back to 'psd'"
                               .format(mode))
                mode = "psd"

            # Only valid and visible for Power Spectral Density
            if self.ui.chk_byfs_spgr_time.isChecked():
                # scale result by f_S
                Hz_unit = fb.fil[0]['plt_fUnit']
                # special treatment for PSD units needed
                if self.ui.chk_log_spgr_time.isChecked():
                    spgr_unit = r" in dB re W / {0}".format(Hz_unit)
                else:
                    spgr_unit = r" in W / {0}".format(Hz_unit)
                scaling = "density"
            else:
                # display result in W / bin
                spgr_unit = r" in {0}W".format(dB_unit)
                scaling = "spectrum"

            # ------- lin / log ----------------------
            if self.ui.chk_log_spgr_time.isChecked():
                scale = 'dB'
                # 10 log10 for 'psd', otherwise 20 log10
                bottom_spgr = self.ui.bottom_t
            else:
                scale = 'linear'
                bottom_spgr = 0

            t_range = (self.t[self.ui.N_start], self.t[-1])
            # hidden images: https://scipython.com/blog/hidden-images-in-spectrograms/

# =============================================================================
            win = self.ui.qfft_win_select.get_window(self.ui.time_nfft_spgr)
            if False:
                Sxx, f, t, im = self.ax_s.specgram(
                    s, Fs=fb.fil[0]['f_S'], NFFT=self.ui.time_nfft_spgr,
                    noverlap=self.ui.time_ovlp_spgr, pad_to=None, xextent=t_range,
                    sides=sides, scale_by_freq=self.ui.chk_byfs_spgr_time.isChecked(),
                    mode=mode, scale=scale, vmin=bottom_spgr, cmap=None)
                # Fs : sampling frequency for scaling
                # window: callable or ndarray, default window_hanning
                # NFFT : data points for each block
                # pad_to: create zero-padding
                # xextent: image extent along x-axis; None or (xmin, xmax)
                # scale_by_freq: True scales power spectral density by f_S

                cbar = self.mplwidget_t.fig.colorbar(im, ax=self.ax_s, aspect=30,
                                                     pad=0.005)
                cbar.ax.set_ylabel(spgr_pre + spgr_symb + spgr_args + spgr_unit)

                self.ax_s.set_ylabel(fb.fil[0]['plt_fLabel'])
            else:
                f, t, Sxx = sig.spectrogram(
                    s, fb.fil[0]['f_S'], window=win,  # ('tukey', 0.25),
                    nperseg=self.ui.time_nfft_spgr, noverlap=self.ui.time_ovlp_spgr,
                    nfft=None, return_onesided=fb.fil[0]['freqSpecsRangeType'] == 'half',
                    scaling=scaling, mode=mode, detrend='constant')
                # Fs : sampling frequency for scaling
                # window: callable or ndarray, default window_hanning
                # nperseg : data points for each segment
                # noverlap : number of overlapping points between segments
                # nfft: = nperseg by default, can be larger to create zero-padding
                # return_onesided : For complex data, a two-sided spectrum is
                #                   returned always
                # scaling: 'density' scales power spectral density by f_S,
                #          'spectrum' returns power spectrum in V**2
                # mode: 'psd', 'complex','magnitude','angle', 'phase' (no unwrapping)

    #            col_mesh = self.ax_s.pcolormesh(t, np.fft.fftshift(f),
    #                           np.fft.fftshift(Sxx, axes=0), shading='gouraud')
                # self.ax_s.colorbar(col_mesh)

                if self.ui.chk_log_spgr_time.isChecked():
                    Sxx = np.maximum(dB_scale * np.log10(np.abs(Sxx)), self.ui.bottom_t)
                # shading: 'auto', 'gouraud', 'nearest'
                col_mesh = self.ax_s.pcolormesh(t, f, Sxx, shading='auto')
                cbar = self.mplwidget_t.fig.colorbar(col_mesh, ax=self.ax_s, aspect=30,
                                                     pad=0.005)
                cbar.ax.set_ylabel(spgr_pre + spgr_symb + spgr_args + spgr_unit)

                self.ax_s.set_ylabel(fb.fil[0]['plt_fLabel'])

        # --------------- 3D Complex  -----------------------------------------
        if self.ACTIVE_3D:  # not implemented / tested yet
            # plotting the stems
            for i in range(self.ui.N_start, self.ui.N_end):
                self.ax3d.plot([self.t[i], self.t[i]], [y_r[i], y_r[i]], [0, y_i[i]],
                               '-', linewidth=2, alpha=.5)

            # plotting a circle on the top of each stem
            self.ax3d.plot(
                self.t[self.ui.N_start:], y_r[self.ui.N_start:], y_i[self.ui.N_start:],
                'o', markersize=8, markerfacecolor='none', label='$y[n]$')

            self.ax3d.set_xlabel('x')
            self.ax3d.set_ylabel('y')
            self.ax3d.set_zlabel('z')

        # --------------- Title and common labels ---------------------------
        self.axes_time[-1].set_xlabel(fb.fil[0]['plt_tLabel'])
        self.axes_time[0].set_title(self.title_str)
        self.ax_r.set_xlim([self.t[self.ui.N_start], self.t[self.ui.N_end-1]])
        # expand_lim(self.ax_r, 0.02)

        self.redraw()  # redraw currently active mplwidget

        self.needs_redraw[0] = False

    # ========================================================================
    # Frequency Plots
    # ========================================================================
    def _init_axes_freq(self):
        """
        Clear the axes of the frequency domain matplotlib widgets and
        calculate the fft
        """
        self.plt_freq_resp = qget_cmb_box(self.ui.cmb_plt_freq_resp).replace("*", "")
        self.plt_freq_stim = qget_cmb_box(self.ui.cmb_plt_freq_stim).replace("*", "")
        self.plt_freq_stmq = qget_cmb_box(self.ui.cmb_plt_freq_stmq).replace("*", "")

        self.plt_freq_enabled = self.plt_freq_stim != "none"\
            or self.plt_freq_stmq != "none"\
            or self.plt_freq_resp != "none"

        # if not self.ui.chk_log_freq.isChecked() \
        # and len(self.mplwidget_f.fig.get_axes()) == 2:
        # get rid of second axis when returning from log mode by clearing all
        #    self.mplwidget_f.fig.clear()

        self.mplwidget_f.fig.clf()  # clear figure with axes

        self.en_re_im_f = qget_cmb_box(self.ui.cmb_freq_display) == "re_im"
        self.en_mag_phi_f = qget_cmb_box(self.ui.cmb_freq_display) == "mag_phi"

        num_subplots_f = 1 + self.en_re_im_f + self.en_mag_phi_f

        self.axes_f = self.mplwidget_f.fig.subplots(
            nrows=num_subplots_f, ncols=1, sharex=True, squeeze=False)[:, 0]
        self.ax_f1 = self.axes_f[0]

        # for ax in self.axes_f:
        #    ax.cla()

        if self.ui.chk_log_freq.isChecked():
            # and len(self.mplwidget_f.fig.get_axes()) == 1:??
            # create second axis scaled for noise power scale if it doesn't exist yet
            self.ax_f1_noise = self.ax_f1.twinx()
            self.ax_f1_noise.is_twin = True

        self.ax_f1.xaxis.tick_bottom()  # remove axis ticks on top
        self.ax_f1.yaxis.tick_left()  # remove axis ticks right
        self.ax_f1.xaxis.set_minor_locator(AutoMinorLocator())  # enable minor ticks
        self.ax_f1.yaxis.set_minor_locator(AutoMinorLocator())

        if self.en_re_im_f or self.en_mag_phi_f:
            self.ax_f2 = self.axes_f[1]
            self.ax_f2.xaxis.tick_bottom()  # remove axis ticks on top
            self.ax_f2.yaxis.tick_left()  # remove axis ticks right
            self.ax_f2.xaxis.set_minor_locator(AutoMinorLocator())  # enable minor ticks
            self.ax_f2.yaxis.set_minor_locator(AutoMinorLocator())

        self.calc_fft()

    # ------------------------------------------------------------------------
    def draw_freq(self):
        """
        (Re-)draw the frequency domain mplwidget
        """
        self._init_axes_freq()
        self._log_mode_freq()

        nenbw = self.ui.win_dict['nenbw']
        cgain = self.ui.win_dict['cgain']

        plt_response = self.plt_freq_resp != "none"
        plt_stimulus = self.plt_freq_stim != "none"
        plt_stimulus_q = self.plt_freq_stmq != "none" and self.fx_sim

        if "*" in qget_cmb_box(self.ui.cmb_plt_freq_stim):
            fmt_mkr_stim = self.fmt_mkr_stim
        else:
            fmt_mkr_stim = {'marker': ''}

        if "*" in qget_cmb_box(self.ui.cmb_plt_freq_stmq):
            fmt_mkr_stmq = self.fmt_mkr_stmq
        else:
            fmt_mkr_stmq = {'marker': ''}

        if "*" in qget_cmb_box(self.ui.cmb_plt_freq_resp):
            fmt_mkr_resp = self.fmt_mkr_resp
        else:
            fmt_mkr_resp = {'marker': ''}

        # en_re_im_f = qget_cmb_box(self.ui.cmb_freq_display) == "re_im"

        H_F_str = ""
        ejO_str = r"$(\mathrm{e}^{\mathrm{j} \Omega})$"
        if self.plt_freq_enabled or self.ui.chk_Hf.isChecked():
            if plt_stimulus:
                H_F_str += r'$X$, '
            if plt_stimulus_q:
                H_F_str += r'$X_Q$, '
            if plt_response:
                H_F_str += r'$Y$, '
            if self.ui.chk_Hf.isChecked():
                H_F_str += r'$H_{id}$, '
            H_F_str = H_F_str.rstrip(', ') + ejO_str

            F_range = fb.fil[0]['freqSpecsRange']

            if fb.fil[0]['freq_specs_unit'] == 'k':
                # By default, k = params['N_FFT'] which is used for the calculation
                # of the non-transient tabs and for F_id / H_id here.
                # Here, the frequency axes must be scaled to fit the number of
                # frequency points self.ui.N
                F_range = [f * self.ui.N / fb.fil[0]['f_max'] for f in F_range]
                f_max = self.ui.N
            else:
                f_max = fb.fil[0]['f_max']

            # freqz-based ideal frequency response:
            F_id, H_id = calc_Hcomplex(fb.fil[0], params['N_FFT'], True, fs=f_max)
            # frequency vector for FFT-based frequency plots:
            F = np.fft.fftfreq(self.ui.N, d=1. / f_max)
        # -----------------------------------------------------------------
        # Scale frequency response and calculate power
        # -----------------------------------------------------------------
        # - Scale signals
        # - Calculate total power P from FFT, corrected by window equivalent noise
        #   bandwidth and fixpoint scaling (scale_i / scale_o)
        # - Correct scale for single-sided spectrum
        # - Scale impulse response with N_FFT to calculate frequency response if requested
            if self.ui.chk_freq_norm_impz.isVisible()\
                and self.ui.chk_freq_norm_impz.isEnabled()\
                and self.ui.chk_freq_norm_impz.isChecked():
                freq_resp = True  # calculate frequency response from impulse response
                scale_impz = self.ui.N
                if self.ui.stim == "dirac":
                    pass
                elif self.ui.stim == "sinc":
                    scale_impz *= self.ui.f1 * 2
                elif self.ui.stim == "gauss":
                    scale_impz *= self.ui.f1 * 2 * self.ui.BW1
                elif self.ui.stim == "rect":
                    scale_impz /= self.ui.TW1
            else:
                freq_resp = False
                scale_impz = 1.

            # scale with window NENBW for correct power calculation
            P_scale = scale_impz / nenbw
            if plt_stimulus:
                # scale display of frequency response
                Px = np.sum(np.square(np.abs(self.X))) * P_scale
                if fb.fil[0]['freqSpecsRangeType'] == 'half' and not freq_resp:
                    X = calc_ssb_spectrum(self.X) * self.scale_i * scale_impz
                else:
                    X = self.X * self.scale_i * scale_impz

            if plt_stimulus_q:
                Pxq = np.sum(np.square(np.abs(self.X_q))) * P_scale
                if fb.fil[0]['freqSpecsRangeType'] == 'half' and not freq_resp:
                    X_q = calc_ssb_spectrum(self.X_q) * self.scale_i * scale_impz
                else:
                    X_q = self.X_q * self.scale_i * scale_impz

            if plt_response:
                Py = np.sum(np.square(np.abs(self.Y * self.scale_o))) * P_scale
                if fb.fil[0]['freqSpecsRangeType'] == 'half' and not freq_resp:
                    Y = calc_ssb_spectrum(self.Y) * self.scale_o * scale_impz
                else:
                    Y = self.Y * self.scale_o * scale_impz

            # ----------------------------------------------------------------
            # Scale and shift frequency range
            # ----------------------------------------------------------------
            if fb.fil[0]['freqSpecsRangeType'] == 'sym':
                # display -f_S/2 ... f_S/2 ->  shift X, Y and F using fftshift()
                if plt_response:
                    Y = np.fft.fftshift(Y)

                if plt_stimulus:
                    X = np.fft.fftshift(X)

                if plt_stimulus_q:
                    X_q = np.fft.fftshift(X_q)

                F    = np.fft.fftshift(F)

                # shift H_id and F_id by f_S/2
                F_id -= f_max/2
                H_id = np.fft.fftshift(H_id)
                if not freq_resp:
                    H_id /= 2

            elif fb.fil[0]['freqSpecsRangeType'] == 'half':
                # display 0 ... f_S/2 -> only use the first half of X, Y and F
                if plt_response:
                    Y = Y[0:self.ui.N//2]
                if plt_stimulus:
                    X = X[0:self.ui.N//2]
                if plt_stimulus_q:
                    X_q = X_q[0:self.ui.N//2]

                F    = F[0:self.ui.N//2]
                F_id = F_id[0:params['N_FFT']//2]
                H_id = H_id[0:params['N_FFT']//2]

            else:  # fb.fil[0]['freqSpecsRangeType'] == 'whole'
                # display 0 ... f_S -> shift frequency axis
                F    = np.fft.fftshift(F) + f_max/2.
                if not freq_resp:
                    H_id /= 2

            # -----------------------------------------------------------------
            # Calculate log FFT and power if selected, set units
            # -----------------------------------------------------------------
            if self.ui.chk_log_freq.isChecked():
                unit = " in dBV"
                unit_P = "dBW"
                H_F_pre = "|"
                H_F_post = "|"

                nenbw = 10 * np.log10(nenbw)
                cgain = 20 * np.log10(cgain)

                if plt_stimulus:
                    Px = 10*np.log10(Px)
                    if self.en_re_im_f:
                        X_r = np.maximum(20 * np.log10(np.abs(X.real)), self.ui.bottom_f)
                        X_i = np.maximum(20 * np.log10(np.abs(X.imag)), self.ui.bottom_f)
                    else:
                        X_r = np.maximum(20 * np.log10(np.abs(X)), self.ui.bottom_f)
                        if self.en_mag_phi_f:
                            X_i = angle_zero(X)

                if plt_stimulus_q:
                    Pxq = 10*np.log10(Pxq)
                    if self.en_re_im_f:
                        X_q_r = np.maximum(20 * np.log10(np.abs(X_q.real)),
                                           self.ui.bottom_f)
                        X_q_i = np.maximum(20 * np.log10(np.abs(X_q.imag)),
                                           self.ui.bottom_f)
                    else:
                        X_q_r = np.maximum(20 * np.log10(np.abs(X_q)), self.ui.bottom_f)
                        if self.en_mag_phi_f:
                            X_q_i = angle_zero(X_q)

                if plt_response:
                    Py = 10*np.log10(Py)
                    if self.en_re_im_f:
                        Y_r = np.maximum(20 * np.log10(np.abs(Y.real)), self.ui.bottom_f)
                        Y_i = np.maximum(20 * np.log10(np.abs(Y.imag)), self.ui.bottom_f)
                    else:
                        Y_r = np.maximum(20 * np.log10(np.abs(Y)), self.ui.bottom_f)
                        if self.en_mag_phi_f:
                            Y_i = angle_zero(Y)

                if self.ui.chk_Hf.isChecked():
                    if self.en_re_im_f:
                        H_id_r = np.maximum(20 * np.log10(np.abs(H_id.real)),
                                            self.ui.bottom_f)
                        H_id_i = np.maximum(20 * np.log10(np.abs(H_id.imag)),
                                            self.ui.bottom_f)
                    else:
                        H_id_r = np.maximum(20 * np.log10(np.abs(H_id)), self.ui.bottom_f)
                        if self.en_mag_phi_f:
                            H_id_i = angle_zero(H_id)

            else:  # non log
                H_F_pre = ""
                H_F_post = ""
                if plt_stimulus:
                    if self.en_re_im_f:
                        X_r = X.real
                        X_i = X.imag
                    else:
                        X_r = np.abs(X)
                        if self.en_mag_phi_f:
                            X_i = angle_zero(X)

                if plt_stimulus_q:
                    if self.en_re_im_f:
                        X_q_r = X_q.real
                        X_q_i = X_q.imag
                    else:
                        X_q_r = np.abs(X_q)
                        if self.en_mag_phi_f:
                            X_q_i = angle_zero(X_q)

                if plt_response:
                    if self.en_re_im_f:
                        Y_r = Y.real
                        Y_i = Y.imag
                    else:
                        Y_r = np.abs(Y)
                        if self.en_mag_phi_f:
                            Y_i = angle_zero(Y)

                if self.ui.chk_Hf.isChecked():
                    if self.en_re_im_f:
                        H_id_r = H_id.real
                        H_id_i = H_id.imag
                    else:
                        H_id_r = np.abs(H_id)
                        if self.en_mag_phi_f:
                            H_id_i = angle_zero(H_id)

                unit = " in V"
                unit_P = "W"

            if self.en_re_im_f:
                H_Fi_str = H_F_pre + r'$\Im\{$' + H_F_str + r'$\}$' + H_F_post\
                    + unit + r" $\rightarrow$"
                H_Fr_str = r'$\Re\{$' + H_F_str + r'$\}$'
            elif self.en_mag_phi_f:
                H_Fi_str = r'$\angle($' + H_F_str + r'$)$' + " in rad "\
                    + r" $\rightarrow$"
                H_Fr_str = "|" + H_F_str + "|"
            else:
                H_F_pre = "|"
                H_Fr_str = H_F_str
                H_Fi_str = 'undefined'
                H_F_post = "|"

            H_Fr_str = H_F_pre + H_Fr_str + H_F_post + unit + r" $\rightarrow$"

            # -----------------------------------------------------------------
            # --------------- Plot stimuli and response -----------------------
            # -----------------------------------------------------------------
            show_info = self.ui.chk_show_info_freq.isChecked()
            h_r = []  # plot handles (real / mag. part)
            h_i = []  # plot handles (imag. / phase part)
            l_r = []  # labels (real / mag. part)
            l_i = []  # labels (imag. / phase part)
            patch_trans = mpl_patches.Rectangle((0, 0), 1, 1, fc="w", fill=False,
                                                ec=None, lw=0)  # ec = 'blue', alpha=0.5
            lbl_empty = "        "

            # -------------------- Plot H_id ----------------------------------
            if self.ui.chk_Hf.isChecked():
                label_re = "$|H_{id}$" + ejO_str + "|"
                if self.en_re_im_f:
                    label_re = "$H_{id,r}$" + ejO_str
                    label_im = "$H_{id,i}$" + ejO_str
                    h_i.append(self.ax_f2.plot(F_id, H_id_i, c="gray", label=label_im)[0])
                    l_i += [label_im]
                elif self.en_mag_phi_f:
                    label_im = r"$\angle H_{id}$" + ejO_str
                    h_i.append(self.ax_f2.plot(F_id, H_id_i, c="gray", label=label_im)[0])
                h_r.append(self.ax_f1.plot(F_id, H_id_r, c="gray", label=label_re)[0])
                if show_info:
                    l_r += [lbl_empty, label_re, lbl_empty]
                    h_r += [patch_trans, patch_trans]
                else:
                    l_r += [label_re]

            # -------------------- Plot X -------------------------------------
            if plt_stimulus:
                label_re = "|$X$" + ejO_str + "|"
                if self.en_re_im_f:
                    label_re = "$X_r$" + ejO_str
                    label_im = "$X_i$" + ejO_str
                    h_i.append(self.draw_data(
                        self.plt_freq_stim, self.ax_f2, F, X_i, label=label_im,
                        bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_stim,
                        mkr_fmt=fmt_mkr_stim))
                    l_i.append(label_im)
                elif self.en_mag_phi_f:
                    label_im = r"$\angle X$" + ejO_str
                    h_i.append(self.draw_data(
                        self.plt_freq_stim, self.ax_f2, F, X_i, label=label_im,
                        plt_fmt=self.fmt_plot_stim, mkr_fmt=fmt_mkr_stim))
                    l_i.append(label_im)

                h_r.append(
                    self.draw_data(self.plt_freq_stim, self.ax_f1, F, X_r, label=label_re,
                                   bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_stim,
                                   mkr_fmt=fmt_mkr_stim))
                if show_info:
                    l_r.extend([lbl_empty, label_re, "$P_X$ = {0:.3g} {1}"
                                .format(Px, unit_P)])
                    h_r.extend([patch_trans, patch_trans])
                else:
                    l_r.append(label_re)

            # -------------------- Plot X_q -----------------------------------
            if plt_stimulus_q:
                label_re = "$|X_Q$" + ejO_str + "|"
                if self.en_re_im_f:
                    label_re = "$X_{Q,r}$" + ejO_str
                    label_im = "$X_{Q,i}$" + ejO_str
                    h_i.append(self.draw_data(
                        self.plt_freq_stmq, self.ax_f2, F, X_q_i, label=label_im,
                        bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_stmq,
                        mkr_fmt=fmt_mkr_stmq))
                    l_i.append(label_im)
                elif self.en_mag_phi_f:
                    label_im = r"$\angle X_Q$" + ejO_str
                    h_i.append(self.draw_data(
                        self.plt_freq_stmq, self.ax_f2, F, X_q_i, label=label_im,
                        plt_fmt=self.fmt_plot_stmq, mkr_fmt=fmt_mkr_stmq))
                    l_i.append(label_im)

                h_r.append(self.draw_data(
                    self.plt_freq_stmq, self.ax_f1, F, X_q_r, label=label_re,
                    bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_stmq,
                    mkr_fmt=fmt_mkr_stmq))
                if show_info:
                    l_r.extend([lbl_empty, label_re, "$P_{{Q}}$ = {0:.3g} {1}"
                                .format(Pxq, unit_P)])
                    h_r.extend([patch_trans, patch_trans])
                else:
                    l_r.append(label_re)

            # -------------------- Plot Y -------------------------------------
            if plt_response:
                label_re = "$|Y$" + ejO_str + "|"
                if self.en_re_im_f:
                    label_re = "$Y_r$" + ejO_str
                    label_im = "$Y_i$" + ejO_str
                    h_i.append(self.draw_data(
                        self.plt_freq_resp, self.ax_f2, F, Y_i, label=label_im,
                        bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_resp,
                        mkr_fmt=fmt_mkr_resp))
                    l_i.append(label_im)
                elif self.en_mag_phi_f:
                    label_im = r"$\angle Y$" + ejO_str
                    h_i.append(self.draw_data(
                        self.plt_freq_resp, self.ax_f2, F, Y_i, label=label_im,
                        plt_fmt=self.fmt_plot_resp, mkr_fmt=fmt_mkr_resp))
                    l_i.append(label_im)

                h_r.append(self.draw_data(
                    self.plt_freq_resp, self.ax_f1, F, Y_r, label=label_re,
                    bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_resp,
                    mkr_fmt=fmt_mkr_resp))
                if show_info:
                    l_r.extend([lbl_empty, label_re, "$P_Y$ = {0:.3g} {1}"
                                .format(Py, unit_P)])
                    h_r.extend([patch_trans, patch_trans])
                else:
                    l_r.append(label_re)

            # --------------- LEGEND (real part) ----------------------------------
            # The legend will fill the first column, then the next from top to bottom etc.
            if self.plt_freq_enabled or self.ui.chk_Hf.isChecked():

                # labels = np.concatenate([labels, [r"$NENBW$:"], ["{0:.4g} {1}"\
                # .format(nenbw, unit_nenbw)], [r"$CGAIN$:", "{0:.4g} {1}".format(nenbw,
                #   unit_nenbw)]])
                # see https://stackoverflow.com/questions/25830780/
                #               tabular-legend-layout-for-matplotlib

                if show_info:
                    # Reorder columns / rows to f
                    def flip_rc(m, cols):
                        mf = []
                        rows = len(m)//cols
                        for j in range(cols):
                            for i in range(rows):
                                mf.append(m[cols*i+j])
                        return mf

                    self.ax_f1.legend(
                        flip_rc(h_r, 3), flip_rc(l_r, 3), loc='best', fontsize='small',
                        fancybox=True, framealpha=0.7, ncol=3, handletextpad=-2,
                        columnspacing=1, labelspacing=1, handleheight=2, handlelength=1.5)

                else:
                    self.ax_f1.legend(h_r, l_r, loc='best', fontsize='small',
                                      fancybox=True, framealpha=0.7)

            # --------------- LEGEND and YLABEL (2nd plot) -------------------
            if (self.en_re_im_f or self.en_mag_phi_f) and self.plt_freq_enabled:
                self.ax_f2.legend(h_i, l_i, loc='best', fontsize='small', fancybox=True,
                                  framealpha=0.7)
                self.ax_f2.set_ylabel(H_Fi_str)

            self.axes_f[-1].set_xlabel(fb.fil[0]['plt_fLabel'])
            self.ax_f1.set_ylabel(H_Fr_str)
            # self.ax_f1.set_xlim(fb.fil[0]['freqSpecsRange'])
            self.ax_f1.set_xlim(F_range)
            self.ax_f1.set_title("Spectrum of " + self.title_str)

            if self.ui.chk_log_freq.isChecked():
                # scale second axis for noise power
                corr = 10*np.log10(self.ui.N) - nenbw  # nenbw is in dB
                mn, mx = self.ax_f1.get_ylim()
                self.ax_f1_noise.set_ylim(mn+corr, mx+corr)
                self.ax_f1_noise.set_ylabel(r'$P_N$ in dBW')

        self.redraw()  # redraw currently active mplwidget

        self.needs_redraw[1] = False

    # -------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the currently visible canvas when e.g. the canvas size has changed
        """
        idx = self.tabWidget.currentIndex()
        self.tabWidget.currentWidget().redraw()
        # wdg = getattr(self, self.tab_mplwidgets[idx])
        logger.debug("Redrawing tab {0}".format(idx))
        # wdg_cur.redraw()
        self.needs_redraw[idx] = False
#        self.mplwidget_t.redraw()
#        self.mplwidget_f.redraw()


# ------------------------------------------------------------------------------
def main():
    import sys
    from pyfda.libs.compat import QApplication

    app = QApplication(sys.argv)
    mainw = Plot_Impz(None)
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
    # module test using python -m pyfda.plot_widgets.plot_impz
