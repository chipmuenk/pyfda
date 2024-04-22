# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Design windowed FIR filters (LP, HP, BP, BS) with fixed order, return
the filter design in coefficient ('ba') format

Attention:
This class is re-instantiated dynamically everytime the filter design method
is selected, calling the __init__ method.

API version info:
    1.0: initial working release
    1.1: mark private methods as private
    1.2: new API using fil_save
    1.3: new public methods destruct_UI + construct_UI (no longer called by __init__)
    1.4: module attribute `filter_classes` contains class name and combo box name
         instead of class attribute `name`
         `FRMT` is now a class attribute
    2.0: Specify the parameters for each subwidget as tuples in a dict where the
         first element controls whether the widget is visible and / or enabled.
         This dict is now called self.rt_dict. When present, the dict self.rt_dict_add
         is read and merged with the first one.

    2.1: Remove method destruct_UI and attributes self.wdg and self.hdl

   :2.2: Rename `filter_classes` -> `classes`, remove Py2 compatibility
"""
from pyfda.libs.compat import (QWidget, pyqtSignal, QComboBox, QIcon, QSize,
                               QPushButton, QHBoxLayout, QVBoxLayout)
import numpy as np
import scipy.signal as sig
from scipy.signal import signaltools
from scipy.special import sinc

import pyfda.filterbroker as fb  # importing filterbroker initializes all its globals
from pyfda.libs.pyfda_lib import fil_save, round_odd, pprint_log
from pyfda.libs.pyfda_qt_lib import popup_warning
from pyfda.libs.pyfda_fft_windows_lib import QFFTWinSelector, get_windows_dict
from pyfda.plot_widgets.plot_fft_win import Plot_FFT_win
from .common import Common, remezord

import logging
logger = logging.getLogger(__name__)

# TODO: Hilbert, differentiator, multiband are missing
# TODO: Improve calculation of F_C and F_C2 using the weights
# TODO: Automatic setting of density factor for remez calculation?
#       Automatic switching to Kaiser / Hermann?
# TODO: Parameters for windows are not stored in fil_dict?

__version__ = "2.2"

classes = {'Firwin': 'Windowed FIR'}  #: Dict containing class name : display name


class Firwin(QWidget):

    FRMT = 'ba'     # output format(s) of filter design routines 'zpk' / 'ba' / 'sos'
                    # currently, only 'ba' is supported for firwin routines

    sig_tx = pyqtSignal(object)  # local signal between FFT widget and FFTWin_Selector
    sig_tx_local = pyqtSignal(object)
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, objectName='firwin_inst'):
        QWidget.__init__(self)

        self.setObjectName(objectName)
        self.ft = 'FIR'

        win_names_list = ["Boxcar", "Rectangular", "Barthann", "Bartlett", "Blackman",
                          "Blackmanharris", "Bohman", "Cosine", "Dolph-Chebyshev", "DPSS",
                          "Flattop", "General Gaussian", "Gauss", "Hamming", "Hann",
                          "Kaiser", "Nuttall", "Parzen", "Triangular", "Tukey"]
        self.cur_win_name = "Kaiser"  # set initial window type
        self.alg = "ichige"

        # initialize windows dict with the list above for firwin window settings
        self.win_dict = get_windows_dict(
            win_names_list=win_names_list,
            cur_win_name=self.cur_win_name)

        # get initial / last setting from dictionary, updating self.win_dict
        self._load_dict()

        # instantiate FFT window with windows dict
        self.fft_widget = Plot_FFT_win(
            win_dict=self.win_dict, sym=True, title="pyFDA FIR Window Viewer")
        # hide window initially, this is modeless i.e. a non-blocking popup window
        self.fft_widget.hide()

        c = Common()
        self.rt_dict = c.rt_base_iir

        self.rt_dict_add = {
            'COM': {
                'min': {
                    'msg': ('a',
                            "<br /><b>Note:</b> Filter order is only a rough "
                            "approximation and most likely far too low!")},
                'man': {
                    'msg': ('a', "Enter desired filter order <b><i>N</i></b> and "
                            "<b>-6 dB</b> pass band corner "
                            "frequency(ies) <b><i>F<sub>C</sub></i></b> .")},
                        },
            'LP': {'man': {}, 'min': {}},
            'HP': {'man': {'msg': ('a', r"<br /><b>Note:</b> Order needs to be odd!")},
                   'min': {}},
            'BS': {'man': {'msg': ('a', r"<br /><b>Note:</b> Order needs to be odd!")},
                   'min': {}},
            'BP': {'man': {}, 'min': {}},
            }

        self.info = """**Windowed FIR filters**

        are designed by truncating the
        infinite impulse response of an ideal filter with a window function.
        The kind of used window has strong influence on ripple etc. of the
        resulting filter.

        **Design routines:**

        ``scipy.signal.firwin()``

        """
        # self.info_doc = [] is set in self._update_UI()

        # ------------------- end of static info for filter tree ---------------

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process local signals from / for
        - FFT window widget
        - qfft_win_select
        """

        logger.debug("SIG_RX - vis: {0}\n{1}"
                     .format(self.isVisible(), pprint_log(dict_sig)))

        if dict_sig['id'] == id(self):
            logger.warning(f"Stopped infinite loop:\n{pprint_log(dict_sig)}")

        # --- signals coming from the FFT window widget or the qfft_win_select
        if dict_sig['class'] in {'Plot_FFT_win', 'QFFTWinSelector'}:
            if 'close_event' in dict_sig:  # hide FFT window windget and return
                self.hide_fft_wdg()
                return
            else:
                if 'view_changed' in dict_sig and 'fft_win' in dict_sig['view_changed']:
                    # self._update_fft_window()  # TODO: needed?
                    # local connection to FFT window widget and qfft_win_select
                    self.emit(dict_sig, sig_name='sig_tx_local')
                    # global connection to upper hierarchies
                    # send notification that filter design has changed
                    self.emit({'filt_changed': 'firwin'})

    # --------------------------------------------------------------------------
    def construct_UI(self):
        """
        Create additional subwidget(s) needed for filter design:
        These subwidgets are instantiated dynamically when needed in
        select_filter.py using the handle to the filter object, fb.filObj .
        """
        # Combobox for selecting the algorithm to estimate minimum filter order
        self.cmb_firwin_alg = QComboBox(self)
        self.cmb_firwin_alg.setObjectName('wdg_cmb_firwin_alg')
        self.cmb_firwin_alg.addItems(['ichige', 'kaiser', 'herrmann'])
        # Minimum size, can be changed in the upper hierarchy levels using layouts:
        self.cmb_firwin_alg.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmb_firwin_alg.hide()

        self.qfft_win_select = QFFTWinSelector(self.win_dict, objectName='fir_win_qfft')
        # Minimum size, can be changed in the upper hierarchy levels using layouts:
        # self.qfft_win_select.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.but_fft_wdg = QPushButton(self)
        self.but_fft_wdg.setIcon(QIcon(":/fft.svg"))
        but_height = self.qfft_win_select.sizeHint().height()
        self.but_fft_wdg.setIconSize(QSize(but_height, but_height))
        self.but_fft_wdg.setFixedSize(QSize(but_height, but_height))
        self.but_fft_wdg.setToolTip('<span>Show / hide FFT widget (select window type '
                                    ' and display its properties).</span>')
        self.but_fft_wdg.setCheckable(True)
        self.but_fft_wdg.setChecked(False)


        self.layHWin1 = QHBoxLayout()
        # self.layHWin1.addWidget(self.cmb_firwin_win)
        # self.layHWin1.addWidget(self.but_fft_wdg)
        self.layHWin1.addWidget(self.cmb_firwin_alg)
        self.layHWin2 = QHBoxLayout()
        self.layHWin2.addWidget(self.but_fft_wdg)
        self.layHWin2.addWidget(self.qfft_win_select)

        self.layVWin = QVBoxLayout()
        self.layVWin.addLayout(self.layHWin1)
        self.layVWin.addLayout(self.layHWin2)
        self.layVWin.setContentsMargins(0, 0, 0, 0)

        # Widget containing all subwidgets (cmbBoxes, Labels, lineEdits)
        self.wdg_fil = QWidget(self)
        self.wdg_fil.setObjectName('wdg_fil')
        self.wdg_fil.setLayout(self.layVWin)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # connect FFT widget to qfft_selector and vice versa and to signals upstream:
        self.fft_widget.sig_tx.connect(self.process_sig_rx)
        self.qfft_win_select.sig_tx.connect(self.process_sig_rx)
        # connect process_sig_rx output to both FFT widgets
        self.sig_tx_local.connect(self.fft_widget.sig_rx)
        self.sig_tx_local.connect(self.qfft_win_select.sig_rx)

        # ----------------------------------------------------------------------
        # SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.cmb_firwin_alg.currentIndexChanged.connect(self._update_fft_window)
        self.but_fft_wdg.clicked.connect(self.toggle_fft_wdg)
        # ----------------------------------------------------------------------

