"""
The following are a Python only set of functions that implement
various scipy.signal functions, these allow the functions to be
used with pypy.  Many of the HDL simulations have significant
speed up (5-10x) with pypy but the scipy support in scipy is
not complete (last check many eons ago).
"""

from math import cos, pi, sin


def convolve(x, h):
    """Convolution
    """
    assert isinstance(x, (list, tuple,))
    assert isinstance(h, (list, tuple,))
    hl, h = len(h), h[::-1]
    d = [0. for _ in range(hl)]
    x = d[:-1] + x + d[:-1]
    y = [0. for _ in range(len(x) - hl + 1)]

    for ii, yy in enumerate(y):
        y[ii] = sum([xx * hh for xx, hh in zip(x[ii:ii + hl], h)])

    return y


def lowpass_ideal(fc, ntaps):
    """
    This is the same function as provided by Ingle, Proakis
    """
    alpha = (ntaps - 1) / 2
    n = range(ntaps)
    m = [(nn - alpha) for nn in n]
    wc = fc * pi
    h = [fc if mm == 0 else wc * sin(wc * mm) / (pi * wc * mm) for mm in m]
    return h, m, wc


def firwin1(ntaps, cutoff, window='hamming', ftype='low'):
    """Generate the windowed FIR coefficients.

    Args:
        ntaps (int): The number of taps (coefficients) in the filter.
        cutoff (float, tuple, list): The frequency requirements.
        window (str): window function to use.
        ftype (str): filter type: low, high, band, stop

    Returns:

    """
    if ftype.lower() in ('lp', 'low', 'lowpass',):
        h, m, fc = lowpass_ideal(cutoff, ntaps)
    else:
        raise NotImplementedError

    # Windows
    # --- [hamming] ---
    if window == 'hamming':
        w = [0.54 - 0.46 * cos((2 * pi * n) / (ntaps - 1))
             for n in range(ntaps)]  # m]
    else:
        raise NotImplementedError

    hd = [hh * ww for hh, ww in zip(h, w)]
    scale = 1 / sum(hd)
    hd = [hh * scale for hh in hd]

    return hd