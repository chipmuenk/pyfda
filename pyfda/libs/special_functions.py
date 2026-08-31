"""
Library with various special functions
"""

import logging
import numpy as np
from numpy import pi, sin, cos, log10
from numpy.typing import NDArray

__all__ =  ['dB', 'lin2unit', 'unit2lin',
           'cround', 'h_mag']

logger = logging.getLogger(__name__)

# Amplitude max, min values to prevent scipy aborts
# (Linear values)
MIN_PB_AMP  = 1e-5  # min pass band ripple
MAX_IPB_AMP = 0.85  # max pass band ripple IIR
MAX_FPB_AMP = 0.5  # max pass band ripple FIR
MIN_SB_AMP  = 1e-6  # max stop band attenuation
MAX_ISB_AMP = 0.65  # min stop band attenuation IIR
MAX_FSB_AMP = 0.45  # min stop band attenuation FIR

# ======================================================================
def db(lin: float | NDArray, power: bool = False) -> float | NDArray:
    """
    Calculate dB from linear value. If power = True, calculate 10 log ...,
    else calculate 20 log ...
    """
    if power:
        return 10. * np.log10(lin)

    return 20 * np.log10(lin)


# ------------------------------------------------------------------------------
def lin2unit(lin_value: float, filt_type: str, amp_label: str,
             unit: str = 'dB') -> float:
    r"""
    Convert linear amplitude specification to dB or W, depending on filter
    type ('FIR' or 'IIR') and whether the specifications belong to passband
    or stopband. This is determined by checking whether amp_label contains
    the strings 'PB' or 'SB' :

    - Passband:
        .. math::

            \\text{IIR:}\quad A_{dB} &= -20 \log_{10}(1 - lin\_value)

            \\text{FIR:}\quad A_{dB} &=  20 \log_{10}\\frac{1 + lin\_value}{1 - lin\_value}

    - Stopband:
        .. math::

            A_{dB} = -20 \log_{10}(lin\_value)

    Returns the result as a float.
    """
    if unit == 'dB':
        if "PB" in amp_label:  # passband
            if filt_type == 'IIR':
                unit_value = -20 * log10(1. - lin_value)
            else:
                unit_value = 20 * log10((1. + lin_value)/(1 - lin_value))
        else:  # stopband
            unit_value = -20 * log10(lin_value)
    elif unit == 'W':
        unit_value = lin_value * lin_value
    else:
        unit_value = lin_value

    return unit_value


# ------------------------------------------------------------------------------
def unit2lin(unit_value: float, filt_type: str, amp_label: str,
             unit: str = 'dB') -> float:
    r"""
    Convert amplitude specification in dB or W to linear specs:

    - Passband:
        .. math::

            \\text{IIR:}\quad A_{PB,lin} &= 1 - 10 ^{-unit\_value/20}

            \\text{FIR:}\quad A_{PB,lin} &= \\frac{10^{unit\_value/20}-1}{10^{unit\_value/20} + 1}

    - Stopband:
        .. math::
            A_{SB,lin} = -10 ^ {-unit\_value/20}

    Returns the result as a float.
    """
    msg = ""  # string for error message
    if np.iscomplex(unit_value) or unit_value < 0:
        unit_value = abs(unit_value)
        msg = "negative or complex, "

    if unit == 'dB':
        try:
            if "PB" in amp_label:  # passband
                if filt_type == 'IIR':
                    lin_value = 1. - 10.**(-unit_value / 20.)
                else:
                    lin_value = (10.**(unit_value / 20.) - 1)\
                        / (10.**(unit_value / 20.) + 1)
            else:  # stopband
                lin_value = 10.**(-unit_value / 20)

        except OverflowError:
            msg += "way "
            lin_value = 10  # definitely too large, will be limited in next section

    elif unit == 'W':
        lin_value = np.sqrt(unit_value)
    else:
        lin_value = unit_value

    # check limits to avoid errors during filter design
    if "PB" in amp_label:  # passband
        if lin_value < MIN_PB_AMP:
            lin_value = MIN_PB_AMP
            msg += "too small, "
        if filt_type == 'IIR':
            if lin_value > MAX_IPB_AMP:
                lin_value = MAX_IPB_AMP
                msg += "too large, "
        elif filt_type == 'FIR':
            if lin_value > MAX_FPB_AMP:
                lin_value = MAX_FPB_AMP
                msg += "too large, "

    else:  # stopband
        if lin_value < MIN_SB_AMP:
            lin_value = MIN_SB_AMP
            msg += "too small, "
        if filt_type == 'IIR':
            if lin_value > MAX_ISB_AMP:
                lin_value = MAX_ISB_AMP
                msg += "too large, "
        elif filt_type == 'FIR':
            if lin_value > MAX_FSB_AMP:
                lin_value = MAX_FSB_AMP
                msg += "too large, "

    if msg:
        logger.warning(
            "Amplitude spec for %s is %s using %.4g %s instead.", amp_label, msg,
            lin2unit(lin_value, filt_type=filt_type, amp_label=amp_label, unit=unit), unit)
    return lin_value

