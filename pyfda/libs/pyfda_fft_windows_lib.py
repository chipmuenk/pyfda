# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

import copy
import numpy as np
import scipy.signal as sig
import scipy

# import logging
# logger = logging.getLogger(__name__)

"""
Reference dictionary with available FFT windows, their function names and
their properties.

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
all_wins_dict_ref = {
    'cur_win_name': 'Hamming',  # name of current window
    #
    'Boxcar': {
        'app': {'fir', 'spec', 'stft'},
        'fn_name': 'boxcar',
        'id': 'boxcar',
        'info': rectangular_info,
        'props': {
            'nenbw': 1,
            'cgain': 1,
            'bw': 1
            }
         },
    'Rectangular': {
        'app': {'fir', 'spec'},
        'fn_name': 'boxcar',
        'id': 'rectangular',
        'info': rectangular_info,
        'props': {
            'nenbw': 1,
            'cgain': 1,
            'bw': 1
            }
        },
    'Barthann': {
        'app': {'fir', 'spec'},
        'fn_name': 'barthann',
        'id': 'barthann',
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
        'app': {'fir', 'spec', 'stft'},
        'fn_name': 'bartlett',
        'id': 'bartlett',
        'info': bartlett_info,
            },
    'Blackman': {
        'app': {'fir', 'spec'},
        'fn_name': 'blackman',
        'id': 'blackman',
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
        'app': {'fir', 'spec'},
        'fn_name': 'pyfda.libs.pyfda_fft_windows_lib.blackmanharris',
        'id': 'blackmanharris',
        'info':
            '''<span>
            The minimum 4-term Blackman-Harris window gives an excellent
            constant side-lobe suppression of more than 90 dB while keeping a
            reasonably narrow main lobe.<br /><br />

            5-, 7- and 9-term Blackman-Harris windows achieve side-lobe suppressions
            of up to 125, 180 and 230 dB.
            </span>''',
        'par': [{
            'name': 'L', 'name_tex': r'$L$', 'val': '4', 'list': ['4', '5', '7', '9'],
            'tooltip': '<span>Number of cosine terms</span>'}]
        },
    'Bohman': {
        'app': {'fir', 'spec'},
        'fn_name': 'bohman',
        'id': 'bohman',
        'info':
            '''<span>Sidelobes of the Bohman window drop with 24 dB/oct.
            </span>'''
        },
    'Cosine': {
        'app': {'fir', 'spec'},
        'fn_name': 'cosine',
        'id': 'cosine',
        'info':
            '''<span>
            The window is half a cosine period, shifted by &pi;/2.
            For that reason it is also known as "half-cosine" or "sine" window.
            </span>''',
        },
    'Dolph-Chebyshev': {
        'app': {'fir', 'spec'},
        'fn_name': 'chebwin',
        'id': 'chebwin',
        'info':
            '''<span>
            This window gives the narrowest main lobe width for
            a given order <i>M</i> and sidelobe equiripple attenuation <i>a</i>,
            using Chebyshev polynomials.
            </span>''',
        'par': [{
            'name': 'a', 'name_tex': r'$a$', 'val': 80, 'min': 45, 'max': 300,
            'tooltip': '<span>Side lobe attenuation in dB.</span>'}]
        },
    'DPSS': {
        'app': {'fir', 'spec'},
        'fn_name': 'dpss',
        'id': 'dpss',
        'info':
            '''<span>
            Digital Prolate Spheroidal Sequences (DPSS) (or Slepian
            sequences) are often used in multitaper power spectral density
            estimation. The first window in the sequence can be used to maximize
            the energy concentration in the main lobe, and is also called the
            Slepian window. <br /><br />

            The Kaiser window is an easier to calculate approximation for the
            Slepian window with &beta; = &pi; <i>NW</i> .
            </span>''',
        'par': [{
             'name': 'NW', 'name_tex': r'$NW$',
             'val': 3, 'min': 0, 'max': 100,
             'tooltip':
                '<span>Standardized half bandwidth, <i>NW = BW &middot; N</i> / 2</span>'
                }]
        },
    #
    'Flattop': {
        'app': {'spec'},
        'fn_name': 'flattop',
        'id': 'flattop',
        'info':
            '''<span>
            Flattop windows give a very low amplitude error, that's why they are
            used frequently in spectrum analyzers and other measurement equipment.
            They are rarely used for FIR filter design.
            </span>'''

        },
    'General Gaussian': {
        'app': {'spec'},
        'fn_name': 'general_gaussian',
        'id': 'general_gaussian',
        'info':
            '''<span>
            General Gaussian window, <i>p</i> = 1 yields a Gaussian window,
            <i>p</i> = 0.5 yields the shape of a Laplace distribution.
            </span>''',
        'par': [{
            'name': 'p', 'name_tex': r'$p$', 'val': 1.5, 'min': 0, 'max': 20,
            'tooltip': '<span>Shape parameter p</span>'
            },
            {
            'name': '&sigma;', 'name_tex': r'$\sigma$', 'val': 5, 'min': 0,
            'max': 100, 'tooltip': '<span>Standard deviation &sigma;</span>'
            }]
        },
    'Gauss': {
        'app': {'spec'},
        'fn_name': 'gaussian',
        'id': 'gaussian',
        'info':
            '''<span>
            The higher the standard deviation of Gaussian window is set,
            the lower the max. sidelobe level becomes. At the same time, the width
            of the main lobe increases.
            </span>''',
        'par': [{
            'name': '&sigma;', 'name_tex': r'$\sigma$', 'val': 5, 'min': 0,
            'max': 100, 'tooltip': '<span>Standard deviation &sigma;</span>'}],
        },
    'Hamming': {
        'app': {'fir', 'spec'},
        'fn_name': 'hamming',
        'id': 'hamming',
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
        'app': {'fir', 'spec'},
        'fn_name': 'hann',
        'id': 'hann',
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
        'app': {'fir', 'spec'},
        'fn_name': 'kaiser',
        'id': 'kaiser',
        'info':
            '''<span>
            The Kaiser window is a very good approximation to the
            Digital Prolate Spheroidal Sequence (DPSS), or Slepian window,
            which maximizes the energy in the main lobe of the window relative
            to the total energy.
            </span>''',
        'par': [{
            'name': '&beta;', 'name_tex': r'$\beta$',
            'val': 10, 'min': 0, 'max': 30,
            'tooltip':
                '<span>Shape parameter; lower values reduce  main lobe width, '
                'higher values reduce side lobe level, typ. in the range '
                '5 ... 20.</span>'}],

        },
    'Nuttall': {
        'app': {'fir', 'spec'},
        'fn_name': 'nuttall',
        'id': 'nuttall'
        },
    'Parzen': {
        'app': {'fir', 'spec'},
        'fn_name': 'parzen',
        'id': 'parzen',
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
    'Triangular': {
        'app': {'fir', 'spec', 'stft'},
        'fn_name': 'triang',
        'id': 'triang',
        'info': bartlett_info
        },
    'Tukey': {
        'app': {'spec', 'stft'},
        'fn_name': 'tukey',
        'id': 'tukey',
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
            </span>''',
        'par': [{
            'name': '&alpha;', 'name_tex': r'$\alpha$', 'val': 0.25, 'min': 0, 'max': 1,
                    'tooltip': '<span>Shape parameter (see window tool tipp)</span>'}]
        },
    'Ultraspherical': {
        'app': {'fir', 'spec'},
        'fn_name': 'pyfda.libs.pyfda_fft_windows_lib.ultraspherical',
        'id': 'ultraspherical',
        'info':'''<span>
            Ultraspherical or Gegenbauer window, <i>p</i> = 1 yields a Gaussian
            window, <i>p</i> = 0.5 yields the shape of a Laplace distribution.

            As this is a three-parameter window (<i>N</i>, &mu;,)
            </span>''',
        'par': [{
            'name': '&mu;', 'name_tex': r'$\mu$',
            'val': 0.5, 'min': -0.5, 'max': 10,
            'tooltip': '<span>Shape parameter &mu; or &alpha;</span>'
            },
            {
            'name': 'x0', 'name_tex': r'$x_0$',
            'val': 1, 'min': -10, 'max': 10,
            'tooltip': '<span>Amplitude</span>'}
             ],
        }
    }


# ------------------------------------------------------------------------------
def get_valid_windows_list(win_names_list=[], win_dict={}):
    """
    Return a list of all keys (= window names) from `win_dict` that are contained in the
    list of window names 'win_names_list'. It is checked whether each key has a dict as
    a value defining the window and whether this dict has a key `fn_name` specifying
    the fully qualified name of the window function

    When `win_dict` is empty, use the global `all_wins_dict_ref` instead.

    When `win_names_list` is empty, return all valid window names.

    All window names in 'win_names_list' without a corresponding key in the windows dict
    raise a warning.

    The result is a alphabetically sorted (on the lower-cased names)
    list containing the valid window names (strings).

    This list can be used e.g. for initialization of a combo box.

    Parameter
    ---------
    win_names_list: list of str
        A list of window names defining the windows available in the constructed
        instance, a subset of all the windows defined in `all_wins_dict_ref`

    win_dict: dict

    Returns
    -------
    A validated list of str with window names

    """
    if not win_dict:  # empty dictionary, use global one
        win_dict = all_wins_dict_ref

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
                    f'Ignoring window name "{wn}", not found in "all_wins_dict_ref".')

    return sorted(wl, key=lambda v: (v.lower(), v))


# ------------------------------------------------------------------------------
def construct_all_wins_dict(win_names_list=[], cur_win_name="Rectangular"):
    """
    Return a deep copy of `all_wins_dict_ref` with only the keys from `win_names_list`
    that specify valid windows. When the latter is empty, put all valid windows from
    `all_wins_dict_ref` into the returned subdictionary (which should be a deep copy of
    `all_wins_dict_ref` in this case).

    `cur_win_name` sets the initial value of the `'cur_win_name'` key in the
    returned dictionary.

    Parameters
    ----------
    win_names_list : list of window names (str), optional

    cur_win_name : str, optional
        Name of initial setting for `cur_win_name` value (current window name),
        default: "Rectangular"

    Returns
    -------
    win_dict: dict
        A dictionary with windows, window functions, docstrings etc
    """
    awd = copy.deepcopy(all_wins_dict_ref)
    all_wins_dict = {k: awd[k] for k in get_valid_windows_list(win_names_list)}
    all_wins_dict.update({'cur_win_name': cur_win_name})
    return all_wins_dict


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

