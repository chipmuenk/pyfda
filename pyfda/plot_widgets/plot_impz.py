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
import logging
logger = logging.getLogger(__name__)

import time
from pyfda.libs.compat import QWidget, pyqtSignal, QTabWidget, QVBoxLayout

import numpy as np
from numpy import pi
import scipy.signal as sig
import matplotlib.patches as mpl_patches
from matplotlib.ticker import AutoMinorLocator

import pyfda.filterbroker as fb
import pyfda.libs.pyfda_fix_lib as fx
from pyfda.libs.pyfda_lib import (to_html, safe_eval, pprint_log, np_type, calc_ssb_spectrum,
        rect_bl, sawtooth_bl, triang_bl, comb_bl, calc_Hcomplex, safe_numexpr_eval)
from pyfda.libs.pyfda_qt_lib import (qget_cmb_box, qset_cmb_box, qstyle_widget,
                                     qadd_item_cmb_box, qdel_item_cmb_box)
from pyfda.pyfda_rc import params # FMT string for QLineEdit fields, e.g. '{:.3g}'
from pyfda.plot_widgets.mpl_widget import MplWidget, stems, no_plot

from pyfda.plot_widgets.plot_impz_ui import PlotImpz_UI

# TODO: "Home" calls redraw for botb mpl widgets
# TODO: changing the view on some widgets redraws h[n] unncessarily

classes = {'Plot_Impz':'y[n]'} #: Dict containing class name : display name

class Plot_Impz(QWidget):
    """
    Construct a widget for plotting impulse and general transient responses
    """
    # incoming
    sig_rx = pyqtSignal(object)
    # outgoing, e.g. when stimulus has been calculated
    sig_tx = pyqtSignal(object)


    def __init__(self, parent):
        super(Plot_Impz, self).__init__(parent)

        self.ACTIVE_3D = False
        self.ui = PlotImpz_UI(self) # create the UI part with buttons etc.

        # initial settings
        self.needs_calc = True   # flag whether plots need to be recalculated
        self.needs_redraw = [True] * 2 # flag which plot needs to be redrawn
        self.error = False
        # initial setting for fixpoint simulation:
        self.fx_sim = qget_cmb_box(self.ui.cmb_sim_select, data=False) == 'Fixpoint'
        self.fx_sim_old = self.fx_sim
        self.tool_tip = "Impulse and transient response"
        self.tab_label = "y[n]"
        self.active_tab = 0 # index for active tab

        self.fmt_plot_resp = {'color':'red', 'linewidth':2, 'alpha':0.5}
        self.fmt_mkr_resp = {'color':'red', 'alpha':0.5}
        self.fmt_plot_stim = {'color':'blue', 'linewidth':2, 'alpha':0.5}
        self.fmt_mkr_stim = {'color':'blue', 'alpha':0.5}
        self.fmt_plot_stmq = {'color':'darkgreen', 'linewidth':2, 'alpha':0.5}
        self.fmt_mkr_stmq = {'color':'darkgreen', 'alpha':0.5}

        self.fmt_stem_stim = params['mpl_stimuli']


        self._construct_UI()

        #--------------------------------------------
        # initialize routines and settings
        self.fx_select()    # initialize fixpoint or float simulation
        self.impz() # initial calculation of stimulus and response and drawing

    def _construct_UI(self):
        """
        Create the top level UI of the widget, consisting of matplotlib widget
        and control frame.
        """
        #----------------------------------------------------------------------
        # Define MplWidget for TIME domain plots
        #----------------------------------------------------------------------
        self.mplwidget_t = MplWidget(self)
        self.mplwidget_t.setObjectName("mplwidget_t1")
        self.mplwidget_t.layVMainMpl.addWidget(self.ui.wdg_ctrl_time)
        self.mplwidget_t.layVMainMpl.setContentsMargins(*params['wdg_margins'])
        self.mplwidget_t.mplToolbar.a_he.setEnabled(True)
        self.mplwidget_t.mplToolbar.a_he.info = "manual/plot_impz.html"

        #----------------------------------------------------------------------
        # Define MplWidget for FREQUENCY domain plots
        #----------------------------------------------------------------------
        self.mplwidget_f = MplWidget(self)
        self.mplwidget_f.setObjectName("mplwidget_f1")
        self.mplwidget_f.layVMainMpl.addWidget(self.ui.wdg_ctrl_freq)
        self.mplwidget_f.layVMainMpl.setContentsMargins(*params['wdg_margins'])
        self.mplwidget_f.mplToolbar.a_he.setEnabled(True)
        self.mplwidget_f.mplToolbar.a_he.info = "manual/plot_impz.html"

        #----------------------------------------------------------------------
        # Tabbed layout with vertical tabs
        #----------------------------------------------------------------------
        self.tabWidget = QTabWidget(self)
        self.tabWidget.addTab(self.mplwidget_t, "Time")
        self.tabWidget.setTabToolTip(0,"Impulse and transient response of filter")
        self.tabWidget.addTab(self.mplwidget_f, "Frequency")
        self.tabWidget.setTabToolTip(1,"Spectral representation of impulse or transient response")
        # list with tabWidgets
        self.tab_mplwidgets = ["mplwidget_t", "mplwidget_f"]
        self.tabWidget.setTabPosition(QTabWidget.West)

        layVMain = QVBoxLayout()
        layVMain.addWidget(self.tabWidget)
        layVMain.addWidget(self.ui.wdg_ctrl_stim)
        layVMain.addWidget(self.ui.wdg_ctrl_run)
        layVMain.setContentsMargins(*params['wdg_margins'])#(left, top, right, bottom)

        self.setLayout(layVMain)
        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        # --- run control ---
        self.ui.cmb_sim_select.currentIndexChanged.connect(self.impz)
        self.ui.chk_scale_impz_f.clicked.connect(self.draw)
        self.ui.but_run.clicked.connect(self.impz)
        self.ui.chk_auto_run.clicked.connect(self.calc_auto)
        self.ui.chk_fx_scale.clicked.connect(self.draw)
        self.ui.but_fft_win.clicked.connect(self.ui.show_fft_win)

        # --- time domain plotting ---
        self.ui.cmb_plt_time_resp.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_time_stim.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_time_stmq.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_time_spgr.currentIndexChanged.connect(self._spgr_cmb)
        self.ui.chk_log_time.clicked.connect(self.draw)
        self.ui.led_log_bottom_time.editingFinished.connect(self._log_bottom)
        self.ui.chk_log_spgr_time.clicked.connect(self.draw)
        self.ui.led_nfft_spgr_time.editingFinished.connect(self._spgr_params)
        self.ui.led_ovlp_spgr_time.editingFinished.connect(self._spgr_params)
        self.ui.cmb_mode_spgr_time.currentIndexChanged.connect(self.draw)
        self.ui.chk_byfs_spgr_time.clicked.connect(self.draw)
        self.ui.chk_fx_limits.clicked.connect(self.draw)
        self.ui.chk_win_time.clicked.connect(self.draw)
        # --- frequency domain plotting ---
        self.ui.cmb_plt_freq_resp.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_freq_stim.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_freq_stmq.currentIndexChanged.connect(self.draw)
        self.ui.chk_Hf.clicked.connect(self.draw)
        self.ui.chk_re_im_freq.clicked.connect(self.draw)
        self.ui.chk_log_freq.clicked.connect(self._log_mode_freq)
        self.ui.led_log_bottom_freq.editingFinished.connect(self._log_mode_freq)
        self.ui.chk_show_info_freq.clicked.connect(self.draw)
        #self.ui.chk_win_freq.clicked.connect(self.draw)

        self.mplwidget_t.mplToolbar.sig_tx.connect(self.process_sig_rx) # connect to toolbar
        self.mplwidget_f.mplToolbar.sig_tx.connect(self.process_sig_rx) # connect to toolbar

        # When user has selected a different tab, trigger a recalculation of current tab
        self.tabWidget.currentChanged.connect(self.draw) # passes number of active tab

        self.sig_rx.connect(self.process_sig_rx)
        # connect UI to widgets and signals upstream:
        self.ui.sig_tx.connect(self.process_sig_rx)

