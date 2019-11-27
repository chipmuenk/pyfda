# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Library with classes and functions for file and text IO
"""
import logging
logger = logging.getLogger(__name__)

import numpy as np
from numpy.fft import fft, fftshift, fftfreq
import scipy.signal.windows as win
import matplotlib.patches as mpl_patches

from pyfda.pyfda_lib import safe_eval, to_html
from pyfda.pyfda_qt_lib import qwindow_stay_on_top
from pyfda.pyfda_rc import params
from pyfda.plot_widgets.mpl_widget import MplWidget

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals

from pyfda.compat import (QMainWindow, Qt, QFrame, pyqtSignal,
                     QCheckBox, QLabel, QLineEdit, QHBoxLayout)
#------------------------------------------------------------------------------
class Plot_FFT_win(QMainWindow):
    """
    Create a pop-up widget for displaying time and frequency view of an FFT 
    window.
    """
    # incoming
    sig_rx = pyqtSignal(object)
    # outgoing
    sig_tx = pyqtSignal(object)

    def __init__(self, parent, win_dict="win_spectral_analysis"):
        super(Plot_FFT_win, self).__init__(parent)
        
        self.needs_calc = True
        self.needs_draw = True  

        self.bottom_f = -80 # min. value for dB display
        self.bottom_t = -60
        self.N = 128 # initial number of data points
        
        self.pad = 8 # amount of zero padding
        
        self.win_dict = fb.fil[0][win_dict]
        
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle('pyFDA Window Viewer')
        self._construct_UI()

        qwindow_stay_on_top(self, True)

#------------------------------------------------------------------------------
    def closeEvent(self, event):
        """
        Catch closeEvent (user has tried to close the window) and send a 
        signal to parent where window closing is registered before actually
        closing the window.
        """
        self.sig_tx.emit({'sender':__name__, 'closeEvent':''})
        event.accept()

#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the navigation toolbar and from sig_rx
        """
        logger.debug("Processing {0} | visible = {1}"\
                     .format(dict_sig, self.isVisible()))
        if self.isVisible():
            if 'data_changed' in dict_sig or 'home' in dict_sig or self.needs_calc:
                self.draw()
                self.needs_calc = False
                self.needs_draw = False               
            elif 'view_changed' in dict_sig or self.needs_draw:
                self.update_view()
                self.needs_draw = False                
            elif ('ui_changed' in dict_sig and dict_sig['ui_changed'] == 'resized')\
                or self.needs_redraw:
                self.redraw()
        else:
            if 'data_changed' in dict_sig:
                self.needs_calc = True
            elif 'view_changed' in dict_sig:
                self.needs_draw = True 
            elif 'ui_changed' in dict_sig and dict_sig['ui_changed'] == 'resized':
                self.needs_redraw = True

    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - Matplotlib widget with NavigationToolbar
        - Frame with control elements
        """
        self.chk_auto_N = QCheckBox(self)
        self.chk_auto_N.setChecked(False)
        self.chk_auto_N.setToolTip("Use number of points from calling routine.")
        
        self.lbl_auto_N = QLabel("Auto " + to_html("N", frmt='i'))
        
        self.led_N = QLineEdit(self)
        self.led_N.setText(str(self.N))
        self.led_N.setMaximumWidth(70)
        self.led_N.setToolTip("<span>Number of window data points.</span>")
        
        self.chk_log_t = QCheckBox("Log", self)
        self.chk_log_t.setChecked(False)
        self.chk_log_t.setToolTip("Display in dB")
        
        self.led_log_bottom_t = QLineEdit(self)
        self.led_log_bottom_t.setText(str(self.bottom_t))
        self.led_log_bottom_t.setMaximumWidth(50)
        self.led_log_bottom_t.setEnabled(self.chk_log_t.isChecked())
        self.led_log_bottom_t.setToolTip("<span>Minimum display value for log. scale.</span>")
        
        self.lbl_log_bottom_t = QLabel("dB", self)
        self.lbl_log_bottom_t.setEnabled(self.chk_log_t.isChecked())

        self.chk_norm_f = QCheckBox("Norm", self)
        self.chk_norm_f.setChecked(True)
        self.chk_norm_f.setToolTip("Normalize window spectrum for a maximum of 1.")
        
        self.chk_half_f = QCheckBox("Half", self)
        self.chk_half_f.setChecked(True)
        self.chk_half_f.setToolTip("Display window spectrum in the range 0 ... 0.5 f_S.")

        self.chk_log_f = QCheckBox("Log", self)
        self.chk_log_f.setChecked(True)
        self.chk_log_f.setToolTip("Display in dB")

        self.led_log_bottom_f = QLineEdit(self)
        self.led_log_bottom_f.setText(str(self.bottom_f))
        self.led_log_bottom_f.setMaximumWidth(50)
        self.led_log_bottom_f.setEnabled(self.chk_log_f.isChecked())
        self.led_log_bottom_f.setToolTip("<span>Minimum display value for log. scale.</span>")

        self.lbl_log_bottom_f = QLabel("dB", self)
        self.lbl_log_bottom_f.setEnabled(self.chk_log_f.isChecked())

        layHControls = QHBoxLayout()
        layHControls.addWidget(self.chk_auto_N)
        layHControls.addWidget(self.lbl_auto_N)
        layHControls.addWidget(self.led_N)  
        layHControls.addStretch(1)        
        layHControls.addWidget(self.chk_log_t)
        layHControls.addWidget(self.led_log_bottom_t)
        layHControls.addWidget(self.lbl_log_bottom_t)
        layHControls.addStretch(10) 
        layHControls.addWidget(self.chk_norm_f)
        layHControls.addStretch(1)
        layHControls.addWidget(self.chk_half_f)
        layHControls.addStretch(1)
        layHControls.addWidget(self.chk_log_f)
        layHControls.addWidget(self.led_log_bottom_f)
        layHControls.addWidget(self.lbl_log_bottom_f)

        #----------------------------------------------------------------------
        #               ### frmControls ###
        #
        # This widget encompasses all control subwidgets
        #----------------------------------------------------------------------
        self.frmControls = QFrame(self)
        self.frmControls.setObjectName("frmControls")
        self.frmControls.setLayout(layHControls)

        #----------------------------------------------------------------------
        #               ### mplwidget ###
        #
        # main widget: Layout layVMainMpl (VBox) is defined with MplWidget,
        #              additional widgets can be added (like self.frmControls)
        #              The widget encompasses all other widgets.
        #----------------------------------------------------------------------
        self.mplwidget = MplWidget(self)
        self.mplwidget.layVMainMpl.addWidget(self.frmControls)
        self.mplwidget.layVMainMpl.setContentsMargins(*params['wdg_margins'])
        
        self.setCentralWidget(self.mplwidget)
        self.ax = self.mplwidget.fig.subplots(nrows=1, ncols=2)
        self.ax_t = self.ax[0]
        self.ax_f = self.ax[1]

        self.draw() # initial drawing

        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.chk_log_f.clicked.connect(self.update_view)
        self.chk_log_t.clicked.connect(self.update_view)
        self.led_log_bottom_t.editingFinished.connect(self.update_bottom)
        self.led_log_bottom_f.editingFinished.connect(self.update_bottom)

        self.chk_auto_N.clicked.connect(self.draw)
        self.led_N.editingFinished.connect(self.draw)
        
        self.chk_norm_f.clicked.connect(self.draw)
        self.chk_half_f.clicked.connect(self.update_view)

        self.mplwidget.mplToolbar.sig_tx.connect(self.process_sig_rx)


#------------------------------------------------------------------------------
    def update_bottom(self):
        """
        Update log bottom settings
        """
        self.bottom_t = safe_eval(self.led_log_bottom_t.text(), self.bottom_t, 
                                  sign='neg', return_type='float')
        self.led_log_bottom_t.setText(str(self.bottom_t))

        self.bottom_f = safe_eval(self.led_log_bottom_f.text(), self.bottom_f, 
                                  sign='neg', return_type='float')
        self.led_log_bottom_f.setText(str(self.bottom_f))

        self.update_view()
#------------------------------------------------------------------------------
    def calc_win(self):
        """
        (Re-)Calculate the window and its FFT
        """
        self.led_N.setEnabled(not self.chk_auto_N.isChecked())
        if self.chk_auto_N.isChecked():
            self.N = self.win_dict['win_len']
            self.led_N.setText(str(self.N))
        else:
            self.N = safe_eval(self.led_N.text(), self.N, sign='pos', return_type='int')

        self.t = np.arange(self.N)
        params = self.win_dict['win_params'] # convert to iterable
        if not params:
            self.win = getattr(win, self.win_dict['win_fnct'])(self.N)
        elif np.isscalar(params):
            self.win = getattr(win, self.win_dict['win_fnct'])(self.N, params)
        else:
            self.win = getattr(win, self.win_dict['win_fnct'])(self.N, *params)
            
        self.nenbw = self.N * np.sum(np.square(self.win)) / (np.square(np.sum(self.win)))
        self.scale = self.N / np.sum(self.win)

        self.F = fftfreq(self.N * self.pad, d=1. / fb.fil[0]['f_S']) # use zero padding
        self.Win = np.abs(fft(self.win, self.N * self.pad))

        if self.chk_norm_f.isChecked():
            self.Win /= (self.N / self.scale)# correct gain for periodic signals (coherent gain)
#------------------------------------------------------------------------------
    def draw(self):
        """
        Main entry point:
        Re-calculate \|H(f)\| and draw the figure
        """
        self.calc_win()
        self.update_view()

#------------------------------------------------------------------------------
    def update_view(self):
        """
        Draw the figure with new limits, scale etc without recalculating H(f)
        """
        self.ax_t.cla()
        self.ax_f.cla()
        
        self.ax_t.set_xlabel(fb.fil[0]['plt_tLabel'])
        self.ax_t.set_ylabel(r'$w[n] \; \rightarrow$')
        #self.ax_t.set_title("Time")
        
        self.ax_f.set_xlabel(fb.fil[0]['plt_fLabel'])
        self.ax_f.set_ylabel(r'$W(f) \; \rightarrow$')
        #self.ax_f.set_title("Frequency")
        
        if self.chk_log_t.isChecked():
            self.ax_t.plot(self.t, np.maximum(20 * np.log10(np.abs(self.win)), self.bottom_t))
        else:
            self.ax_t.plot(self.t, self.win)

        if self.chk_half_f.isChecked():
            F = self.F[:len(self.F*self.pad)//2]
            Win = self.Win[:len(self.F*self.pad)//2]
        else:
            F = fftshift(self.F)
            Win = fftshift(self.Win)
            
        if self.chk_log_f.isChecked():
            self.ax_f.plot(F, np.maximum(20 * np.log10(np.abs(Win)), self.bottom_f))
            nenbw = 10 * np.log10(self.nenbw)
            unit_nenbw = "dB"
        else:
            self.ax_f.plot(F, Win)
            nenbw = self.nenbw
            unit_nenbw = "bins"
            
        self.led_log_bottom_t.setEnabled(self.chk_log_t.isChecked())
        self.lbl_log_bottom_t.setEnabled(self.chk_log_t.isChecked())
        self.led_log_bottom_f.setEnabled(self.chk_log_f.isChecked())
        self.lbl_log_bottom_f.setEnabled(self.chk_log_f.isChecked())
        
        window_name = self.win_dict['win_name']
        self.mplwidget.fig.suptitle(r'{0} Window'.format(window_name))

        # create two empty patches
        handles = [mpl_patches.Rectangle((0, 0), 1, 1, fc="white", ec="white", lw=0, alpha=0)] * 2

        labels = []
        labels.append("$NENBW$ = {0:.4g} {1}".format(nenbw, unit_nenbw))
        labels.append("$CGAIN$  = {0:.4g}".format(self.scale))
        self.ax_f.legend(handles, labels, loc='best', fontsize='small',
                               fancybox=True, framealpha=0.7)

        self.redraw()

#------------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the canvas when e.g. the canvas size has changed
        """
        self.mplwidget.redraw()

#==============================================================================

if __name__=='__main__':
    import sys
    from pyfda.compat import QApplication
    
    """ Test with python -m pyfda.plot_widgets.plot_fft_win"""
    app = QApplication(sys.argv)
    mainw = Plot_FFT_win(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())

