# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

import importlib
import copy
import numpy as np
import scipy.signal as sig
import scipy

from .pyfda_qt_lib import qset_cmb_box, qget_cmb_box
from .pyfda_lib import to_html, safe_eval, pprint_log
from pyfda.pyfda_rc import params
from .compat import (QWidget, QLabel, QComboBox, QLineEdit,
                     QHBoxLayout, pyqtSignal)

import logging
logger = logging.getLogger(__name__)

"""
Dictionary with available FFT windows, their function names and their properties.

When the function name `fn_name` is just a string, it is taken from
`scipy.signal.windows`, otherwise it has to be fully qualified name.
"""
bartlett_info =\
    '''<span>
    The Bartlett and triangular windows are similar, except that the end
    point(s) of the Bartlett window are at zero. Its side lobes fall off with
    12 dB/oct., the min. side lobe suppression is 26 dB.<br /><br />

    It can be constructed as the convolution of two rectangular windows,
    hence, its Fourier transform is the product of two (periodic) sinc
    functions, decaying twice as fast as the spectrum of a rectangular window.
    </span>'''
rectangular_info =\
    '''<span>
    Boxcar or Rectangular window, best suited for analyzing coherent signals,
    i.e. where the window length is an integer number of the signal period.
    It also works great when the signal length is shorter than the window
    length (e.g. for the impulse response of a FIR filter). For other signals, it
    has the worst sidelobe suppression (13 dB) of all windows.
    This window also has the best SNR of all windows.<br /><br />

    When used for FIR filter design, a filter with the least square error
    is returned, created by truncating the sinc-law frequency response after
    N terms and transforming back to the time domain. It has the sharpest
    transition of all windowed FIR filters but the worst stop band attenuation.
    </span>'''