# ------------------------------------------------------------------------------
def cround(x: NDArray | complex | float, n_dig: int = 0) -> NDArray | complex | float:
    """
    Round real or complex numbers to n_dig digits. If n_dig == 0, don't round at all,
    just convert complex numbers with an imaginary part very close to zero to
    real.
    """
    x = np.real_if_close(x, 1e-15)
    if n_dig > 0:
        if np.iscomplex(x):
            x = np.complex(np.around(x.real, n_dig), np.around(x.imag, n_dig))
        else:
            x = np.around(x, n_dig)
    return x

# ------------------------------------------------------------------------------
def h_mag(num: NDArray, den: NDArray, z: NDArray, h_max: float, h_min: float | None = None,
          log: bool = False, div_by_0: str = 'ignore') -> NDArray:
    r"""
    Calculate `\|H(z)\|` at the complex frequency(ies) `z` (scalar or
    array-like).  The function `H(z)` is given in polynomial form with numerator and
    denominator. When ``log == True``, :math:`20 \log_{10} (|H(z)|)` is returned.

    The result is clipped at h_min, h_max; clipping can be disabled by passing
    None as the argument.

    Parameters
    ----------
    num : array-like (1D)
        The numerator polynome of H(z).
    den : array-like (1D)
        The denominator polynome of H(z).
    z : float or array-like (1D)
        The complex frequency(ies) where `H(z)` is to be evaluated
    h_max : float
        The maximum value to which the result is clipped
    h_min : float, optional
        The minimum value to which the result is clipped (default: None)
    log : boolean, optional
        When true, return 20 * log10 (\|H(z)\|). The clipping limits have to
        be given as dB in this case.
    div_by_0 : string, optional
        What to do when division by zero occurs during calculation (default:
        'ignore'). As the denomintor of H(z) becomes 0 at each pole, warnings
        are suppressed by default. This parameter is passed to numpy.seterr(),
        hence other valid options are 'warn', 'raise' and 'print'.

    Returns
    -------
    h_mag : array-like
        The magnitude `\|H(z)\|` for each value of `z`.
    """
    den_val = abs(np.polyval(den, z))  # evaluate denominator at z
    num_val = abs(np.polyval(num, z))  # evaluate numerator at z
    olderr = np.geterr()  # store current floating point error behaviour
    # turn off divide by zero warnings, just return 'inf':
    np.seterr(divide=div_by_0)

    H_val = np.nan_to_num(num_val / den_val)  # remove nan and inf
    if log:
        H_val = 20 * np.log10(H_val)

    np.seterr(**olderr)  # restore previous floating point error behaviour

    # clip result to h_min / h_max
    return np.clip(H_val, h_min, h_max)

