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
import logging

import numpy as np
import scipy.signal as sig
import matplotlib.patches as mpl_patches
# import matplotlib.lines as lines
from matplotlib.ticker import AutoMinorLocator

from pyfda.libs.compat import (
    QWidget, pyqtSignal, QTabWidget, QVBoxLayout, QIcon, QSize, QSizePolicy)
from pyfda.config_file_parser import ConfigFileParser as CFP
from pyfda.filterbroker import get_fx, set_fx, fb_get, fb_set
import pyfda.libs.pyfda_fix_lib as fx
from pyfda.libs.pyfda_sig_lib import angle_zero, calc_ssb_spectrum
from pyfda.libs.pyfda_lib import safe_eval, first_item
from pyfda.libs.pyfda_qt_lib import (
    emit, qget_cmb_box, qset_cmb_box, qstyle_widget, qcmb_box_add_item,
    qcmb_box_del_item)
from pyfda.plot_widgets.mpl_widget import MplWidget, stems, scatter
from pyfda.plot_widgets.tran.plot_tran_stim import PlotTranStim
from pyfda.plot_widgets.tran.tran_io import TranIO
from pyfda.plot_widgets.plot_tran_ui import PlotTranUI
from pyfda.pyfda_rc import params  # FMT string for QLineEdit fields, e.g. '{:.3g}'

logger = logging.getLogger(__name__)

# TODO: "Home" calls redraw for botb mpl widgets
# TODO: changing the view on some widgets redraws h[n] unncessarily

classes = {'PlotTran': 'y[n] / Y(f)'}  #: Dict containing class name : display name

USE_3D_CMPLX = False  # Plot complex responses as 3D (not yet implemented)