# ==============================================================================
    def _update_fft_window(self):
        """ Update window type for FirWin - unneeded at the moment """
        self.alg = str(self.cmb_firwin_alg.currentText())
        self.emit({'filt_changed': 'firwin'})

    # --------------------------------------------------------------------------
    def _load_dict(self):
        """
        Reload window selection and parameters from filter dictionary
        and set UI elements accordingly. load_dict() is called upon
        initialization and when the filter is loaded from disk.
        """
        self.N = fb.fil[0]['N']
        # alg_idx = 0
        if 'wdg_fil' in fb.fil[0] and 'firwin' in fb.fil[0]['wdg_fil']\
                and type(fb.fil[0]['wdg_fil']['firwin']) is dict:
            self.win_dict = fb.fil[0]['wdg_fil']['firwin']

        self.emit({'view_changed': 'fft_win_type'}, sig_name='sig_tx_local')

    # --------------------------------------------------------------------------
    def _store_dict(self):
        """
        Store window and parameter settings using `self.win_dict` in filter dictionary.
        """
        if 'wdg_fil' not in fb.fil[0]:
            fb.fil[0].update({'wdg_fil': {}})
        fb.fil[0]['wdg_fil'].update({'firwin': self.win_dict})

    # --------------------------------------------------------------------------
    def _get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N     = fil_dict['N']
        self.F_PB  = fil_dict['F_PB']
        self.F_SB  = fil_dict['F_SB']
        self.F_PB2 = fil_dict['F_PB2']
        self.F_SB2 = fil_dict['F_SB2']
        self.F_C   = fil_dict['F_C']
        self.F_C2  = fil_dict['F_C2']

        # firwin amplitude specs are linear (not in dBs)
        self.A_PB  = fil_dict['A_PB']
        self.A_PB2 = fil_dict['A_PB2']
        self.A_SB  = fil_dict['A_SB']
        self.A_SB2 = fil_dict['A_SB2']

