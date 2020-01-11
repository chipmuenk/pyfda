# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Create a popup window with FFT window information
"""
import logging
logger = logging.getLogger(__name__)

import numpy as np
from numpy.fft import fft, fftshift, fftfreq
from scipy.signal import argrelextrema

import matplotlib.patches as mpl_patches

from pyfda.libs.pyfda_lib import safe_eval, to_html
from pyfda.libs.pyfda_qt_lib import qwindow_stay_on_top
from pyfda.pyfda_rc import params
from pyfda.libs.pyfda_fft_windows_lib import calc_window_function
from pyfda.plot_widgets.mpl_widget import MplWidget

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals

from pyfda.libs.compat import (Qt, pyqtSignal, QHBoxLayout, QVBoxLayout,
                     QDialog, QCheckBox, QLabel, QLineEdit, QFrame, QFont,
                     QTextBrowser, QSplitter,QTableWidget, QTableWidgetItem)

#------------------------------------------------------------------------------
class Plot_FFT_win(QDialog):
    """
    Create a pop-up widget for displaying time and frequency view of an FFT
    window.

    Data is passed via the dictionary `win_dict` that is passed during construction.
    """
    # incoming
    sig_rx = pyqtSignal(object)
    # outgoing
    sig_tx = pyqtSignal(object)

    def __init__(self, parent, win_dict=fb.fil[0]['win_fft'], sym=True, title='pyFDA Window Viewer'):
        super(Plot_FFT_win, self).__init__(parent)

        self.needs_calc = True
        self.needs_draw = True
        self.needs_redraw = True

        self.bottom_f = -80 # min. value for dB display
        self.bottom_t = -60
        self.N = 32 # initial number of data points
        self.N_auto = win_dict['win_len']

        self.pad = 16 # amount of zero padding

        self.win_dict = win_dict
        self.sym = sym

        self.tbl_rows = 2
        self.tbl_cols = 6
        # initial settings for checkboxes
        self.tbl_sel = [True, True, False, False]

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(title)
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
        logger.info("Processing {0} | visible = {1}"\
                     .format(dict_sig, self.isVisible()))
        if ('data_changed' in dict_sig and dict_sig['data_changed'] == 'win')\
            or self.needs_calc:
            logger.warning("Auto: {0} - WinLen: {1}".format(self.N_auto, self.win_dict['win_len']))
            self.N_auto = self.win_dict['win_len']
            self.calc_N()
            
            if self.isVisible():
                self.draw()
                self.needs_calc = False
            else:
                self.needs_calc = True

        elif 'home' in dict_sig:
            self.update_view()

        else:
            logger.error("Unknown content of dict_sig: {0}".format(dict_sig))
                
            
        # if self.isVisible():
        #     if 'data_changed' in dict_sig or 'home' in dict_sig\
        #         or 'filt_changed' in dict_sig or self.needs_calc:
        #         self.draw()
        #         self.needs_calc = False
        #         self.needs_draw = False
        #     elif 'view_changed' in dict_sig or self.needs_draw:
        #         self.update_view()
        #         self.needs_draw = False
        #     elif ('ui_changed' in dict_sig and dict_sig['ui_changed'] == 'resized')\
        #         or self.needs_redraw:
        #         self.redraw()
        #         self.needs_redraw = False
        # else:
        #     if 'data_changed' in dict_sig or 'filt_changed' in dict_sig:
        #         self.needs_calc = True
        #     elif 'view_changed' in dict_sig:
        #         self.needs_draw = True
        #     elif 'ui_changed' in dict_sig and dict_sig['ui_changed'] == 'resized':
        #         self.needs_redraw = True

    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - Matplotlib widget with NavigationToolbar
        - Frame with control elements
        """
        self.bfont = QFont()
        self.bfont.setBold(True)

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

        self.tblWinProperties = QTableWidget(self.tbl_rows, self.tbl_cols, self)
        self.tblWinProperties.setAlternatingRowColors(True)
        self.tblWinProperties.verticalHeader().setVisible(False)
        self.tblWinProperties.horizontalHeader().setVisible(False)
        self._init_table(self.tbl_rows, self.tbl_cols, " ")

        self.txtInfoBox = QTextBrowser(self)

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

        #----------------------------------------------------------------------
        #               ### frmInfo ###
        #
        # This widget encompasses the text info box and the table with window
        # parameters.
        #----------------------------------------------------------------------
        layVInfo = QVBoxLayout(self)
        layVInfo.addWidget(self.tblWinProperties)
        layVInfo.addWidget(self.txtInfoBox)

        self.frmInfo = QFrame(self)
        self.frmInfo.setObjectName("frmInfo")
        self.frmInfo.setLayout(layVInfo)

        #----------------------------------------------------------------------
        #               ### splitter ###
        #
        # This widget encompasses all control subwidgets
        #----------------------------------------------------------------------

        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        splitter.addWidget(self.mplwidget)
        splitter.addWidget(self.frmInfo)

        # setSizes uses absolute pixel values, but can be "misused" by specifying values
        # that are way too large: in this case, the space is distributed according
        # to the _ratio_ of the values:
        splitter.setSizes([3000,1000])

        layVMain = QVBoxLayout()
        layVMain.addWidget(splitter)
        self.setLayout(layVMain)


        #----------------------------------------------------------------------
        #           Set subplots
        #
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

        self.chk_auto_N.clicked.connect(self.calc_N)
        self.led_N.editingFinished.connect(self.draw)

        self.chk_norm_f.clicked.connect(self.draw)
        self.chk_half_f.clicked.connect(self.update_view)

        self.mplwidget.mplToolbar.sig_tx.connect(self.process_sig_rx)
        self.tblWinProperties.itemClicked.connect(self._handle_item_clicked)