class PlotTran(QWidget):
    """
    Construct a widget for plotting impulse and general transient responses
    """
    sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outgoing, e.g. when stimulus has been calculated

    def __init__(self, objectName='plot_impz_inst'):
        super().__init__()

        self.setObjectName(objectName)

        # arrays that need to be passed to subwidgets
        self.x = self.y = self.x_q = None

        ###### initial settings #################################################
        # ==================
        # flag whether specs have been changed and plots need to be recalculated
        self.needs_calc = True
        # same when fixpoint specs have been changed, only needed in Fixpoint mode
        self.needs_calc_fx = True
        self.needs_redraw = [True] * 2  # flags which plots need to be redrawn
        self.error = False

        fb_set('qfrmt', 'float64')  # disable fixpoint mode initially
        self.get_fx_old = get_fx()   # previous setting of fixpoint mode

        self.tool_tip = "Impulse / transient response and their spectra"
        self.tab_label = "y[n]"
        self.active_tab = 0  # index for active tab

        ###### Styles for lines and markers ######################################
        # markersize=None, markeredgewidth=None, markeredgecolor=None,
        # markerfacecolor=None, markerfacecoloralt='none', fillstyle=None,
        self.fmt_mkr_size = 8
        self.fmt_plot_resp = {'color': 'red', 'linewidth': 2, 'alpha': 0.5}
        self.fmt_mkr_resp = {'marker': 'o', 'color': 'red', 'alpha': 0.5,
                             'ms': self.fmt_mkr_size}
        self.fmt_plot_stim = {'color': 'blue', 'linewidth': 2, 'alpha': 0.5}
        self.fmt_plot_stim_interp = {'color': 'grey', 'linewidth': 2, 'alpha': 0.5}

        self.fmt_mkr_stim = {'marker': 's', 'color': 'blue', 'alpha': 0.5,
                             'ms': self.fmt_mkr_size}
        self.fmt_plot_stmq = {'color': 'darkgreen', 'linewidth': 2, 'alpha': 0.5}
        self.fmt_mkr_stmq = {'marker': 'D', 'color': 'darkgreen', 'alpha': 0.5,
                             'ms': self.fmt_mkr_size}
        # ########################################################################

        # create the UI part with buttons etc.
        self.ui = PlotTranUI()
        self.stim_wdg = PlotTranStim()
        self.tran_io_wdg = TranIO(self)

        self._construct_ui()

        # --------------------------------------------
        # initialize UI for fixpoint or float simulation
        self.update_fx_settings()

        self.impz_init()  # initial calculation of stimulus and response and drawing

    # -----------------------------------------------------------------------
    def emit(self, dict_sig: dict) -> None:
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    # -----------------------------------------------------------------------
    def _construct_ui(self) -> None:
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
        self.mplwidget_t.lay_v_main_mpl.addWidget(self.ui.wdg_ctrl_time)
        self.mplwidget_t.lay_v_main_mpl.setContentsMargins(*params['mpl_margins'])
        self.mplwidget_t.mpl_toolbar.a_en.setVisible(True)
        self.mplwidget_t.mpl_toolbar.a_he.setEnabled(True)
        self.mplwidget_t.mpl_toolbar.a_he.info = "manual/plot_tran.html"
        self.mplwidget_t.mpl_toolbar.a_ui_num_levels = 4
        self.mplwidget_t.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ---------- MplWidget for FREQUENCY domain plots ----------------------
        self.mplwidget_f = MplWidget(self)
        self.mplwidget_f.setObjectName("mplwidget_f1")
        self.mplwidget_f.lay_v_main_mpl.addWidget(self.ui.wdg_ctrl_freq)
        self.mplwidget_f.lay_v_main_mpl.setContentsMargins(*params['mpl_margins'])
        self.mplwidget_f.mpl_toolbar.a_en.setVisible(True)
        self.mplwidget_f.mpl_toolbar.a_he.setEnabled(True)
        self.mplwidget_f.mpl_toolbar.a_he.info = "manual/plot_tran.html"
        self.mplwidget_f.mpl_toolbar.a_ui_num_levels = 4
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
        # set "Stim:" label width to same width as "Plots:" label:
        self.stim_wdg.ui.lbl_title_stim.setFixedWidth(
            self.ui.lbl_title_plot_time.sizeHint().width())
        # set "File:" label (tran_io_wdg) to same width as "Plots:" label (stim_wdg):
        self.tran_io_wdg.ui.lbl_title_io_file.setFixedWidth(
            self.ui.lbl_title_plot_time.sizeHint().width())

        # This places the combo box for adding / using file data to the
        # run control toolbar:
        self.ui.frm_file_io.setLayout(self.stim_wdg.ui.lay_h_file_io)

        self.tab_stim_w = QTabWidget(self)
        self.tab_stim_w.setObjectName("tab_stim_w")
        self.tab_stim_w.setTabPosition(QTabWidget.West)

        self.tab_stim_w.addTab(self.stim_wdg, QIcon(":/graph_90.svg"), "")
        self.tab_stim_w.setTabToolTip(0, "Stimuli")

        self.tab_stim_w.addTab(self.tran_io_wdg, QIcon(":/file.svg"), "")
        self.tab_stim_w.setTabToolTip(1, "File I/O")

        self.resize_stim_tab_widget()

        # All the following do not reflect QSS settings always yields w = 30.
        # Try {font.pixelSize()} ?
        # tab_w = self.tab_stim_w.tabBar().geometry().height()
        # tab_w2 = self.tab_stim_w.tabBar().height()
        # The following works somewhat under Windwos, but crashes under Linux
        # tab_w2 = self.tab_stim_w.tabBar().tabSizeHint(0).width()
        # logger.warning(f"w={tab_w}, w2={tab_w2}")
        tab_w = int(round(25 * params['screen']['scaling']))  # TODO: hacky ...
        self.tab_stim_w.setIconSize(QSize(tab_w, tab_w))
        # ----------------------------------------------------------------------
        # ---------------- GLOBAL LAYOUT ---------------------------------------
        # ----------------------------------------------------------------------
        lay_v_main = QVBoxLayout()
        lay_v_main.addWidget(self.tab_mpl_w)
        lay_v_main.addWidget(self.tab_stim_w)
        lay_v_main.addWidget(self.ui.wdg_ctrl_run)
        lay_v_main.setContentsMargins(*params['mpl_margins'])

        self.setLayout(lay_v_main)
        self.updateGeometry()

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # connect rx global events to process_sig_rx() and to listening subwidgets
        self.sig_rx.connect(self.process_sig_rx)
        self.sig_rx.connect(self.stim_wdg.sig_rx)
        self.sig_rx.connect(self.tran_io_wdg.sig_rx)
        # connect UI and subwidgets tx events to process_sig_rx()
        self.ui.sig_tx.connect(self.process_sig_rx)
        self.stim_wdg.sig_tx.connect(self.process_sig_rx)
        self.tran_io_wdg.sig_tx.connect(self.process_sig_rx)
        self.mplwidget_t.mpl_toolbar.sig_tx.connect(self.process_sig_rx_t)
        self.mplwidget_f.mpl_toolbar.sig_tx.connect(self.process_sig_rx_f)
        # self.mplwidget.mpl_toolbar.enable_plot(state = False) # disable initially

        # When user has selected a different local tab, trigger a redraw of current tab
        self.tab_mpl_w.currentChanged.connect(self.draw)  # passes # of active tab
        # ---------------------------------------------------------------------
        # UI SIGNALS & SLOTs
        # ---------------------------------------------------------------------
        self.tab_stim_w.currentChanged.connect(self.resize_stim_tab_widget)
        # --- run control ---
        self.ui.cmb_sim_select.currentIndexChanged.connect(self.update_fx_settings)
        self.ui.but_run.clicked.connect(self.impz_init)
        self.ui.but_auto_run.clicked.connect(self.calc_auto)
        self.stim_wdg.ui.but_file_io.clicked.connect(self.set_n_to_file_len)
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
        self.ui.chk_fx_range_x.clicked.connect(self.draw)
        self.ui.chk_fx_range_y.clicked.connect(self.draw)
        self.ui.chk_win_time.clicked.connect(self.draw)
        # --- frequency domain plotting ---------------------------------------
        self.ui.cmb_plt_freq_resp.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_freq_stim.currentIndexChanged.connect(self.draw)
        self.ui.cmb_plt_freq_stmq.currentIndexChanged.connect(self.draw)
        self.ui.but_hf_id.clicked.connect(self.draw)
        self.ui.cmb_freq_display.currentIndexChanged.connect(self.draw)
        self.ui.but_log_freq.clicked.connect(self.draw)
        self.ui.led_log_bottom_freq.editingFinished.connect(self.draw)
        self.ui.but_freq_norm_impz.clicked.connect(self.draw)
        self.ui.but_freq_index_k.clicked.connect(self._update_index_k)
        self.ui.but_freq_show_info.clicked.connect(self.draw)
        # --- subwidgets

    # -----------------------------------------------------------------------
    def _update_index_k(self, arg) -> None:
        """
        Update state of index_k button in filterbroker, update frequency scaling and call `draw()`
        """
        fb_set("tab_yn", "display_index_k", self.ui.but_freq_index_k.isChecked())
        self.stim_wdg.ui.normalize_freqs()
        self.draw(arg)  # pass button state to draw()

    # -----------------------------------------------------------------------
    def toggle_stim_options(self) -> None:
        """
        Toggle visibility of stimulus options, depending on the state of the
        "Stimuli" button
        """
        self.tab_stim_w.setVisible(
            qget_cmb_box(self.ui.cmb_ui_select) in {"stim", "plot_stim"})
        self.ui.wdg_ctrl_freq.setVisible(
            qget_cmb_box(self.ui.cmb_ui_select) in {"plot", "plot_stim"})
        self.ui.wdg_ctrl_time.setVisible(
            qget_cmb_box(self.ui.cmb_ui_select) in {"plot", "plot_stim"})

    # -----------------------------------------------------------------------
    def set_ui_level(self, ui_level: int) -> None:
        """
        Sync time and frequency subwidget and set their ui display level
        """
        self.mplwidget_f.mpl_toolbar.cycle_ui_level(ui_level)
        self.mplwidget_t.mpl_toolbar.cycle_ui_level(ui_level)
        if ui_level == 0:
            self.ui.wdg_ctrl_time.setVisible(True)
            self.ui.wdg_ctrl_freq.setVisible(True)
            self.tab_stim_w.setVisible(True)
            self.ui.wdg_ctrl_run.setVisible(True)
        elif ui_level == 1:
            self.ui.wdg_ctrl_time.setVisible(False)
            self.ui.wdg_ctrl_freq.setVisible(False)
            self.tab_stim_w.setVisible(True)
            self.ui.wdg_ctrl_run.setVisible(True)
        elif ui_level == 2:
            self.ui.wdg_ctrl_time.setVisible(False)
            self.ui.wdg_ctrl_freq.setVisible(False)
            self.tab_stim_w.setVisible(False)
            self.ui.wdg_ctrl_run.setVisible(True)
        elif ui_level == 3:
            self.ui.wdg_ctrl_time.setVisible(False)
            self.ui.wdg_ctrl_freq.setVisible(False)
            self.tab_stim_w.setVisible(False)
            self.ui.wdg_ctrl_run.setVisible(False)
        else:
            logger.warning("Undefined 'ui_level = %d!", ui_level)

    # -----------------------------------------------------------------------
    def resize_stim_tab_widget(self) -> None:
        """
        Resize active tab of stimulus Tab widget to fit the height of the contained
        widget. This is triggered by:
        - initialization in `_construct_ui()`
        - changed tab in the stimulus tab widget (signal-slot)
        - an 'ui-changed' - signal (`process_signal_rx()`)
        """
        # logger.warning(f"width = {self.tab_stim_w.tabBar().width()}, "
        #                f"height = {self.tab_stim_w.tabBar().height()}")
        # logger.warning(f"w = {self.tab_mpl_w.tabBar().width()}, "
        #                f"height = {self.tab_mpl_w.tabBar().height()}")
        # tabBar height is also the width / hight of the tab icons

        min_height = self.tab_stim_w.tabBar().height()
        # logger.warning(f"min hint = {self.stim_wdg.minimumSizeHint()}, min_height = {min_height}")
        if self.tab_stim_w.currentWidget() is None:
            logger.warning("no embedded widget!")
            height = 0
        else:
            height = self.tab_stim_w.currentWidget().minimumSizeHint().height()
        self.tab_stim_w.setMaximumHeight(max(height, min_height))
        self.tab_stim_w.setMinimumHeight(max(height, min_height))

    # -----------------------------------------------------------------------
    def process_sig_rx_t(self, dict_sig: dict | None = None) -> None:
        """
        Special treatment for signals coming from TIME plot navigation toolbar
        """
        # cycle ui level
        if 'mpl_toolbar' in dict_sig and dict_sig['mpl_toolbar'] == 'ui_level':
            # read out ui level directly
            self.set_ui_level(self.mplwidget_t.mpl_toolbar.a_ui_level)
        # redraw plot when it has become enabled
        elif dict_sig['mpl_toolbar'] == 'enable_plot'\
                and self.mplwidget_t.mpl_toolbar.plot_enabled:
            self.draw()
        else:
            self.process_sig_rx(dict_sig)

    # -----------------------------------------------------------------------
    def process_sig_rx_f(self, dict_sig: dict | None = None) -> None:
        """
        Special treatment for signals coming from FREQ plot navigation toolbar
        """
        # cycle ui level
        if 'mpl_toolbar' in dict_sig and dict_sig['mpl_toolbar'] == 'ui_level':
            # read out ui level directly
            self.set_ui_level(self.mplwidget_f.mpl_toolbar.a_ui_level)
        # redraw plot when it has become enabled
        elif dict_sig['mpl_toolbar'] == 'enable_plot'\
                and self.mplwidget_f.mpl_toolbar.plot_enabled:
            self.draw()
        else:
            self.process_sig_rx(dict_sig)

    # -----------------------------------------------------------------------
    def process_sig_rx(self, dict_sig: dict | None = None) -> None:
        # Process signals coming from
        # - the navigation toolbars (time and freq.)
        # - local widgets (impz_ui) and
        # - plot_tab_widgets() (global signals)

        logger.debug(
            "SIG_RX - needs_calc: %s | vis: %s\n%s\t ",
            self.needs_calc, self.isVisible(), first_item(dict_sig))

        if dict_sig['id'] == id(self):
            # logger.warning(f'Stopped infinite loop: "{first_item(dict_sig)}"')
            return

        if 'fx_sim' in dict_sig:
            # --------------- specs changed ------------
            if dict_sig['fx_sim'] == 'specs_changed':
                # Fixpoint widget specs have been updated.
                # If fixpoint mode is active:
                # - set `self.needs_calc_fx = True`.
                # - reset error flag
                # - force recalculation (`self.needs_calc = True`)
                # - update run button style to 'changed'
                # - if widget is visible and autorun is selected,
                #     initialize fixpoint widget and
                #     start simulation via `calc_auto` -> `self.impz_init()`
                self.needs_calc = True  # force recalculation
                self.error = False      # reset error flag
                # set cmb box for fixpoint / float simulation and update ui:
                self.update_fx_settings()
                if get_fx():
                    self.needs_calc_fx = True   # fx sim needs recalculation

                qstyle_widget(self.ui.but_run, 'changed')
                self.ui.but_run.setIcon(QIcon(":/play.svg"))
                if self.isVisible():
                    self.calc_auto() # call impz_init() if autorun is selected

            # --------------- 'start_fx_response_calculation' ---------
            elif dict_sig['fx_sim'] == 'start_fx_response_calculation':
                # The fixpoint widget has been initialized and starts the fx simulation
                # via `self.impz()` if the widget is visible. The handle to the fixpoint
                # simulation method has been passed via `dict_sig['fxfilter_func']`
                self.fxfilter = dict_sig['fxfilter_func']
                if self.isVisible():
                    self.impz()
                return

            # --------------- ERROR in fixpoint simulation ------------
            elif dict_sig['fx_sim'] == 'error':
                self.needs_calc = True
                self.error = True
                self.ui.but_run.setIcon(QIcon(":/play.svg"))
                qstyle_widget(self.ui.but_run, "error")
                if 'err_msg' in dict_sig:
                    logger.error(dict_sig['err_msg'])
                return

            # --------------- MISSING VALUE for 'fx_sim' key ----------
            elif not dict_sig['fx_sim']:
                logger.error("Missing value for key 'fx_sim'.")

            else:
                logger.error("Unknown value '%s' for 'fx_sim' key\n\treceived from '%s'",
                              dict_sig['fx_sim'], dict_sig['class'])

        # --- widget is visible, handle all signals except 'fx_sim' -----------
        elif self.isVisible():
            if 'data_changed' in dict_sig or self.needs_calc\
                    or (get_fx() and self.needs_calc_fx):
                # a file has been loaded or unloaded:
                if 'data_changed' in dict_sig and dict_sig['data_changed'] == 'file_io':
                    # make file data available to stimulus widget and modify number of
                    # data points to be used:
                    self.file_io()

                # update number of data points in impz_ui and FFT window
                # needed when e.g. FIR filter order has been changed, requiring
                # a different number of data points for simulation. Don't emit a signal.
                self.ui.update_n(emit_signal=False)
                self.needs_calc = True
                # Highlight "RUN" button
                self.ui.but_run.setIcon(QIcon(":/play.svg"))
                qstyle_widget(self.ui.but_run, 'changed')
                self.impz_init()

            elif 'mpl_toolbar' in dict_sig:
                if dict_sig['mpl_toolbar'] == 'home':
                    self.zoom_home()
                    self.needs_redraw[self.tab_mpl_w.currentIndex()] = False

            elif 'ui_local_changed' in dict_sig:
                if dict_sig['ui_local_changed'] == 'csv':
                    # CSV options window has been closed, propagate the event
                    self.emit({'ui_global_changed': 'csv'})
                else:
                    # treat all other local UI events here
                    self.needs_calc = True
                    # make file data available to stimulus widget:
                    self.file_io()
                    self.impz_init()

            elif 'view_changed' in dict_sig or any(self.needs_redraw):
                self.draw()  # redraw a.o. changed axes scaling

        else:  # invisible
            if 'data_changed' in dict_sig:
                self.needs_calc = True
            elif 'view_changed' in dict_sig and dict_sig['view_changed'] == 'f_S':
                self.needs_redraw = [True] * 2
                # update frequency related widgets (visible or not)
            elif 'ui_local_changed' in dict_sig:
                # self.needs_redraw = [True] * 2
                self.needs_calc = True

    # -----------------------------------------------------------------------
    def set_n_to_file_len(self) -> None:
        """
        Check status of file_io widget:
        - if no file is loaded, do nothing. This shouldn't happen (check to be sure ...)
        - else set n_end = len(file_data) in the UI
        """
        if not hasattr(self.tran_io_wdg, 'N') or self.tran_io_wdg.N == 0:
            self.ui.frm_file_io.setEnabled(False)
            logger.warning("No data loaded, you shouldn't see this message!")
        # File is loaded, copy file length to n_end
        else:
            # copy number of data points to N, disable N_auto, enable lineedit for N
            self.ui.update_n(n_end = self.tran_io_wdg.N)
            self.ui.but_n_auto.setChecked(False)
            self.ui.led_N_points.setEnabled(True)

    # -----------------------------------------------------------------------
    def file_io(self) -> None:
        """
        Check status of file_io widget:

        - if no file is loaded, do nothing and return 0, disable `cmb_file_io` and
          the option to transfer the number of samples to N
        - else map the file data to `self.stim_wdg.x_file` to make it accessible
           from the stimulus widget. If `cmb_file_io == `use`, disable the widget to
           modify stimuli
        """
        # No file has been loaded or number of data points is zero
        #    -> disable file_io combobox:
        if self.tran_io_wdg.ui.but_load.property("state") != "ok" or\
            not self.tran_io_wdg.ui.but_load.isEnabled() or\
                not hasattr(self.tran_io_wdg, 'x') or self.tran_io_wdg.x is None:
            self.ui.frm_file_io.setEnabled(False)
            self.stim_wdg.ui.wdg_stim.setEnabled(True)

        # File is loaded, enable file_io combobox, disable stimulus and formula
        # widget if file_io is set to "use" (in contrast to "add")
        else:
            self.ui.frm_file_io.setEnabled(True)
            self.stim_wdg.x_file = self.tran_io_wdg.x_file
            self.stim_wdg.ui.wdg_stim.setEnabled(
                qget_cmb_box(self.stim_wdg.ui.cmb_file_io) != "use")

    # =======================================================================
    # Simulation: Calculate stimulus, response and draw them
    # =======================================================================
    def calc_auto(self) -> None:
        """
        Triggered when checkbox "Autorun" is clicked or specs have been edited,
        requiring a recalculation.

        When Autorun has been pushed (`but_auto_run.isChecked() == True`) and
        calculation is required, automatically run `impz_init()`.
        """
        if self.ui.but_auto_run.isChecked() and self.needs_calc:
            self.impz_init()

    # -----------------------------------------------------------------------
    def impz_init(self, arg: bool | None = None) -> None:
        """
        Initialize transient simulation.

        Parameters
        ----------
        arg: bool or None

        Returns
        --------
        None

        Triggered by:

            - `_construct_ui()` during initialization
            - Pressing "Run" button, passing button state as a bool
            - `self.ui.cmb_sim_select` when changing between fixpoint and float mode
            - `self.calc_auto()` when activating "Autorun"
            - Autorun (when something relevant in the UI has been updated)
            - signal ``{'fx_sim' : 'specs_changed'}``

        The following tasks are performed:

            - Enable energy scaling for impulse stimuli when requirements are met
            - check for and enable fixpoint settings
            - resize stimulus widget
            - when triggered by `but_run` or when `Auto`== pressed and
              `self.needs_calc == True`, continue with calculating stimulus / response
            - When in fixpoint mode, initialize quantized stimulus `x_q` and input
              quantizer and emit `{'fx_sim':'init'}`
        """

        # logger.info("impz_init")
        self.resize_stim_tab_widget()
        # allow scaling the frequency response from pure impulse (no DC, noise or file)
        # button is only visible for impulse-shaped stimuli
        self.ui.but_freq_norm_impz.setEnabled(
            (self.stim_wdg.ui.noi == 0 or
             self.stim_wdg.ui.cmb_stim_noise.currentText() == 'None')
            and self.stim_wdg.ui.dc == 0
            and self.stim_wdg.ui.cmb_stim == "impulse"
            and self.tran_io_wdg.ui.but_load.property("state") != "ok"
            )
        self.ui.but_freq_norm_impz.setVisible(self.stim_wdg.ui.cmb_stim == "impulse")

        self.error = False
        self.needs_redraw = [True] * 2

        # check for fixpoint setting `get_fx()` and update UI if needed
        self.update_fx_settings()

        if isinstance(arg, bool):
            self.needs_calc = True  # but_run has been pressed -> force run
        elif not self.ui.but_auto_run.isChecked():  # "Auto" is not active, return
            return

        if self.needs_calc:
            # Test whether stimulus or filter coefficients are complex and set flag
            #  correspondingly, additionally calculate up to 10 samples to test for
            # complex values:
            self.n_first = 0  # initialize frame index
            x_test = np.zeros(10, dtype=complex)
            # TODO: For stimuli that become complex only after the 10th sample,
            #       the test fails
            # TODO: np.iscomplexobj() returns true for an array with dtype complex
            #       although each item is real.
            self.stim_wdg.calc_stimulus_frame(x_test, n_frame = min(10, self.ui.n_end))

            # convert from np.bool to bool to avoid deprecation warning concerning
            # 'np.bool_' scalars to be interpreted as an index.
            self.cmplx = bool(\
                (self.stim_wdg.ui.led_dc.isVisible() and isinstance(self.stim_wdg.ui.dc, complex))\
                or (self.stim_wdg.ui.led_amp_1.isVisible()
                    and isinstance(self.stim_wdg.ui.a1, complex))\
                or (self.stim_wdg.ui.led_amp_2.isVisible()
                    and isinstance(self.stim_wdg.ui.a2, complex))\
                or np.any(np.iscomplex(np.asarray(fb_get('ba'))))\
                or (self.tran_io_wdg.ui.but_load.property("state") == 'ok'
                    and np.iscomplexobj(self.tran_io_wdg.x))\
                or np.any(np.iscomplex(x_test)))

            self.ui.lbl_stim_cmplx_warn.setVisible(self.cmplx)

            # set title and axis string
            self.stim_wdg.init_labels_stim()
            self.title_str = self.stim_wdg.title_str

            self.n = np.arange(self.ui.n_end, dtype=float)

            # initialize arrays for stimulus and response
            if self.cmplx:
                self.x = np.zeros(self.ui.n_end, dtype=complex)
                self.y = np.zeros(self.ui.n_end, dtype=complex)
            else:
                self.x = np.zeros(self.ui.n_end, dtype=float)
                self.y = np.zeros(self.ui.n_end, dtype=float)

            # initialize progress bar
            self.ui.prg_wdg.setMaximum(self.ui.n_end)
            self.ui.prg_wdg.setValue(0)
            self.ui.but_run.setIcon(QIcon(":/stop.svg"))
            qstyle_widget(self.ui.but_run, "running")

            self.t_start = time.process_time()  # store starting time

            if get_fx():
                # - update plot title string
                # - setup input quantizer self.q_i
                # - emit {'fx_sim': 'init'} to listening widgets (input_fixpoint_specs)
                self.title_str = r'$Fixpoint$ ' + self.title_str
                 # initialize array for quantized stimulus
                self.x_q = np.empty_like(self.x, dtype=np.float64)
                if np.any(np.iscomplex(x_test)):
                    logger.warning(
                        "Complex stimulus: Only its real part is used for the fixpoint filter!")
                # setup and initialize input quantizer
                self.q_i = fx.Fixed(fb_get('fxq', 'QI'))
                # always use integer decimal format for input quantizer
                # self.q_i.set_qdict({'fx_base': 'dec'})

                # initialize FX filter and get a handle for `fxfilter()` function
                self.emit({'fx_sim': 'init'})
                return  # process_sig_rx() directly calls impz() in next step

            # Initialize filter memory with zeros, for either cascaded structure (sos)
            # or direct form
            self.sos = np.asarray(fb_get('sos'))
            if len(self.sos) > 0:  # has second order sections
                self.zi = np.zeros((self.sos.shape[0], 2))
            else:
                self.bb = np.asarray(fb_get('ba', 0))
                self.aa = np.asarray(fb_get('ba', 1))
                if min(len(self.aa), len(self.bb)) < 2:
                    logger.error(
                        'No proper filter coefficients: len(a), len(b) < 2 !')
                    return
                self.zi = np.zeros(max(len(self.aa), len(self.bb)) - 1)
            # calculate float impulse response:
            self.impz()

    # -----------------------------------------------------------------------
    def impz(self) -> None:
        """
        Calculate floating point / fixpoint response and redraw it

        Triggered by:

        - `self.impz_init()` (floating point)
        -  Fixpoint widget, requesting "start_fx_response_calculation"
            via `process_rx_signal()` (fixpoint filter)
        """
        while self.n_first < self.ui.n_end:
            # logger.info("impz(): Calculating frame "
            #             f"{int(np.ceil(self.n_first / self.ui.n_frame)) + 1} of "
            #             f"{int(np.ceil(self.ui.n_end / self.ui.n_frame))}")
            # The last frame could be shorter than self.ui.n_frame:
            len_frame = min(self.ui.n_frame, self.ui.n_end - self.n_first)
            # Define slicing expression for the current frame
            frame = slice(self.n_first, self.n_first + len_frame)

            # ------------------------------------------------------------------
            # ---- calculate stimuli for current frame inplace -----------------
            # ------------------------------------------------------------------
            # self.x[frame] = self.stim_wdg.calc_stimulus_frame(
            self.stim_wdg.calc_stimulus_frame(
                self.x, n_first=self.n_first, n_frame=len_frame, n_end=self.ui.n_end)

            # ------------------------------------------------------------------
            # ---- calculate fixpoint or floating point response for current frame
            # ------------------------------------------------------------------
            if get_fx():  # fixpoint filter
                # Quantize stimulus:
                self.x_q[frame] = self.q_i.fixp(self.x[frame].real,
                                                out_frmt=fb_get('qfrmt'))
                # --------------------------------------------------------------
                # ---- Get fixpoint response for current frame -----------------
                # --------------------------------------------------------------
                try:
                    self.y[frame] = np.asarray(self.fxfilter(self.x_q[frame]))
                    # logger.warning(f"y_frame = {pprint_log(self.y[frame])}")

                except ValueError as e:
                    if self.fxfilter(self.x_q[frame]) is None:
                        logger.error("Fixpoint simulation returned empty results!")
                    else:
                        logger.error("Simulator error %s", e)
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
            self.n_first += self.ui.n_frame
            self.ui.prg_wdg.setValue(self.n_first)

        # -------------------------------------------------------------
        # ----------------------- finish ------------------------------
        # -------------------------------------------------------------
        self.impz_finish()

    # -----------------------------------------------------------------------
    def impz_finish(self) -> None:
        """
        Do some housekeeping, resetting and drawing when `self.impz()`
        has finished:

        - Calculate step error if selected
        - Check for complex stimulus or response
        - Calculate simulation time
        - Draw the signals
        - Reset Run Icon to normal state, reset `needs_calc` flag
        - Update File IO save combo boxes

        """
        # step error calculation: calculate system DC response and subtract it
        # from the response
        if self.stim_wdg.ui.stim == "step" and self.stim_wdg.ui.but_step_err.isChecked():
            if len(self.sos) > 0:  # has second order sections
                dc = sig.sosfreqz(self.sos, [0])  # yields (w(0), H(0))
            else:
                dc = sig.freqz(self.bb, self.aa, [0])
            self.y[max(self.ui.n_start, self.stim_wdg.t1_idx):] = \
                self.y[max(self.ui.n_start, self.stim_wdg.t1_idx):] - abs(dc[1])

        self.ui.prg_wdg.setValue(self.ui.n_end)  # 100% reached
        self.t_resp = time.process_time()

        self.draw()
        # self.needs_redraw[self.tab_mpl_w.currentIndex()] = False
        self.needs_calc = False
        self.needs_calc_fx = False
        logger.info('Calc / plot (%5.4g / %5.4g ms) transient %sresponse',
                    (self.t_resp - self.t_start) * 1000,
                    (time.process_time() - self.t_resp) * 1000,
                    self.fx_str)

        self.ui.but_run.setIcon(QIcon(":/play.svg"))
        qstyle_widget(self.ui.but_run, "normal")
        self.ui.but_run.setIcon(QIcon(":/play.svg"))
        qstyle_widget(self.ui.but_run, "normal")
        # update TranIO ui, depending on complex and fixpoint status
        self.tran_io_wdg.ui.update_ui(cmplx=self.cmplx, fx=get_fx())

        if get_fx():
            self.emit({'fx_sim': 'finish'})

    # -----------------------------------------------------------------------
    def update_fx_settings(self, arg: int | None = None) -> None:
        """
        `arg` can have the following types, triggered by:

        - `None`: from `__init__()`, `impz_init()` or `process_sig_rx()` when
            {dict_sig['fx_sim'] == 'specs_changed'} was received. Read the state of
            `get_fx()` and update combobox correspondingly
        - int 0 or 1 from `self.ui.cmb_sim_select` when index was changed
            (signal-slot-connection), update `set_fx()` correspondingly,
            fire signal {'fx_sim': 'specs_changed'} and start simulation
        - str 'fixpoint' or 'float': from a direct call (not used currently),
            update ui and combobox `self.ui.cmb_sim_select` correspondingly

        When fixpoint simulation is selected, all corresponding widgets are made
        visible and `get_fx()` becomes True.

        If `get_fx()` has changed since last time, `self.needs_calc`
        is set to `True` and the run button is set to 'changed'.
        """

        # Direct call with no argument, set combobox according to `get_fx()``
        if arg is None:
            if get_fx():
                qset_cmb_box(self.ui.cmb_sim_select, 'fixpoint', data=True)
            else:
                qset_cmb_box(self.ui.cmb_sim_select, 'float', data=True)

        # Combobox modified, `set_fx()` according to combobox and start sim
        elif isinstance(arg, int):
            # restore last fixpoint / float mode
            set_fx(qget_cmb_box(self.ui.cmb_sim_select) == 'fixpoint')
            self.emit({'fx_sim': 'specs_changed'})
            self.needs_calc = True
            self.calc_auto()  # run simulation if autostart has been selected

        # Direct call with argument: Set UI and `set_fx()` accord. to `arg`
        # elif arg in {'float', 'fixpoint'}:
        #     qset_cmb_box(self.ui.cmb_sim_select, arg, data=True)
        #     set_fx(arg == "fixpoint")
        else:
            logger.error("Unknown argument '%s'!", arg)
            return

        _is_fx = get_fx()
        # enable fixpoint plot widgets only in fixpoint mode
        self.ui.cmb_plt_freq_stmq.setVisible(_is_fx)  # cmb box freq. domain
        self.ui.lbl_plt_freq_stmq.setVisible(_is_fx)  # label freq. domain
        self.ui.cmb_plt_time_stmq.setVisible(_is_fx)  # cmb box time domain
        self.ui.lbl_plt_time_stmq.setVisible(_is_fx)  # cmb box time domain
        self.ui.lbl_fx_range.setVisible(_is_fx)  # display fx range limits
        self.ui.chk_fx_range_x.setVisible(_is_fx)  # display fx range limits
        self.ui.chk_fx_range_y.setVisible(_is_fx)  # display fx range limits

        # add / delete fixpoint entry to / from spectrogram combo box and set
        # `fx_str = "fixpoint"`` or `""``
        if _is_fx:
            qcmb_box_add_item(self.ui.cmb_plt_time_spgr, ["xqn", "x_q[n]", ""])
            self.fx_str = "fixpoint "
        else:
            qcmb_box_del_item(self.ui.cmb_plt_time_spgr, "x_q[n]")
            self.fx_str = ""

        if _is_fx != self.get_fx_old:
            self.ui.but_run.setIcon(QIcon(":/play.svg"))
            qstyle_widget(self.ui.but_run, 'changed')
            # force recalculation of stimulus and response when switching
            # between float and fixpoint
            self.needs_calc = True

        self.get_fx_old = get_fx()

    # -----------------------------------------------------------------------
    def calc_fft(self):
        """
        (Re-)calculate FFTs of stimulus `self.x_fft`, quantized stimulus
        `self.x_q_fft` and response `self.y_fft` using the window function
        from `self.ui.all_wins_dict['win']`.
        """
        # calculate FFT of stimulus / response
        N = self.ui.N
        win = self.ui.qfft_win_select.calc_window(N) / self.ui.all_wins_dict['cgain']
        if self.x is None:
            self.x_fft = np.zeros(N)  # dummy result
            logger.warning("Stimulus is 'None', FFT cannot be calculated.")
        elif len(self.x) < self.ui.n_end:
            self.x_fft = np.zeros(N)  # dummy result
            logger.warning("Length of stimulus is %d < N = %d, FFT cannot be calculated.",
                           len(self.x), self.ui.n_end)
        else:
            # multiply the  time signal with window function
            x_win = self.x[self.ui.n_start:self.ui.n_end] * win
            # calculate absolute value and scale by N_FFT
            self.x_fft = np.fft.fft(x_win) / self.ui.N
            # self.x_fft[0] = self.x_fft[0] * np.sqrt(2) # correct value at DC

            if get_fx() and hasattr(self, "q_i"):
                # same for fixpoint simulation
                x_q_win = self.q_i.fixp(self.x[self.ui.n_start:self.ui.n_end])\
                    * win
                self.x_q_fft = np.fft.fft(x_q_win) / self.ui.N
                # self.x_q_fft[0] = self.x_q_fft[0] * np.sqrt(2) # correct value at DC

        if self.y is None or len(self.y) < self.ui.n_end:
            self.y_fft = np.zeros(self.ui.N)  # dummy result
            if self.y is None:
                logger.warning("Transient response is 'None', FFT cannot be calculated.")
            else:
                logger.warning(
                    "Length of transient response is %d < N = %d, FFT cannot be "
                    "calculated.", len(self.y), self.ui.n_end)
        else:
            y_win = self.y[self.ui.n_start:self.ui.n_end] * win
            self.y_fft = np.fft.fft(y_win) / self.ui.N
            # self.y_fft[0] = self.y_fft[0] * np.sqrt(2) # correct value at DC

        # if self.ui.chk_win_freq.isChecked():
        #    self.win_fft = np.abs(np.fft.fft(win)) / self.ui.N

        self.needs_redraw[1] = True   # redraw of frequency widget needed

    #########################################################################
    #        PLOTTING
    #########################################################################

    def draw(self, arg: bool | int = None) -> None:
        """
        (Re-)draw the figure without recalculation. When triggered by a signal-
        slot connection from a button, combobox etc., arg is a boolean or an
        integer representing the state of the widget. In this case,
        `needs_redraw` is set to True.
        """
        if arg is not None:
            self.needs_redraw = [True] * 2

        if not hasattr(self, 'cmplx'):  # has response been calculated yet?
            logger.error("Response should have been calculated by now!")
            return

        self.scale_i = self.scale_iq = self.scale_o = 1
        self.fx_min_x = self.fx_min_y = -1.
        self.fx_max_x = self.fx_max_y = 1.
        if get_fx():  # fixpoint simulation enabled -> scale stimulus and response
            try:
                if fb_get('qfrmt') == 'qint':
                    # display stimulus and response as integer values
                    # in the range +/- 2 ** (WI + WF)
                    self.scale_i = 1 << fb_get('fxq', 'QI', 'WF')
                    self.scale_iq = 1
                    self.scale_o = 1 << fb_get('fxq', 'QO', 'WF')

                    self.fx_min_x = - (1 << (fb_get('fxq', 'QI', 'WI')
                                     + fb_get('fxq', 'QI', 'WF')))
                    self.fx_max_x = -self.fx_min_x - 1
                    self.fx_min_y = - (1 << (fb_get('fxq', 'QO', 'WI')
                                     + fb_get('fxq', 'QO', 'WF')))
                    self.fx_max_y = -self.fx_min_y - 1
                elif fb_get('qfrmt') == 'qfrac':
                    # display values scaled as "real world (float) values"
                    self.scale_i = self.scale_iq = self.scale_o = 1
                    self.fx_min_x = -(1 << fb_get('fxq', 'QI', 'WI'))
                    self.fx_max_x = -self.fx_min_x\
                        - 1. / (1 << fb_get('fxq', 'QI', 'WF'))
                    self.fx_min_y = -(1 << fb_get('fxq', 'QO', 'WI'))
                    self.fx_max_y = -self.fx_min_y -\
                        1. / (1 << fb_get('fxq', 'QO', 'WF'))
                else:
                    logger.error("Undefined qfrmt = '%s'!", fb_get('qfrmt'))

            except AttributeError as e:
                logger.error("Attribute error: %s", e)
            except TypeError as e:
                logger.error("Type error: 'fxqc_dict'=%s,\n\t%s", fb_get('fxq'), e)
            except ValueError as e:
                logger.error("Value error: %s", e)

        idx = self.tab_mpl_w.currentIndex()

        if idx == 0 and self.needs_redraw[0]\
                and self.mplwidget_t.mpl_toolbar.plot_enabled:
            self.draw_time(n_start=self.ui.n_start, n_end=self.ui.n_end)
        elif idx == 1 and self.needs_redraw[1]\
                and self.mplwidget_f.mpl_toolbar.plot_enabled:
            self.draw_freq()

    # ----------------------------------------------------------------------
    def _spgr_ui2params(self) -> None:
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