# ------------------------------------------------------------------------------
def unique_roots(p, tol: float = 1e-3, magsort: bool = False,
                 rtype: str = 'min', rdist: str = 'euclidian'):
    """
    Determine unique roots and their multiplicities from a list of roots.

    Parameters
    ----------
    p : array_like
        The list of roots.
    tol : float, default tol = 1e-3
        The tolerance for two roots to be considered equal. Default is 1e-3.
    magsort: Boolean, default = False
        When magsort = True, use the root magnitude as a sorting criterium (as in
        the version used in numpy < 1.8.2). This yields false results for roots
        with similar magniudes (e.g. on the unit circle) but is signficantly
        faster for a large number of roots (factor 20 for 500 double roots.)
    rtype : {'max', 'min, 'avg'}, optional
        How to determine the returned root if multiple roots are within
        `tol` of each other.
        - 'max' or 'maximum': pick the maximum of those roots (magnitude ?).
        - 'min' or 'minimum': pick the minimum of those roots (magnitude?).
        - 'avg' or 'mean' : take the average of those roots.
        - 'median' : take the median of those roots
    dist : {'manhattan', 'euclid'}, optional
        How to measure the distance between roots: 'euclid' is the euclidian
        distance. 'manhattan' is less common, giving the
        sum of the differences of real and imaginary parts.

    Returns
    -------
    pout : list
        The list of unique roots, sorted from low to high (only for real roots).
    mult : list
        The multiplicity of each root.

    Notes
    -----
    This utility function is not specific to roots but can be used for any
    sequence of values for which uniqueness and multiplicity has to be
    determined. For a more general routine, see `numpy.unique`.

    Examples
    --------
    >>> vals = [0, 1.3, 1.31, 2.8, 1.25, 2.2, 10.3]
    >>> uniq, mult = unique_roots(vals, tol=2e-2, rtype='avg')

    Check which roots have multiplicity larger than 1:

    >>> uniq[mult > 1]
    array([ 1.305])

    Find multiples of complex roots on the unit circle:
    >>> vals = np.roots(1,2,3,2,1)
    uniq, mult = unique_roots(vals, rtype='avg')

    Notes
    -----
    adapted from scipy.signal.signaltools.py:
    TODO: comparison of real values has several problems (5 * tol ???)
    TODO: speed improvements
    """
    # ----------------------------------------------------------------
    def cmplx_sort(p):
        """
        sort roots based on magnitude.

        from scipy.signal.signaltools.py:
        """
        p = np.asarray(p)
        if np.iscomplexobj(p):
            indx = np.argsort(abs(p))
        else:
            indx = np.argsort(p)
        return np.take(p, indx, 0), indx

    def manhattan(a, b):
        """
        Manhattan distance between a and b
        """
        return np.abs(a.real - b.real) + np.abs(a.imag - b.imag)

    def euclid(a, b):
        """
        Euclidian distance between a and b
        """
        return np.abs(a - b)
    # ---------------------------------------------------------------------

    if rtype in ['max', 'maximum']:
        comproot = np.max
    elif rtype in ['min', 'minimum']:
        comproot = np.min
    elif rtype in ['avg', 'mean']:
        comproot = np.mean
    elif rtype == 'median':
        comproot = np.median
    else:
        raise TypeError(rtype)

    if rdist in ['euclid', 'euclidian']:
        dist_roots = euclid
    elif rdist in ['rect', 'manhattan']:
        dist_roots = manhattan
    else:
        raise TypeError(rdist)

    mult = []  # initialize list for multiplicities
    pout = []  # initialize list for reduced output list of roots

    # handle scalars
    tol = abs(tol)
    p = np.atleast_1d(p)  # convert p to at least 1D array
    if len(p) == 0:
        return pout, mult

    if len(p) == 1:
        pout = p
        mult = [1]
        return pout, mult

    # handle lists / arrays
    pout = p[np.isnan(p)].tolist()  # copy nan elements to pout, convert to list
    mult = len(pout) * [1]  # generate an (empty) list with a "1" for each nan
    p = p[~np.isnan(p)]     # delete nan elements from p, convert to list

    if len(p) == 0:
        pass

    elif (np.iscomplexobj(p) and not magsort):
        while len(p):
            # calculate distance of first root against all others and itself
            # -> multiplicity is at least 1, first root is always deleted
            tolarr = np.less(dist_roots(p[0], p), tol)
            mult.append(np.sum(tolarr))  # multiplicity = number of "hits"
            pout.append(comproot(p[tolarr]))  # pick the roots within the tolerance

            p = p[~tolarr]  # and delete them
    else:
        sameroots = []  # temporary list for roots within the tolerance
        p, indx = cmplx_sort(p)
        indx = len(mult)-1
        curp = p[0] + 5 * tol  # needed to avoid "self-detection" ?
        for k in range(len(p)):
            tr = p[k]
            if abs(tr - curp) < tol:
                sameroots.append(tr)
                curp = comproot(sameroots)  # not correct for 'avg'
                                            # of multiple (N > 2) root !
                pout[indx] = curp
                mult[indx] += 1
            else:
                pout.append(tr)
                curp = tr
                sameroots = [tr]
                indx += 1
                mult.append(1)

    return np.array(pout), np.array(mult)