all_windows_dict = {
    # array for caching window values, dtype=object because subarrays
    # differ in length
    'win': np.array([], dtype=object),
    'cur_win_name': 'Hamming',  # name of current window
    #
    'Boxcar': {
        'fn_name': 'boxcar',
        'info': rectangular_info,
        'props': {
            'nenbw': 1,
            'cgain': 1,
            'bw': 1
            }
         },
    'Rectangular': {
        'fn_name': 'boxcar',
        'info': rectangular_info,
        'props': {
            'nenbw': 1,
            'cgain': 1,
            'bw': 1
            }
        },
    'Barthann': {
        'fn_name': 'barthann',
        'info':
            '''<span>
            The modified Bartlett-Hann window is a weighted combination of Bartlett
            (triangular) and Hann window and has a similar mainlobe width as those two.
            Sidelobes are asymptotically decaying, near sidelobes have a lower level
            than Bartlett and Hann windows, far sidelobes have lower levels than
            Bartlett and Hamming windows.
            </span>'''
            },
    'Bartlett': {
        'fn_name': 'bartlett',
        'info': bartlett_info,
            },
    'Blackman': {
        'fn_name': 'blackman',
        'info':
            '''<span>
            The Blackman window is used for both FIR filter design and spectral analysis.
            Compared to Hann and Hamming window, it has a wider main lobe (less sharp
            transition between pass and stop band / worse frequency resolution)
            and lower sidelobe levels (improved stopband rejection / less leakage of
            high-frequency interferers).<br /><br />

            The Blackman window is a three term cosine window with coefficients of
            a_0 = 0.42, a1 = 0.5, a2 = 0.08. The maximum sidelobe level is -57 dB,
            sidelobes have a fall-off rate of -18 dB/dec.
            Its main lobe width is 12 &pi; / <i>N</i>.
            </span>'''
        },
    'Blackmanharris': {
        'fn_name': 'pyfda.libs.pyfda_fft_windows_lib.blackmanharris',
        'par': [{
            'name': 'L', 'name_tex': r'$L$', 'val': '4', 'list': ['4', '5', '7', '9'],
            'tooltip': '<span>Number of cosine terms</span>'}],
        'info':
            '''<span>
            The minimum 4-term Blackman-Harris window gives an excellent
            constant side-lobe suppression of more than 90 dB while keeping a
            reasonably narrow main lobe.<br /><br />

            5-, 7- and 9-term Blackman-Harris windows achieve side-lobe suppressions
            of up to 125, 180 and 230 dB.
            </span>'''
        },
    'Bohman': {
        'fn_name': 'bohman',
        'info':
            '''<span>Sidelobes of the Bohman window drop with 24 dB/oct.
            </span>'''
        },
    'Cosine': {
        'fn_name': 'cosine',
        'info':
            '''<span>
            The window is half a cosine period, shifted by &pi;/2.
            For that reason it is also known as "half-cosine" or "sine" window.
            </span>''',
        },
    'Dolph-Chebyshev': {
        'fn_name': 'chebwin',
        'par': [{
            'name': 'a', 'name_tex': r'$a$', 'val': 80, 'min': 45, 'max': 300,
            'tooltip': '<span>Side lobe attenuation in dB.</span>'}],
        'info':
            '''<span>
            This window gives the narrowest main lobe width for
            a given order <i>M</i> and sidelobe equiripple attenuation <i>a</i>,
            using Chebyshev polynomials.
            </span>''',
        },
    'DPSS': {
        'fn_name': 'dpss',
        'par': [{
             'name': 'NW', 'name_tex': r'$NW$',
             'val': 3, 'min': 0, 'max': 100,
             'tooltip':
                '<span>Standardized half bandwidth, <i>NW = BW &middot; N</i> / 2</span>'
                }],
        'info':
            '''<span>
            Digital Prolate Spheroidal Sequences (DPSS) (or Slepian
            sequences) are often used in multitaper power spectral density
            estimation. The first window in the sequence can be used to maximize
            the energy concentration in the main lobe, and is also called the
            Slepian window. <br /><br />

            The Kaiser window is an easier to calculate approximation for the
            Slepian window with &beta; = &pi; <i>NW</i> .
            </span>'''
        },
    #
    'Flattop': {
        'fn_name': 'flattop',
        'info':
            '''<span>
            Flattop windows give a very low amplitude error, that's why they are
            used frequently in spectrum analyzers and other measurement equipment.
            They are rarely used for FIR filter design.
            </span>'''

        },
    'General Gaussian': {
        'fn_name': 'general_gaussian',
        'par': [{
            'name': 'p', 'name_tex': r'$p$', 'val': 1.5, 'min': 0, 'max': 20,
            'tooltip': '<span>Shape parameter p</span>'
            },
            {
            'name': '&sigma;', 'name_tex': r'$\sigma$', 'val': 5, 'min': 0,
            'max': 100, 'tooltip': '<span>Standard deviation &sigma;</span>'
            }],
        'info':
            '''<span>
            General Gaussian window, <i>p</i> = 1 yields a Gaussian window,
            <i>p</i> = 0.5 yields the shape of a Laplace distribution.
            </span>'''
        },
    'Gauss': {
        'fn_name': 'gaussian',
        'par': [{
            'name': '&sigma;', 'name_tex': r'$\sigma$', 'val': 5, 'min': 0,
            'max': 100, 'tooltip': '<span>Standard deviation &sigma;</span>'}],
        'info':
            '''<span>
            The higher the standard deviation of Gaussian window is set,
            the lower the max. sidelobe level becomes. At the same time, the width
            of the main lobe increases.
            </span>'''
        },
    'Hamming': {
        'fn_name': 'hamming',
        'info':
            '''<span>
            The Hamming Window is used for both FIR filter design and spectral analysis.
            It has been optimized for suppression of
            the first side lobe. Compared to the Hann window, this comes at
            the cost of a worse (constant) level of higher side lobes.<br /><br />

            Mathematically, it is a two-term raised cosine
            window with non-zero endpoints (DC-offset).
            </span>'''
         },
    'Hann': {
        'fn_name': 'hann',
        'info':
            '''<span>
            The Hann (or, falsely, "Hanning") window is smooth at the
            edges. In the frequency domain this corresponds to side-lobes falling
            off with a rate of 18 dB/oct or 30 dB/dec. The first sidelobe is quite
            high (-32 dB). It is a good compromise for many applications, especially
            when higher frequency components need to be suppressed.
            <br /><br />

            Mathematically, it is the most simple two-term raised cosine
            or squared sine window.
            </span>'''
            },
    'Kaiser': {
        'fn_name': 'kaiser',
        'par': [{
            'name': '&beta;', 'name_tex': r'$\beta$',
            'val': 10, 'min': 0, 'max': 30,
            'tooltip':
                '<span>Shape parameter; lower values reduce  main lobe width, '
                'higher values reduce side lobe level, typ. in the range '
                '5 ... 20.</span>'}],
        'info':
            '''<span>
            The Kaiser window is a very good approximation to the
            Digital Prolate Spheroidal Sequence (DPSS), or Slepian window,
            which maximizes the energy in the main lobe of the window relative
            to the total energy.
            </span>'''
        },
    'Nuttall': {
        'fn_name': 'nuttall'
        },
    'Parzen': {
        'fn_name': 'parzen',
        'info':
            '''<span>
            The Parzen window is a 4th order B-spline window whose sidelobes
            fall off with -24 dB/oct.
            <br/ ><br />

            It can be constructed by convolving a rectangular window four times
            (or multiplying its frequency response four times).
            <br /><br />

            See also: Boxcar and Triangular / Bartlett windows.
            </span>'''
            },
    'Slepian': {
        'fn_name': 'slepian',
        'par': [{
             'name': 'BW', 'name_tex': r'$BW$',
             'val': 0.3, 'min': 0, 'max': 100,
             'tooltip': '<span>Bandwidth</span>'}],
        'info':
            '''<span>
            Used to maximize the energy concentration in the main lobe.
            Also called the digital prolate spheroidal sequence (DPSS).
            <br /><br />

            See also: Kaiser window.
            </span>'''
        },
    'Triangular': {
        'fn_name': 'triang',
        'info': bartlett_info
        },
    'Tukey': {
        'fn_name': 'tukey',
        'par': [{
            'name': '&alpha;', 'name_tex': r'$\alpha$', 'val': 0.25, 'min': 0, 'max': 1,
                    'tooltip': '<span>Shape parameter (see window tool tipp)</span>'}],
        'info':
            '''<span>
            Also known as "tapered cosine window", this window is constructed from a
            rectangular window whose edges are tapered with cosine functions. The shape
            factor &alpha; defines the fraction of the window inside the cosine tapered
            region. Hence, &alpha; = 0 returns a rectangular window, &alpha; = 1 a
            Hann window.
            <br /><br />

            Tukey windows are used a.o. for analyzing transient data containing short
            bursts. It is the default window for scipy.signal.spectrogram with
            &alpha; = 0.25). Amplitudes of transient events are less likely to be
            altered by this window than e.g. by a Hann window.
            </span>'''
        },
    'Ultraspherical': {
        'fn_name': 'pyfda.libs.pyfda_fft_windows_lib.ultraspherical',
        'par': [{
            'name': '&mu;', 'name_tex': r'$\mu',
            'val': 0.5, 'min': -0.5, 'max': 10,
            'tooltip': '<span>Shape parameter &mu; or &alpha;</span>'
            },
            {
            'name': 'x0', 'name_tex': r'$x_0$',
            'val': 1, 'min': -10, 'max': 10,
            'tooltip': '<span>Amplitude</span>'}
             ],
        'info':
            '''<span>
            Ultraspherical or Gegenbauer window, <i>p</i> = 1 yields a Gaussian
            window, <i>p</i> = 0.5 yields the shape of a Laplace distribution.

            As this is a three-parameter window (<i>N</i>, &mu;,)
            </span>''',
        }
    }