#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from
        - the navigation toolbars (time and freq.)
        - local widgets (impz_ui) and
        - plot_tab_widgets() (global signals)
        """

        logger.debug("PROCESS_SIG_RX - needs_calc: {0} | vis: {1}\n{2}"\
                     .format(self.needs_calc, self.isVisible(), pprint_log(dict_sig)))

        if dict_sig['sender'] == __name__:
            logger.debug("Stopped infinite loop:\n{0}".format(pprint_log(dict_sig)))
            return

        self.error = False

        if 'closeEvent' in dict_sig:
            self.close_FFT_win()
            return # probably not needed
        # --- signals for fixpoint simulation ---------------------------------
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

                - Calculate stimuli, quantize and pass to dict_sig with `'fx_sim':'send_stimulus'`
                  and `'fx_stimulus':<quantized stimulus array>`. Stimuli are scaled with the input
                  fractional word length, i.e. with 2**WF (input) to obtain integer values
                  """
                self.needs_calc = True # always require recalculation when triggered externally
                self.needs_redraw = [True] * 2
                self.error = False
                qstyle_widget(self.ui.but_run, "changed")
                self.fx_select("Fixpoint")
                if self.isVisible():
                    self.calc_stimulus()

            elif dict_sig['fx_sim'] == 'set_results':
                """
                - Convert simulation results to integer and transfer them to the plotting
                  routine
                """
                logger.debug("Received fixpoint results.")
                self.draw_response_fx(dict_sig=dict_sig)

            elif dict_sig['fx_sim'] == 'error':
                self.needs_calc = True
                self.error = True
                qstyle_widget(self.ui.but_run, "error")
                return

            elif not dict_sig['fx_sim']:
                logger.error('Missing value for key "fx_sim".')

            else:
                logger.error('Unknown value "{0}" for "fx_sim" key\n'\
                             '\treceived from "{1}"'.format(dict_sig['fx_sim'],
                                               dict_sig['sender']))

        # --- widget is visible, handle all signals except 'fx_sim' -----------
        elif self.isVisible(): # all signals except 'fx_sim'
            if 'data_changed' in dict_sig or 'specs_changed' in dict_sig or self.needs_calc:
                # update number of data points in impz_ui and FFT window
                # needed when e.g. FIR filter order has changed. Don't emit a signal.
                self.ui.update_N(emit=False)
                self.needs_calc = True
                qstyle_widget(self.ui.but_run, "changed")
                self.impz()

            elif 'view_changed' in dict_sig:
                self.draw()

            elif 'ui_changed' in dict_sig:
                # exclude those ui elements  / events that don't require a recalculation
                if dict_sig['ui_changed'] in {'win'}:
                    self.draw()
                elif dict_sig['ui_changed'] in {'resized','tab'}:
                    pass

                else: # all the other ui elements are treated here
                    self.needs_calc = True
                    qstyle_widget(self.ui.but_run, "changed")
                    self.impz()

            elif 'home' in dict_sig:
                self.redraw()
                # self.tabWidget.currentWidget().redraw()
                # redraw method of current mplwidget, always redraws tab 0
                self.needs_redraw[self.tabWidget.currentIndex()] = False

        else: # invisible
            if 'data_changed' in dict_sig or 'specs_changed' in dict_sig:
                self.needs_calc = True

#            elif 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'get_stimulus':
#                    self.needs_calc = True # always require recalculation when triggered externally
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
        self.ui.chk_scale_impz_f.setEnabled((self.ui.noi == 0 or self.ui.cmbNoise.currentText() == 'None')\
                                            and self.ui.DC == 0)

        self.fx_select() # check for fixpoint setting and update if needed
        if type(arg) == bool: # but_run has been pressed
            self.needs_calc = True # force recalculation when but_run is pressed
        elif not self.ui.chk_auto_run.isChecked():
            return

        if self.needs_calc:
            logger.debug("Calc impz started!")
            if self.fx_sim: # start a fixpoint simulation
                self.sig_tx.emit({'sender':__name__, 'fx_sim':'init'})
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

        if fx in {0, 1}: # connected to index change of combo box
            pass
        elif fx in {"Float", "Fixpoint"}: # direct function call
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
        self.ui.chk_fx_scale.setVisible(self.fx_sim)
        self.ui.chk_fx_limits.setVisible(self.fx_sim)
        
        if self.fx_sim:
            qadd_item_cmb_box(self.ui.cmb_plt_time_spgr, "x_q[n]")
        else:
            qdel_item_cmb_box(self.ui.cmb_plt_time_spgr, "x_q[n]")

        if self.fx_sim != self.fx_sim_old:
            qstyle_widget(self.ui.but_run, "changed")
            # even if nothing else has changed, stimulus and response must be recalculated
            self.needs_calc = True

        self.fx_sim_old = self.fx_sim