# --------------------------------------------------------------------------
    def _spgr_cmb(self) -> None:
        """
        Update spectrogram UI when signal selection combobox has been changed
        """
        self.ui.wdg_ctrl_time_spgr.setVisible(
            qget_cmb_box(self.ui.cmb_plt_time_spgr) != 'none')

        self.draw()

    # ----------------------------------------------------------------------
    def _log_mode_time(self) -> None:
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

    # -----------------------------------------------------------------------
    def _log_mode_freq(self) -> None:
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

    # -----------------------------------------------------------------------
    def draw_data(self, plt_style: str, ax: object, x: np.ndarray, y:np.ndarray,
                  bottom: float = 0., label: str = '',
                  plt_fmt: dict | None = None, mkr_fmt: dict | None = None) -> object:
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
        if plt_fmt is None:
            plt_fmt = {}
        if mkr_fmt is None:
            mkr_fmt = {}

        # plot lines
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
            handle_mkr = scatter(x, y, ax=ax, mkr_fmt=mkr_fmt, label=label)
            # join handles to plot them on top of each other in the legend
            handle = (handle, handle_mkr)
        return handle

    # ================ Plotting routine time domain =========================
    def _init_axes_time(self) -> None:
        """
        Clear and initialize the axes of the time domain matplotlib widgets
        """
        # calculate time vector from index n and T_S
        self.t = self.n * fb_get('T_S')

        # Read out combo boxes with plotting styles and remove the '*' for markers
        self.plt_time_resp = qget_cmb_box(self.ui.cmb_plt_time_resp).replace("*", "")
        self.plt_time_stim = qget_cmb_box(self.ui.cmb_plt_time_stim).replace("*", "")
        self.plt_time_stmq = qget_cmb_box(self.ui.cmb_plt_time_stmq).replace("*", "")
        self.plt_time_spgr = qget_cmb_box(self.ui.cmb_plt_time_spgr)
        self.spgr = self.plt_time_spgr != "none"

        self.plt_time_enabled = self.plt_time_resp != "none"\
            or self.plt_time_stim != "none" or (self.plt_time_stmq != "none" and get_fx())

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

        for ax in self.axes_time:
            ax.xaxis.tick_bottom()  # remove axis ticks on top
            ax.yaxis.tick_left()  # remove axis ticks right
            ax.xaxis.set_minor_locator(AutoMinorLocator())  # enable minor ticks
            ax.yaxis.set_minor_locator(AutoMinorLocator())

    # ------------------------------------------------------------------------
    def draw_time(self, n_start: int = 0, n_end: int = 0) -> None:
        """
        (Re-)draw the time domain mplwidget
        """
        if self.y is None:  # safety net for empty responses
            for ax in self.mplwidget_t.fig.get_axes():  # remove all axes
                self.mplwidget_t.fig.delaxes(ax)
            return
        if n_end == 0:
            n_end = self.ui.n_end

        h_str = self.stim_wdg.h_str
        h_i_str = 'undefined'  # this should always be overwritten

        self._init_axes_time()
        self._log_mode_time()

        # '$h... = some impulse response, don't change
        if not h_str or h_str[1] != 'h':
            h_str = ''
            if qget_cmb_box(self.ui.cmb_plt_time_stim) != "none":
                h_str += r'$x$, '
            if qget_cmb_box(self.ui.cmb_plt_time_stmq) != "none" and get_fx():
                h_str += r'$x_Q$, '
            if qget_cmb_box(self.ui.cmb_plt_time_resp) != "none":
                h_str += r'$y$'
            h_str = h_str.rstrip(', ')

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

        # fixpoint simulation enabled -> assign frame to x_q
        if get_fx() and hasattr(self, 'x_q'):
            x_q = self.x_q[self.ui.n_start:n_end]
            if self.ui.but_log_time.isChecked():
                x_q = np.maximum(20 * np.log10(abs(x_q)), self.ui.bottom_t)
        else:
            x_q = None

        # Create finer grid for plotting interpolated waveforms
        if self.ui.chk_plt_time_stim_interp.isChecked():
            I_x = 20
            # self.t_interp = np.linspace(self.t[0], self.t[-1], (len(self.t) - 1) * I_x + 1)
            # self.x_interp = np.interp(self.t_interp, self.t, self.x, left=None, right=None,
            #                      period=None)
            self.x_interp = sig.resample_poly(
                self.x, I_x, 1, axis=0, window=('kaiser', 5.0),
                padtype='line', cval=None)[n_start * I_x: n_end * I_x]
            self.t_interp = np.linspace(
                self.n[0], self.n[-1] + 1, len(self.n) * I_x,
                endpoint=False)[n_start * I_x: n_end * I_x] * fb_get('T_S')


        t = self.t[n_start:n_end]
        # obtain same scaling for x as for quantized signals:
        x = self.x[n_start:n_end] * self.scale_i
        y = self.y[n_start:n_end]

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

            x_r = np.maximum(20 * np.log10(abs(x_r)), self.ui.bottom_t)
            y_r = np.maximum(20 * np.log10(abs(y_r)), self.ui.bottom_t)

            if self.cmplx:
                x_i = np.maximum(20 * np.log10(abs(x_i)), self.ui.bottom_t)
                y_i = np.maximum(20 * np.log10(abs(y_i)), self.ui.bottom_t)
                h_i_str = r'$|\Im\{$' + h_str + r'$\}|$' + ' in dBV'
                h_str = r'$|\Re\{$' + h_str + r'$\}|$' + ' in dBV'
            else:
                h_str = '$|$' + h_str + '$|$ in dBV'

            fx_min_x = fx_max_x = 20*np.log10(abs(self.fx_min_x))
            fx_min_y = fx_max_y = 20*np.log10(abs(self.fx_min_y))
        else:
            bottom_t = 0
            fx_max_x = self.fx_max_x
            fx_min_x = self.fx_min_x
            fx_max_y = self.fx_max_y
            fx_min_y = self.fx_min_y
            if self.cmplx:
                h_i_str = r'$\Im\{$' + h_str + r'$\}$ in V'
                h_str = r'$\Re\{$' + h_str + r'$\}$ in V'
            else:
                h_str = h_str + ' in V'

        if self.ui.chk_fx_range_x.isChecked() and get_fx():
            self.ax_r.axhline(fx_max_x, 0, 1, linestyle='--')
            self.ax_r.axhline(fx_min_x, 0, 1, linestyle='--')
        if self.ui.chk_fx_range_y.isChecked() and get_fx():
            self.ax_r.axhline(fx_max_y, 0, 1, linestyle='-.')
            self.ax_r.axhline(fx_min_y, 0, 1, linestyle='-.')

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
            if self.ui.but_log_time.isChecked():
                win = np.maximum(
                    20 * np.log10(abs(self.ui.qfft_win_select.calc_window(self.ui.N))),
                    self.ui.bottom_t)
            else:
                win = self.ui.qfft_win_select.calc_window(self.ui.N)
            h_r.append(self.ax_r.plot(
                t, win, c="gray",
                label=fb_get('tran_freq_win', 'disp_name'))[0])
            l_r += [fb_get('tran_freq_win', 'disp_name')]
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
            # self.ax_r.set_ylabel(h_str + r'$\rightarrow $') # common x-axis

            self.ax_i.set_ylabel(h_i_str + r'$\rightarrow $')
            self.ax_i.legend(h_i, l_i, loc='best', fontsize='small', fancybox=True,
                             framealpha=0.7)

        self.ax_r.set_ylabel(h_str + r'$\rightarrow $')

        # --------------- Spectrogram -----------------------------------------
        if self.spgr:
            if 2 * self.ui.time_nfft_spgr - self.ui.time_ovlp_spgr > self.ui.N:
                logger.warning(
                    "Only one segment is calculated since 2 NFFT - N_OVLP = %d > N = %d",
                    2 * self.ui.time_nfft_spgr - self.ui.time_ovlp_spgr, self.ui.N)
            if self.ui.time_nfft_spgr > self.ui.N:
                logger.warning(
                    "NFFT per segment = %d is larger than number N of data points %d, "
                    "setting NFFT = N.", self.ui.time_nfft_spgr, self.ui.N)
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
            spgr_args = r"$({0}, {1})$".format(fb_get('plt_tLabel')[1],
                                               fb_get('plt_fLabel')[1])

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
                spgr_symb = fr"$S_{{{sig_lbl.lower()+sig_lbl.lower()}}}$"
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
                    spgr_unit = f" in {dB_unit}W"
                    scaling = "spectrum"

            elif mode in {"magnitude", "complex"}:
                # "complex" cannot be plotted directly
                spgr_pre = r"|"
                spgr_symb = f"${sig_lbl}$"
                spgr_unit = fr"| in {dB_unit}V"

            elif mode in {"angle", "phase"}:
                spgr_unit = r" in rad"
                spgr_symb = f"${sig_lbl}$"
                spgr_pre = r"$\angle$"

            else:
                logger.warning("Unknown spectrogram mode '%s', falling back to 'psd'", mode)
                mode = "psd"