# ------------------------------------------------------------------------------
def get_valid_windows_list(win_names_list=[], win_dict={}):
    """
    Extract the list of all the keys from `win_dict` that define a
    window and are contained in the list of window names 'win_names_list'.
    This is verified by checking whether the key in `win_dict` has a dict
    as a value with the key `fn_name` and the window function as a value.
    When `win_dict` is empty, use the global `all_windows_dict`.

    When `win_names_list` is empty, return all valid window names from `all_windows_dict`.

    All window names in 'win_names_list' without a corresponding key in `all_windows_dict`
    raise a warning.

    The result is a alphabetically sorted (on the lower-cased names)
    list containing the valid window names (strings).

    This list can be used e.g. for initialization of a combo box.

    Parameter
    ---------
    win_names_list: list of str
        A list of window names defining the windows available in the constructed
        instance, a subset of all the windows defined in `all_windows_dict`

    win_dict: dict

    Returns
    -------
    A validated list of window names

    """
    if not win_dict:  # empty dictionary, use global one
        win_dict = all_windows_dict

    if not win_names_list:  # empty list, extract all valid keys
        wl = [k for k in win_dict
              if type(win_dict[k]) == dict
              and "fn_name" in win_dict[k]]
    else:
        wl = [k for k in win_dict
              if k in win_names_list
              and type(win_dict[k]) == dict
              and "fn_name" in win_dict[k]]

        for wn in win_names_list:
            if wn not in wl:
                logger.warning(
                    'Ignoring window name "{}", not found in "all_windows_dict".'
                    .format(wn))

    return sorted(wl, key=lambda v: (v.lower(), v))