#------------------------------------------------------------------------------
    def calc_stimulus(self):
        """
        (Re-)calculate stimulus `self.x`
        """
        self.n = np.arange(self.ui.N_end)
        phi1 = self.ui.phi1 / 180 * pi
        phi2 = self.ui.phi2 / 180 * pi

        # calculate stimuli x[n] ==============================================
        self.H_str = ''
        self.title_str = ""

        if self.ui.stim == "Impulse":
            if np_type(self.ui.A1) == complex:
                A_type = complex
            else:
                A_type = float

            self.x = np.zeros(self.ui.N_end, dtype=A_type)
            self.x[0] = self.ui.A1 # create dirac impulse as input signal
            self.title_str = r'Impulse Response'
            self.H_str = r'$h[n]$' # default

        elif self.ui.stim == "None":
            self.x = np.zeros(self.ui.N_end)
            self.title_str = r'Zero Input System Response'
            self.H_str = r'$h_0[n]$' # default

        elif self.ui.stim == "Step":
            self.x = self.ui.A1 * np.ones(self.ui.N_end) # create step function
            self.title_str = r'Step Response'
            self.H_str = r'$h_{\epsilon}[n]$'

        elif self.ui.stim == "StepErr":
            self.x = self.ui.A1 * np.ones(self.ui.N_end) # create step function
            self.title_str = r'Settling Error'
            self.H_str = r'$h_{\epsilon, \infty} - h_{\epsilon}[n]$'

        elif self.ui.stim == "Cos":
            self.x = self.ui.A1 * np.cos(2*pi * self.n * self.ui.f1 + phi1) +\
                self.ui.A2 * np.cos(2*pi * self.n * self.ui.f2 + phi2)
            self.title_str += r'Cosine Signal'

        elif self.ui.stim == "Sine":
            self.x = self.ui.A1 * np.sin(2*pi * self.n * self.ui.f1 + phi1) +\
                self.ui.A2 * np.sin(2*pi * self.n * self.ui.f2 + phi2)
            self.title_str += r'Sinusoidal Signal '

        elif self.ui.stim == "Chirp":
            self.x = self.ui.A1 * sig.chirp(self.n, self.ui.f1, self.ui.N_end, self.ui.f2,
                                            method=self.ui.chirp_method.lower(), phi=phi1)
            self.title_str += self.ui.chirp_method + ' Chirp Signal'

        elif self.ui.stim == "Triang":
            if self.ui.chk_stim_bl.isChecked():
                self.x = self.ui.A1 * triang_bl(2*pi * self.n * self.ui.f1 + phi1)
                self.title_str += r'Bandlim. Triangular Signal'
            else:
                self.x = self.ui.A1 * sig.sawtooth(2*pi * self.n * self.ui.f1 + phi1, width=0.5)
                self.title_str += r'Triangular Signal'

        elif self.ui.stim == "Saw":
            if self.ui.chk_stim_bl.isChecked():
                self.x = self.ui.A1 * sawtooth_bl(2*pi * self.n * self.ui.f1 + phi1)
                self.title_str += r'Bandlim. Sawtooth Signal'
            else:
                self.x = self.ui.A1 * sig.sawtooth(2*pi * self.n * self.ui.f1 + phi1)
                self.title_str += r'Sawtooth Signal'

        elif self.ui.stim == "Rect":
            if self.ui.chk_stim_bl.isChecked():
                self.x = self.ui.A1 * rect_bl(2*pi * self.n * self.ui.f1 + phi1, duty=0.5)
                self.title_str += r'Bandlimited Rect. Signal'
            else:
                self.x = self.ui.A1 * sig.square(2*pi * self.n * self.ui.f1 + phi1, duty=0.5)
                self.title_str += r'Rect. Signal'

        elif self.ui.stim == "Comb":
            self.x = self.ui.A1 * comb_bl(2*pi * self.n * self.ui.f1 + phi1)
            self.title_str += r'Bandlim. Comb Signal'

        elif self.ui.stim == "AM":
            self.x = self.ui.A1 * np.sin(2*pi * self.n * self.ui.f1 + phi1)\
                * self.ui.A2 * np.sin(2*pi * self.n * self.ui.f2 + phi2)
            self.title_str += r'AM Signal $A_1 \sin(2 \pi n f_1 + \varphi_1) \cdot A_2 \sin(2 \pi n f_2 + \varphi_2)$'
        elif self.ui.stim == "PM / FM":
            self.x = self.ui.A1 * np.sin(2*pi * self.n * self.ui.f1 + phi1 +\
                self.ui.A2 * np.sin(2*pi * self.n * self.ui.f2 + phi2))
            self.title_str += r'PM / FM Signal $A_1 \sin(2 \pi n f_1 + \varphi_1 + A_2 \sin(2 \pi n f_2 + \varphi_2))$'
        elif self.ui.stim == "Formula":
            param_dict = {"A1":self.ui.A1, "A2":self.ui.A2,
                          "f1":self.ui.f1, "f2":self.ui.f2,
                          "phi1":self.ui.phi1, "phi2":self.ui.phi2,
                          "f_S":fb.fil[0]['f_S'], "n":self.n}

            self.x = safe_numexpr_eval(self.ui.stim_formula, (self.ui.N_end,), param_dict)
            self.title_str += r'Formula Defined Signal'
        else:
            logger.error('Unknown stimulus format "{0}"'.format(self.ui.stim))
            return

        # Add noise to stimulus
        noi = 0
        if self.ui.noise == "gauss":
            noi = self.ui.noi * np.random.randn(len(self.x))
            self.title_str += r' + Gaussian Noise'
        elif self.ui.noise == "uniform":
            noi = self.ui.noi * (np.random.rand(len(self.x))-0.5)
            self.title_str += r' + Uniform Noise'
        elif self.ui.noise == "prbs":
            noi = self.ui.noi * 2 * (np.random.randint(0, 2, len(self.x))-0.5)
            self.title_str += r' + PRBS Noise'
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
            self.q_i = fx.Fixed(fb.fil[0]['fxqc']['QI']) # setup quantizer for input quantization
            self.q_i.setQobj({'frmt':'dec'})    # always use integer decimal format
            if np.any(np.iscomplex(self.x)):
                logger.warning("Complex stimulus: Only its real part will be processed by the fixpoint filter!")
            
            self.x_q = self.q_i.fixp(self.x.real)

            self.sig_tx.emit({'sender':__name__, 'fx_sim':'send_stimulus',
                    'fx_stimulus':np.round(self.x_q * (1 << self.q_i.WF)).astype(int)})
            logger.debug("fx stimulus sent")

        self.needs_redraw[:] = [True] * 2

#------------------------------------------------------------------------------
    def calc_response(self):
        """
        (Re-)calculate ideal filter response `self.y` from stimulus `self.x` and 
        the filter coefficients using `lfilter()`, `sosfilt()` or `filtfilt()`.

        Set the flag `self.cmplx` when response `self.y` or stimulus `self.x` are complex.
        """

        self.bb = np.asarray(fb.fil[0]['ba'][0])
        self.aa = np.asarray(fb.fil[0]['ba'][1])
        if min(len(self.aa), len(self.bb)) < 2:
            logger.error('No proper filter coefficients: len(a), len(b) < 2 !')
            return

        logger.debug("Coefficient area = {0}".format(np.sum(np.abs(self.bb))))

        sos = np.asarray(fb.fil[0]['sos'])
        antiCausal = 'zpkA' in fb.fil[0]
        causal     = not antiCausal

        if len(sos) > 0 and causal: # has second order sections and is causal
            y = sig.sosfilt(sos, self.x)
        elif antiCausal:
            y = sig.filtfilt(self.bb, self.aa, self.x, -1, None)
        else: # no second order sections or antiCausals for current filter
            y = sig.lfilter(self.bb, self.aa, self.x)

        if self.ui.stim == "StepErr":
            dc = sig.freqz(self.bb, self.aa, [0]) # DC response of the system
            y = y - abs(dc[1]) # subtract DC (final) value from response

        self.y = np.real_if_close(y, tol=1e3)  # tol specified in multiples of machine eps

        self.needs_redraw[:] = [True] * 2

        # Calculate imag. and real components from response
        self.cmplx = np.any(np.iscomplex(self.y)) or np.any(np.iscomplex(self.x))
#------------------------------------------------------------------------------
    def draw_response_fx(self, dict_sig=None):
        """
        Get Fixpoint results and plot them
        """
        if self.needs_calc:
            self.needs_redraw = [True] * 2
            #t_draw_start = time.process_time()
            self.y = np.asarray(dict_sig['fx_results'])
            if self.y is None:
                qstyle_widget(self.ui.but_run, "error")
                self.needs_calc = True
            else:
                self.needs_calc = False

                self.draw()
                qstyle_widget(self.ui.but_run, "normal")

                self.sig_tx.emit({'sender':__name__, 'fx_sim':'finish'})

