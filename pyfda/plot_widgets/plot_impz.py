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
import time
from pyfda.libs.compat import (
    QWidget, pyqtSignal, QTabWidget, QVBoxLayout, QIcon, QSize, QSizePolicy)

import numpy as np
import scipy.signal as sig
import matplotlib.patches as mpl_patches
# import matplotlib.lines as lines
from matplotlib.ticker import AutoMinorLocator

import pyfda.filterbroker as fb
import pyfda.libs.pyfda_fix_lib as fx
from pyfda.libs.pyfda_sig_lib import angle_zero
from pyfda.libs.pyfda_lib import (
    safe_eval, pprint_log, calc_ssb_spectrum, calc_Hcomplex)
from pyfda.libs.pyfda_qt_lib import (
    qget_cmb_box, qset_cmb_box, qstyle_widget, qcmb_box_add_item, qcmb_box_del_item)
from pyfda.pyfda_rc import params  # FMT string for QLineEdit fields, e.g. '{:.3g}'
from pyfda.plot_widgets.mpl_widget import MplWidget, stems, scatter

from pyfda.plot_widgets.tran.plot_tran_stim import Plot_Tran_Stim
from pyfda.plot_widgets.tran.tran_io import Tran_IO
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
    sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outgoing, e.g. when stimulus has been calculated
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self):
        super().__init__()

        self.ACTIVE_3D = False
        self.ui = PlotImpz_UI()  # create the UI part with buttons etc.

        # initial settings
        # ==================
        # flag whether specs have been changed and plots need to be recalculated
        self.needs_calc = True
        # same when fixpoint specs have been changed, only needed in Fixpoint mode
        self.needs_calc_fx = True
        self.needs_redraw = [True] * 2  # flag which plot needs to be redrawn
        self.error = False
        fb.fil[0]['fx_sim'] = False  # disable fixpoint mode initially
        self.fx_sim_old = fb.fil[0]['fx_sim']
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
        self.fmt_plot_stim_interp = {'color': 'black', 'linewidth': 1, 'alpha': 0.5}

        self.fmt_mkr_stim = {'marker': 's', 'color': 'blue', 'alpha': 0.5,
                             'ms': self.fmt_mkr_size}
        self.fmt_plot_stmq = {'color': 'darkgreen', 'linewidth': 2, 'alpha': 0.5}
        self.fmt_mkr_stmq = {'marker': 'D', 'color': 'darkgreen', 'alpha': 0.5,
                             'ms': self.fmt_mkr_size}

        self._construct_UI()

        # --------------------------------------------
        # initialize UI and `fb.fil[0]['fx_sim']` for fixpoint or float simulation
        # self.update_fx_ui_settings(qget_cmb_box(self.ui.cmb_sim_select, data=False))
        self.update_fx_ui_settings()
        # store current state of `fb.fil[0]['fx_sim']``
        # self.fx_sim_old = fb.fil[0]['fx_sim']

        self.impz_init()  # initial calculation of stimulus and response and drawing

    def _construct_UI(self):
        """
        Create the top level UI of the widget, consisting of tabbed matplotlib widgets,
        tabbed stimuli and a control frame.
        """
        # ----------------------------------------------------------------------
        # Tabbed layout with vertical tabs ("west") for time and frequency domain
        # ----------------------------------------------------------------------
        # ---------- MplWidget for TIME domain plots ---------------------------
        self.mplwidget_t = MplWidget(self)
        self.mplwidget_t.setObjectName("mplwidget_t1")
        self.mplwidget_t.layVMainMpl.addWidget(self.ui.wdg_ctrl_time)
        self.mplwidget_t.layVMainMpl.setContentsMargins(*params['mpl_margins'])
        self.mplwidget_t.mplToolbar.a_he.setEnabled(True)
        self.mplwidget_t.mplToolbar.a_he.info = "manual/plot_impz.html"
        self.mplwidget_t.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ---------- MplWidget for FREQUENCY domain plots ----------------------
        self.mplwidget_f = MplWidget(self)
        self.mplwidget_f.setObjectName("mplwidget_f1")
        self.mplwidget_f.layVMainMpl.addWidget(self.ui.wdg_ctrl_freq)
        self.mplwidget_f.layVMainMpl.setContentsMargins(*params['mpl_margins'])
        self.mplwidget_f.mplToolbar.a_he.setEnabled(True)
        self.mplwidget_f.mplToolbar.a_he.info = "manual/plot_impz.html"
        self.mplwidget_f.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ----------- Construct TabWidget with time and frequency plot widgets
        self.tab_mpl_w = QTabWidget(self)
        self.tab_mpl_w.setTabPosition(QTabWidget.West)
        self.tab_mpl_w.setObjectName("tab_mpl_w")
        self.tab_mpl_w.addTab(self.mplwidget_t, "Time")
        self.tab_mpl_w.setTabToolTip(0, "Impulse and transient response of filter")
        self.tab_mpl_w.addTab(self.mplwidget_f, "Frequency")
        self.tab_mpl_w.setTabToolTip(
            1, "Spectral representation of impulse or transient response")
        # list with mplwidgets
        self.tab_mplwidget_list = ["mplwidget_t", "mplwidget_f"]

        # ----------------------------------------------------------------------
        # Tabbed layout with vertical tabs ("west") for stimulus and audio
        # ----------------------------------------------------------------------
        self.stim_wdg = Plot_Tran_Stim()
        # set "Stim:" label width to same width as "Plots:" label:
        self.stim_wdg.ui.lbl_title_stim.setFixedWidth(self.ui.lbl_title_plot_time.sizeHint().width())
        self.file_io_wdg = Tran_IO()

        self.tab_stim_w = QTabWidget(self)
        self.tab_stim_w.setObjectName("tab_stim_w")
        self.tab_stim_w.setTabPosition(QTabWidget.West)
        self.tab_stim_w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        tab_w = 30  # needs to fit with the tab size defined in pyfda_rc.py
        # tab_w = self.tab_mpl_w.tabBar().tabSizeHint(0).width()  # crashes under Linux
        self.tab_stim_w.setIconSize(QSize(tab_w, tab_w))
        self.tab_stim_w.addTab(self.stim_wdg, QIcon(":/graph_90.png"), "")
        self.tab_stim_w.setTabToolTip(0, "Stimuli")

        self.tab_stim_w.addTab(self.file_io_wdg, QIcon(":/file.svg"), "")
        self.tab_stim_w.setTabToolTip(1, "I/O")

        self.resize_stim_tab_widget()
        # ----------------------------------------------------------------------
        # ---------------- GLOBAL LAYOUT ---------------------------------------
        # ----------------------------------------------------------------------
        layVMain = QVBoxLayout()
        layVMain.addWidget(self.tab_mpl_w)
        layVMain.addWidget(self.tab_stim_w)
        layVMain.addWidget(self.ui.wdg_ctrl_run)
        layVMain.setContentsMargins(*params['mpl_margins'])

        self.setLayout(layVMain)
        self.updateGeometry()

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        # connect UI to widgets and signals upstream:
        self.ui.sig_tx.connect(self.process_sig_rx)

        self.stim_wdg.sig_tx.connect(self.process_sig_rx)
        self.sig_rx.connect(self.stim_wdg.sig_rx)
        self.file_io_wdg.sig_tx.connect(self.process_sig_rx)
        self.mplwidget_t.mplToolbar.sig_tx.connect(self.process_sig_rx)
        self.mplwidget_f.mplToolbar.sig_tx.connect(self.process_sig_rx)
        # self.mplwidget.mplToolbar.enable_plot(state = False) # disable initially
        # When user has selected a different local tab, trigger a redraw of current tab
        self.tab_mpl_w.currentChanged.connect(self.draw)  # passes # of active tab

        # ---------------------------------------------------------------------
        # UI SIGNALS & SLOTs
        # ---------------------------------------------------------------------
        self.tab_stim_w.currentChanged.connect(self.resize_stim_tab_widget)
        # --- run control ---
        self.ui.cmb_sim_select.currentIndexChanged.connect(self.toggle_fx_setting)
        self.ui.but_run.clicked.connect(self.impz_init)
        self.ui.but_auto_run.clicked.connect(self.calc_auto)
        self.ui.but_fx_scale.clicked.connect(self.draw)
        self.ui.cmb_ui_select.currentIndexChanged.connect(self.toggle_stim_options)
        # --- time domain plotting --------------------------------------------
        self.ui.cmb_plt_time_resp.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_time_stim.currentIndexChanged.connect(self.draw)
        self.ui.chk_plt_time_stim_interp.clicked.connect(self.draw)
        self.ui.cmb_plt_time_stmq.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_time_spgr.currentIndexChanged.connect(self._spgr_cmb)
        self.ui.but_log_time.clicked.connect(self.draw)
        self.ui.led_log_bottom_time.editingFinished.connect(self.draw)
        self.ui.but_log_spgr_time.clicked.connect(self.draw)
        self.ui.led_time_nfft_spgr.editingFinished.connect(self._spgr_ui2params)
        self.ui.led_time_ovlp_spgr.editingFinished.connect(self._spgr_ui2params)
        self.ui.cmb_mode_spgr_time.currentIndexChanged.connect(self.draw)
        self.ui.chk_byfs_spgr_time.clicked.connect(self.draw)
        self.ui.but_fx_range.clicked.connect(self.draw)
        self.ui.chk_win_time.clicked.connect(self.draw)
        # --- frequency domain plotting ---------------------------------------
        self.ui.cmb_plt_freq_resp.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_freq_stim.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_freq_stmq.currentIndexChanged.connect(self.draw)
        self.ui.but_Hf.clicked.connect(self.draw)
        self.ui.cmb_freq_display.currentIndexChanged.connect(self.draw)
        self.ui.but_log_freq.clicked.connect(self.draw)
        self.ui.led_log_bottom_freq.editingFinished.connect(self.draw)
        self.ui.but_freq_norm_impz.clicked.connect(self.draw)
        self.ui.but_freq_show_info.clicked.connect(self.draw)

