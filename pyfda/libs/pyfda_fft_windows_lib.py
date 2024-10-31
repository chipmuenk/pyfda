# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

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
    12 dB/oct. or 40 dB/dec., the min. side lobe suppression is 26 dB.<br /><br />

    It can be constructed as the convolution of two rectangular windows,
    hence, its Fourier transform is the product of two (periodic) sinc
    functions, decaying twice as fast as the spectrum of a rectangular window.
    </span>'''
rectangular_info =\
    '''<span>
    Boxcar or Rectangular window, best suited for analyzing <br />
    a) <b>coherent signals</b>, i.e. where the window length is an integer number of the
    signal period.<br />
    b) <b>impulses</b> where the signal length is shorter than the window
    length (e.g. for the impulse response of a FIR filter).<br />
    c) <b>noisy sinusoids with low SNR</b> because this window has the best equivalent
    noise bandwidth.<br />
    It should not be used for other signals as it has the worst sidelobe suppression
    (13 dB) of all windows. Sidelobes decay with only 6 dB/oct. or 20 dB / dec.
    <br /><br />

    When used for FIR filter design, a filter with the least square error
    is returned, created by truncating the sinc-law frequency response after
    <i>N</i> terms and transforming back to the time domain. It has the sharpest
    transition of all windowed FIR filters but the worst stop band attenuation
    and a large ripple in the passband. Attenuation in the stop band grows with
    only 6 dB/oct. or 20 dB / dec.
    </span>'''
all_wins_dict_ref = {
    'boxcar': {
        'app': ['fir', 'spec', 'stft', 'all'],
        'disp_name': 'Boxcar',
        'fn_name': 'boxcar',
        'id': 'boxcar',
        'info': rectangular_info,
        'par': [],
        'par_val': []
         },
    'rectangular': {
        'app': ['fir', 'spec', 'all'],
        'disp_name': 'Rectangular',
        'fn_name': 'boxcar',
        'id': 'rectangular',
        'info': rectangular_info,
        'par': [],
        'par_val': []
        },
    'barthann': {
        'app': ['fir', 'spec', 'all'],
        'disp_name': 'Barthann',
        'fn_name': 'barthann',
        'id': 'barthann',
        'info':
            '''<span>
            The modified Bartlett-Hann window is a weighted combination of Bartlett
            (triangular) and Hann window and has a similar mainlobe width as those two.
            Sidelobes are asymptotically decaying, near sidelobes have a lower level
            than Bartlett and Hann windows, far sidelobes have lower levels than
            Bartlett and Hamming windows.
            </span>''',
        'par': [],
        'par_val': []
            },
    'bartlett': {
        'app': ['fir', 'spec', 'stft', 'all'],
        'disp_name': 'Bartlett',
        'fn_name': 'bartlett',
        'id': 'bartlett',
        'info': bartlett_info,
        'par': [],
        'par_val': []
            },
    'blackman': {
        'app': ['fir', 'spec', 'all'],
        'disp_name': 'Blackman',
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
            </span>''',
        'par': [],
        'par_val': []
        },
    'blackmanharris': {
        'app': ['fir', 'spec', 'all'],
        'disp_name':'Blackman-Harris',
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
            'name': 'L', 'name_tex': r'$L$', 'list': ['4', '5', '7', '9'],
            'tooltip': '<span>Number of cosine terms</span>'}],
        'par_val': ['4']
        },
    'bohman': {
        'app': ['fir', 'spec', 'all'],
        'disp_name': 'Bohman',
        'fn_name': 'bohman',
        'id': 'bohman',
        'info':
            '''<span>Sidelobes of the Bohman window drop with 24 dB/oct.
            </span>''',
        'par': [],
        'par_val': []
        },
    'cosine': {
        'app': ['fir', 'spec', 'all'],
        'disp_name':  'Cosine',
        'fn_name': 'cosine',
        'id': 'cosine',
        'info':
            '''<span>
            The window is half a cosine period, shifted by &pi;/2.
            For that reason it is also known as "half-cosine" or "sine" window.
            </span>''',
        'par': [],
        'par_val': []
        },
    'chebwin': {
        'app': ['fir', 'spec', 'all'],
        'disp_name': 'Dolph-Chebyshev',
        'fn_name': 'chebwin',
        'id': 'chebwin',
        'info':
            '''<span>
            This one-parameter family of window allows choosing the (constant) sidelobe
            attenuation <i>a</i>. It gives the narrowest main lobe width for
            a given order <i>M</i> and sidelobe equiripple attenuation <i>a</i>,
            using Chebyshev polynomials.
            </span>''',
        'par': [{
            'name': 'a', 'name_tex': r'$a$', 'min': 45, 'max': 300,
            'tooltip': '<span>Side lobe attenuation in dB.</span>'}],
        'par_val': [80]
        },
    'dpss': {
        'app': ['spec', 'stft', 'fir', 'all'],
        'disp_name': 'DPSS',
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
             'name': 'NW', 'name_tex': r'$NW$', 'min': 0, 'max': 100,
             'tooltip':
                '<span>Standardized half bandwidth, <i>NW = BW &middot; N</i> / 2</span>'
                }],
        'par_val': [3]
        },
    #
    'flattop': {
        'app': ['spec'],
        'disp_name': 'Flattop',
        'fn_name': 'flattop',
        'id': 'flattop',
        'info':
            '''<span>
            Flattop windows are a family of windows with very low amplitude error /
            passband ripple used frequently in spectrum analyzers and other measurement
            equipment. Their 3dB bandwidth is approx. 2.5 times larger than that of a
            Hann window.

            They are 2nd ... 4th-order (3 ... 5 term) cosine windows.
            </span>''',
        'par': [],
        'par_val': []
        },
    'general_gaussian': {
        'app': ['spec', 'all'],
        'disp_name': 'General Gaussian',
        'fn_name': 'general_gaussian',
        'id': 'general_gaussian',
        'info':
            '''<span>
            General Gaussian window, <i>p</i> = 1 yields a Gaussian window,
            <i>p</i> = 0.5 yields the shape of a Laplace distribution.
            </span>''',
        'par': [{
            'name': 'p', 'name_tex': r'$p$', 'min': 0, 'max': 20,
            'tooltip': '<span>Shape parameter p</span>'
            },
            {
            'name': '&sigma;', 'name_tex': r'$\sigma$', 'min': 0,
            'max': 100, 'tooltip': '<span>Standard deviation &sigma;</span>'
            }],
        'par_val': [1.5, 5]
        },
    'gaussian': {
        'app': ['spec', 'all'],
        'disp_name': 'Gauss',
        'fn_name': 'gaussian',
        'id': 'gaussian',
        'info':
            '''<span>
            The Gaussian function provides the minimum time-bandwidth product and
            hence a great compromise between localization in the time and frequency
            domain.

            A higher standard deviation creates a wider Gaussian distribution in the
            time domain, yielding a narrower main lobe and higher sidelobe levels in
            the frequency domain and vice versa.

            When used as a window, it has to be truncated and no longer
            provides the minimum time-bandwidth product. For &sigma; &gt; 3, the
            truncation error is sufficiently small for most applications.

            &sigma; = (N -1)/(2a)
            </span>''',
        'par': [{
            'name': '&sigma;', 'name_tex': r'$\sigma$', 'min': 0,
            'max': 100, 'tooltip': '<span>Standard deviation &sigma;</span>'}],
        'par_val': [5]
        },
    'hamming': {
        'app': ['fir', 'spec', 'all'],
        'disp_name': 'Hamming',
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
            </span>''',
        'par': [],
        'par_val': []
         },
    'hann': {
        'app': ['fir', 'spec', 'all'],
        'disp_name': 'Hann',
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
            </span>''',
        'par': [],
        'par_val': []
            },
    'kaiser': {
        'app': ['fir', 'spec', 'all'],
        'disp_name': 'Kaiser',
        'fn_name': 'kaiser',
        'id': 'kaiser',
        'info':
            '''<span>
            The Kaiser or Kaiser-Bessel window is a family of one parameter windows
            where the &beta; parameter provides an easy control over the trade-off
            between main-lobe width and side-lobe level. High values give low
            side-lobe levels but a wide main-lobe width and vice versa.<br><br>

            It is a very good approximation to the
            Digital Prolate Spheroidal Sequence (DPSS), or Slepian window,
            which maximizes the energy in the main lobe of the window relative
            to the total energy but is easier to compute.
            </span>''',
        'par': [{
            'name': '&beta;', 'name_tex': r'$\beta$', 'min': 0, 'max': 30,
            'tooltip':
                '<span>Shape parameter; lower values reduce  main lobe width, '
                'higher values reduce side lobe level, typ. in the range '
                '5 ... 20.</span>'}],
        'par_val': [10]
        },
    'nuttall': {
        'app': ['fir', 'spec', 'all'],
        'disp_name': 'Nuttall',
        'fn_name': 'nuttall',
        'id': 'nuttall',
        'info':
            '''<span>
            A nuttall window is very similar to a four-term Blackman-Harris window.
            It gives an excellent constant side-lobe suppression of more
            than 90 dB while keeping a reasonably narrow main lobe.<br /><br /></span>''',
        'par': [],
        'par_val': []
        },
    'parzen': {
        'app': ['fir', 'spec', 'all'],
        'disp_name': 'Parzen',
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
            </span>''',
        'par': [],
        'par_val': []
            },
    'triang': {
        'app': ['fir', 'spec', 'stft', 'all'],
        'disp_name': 'Triangular',
        'fn_name': 'triang',
        'id': 'triang',
        'info': bartlett_info,
        'par': [],
        'par_val': []
        },
    'tukey': {
        'app': ['spec', 'stft'],
        'disp_name': 'Tukey',
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
            'name': '&alpha;', 'name_tex': r'$\alpha$', 'min': 0, 'max': 1,
                    'tooltip': '<span>Shape parameter (see window tool tipp)</span>'}],
        'par_val': [0.25]
        },
    'ultraspherical': {
        # for some reason, this window crashes pyfda
        'app': [],
        'disp_name': 'Ultraspherical',
        'fn_name': 'pyfda.libs.pyfda_fft_windows_lib.ultraspherical',
        'id': 'ultraspherical',
        'info':'''<span>
            Ultraspherical or Gegenbauer window, <i>&mu;</i> = 1 yields a Gaussian
            window, <i>&mu;</i> = 0.5 yields the shape of a Laplace distribution.

            This is a three-parameter window (<i>N</i>, &mu;,x_0).
            </span>''',
        'par': [{
            'name': '&mu;', 'name_tex': r'$\mu$', 'min': -0.5, 'max': 10,
            'tooltip': '<span>Shape parameter &mu; or &alpha;</span>'
            },
            {
            'name': 'x0', 'name_tex': r'$x_0$', 'min': -10, 'max': 10,
            'tooltip': '<span>Amplitude</span>'}
             ],
        'par_val': [0.5, 1]
        }
    }


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

