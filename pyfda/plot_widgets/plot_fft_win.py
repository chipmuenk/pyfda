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
import scipy.signal.windows as win

#from pyfda.pyfda_lib import safe_eval
from pyfda.pyfda_qt_lib import qget_selected, qget_cmb_box, qset_cmb_box
from pyfda.pyfda_rc import params
from pyfda.plot_widgets.mpl_widget import MplWidget
#import pyfda.pyfda_dirs as dirs
import pyfda.filterbroker as fb # importing filterbroker initializes all its globals

from pyfda.compat import (QMainWindow, QtCore, QFrame, QLabel, pyqtSignal,
                     QCheckBox, QComboBox, QPushButton, QLineEdit,
                     QHBoxLayout, QVBoxLayout)
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

    def __init__(self, parent):
        super(Plot_FFT_win, self).__init__(parent)
        self.needs_calc = False
        self.bottom_f = -80 # min. value for dB display
        
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle('pyFDA Window Viewer')
        self._construct_UI()

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
        logger.debug("Processing {0} | needs_calc = {1}, visible = {2}"\
                     .format(dict_sig, self.needs_calc, self.isVisible()))
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

        self.cmbUnitsPhi = QComboBox(self)
        units = ["rad", "rad/pi",  "deg"]
        scales = [1.,   1./ np.pi, 180./np.pi]
        for unit, scale in zip(units, scales):
            self.cmbUnitsPhi.addItem(unit, scale)
        self.cmbUnitsPhi.setObjectName("cmbUnitsA")
        self.cmbUnitsPhi.setToolTip("Set unit for phase.")
        self.cmbUnitsPhi.setCurrentIndex(0)
        self.cmbUnitsPhi.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.chk_f_log = QCheckBox("Log", self)
        self.chk_f_log.setChecked(False)
        self.chk_f_log.setToolTip("Display in dB")
        
        self.led_log_bottom_f = QLineEdit(self)
        self.led_log_bottom_f.setText(str(self.bottom_f))
        self.led_log_bottom_f.setToolTip("<span>Minimum display value for log. scale.</span>")


        layHControls = QHBoxLayout()
        layHControls.addWidget(self.cmbUnitsPhi)
        layHControls.addWidget(self.chk_f_log)
        layHControls.addWidget(self.led_log_bottom_f)
        layHControls.addStretch(10)

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

        self.init_axes()

        self.draw() # initial drawing

        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.chk_f_log.clicked.connect(self.draw)
        self.cmbUnitsPhi.currentIndexChanged.connect(self.draw)
        self.mplwidget.mplToolbar.sig_tx.connect(self.process_sig_rx)

#------------------------------------------------------------------------------
    def init_axes(self):
        """
        Initialize and clear the axes - this is only called once
        """
        window_name = "Kaiser"
        self.fig = self.mplwidget.fig
        self.fig.suptitle(r'{0} Window in Time and Spectrum'.format(window_name))
        self.fig.subplots_adjust(top=0.88)

        self.ax_t = self.fig.add_subplot(211)
        self.ax_t.set_title("Time")
        self.ax_f = self.fig.add_subplot(212)
        self.ax_f.set_title("Frequency")
        self.ax_t.get_xaxis().tick_bottom() # remove axis ticks on top
        self.ax_t.get_yaxis().tick_left() # remove axis ticks right
        self.ax_t.set_xlabel(fb.fil[0]['plt_tLabel'])
        self.fig.set_tight_layout(True)

#------------------------------------------------------------------------------
    def calc_win(self):
        """
        (Re-)Calculate the FFT window in the time domain, only dummy data at the moment
        """
        # calculate H_cplx(W) (complex) for W = 0 ... 2 pi:
        self.N = fb.fil[0]['win_len']
        self.t = np.arange(self.N)
        self.win = getattr(win, fb.fil[0]['win_fnct'])(self.N)
        # replace nan and inf by finite values, otherwise np.unwrap yields
        # an array full of nans
        
#------------------------------------------------------------------------------
    def calc_win_freq(self):
        """
        Calculate frequency transform of window function
        """
        self.F = np.fft.fftfreq(self.N, d=1. / fb.fil[0]['f_S'])
        self.Win = np.abs(np.fft.fft(self.win)) / self.N

        if fb.fil[0]['freqSpecsRangeType'] == 'half':
            self.Win[1:] = 2 * self.Win[1:]
        if self.chk_f_log.isChecked():
            self.Win = np.maximum(20 * np.log10(self.Win), self.bottom_f)  

        if fb.fil[0]['freqSpecsRangeType'] == 'sym':
        # shift X, Y and F by f_S/2
            self.Win = np.fft.fftshift(self.Win)
            self.F = np.fft.fftshift(self.F)
        elif fb.fil[0]['freqSpecsRangeType'] == 'half':
            self.Win = self.Win[0:self.N//2]
            self.F = self.F[0:self.N//2]
        else: # fb.fil[0]['freqSpecsRangeType'] == 'whole'
            # plot for F = 0 ... 1
            self.F = np.fft.fftshift(self.F) + fb.fil[0]['f_S']/2.

#------------------------------------------------------------------------------
    def draw(self):
        """
        Main entry point:
        Re-calculate \|H(f)\| and draw the figure
        """
        self.calc_win()
        self.calc_win_freq()
        self.update_view()

#------------------------------------------------------------------------------
    def update_view(self):
        """
        Draw the figure with new limits, scale etc without recalculating H(f)
        """

        self.unitPhi = qget_cmb_box(self.cmbUnitsPhi, data=False)

        #========= select frequency range to be displayed =====================
        #=== shift, scale and select: W -> F, H_cplx -> H_c

        y_str = r'$t \rightarrow$'

        #---------------------------------------------------------
        #self.ax_t.clear() # need to clear, doesn't overwrite
        #self.ax_f.clear() # need to clear, doesn't overwrite
        line_win_t, = self.ax_t.plot(self.t, self.win)
        line_win_t, = self.ax_f.plot(self.F, self.Win)
        #---------------------------------------------------------
        self.ax_t.set_ylabel(y_str)
        
        self.ax_f.set_xlabel(fb.fil[0]['plt_fLabel'])
        self.ax_f.set_xlim(fb.fil[0]['freqSpecsRange'])

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