# ------------------------------------------------------------------------------
def get_windows_dict(win_names_list=[], cur_win_name="Rectangular"):
    """
    Return a subdictionary of a deep copy of `all_windows_dict` containing all valid
    windows for the names passed in `win_names_list`. When the latter is empty, put all
    valid windows into the returned subdictionary (which should be more or less a mutable
    deep copy of `all_windows_dict` in this case.).

    `cur_win_name` determines the initial value of the `cur_win_name` key in the
    returned dictionary.

    Parameters
    ----------
    win_names_list : list of window names (str), optional

    cur_win_name : str, optional
        Name of initial setting for `cur_win_name` value (current window name),
        default: "Rectangular"

    Returns
    -------
    dict
      A dictionary with windows, window functions, docstrings etc
    """
    awd = copy.deepcopy(all_windows_dict)
    d = {k: awd[k] for k in get_valid_windows_list(win_names_list)}
    d.update({'cur_win_name': cur_win_name, 'win': awd['win']})
    return d


# -------------------------------------------------------------------------------------
def blackmanharris(N, L, sym):
    if L == '4':
        return sig.windows.blackmanharris(N, sym)

    elif L == '5':
        """ 5 Term Cosine, 125.427 dB, NBW 2.21535 bins, 9.81016 dB gain """
        a = [3.232153788877343e-001,
             -4.714921439576260e-001,
             1.755341299601972e-001,
             -2.849699010614994e-002,
             1.261357088292677e-003]
    elif L == '7':
        """ 7 Term Cosine, 180.468 dB, NBW 2.63025 bins, 11.33355 dB gain"""
        a = [2.712203605850388e-001,
             -4.334446123274422e-001,
             2.180041228929303e-001,
             -6.578534329560609e-002,
             1.076186730534183e-002,
             -7.700127105808265e-004,
             1.368088305992921e-005]
    elif L == '9':
        """ 9 Term Cosine, 234.734 dB, NBW 2.98588 bins, 12.45267 dB gain"""
        a = [2.384331152777942e-001,
             -4.005545348643820e-001,
             2.358242530472107e-001,
             -9.527918858383112e-002,
             2.537395516617152e-002,
             -4.152432907505835e-003,
             3.685604163298180e-004,
             -1.384355593917030e-005,
             1.161808358932861e-007]
    else:
        raise Exception(
            "Undefined parameter '{0}' for order L!"
            .format(L))
        return

    return calc_cosine_window(N, sym, a)


def calc_cosine_window(N, sym, a):
    """
    Return window based on cosine functions with amplitudes specified
    by the list `a`.
    """
    if sym:
        L = N-1
    else:
        L = N
    x = np.arange(N) * 2 * np.pi / L
    win = a[0]
    for k in range(1, len(a)):
        win += a[k] * np.cos(k*x)
    return win