#------------------------------------------------------------------------------
    def calc_fft(self):
        """
        (Re-)calculate FFTs of stimulus `self.X`, quantized stimulus `self.X_q`
        and response `self.Y` using the window function `self.ui.win`.
        """
        # calculate FFT of stimulus / response
        if self.x is None or len(self.x) < self.ui.N_end:
            self.X = np.zeros(self.ui.N_end-self.ui.N_start) # dummy result
            if self.x is None:
                logger.warning("Stimulus is 'None', FFT cannot be calculated.")
            else:
                logger.warning("Length of stimulus is {0} < N = {1}, FFT cannot be calculated."
                               .format(len(self.x), self.ui.N_end))
        else:
            # multiply the  time signal with window function
            x_win = self.x[self.ui.N_start:self.ui.N_end] * self.ui.win
            # calculate absolute value and scale by N_FFT
            self.X = np.fft.fft(x_win) / self.ui.N
            #self.X[0] = self.X[0] * np.sqrt(2) # correct value at DC

            if self.fx_sim:
                # same for fixpoint simulation
                x_q_win = self.q_i.fixp(self.x[self.ui.N_start:self.ui.N_end]) * self.ui.win
                self.X_q = np.fft.fft(x_q_win) / self.ui.N
                #self.X_q[0] = self.X_q[0] * np.sqrt(2) # correct value at DC

        if self.y is None or len(self.y) < self.ui.N_end:
            self.Y = np.zeros(self.ui.N_end-self.ui.N_start) # dummy result
            if self.y is None:
                logger.warning("Transient response is 'None', FFT cannot be calculated.")
            else:
                logger.warning("Length of transient response is {0} < N = {1}, FFT cannot be calculated."
                               .format(len(self.y), self.ui.N_end))
        else:
            y_win = self.y[self.ui.N_start:self.ui.N_end] * self.ui.win
            self.Y = np.fft.fft(y_win) / self.ui.N
            #self.Y[0] = self.Y[0] * np.sqrt(2) # correct value at DC

#        if self.ui.chk_win_freq.isChecked():
#            self.Win = np.abs(np.fft.fft(self.ui.win)) / self.ui.N

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

        if not hasattr(self, 'cmplx'): # has response been calculated yet?
            logger.error("Response should have been calculated by now!")
            return

        f_unit = fb.fil[0]['plt_fUnit']
        if f_unit in {"f_S", "f_Ny"}:
            unit_frmt = "i" # italic
        else:
            unit_frmt = None
        self.ui.lblFreqUnit1.setText(to_html(f_unit, frmt=unit_frmt))
        self.ui.lblFreqUnit2.setText(to_html(f_unit, frmt=unit_frmt))
        self.t = self.n / fb.fil[0]['f_S']
        self.ui.load_fs()

        self.scale_i = self.scale_o = 1
        self.fx_min = -1.
        self.fx_max = 1.
        if self.fx_sim: # fixpoint simulation enabled -> scale stimulus and response
            try:
                if self.ui.chk_fx_scale.isChecked():
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
                logger.error("Type error: 'fxqc_dict'={0},\n{1}".format(fb.fil[0]['fxqc'], e))
            except ValueError as e:
                logger.error("Value error: {0}".format(e))

        idx = self.tabWidget.currentIndex()

        if idx == 0 and self.needs_redraw[0]:
            self.draw_time()
        elif idx == 1 and self.needs_redraw[1]:
            self.draw_freq()

        self.ui.show_fft_win()

#------------------------------------------------------------------------------
    def _spgr_params(self):
        """
        Update parameters for spectrogram
        """
        self.ui.nfft_spgr_time = safe_eval(self.ui.led_nfft_spgr_time.text(),
                                         self.ui.nfft_spgr_time, return_type='int', sign='pos')
        self.ui.led_nfft_spgr_time.setText(str(self.ui.nfft_spgr_time))

        self.ui.ovlp_spgr_time = safe_eval(self.ui.led_ovlp_spgr_time.text(),
                                         self.ui.ovlp_spgr_time, return_type='int', sign='poszero')
        self.ui.led_ovlp_spgr_time.setText(str(self.ui.ovlp_spgr_time))
        
        if self.ui.nfft_spgr_time <= self.ui.ovlp_spgr_time:
            logger.warning("N_OVLP must be less than N_FFT!")

        self.draw()
        
#------------------------------------------------------------------------------
    def _spgr_cmb(self):
        """
        Update spectrogram ui
        """
        spgr_en = self.ui.cmb_plt_time_spgr.currentText() != "None"

        self.ui.lbl_log_spgr_time.setVisible(spgr_en)
        self.ui.chk_log_spgr_time.setVisible(spgr_en)   
        self.ui.lbl_nfft_spgr_time.setVisible(spgr_en)
        self.ui.led_nfft_spgr_time.setVisible(spgr_en)
        self.ui.lbl_ovlp_spgr_time.setVisible(spgr_en)
        self.ui.led_ovlp_spgr_time.setVisible(spgr_en)
        self.ui.lbl_mode_spgr_time.setVisible(spgr_en)
        self.ui.cmb_mode_spgr_time.setVisible(spgr_en)
        self.ui.lbl_byfs_spgr_time.setVisible(spgr_en)
        self.ui.chk_byfs_spgr_time.setVisible(spgr_en)

        self.draw()


#------------------------------------------------------------------------------
    def _log_bottom(self):
        """
        Select / deselect log. mode for time domain and update self.ui.bottom_t
        """
        log = self.ui.chk_log_time.isChecked()
        #self.ui.lbl_log_bottom_time.setVisible(log)
        #self.ui.led_log_bottom_time.setVisible(log)

        self.ui.bottom_t = safe_eval(self.ui.led_log_bottom_time.text(),
                                         self.ui.bottom_t, return_type='float', sign='neg')
        self.ui.led_log_bottom_time.setText(str(self.ui.bottom_t))

        self.draw()