#------------------------------------------------------------------------------
    def _init_table(self, rows, cols, val):
        for r in range(rows):
            for c in range(cols):
                item = QTableWidgetItem(val)
                if c % 3 == 0:
                    item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    if self.tbl_sel[r * 2 + c % 3]:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
                self.tblWinProperties.setItem(r,c,item)
 #   https://stackoverflow.com/questions/12366521/pyqt-checkbox-in-qtablewidget

#------------------------------------------------------------------------------
    def _set_table_item(self, row, col, val, font=None, sel=None):
        """
        Set the table item with the index `row, col` and the value val
        """
        item = self.tblWinProperties.item(row, col)
        item.setText(str(val))

        if font:
            self.tblWinProperties.item(row,col).setFont(font)

        if sel == True:
            item.setCheckState(Qt.Checked)
        if sel == False:
            item.setCheckState(Qt.Unchecked)
        # when sel is not specified, don't change anything

#------------------------------------------------------------------------------
    def _handle_item_clicked(self, item):
        if item.column() % 3 == 0: # clicked on checkbox
            num = item.row() * 2 + item.column() // 3
            if item.checkState() == Qt.Checked:
                self.tbl_sel[num] = True
                logger.debug('"{0}:{1}" Checked'.format(item.text(), num))
            else:
                self.tbl_sel[num] = False
                logger.debug('"{0}:{1}" Unchecked'.format(item.text(), num))

        elif item.column() % 3 == 1: # clicked on value field
            logger.info("{0:s} copied to clipboard.".format(item.text()))
            fb.clipboard.setText(item.text())

        self.update_view()

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
    def calc_N(self):
        """
        (Re-)Calculate the number of data points when Auto N chkbox has been
        clicked or when the number of data points has been updated outside this
        class
        """
        if self.chk_auto_N.isChecked():
            self.N = self.N_auto

        self.draw()