# ------------------------------------------------------------------------------
    def toggle_stim_options(self):
        """
        Toggle visibility of stimulus options, depending on the state of the
        "Stimuli" button
        """
        self.tab_stim_w.setVisible(qget_cmb_box(self.ui.cmb_ui_select) in {"stim", "plot_stim"})
        self.ui.wdg_ctrl_freq.setVisible(qget_cmb_box(self.ui.cmb_ui_select) in {"plot", "plot_stim"})
        self.ui.wdg_ctrl_time.setVisible(qget_cmb_box(self.ui.cmb_ui_select) in {"plot", "plot_stim"})

# ------------------------------------------------------------------------------
    def resize_stim_tab_widget(self):
        """
        Resize active tab of stimulus Tab widget to fit the height of the contained
        widget. This is triggered by:
        - initialization in `_construct_UI()`
        - changed tab in the stimulus tab widget (signal-slot)
        - an 'ui-changed' - signal (`process_signal_rx()`)
        """
        # logger.warning(f"w = {self.tab_stim_w.tabBar().width()}, "
        #                f"h = {self.tab_stim_w.tabBar().height()}")
        # logger.warning(f"w = {self.tab_mpl_w.tabBar().width()}, "
        #                f"h = {self.tab_mpl_w.tabBar().height()}")
        # tabBar height is also the width / hight of the tab icons
        h_min = self.tab_stim_w.tabBar().height()
        # logger.warning(f"min hint = {self.stim_wdg.minimumSizeHint()}, h_min = {h_min}")
        if self.tab_stim_w.currentWidget() is None:
            logger.warning("no embedded widget!")
            h = 0
        else:
            h = self.tab_stim_w.currentWidget().minimumSizeHint().height()
        self.tab_stim_w.setMaximumHeight(max(h, h_min))
        self.tab_stim_w.setMinimumHeight(max(h, h_min))

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from
        - the navigation toolbars (time and freq.)
        - local widgets (impz_ui) and
        - plot_tab_widgets() (global signals)
        """
        logger.debug("SIG_RX - needs_calc: {0} | vis: {1}\n{2}\n\tfx_sim = {3}: cmb = {4}"
                    .format(self.needs_calc, self.isVisible(), pprint_log(dict_sig),
                            fb.fil[0]['fx_sim'], qget_cmb_box(self.ui.cmb_sim_select)))
        # logger.debug(f'SIG_RX: "{first_item(dict_sig)}"')

        if dict_sig['id'] == id(self):
            # logger.debug(f'Stopped infinite loop: "{first_item(dict_sig)}"')
            return

        if 'fx_sim' in dict_sig:
            # --------------- START (ext. widget) ------------
            if dict_sig['fx_sim'] == 'start_fx_sim':
                """
                Fixpoint simulation started from external widget, e.g.
                from 'input_fixpoint_specs' by pressing the "Sim FX" button
                - Reset error flag and set 'needs_calc' flags
                - Set fixpoint mode
                - Update run button to "changed"
                - Force-start simulation with `self.impz_init(True)`
                """

                self.needs_calc = True      # force recalculation
                self.needs_calc_fx = True   # force fx recalculation
                self.error = False          # reset error flag

                self.update_fx_ui_settings("fixpoint")  # set fixpoint mode
                qstyle_widget(self.ui.but_run, "changed")
                self.ui.but_run.setIcon(QIcon(":/play.svg"))
                self.impz_init(True)
                return
            # --------------- specs changed ------------
            elif dict_sig['fx_sim'] == 'specs_changed':
                """
                Fixpoint widget specs have been updated.
                - set `self.needs_calc_fx = True`.
                If fixpoint mode is active:
                - Reset error flag
                - Force recalculation (`self.needs_calc = True`)
                - Update run button style to "changed"
                - If widget is visible, initialize fixpoint widget and
                    start simulation via `self.impz_init()`
                """
                self.needs_calc_fx = True   # fx sim needs recalculation

                if fb.fil[0]['fx_sim']:     # fixpoint mode is active
                    self.error = False      # reset error flag
                    self.needs_calc = True  # force recalculation

                    qstyle_widget(self.ui.but_run, "changed")
                    self.ui.but_run.setIcon(QIcon(":/play.svg"))
                    if self.isVisible():
                        self.impz_init()

            # --------------- 'start_fx_response_calculation' ---------
            elif dict_sig['fx_sim'] == 'start_fx_response_calculation':
                """
                The fixpoint widget has been initialized and starts the fx simulation
                when the widget is visible via `self.impz()` and the handle to the
                fixpoint simulation method handle passed in `dict_sig['fxfilter_func']`
                """
                self.fxfilter = dict_sig['fxfilter_func']
                if self.isVisible():
                    self.impz()
                return

            # --------------- ERROR -------------------
            elif dict_sig['fx_sim'] == 'error':
                self.needs_calc = True
                self.error = True
                self.ui.but_run.setIcon(QIcon(":/play.svg"))
                qstyle_widget(self.ui.but_run, "error")
                if 'err_msg' in dict_sig:
                    logger.error(dict_sig['err_msg'])
                return

            # ---------------
            elif not dict_sig['fx_sim']:
                logger.error('Missing value for key "fx_sim".')

            else:
                logger.error('Unknown value "{0}" for "fx_sim" key\n'
                             '\treceived from "{1}"'.format(dict_sig['fx_sim'],
                                                            dict_sig['class']))

        # --- widget is visible, handle all signals except 'fx_sim' -----------
        elif self.isVisible():
            if 'data_changed' in dict_sig or 'specs_changed' in dict_sig\
                    or self.needs_calc or (fb.fil[0]['fx_sim'] and self.needs_calc_fx):

                N_end = 0
                # new file has been loaded
                if 'data_changed' in dict_sig and dict_sig['data_changed'] == 'file_io':
                    # make file data available to stimulus widget and modify number of
                    # data points to be used:
                    self.file_loaded()

                # update number of data points in impz_ui and FFT window
                # needed when e.g. FIR filter order has been changed, requiring
                # a different number of data points for simulation. Don't emit a signal.
                self.ui.update_N(emit=False)
                self.needs_calc = True
                # Highlight "RUN" button
                self.ui.but_run.setIcon(QIcon(":/play.svg"))
                qstyle_widget(self.ui.but_run, "changed")
                self.impz_init()

            elif 'ui_local_changed' in dict_sig:
                # treat all local UI events here
                self.resize_stim_tab_widget()
                self.needs_calc = True
                # make file data available to stimulus widget and modify number of
                # data points to be used:
                self.file_loaded()
                self.impz_init()

            elif 'view_changed' in dict_sig:
                if dict_sig['view_changed'] == 'f_S':
                    self.stim_wdg.ui.recalc_freqs()
                self.draw()

            elif 'home' in dict_sig:
                self.redraw()
                self.needs_redraw[self.tab_mpl_w.currentIndex()] = False

        else:  # invisible
            if 'data_changed' in dict_sig or 'specs_changed' in dict_sig:
                self.needs_calc = True

            elif 'view_changed' in dict_sig:
                # update frequency related widgets (visible or not)
                if dict_sig['view_changed'] == 'f_S':
                    self.stim_wdg.ui.recalc_freqs()
            elif 'ui_local_changed' in dict_sig:
                self.needs_redraw = [True] * 2

    def file_loaded(self):
        """
        Check status of file_io widget:
        - if no file is loaded or `cmb_file_io == 'off'`, do nothing and return 0
        - if `cmb_file_io == 'add'`, map the file data to `self.stim_wdg.x_file`
          to make it accessible from the stimulus widget
        - if `cmb_file_io == 'use'` do the same and set N_end = len(file_data) in th UI
        """
        # logger.info(
        #     f"File loaded with {self.file_io_wdg.n_chan} channel(s) and "
        #     f"{self.file_io_wdg.N} samples.")
        if not hasattr(self.file_io_wdg, 'N') or self.file_io_wdg.N == 0:
            qset_cmb_box(self.stim_wdg.ui.cmb_file_io, "off", data=True)
            self.stim_wdg.ui.cmb_file_io.setEnabled(False)
        else:
            self.stim_wdg.ui.cmb_file_io.setEnabled(True)
            if qget_cmb_box(self.stim_wdg.ui.cmb_file_io) == "off":
                return

            # map data from file io widget to stimulus widget:
            self.stim_wdg.x_file = self.file_io_wdg.x
            if qget_cmb_box(self.stim_wdg.ui.cmb_file_io) == "use":
                # override ui setting of N_end
                self.ui.update_N(emit=False, N_end = self.file_io_wdg.N)
            else:  # qget_cmb_box(self.stim_wdg.ui.cmb_file_io) == "add":
                pass
        return

# =============================================================================
# Simulation: Calculate stimulus, response and draw them
# =============================================================================
    def calc_auto(self, autorun=None):
        """
        Triggered when checkbox "Autorun" is clicked.

        When Autorun has been pushed (`but_auto_run.isChecked() == True`) and
        calculation is required, automatically run `impz_init()`.
        """
        if self.ui.but_auto_run.isChecked() and self.needs_calc:
            self.impz_init()

    # --------------------------------------------------------------------------
    def impz_init(self, arg=None):
        """
        Triggered by:
            - _construct_UI()  [Initialization]
            - Pressing "Run" button, passing button state as a boolean
            - Changing between fixpoint and float mode (`self.ui.cmb_sim_select)
            - Activating "Autorun" via `self.calc_auto()`
            - Autorun (when something relevant in the UI has been updated)
            - 'fx_sim' : 'specs_changed'

        The following tasks are performed:
            - Enable energy scaling for impulse stimuli when requirements are met
            - check for and enable fixpoint settings
            - when triggered by `but_run` or when `Auto`== pressed and
              `self.needs_calc == True`, continue with calculating stimulus / response
            - When in fixpoint mode, initialize quantized stimulus `x_q` and input
              quantizer and emit {'fx_sim':'init'}
        """
        # set number of data points from file length when 'use' is selected
        if qget_cmb_box(self.stim_wdg.ui.cmb_file_io) == 'use':
            self.ui.update_N(emit=False, N_end=self.file_io_wdg.N)

        # allow scaling the frequency response from pure impulse (no DC, noise or file)
        # button is only visible for impulse-shaped stimuli
        self.ui.but_freq_norm_impz.setEnabled(
            (self.stim_wdg.ui.noi == 0 or
             self.stim_wdg.ui.cmbNoise.currentText() == 'None')
            and self.stim_wdg.ui.DC == 0
            and self.stim_wdg.ui.cmb_stim == "impulse"
            and qget_cmb_box(self.stim_wdg.ui.cmb_file_io) == "off"
            )
        self.ui.but_freq_norm_impz.setVisible(self.stim_wdg.ui.cmb_stim == "impulse")

        self.error = False
        self.needs_redraw = [True] * 2

        # check for fixpoint setting (fb.fil[0]['fx_sim']) and update UI if needed
        self.update_fx_ui_settings()

        if type(arg) == bool:
            self.needs_calc = True  # but_run has been pressed -> force run
        elif not self.ui.but_auto_run.isChecked():  # "Auto" is not active, return
            return

        if self.needs_calc:
            # set title and axis string and calculate 10 samples to determine ndtype
            x_test = self.stim_wdg.calc_stimulus_frame(init=True)
            self.title_str = self.stim_wdg.title_str

            self.N_first = 0  # initialize frame index
            self.n = np.arange(self.ui.N_end, dtype=float)
            self.x = np.empty(self.ui.N_end, dtype=x_test.dtype)  # stimulus
            # Test whether stimulus or filter coefficients are complex and set
            # flag and UI field correspondingly
            self.cmplx = bool(
                np.any(np.any(np.iscomplex(x_test))
                       or np.any(np.iscomplex(np.asarray(fb.fil[0]['ba'])))))
            if self.cmplx:
                self.y = np.empty_like(self.x, dtype=complex)  # always complex
            else:
                self.y = np.empty_like(self.x)  # same type as self.x
            self.ui.lbl_stim_cmplx_warn.setVisible(self.cmplx)

            # initialize progress bar
            self.ui.prg_wdg.setMaximum(self.ui.N_end)
            self.ui.prg_wdg.setValue(0)
            self.ui.but_run.setIcon(QIcon(":/stop.svg"))
            qstyle_widget(self.ui.but_run, "running")

            self.t_start = time.process_time()  # store starting time

            if fb.fil[0]['fx_sim']:
                # - update plot title string
                # - setup input quantizer self.q_i
                # - emit {'fx_sim': 'init'} to listening widgets (input_fixpoint_specs)
                self.title_str = r'$Fixpoint$ ' + self.title_str
                self.x_q = np.empty_like(self.x, dtype=np.float64)  # quantized stimulus
                if np.any(np.iscomplex(x_test)):
                    logger.warning(
                        "Complex stimulus: Only its real part is used for the "
                        "fixpoint filter!")
                # setup and initialize input quantizer
                self.q_i = fx.Fixed(fb.fil[0]['fxqc']['QI'])
                # always use integer decimal format for input quantizer
                self.q_i.set_qdict({'fx_base': 'dec'})

                # initialize FX filter and get a handle for `fxfilter()` function
                self.emit({'fx_sim': 'init'})
                return  # process_sig_rx() directly calls impz() in next step
            else:
                # Initialize filter memory with zeros, for either cascaded structure (sos)
                # or direct form
                self.sos = np.asarray(fb.fil[0]['sos'])
                if len(self.sos) > 0:  # has second order sections
                    self.zi = np.zeros((self.sos.shape[0], 2))
                else:
                    self.bb = np.asarray(fb.fil[0]['ba'][0])
                    self.aa = np.asarray(fb.fil[0]['ba'][1])
                    if min(len(self.aa), len(self.bb)) < 2:
                        logger.error(
                            'No proper filter coefficients: len(a), len(b) < 2 !')
                        return
                    self.zi = np.zeros(max(len(self.aa), len(self.bb)) - 1)
                # calculate float impulse response:
                self.impz()

    # --------------------------------------------------------------------------
    def impz(self):
        """
        Calculate floating point / fixpoint response and redraw it

        Triggered by:
        - `self.impz_init()` (floating point)
        -  Fixpoint widget, requesting "start_fx_response_calculation"
            via `process_rx_signal()` (fixpoint filter)
        """
        while self.N_first < self.ui.N_end:
            # logger.info("impz(): Calculating frame "
            #             f"{int(np.ceil(self.N_first / self.ui.N_frame)) + 1} of "
            #             f"{int(np.ceil(self.ui.N_end / self.ui.N_frame))}")
            # The last frame could be shorter than self.ui.N_frame:
            L_frame = min(self.ui.N_frame, self.ui.N_end - self.N_first)
            # Define slicing expression for the current frame
            frame = slice(self.N_first, self.N_first + L_frame)

            # ------------------------------------------------------------------
            # ---- calculate stimuli for current frame -------------------------
            # ------------------------------------------------------------------
            self.x[frame] = self.stim_wdg.calc_stimulus_frame(
                N_first=self.N_first, N_frame=L_frame, N_end=self.ui.N_end)

            # ------------------------------------------------------------------
            # ---- calculate fixpoint or floating point response for current frame
            # ------------------------------------------------------------------
            if fb.fil[0]['fx_sim']:  # fixpoint filter
                self.x_q[frame] = self.q_i.fixp(self.x[frame].real)  # quantize stimulus
                # --------------------------------------------------------------
                # ---- Get fixpoint response for current frame -----------------
                # --------------------------------------------------------------
                try:
                    self.y[frame] = np.asarray(self.fxfilter(self.x_q[frame]))

                except ValueError as e:
                    if self.fxfilter(self.x_q[frame]) is None:
                        logger.error("Fixpoint simulation returned empty results!")
                    else:
                        logger.error("Simulator error {0}".format(e))
                        fb.fx_results = None
                    self.error = True

                if self.error:
                    self.ui.but_run.setIcon(QIcon(":/play.svg"))
                    qstyle_widget(self.ui.but_run, "error")
                    self.needs_calc = True
                    break  # exit while loop

            else:
                # --------------------------------------------------------------
                # ---- Get floating point response for current frame -----------
                # --------------------------------------------------------------
                if len(self.sos) > 0:  # has second order sections
                    self.y[frame], self.zi = sig.sosfilt(self.sos, self.x[frame],
                                                         zi=self.zi)
                else:  # no second order sections
                    self.y[frame], self.zi = sig.lfilter(
                        self.bb, self.aa, self.x[frame], zi=self.zi)
                # remove complex values produced by numerical inaccuracies,
                # `tol` is specified in multiples of machine eps
                self.y[frame] = np.real_if_close(self.y[frame], tol=1e3)

            # TODO: Test for user interrupt here
            # --- Increase frame counter ---------------------------------------
            self.N_first += self.ui.N_frame
            self.ui.prg_wdg.setValue(self.N_first)

        # -------------------------------------------------------------
        # ----------------------- finish ------------------------------
        # -------------------------------------------------------------
        self.impz_finish()

    # --------------------------------------------------------------------------
    def impz_finish(self):
        """
        Do some housekeeping, resetting and drawing when `self.impz()`
        has finished:

        - Calculate step error if selected
        - Check for complex stimulus or response
        - Calculate simulation time
        - Draw the signals
        - Reset Run Icon to normal state, reset `needs_calc` flag

        """
        # step error calculation: calculate system DC response and subtract it
        # from the response
        if self.stim_wdg.ui.stim == "step" and self.stim_wdg.ui.chk_step_err.isChecked():
            if len(self.sos) > 0:  # has second order sections
                dc = sig.sosfreqz(self.sos, [0])  # yields (w(0), H(0))
            else:
                dc = sig.freqz(self.bb, self.aa, [0])
            self.y[max(self.ui.N_start, self.stim_wdg.T1_idx):] = \
                self.y[max(self.ui.N_start, self.stim_wdg.T1_idx):] - abs(dc[1])

        self.ui.prg_wdg.setValue(self.ui.N_end)  # 100% reached
        self.t_resp = time.process_time()

        t_sim_str = f"[{(self.t_resp - self.t_start) * 1000:5.4g} ms]: "
        logger.info(t_sim_str + f"Calculated transient {self.fx_str}response")

        self.draw()
        # self.needs_redraw[self.tab_mpl_w.currentIndex()] = False
        self.needs_calc = False
        self.needs_calc_fx = False
        logger.info('[{0:5.4g} ms]: Plotted transient {1}response'
                    .format((time.process_time() - self.t_resp)*1000, self.fx_str))
        self.ui.but_run.setIcon(QIcon(":/play.svg"))
        qstyle_widget(self.ui.but_run, "normal")

        if fb.fil[0]['fx_sim']:
            self.emit({'fx_sim': 'finish'})

# =============================================================================
    def toggle_fx_setting(self):
        """ Triggered by changing `self.ui.cmb_sim_select` """

        fb.fil[0]['fx_sim'] = (qget_cmb_box(self.ui.cmb_sim_select) == "fixpoint")
        self.update_fx_ui_settings()
        self.impz_init()

    # --------------------------------------------------------------------------
    def update_fx_ui_settings(self, fx=None):
        """
        Select between fixpoint and floating point simulation and update FX UI
        settings.

        Parameter `fx` can be:

        - str "fixpoint", "float" or `None` when called directly. "fixpoint"
          or "float" updates the combobox setting correspondingly. `None`
          only upcates the UI.

        - int 0 or 1 when triggered by changing the index of combobox
          `self.ui.cmb_sim_select` (signal-slot-connection)

        When fixpoint simulation is selected, all corresponding widgets are made
        visible and `fb.fil[0]['fx_sim']` is set to True.

        If `fb.fil[0]['fx_sim']` has been changed since last time, `self.needs_calc`
        is set to True and the run button is set to "changed".
        """
        if fx in {"float", "fixpoint"}:
            # Function call with argument: Set UI and fb.fil[0]['fx_sim'] accord. to `fx`
            qset_cmb_box(self.ui.cmb_sim_select, fx, data=True)
            fb.fil[0]['fx_sim'] = (fx == "fixpoint")
        elif fb.fil[0]['fx_sim']:
            qset_cmb_box(self.ui.cmb_sim_select, "fixpoint", data=True)
        else:
            qset_cmb_box(self.ui.cmb_sim_select, "float", data=True)

        # plot styles for quantized stimulus signal
        self.ui.cmb_plt_freq_stmq.setVisible(fb.fil[0]['fx_sim'])  # cmb box freq. domain
        self.ui.lbl_plt_freq_stmq.setVisible(fb.fil[0]['fx_sim'])  # label freq. domain
        self.ui.cmb_plt_time_stmq.setVisible(fb.fil[0]['fx_sim'])  # cmb box time domain
        self.ui.lbl_plt_time_stmq.setVisible(fb.fil[0]['fx_sim'])  # cmb box time domain
        self.ui.but_fx_scale.setVisible(fb.fil[0]['fx_sim'])  # fx scale int
        self.ui.but_fx_range.setVisible(fb.fil[0]['fx_sim'])  # display fx range limits

        # add / delete fixpoint entry to / from spectrogram combo box and set
        # `fx_str = "fixpoint"`` or `""``
        if fb.fil[0]['fx_sim']:
            qcmb_box_add_item(self.ui.cmb_plt_time_spgr, ["xqn", "x_q[n]", ""])
            self.fx_str = "fixpoint "
        else:
            qcmb_box_del_item(self.ui.cmb_plt_time_spgr, "x_q[n]")
            self.fx_str = ""

        if fb.fil[0]['fx_sim'] != self.fx_sim_old:
            self.ui.but_run.setIcon(QIcon(":/play.svg"))
            qstyle_widget(self.ui.but_run, "changed")
            # force recalculation of stimulus and response when switching
            # between float and fixpoint
            self.needs_calc = True

        self.fx_sim_old = fb.fil[0]['fx_sim']

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

            if fb.fil[0]['fx_sim'] and hasattr(self, "q_i"):
                # same for fixpoint simulation
                x_q_win = self.q_i.fixp(self.x[self.ui.N_start:self.ui.N_end])\
                    * win
                self.X_q = np.fft.fft(x_q_win) / self.ui.N
                # self.X_q[0] = self.X_q[0] * np.sqrt(2) # correct value at DC

        if self.y is None or len(self.y) < self.ui.N_end:
            self.Y = np.zeros(self.ui.N)  # dummy result
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

        self.scale_i = self.scale_o = 1
        self.fx_min = -1.
        self.fx_max = 1.
        if fb.fil[0]['fx_sim']:
            # fixpoint simulation enabled -> scale stimulus and response
            try:
                if self.ui.but_fx_scale.isChecked():
                    # display stimulus and response as integer values:
                    # - multiply stimulus and response by 2 ** WF
                    self.scale_i = 1 << fb.fil[0]['fxqc']['QI']['WF']
                    self.scale_o = 1 << fb.fil[0]['fxqc']['QO']['WF']
                    self.fx_min = - (1 << fb.fil[0]['fxqc']['QO']['W']-1)
                    self.fx_max = -self.fx_min - 1
                else:
                    # display values scaled as "real world (float) values"
                    self.fx_min = -(1 << fb.fil[0]['fxqc']['QO']['WI'])
                    self.fx_max = -self.fx_min - 1. / (1 << fb.fil[0]['fxqc']['QO']['WF'])

            except AttributeError as e:
                logger.error("Attribute error: {0}".format(e))
            except TypeError as e:
                logger.error(
                    "Type error: 'fxqc_dict'={0},\n{1}".format(fb.fil[0]['fxqc'], e))
            except ValueError as e:
                logger.error("Value error: {0}".format(e))

        idx = self.tab_mpl_w.currentIndex()

        if idx == 0 and self.needs_redraw[0]:
            self.draw_time(N_start=self.ui.N_start, N_end=self.ui.N_end)
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
        Update spectrogram UI when signal selection combobox has been changed
        """
        self.ui.wdg_ctrl_time_spgr.setVisible(
            qget_cmb_box(self.ui.cmb_plt_time_spgr) != 'none')

        self.draw()

    # ------------------------------------------------------------------------
    def _log_mode_time(self):
        """
        Select / deselect log. mode for time domain and update self.ui.bottom_t
        """
        if qget_cmb_box(self.ui.cmb_mode_spgr_time) in {'phase', 'angle'}:
            # must be linear if mode is 'angle' or 'phase'
            self.ui.but_log_spgr_time.setChecked(False)
            self.ui.but_log_spgr_time.setEnabled(False)
        else:
            self.ui.but_log_spgr_time.setEnabled(True)

        log = self.ui.but_log_time.isChecked() or\
            (self.ui.but_log_spgr_time.isChecked() and self.spgr)
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

        log = self.ui.but_log_freq.isChecked()
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
    def draw_data(self, plt_style: str, ax: object, x: np.ndarray, y:np.ndarray,
                  bottom: float = 0, label: str = '',
                  plt_fmt: dict = {}, mkr_fmt: dict = {}, **args):
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
            Bottom line y-coordinate for stem plot. The default is 0.
        label : str
            Plot label
        plt_fmt : dict
            Line styles (color, linewidth etc.) for plotting (default: None).
        mkr_fmt : dict
            Marker styles
        args : dict
            additional keys and values. As they might not be
            compatible with every plot style, they have to be added individually

        Returns
        -------
        handle :  A `lines.Line2D()` objects or tuple with two of them
            This provides a handle to the properties of line and marker (optionally)
            which are displayed by legend
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

        # plot markers (except for 'stem' and 'dots' where they have been plotted already)
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
        # calculate time vector from index n and T_S
        self.t = self.n * fb.fil[0]['T_S']

        # Read out combo boxes with plotting styles and remove the '*' for markers
        self.plt_time_resp = qget_cmb_box(self.ui.cmb_plt_time_resp).replace("*", "")
        self.plt_time_stim = qget_cmb_box(self.ui.cmb_plt_time_stim).replace("*", "")
        self.plt_time_stmq = qget_cmb_box(self.ui.cmb_plt_time_stmq).replace("*", "")
        self.plt_time_spgr = qget_cmb_box(self.ui.cmb_plt_time_spgr)
        self.spgr = self.plt_time_spgr != "none"

        self.plt_time_enabled = self.plt_time_resp != "none"\
            or self.plt_time_stim != "none"\
            or (self.plt_time_stmq != "none" and fb.fil[0]['fx_sim'])

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
    def draw_time(self, N_start, N_end):
        """
        (Re-)draw the time domain mplwidget
        """
        if self.y is None:  # safety net for empty responses
            for ax in self.mplwidget_t.fig.get_axes():  # remove all axes
                self.mplwidget_t.fig.delaxes(ax)
            return

        H_str = self.stim_wdg.H_str

        self._init_axes_time()
        self._log_mode_time()

        # '$h... = some impulse response, don't change
        if not H_str or H_str[1] != 'h':
            H_str = ''
            if qget_cmb_box(self.ui.cmb_plt_time_stim) != "none":
                H_str += r'$x$, '
            if qget_cmb_box(self.ui.cmb_plt_time_stmq) != "none" and fb.fil[0]['fx_sim']:
                H_str += r'$x_Q$, '
            if qget_cmb_box(self.ui.cmb_plt_time_resp) != "none":
                H_str += r'$y$'
            H_str = H_str.rstrip(', ')

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
        if fb.fil[0]['fx_sim'] and hasattr(self, 'x_q'):
            x_q = self.x_q[self.ui.N_start:N_end] * self.scale_i
            if self.ui.but_log_time.isChecked():
                x_q = np.maximum(20 * np.log10(abs(x_q)), self.ui.bottom_t)

            # logger.warning("self.scale I:{0} O:{1}".format(self.scale_i, self.scale_o))
        else:
            x_q = None

        # Create finer grid for plotting interpolated waveforms
        if self.ui.chk_plt_time_stim_interp.isChecked():
            I = 20
            # self.t_interp = np.linspace(self.t[0], self.t[-1], (len(self.t) - 1) * I + 1)
            # self.x_interp = np.interp(self.t_interp, self.t, self.x, left=None, right=None,
            #                      period=None)
            self.x_interp = sig.resample_poly(self.x, I, 1, axis=0, window=('kaiser', 5.0),
                                              padtype='line', cval=None)
            self.t_interp = np.linspace(self.n[0], self.n[-1] + 1, len(self.n) * I, endpoint=False) * fb.fil[0]['T_S']

        t = self.t[N_start:N_end]
        x = self.x[N_start:N_end] * self.scale_i
        y = self.y[N_start:N_end] * self.scale_o
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
        lbl_x_r_interp = "$x(t)$"

        # log. scale for stimulus / response time domain:
        if self.ui.but_log_time.isChecked():
            bottom_t = self.ui.bottom_t
            win = np.maximum(20 * np.log10(
                abs(self.ui.qfft_win_select.get_window(self.ui.N))), self.ui.bottom_t)
            x_r = np.maximum(20 * np.log10(abs(x_r)), self.ui.bottom_t)
            y_r = np.maximum(20 * np.log10(abs(y_r)), self.ui.bottom_t)

            if self.cmplx:
                x_i = np.maximum(20 * np.log10(abs(x_i)), self.ui.bottom_t)
                y_i = np.maximum(20 * np.log10(abs(y_i)), self.ui.bottom_t)
                H_i_str = r'$|\Im\{$' + H_str + r'$\}|$' + ' in dBV'
                H_str = r'$|\Re\{$' + H_str + r'$\}|$' + ' in dBV'
            else:
                H_str = '$|$' + H_str + '$|$ in dBV'

            fx_min = 20*np.log10(abs(self.fx_min))
            fx_max = fx_min
        else:
            bottom_t = 0
            fx_max = self.fx_max
            fx_min = self.fx_min
            if self.cmplx:
                H_i_str = r'$\Im\{$' + H_str + r'$\}$ in V'
                H_str = r'$\Re\{$' + H_str + r'$\}$ in V'
            else:
                H_str = H_str + ' in V'

        if self.ui.but_fx_range.isChecked() and fb.fil[0]['fx_sim']:
            self.ax_r.axhline(fx_max, 0, 1, color='k', linestyle='--')
            self.ax_r.axhline(fx_min, 0, 1, color='k', linestyle='--')

        h_r = []  # plot handles (real part)
        h_i = []  # plot handles (imag. part)
        l_r = []  # labels (real part)
        l_i = []  # labels (imag. part)

        # --------------- Stimulus plot --------------------------------------
        if self.plt_time_stim != "none":
            h_r.append(self.draw_data(
                self.plt_time_stim, self.ax_r, t,
                x_r, label=lbl_x_r, bottom=bottom_t,
                plt_fmt=self.fmt_plot_stim, mkr_fmt=fmt_mkr_stim))
            l_r += [lbl_x_r]

            if self.ui.chk_plt_time_stim_interp.isChecked():
                # add interpolated waveform
                h_r.append(self.draw_data(
                    "line", self.ax_r, self.t_interp,
                    self.x_interp, label=lbl_x_r_interp, bottom=bottom_t,
                    plt_fmt=self.fmt_plot_stim_interp, mkr_fmt={'marker': ''}))
                l_r += [lbl_x_r_interp]

        # -------------- Stimulus <q> plot ------------------------------------
        if x_q is not None and self.plt_time_stmq != "none":
            h_r.append(self.draw_data(
                self.plt_time_stmq, self.ax_r, t,
                x_q, label='$x_q[n]$', bottom=bottom_t,
                plt_fmt=self.fmt_plot_stmq, mkr_fmt=fmt_mkr_stmq))
            l_r += ['$x_q[n]$']
        # --------------- Response plot ----------------------------------
        if self.plt_time_resp != "none":
            h_r.append(self.draw_data(
                self.plt_time_resp, self.ax_r, t,
                y_r, label=lbl_y_r, bottom=bottom_t,
                plt_fmt=self.fmt_plot_resp, mkr_fmt=fmt_mkr_resp))
            l_r += [lbl_y_r]
        # --------------- Window plot ----------------------------------
        if self.ui.chk_win_time.isChecked():
            h_r.append(self.ax_r.plot(
                t, win, c="gray",
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
                    self.plt_time_stim, self.ax_i, t,
                    x_i, label=lbl_x_i, bottom=bottom_t,
                    plt_fmt=self.fmt_plot_stim, mkr_fmt=fmt_mkr_stim))
                l_i += [lbl_x_i]

            if self.plt_time_resp != "none":
                # --- imag. part of response -----
                h_i.append(self.draw_data(
                    self.plt_time_resp, self.ax_i, t,
                    y_i, label=lbl_y_i, bottom=bottom_t,
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
        #    self.ax_r.set_xlabel(fb.fil[0]['plt_tLabel'])
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
                s = x
                sig_lbl = 'X'
            elif self.plt_time_spgr == "xqn" and hasattr(self, "x_q"):
                s = x_q
                sig_lbl = 'X_Q'
            elif self.plt_time_spgr == "yn":
                s = y
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
            spgr_unit = r" in W / Hz"  # default unit for spectrogram
            scaling = "density"  # default scaling for spectrogram
            if self.ui.but_log_spgr_time.isChecked():
                dB_unit = "dB"
            else:
                dB_unit = ""
            if mode == "psd":
                spgr_symb = r"$S_{{{0}}}$".format(sig_lbl.lower()+sig_lbl.lower())
                dB_scale = 10  # log scale for PSD

                if self.ui.chk_byfs_spgr_time.isChecked():
                    # display result scaled by f_S
                    if self.ui.but_log_spgr_time.isChecked():
                        spgr_unit = r" in dB re W / Hz"
                    else:
                        spgr_unit = r" in W / Hz"
                    scaling = "density"
                else:
                    # display result in W / bin
                    spgr_unit = r" in {0}W".format(dB_unit)
                    scaling = "spectrum"

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

            # ------- lin / log ----------------------
            if self.ui.but_log_spgr_time.isChecked():
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

                if self.ui.but_log_spgr_time.isChecked():
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

        # if not self.ui.but_log_freq.isChecked() \
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

        if self.ui.but_log_freq.isChecked():
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
        plt_stimulus_q = self.plt_freq_stmq != "none" and fb.fil[0]['fx_sim']\
            and hasattr(self, "X_q")

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
        if self.plt_freq_enabled or self.ui.but_Hf.isChecked():
            if plt_stimulus:
                H_F_str += r'$X$, '
            if plt_stimulus_q:
                H_F_str += r'$X_Q$, '
            if plt_response:
                H_F_str += r'$Y$, '
            if self.ui.but_Hf.isChecked():
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
        # - Calculate total power P from FFT, corrected by window correlated gain
        #   bandwidth and fixpoint scaling (scale_i / scale_o)
        # - Correct scale for single-sided spectrum
        # - Scale impulse response with N_FFT to calculate frequency response if requested
            if self.ui.but_freq_norm_impz.isVisible()\
                and self.ui.but_freq_norm_impz.isEnabled()\
                    and self.ui.but_freq_norm_impz.isChecked():
                freq_resp = True  # calculate frequency response from impulse response
                scale_impz = self.ui.N * self.ui.win_dict['cgain']\
                    * self.stim_wdg.ui.scale_impz
                if self.ui.win_dict['cur_win_name'].lower() not in\
                        {'boxcar', 'rectangular'}:
                    logger.warning("Window type needs to be Boxcar (Rectangular)"
                                   " for correct scaling!")
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

                F = np.fft.fftshift(F)

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

                F = F[0:self.ui.N//2]
                F_id = F_id[0:params['N_FFT']//2]
                H_id = H_id[0:params['N_FFT']//2]

            else:  # fb.fil[0]['freqSpecsRangeType'] == 'whole'
                # display 0 ... f_S -> shift frequency axis
                F = np.fft.fftshift(F) + f_max/2.
                if not freq_resp:
                    H_id /= 2

            # -----------------------------------------------------------------
            # Calculate log FFT and power if selected, set units
            # -----------------------------------------------------------------
            if self.ui.but_log_freq.isChecked():
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

                if self.ui.but_Hf.isChecked():
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

                if self.ui.but_Hf.isChecked():
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
            show_info = self.ui.but_freq_show_info.isChecked()
            h_r = []  # plot handles (real / mag. part)
            h_i = []  # plot handles (imag. / phase part)
            l_r = []  # labels (real / mag. part)
            l_i = []  # labels (imag. / phase part)
            patch_trans = mpl_patches.Rectangle((0, 0), 1, 1, fc="w", fill=False,
                                                ec=None, lw=0)  # ec = 'blue', alpha=0.5
            lbl_empty = "        "

            # -------------------- Plot H_id ----------------------------------
            if self.ui.but_Hf.isChecked():
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
            if self.plt_freq_enabled or self.ui.but_Hf.isChecked():

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

            if self.ui.but_log_freq.isChecked():
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
        idx = self.tab_mpl_w.currentIndex()
        self.tab_mpl_w.currentWidget().redraw()
        # wdg = getattr(self, self.tab_mplwidget_list[idx])
        logger.debug("Redrawing tab {0}".format(idx))
        # wdg_cur.redraw()
        self.needs_redraw[idx] = False
#        self.mplwidget_t.redraw()
#        self.mplwidget_f.redraw()


# ------------------------------------------------------------------------------

if __name__ == "__main__":
    """ Run widget standalone with `python -m pyfda.plot_widgets.plot_impz` """
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = Plot_Impz()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