#------------------------------------------------------------------------------
    def _log_mode_freq(self):
        """
        Select / deselect log. mode for frequency domain and update self.ui.bottom_f
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

        self.draw()

#------------------------------------------------------------------------------
    def draw_data(self, plt_style, ax, x, y, bottom=0, label='',
                  plt_fmt=None, mkr=False, mkr_fmt=None, **args):
        """
        Plot x, y data (numpy arrays with equal length) in a plot style defined
        by `plt_style`.

        Parameters
        ----------
        plt_style : str
            one of "line", "stem", "step", "dots"
        ax : matplotlib axis
            Handle to the axis where signal is
        x : array-like
            x-axis: time or frequency data
        y : array-like
            y-data
        bottom : float
            Bottom line for stem plot. The default is 0.
        label : str
            Plot label
        plt_fmt : dict
            General styles (color, linewidth etc.) for plotting. The default is None.
        mkr : bool
            Plot a marker for every data point if enabled
        mkr_fmt : dict
            Marker styles
        args : dictionary with additional keys and values. As they might not be
            compatible with every plot style, they have to be added individually

        Returns
        -------
        None

        """

        if plt_fmt is None:
            plt_fmt = {}
        if plt_style == "line":
            ax.plot(x,y, label=label, **plt_fmt)
        elif plt_style == "stem":
            stems(x,y, ax=ax, bottom=bottom, label=label, **plt_fmt)
        elif plt_style == "step":
            ax.plot(x,y, drawstyle='steps-mid', label=label, **plt_fmt)
        elif plt_style == "dots":
            ax.scatter(x,y, label=label, **plt_fmt)
        else:
            pass

        if mkr:
            if 'marker' in args:
                ax.scatter(x,y, **mkr_fmt, marker=args['marker'])
            else:
                ax.scatter(x, y, **mkr_fmt)

    #================ Plotting routine time domain =========================
    def _init_axes_time(self):
        """
        Clear the axes of the time domain matplotlib widgets and (re)draw the plots.
        """
        self.plt_time_resp = qget_cmb_box(self.ui.cmb_plt_time_resp, data=False).lower().replace("*", "")
        self.plt_time_resp_mkr = "*" in qget_cmb_box(self.ui.cmb_plt_time_resp, data=False)

        self.plt_time_stim = qget_cmb_box(self.ui.cmb_plt_time_stim, data=False).lower().replace("*", "")
        self.plt_time_stim_mkr = "*" in qget_cmb_box(self.ui.cmb_plt_time_stim, data=False)

        self.plt_time_stmq = qget_cmb_box(self.ui.cmb_plt_time_stmq, data=False).lower().replace("*", "")
        self.plt_time_stmq_mkr = "*" in qget_cmb_box(self.ui.cmb_plt_time_stmq, data=False)
    
        self.plt_time_spgr = qget_cmb_box(self.ui.cmb_plt_time_spgr, data=False).lower()
        self.spgr = self.plt_time_spgr != "none"

        self.plt_time = self.plt_time_resp != "none" or self.plt_time_stim != "none"\
            or (self.plt_time_stmq != "none" and self.fx_sim)\
            or self.spgr or self.ui.chk_win_time.isChecked()

        self.mplwidget_t.fig.clf() # clear figure with axes

        if self.plt_time:
            num_subplots = 1 + self.cmplx + self.spgr
            
            # return a one-dimensional list with num_subplots axes
            self.axes_time = self.mplwidget_t.fig.subplots(nrows=num_subplots, ncols=1,
                                               sharex=True, squeeze = False)[:,0]
            
            self.ax_r = self.axes_time[0]
            self.ax_r.cla()

            if self.cmplx:
                self.ax_i = self.axes_time[1]
                self.ax_i.cla()
                self.mplwidget_t.fig.align_ylabels()
            
            if self.spgr:
                self.ax_s = self.axes_time[-1] # assign last axis

            if self.ACTIVE_3D: # not implemented / tested yet
                self.ax3d = self.mplwidget_t.fig.add_subplot(111, projection='3d')
                
            for ax in self.axes_time:
                ax.xaxis.tick_bottom() # remove axis ticks on top
                ax.yaxis.tick_left() # remove axis ticks right
                ax.xaxis.set_minor_locator(AutoMinorLocator()) # enable minor ticks
                ax.yaxis.set_minor_locator(AutoMinorLocator())               

#------------------------------------------------------------------------------
    def draw_time(self):
        """
        (Re-)draw the time domain mplwidget
        """
        if self.y is None: # safety net for empty responses
            for ax in self.mplwidget_t.fig.get_axes(): # remove all axes
                self.mplwidget_t.fig.delaxes(ax)
            return

        if not self.H_str or self.H_str[1] != 'h': # '$h... = some impulse response, don't change
            self.H_str = ''
            if qget_cmb_box(self.ui.cmb_plt_time_stim, data=False).lower() != "none":
                self.H_str += r'$x$, '
            if qget_cmb_box(self.ui.cmb_plt_time_stmq, data=False).lower() != "none" and self.fx_sim:
                self.H_str += r'$x_Q$, '
            if qget_cmb_box(self.ui.cmb_plt_time_resp, data=False).lower() != "none":
                self.H_str += r'$y$'
            self.H_str = self.H_str.rstrip(', ')

        mkfmt_i = 'd'

        self._init_axes_time()

        if self.fx_sim: # fixpoint simulation enabled -> scale stimulus and response
            x_q = self.x_q * self.scale_i
            if self.ui.chk_log_time.isChecked():
                x_q = np.maximum(20 * np.log10(abs(x_q)), self.ui.bottom_t)

            logger.debug("self.scale I:{0} O:{1}".format(self.scale_i, self.scale_o))
        else:
            x_q = None
            
        x = self.x * self.scale_i
        y = self.y * self.scale_o
        
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

        if self.ui.chk_log_time.isChecked(): # log. scale for stimulus / response time domain
            bottom_t = self.ui.bottom_t
            win = np.maximum(20 * np.log10(abs(self.ui.win)), self.ui.bottom_t)
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
            win = self.ui.win
            if self.cmplx:
                H_i_str = r'$\Im\{$' + self.H_str + r'$\}$ in V'
                H_str = r'$\Re\{$' + self.H_str + r'$\}$ in V'
            else:
                H_str = self.H_str + ' in V'

        if self.ui.chk_fx_limits.isChecked() and self.fx_sim:
            self.ax_r.axhline(fx_max, 0, 1, color='k', linestyle='--')
            self.ax_r.axhline(fx_min, 0, 1, color='k', linestyle='--')

        # --------------- Stimulus plot ----------------------------------
        self.draw_data(self.plt_time_stim, self.ax_r, self.t[self.ui.N_start:],
              x_r[self.ui.N_start:], label=lbl_x_r, bottom=bottom_t,
              plt_fmt=self.fmt_plot_stim, mkr=self.plt_time_stim_mkr, mkr_fmt=self.fmt_mkr_stim)

        #-------------- Stimulus <q> plot --------------------------------
        if x_q is not None and self.plt_time_stmq != "none":
            self.draw_data(self.plt_time_stmq, self.ax_r, self.t[self.ui.N_start:],
                  x_q[self.ui.N_start:], label='$x_q[n]$', bottom=bottom_t,
                  plt_fmt=self.fmt_plot_stmq, mkr=self.plt_time_stmq_mkr, mkr_fmt=self.fmt_mkr_stmq)

        # --------------- Response plot ----------------------------------
        self.draw_data(self.plt_time_resp, self.ax_r, self.t[self.ui.N_start:],
              y_r[self.ui.N_start:], label=lbl_y_r, bottom=bottom_t,
              plt_fmt=self.fmt_plot_resp, mkr=self.plt_time_resp_mkr, mkr_fmt=self.fmt_mkr_resp)

        # --------------- Window plot ----------------------------------
        if self.ui.chk_win_time.isChecked():
            self.ax_r.plot(self.t[self.ui.N_start:], win, c="gray", label=self.ui.window_name)

        # --------------- LEGEND (real part) ----------------------------------
        if self.plt_time:
            self.ax_r.legend(loc='best', fontsize='small', fancybox=True, framealpha=0.7)

        # --------------- Complex response ----------------------------------
        if self.cmplx and (self.plt_time_resp != "none" or self.plt_time_stim != "none"):

            # --- imag. part of response -----
            self.draw_data(self.plt_time_resp, self.ax_i, self.t[self.ui.N_start:],
                  y_i[self.ui.N_start:], label=lbl_y_i, bottom=bottom_t,
                  plt_fmt=self.fmt_plot_resp, mkr=self.plt_time_resp_mkr, mkr_fmt=self.fmt_mkr_resp,
                  marker=mkfmt_i)

            # --- imag. part of stimulus -----
            self.draw_data(self.plt_time_stim, self.ax_i, self.t[self.ui.N_start:],
                  x_i[self.ui.N_start:], label=lbl_x_i, bottom=bottom_t,
                  plt_fmt=self.fmt_plot_stim, mkr=self.plt_time_stim_mkr, mkr_fmt=self.fmt_mkr_stim,
                  marker=mkfmt_i)

            # --- labels and markers -----
            # plt.setp(ax_r.get_xticklabels(), visible=False)
            # is shorter but imports matplotlib, set property directly instead:
            [label.set_visible(False) for label in self.ax_r.get_xticklabels()]
            #self.ax_r.set_ylabel(H_str + r'$\rightarrow $') # common x-axis

            self.ax_i.set_ylabel(H_i_str + r'$\rightarrow $')
            self.ax_i.legend(loc='best', fontsize='small', fancybox=True, framealpha=0.7)
        #else:
#            self.ax_r.set_xlabel(fb.fil[0]['plt_tLabel'])
        self.ax_r.set_ylabel(H_str + r'$\rightarrow $')

        # --------------- Spectrogram -----------------------------------------
        if self.spgr:
            if self.plt_time_spgr == "x[n]":
                s = x[self.ui.N_start:]
                sig_lbl = 'X'
            elif self.plt_time_spgr == "x_q[n]":
                s = self.x_q[self.ui.N_start:]
                sig_lbl = 'X_Q'
            elif self.plt_time_spgr == "y[n]":
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
            self.ui.lbl_byfs_spgr_time.setVisible(mode=='psd')
            self.ui.chk_byfs_spgr_time.setVisible(mode=='psd')
            spgr_pre =  ""
            if self.ui.chk_log_spgr_time.isChecked():
                dB_unit = "dB"
            else:
                dB_unit = ""
            if mode == "psd":
                spgr_symb = r"$S_{{{0}}}$".format(sig_lbl.lower()+sig_lbl.lower())
                # Power Spectral Density
                if self.ui.chk_byfs_spgr_time.isChecked():
                    # scale result by f_S
                    spgr_unit = r" in {0}W / Hz".format(dB_unit)
                else:
                    spgr_unit = r" in {0}W".format(dB_unit)
                
            elif mode in {"magnitude", "complex"}:
                # "complex" cannot be plotted directly
                spgr_pre = r"|"
                spgr_symb = "${0}$".format(sig_lbl)
                spgr_unit = r"| in {0}V".format(dB_unit)
                
            elif mode in {"angle", "phase"}:
                spgr_unit = r" in rad"
                spgr_symb = "${0}$".format(sig_lbl)
                spgr_pre = r"$\angle$"
                # must be linear if mode is 'angle' or 'phase':
                self.ui.chk_log_spgr_time.blockSignals(True)
                self.ui.chk_log_spgr_time.setChecked(False)
                self.ui.chk_log_spgr_time.blockSignals(False)
            else:
                logger.warning("Unknown spectrogram mode {0}".format(mode))
                mode = None

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
#             f, t, Sxx = sig.spectrogram(s, fb.fil[0]['f_S'], 
#                                         nperseg=None, noverlap=None, nfft=None,
#                                         return_onesided = fb.fil[0]['freqSpecsRangeType'] == 'half',
#                                         scaling='density',mode='psd')
#             # mode: 'psd', 'complex','magnitude','angle', 'phase'
# =============================================================================
            Sxx,f,t,im = self.ax_s.specgram(s, Fs=fb.fil[0]['f_S'], NFFT=self.ui.nfft_spgr_time,
                                        noverlap=self.ui.ovlp_spgr_time, pad_to=None, xextent=t_range,
                                        sides=sides, scale_by_freq=self.ui.chk_byfs_spgr_time.isChecked(),
                                        mode=mode, scale=scale, vmin=bottom_spgr, cmap=None)
            # Fs : sampling frequency for scaling
            # window: callable or ndarray, default window_hanning
            # NFFT : data points for each block
            # pad_to: create zero-padding
            # xextent: image extent along x-axis; None or (xmin, xmax)
            # scale_by_freq: True scales power spectral density by f_S

#            col_mesh = self.ax_s.pcolormesh(t, np.fft.fftshift(f), 
#                                 np.fft.fftshift(Sxx, axes=0), shading='gouraud') # *fb.fil[0]['f_S']
            #self.ax_s.colorbar(col_mesh)

            cbar = self.mplwidget_t.fig.colorbar(im, ax=self.ax_s, aspect=30, pad=0.005)
            cbar.ax.set_ylabel(spgr_pre + spgr_symb + spgr_args + spgr_unit)

            self.ax_s.set_ylabel(fb.fil[0]['plt_fLabel'])        

        # --------------- 3D Complex  -----------------------------------------
        if self.ACTIVE_3D: # not implemented / tested yet
            # plotting the stems
            for i in range(self.ui.N_start, self.ui.N_end):
                self.ax3d.plot([self.t[i], self.t[i]], [y_r[i], y_r[i]], [0, y_i[i]],
                               '-', linewidth=2, alpha=.5)

            # plotting a circle on the top of each stem
            self.ax3d.plot(self.t[self.ui.N_start:], y_r[self.ui.N_start:], y_i[self.ui.N_start:],
                            'o', markersize=8, markerfacecolor='none', label='$y[n]$')

            self.ax3d.set_xlabel('x')
            self.ax3d.set_ylabel('y')
            self.ax3d.set_zlabel('z')

        # --------------- Title and common labels ----------------------------        
        self.axes_time[-1].set_xlabel(fb.fil[0]['plt_tLabel'])
        self.axes_time[0].set_title(self.title_str)
        self.ax_r.set_xlim([self.t[self.ui.N_start], self.t[self.ui.N_end-1]])
        #expand_lim(self.ax_r, 0.02)

        self.redraw() # redraw currently active mplwidget

        self.needs_redraw[0] = False

    #=========================================================================
    # Frequency Plots
    #=========================================================================
    def _init_axes_freq(self):
        """
        Clear the axes of the frequency domain matplotlib widgets and
        calculate the fft
        """
        self.plt_freq_resp = qget_cmb_box(self.ui.cmb_plt_freq_resp,
                                          data=False).lower().replace("*", "")
        self.plt_freq_resp_mkr = "*" in qget_cmb_box(self.ui.cmb_plt_freq_resp, data=False)

        self.plt_freq_stim = qget_cmb_box(self.ui.cmb_plt_freq_stim,
                                          data=False).lower().replace("*", "")
        self.plt_freq_stim_mkr = "*" in qget_cmb_box(self.ui.cmb_plt_freq_stim, data=False)

        self.plt_freq_stmq = qget_cmb_box(self.ui.cmb_plt_freq_stmq,
                                          data=False).lower().replace("*", "")
        self.plt_freq_stmq_mkr = "*" in qget_cmb_box(self.ui.cmb_plt_freq_stmq, data=False)


        self.plt_freq_enabled = self.plt_freq_stim != "none" or self.plt_freq_stmq != "none"\
                                    or self.plt_freq_resp != "none"

        #if not self.ui.chk_log_freq.isChecked() and len(self.mplwidget_f.fig.get_axes()) == 2:
        #    self.mplwidget_f.fig.clear() # get rid of second axis when returning from log mode by clearing all
        
        self.mplwidget_f.fig.clf() # clear figure with axes

        en_re_im_f = self.ui.chk_re_im_freq.isChecked()

        num_subplots_f = 1 + en_re_im_f
        
        self.axes_f = self.mplwidget_f.fig.subplots(nrows=num_subplots_f, ncols=1,
                                               sharex=True, squeeze = False)[:,0]
        self.ax_f1 = self.axes_f[0]

        #for ax in self.axes_f:
        #    ax.cla()

        if self.ui.chk_log_freq.isChecked():# and len(self.mplwidget_f.fig.get_axes()) == 1:
            # create second axis scaled for noise power scale if it doesn't exist yet
            self.ax_f1_noise = self.ax_f1.twinx()
            self.ax_f1_noise.is_twin = True

        self.ax_f1.xaxis.tick_bottom() # remove axis ticks on top
        self.ax_f1.yaxis.tick_left() # remove axis ticks right
        self.ax_f1.xaxis.set_minor_locator(AutoMinorLocator()) # enable minor ticks
        self.ax_f1.yaxis.set_minor_locator(AutoMinorLocator())
        
        if en_re_im_f:
            self.ax_f2 = self.axes_f[1]
            self.ax_f2.xaxis.tick_bottom() # remove axis ticks on top
            self.ax_f2.yaxis.tick_left() # remove axis ticks right
            self.ax_f2.xaxis.set_minor_locator(AutoMinorLocator()) # enable minor ticks
            self.ax_f2.yaxis.set_minor_locator(AutoMinorLocator())

        self.calc_fft()

    def draw_freq(self):
        """
        (Re-)draw the frequency domain mplwidget
        """

        self._init_axes_freq()
        plt_response = self.plt_freq_resp != "none"
        plt_stimulus = self.plt_freq_stim != "none"
        plt_stimulus_q = self.plt_freq_stmq != "none" and self.fx_sim
        en_re_im_f = self.ui.chk_re_im_freq.isChecked()

        # freqz-based ideal frequency response
        F_id, H_id = np.abs(calc_Hcomplex(fb.fil[0], params['N_FFT'], True, fs=fb.fil[0]['f_max']))

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

            # frequency vector for FFT-based frequency plots

            F = np.fft.fftfreq(self.ui.N, d=1. / fb.fil[0]['f_max'])
            F_range = fb.fil[0]['freqSpecsRange']

            if fb.fil[0]['freq_specs_unit'] == 'k':
                # By default, k = params['N_FFT'] which is used for the calculation
                # of the non-transient tabs and for F_id / H_id here. 
                # Here, the frequency axes must be scaled to fit the number of 
                # frequency points self.ui.N
                k_scale = self.ui.N / fb.fil[0]['f_max']
                F_id *= k_scale
                F_range = [f * k_scale for f in F_range]
                f_max = self.ui.N
            else:
                f_max = fb.fil[0]['f_max']
                
        #-----------------------------------------------------------------
        # Scale frequency response and calculate power
        #-----------------------------------------------------------------
        # - Scale signals
        # - Calculate total power P from FFT, corrected by window equivalent noise
        #   bandwidth and fixpoint scaling (scale_i / scale_o)
        # - Correct scale for single-sided spectrum
        # - Scale impulse response with N_FFT to calculate frequency response if requested
            if self.ui.chk_scale_impz_f.isEnabled() and self.ui.stim == "Impulse"\
                and self.ui.chk_scale_impz_f.isChecked():
                freq_resp = True # calculate frequency response from impulse response
                scale_impz = self.ui.N
            else:
                freq_resp = False
                scale_impz = 1.

            if plt_stimulus:
                # scale display of frequency response
                Px = np.sum(np.square(np.abs(self.X))) * scale_impz / self.ui.nenbw  
                if fb.fil[0]['freqSpecsRangeType'] == 'half' and not freq_resp:
                    X = calc_ssb_spectrum(self.X) * self.scale_i * scale_impz
                else:
                    X = self.X * self.scale_i * scale_impz

            if plt_stimulus_q:
                Pxq = np.sum(np.square(np.abs(self.X_q))) * scale_impz / self.ui.nenbw
                if fb.fil[0]['freqSpecsRangeType'] == 'half' and not freq_resp:
                    X_q = calc_ssb_spectrum(self.X_q) * self.scale_i * scale_impz
                else:
                    X_q = self.X_q * self.scale_i * scale_impz

            if plt_response:
                Py = np.sum(np.square(np.abs(self.Y * self.scale_o))) * scale_impz / self.ui.nenbw
                if fb.fil[0]['freqSpecsRangeType'] == 'half' and not freq_resp:
                    Y = calc_ssb_spectrum(self.Y) * self.scale_o * scale_impz
                else:
                    Y = self.Y * self.scale_o * scale_impz

        #-----------------------------------------------------------------
        # Set frequency range
        #-----------------------------------------------------------------
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
                F_id -= fb.fil[0]['f_S']/2.
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

            else: # fb.fil[0]['freqSpecsRangeType'] == 'whole'
                # display 0 ... f_S -> shift frequency axis
                F    = np.fft.fftshift(F) + f_max/2.
                if not freq_resp:
                    H_id /= 2
        #-----------------------------------------------------------------
        # Calculate log FFT and power if selected, set units
        #-----------------------------------------------------------------

            if self.ui.chk_log_freq.isChecked():
                unit = " in dBV"
                unit_P = "dBW"
                unit_nenbw = "dB"
                unit_cgain = "dB"
                H_F_pre = "|"
                H_F_post = "|"

                nenbw = 10 * np.log10(self.ui.nenbw)
                cgain = 20 * np.log10(self.ui.cgain)
                H_id = np.maximum(20 * np.log10(H_id), self.ui.bottom_f)
                if plt_stimulus:
                    Px = 10*np.log10(Px)
                    if en_re_im_f:
                        X_r = np.maximum(20 * np.log10(np.abs(X.real)), self.ui.bottom_f)
                        X_i = np.maximum(20 * np.log10(np.abs(X.imag)), self.ui.bottom_f)
                    else:
                        X_r = np.maximum(20 * np.log10(np.abs(X)), self.ui.bottom_f)                        
 
                if plt_stimulus_q:
                    Pxq = 10*np.log10(Pxq)
                    if en_re_im_f:
                        X_q_r = np.maximum(20 * np.log10(np.abs(X_q.real)), self.ui.bottom_f)
                        X_q_i = np.maximum(20 * np.log10(np.abs(X_q.imag)), self.ui.bottom_f)
                    else:
                        X_q_r = np.maximum(20 * np.log10(np.abs(X_q)), self.ui.bottom_f)
                        
                if plt_response:
                    Py = 10*np.log10(Py)
                    if en_re_im_f:
                        Y_r = np.maximum(20 * np.log10(np.abs(Y.real)), self.ui.bottom_f)
                        Y_i = np.maximum(20 * np.log10(np.abs(Y.imag)), self.ui.bottom_f)
                    else:
                        Y_r = np.maximum(20 * np.log10(np.abs(Y)), self.ui.bottom_f)                        

            else:
                H_F_pre = ""
                H_F_post = ""
                if plt_stimulus:
                    if en_re_im_f:
                        X_r = X.real
                        X_i = X.imag
                    else:
                        X_r = np.abs(X)

                if plt_stimulus_q:
                    if en_re_im_f:
                        X_q_r = X_q.real
                        X_q_i = X_q.imag                        
                    else:
                        X_q_r = np.abs(X_q)

                if plt_response:
                    if en_re_im_f:
                        Y_r = Y.real
                        Y_i = Y.imag
                    else:
                        Y_r = np.abs(Y)

                unit = " in V"
                unit_P = "W"
                unit_nenbw = "bins"
                unit_cgain = ""
                nenbw = self.ui.nenbw
                cgain = self.ui.cgain
            
            if en_re_im_f:
                H_Fi_str = r'$\Im\{$' + H_F_str + r'$\}$'
                H_Fr_str = r'$\Re\{$' + H_F_str + r'$\}$'
            else:
                H_F_pre = "|"
                H_Fr_str = H_F_str
                H_Fi_str = 'undefined'
                H_F_post = "|"

            H_Fi_str = H_F_pre + H_Fi_str + H_F_post + unit
            H_Fr_str = H_F_pre + H_Fr_str + H_F_post + unit

            # --------------- Plot stimulus and response ----------------------
            show_info = self.ui.chk_show_info_freq.isChecked()
            if plt_stimulus:
                label_1 = "|$X$" + ejO_str + "|"
                if en_re_im_f:
                    label_1 = "$X_r$" + ejO_str
                    label_2 = "$X_i$" + ejO_str
                    self.draw_data(self.plt_freq_stim, self.ax_f2, F, X_i,
                        label=label_2, bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_stim,
                        mkr=self.plt_freq_stim_mkr, mkr_fmt=self.fmt_mkr_stim)
                if show_info:
                    label_1 += ":\t$P$ = {0:.3g} {1}".format(Px, unit_P)

                self.draw_data(self.plt_freq_stim, self.ax_f1, F, X_r,
                    label=label_1, bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_stim,
                    mkr=self.plt_freq_stim_mkr, mkr_fmt=self.fmt_mkr_stim)

            if plt_stimulus_q:
                label_1 = "$|X_Q$" + ejO_str + "|"
                if en_re_im_f:
                    label_1 = "$X_{Q,r}$" + ejO_str
                    label_2 = "$X_{Q,i}$" + ejO_str
                    self.draw_data(self.plt_freq_stmq, self.ax_f2, F, X_q_i,
                        label=label_2, bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_stmq,
                        mkr=self.plt_freq_stmq_mkr, mkr_fmt=self.fmt_mkr_stmq)
                if show_info:
                    label_1 += ":\t$P$ = {0:.3g} {1}".format(Pxq, unit_P)

                self.draw_data(self.plt_freq_stmq, self.ax_f1, F, X_q_r,
                    label=label_1, bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_stmq,
                    mkr=self.plt_freq_stmq_mkr, mkr_fmt=self.fmt_mkr_stmq)

            if plt_response:
                label_1 = "$|Y$" + ejO_str + "|"
                if en_re_im_f:
                    label_1 = "$Y_r$" + ejO_str
                    label_2 = "$Y_i$" + ejO_str
                    self.draw_data(self.plt_freq_resp, self.ax_f2, F, Y_i,
                        label=label_2, bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_resp,
                        mkr=self.plt_freq_resp_mkr, mkr_fmt=self.fmt_mkr_resp)
                if show_info:
                    label_1 += ":\t$P$ = {0:.3g} {1}".format(Py, unit_P)

                self.draw_data(self.plt_freq_resp, self.ax_f1, F, Y_r,
                    label=label_1, bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_resp,
                    mkr=self.plt_freq_resp_mkr, mkr_fmt=self.fmt_mkr_resp)

            if self.ui.chk_Hf.isChecked():
                self.ax_f1.plot(F_id, H_id, c="gray",label="$H_{id}$" + ejO_str)
            
            # --------------- LEGEND (real part) ----------------------------------
            if self.plt_freq_enabled or self.ui.chk_Hf.isChecked():
                self.ax_f1.legend(loc='best', fontsize='small', fancybox=True, framealpha=0.7)
                # get handles and labels for all plots so far
                handles, labels = self.ax_f1.get_legend_handles_labels()
                # get a tuple with pairs of (label, handle), sorted for the label
                sorted_pairs = sorted(zip(labels, handles))
                # convert back to two lists
                labels, handles = [ list(tuple) for tuple in  zip(*sorted_pairs)]
    
                if show_info:
                    # Create two empty patches for NENBW and CGAIN and extend handles list with them
                    handles.extend([mpl_patches.Rectangle((0, 0), 1, 1, fc="white",
                                                         ec="white", lw=0, alpha=0)] * 2)
                    labels.append("$NENBW$ = {0:.4g} {1}".format(nenbw, unit_nenbw))
                    labels.append("$CGAIN$  = {0:.4g} {1}".format(cgain, unit_cgain))               

                    self.ax_f1.legend(handles, labels, loc='best', fontsize='small',
                               fancybox=True, framealpha=0.7)                

            if en_re_im_f and self.plt_freq_enabled:
                self.ax_f2.legend(loc='best', fontsize='small',
                               fancybox=True, framealpha=0.7)
                self.ax_f2.set_ylabel(H_Fi_str)

            self.axes_f[-1].set_xlabel(fb.fil[0]['plt_fLabel'])
            self.ax_f1.set_ylabel(H_Fr_str)
            #self.ax_f1.set_xlim(fb.fil[0]['freqSpecsRange'])
            self.ax_f1.set_xlim(F_range)
            self.ax_f1.set_title("Spectrum of " + self.title_str)

            if self.ui.chk_log_freq.isChecked():
                # scale second axis for noise power
                corr = 10*np.log10(self.ui.N / self.ui.nenbw)
                mn, mx = self.ax_f1.get_ylim()
                self.ax_f1_noise.set_ylim(mn+corr, mx+corr)
                self.ax_f1_noise.set_ylabel(r'$P_N$ in dBW')

        self.redraw() # redraw currently active mplwidget

        self.needs_redraw[1] = False
#------------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the currently visible canvas when e.g. the canvas size has changed
        """
        idx = self.tabWidget.currentIndex()
        self.tabWidget.currentWidget().redraw()
        #wdg = getattr(self, self.tab_mplwidgets[idx])
        logger.debug("Redrawing tab {0}".format(idx))
        #wdg_cur.redraw()
        self.needs_redraw[idx] = False
#        self.mplwidget_t.redraw()
#        self.mplwidget_f.redraw()

#------------------------------------------------------------------------------

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