# #### original code ####
#    p = asarray(p) * 1.0
#    tol = abs(tol)
#    p, indx = cmplx_sort(p)
#    pout = []
#    mult = []
#    indx = -1
#    curp = p[0] + 5 * tol
#    sameroots = []
#    for k in range(len(p)):
#        tr = p[k]
#        if abs(tr - curp) < tol:
#            sameroots.append(tr)
#            curp = comproot(sameroots)
#            pout[indx] = curp
#            mult[indx] += 1
#        else:
#            pout.append(tr)
#            curp = tr
#            sameroots = [tr]
#            indx += 1
#            mult.append(1)
#    return array(pout), array(mult)

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Bandlimited versions of periodic functions
# ------------------------------------------------------------------------------
def sawtooth_bl(t: NDArray) -> NDArray:
    """
    Bandlimited sawtooth function as a direct replacement for `scipy.signal.sawtooth`.
    It is calculated by Fourier synthesis, i.e. by summing up all sine wave components
    up to the Nyquist frequency.

    By Endolith, https://gist.github.com/endolith/407991
    """
    if t.dtype.char in ['fFdD']:
        ytype = t.dtype.char
    else:
        ytype = 'd'
    y = np.zeros(t.shape, ytype)
    # Get sampling frequency from timebase
    fs = 1 / (t[1] - t[0])
    # Sum all multiple sine waves up to the Nyquist frequency:
    for h in range(1, int(fs*pi)+1):
        y += 2 / pi * -sin(h * t) / h
    return y


# ------------------------------------------------------------------------------
def triang_bl(t: NDArray) -> NDArray:
    """
    Bandlimited triangle function as a direct replacement for `scipy.signal.sawtooth(width=0.5)`.
    It is calculated by Fourier synthesis, i.e. by summing up all sine wave components up to
    the Nyquist frequency.

    By Endolith, https://gist.github.com/endolith/407991
    """
    if t.dtype.char in ['fFdD']:
        ytype = t.dtype.char
    else:
        ytype = 'd'
    y = np.zeros(t.shape, ytype)
    # Get sampling frequency from timebase
    fs = 1 / (t[1] - t[0])
    # Sum all multiple sine waves up to the Nyquist frequency:
    for h in range(1, int(fs * pi) + 1, 2):
        y += 8 / pi**2 * -cos(h * t) / h**2
    return y


# ------------------------------------------------------------------------------
def rect_bl(t: NDArray, duty: float = 0.5) -> NDArray:
    """
    Bandlimited rectangular function as a direct replacement for `scipy.signal.square`.
    It is derived from sawtooth_bl() which is calculated by Fourier synthesis, i.e.
    by summing up all sine wave components up to the Nyquist frequency.

    By Endolith, https://gist.github.com/endolith/407991
    """
    return sawtooth_bl(t - duty*2*pi) - sawtooth_bl(t) + 2*duty-1


# ------------------------------------------------------------------------------
def comb_bl(t: NDArray) -> NDArray:
    """
    Bandlimited comb function. It is calculated by Fourier synthesis, i.e.
    by summing up all cosine components up to the Nyquist frequency.

    By Endolith, https://gist.github.com/endolith/407991
    """
    if t.dtype.char in ['fFdD']:
        ytype = t.dtype.char
    else:
        ytype = 'd'
    y = np.zeros(t.shape, ytype)
    # Get sampling frequency from timebase
    # Sum all multiple sine waves up to the Nyquist frequency:
    fs = 1 / (t[1] - t[0])
    N = int(fs * pi) + 1
    for h in range(1, N):
        y += cos(h * t)
    y /= N
    return y

# ------------------------------------------------------------------------------
# Functions dealing with odd and even numbers
# ------------------------------------------------------------------------------
def round_odd(x) -> int:
    """Return the nearest odd integer from x. x can be integer or float."""
    return int(x-np.mod(x, 2)+1)


# ------------------------------------------------------------------------------
def round_even(x) -> int:
    """Return the nearest even integer from x. x can be integer or float."""
    return int(x-np.mod(x, 2))


# ------------------------------------------------------------------------------
def ceil_odd(x) -> int:
    """
    Return the smallest odd integer not less than x. x can be integer or float.
    """
    return round_odd(x+1)


# ------------------------------------------------------------------------------
def floor_odd(x) -> int:
    """
    Return the largest odd integer not larger than x. x can be integer or float.
    """
    return round_odd(x-1)


# ------------------------------------------------------------------------------
def ceil_even(x) -> int:
    """
    Return the smallest even integer not less than x. x can be integer or float.
    """
    return round_even(x+1)


# ------------------------------------------------------------------------------
def floor_even(x) -> int:
    """
    Return the largest even integer not larger than x. x can be integer or float.
    """
    return round_even(x-1)

