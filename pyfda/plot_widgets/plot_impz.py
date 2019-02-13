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
from __future__ import print_function, division, unicode_literals, absolute_import
import logging
logger = logging.getLogger(__name__)

from ..compat import QWidget, QEvent, Qt, pyqtSignal, QTabWidget, QVBoxLayout

import numpy as np
import scipy.signal as sig
import matplotlib.patches as mpl_patches

import pyfda.filterbroker as fb
from pyfda.pyfda_lib import expand_lim, to_html, safe_eval
from pyfda.pyfda_qt_lib import qget_cmb_box, qset_cmb_box, qstyle_widget
from pyfda.pyfda_rc import params # FMT string for QLineEdit fields, e.g. '{:.3g}'
from pyfda.plot_widgets.mpl_widget import MplWidget, stems, no_plot
#from mpl_toolkits.mplot3d.axes3d import Axes3D
from .plot_impz_ui import PlotImpz_UI

# TODO: "Home" calls redraw for all three mpl widgets
# TODO: changing the view on some widgets redraws h[n] unncessarily
# TODO: keywords 'ms', 'alpha', 'lw' not defined for stems?
# TODO: fixpoint scaling is applied in spite of cmbbox = float
# TODO: fir fixpoint  scaling is off by 1 bit due to W_c + W_I without -1
# TODO: Increasing number of data points repeats the previous ones in fixpoint mode

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
        
        # initial settings for line edit widgets
        self.f1 = self.ui.f1
        self.f2 = self.ui.f2
        
        self.plt_freq = self.ui.plt_freq
        self.plt_time_stim = self.ui.plt_time_stim
        self.plt_time_resp = self.ui.plt_time_resp
        self.bottom = self.ui.bottom

        self.needs_draw = True   # flag whether plots need to be updated 
        self.needs_redraw = [True] * 3 # flag which plot needs to be redrawn
        self.fx_sim = False # initial setting for fixpoint simulation
        self.tool_tip = "Impulse and transient response"
        self.tab_label = "h[n]"
        self.active_tab = 0 # index for active tab

        self._construct_UI()
        
        #--------------------------------------------
        # initialize routines and settings
        self._log_mode_time()
        self.fx_select()    # initialize fixpoint or float simulation    
        self.draw() # initial calculation and drawing


    def _construct_UI(self):
        """
        Create the top level UI of the widget, consisting of matplotlib widget
        and control frame.
        """
        #----------------------------------------------------------------------
        # Define MplWidgets: Time domain plots
        #----------------------------------------------------------------------
        self.mplwidget_t = MplWidget(self)
        self.mplwidget_t.setObjectName("mplwidget_t1")
        self.mplwidget_t.layVMainMpl.addWidget(self.ui.wdg_ctrl_time)
        self.mplwidget_t.layVMainMpl.setContentsMargins(*params['wdg_margins'])
        # MplWidget for frequency domain plots
        self.mplwidget_f = MplWidget(self)
        self.mplwidget_f.setObjectName("mplwidget_f1")
        self.mplwidget_f.layVMainMpl.addWidget(self.ui.wdg_ctrl_freq)
        self.mplwidget_f.layVMainMpl.setContentsMargins(*params['wdg_margins'])
        # MplWidget for stimulus plots
        self.mplwidget_s = MplWidget(self)
        self.mplwidget_s.layVMainMpl.addWidget(self.ui.wdg_ctrl_stim)
        self.mplwidget_s.layVMainMpl.setContentsMargins(*params['wdg_margins'])

        #----------------------------------------------------------------------
        # Tabbed layout with vertical tabs
        #----------------------------------------------------------------------
        self.tabWidget = QTabWidget(self)
        self.tabWidget.addTab(self.mplwidget_t, "Time")
        self.tabWidget.addTab(self.mplwidget_f, "Frequency")
        self.tabWidget.addTab(self.mplwidget_s, "Stimuli")
        # list with tabWidgets
        self.tab_mplwidgets = ["mplwidget_t", "mplwidget_f", "mplwidget_s"]
        self.tabWidget.setTabPosition(QTabWidget.West)

        layVMain = QVBoxLayout()
        layVMain.addWidget(self.tabWidget)
        layVMain.addWidget(self.ui.wdg_ctrl_run)
        layVMain.setContentsMargins(*params['wdg_margins'])#(left, top, right, bottom)

        self.setLayout(layVMain)
        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        # --- run control ---
        self.ui.cmb_sim_select.currentIndexChanged.connect(self.fx_select)
        self.ui.but_run.clicked.connect(self.fx_run)
        self.ui.chk_fx_scale.clicked.connect(self.draw_impz_time)
        # --- time domain plotting ---
        self.ui.cmb_plt_time_resp.currentIndexChanged.connect(self.draw_impz_time)
        self.ui.chk_marker_resp.clicked.connect(self.draw_impz_time)
        self.ui.cmb_plt_time_stim.currentIndexChanged.connect(self.draw_impz_time)
        self.ui.chk_marker_stim.clicked.connect(self.draw_impz_time)
        self.ui.chk_log.clicked.connect(self._log_mode_time)
        self.ui.led_log_bottom.editingFinished.connect(self._log_mode_time)
        self.ui.chk_fx_range.clicked.connect(self.draw_impz_time)
        # --- frequency domain plotting ---
        self.ui.cmb_plt_freq.currentIndexChanged.connect(self.draw_impz_freq)
        # --- stimulus plotting ---
        self.ui.chk_stim_plot.clicked.connect(self.draw_impz_stim)
        self.ui.chk_stems_stim.clicked.connect(self.draw_impz_stim)

        # frequency widgets require special handling as they are scaled with f_s
        self.ui.ledFreq1.installEventFilter(self)
        self.ui.ledFreq2.installEventFilter(self)

        self.mplwidget_t.mplToolbar.sig_tx.connect(self.process_sig_rx) # connect to toolbar
        self.mplwidget_f.mplToolbar.sig_tx.connect(self.process_sig_rx) # connect to toolbar
        self.mplwidget_s.mplToolbar.sig_tx.connect(self.process_sig_rx) # connect to toolbar
        
        # When user has selected a different tab, trigger a draw (incl. maybe recalc) of current tab
        self.tabWidget.currentChanged.connect(self.draw) # passes number of active tab

        self.sig_rx.connect(self.ui.sig_rx)
        self.ui.sig_tx.connect(self.process_sig_rx) # connect to widgets and signals upstream