#        self.alg = 'ichige' # algorithm for determining the minimum order
#        self.alg = self.cmb_firwin_alg.currentText()

    def _test_N(self):
        """
        Warn the user if the calculated order is too high for a reasonable filter
        design.
        """
        if self.N > 1000:
            return popup_warning(self, self.N, "FirWin")
        else:
            return True

    def _save(self, fil_dict, arg):
        """
        Convert between poles / zeros / gain, filter coefficients (polynomes)
        and second-order sections and store all available formats in the passed
        dictionary 'fil_dict'.
        """
        fil_save(fil_dict, arg, self.FRMT, __name__)

        try:  # has the order been calculated by a "min" filter design?
            fil_dict['N'] = self.N  # yes, update filterbroker
        except AttributeError:
            pass
        self._store_dict()

# ------------------------------------------------------------------------------
    def firwin(self, numtaps, cutoff, window=None, pass_zero=True,
               scale=True, nyq=1.0, fs=None):

        """
        FIR filter design using the window method. This is more or less the
        same as `scipy.signal.firwin` with the exception that an ndarray with
        the window values can be passed as an alternative to the window name.

        The parameters "width" (specifying a Kaiser window) and "fs" have been
        omitted, they are not needed here.

        This function computes the coefficients of a finite impulse response
        filter.  The filter will have linear phase; it will be Type I if
        `numtaps` is odd and Type II if `numtaps` is even.
        Type II filters always have zero response at the Nyquist rate, so a
        ValueError exception is raised if firwin is called with `numtaps` even and
        having a passband whose right end is at the Nyquist rate.

        Parameters
        ----------
        numtaps : int
            Length of the filter (number of coefficients, i.e. the filter
            order + 1).  `numtaps` must be even if a passband includes the
            Nyquist frequency.
        cutoff : float or 1D array_like
            Cutoff frequency of filter (expressed in the same units as `nyq`)
            OR an array of cutoff frequencies (that is, band edges). In the
            latter case, the frequencies in `cutoff` should be positive and
            monotonically increasing between 0 and `nyq`.  The values 0 and
            `nyq` must not be included in `cutoff`.
        window : ndarray or string
            string: use the window with the passed name from scipy.signal.windows

            ndarray: The window values - this is an addition to the original
            firwin routine.
        pass_zero : bool, optional
            If True, the gain at the frequency 0 (i.e. the "DC gain") is 1.
            Otherwise the DC gain is 0.
        scale : bool, optional
            Set to True to scale the coefficients so that the frequency
            response is exactly unity at a certain frequency.
            That frequency is either:
            - 0 (DC) if the first passband starts at 0 (i.e. pass_zero
              is True)
            - `nyq` (the Nyquist rate) if the first passband ends at
              `nyq` (i.e the filter is a single band highpass filter);
              center of first passband otherwise
        nyq : float, optional
            Nyquist frequency.  Each frequency in `cutoff` must be between 0
            and `nyq`.

        Returns
        -------
        h : (numtaps,) ndarray
            Coefficients of length `numtaps` FIR filter.
        Raises
        ------
        ValueError
            If any value in `cutoff` is less than or equal to 0 or greater
            than or equal to `nyq`, if the values in `cutoff` are not strictly
            monotonically increasing, or if `numtaps` is even but a passband
            includes the Nyquist frequency.
        See also
        --------
        scipy.firwin
        """
        cutoff = np.atleast_1d(cutoff) / float(nyq)

        # Check for invalid input.
        if cutoff.ndim > 1:
            raise ValueError("The cutoff argument must be at most "
                             "one-dimensional.")
        if cutoff.size == 0:
            raise ValueError("At least one cutoff frequency must be given.")
        if cutoff.min() <= 0 or cutoff.max() >= 1:
            raise ValueError("Invalid cutoff frequency {0}: frequencies must be "
                             "greater than 0 and less than nyq.".format(cutoff))
        if np.any(np.diff(cutoff) <= 0):
            raise ValueError("Invalid cutoff frequencies: the frequencies "
                             "must be strictly increasing.")

        pass_nyquist = bool(cutoff.size & 1) ^ pass_zero
        if pass_nyquist and numtaps % 2 == 0:
            raise ValueError("A filter with an even number of coefficients must "
                             "have zero response at the Nyquist rate.")

        # Insert 0 and/or 1 at the ends of cutoff so that the length of cutoff
        # is even, and each pair in cutoff corresponds to passband.
        cutoff = np.hstack(([0.0] * pass_zero, cutoff, [1.0] * pass_nyquist))

        # `bands` is a 2D array; each row gives the left and right edges of
        # a passband.
        bands = cutoff.reshape(-1, 2)

        # Build up the coefficients.
        alpha = 0.5 * (numtaps - 1)
        m = np.arange(0, numtaps) - alpha
        h = 0
        for left, right in bands:
            h += right * sinc(right * m)
            h -= left * sinc(left * m)

        if type(window) == str:
            # Get and apply the window function.
            # from scipy.signal.signaltools import get_window
            win = signaltools.get_window(window, numtaps, fftbins=False)
        elif type(window) == np.ndarray:
            win = window
        else:
            logger.error("The 'window' was neither a string nor a numpy array, "
                         "it could not be evaluated.")
            return None
        # apply the window function.
        h *= win

        # Now handle scaling if desired.
        if scale:
            # Get the first passband.
            left, right = bands[0]
            if left == 0:
                scale_frequency = 0.0
            elif right == 1:
                scale_frequency = 1.0
            else:
                scale_frequency = 0.5 * (left + right)
            c = np.cos(np.pi * m * scale_frequency)
            s = np.sum(h * c)
            h /= s
        return h

    def _firwin_ord(self, F, W, A, alg):
        # http://www.mikroe.com/chapters/view/72/chapter-2-fir-filters/
        delta_f = abs(F[1] - F[0]) * 2  # referred to f_Ny
        # delta_A = np.sqrt(A[0] * A[1])
        if "Kaiser" in self.win_dict and self.win_dict['cur_win_name'] == "Kaiser":
            N, beta = sig.kaiserord(20 * np.log10(np.abs(fb.fil[0]['A_SB'])), delta_f)
            # logger.warning(f"N={N}, beta={beta}, A_SB={fb.fil[0]['A_SB']}")
            self.win_dict["Kaiser"]["par"][0]["val"] = beta
            self.qfft_win_select.led_win_par_0.setText(str(beta))
            self.qfft_win_select.ui2dict_params()  # pass changed parameter to other widgets
        else:
            N = remezord(
                F, W, A, fs=1, alg=alg)[0]
        self.emit({'view_changed': 'fft_win_type'}, sig_name='sig_tx_local')
        return N

    def LPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N = self._firwin_ord([self.F_PB, self.F_SB], [1, 0],
                                  [self.A_PB, self.A_SB], alg=self.alg)
        if not self._test_N():
            return -1

        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2  # average calculated F_PB and F_SB
        self._save(fil_dict,
                   self.firwin(self.N, fil_dict['F_C'], nyq=0.5,
                               window=self.qfft_win_select.get_window(self.N, sym=True)))

    def LPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict,
                   self.firwin(self.N, fil_dict['F_C'], nyq=0.5,
                               window=self.qfft_win_select.get_window(self.N, sym=True)))

    def HPmin(self, fil_dict):
        self._get_params(fil_dict)
        N = self._firwin_ord([self.F_SB, self.F_PB], [0, 1],
                             [self.A_SB, self.A_PB], alg=self.alg)
        self.N = round_odd(N)  # enforce odd order
        if not self._test_N():
            return -1
        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2  # average calculated F_PB and F_SB
        self._save(fil_dict,
                   self.firwin(self.N, fil_dict['F_C'], pass_zero=False, nyq=0.5,
                               window=self.qfft_win_select.get_window(self.N, sym=True)))

    def HPman(self, fil_dict):
        self._get_params(fil_dict)
        self.N = round_odd(self.N)  # enforce odd order
        if not self._test_N():
            return -1
        self._save(fil_dict,
                   self.firwin(self.N, fil_dict['F_C'], pass_zero=False, nyq=0.5,
                               window=self.qfft_win_select.get_window(self.N, sym=True)))

    # For BP and BS, F_PB and F_SB have two elements each
    def BPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N = remezord([self.F_SB, self.F_PB, self.F_PB2, self.F_SB2], [0, 1, 0],
                          [self.A_SB, self.A_PB, self.A_SB2], fs=1, alg=self.alg)[0]
        if not self._test_N():
            return -1

        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2  # average calculated F_PB and F_SB
        fil_dict['F_C2'] = (self.F_SB2 + self.F_PB2)/2
        self._save(fil_dict,
                   self.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']], nyq=0.5,
                               pass_zero=False,
                               window=self.qfft_win_select.get_window(self.N, sym=True)))

    def BPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict,
                   self.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']], nyq=0.5,
                               pass_zero=False,
                               window=self.qfft_win_select.get_window(self.N, sym=True)))

    def BSmin(self, fil_dict):
        self._get_params(fil_dict)
        N = remezord([self.F_PB, self.F_SB, self.F_SB2, self.F_PB2], [1, 0, 1],
                     [self.A_PB, self.A_SB, self.A_PB2], fs=1, alg=self.alg)[0]
        self.N = round_odd(N)  # enforce odd order
        if not self._test_N():
            return -1
        fil_dict['F_C'] = (self.F_SB + self.F_PB) / 2  # average calculated F_PB and F_SB
        fil_dict['F_C2'] = (self.F_SB2 + self.F_PB2) / 2
        self._save(fil_dict,
                   self.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']],
                               window=self.qfft_win_select.get_window(self.N, sym=True),
                               pass_zero=True, nyq=0.5))

    def BSman(self, fil_dict):
        self._get_params(fil_dict)
        self.N = round_odd(self.N)  # enforce odd order
        if not self._test_N():
            return -1
        self._save(fil_dict,
                   self.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']],
                               window=self.qfft_win_select.get_window(self.N, sym=True),
                               pass_zero=True, nyq=0.5))

    # ------------------------------------------------------------------------------
    def toggle_fft_wdg(self):
        """
        Show / hide FFT widget depending on the state of the corresponding button
        When widget is shown, trigger an update of the window function.
        """
        if self.but_fft_wdg.isChecked():
            self.fft_widget.show()
            self.emit({'view_changed': 'fft_win_type'}, sig_name='sig_tx_local')
        else:
            self.fft_widget.hide()

    # --------------------------------------------------------------------------
    def hide_fft_wdg(self):
        """
        The closeEvent caused by clicking the "x" in the FFT widget is caught
        there and routed here to only hide the window
        """
        self.but_fft_wdg.setChecked(False)
        self.fft_widget.hide()


# ------------------------------------------------------------------------------
def main():
    import sys
    from pyfda.libs.compat import QApplication, QFrame

    app = QApplication(sys.argv)

    # instantiate filter widget
    filt = Firwin()
    filt.construct_UI()
    wdg_firwin = getattr(filt, 'wdg_fil')

    layVDynWdg = QVBoxLayout()
    layVDynWdg.addWidget(wdg_firwin, stretch=1)

    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][filt.FRMT])  # return results in default format

    frmMain = QFrame()
    frmMain.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
    frmMain.setLayout(layVDynWdg)

    mainw = frmMain
    mainw.show()

    app.exec_()


if __name__ == "__main__":
    '''test using "python -m pyfda.filter_widgets.firwin" '''
    main()