# =============================================================================
            win = self.ui.qfft_win_select.calc_window(self.ui.time_nfft_spgr)

            f, t, Sxx = sig.spectrogram(
                s, fb_get('f_S'), window=win,  # ('tukey', 0.25),
                nperseg=self.ui.time_nfft_spgr, noverlap=self.ui.time_ovlp_spgr,
                nfft=None, return_onesided=fb_get('freqSpecsRangeType') == 'half',
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

            self.ax_s.set_ylabel(fb_get('plt_fLabel'))

        # --------------- 3D Complex  -----------------------------------------
        if USE_3D_CMPLX:  # not implemented / tested yet: complex data as 3D plot
            # plotting the stems
            for i in range(self.ui.n_start, self.ui.n_end):
                self.ax3d.plot([self.t[i], self.t[i]], [y_r[i], y_r[i]], [0, y_i[i]],
                               '-', linewidth=2, alpha=.5)

            # plotting a circle on the top of each stem
            self.ax3d.plot(
                self.t[self.ui.n_start:], y_r[self.ui.n_start:], y_i[self.ui.n_start:],
                'o', markersize=8, markerfacecolor='none', label='$y[n]$')

            self.ax3d.set_xlabel('x')
            self.ax3d.set_ylabel('y')
            self.ax3d.set_zlabel('z')

        # --------------- Title and common labels ---------------------------
        self.axes_time[-1].set_xlabel(fb_get('plt_tLabel'))
        self.axes_time[0].set_title(self.title_str)
        self.ax_r.set_xlim([self.t[self.ui.n_start], self.t[self.ui.n_end-1]])
        # expand_lim(self.ax_r, 0.02)

        self.redraw()  # redraw currently active mplwidget

        self.needs_redraw[0] = False

    # ========================================================================
    # Frequency Plots
    # ========================================================================
    def _init_axes_freq(self) -> None:
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
    def draw_freq(self) -> None:
        """
        (Re-)draw the frequency domain mplwidget
        """
        self._init_axes_freq()
        self._log_mode_freq()

        nenbw = self.ui.all_wins_dict['nenbw']
        cgain = self.ui.all_wins_dict['cgain']

        plt_response = self.plt_freq_resp != "none"
        plt_stimulus = self.plt_freq_stim != "none"
        plt_stimulus_q = self.plt_freq_stmq != "none" and get_fx()\
            and hasattr(self, "x_q_fft")

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

        h_f_str = ""
        e_jomega_str = r"$(\mathrm{e}^{\mathrm{j} \Omega})$"
        if self.plt_freq_enabled or self.ui.but_hf_id.isChecked():
            if plt_stimulus:
                h_f_str += r'$X$, '
            if plt_stimulus_q:
                h_f_str += r'$X_Q$, '
            if plt_response:
                h_f_str += r'$Y$, '
            if self.ui.but_hf_id.isChecked():
                h_f_str += r'$H_{id}$, '
            h_f_str = h_f_str.rstrip(', ') + e_jomega_str

            f_range = fb_get('freqSpecsRange')

            if self.ui.but_freq_index_k.isChecked():
                #
                # '<i>k</i>' specifies frequencies w.r.t. " + to_html("f_S", frmt = 'i') +
                # but plots graphs over the frequency index <i>k</i>.</span>",
                #
                # k is checked: specify frequencies as indices of the FFT, f_k = k * f_S / N_FFT
                # Elsewhere (non-transient tabs), k = CFP.conf_settings['N_FFT'] is used for the
                # calculation of the FFT, it is also used for f_id / h_id here.
                # In the transient tab, the frequency axes must be scaled according to the number of
                # frequency points self.ui.N
                f_range = [frq * self.ui.N / fb_get('f_max') for frq in f_range]
                f_max = self.ui.N
            else:
                f_max = fb_get('f_max')

            # freqz-based ideal frequency response:
            f_id, h_id = sig.freqz(fb_get('ba', 0), fb_get('ba', 1),
                                   worN=CFP.conf_settings['N_FFT'], whole=True, fs=f_max)

            # frequency vector for FFT-based frequency plots:
            f = np.fft.fftfreq(self.ui.N, d=1. / f_max)

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
                scale_impz = self.ui.N * self.ui.all_wins_dict['cgain']\
                    * self.stim_wdg.ui.scale_impz
                if fb_get('tran_freq_win', 'id') not in\
                        {'boxcar', 'rectangular'}:
                    logger.warning("Use a Boxcar (Rectangular) window for a correctly scaled\n"
                                   "\tFFT of an impulse instead of a %s window!",
                                   fb_get('tran_freq_win', 'disp_name'))
            else:
                freq_resp = False
                scale_impz = 1.

            # scale with window NENBW for correct power calculation
            p_scale = scale_impz / nenbw
            onesided = fb_get('freqSpecsRangeType') == 'half'
            if plt_stimulus:
                if onesided and self.cmplx and not freq_resp:
                    logger.warning(
                        "You are displaying a single-sided spectrum. For complex-valued time signals, "
                        "you should display both sides (0 ... f_S or -f_S/2 ... f_S/2).")
                # scale display of stimulus: `self.x` is unscaled, hence x_fft needs
                # to be multiplied by self.scale_i
                p_x = np.sum(np.square(np.abs(self.x_fft))) * p_scale
                if onesided and not freq_resp:
                    x_fft_disp = calc_ssb_spectrum(self.x_fft, mag=self.cmplx) * scale_impz
                else:
                    x_fft_disp = self.x_fft * scale_impz

            if plt_stimulus_q:
                p_x_q = np.sum(np.square(np.abs(self.x_q_fft))) * p_scale
                if onesided and not freq_resp:
                    x_q_fft_disp = calc_ssb_spectrum(
                        self.x_q_fft, mag=self.cmplx) / self.scale_iq * scale_impz
                else:
                    x_q_fft_disp = self.x_q_fft / self.scale_iq * scale_impz

            if plt_response:
                p_y = np.sum(np.square(np.abs(self.y_fft / self.scale_o))) * p_scale
                if onesided and not freq_resp:
                    y_fft_disp = calc_ssb_spectrum(
                        self.y_fft, mag=self.cmplx) / self.scale_o * scale_impz
                else:
                    y_fft_disp = self.y_fft / self.scale_o * scale_impz

            # ----------------------------------------------------------------
            # Scale and shift frequency range
            # ----------------------------------------------------------------
            if fb_get('freqSpecsRangeType') == 'sym':
                # display -f_S/2 ... f_S/2 ->  shift x_fft_disp, y_fft_disp and f using fftshift()
                if plt_response:
                    y_fft_disp = np.fft.fftshift(y_fft_disp)

                if plt_stimulus:
                    x_fft_disp = np.fft.fftshift(x_fft_disp)

                if plt_stimulus_q:
                    x_q_fft_disp = np.fft.fftshift(x_q_fft_disp)

                f = np.fft.fftshift(f)

                # shift h_id and f_id by f_S/2
                f_id -= f_max/2
                h_id = np.fft.fftshift(h_id)
                if not freq_resp:
                    h_id /= 2

            elif onesided:
                # display 0 ... f_S/2 -> only use the first half of x_fft_disp, y_fft_disp and f
                if plt_response:
                    y_fft_disp = y_fft_disp[0:self.ui.N//2]
                if plt_stimulus:
                    x_fft_disp = x_fft_disp[0:self.ui.N//2]
                if plt_stimulus_q:
                    x_q_fft_disp = x_q_fft_disp[0:self.ui.N//2]

                f = f[0:self.ui.N//2]
                f_id = f_id[0:CFP.conf_settings['N_FFT']//2]
                h_id = h_id[0:CFP.conf_settings['N_FFT']//2]

            else:  # fb_get('freqSpecsRangeType') == 'whole'
                # display 0 ... f_S -> shift frequency axis
                f = np.fft.fftshift(f) + f_max/2.
                if not freq_resp:
                    h_id /= 2

            # -----------------------------------------------------------------
            # Calculate log FFT and power if selected, set units
            # -----------------------------------------------------------------
            if self.ui.but_log_freq.isChecked():
                unit = " in dBV"
                unit_p = "dBW"
                h_f_pre = "|"
                h_f_post = "|"

                nenbw = 10 * np.log10(nenbw)
                cgain = 20 * np.log10(cgain)

                if plt_stimulus:
                    p_x = 10*np.log10(p_x)
                    if self.en_re_im_f:
                        x_r = np.maximum(20 * np.log10(np.abs(x_fft_disp.real)), self.ui.bottom_f)
                        x_i = np.maximum(20 * np.log10(np.abs(x_fft_disp.imag)), self.ui.bottom_f)
                    else:
                        x_r = np.maximum(20 * np.log10(np.abs(x_fft_disp)), self.ui.bottom_f)
                        if self.en_mag_phi_f:
                            x_i = angle_zero(x_fft_disp)

                if plt_stimulus_q:
                    p_x_q = 10*np.log10(p_x_q)
                    if self.en_re_im_f:
                        X_q_r = np.maximum(20 * np.log10(np.abs(x_q_fft_disp.real)),
                                           self.ui.bottom_f)
                        X_q_i = np.maximum(20 * np.log10(np.abs(x_q_fft_disp.imag)),
                                           self.ui.bottom_f)
                    else:
                        X_q_r = np.maximum(20 * np.log10(np.abs(x_q_fft_disp)), self.ui.bottom_f)
                        if self.en_mag_phi_f:
                            X_q_i = angle_zero(x_q_fft_disp)

                if plt_response:
                    p_y = 10*np.log10(p_y)
                    if self.en_re_im_f:
                        y_r = np.maximum(20 * np.log10(np.abs(y_fft_disp.real)), self.ui.bottom_f)
                        y_i = np.maximum(20 * np.log10(np.abs(y_fft_disp.imag)), self.ui.bottom_f)
                    else:
                        y_r = np.maximum(20 * np.log10(np.abs(y_fft_disp)), self.ui.bottom_f)
                        if self.en_mag_phi_f:
                            y_i = angle_zero(y_fft_disp)

                if self.ui.but_hf_id.isChecked():
                    if self.en_re_im_f:
                        h_id_r = np.maximum(20 * np.log10(np.abs(h_id.real)),
                                            self.ui.bottom_f)
                        h_id_i = np.maximum(20 * np.log10(np.abs(h_id.imag)),
                                            self.ui.bottom_f)
                    else:
                        h_id_r = np.maximum(20 * np.log10(np.abs(h_id)), self.ui.bottom_f)
                        if self.en_mag_phi_f:
                            h_id_i = angle_zero(h_id)

            else:  # non log
                h_f_pre = ""
                h_f_post = ""
                if plt_stimulus:
                    if self.en_re_im_f:
                        x_r = x_fft_disp.real
                        x_i = x_fft_disp.imag
                    else:
                        x_r = np.abs(x_fft_disp)
                        if self.en_mag_phi_f:
                            x_i = angle_zero(x_fft_disp)

                if plt_stimulus_q:
                    if self.en_re_im_f:
                        X_q_r = x_q_fft_disp.real
                        X_q_i = x_q_fft_disp.imag
                    else:
                        X_q_r = np.abs(x_q_fft_disp)
                        if self.en_mag_phi_f:
                            X_q_i = angle_zero(x_q_fft_disp)

                if plt_response:
                    if self.en_re_im_f:
                        y_r = y_fft_disp.real
                        y_i = y_fft_disp.imag
                    else:
                        y_r = np.abs(y_fft_disp)
                        if self.en_mag_phi_f:
                            y_i = angle_zero(y_fft_disp)

                if self.ui.but_hf_id.isChecked():
                    if self.en_re_im_f:
                        h_id_r = h_id.real
                        h_id_i = h_id.imag
                    else:
                        h_id_r = np.abs(h_id)
                        if self.en_mag_phi_f:
                            h_id_i = angle_zero(h_id)

                unit = " in V"
                unit_p = "W"

            if self.en_re_im_f:
                h_fi_str = h_f_pre + r'$\Im\{$' + h_f_str + r'$\}$' + h_f_post\
                    + unit + r" $\rightarrow$"
                h_fr_str = r'$\Re\{$' + h_f_str + r'$\}$'
            elif self.en_mag_phi_f:
                h_fi_str = r'$\angle($' + h_f_str + r'$)$' + " in rad "\
                    + r" $\rightarrow$"
                h_fr_str = "|" + h_f_str + "|"
            else:
                h_f_pre = "|"
                h_fr_str = h_f_str
                h_fi_str = 'undefined'
                h_f_post = "|"

            h_fr_str = h_f_pre + h_fr_str + h_f_post + unit + r" $\rightarrow$"

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

            # -------------------- Plot h_id ----------------------------------
            if self.ui.but_hf_id.isChecked():
                label_re = "$|H_{id}$" + e_jomega_str + "|"
                if self.en_re_im_f:
                    label_re = "$H_{id,r}$" + e_jomega_str
                    label_im = "$H_{id,i}$" + e_jomega_str
                    h_i.append(self.ax_f2.plot(f_id, h_id_i, c="gray", label=label_im)[0])
                    l_i += [label_im]
                elif self.en_mag_phi_f:
                    label_im = r"$\angle H_{id}$" + e_jomega_str
                    h_i.append(self.ax_f2.plot(f_id, h_id_i, c="gray", label=label_im)[0])
                h_r.append(self.ax_f1.plot(f_id, h_id_r, c="gray", label=label_re)[0])
                if show_info:
                    l_r += [lbl_empty, label_re, lbl_empty]
                    h_r += [patch_trans, patch_trans]
                else:
                    l_r += [label_re]

            # -------------------- Plot X -------------------------------------
            if plt_stimulus:
                label_re = "|$X$" + e_jomega_str + "|"
                if self.en_re_im_f:
                    label_re = "$X_r$" + e_jomega_str
                    label_im = "$X_i$" + e_jomega_str
                    h_i.append(self.draw_data(
                        self.plt_freq_stim, self.ax_f2, f, x_i, label=label_im,
                        bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_stim,
                        mkr_fmt=fmt_mkr_stim))
                    l_i.append(label_im)
                elif self.en_mag_phi_f:
                    label_im = r"$\angle X$" + e_jomega_str
                    h_i.append(self.draw_data(
                        self.plt_freq_stim, self.ax_f2, f, x_i, label=label_im,
                        plt_fmt=self.fmt_plot_stim, mkr_fmt=fmt_mkr_stim))
                    l_i.append(label_im)

                h_r.append(
                    self.draw_data(self.plt_freq_stim, self.ax_f1, f, x_r, label=label_re,
                                   bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_stim,
                                   mkr_fmt=fmt_mkr_stim))
                if show_info:
                    l_r.extend([lbl_empty, label_re, f"$P_X$ = {p_x:.3g} {unit_p}"])
                    h_r.extend([patch_trans, patch_trans])
                else:
                    l_r.append(label_re)

            # -------------------- Plot X_q -----------------------------------
            if plt_stimulus_q:
                label_re = "$|X_Q$" + e_jomega_str + "|"
                if self.en_re_im_f:
                    label_re = "$X_{Q,r}$" + e_jomega_str
                    label_im = "$X_{Q,i}$" + e_jomega_str
                    h_i.append(self.draw_data(
                        self.plt_freq_stmq, self.ax_f2, f, X_q_i, label=label_im,
                        bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_stmq,
                        mkr_fmt=fmt_mkr_stmq))
                    l_i.append(label_im)
                elif self.en_mag_phi_f:
                    label_im = r"$\angle X_Q$" + e_jomega_str
                    h_i.append(self.draw_data(
                        self.plt_freq_stmq, self.ax_f2, f, X_q_i, label=label_im,
                        plt_fmt=self.fmt_plot_stmq, mkr_fmt=fmt_mkr_stmq))
                    l_i.append(label_im)

                h_r.append(self.draw_data(
                    self.plt_freq_stmq, self.ax_f1, f, X_q_r, label=label_re,
                    bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_stmq,
                    mkr_fmt=fmt_mkr_stmq))
                if show_info:
                    l_r.extend([lbl_empty, label_re, f"$P_{{Q}}$ = {p_x_q:.3g} {unit_p}"])
                    h_r.extend([patch_trans, patch_trans])
                else:
                    l_r.append(label_re)

            # -------------------- Plot Y -------------------------------------
            if plt_response:
                label_re = "$|Y$" + e_jomega_str + "|"
                if self.en_re_im_f:
                    label_re = "$Y_r$" + e_jomega_str
                    label_im = "$Y_i$" + e_jomega_str
                    h_i.append(self.draw_data(
                        self.plt_freq_resp, self.ax_f2, f, y_i, label=label_im,
                        bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_resp,
                        mkr_fmt=fmt_mkr_resp))
                    l_i.append(label_im)
                elif self.en_mag_phi_f:
                    label_im = r"$\angle Y$" + e_jomega_str
                    h_i.append(self.draw_data(
                        self.plt_freq_resp, self.ax_f2, f, y_i, label=label_im,
                        plt_fmt=self.fmt_plot_resp, mkr_fmt=fmt_mkr_resp))
                    l_i.append(label_im)

                h_r.append(self.draw_data(
                    self.plt_freq_resp, self.ax_f1, f, y_r, label=label_re,
                    bottom=self.ui.bottom_f, plt_fmt=self.fmt_plot_resp,
                    mkr_fmt=fmt_mkr_resp))
                if show_info:
                    l_r.extend([lbl_empty, label_re, f"$P_Y$ = {p_y:.3g} {unit_p}"])
                    h_r.extend([patch_trans, patch_trans])
                else:
                    l_r.append(label_re)

            # --------------- LEGEND (real part) ----------------------------------
            # The legend will fill the first column, then the next from top to bottom etc.
            if self.plt_freq_enabled or self.ui.but_hf_id.isChecked():

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
                self.ax_f2.set_ylabel(h_fi_str)

            if self.ui.but_freq_index_k.isChecked():
                self.axes_f[-1].set_xlabel(r'$k \; \rightarrow$')
            else:
                self.axes_f[-1].set_xlabel(fb_get('plt_fLabel'))
            self.ax_f1.set_ylabel(h_fr_str)
            # self.ax_f1.set_xlim(fb_get('freqSpecsRange'))
            self.ax_f1.set_xlim(f_range)
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
    def redraw(self) -> None:
        """
        Redraw the currently visible canvas (but not the plot!) when e.g. the canvas
        size has changed
        """
        idx = self.tab_mpl_w.currentIndex()
        self.tab_mpl_w.currentWidget().redraw()
        logger.debug("Redrawing tab %d", idx)
        self.needs_redraw[idx] = False
#        self.mplwidget_t.redraw()

     # -------------------------------------------------------------------------
    def zoom_home(self) -> None:
        """
        Zoom to home settings
        """
        idx = self.tab_mpl_w.currentIndex()
        if idx == 0:  # time plot widget
            self.draw_time()
        else:
            self.draw_freq()

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    # Run widget standalone with `python -m pyfda.plot_widgets.plot_tran`
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda.pyfda_rc import QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS.QSS_RC)
    mainw = PlotTran()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