def ultraspherical(N, alpha=0.5, x_0=1, sym=True):
    """ The window does not work yet!
        More info: https://www.recordingblogs.com/wiki/ultraspherical-window
        and https://www.ece.uvic.ca/~andreas/RLectures/UltraSpherWinJASP.pdf
    """

    if sym:
        L = N-1
    else:
        L = N
    # x = np.arange(N) * np.pi / (N)

    geg_ev = scipy.special.eval_gegenbauer
    w0 = geg_ev(N, alpha, x_0)
    w = np.zeros(N)
    # a = 2
    # for n in range(5 + 1):
    #     x = np.linspace(-1.1, 1.1, 5001)
    #     y = eval_gegenbauer(n, a, x)
    #     plt.plot(x, y, label=r'$C_{%i}^{(2)}$' % n, zorder=-n)
    #     plt.ylim((-10,10))

    for n in range(0, N):
        w[n] = w0
        for k in range(1, N//2+1):
            w[n] += geg_ev(N, alpha, x_0 * np.cos(k*np.pi/(N+1)))\
                    * np.cos(2*n*np.pi*k/(N+1))
    #     rtn +=  np.cos(x*k)

    # w = geg_ev(N-1, alpha, x_0 * np.cos(x))
    # logger.error(W[0].dtype, len(W))
    # W = np.abs(fft.ifft(w))
    # logger.error(type(w[0].dtype), len(w))
    return w


class UserWindows(object):
    def __init__(self, parent):
        super(UserWindows, self).__init__(parent)


# =======
# see also:
# https://www.electronicdesign.com/technologies/analog/article/21798689/choose-the-right-fft-window-function-when-evaluating-precision-adcs
# https://github.com/capitanov/blackman_harris_win
# https://en.m.wikipedia.org/wiki/Window_function
# https://www.dsprelated.com/freebooks/sasp/Blackman_Harris_Window_Family.html
# https://www.mathworks.com/matlabcentral/mlc-downloads/downloads/submissions/46092/versions/3/previews/coswin.m/index.html

# Refs:
#   "A Family of Cosine-Sum Windows for High-Resolution Measurements"
#    Hans-Helge Albrecht
#    Physikalisch-Technische Bundesanstalt
#   Acoustics, Speech, and Signal Processing, 2001. Proceedings. (ICASSP '01).
#    2001 IEEE International Conference on   (Volume:5 )
#    pgs. 3081-3084

# "Tailoring of Minimum Sidelobe Cosine-Sum Windows for High-Resolution Measurements"
#   Hans-Helge Albrecht
#   Physikalisch-Technische Bundesanstalt (PTB), Berlin, Germany
#   The Open Signal Processing Journal, 2010, 3, pp. 20-29

# Heinzel G. et al.,
# "Spectrum and spectral density estimation by the Discrete Fourier transform (DFT),
# including a comprehensive list of window functions and some new flat-top windows",
# February 15, 2002
# https://holometer.fnal.gov/GH_FFT.pdf


# =============================================================================
class QFFTWinSelector(QWidget):
    # those signals are class variables, shared between instances for more than one
    # instance. This is not a problem as signals are distinguished by the attached
    # dict with the payload
    sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outgoing

    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent, win_dict):
        super(QFFTWinSelector, self).__init__(parent)

        self.win_dict = win_dict
        self.err = False  # error flag for window calculation
        self._construct_UI()
        self.set_window_name()  # initialize win_dict
        self.ui2dict_win()

    # --------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the widget one hierarchy higher to update
        the widgets from the dictionary

        """
        # logger.debug("SIG_RX:\n{0}".format(pprint_log(dict_sig)))

        if dict_sig['id'] == id(self):
            return  # signal has been emitted from same instance

        elif 'view_changed' in dict_sig:
            if dict_sig['view_changed'] == 'fft_win_par':
                self.dict2ui_params()
            elif dict_sig['view_changed'] == 'fft_win_type':
                self.dict2ui()

    # --------------------------------------------------------------------------
    def _construct_UI(self):
        """
        Create the FFT window selection widget, consisting of:
        - combobox for windows
        - 0 or more parameter fields
        """
        # FFT window type
        self.cmb_win_fft = QComboBox(self)
        self.cmb_win_fft.addItems(get_valid_windows_list(win_dict=self.win_dict))
        self.cmb_win_fft.setToolTip("FFT window type.")
        qset_cmb_box(self.cmb_win_fft, self.win_dict['cur_win_name'])

        # Variant of FFT window type (not implemented yet)
        self.cmb_win_fft_variant = QComboBox(self)
        self.cmb_win_fft_variant.setToolTip("FFT window variant.")
        self.cmb_win_fft_variant.setVisible(False)

        # First numeric parameter for FFT window
        self.lbl_win_par_0 = QLabel("Param1")
        self.led_win_par_0 = QLineEdit(self)
        self.led_win_par_0.setText("1")
        self.led_win_par_0.setObjectName("ledWinPar1")
        self.cmb_win_par_0 = QComboBox(self)

        # Second numeric parameter for FFT window
        self.lbl_win_par_1 = QLabel("Param2")
        self.led_win_par_1 = QLineEdit(self)
        self.led_win_par_1.setText("2")
        self.led_win_par_1.setObjectName("ledWinPar2")
        self.cmb_win_par_1 = QComboBox(self)

        layH_main = QHBoxLayout(self)
        layH_main.addWidget(self.cmb_win_fft)
        layH_main.addWidget(self.cmb_win_fft_variant)
        layH_main.addWidget(self.lbl_win_par_0)
        layH_main.addWidget(self.led_win_par_0)
        layH_main.addWidget(self.cmb_win_par_0)
        layH_main.addWidget(self.lbl_win_par_1)
        layH_main.addWidget(self.led_win_par_1)
        layH_main.addWidget(self.cmb_win_par_1)

        layH_main.setContentsMargins(*params['wdg_margins'])  # (left, top, right, bottom)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # careful! currentIndexChanged passes an integer (the current index)
        # to update_win
        self.cmb_win_fft.currentIndexChanged.connect(self.ui2dict_win_emit)
        self.led_win_par_0.editingFinished.connect(self.ui2dict_params)
        self.led_win_par_1.editingFinished.connect(self.ui2dict_params)
        self.cmb_win_par_0.currentIndexChanged.connect(self.ui2dict_params)
        self.cmb_win_par_1.currentIndexChanged.connect(self.ui2dict_params)

# ------------------------------------------------------------------------------
    def set_window_name(self, win_name: str = "") -> bool:
        """
        Select and set a window function object from its name `win_name` and update the
        `win_dict` dictionary correspondingly with:

        win_dict['cur_win_name']        # win_name: new current window name (str)
        win_dict['win']                 # []: clear window function array (empty list)
        win_dict[win_name]['win_fnct']  # function object
        win_dict[win_name]['n_par']     # number of parameters (int)

        The above is only updated when the window type has been changed compared to
        `win_dict['cur_win_name']` !

        Parameters
        ----------
        win_name : str
            Name of the window, which will be looked up in `all_windows_dict`. If it is
            "", use `self.win_dict['cur_win_name']` instead

        Returns
        -------
        win_err : bool
            Error flag; `True` when `win_name` could not be resolved
        """
        if win_name == "":
            win_name = self.win_dict['cur_win_name']

        elif win_name not in self.win_dict:
            logger.warning(
                f'Unknown window name "{win_name}", using rectangular window instead.')
            win_name = "Rectangular"

        # operate with the window specific sub-dictionary `win_dict[win_name]`
        # dictionary in the following
        d = self.win_dict[win_name]
        fn_name = d['fn_name']

        if 'par' in d:
            n_par = len(d['par'])
        else:
            n_par = 0

        # --------------------------------------
        # get attribute fn_name from submodule (default: sig.windows) and
        # return the desired window function:
        win_err = False
        mod_fnct = fn_name.split('.')  # try to split fully qualified name at "."
        fnct = mod_fnct[-1]  # last / rightmost part = function name
        if len(mod_fnct) == 1:
            # only one element, no module given -> use scipy.signal.windows
            win_fnct = getattr(sig.windows, fnct, None)
            if not win_fnct:
                logger.error(f'No window function "{fn_name}" in scipy.signal.windows, '
                            'using rectangular window instead!')
                win_err = True
        else:
            # extract module name from fully qualified name, starting with first /
            # leftmost part of string to the last '.'
            mod_name = fn_name[:fn_name.rfind(".")]
            try:
                mod = importlib.import_module(mod_name)
                win_fnct = getattr(mod, fnct, None)
            except ImportError:  # no valid module
                logger.error(f'Found no valid module "{mod_name}", '
                            'using rectangular window instead!')
                win_err = True
            except NameError:
                logger.error(f'Found no valid window function "{fn_name}", '
                            'using rectangular window instead!')
                win_err = True

        if win_err:
            win_fnct = getattr(sig.windows, 'boxcar', None)
            win_name = "Rectangular"
            n_par = 0

        self.win_dict.update({'cur_win_name': win_name, 'win': []})
        self.win_dict[win_name].update({'win_fnct': win_fnct, 'n_par': n_par})

        return win_err  # error flag, UI (window combo box) needs to be updated

# ------------------------------------------------------------------------------
    def get_window(self, N: int, win_name: str = None, sym: bool = False,
                   clear_cache: bool = False) -> np.array:
        """
        Calculate or retrieve from cache the selected window function with `N` points.

        Parameters
        ----------
        N : int
            Number of data points

        win_name : str, optional
            Name of the window. If specified (default is None), this will be used to
            obtain the window function, its parameters and tool tipps etc. via
            `set_window_name()`. If not, the previous setting are used. If window
            and number of data points are unchanged, the window is retrieved from
            `self.win_dict['win']` instead of recalculating it.

            If some kind of error occurs during calculation of the window, a rectangular
            window is used as a fallback and the class attribute `self.err` is
            set to `True`.

        sym : bool, optional
            When True, generate a symmetric window for filter design.
            When False (default), generate a periodic window for spectral analysis.

        clear_cache : bool, optional
            Clear the window cache

        Returns
        -------
        win_fnct : ndarray
            The window function with `N` data points (should be normalized to 1)
            This is also stored in `self.win_dict['win']`. Additionally, the normalized
            equivalent noise bandwidth is calculated and stored as
            `self.win_dict['nenbw']` as well as the correlated gain
            `self.win_dict['cgain']`.
        """
        N_cache = 6  # number of windows that can be cached
        win = self.win_dict['win']
        self.err = False

        if clear_cache:
            self.win_dict['win'] = []  # clear the cache
            self.win_idx = 0
        if win_name is None or win_name == self.win_dict['cur_win_name']:
            win_name = self.win_dict['cur_win_name']
            if win == []: # cache has been cleared, reset index
                self.win_idx = 0
            else:
                for i in range(len(win)):
                    if len(win[i]) == N:
                        # logger.warning(f"cache win {i} / {self.win_idx} (N = {N})")
                        return win[i] # return unchanged window function

        win_fnct = self.win_dict[win_name]['win_fnct']
        fn_name = self.win_dict[win_name]['fn_name']
        n_par = self.win_dict[win_name]['n_par']

        try:
            if fn_name == 'dpss':
                logger.info("dpss!")
                w = scipy.signal.windows.dpss(N, self.in_dict[win_name]['par'][0]['val'],
                                              sym=sym)
            elif n_par == 0:
                w = win_fnct(N, sym=sym)
            elif n_par == 1:
                w = win_fnct(N, self.win_dict[win_name]['par'][0]['val'], sym=sym)
            elif n_par == 2:
                w = win_fnct(N, self.win_dict[win_name]['par'][0]['val'],
                             self.win_dict[win_name]['par'][1]['val'], sym=sym)
            else:
                logger.error(
                    "{0:d} parameters are not supported for windows at the moment!"
                    .format(n_par))
                w = None
        except Exception as e:
            logger.error('An error occurred calculating the window function "{0}":\n{1}'
                         .format(fn_name, e))
            w = None
        if w is None:  # Fall back to rectangular window
            self.err = True
            logger.warning('Falling back to rectangular window.')
            self.set_window_name("Rectangular")
            w = np.ones(N)

        nenbw = N * np.sum(np.square(w)) / (np.square(np.sum(w)))
        cgain = np.sum(w) / N  # coherent gain / DC average

        # build a cache with window values and keep an index to replace
        # oldest entry first
        if len(win) < N_cache:
            win.append(w)
        else:
            win[self.win_idx] = w
            self.win_idx = (self.win_idx + 1) % N_cache

        self.win_dict.update({'win': win, 'nenbw': nenbw, 'cgain': cgain})

        return w

# ------------------------------------------------------------------------------
    def dict2ui(self):
        """
        The `win_dict` dictionary has been updated somewhere else, now update the window
        selection widget and make corresponding parameter widgets visible if
        `self.win_dict['cur_win_name']` is different from current combo box entry:

        - set FFT window type combobox from `self.win_dict['cur_win_name']`
        - use `ui2dict_win()` to update parameter widgets for new window type
          from `self.win_dict` without emitting a signal
        """
        if qget_cmb_box(self.cmb_win_fft, data=False) == self.win_dict['cur_win_name']:
            return
        else:
            qset_cmb_box(self.cmb_win_fft, self.win_dict['cur_win_name'], data=False)
            self.ui2dict_win()

# ------------------------------------------------------------------------------
    def dict2ui_params(self):
        """
        Set parameter values from `win_dict`
        """
        cur = qget_cmb_box(self.cmb_win_fft, data=False)
        n_par = self.win_dict[cur]['n_par']

        if n_par > 0:
            if 'list' in self.win_dict[cur]['par'][0]:
                qset_cmb_box(self.cmb_win_par_0, str(self.win_dict[cur]['par'][0]['val']))
            else:
                self.led_win_par_0.setText(str(self.win_dict[cur]['par'][0]['val']))

        if n_par > 1:
            if 'list' in self.win_dict[cur]['par'][1]:
                qset_cmb_box(self.cmb_win_par_1, str(self.win_dict[cur]['par'][1]['val']))
            else:
                self.led_win_par_1.setText(str(self.win_dict[cur]['par'][1]['val']))

# ------------------------------------------------------------------------------
    def ui2dict_params(self):
        """
        Read out window parameter widget(s) when editing is finished and
        update win_dict.

        Emit 'view_changed': 'fft_win_par'
        """
        cur = self.win_dict['cur_win_name']  # current window name / key
        self.win_dict['win'] = []  # reset the window cache

        if self.win_dict[cur]['n_par'] > 1:
            if 'list' in self.win_dict[cur]['par'][1]:
                param = qget_cmb_box(self.cmb_win_par_1, data=False)
            else:
                param = safe_eval(self.led_win_par_1.text(),
                                  self.win_dict[cur]['par'][1]['val'],
                                  return_type='float')
                if param < self.win_dict[cur]['par'][1]['min']:
                    param = self.win_dict[cur]['par'][1]['min']
                elif param > self.win_dict[cur]['par'][1]['max']:
                    param = self.win_dict[cur]['par'][1]['max']
                self.led_win_par_1.setText(str(param))
            self.win_dict[cur]['par'][1]['val'] = param

        if self.win_dict[cur]['n_par'] > 0:
            if 'list' in self.win_dict[cur]['par'][0]:
                param = qget_cmb_box(self.cmb_win_par_0, data=False)
            else:
                param = safe_eval(self.led_win_par_0.text(),
                                  self.win_dict[cur]['par'][0]['val'],
                                  return_type='float')
                if param < self.win_dict[cur]['par'][0]['min']:
                    param = self.win_dict[cur]['par'][0]['min']
                elif param > self.win_dict[cur]['par'][0]['max']:
                    param = self.win_dict[cur]['par'][0]['max']
                self.led_win_par_0.setText(str(param))
            self.win_dict[cur]['par'][0]['val'] = param

        self.emit({'view_changed': 'fft_win_par'})

# ------------------------------------------------------------------------------
    def ui2dict_win_emit(self, arg=None) -> None:
        """
        - triggered by the window type combo box
        - read FFT window type combo box and update win_dict using `set_window_name()`,
          update parameter widgets accordingly
        - emit 'view_changed': 'fft_win_type'
        """
        self.ui2dict_win()
        self.emit({'view_changed': 'fft_win_type'})

# ------------------------------------------------------------------------------
    def ui2dict_win(self) -> None:
        """
        - read FFT window type combo box and update win_dict using `set_window_name()`
        - determine number of parameters and make lineedit or combobox fields visible
        - set tooltipps and parameter values from dict
        """
        cur = qget_cmb_box(self.cmb_win_fft, data=False)
        err = self.set_window_name(cur)
        # if selected window does not exist (`err = True`) or produces errors, fall back
        # to 'cur_win_name'
        if err:
            cur = self.win_dict['cur_win_name']
            qset_cmb_box(self.cmb_win_fft, cur, data=False)

        # update visibility and values of parameter widgets:
        n_par = self.win_dict[cur]['n_par']

        self.lbl_win_par_0.setVisible(n_par > 0)
        self.led_win_par_0.setVisible(False)
        self.cmb_win_par_0.setVisible(False)

        self.lbl_win_par_1.setVisible(n_par > 1)
        self.led_win_par_1.setVisible(False)
        self.cmb_win_par_1.setVisible(False)

        if n_par > 0:
            self.lbl_win_par_0.setText(
                to_html(self.win_dict[cur]['par'][0]['name'] + " =", frmt='bi'))
            if 'list' in self.win_dict[cur]['par'][0]:
                self.led_win_par_0.setVisible(False)
                self.cmb_win_par_0.setVisible(True)
                self.cmb_win_par_0.blockSignals(True)
                self.cmb_win_par_0.clear()
                self.cmb_win_par_0.addItems(self.win_dict[cur]['par'][0]['list'])
                qset_cmb_box(self.cmb_win_par_0, str(self.win_dict[cur]['par'][0]['val']))
                self.cmb_win_par_0.setToolTip(
                    self.win_dict[cur]['par'][0]['tooltip'])
                self.cmb_win_par_0.blockSignals(False)
            else:
                self.led_win_par_0.setVisible(True)
                self.cmb_win_par_0.setVisible(False)
                self.led_win_par_0.setText(
                    str(self.win_dict[cur]['par'][0]['val']))
                self.led_win_par_0.setToolTip(
                    self.win_dict[cur]['par'][0]['tooltip'])

        if n_par > 1:
            self.lbl_win_par_1.setText(
                to_html(self.win_dict[cur]['par'][1]['name'] + " =", frmt='bi'))
            if 'list' in self.win_dict[cur]['par'][1]:
                self.led_win_par_1.setVisible(False)
                self.cmb_win_par_1.setVisible(True)
                self.cmb_win_par_1.blockSignals(True)
                self.cmb_win_par_1.clear()
                self.cmb_win_par_1.addItems(self.win_dict[cur]['par'][1]['list'])
                qset_cmb_box(self.cmb_win_par_1, str(self.win_dict[cur]['par'][1]['val']))
                self.cmb_win_par_1.setToolTip(self.win_dict[cur]['par'][1]['tooltip'])
                self.cmb_win_par_1.blockSignals(False)
            else:
                self.led_win_par_1.setVisible(True)
                self.cmb_win_par_1.setVisible(False)
                self.led_win_par_1.setText(str(self.win_dict[cur]['par'][1]['val']))
                self.led_win_par_1.setToolTip(self.win_dict[cur]['par'][1]['tooltip'])