#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the navigation toolbar and input_tab_widgets
        """
        logger.debug("Processing {0} | needs_draw = {1}, visible = {2}"\
                     .format(dict_sig, self.needs_draw, self.isVisible()))
        if dict_sig['sender'] == __name__:
            logger.warning("Stopped infinite loop, {0}".format(dict_sig))
        if 'fx_sim' in dict_sig:
            try:
                if dict_sig['fx_sim'] == 'set_hdl_dict':
                    self.fx_set_hdl_dict(dict_sig) # pass hdl dict

                if dict_sig['fx_sim'] == 'get_stimulus':
                    # read hdl_dict and calculate stimulus
                    self.hdl_dict = dict_sig['hdl_dict']
                    self.calc_stimulus() # calculate selected stimulus with selected length
                    # pass stimulus in self.x back  via dict
                    self.sig_tx.emit({'sender':__name__, 'fx_sim':'set_stimulus',
                                      'fx_stimulus':self.x})
                elif dict_sig['fx_sim'] == 'set_results':
                    logger.info("Received fixpoint results.")
                    self.fx_set_results(dict_sig) # plot fx simulation results 

            except KeyError as e:
                logger.error('Key {0} missing in "hdl_dict".'.format(e))
                self.fx_sim = False

        if self.isVisible():
            if 'data_changed' in dict_sig or 'specs_changed' in dict_sig\
                or 'view_changed' in dict_sig or self.needs_draw:
                # todo: after 'data_changed' all needs to be set to True except current widget
                self.draw()

            elif 'home' in dict_sig:
                self.redraw()
                # self.tabWidget.currentWidget().redraw() # redraw method of current mplwidget, always redraws tab 0
                self.needs_redraw[self.tabWidget.currentIndex()] = False
            elif 'ui_changed' in dict_sig and dict_sig['ui_changed'] == 'resized'\
                    or self.needs_redraw[self.tabWidget.currentIndex()]:
                self.needs_redraw[:] = [True] * 3
                self.redraw() # redraw current widget

        else:
            if 'data_changed' in dict_sig or 'specs_changed' in dict_sig:
                self.needs_draw = True
            elif 'ui_changed' in dict_sig and dict_sig['ui_changed'] == 'resized':
                self.needs_redraw[:] = [True] * 3

#------------------------------------------------------------------------------
    def eventFilter(self, source, event):
        """
        Filter all events generated by the monitored widgets. Source and type
        of all events generated by monitored objects are passed to this eventFilter,
        evaluated and passed on to the next hierarchy level.

        - When a QLineEdit widget gains input focus (``QEvent.FocusIn``), display
          the stored value from filter dict with full precision
        - When a key is pressed inside the text field, set the `spec_edited` flag
          to True.
        - When a QLineEdit widget loses input focus (``QEvent.FocusOut``), store
          current value normalized to f_S with full precision (only if
          ``spec_edited == True``) and display the stored value in selected format
        """

        def _store_entry(source):
            if self.spec_edited:
                if source.objectName() == "stimFreq1":
                   self.f1 = safe_eval(source.text(), self.f1 * fb.fil[0]['f_S'],
                                            return_type='float') / fb.fil[0]['f_S']
                   source.setText(str(params['FMT'].format(self.f1 * fb.fil[0]['f_S'])))

                elif source.objectName() == "stimFreq2":
                   self.f2 = safe_eval(source.text(), self.f2 * fb.fil[0]['f_S'],
                                            return_type='float') / fb.fil[0]['f_S']
                   source.setText(str(params['FMT'].format(self.f2 * fb.fil[0]['f_S'])))

                self.spec_edited = False # reset flag
                self.draw()

#        if isinstance(source, QLineEdit): 
#        if source.objectName() in {"stimFreq1","stimFreq2"}:
        if event.type() in {QEvent.FocusIn,QEvent.KeyPress, QEvent.FocusOut}:
            if event.type() == QEvent.FocusIn:
                self.spec_edited = False
                self.load_fs()
            elif event.type() == QEvent.KeyPress:
                self.spec_edited = True # entry has been changed
                key = event.key()
                if key in {Qt.Key_Return, Qt.Key_Enter}:
                    _store_entry(source)
                elif key == Qt.Key_Escape: # revert changes
                    self.spec_edited = False
                    if source.objectName() == "stimFreq1":                    
                        source.setText(str(params['FMT'].format(self.f1 * fb.fil[0]['f_S'])))
                    elif source.objectName() == "stimFreq2":                    
                        source.setText(str(params['FMT'].format(self.f2 * fb.fil[0]['f_S'])))

            elif event.type() == QEvent.FocusOut:
                _store_entry(source)

        # Call base class method to continue normal event processing:
        return super(Plot_Impz, self).eventFilter(source, event)
       
#-------------------------------------------------------------        
    def load_fs(self):
        """
        Reload sampling frequency from filter dictionary and transform
        the displayed frequency spec input fields according to the units
        setting (i.e. f_S). Spec entries are always stored normalized w.r.t. f_S 
        in the dictionary; when f_S or the unit are changed, only the displayed values
        of the frequency entries are updated, not the dictionary!

        load_fs() is called during init and when the frequency unit or the
        sampling frequency have been changed.

        It should be called when sigSpecsChanged or sigFilterDesigned is emitted
        at another place, indicating that a reload is required.
        """

        # recalculate displayed freq spec values for (maybe) changed f_S
        if self.ui.ledFreq1.hasFocus():
            # widget has focus, show full precision
            self.ui.ledFreq1.setText(str(self.f1 * fb.fil[0]['f_S']))
        elif self.ui.ledFreq2.hasFocus():
            # widget has focus, show full precision
            self.ui.ledFreq2.setText(str(self.f2 * fb.fil[0]['f_S']))
        else:
            # widgets have no focus, round the display
            self.ui.ledFreq1.setText(
                str(params['FMT'].format(self.f1 * fb.fil[0]['f_S'])))
            self.ui.ledFreq2.setText(
                str(params['FMT'].format(self.f2 * fb.fil[0]['f_S'])))

# =============================================================================
    def fx_select(self):
        """
        Select between fixpoint and floating point simulation
        """
        self.sim_select = qget_cmb_box(self.ui.cmb_sim_select, data=False)
        self.fx_sim = (self.sim_select == 'Fixpoint')
        self.ui.but_run.setVisible(self.fx_sim)
        self.ui.chk_fx_scale.setVisible(self.fx_sim)
        self.ui.chk_fx_range.setVisible(self.fx_sim)
        self.hdl_dict = None

        if self.fx_sim:
            qstyle_widget(self.ui.but_run, "changed")
            self.fx_run()
        else:
            self.draw()

    def fx_run(self):
        """
        Run fixpoint simulation
        """        
        self.sig_tx.emit({'sender':__name__, 'fx_sim':'start'})

    def fx_set_hdl_dict(self, dict_sig):
        """
        Set quantization dict
        """
        try:
            self.hdl_dict = dict_sig['hdl_dict']
        except (KeyError, ValueError) as e:
            logger.warning(e)
            
    def fx_set_results(self, dict_sig):
        """
        Get simulation results from `dict_sig` and transfer them to plotting
        routine.
        """
        self.calc_response(dict_sig['fx_results'])
        qset_cmb_box(self.ui.cmb_sim_select, "Fixpoint", fireSignals=True)
        self.calc_fft()
        self.draw_impz()

#------------------------------------------------------------------------------
    def calc_stimulus(self):
        """
        (Re-)calculate stimulus `self.x`
        """
        self.n = np.arange(self.ui.N_end)
        self.t = self.n / fb.fil[0]['f_S']

        # calculate stimuli x[n] ==============================================
        if self.ui.stim == "Pulse":
            self.x = np.zeros(self.ui.N_end)
            self.x[0] = self.ui.A1 # create dirac impulse as input signal
            self.title_str = r'Impulse Response'
            self.H_str = r'$h[n]$' # default

        elif self.ui.stim == "Step":
            self.x = self.ui.A1 * np.ones(self.ui.N_end) # create step function
            self.title_str = r'Filter Step Response'
            self.H_str = r'$h_{\epsilon}[n]$'
            
        elif self.ui.stim == "StepErr":
            self.x = self.ui.A1 * np.ones(self.ui.N_end) # create step function
            self.title_str = r'Settling Error'
            self.H_str = r'$h_{\epsilon, \infty} - h_{\epsilon}[n]$'
            
        elif self.ui.stim == "Cos":
            self.x = self.ui.A1 * np.cos(2 * np.pi * self.n * self.f1) +\
                self.ui.A2 * np.cos(2 * np.pi * self.n * self.f2 + self.ui.phi2)
            self.title_str = r'Filter Response to Cosine Signal'
            self.H_str = r'$y[n]$'
                
        elif self.ui.stim == "Sine":
            self.x = self.ui.A1 * np.sin(2 * np.pi * self.n * self.f1 + self.ui.phi1) +\
                self.ui.A2 * np.sin(2 * np.pi * self.n * self.f2 + self.ui.phi2)
            self.title_str = r'Filter Response to Sinusoidal Signal'
            self.H_str = r'$y[n]$'
            
        elif self.ui.stim == "Rect":
            self.x = self.ui.A1 * np.sign(np.sin(2 * np.pi * self.n * self.f1))
            self.title_str = r'Filter Response to Rect. Signal'
            self.H_str = r'$y[n]$'

        elif self.ui.stim == "Saw":
            self.x = self.ui.A1 * sig.sawtooth(self.n * self.f1 * 2*np.pi)
            self.title_str = r'Filter Response to Sawtooth Signal'
            self.H_str = r'$y[n]$'

        else:
            logger.error('Unknown stimulus "{0}"'.format(self.ui.stim))
            return
        
        # Add noise to stimulus
        if self.ui.noise == "gauss":
            self.x[self.ui.N_start:] += self.ui.noi * np.random.randn(self.ui.N)
        elif self.ui.noise == "uniform":
            self.x[self.ui.N_start:] += self.ui.noi * (np.random.rand(self.ui.N)-0.5)
        # Add DC to stimulus when visible / enabled
        if self.ui.ledDC.isVisible:
            self.x += self.ui.DC
        self.needs_redraw[:] = [True] * 3
        
#------------------------------------------------------------------------------
    def calc_response(self, y_fx = None):
        """
        (Re-)calculate filter response `self.y` from either stimulus `self.x`
        (float mode) or copy fixpoint response. 
        Split response into imag. and real components `self.y_i` and `self.y_r`
        and set the flag `self.cmplx`.
        """
        if self.fx_sim: # use fixpoint simulation results instead of floating results
            if y_fx is not None:
                self.y = np.array(y_fx)
                qstyle_widget(self.ui.but_run, "normal")
            else:
                self.y = None
        else:
            # calculate response self.y_r[n] and self.y_i[n] (for complex case) =====   
            self.bb = np.asarray(fb.fil[0]['ba'][0])
            self.aa = np.asarray(fb.fil[0]['ba'][1])
            if min(len(self.aa), len(self.bb)) < 2:
                logger.error('No proper filter coefficients: len(a), len(b) < 2 !')
                return

            logger.info("Coefficient area = {0}".format(np.sum(np.abs(self.bb))))
    
            sos = np.asarray(fb.fil[0]['sos'])
            antiCausal = 'zpkA' in fb.fil[0]
            causal     = not (antiCausal)
    
            if len(sos) > 0 and causal: # has second order sections and is causal
                y = sig.sosfilt(sos, self.x)
            elif antiCausal:
                y = sig.filtfilt(self.bb, self.aa, self.x, -1, None)
            else: # no second order sections or antiCausals for current filter
                y = sig.lfilter(self.bb, self.aa, self.x)
    
            if self.ui.stim == "StepErr":
                dc = sig.freqz(self.bb, self.aa, [0]) # DC response of the system
                y = y - abs(dc[1]) # subtract DC (final) value from response
    
            self.y = np.real_if_close(y, tol = 1e3)  # tol specified in multiples of machine eps

        self.needs_redraw[0] = True
        self.needs_redraw[1] = True

        # Calculate imag. and real components from response
        self.cmplx = np.any(np.iscomplex(self.y))
        if self.cmplx:
            self.y_i = self.y.imag
            self.y_r = self.y.real
        else:
            self.y_r = self.y
            self.y_i = None

#------------------------------------------------------------------------------
    def calc_fft(self):
        """
        (Re-)calculate ffts X(f) and Y(f) of stimulus and response
        """
        # calculate FFT of stimulus / response
        if self.plt_freq in {"Stimulus", "Both"}:
            x_win = self.x[self.ui.N_start:self.ui.N_end] * self.ui.win
            self.X = np.abs(np.fft.fft(x_win)) / self.ui.N
            self.needs_redraw[1] = True

        if self.plt_freq in {"Response", "Both"}:
            y_win = self.y[self.ui.N_start:self.ui.N_end] * self.ui.win
            self.Y = np.abs(np.fft.fft(y_win)) / self.ui.N
            self.needs_redraw[1] = True
#------------------------------------------------------------------------------
    def update_view(self):
        """
        Only update the limits without recalculating the impulse response
        """
        self.draw_impz()

###############################################################################
#        PLOTTING
###############################################################################
    def draw(self):
        """
        Recalculate response and redraw it
        """
        if True: # self.needs_draw: doesn't work yet - number of data points needs to updated
            self.calc_stimulus()
            self.calc_response()
            self.needs_draw = False
        self.draw_impz()

#------------------------------------------------------------------------------
    def draw_impz(self):
        """
        (Re-)draw the figure without recalculation
        """
        if not hasattr(self, 'cmplx'): # has response been calculated yet?            logger.error("self.y {0}".format(self.y))
            self.calc_stimulus()
            self.calc_response()
            
        f_unit = fb.fil[0]['freq_specs_unit']
        if f_unit in {"f_S", "f_Ny"}:
            unit_frmt = "i" # italic
        else:
            unit_frmt = None
        self.ui.lblFreqUnit1.setText(to_html(f_unit, frmt=unit_frmt))
        self.ui.lblFreqUnit2.setText(to_html(f_unit, frmt=unit_frmt))
        self.load_fs()
        #self.init_axes()

        self.fmt_plot_resp = {'color':'red', 'linewidth':2}
        self.fmt_plot_stim = {'color':'green', 'linewidth':2, 'alpha':0.5}
        self.fmt_mkr_stim = {'color':'green', 'alpha':0.5}
        self.fmt_mkr_resp = {'color':'blue'}
        self.fmt_stem_stim = params['mpl_stimuli']
        
        idx = self.tabWidget.currentIndex()
        if idx == 0:
            self.draw_impz_time()
        elif idx == 1:
            self.draw_impz_freq()
        elif idx == 2:
            self.draw_impz_stim()
        else:
            logger.error("Index {0} out of range!".format(idx))

        
        #================ Plotting routine time domain =========================
    def _log_mode_time(self):
        """
        Select / deselect log. mode for time domain and update self.bottom
        """
        log = self.ui.chk_log.isChecked()
        self.ui.lbl_log_bottom.setVisible(log)
        self.ui.led_log_bottom.setVisible(log)
        self.ui.lbl_dB.setVisible(log)
        if log:
            self.bottom = safe_eval(self.ui.led_log_bottom.text(), self.bottom,
                                    return_type='float', sign='neg')
            self.ui.led_log_bottom.setText(str(self.bottom))
            
        #self.sig_tx.emit({'sender':__name__, 'view_changed':'log_time'})
        # TODO: draw() really needed?
        self.draw_impz()

    def _init_axes_time(self):
        """
        Clear the axes of the time domain matplotlib widgets and (re)draw the plots.
        """
        self.plt_time_stim = qget_cmb_box(self.ui.cmb_plt_time_stim, data=False).lower()
        self.plt_time_resp = qget_cmb_box(self.ui.cmb_plt_time_resp, data=False).lower()
        plt_time = self.plt_time_resp != "none" or self.plt_time_stim != "none"\
            or self.ui.chk_marker_resp.isChecked() or self.ui.chk_marker_stim.isChecked()
        
        for ax in self.mplwidget_t.fig.get_axes():
            self.mplwidget_t.fig.delaxes(ax) # clear twinned axes if present

        if plt_time:
            num_subplots = 1 + (self.cmplx and self.plt_time_resp != "none")
    
            self.mplwidget_t.fig.subplots_adjust(hspace = 0.5)
        
            self.ax_r = self.mplwidget_t.fig.add_subplot(num_subplots,1 ,1)
            self.ax_r.clear()
            self.ax_r.get_xaxis().tick_bottom() # remove axis ticks on top
            self.ax_r.get_yaxis().tick_left() # remove axis ticks right
    
            if self.cmplx and self.plt_time_resp != "none":
                self.ax_i = self.mplwidget_t.fig.add_subplot(num_subplots, 1, 2, sharex = self.ax_r)
                self.ax_i.clear()
                self.ax_i.get_xaxis().tick_bottom() # remove axis ticks on top
                self.ax_i.get_yaxis().tick_left() # remove axis ticks right
    
            if self.ACTIVE_3D: # not implemented / tested yet
                self.ax3d = self.mplwidget_t.fig.add_subplot(111, projection='3d')
    

    def draw_impz_time(self):
        """
        (Re-)draw the time domain mplwidget
        """
        if self.y is None:
            for ax in self.mplwidget_t.fig.get_axes(): # remove all axes
                self.mplwidget_t.fig.delaxes(ax)
            return

        mkfmt_i = 'd'
        
        self._init_axes_time()
        scale_i = scale_o = 1
        fx_min = -1.
        fx_max = 1.
        fx_title = ""
        if self.fx_sim: # fixpoint simulation enabled -> scale stimulus and response
            WI = WO = 1
            try:
                logger.info("hdl_dict = {0}".format(self.hdl_dict))
                WI = self.hdl_dict['QI']['W']
                WO = self.hdl_dict['QO']['W']
                fx_title = "Fixpoint "

            except AttributeError as e:
                logger.error("Attribute error: {0}".format(e))

            except TypeError as e:
                logger.error("Type error: 'hdl_dict'={0},\n{1}".format(self.hdl_dict, e))

            except ValueError as e:
                logger.error("Value error: {0}".format(e))


            if self.ui.chk_fx_scale.isChecked():
                scale_i = 1 << WI-1
                fx_min = - (1 << WO-1)
                fx_max = (1 << WO-1) - 1
            else:
                scale_o = 1. / (1 << WO-1)
                fx_min = -1
                fx_max = 1 - scale_o

            logger.info("scale I:{0} O:{1}".format(scale_i, scale_o))

        if self.ui.chk_log.isChecked(): # log. scale for stimulus / response time domain
            H_str = '$|$' + self.H_str + '$|$ in dBV'
            x = np.maximum(20 * np.log10(abs(self.x * scale_i)), self.bottom)
            y = np.maximum(20 * np.log10(abs(self.y_r * scale_o)), self.bottom)
            if self.cmplx:
                y_i = np.maximum(20 * np.log10(abs(self.y_i)), self.bottom)
                H_i_str = r'$|\Im\{$' + self.H_str + '$\}|$' + ' in dBV'
                H_str =   r'$|\Re\{$' + self.H_str + '$\}|$' + ' in dBV'
            fx_min = 20*np.log10(abs(fx_min))
            fx_max = fx_min
        else:
            self.bottom = 0
            x = self.x * scale_i
            y = self.y_r * scale_o
            if self.cmplx:
                y_i = self.y_i * scale_o
            
            if self.cmplx:           
                H_i_str = r'$\Im\{$' + self.H_str + '$\}$ in V'
                H_str = r'$\Re\{$' + self.H_str + '$\}$ in V'
            else:
                H_str = self.H_str + ' in V'

        if self.ui.chk_fx_range.isChecked() and self.fx_sim:
            self.ax_r.axhline(fx_max,0, 1, color='k', linestyle='--')
            self.ax_r.axhline(fx_min,0, 1, color='k', linestyle='--')
            
        plot_stim_dict = self.fmt_plot_stim.copy()

        if self.plt_time_stim == "line":
            plot_stim_fnc = self.ax_r.plot
        elif self.plt_time_stim == "stem":
            plot_stim_fnc = stems
            plot_stim_dict.update({'ax':self.ax_r, 'bottom':self.bottom})
        elif self.plt_time_stim == "step":
            plot_stim_fnc = self.ax_r.plot
            plot_stim_dict.update({'drawstyle':'steps-mid'})
        else:
            plot_stim_fnc = no_plot

        plot_stim_fnc(self.t[self.ui.N_start:], x[self.ui.N_start:], label='$Stim.$',
                 **plot_stim_dict)
        if self.ui.chk_marker_stim.isChecked():
            self.ax_r.scatter(self.t[self.ui.N_start:], x[self.ui.N_start:], label='$Stim.$',
                 **self.fmt_mkr_stim)

        plot_resp_dict = self.fmt_plot_resp.copy()
        if self.plt_time_resp == "line":
            plot_resp_fnc = self.ax_r.plot
        elif self.plt_time_resp == "stem":
            plot_resp_fnc = stems
            plot_resp_dict.update({'ax':self.ax_r, 'bottom':self.bottom})
        elif self.plt_time_resp == "step":
            plot_resp_fnc = self.ax_r.plot
            plot_resp_dict.update({'drawstyle':'steps-mid'})
        elif self.plt_time_resp == "marker":
            plot_resp_fnc = self.ax_r.scatter
        else:
            plot_resp_fnc = no_plot
            
        plot_resp_fnc(self.t[self.ui.N_start:], y[self.ui.N_start:], label='$y[n]$',
                 **plot_resp_dict)

        if self.ui.chk_marker_resp.isChecked():
            self.ax_r.scatter(self.t[self.ui.N_start:], y[self.ui.N_start:], label='$y[n]$',
                 **self.fmt_mkr_resp)

        if self.cmplx and self.plt_time_resp != "none":
            [ml_i, sl_i, bl_i] = self.ax_i.stem(self.t[self.ui.N_start:], y_i[self.ui.N_start:],
                bottom=self.bottom, markerfmt=mkfmt_i, label = '$y_i[n]$')
            self.ax_i.set_xlabel(fb.fil[0]['plt_tLabel'])
            # self.ax_r.get_xaxis().set_ticklabels([]) # removes both xticklabels
            # plt.setp(ax_r.get_xticklabels(), visible=False) 
            # is shorter but imports matplotlib, set property directly instead:
            [label.set_visible(False) for label in self.ax_r.get_xticklabels()]
            self.ax_r.set_ylabel(H_str + r'$\rightarrow $')
            self.ax_i.set_ylabel(H_i_str + r'$\rightarrow $')
        else:
            self.ax_r.set_xlabel(fb.fil[0]['plt_tLabel'])
            self.ax_r.set_ylabel(H_str + r'$\rightarrow $')
        
        self.ax_r.set_title(fx_title + self.title_str)
        self.ax_r.set_xlim([self.t[self.ui.N_start],self.t[self.ui.N_end-1]])
        expand_lim(self.ax_r, 0.02)

        if self.ACTIVE_3D: # not implemented / tested yet
            # plotting the stems
            for i in range(self.ui.N_start, self.ui.N_end):
              self.ax3d.plot([self.t[i], self.t[i]], [y[i], y[i]], [0, y_i[i]],
                             '-', linewidth=2, alpha=.5)

            # plotting a circle on the top of each stem
            self.ax3d.plot(self.t[self.ui.N_start:], y[self.ui.N_start:], y_i[self.ui.N_start:], 'o', markersize=8,
                           markerfacecolor='none', label='$y[n]$')

            self.ax3d.set_xlabel('x')
            self.ax3d.set_ylabel('y')
            self.ax3d.set_zlabel('z')

        self.redraw() # redraw currently active mplwidget

    #--------------------------------------------------------------------------
    def _init_axes_freq(self):
        """
        Clear the axes of the frequency domain matplotlib widgets and 
        calculate the fft
        """
        self.plt_freq = qget_cmb_box(self.ui.cmb_plt_freq, data=False)

        if self.plt_freq == "None":
            for ax in self.mplwidget_f.fig.get_axes(): # remove all axes
                self.mplwidget_f.fig.delaxes(ax) 
        else:
            if not hasattr(self, 'ax_fft'):
                self.ax_fft = self.mplwidget_f.fig.add_subplot(111)
            else:
                self.ax_fft.clear()
            self.ax_fft.get_xaxis().tick_bottom() # remove axis ticks on top
            self.ax_fft.get_yaxis().tick_left() # remove axis ticks right
            self.ax_fft.set_title("FFT of Transient Response")

            self.calc_fft()

    def draw_impz_freq(self):
        """
        (Re-)draw the frequency domain mplwidget
        """
        self._init_axes_freq()

        if self.plt_freq != "None":
            plt_response = self.plt_freq in {"Response","Both"}
            plt_stimulus = self.plt_freq in {"Stimulus","Both"}
            if plt_response and not plt_stimulus:
                XY_str = r'$|Y(\mathrm{e}^{\mathrm{j} \Omega})|$'
            elif not plt_response and plt_stimulus:
                XY_str = r'$|X(\mathrm{e}^{\mathrm{j} \Omega})|$'
            else:
                XY_str = r'$|X,Y(\mathrm{e}^{\mathrm{j} \Omega})|$'
            F = np.fft.fftfreq(self.ui.N, d = 1. / fb.fil[0]['f_S'])

            if plt_stimulus:
                X = self.X.copy()/np.sqrt(2) # enforce deep copy and convert to RMS
                self.Px = np.sum(np.square(self.X))
                if fb.fil[0]['freqSpecsRangeType'] == 'half':
                    X[1:] = 2 * X[1:] # correct for single-sided spectrum (except DC)
            if plt_response:
                Y = self.Y.copy()/np.sqrt(2) # enforce deep copy and convert to RMS
                self.Py = np.sum(np.square(self.Y))
                if fb.fil[0]['freqSpecsRangeType'] == 'half':
                    Y[1:] = 2 * Y[1:] # correct for single-sided spectrum (except DC)

            if self.ui.chkLogF.isChecked():
                unit = unit_P = "dBW"
                unit_nenbw = "dB"
                nenbw = 10 * np.log10(self.ui.nenbw)
                if plt_stimulus:
                    X = np.maximum(20 * np.log10(X), self.ui.bottom_f)
                    self.Px = 10*np.log10(self.Px)
                if plt_response:
                    Y = np.maximum(20 * np.log10(Y), self.ui.bottom_f)
                    self.Py = 10*np.log10(self.Py)
            else:
                unit = "Vrms"
                unit_P = "W"
                unit_nenbw = "bins"
                nenbw = self.ui.nenbw

            XY_str = XY_str + ' in ' + unit

            if fb.fil[0]['freqSpecsRangeType'] == 'sym':
            # shift X, Y and F by f_S/2
                if plt_response:
                    Y = np.fft.fftshift(Y)
                if plt_stimulus:
                    X = np.fft.fftshift(X)
                F = np.fft.fftshift(F)
            elif fb.fil[0]['freqSpecsRangeType'] == 'half':
                # only use the first half of X, Y and F
                if plt_response:
                    Y = Y[0:self.ui.N//2]
                if plt_stimulus:
                    X = X[0:self.ui.N//2]
                F = F[0:self.ui.N//2]
            else: # fb.fil[0]['freqSpecsRangeType'] == 'whole'
                # plot for F = 0 ... 1
                F = np.fft.fftshift(F) + fb.fil[0]['f_S']/2.

            handles = []
            labels = []
            if plt_stimulus:
                h, = self.ax_fft.plot(F, X, **self.fmt_plot_stim)
                handles.append(h)
                labels.append("$P_X$ = {0:.3g} {1}".format(self.Px, unit_P))
            if plt_response:
                h, = self.ax_fft.plot(F, Y, **self.fmt_plot_resp)
                handles.append(h)
                labels.append("$P_Y$ = {0:.3g} {1}".format(self.Py, unit_P))
                
            labels.append("$NENBW$ = {0:.4g} {1}".format(nenbw, unit_nenbw))
            labels.append("$CGAIN$  = {0:.4g}".format(self.ui.scale))
            handles.append(mpl_patches.Rectangle((0, 0), 1, 1, fc="white",ec="white", lw=0))
            self.ax_fft.legend(handles, labels, loc='best', fontsize = 'small',
                               fancybox=True, framealpha=0.5)
            
            self.ax_fft.set_xlabel(fb.fil[0]['plt_fLabel'])
            self.ax_fft.set_ylabel(XY_str)
            self.ax_fft.set_xlim(fb.fil[0]['freqSpecsRange'])

            if self.ui.chkLogF.isChecked():
                # create second axis scaled for noise power scale if it doesn't exist
                if not hasattr(self, 'ax_fft_noise'):
                    self.ax_fft_noise = self.ax_fft.twinx()
                    self.ax_fft_noise.is_twin = True
                self.ax_fft_noise.clear()

                corr = 10*np.log10(self.ui.N / self.ui.nenbw) 
                mn, mx = self.ax_fft.get_ylim()
                self.ax_fft_noise.set_ylim(mn+corr, mx+corr)
                self.ax_fft_noise.set_ylabel(r'$P_N$ in dBW')
            else:
                if hasattr(self, 'ax_fft_noise'): # remove twin axes
                    self.mplwidget_f.fig.delaxes(self.ax_fft_noise)
                    del self.ax_fft_noise
        self.redraw() # redraw currently active mplwidget

    #--------------------------------------------------------------------------      
    def _init_axes_stim(self):
        """
        clear the axes of the stimulus matplotlib widget and (re)draw the plots
        """
        if not self.ui.chk_stim_plot.isChecked():
            self.mplwidget_s.fig.clf()
        else:
            self.ax_stim = self.mplwidget_s.fig.add_subplot(111)    
            self.ax_stim.clear() # same as cla()

            self.ax_stim.get_xaxis().tick_bottom() # remove axis ticks on top
            self.ax_stim.get_yaxis().tick_left() # remove axis ticks right

    def draw_impz_stim(self):
        """
        (Re-)draw the stimulus
        """
        self._init_axes_stim()

        if self.ui.chk_stim_plot.isChecked():
            H_str = self.H_str + ' in V'
            if self.ui.chk_stems_stim.isChecked(): # stem plot
                [ms_s, ss_s, bs_s] = self.ax_stim.stem(self.t[self.ui.N_start:], self.x[self.ui.N_start:], 
                    label = 'Stim.', **self.fmt_stem_stim)
                ms_s.set_mfc(self.fmt_stem_stim['mfc'])
                ms_s.set_mec(self.fmt_stem_stim['mec'])
                ms_s.set_ms(self.fmt_stem_stim['ms'])
                ms_s.set_alpha(self.fmt_stem_stim['alpha'])
                for stem in ss_s:
                    stem.set_linewidth(self.fmt_stem_stim['lw'])
                    stem.set_color(self.fmt_stem_stim['mec'])
                    stem.set_alpha(self.fmt_stem_stim['alpha'])
                bs_s.set_color(self.fmt_stem_stim['mfc']) # same format
                bs_s.set_alpha(self.fmt_stem_stim['alpha'])  # as stem for baseline
            else: # line plot
                self.ax_stim.plot(self.t[self.ui.N_start:], self.x[self.ui.N_start:], 
                    label='Stim.', **self.fmt_plot_stim)                
            
            self.ax_stim.set_title("Stimulus")
            self.ax_stim.set_xlim([self.t[self.ui.N_start],self.t[self.ui.N_end-1]])
            expand_lim(self.ax_stim, 0.02)
            self.ax_stim.set_xlabel(fb.fil[0]['plt_tLabel'])
            self.ax_stim.set_ylabel(H_str + r'$\rightarrow $')
        else:
            self._init_axes_stim()

        self.redraw() # redraw currently active mplwidget

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
#        self.mplwidget_s.redraw()

#------------------------------------------------------------------------------

def main():
    import sys
    from ..compat import QApplication

    app = QApplication(sys.argv)
    mainw = Plot_Impz(None)
    app.setActiveWindow(mainw) 
    mainw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
    # module test using python -m pyfda.plot_widgets.plot_impz