#------------------------------------------------------------------------------
    def calc_win(self):
        """
        (Re-)Calculate the window and its FFT
        """
        self.led_N.setEnabled(not self.chk_auto_N.isChecked())

        if not self.chk_auto_N.isChecked():
            self.N = safe_eval(self.led_N.text(), self.N, sign='pos', return_type='int')
       # else:
            #self.N = self.win_dict['win_len']

        self.led_N.setText(str(self.N))

        self.n = np.arange(self.N)

        self.win = calc_window_function(self.win_dict, self.win_dict['name'], self.N, sym=self.sym)


        self.nenbw = self.N * np.sum(np.square(self.win)) / (np.square(np.sum(self.win)))
        self.scale = self.N / np.sum(self.win)

        self.F = fftfreq(self.N * self.pad, d=1. / fb.fil[0]['f_S']) # use zero padding
        self.Win = np.abs(fft(self.win, self.N * self.pad))
        if self.chk_norm_f.isChecked():
            self.Win /= (self.N / self.scale)# correct gain for periodic signals (coherent gain)

        first_zero = argrelextrema(self.Win[:(self.N*self.pad)//2], np.less)
        if np.shape(first_zero)[1] > 0:
            first_zero = first_zero[0][0]
            self.first_zero_f = self.F[first_zero]
            self.sidelobe_level = np.max(self.Win[first_zero:(self.N*self.pad)//2])
        else:
            self.first_zero_f = np.nan
            self.sidelobe_level = 0

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
        Draw the figure with new limits, scale etc without recalculating the
        window.
        """
        # suppress "divide by zero in log10" warnings
        old_settings_seterr = np.seterr()
        np.seterr(divide='ignore')

        self.ax_t.cla()
        self.ax_f.cla()

        self.ax_t.set_xlabel(fb.fil[0]['plt_tLabel'])
        self.ax_t.set_ylabel(r'$w[n] \; \rightarrow$')

        self.ax_f.set_xlabel(fb.fil[0]['plt_fLabel'])
        self.ax_f.set_ylabel(r'$W(f) \; \rightarrow$')

        if self.chk_log_t.isChecked():
            self.ax_t.plot(self.n, np.maximum(20 * np.log10(np.abs(self.win)), self.bottom_t))
        else:
            self.ax_t.plot(self.n, self.win)

        if self.chk_half_f.isChecked():
            F = self.F[:len(self.F*self.pad)//2]
            Win = self.Win[:len(self.F*self.pad)//2]
        else:
            F = fftshift(self.F)
            Win = fftshift(self.Win)

        if self.chk_log_f.isChecked():
            self.ax_f.plot(F, np.maximum(20 * np.log10(np.abs(Win)), self.bottom_f))
            self.nenbw_disp = 10 * np.log10(self.nenbw)
            self.scale_disp = 20 * np.log10(self.scale)
            self.sidelobe_level_disp = 20 * np.log10(self.sidelobe_level)
            self.unit_nenbw = "dB"
            self.unit_scale = "dB"
        else:
            self.ax_f.plot(F, Win)
            self.nenbw_disp = self.nenbw
            self.scale_disp = self.scale
            self.sidelobe_level_disp = self.sidelobe_level
            self.unit_nenbw = "bins"
            self.unit_scale = ""

        self.led_log_bottom_t.setEnabled(self.chk_log_t.isChecked())
        self.lbl_log_bottom_t.setEnabled(self.chk_log_t.isChecked())
        self.led_log_bottom_f.setEnabled(self.chk_log_f.isChecked())
        self.lbl_log_bottom_f.setEnabled(self.chk_log_f.isChecked())

        window_name = self.win_dict['name']
        param_txt = ""
        if self.win_dict['n_par'] > 0:
            param_txt = " (" + self.win_dict['par'][0]['name_tex'] + " = {0:.3g})".format(self.win_dict['par'][0]['val'])
        if self.win_dict['n_par'] > 1:
            param_txt = param_txt[:-1]\
                + ", {0:s} = {1:.3g})".format(self.win_dict['par'][1]['name_tex'], self.win_dict['par'][1]['val'])

        self.mplwidget.fig.suptitle(r'{0} Window'.format(window_name)
                                    +param_txt)

        # plot a line at the max. sidelobe level
        if self.tbl_sel[3]:
            self.ax_f.axhline(self.sidelobe_level_disp, ls='dotted', c='b')

        patch = mpl_patches.Rectangle((0, 0), 1, 1, fc="white", ec="white", lw=0, alpha=0)
        # Info legend for time domain window
        labels_t = []
        labels_t.append("$N$ = {0:d}".format(self.N))
        self.ax_t.legend([patch], labels_t, loc='best', fontsize='small',
                              fancybox=True, framealpha=0.7,
                              handlelength=0, handletextpad=0)

        # Info legend for frequency domain window
        labels_f = []
        N_patches = 0
        if self.tbl_sel[0]:
            labels_f.append("$NENBW$ = {0:.4g} {1}".format(self.nenbw_disp, self.unit_nenbw))
            N_patches += 1
        if self.tbl_sel[1]:
            labels_f.append("$CGAIN$ = {0:.4g} {1}".format(self.scale_disp, self.unit_nenbw))
            N_patches += 1
        if self.tbl_sel[2]:
            labels_f.append("1st Zero = {0:.4g}".format(self.first_zero_f))
            N_patches += 1
        if N_patches > 0:
            self.ax_f.legend([patch] * N_patches, labels_f, loc='best', fontsize='small',
                                   fancybox=True, framealpha=0.7,
                                   handlelength=0, handletextpad=0)
        np.seterr(**old_settings_seterr)

        self.update_info()
        self.redraw()

#------------------------------------------------------------------------------
    def update_info(self):
        """
        Update the text info box for the window
        """
        if 'info' in self.win_dict:
            self.txtInfoBox.setText(self.win_dict['info'])

        self._set_table_item(0,0, "ENBW", font=self.bfont)#, sel=True)
        self._set_table_item(0,1, "{0:.5g}".format(self.nenbw_disp))
        self._set_table_item(0,2, self.unit_nenbw)
        self._set_table_item(0,3, "Scale", font=self.bfont)#, sel=True)
        self._set_table_item(0,4, "{0:.5g}".format(self.scale_disp))
        self._set_table_item(0,5, self.unit_scale)

        self._set_table_item(1,0, "1st Zero", font=self.bfont)#, sel=True)
        self._set_table_item(1,1, "{0:.5g}".format(self.first_zero_f))
        self._set_table_item(1,2, "f_S")

        self._set_table_item(1,3, "Sidelobes", font=self.bfont)#, sel=True)
        self._set_table_item(1,4, "{0:.5g}".format(self.sidelobe_level_disp))
        self._set_table_item(1,5, self.unit_scale)

        self.tblWinProperties.resizeColumnsToContents()
        self.tblWinProperties.resizeRowsToContents()
#------------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the canvas when e.g. the canvas size has changed
        """
        self.mplwidget.redraw()
        self.needs_redraw = False

#==============================================================================

if __name__=='__main__':
    import sys
    from pyfda.libs.compat import QApplication

    """ Test with python -m pyfda.plot_widgets.plot_fft_win"""
    app = QApplication(sys.argv)
    mainw = Plot_FFT_win(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())

    # module test using python -m pyfda.plot_widgets.plot_fft_win
