# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Library with various signal processing related functions
"""
import logging
logger = logging.getLogger(__name__)

import time
import numpy as np
from numpy import pi
import scipy.signal as sig

import pyfda.libs.pyfda_lib as pyfda_lib
import pyfda.filterbroker as fb


def impz(b, a=1, FS=1, N=0, step=False):
    """
Calculate impulse response of a discrete time filter, specified by
numerator coefficients b and denominator coefficients a of the system
function H(z).

When only b is given, the impulse response of the transversal (FIR)
filter specified by b is calculated.

Parameters
----------
b :  array_like
     Numerator coefficients (transversal part of filter)

a :  array_like (optional, default = 1 for FIR-filter)
     Denominator coefficients (recursive part of filter)

FS : float (optional, default: FS = 1)
     Sampling frequency.

N :  float (optional)
     Number of calculated points.
     Default: N = len(b) for FIR filters, N = 100 for IIR filters

step : bool (optional, default False)
     return the step response instead of the impulse response

Returns
-------
hn : ndarray
    impulse or step response with length N (see above)
td : ndarray
    contains the time steps with same length as hn


Examples
--------
>>> b = [1,2,3] # Coefficients of H(z) = 1 + 2 z^2 + 3 z^3
>>> h, n = dsp_lib.impz(b)
"""
    a = np.asarray(a)
    b = np.asarray(b)

    if len(a) == 1:
        if len(b) == 1:
            raise TypeError(
                'No proper filter coefficients: len(a) = len(b) = 1 !')
        else:
            IIR = False
    else:
        if len(b) == 1:
            IIR = True
        # Test whether all elements except first are zero
        elif not np.any(a[1:]) and a[0] != 0:
            #  same as:   elif np.all(a[1:] == 0) and a[0] <> 0:
            IIR = False
        else:
            IIR = True

    if N == 0:  # set number of data points automatically
        if IIR:
            N = 100  # TODO: IIR: more intelligent algorithm needed
        else:
            N = min(len(b),  100)  # FIR: N = number of coefficients (max. 100)

    impulse = np.zeros(N)
    impulse[0] = 1.0  # create dirac impulse as input signal
    hn = np.array(sig.lfilter(b, a, impulse))  # calculate impulse response
    td = np.arange(len(hn)) / FS

    if step:  # calculate step response
        hn = np.cumsum(hn)

    return hn, td
# --------------------------------------------------------------------------
def zeros_with_val(N: int, val: float = 1., pos: int = 0):
    """
    Create a 1D array of `N` zeros where the element at position `pos` has the
    value `val`.

    Parameters
    ----------

    N: int
        number of elements
    val: scalar
        value to be inserted at position `pos` (default: 1)
    pos: int
        Position of `val` to be inserted (default: 0)

    Returns
    -------
    arr: np.ndarray
       Array with zeros except for element at position `pos`
    """
    if pos >= N or -pos > N:
        raise(IndexError)

    a = np.zeros(N, dtype=type(val))
    a[pos] = val
    return a

# ------------------------------------------------------------------------------
def zpk2array(zpk):
    """
    Test whether Z = zpk[0] and P = zpk[1] have the same length, if not, equalize
    the lengths by adding zeros.

    Test whether gain = zpk[2] is a scalar or a vector
    and whether it (or the first element of the vector) is != 0. If the gain is 0,
    set gain = 1.

    Finally, convert the gain into an vector with the same length as P and Z and
    return the the three vectors as one array.

    Parameters
    ----------
    zpk :  list, tuple or ndarray
        Zeros, poles and gain of the system

    Returns
    -----
    zpk as an array or an error string
    """
    try:
        _ = len(zpk)
    except TypeError:
        return f"zpk is a scalar or 'None'!"

    if type(zpk) in {np.ndarray, list, tuple}:
        if len(zpk) == 3:  # dimensions are ok, but poles / gain could be empty
            if np.isscalar(zpk[2]) or zpk[2] == []:
                if zpk[2] == 0:
                    zpk[2] = 1
            else:
                # logger.error(zpk[2])
                if zpk[2][0] in {0, None}:
                    zpk[2][0] = 1

        elif len(zpk) == 2:  # only poles and zeros given:
            zpk = list(zpk)
            zpk.append([1])  # set gain = 1
        elif len(zpk) == 1:  # only zeros given:
            zpk = list(zpk)
            zpk.append([0], [1])  # set pole = 0, gain = 1
        else:
            logger.error(f"'zpk' has unsuitable shape '{np.shape(zpk)}'")
            return f"'zpk' has unsuitable shape '{np.shape(zpk)}'"
    else:
        return f"'zpk' has an unsuitable type '{type(zpk)}'"

    return pyfda_lib.iter2ndarray(zpk)

# ------------------- -----------------------------------------------------------
def angle_zero(X, n_eps=1e3, mode='auto', wrapped='auto'):

    """
    Calculate angle of argument `X` when abs(X) > `n_eps` * machine resolution.
    Otherwise, zero is returned.
    """

    phi = np.angle(np.where((np.abs(X) > n_eps * np.spacing(1)), X, 0))

    return phi


# ------------------------------------------------------------------------------
def div_safe(num, den, n_eps: float = 1., i_scale: float = 1., verbose: bool = False):

    """
    Perform elementwise array division after treating singularities, meaning:

    - check whether denominator (`den`) coefficients approach zero
    - check whether numerator (`num`) or denominator coefficients are non-finite, i.e.
      one of `nan`, `ìnf` or `ninf`.

    At each singularity, replace denominator coefficient by `1` and numerator
    coefficient by `0`

    Parameters
    ----------
    num : array_like
        numerator coefficients

    den : array_like
        denominator coefficients

    n_eps : float
        n_eps * machine resolution is the limit for the denominator below which
        the ratio is set to zero. The machine resolution in numpy is given by
        `np.spacing(1)`, the distance to the nearest number which is equivalent
        to matlab's "eps".

    i_scale : float
        The scale for the index `i` for `num, den` for printing the index of
        the singularities.

    verbose : bool, optional
        whether to print  The default is False.

    Returns
    -------
    ratio : array_like
            The ratio of num and den (zero at singularities)

    """
    singular = np.where(~np.isfinite(den) | ~np.isfinite(num) |
                        (abs(den) < n_eps * np.spacing(1)))[0]

    if verbose and np.any(singular):
        logger.warning('div_safe singularity -> setting to 0 at:')
        for i in singular:
            logger.warning('i = {0} '.format(i * i_scale))

    num[singular] = 0
    den[singular] = 1

    return num / den


# ------------------------------------------------------------------------------
def validate_sos(sos):
    """
    Helper to validate a SOS input

    Copied from `scipy.signal._filter_design._validate_sos()`
    """
    sos = np.atleast_2d(sos)
    if sos.ndim != 2:
        raise ValueError('sos array must be 2D')
    n_sections, m = sos.shape
    if m != 6:
        raise ValueError('sos array must be shape (n_sections, 6)')
    if not (sos[:, 3] == 1).all():
        raise ValueError('sos[:, 3] should be all ones')
    return sos, n_sections


# ------------------------------------------------------------------------------
def group_delay(b, a=1, nfft=512, whole=False, analog=False, verbose=True,
                fs=2.*pi, sos=False, alg="scipy", n_eps=100):
    """
Calculate group delay of a discrete time filter, specified by
numerator coefficients `b` and denominator coefficients `a` of the system
function `H` ( `z`).

When only `b` is given, the group delay of the transversal (FIR)
filter specified by `b` is calculated.

Parameters
----------
b :  array_like
     Numerator coefficients (transversal part of filter)

a :  array_like (optional, default = 1 for FIR-filter)
     Denominator coefficients (recursive part of filter)

whole : boolean (optional, default : False)
     Only when True calculate group delay around
     the complete unit circle (0 ... 2 pi)

verbose : boolean (optional, default : True)
    Print warnings about frequency points with undefined group delay (amplitude = 0)
    and the time used for calculating the group delay

nfft :  integer (optional, default: 512)
     Number of FFT-points

fs : float (optional, default: fs = 2*pi)
     Sampling frequency.

alg : str (default: "scipy")
      The algorithm for calculating the group delay:
          - "scipy" The algorithm used by scipy's grpdelay,
          - "jos": The original J.O.Smith algorithm; same as in "scipy" except that
            the frequency response is calculated with the FFT instead of polyval
          - "diff": Group delay is calculated by differentiating the phase
          - "Shpakh": Group delay is calculated from second-order sections

n_eps : integer (optional, default : 100)
        Minimum value in the calculation of intermediate values before tau_g is set
        to zero.

Returns
-------
tau_g : ndarray
        group delay

w : ndarray
    angular frequency points where group delay was computed

Notes
=======

The following explanations follow [JOS]_.

**Definition and direct calculation ('diff')**

The group delay :math:`\\tau_g(\\omega)` of discrete time (DT) and continuous time
(CT) systems is the rate of change of phase with respect to angular frequency.
In the following, derivative is always meant w.r.t. :math:`\\omega`:

.. math::

    \\tau_g(\\omega)
        = -\\frac{\\partial }{\\partial \\omega}\\angle H( \\omega)
        = -\\frac{\\partial \\phi(\\omega)}{\\partial \\omega}
        = -  \\phi'(\\omega)

With numpy / scipy, the group delay can be calculated directly with

.. code-block:: python

    w, H = sig.freqz(b, a, worN=nfft, whole=whole)
    tau_g = -np.diff(np.unwrap(np.angle(H)))/np.diff(w)

The derivative can create numerical problems for e.g. phase jumps at zeros of
frequency response or when the complex frequency response becomes very small e.g.
in the stop band.

This can be avoided by calculating the group delay from the derivative of the
*logarithmic* frequency response in polar form (amplitude response and phase):

.. math::

    \\ln ( H( \\omega))
      = \\ln \\left({H_A( \\omega)} e^{j \\phi(\\omega)} \\right)
      = \\ln \\left({H_A( \\omega)} \\right) + j \\phi(\\omega)

      \\Rightarrow \\; \\frac{\\partial }{\\partial \\omega} \\ln ( H( \\omega))
      = \\frac{H_A'( \\omega)}{H_A( \\omega)} +  j \\phi'(\\omega)

where :math:`H_A(\\omega)` is the amplitude response. :math:`H_A(\\omega)` and
its derivative :math:`H_A'(\\omega)` are real-valued, therefore, the group
delay can be calculated by separating real and imginary components (and discarding
the real part):

.. math::

    \\begin{align}
    \\Re \\left\\{\\frac{\\partial }{\\partial \\omega} \\ln ( H( \\omega))\\right\\} &= \\frac{H_A'( \\omega)}{H_A( \\omega)} \\\
    \\Im \\left\\{\\frac{\\partial }{\\partial \\omega} \\ln ( H( \\omega))\\right\\} &= \\phi'(\\omega)
    \\end{align}

and hence

.. math::

      \\tau_g(\\omega) = -\\phi'(\\omega) =
      -\\Im \\left\\{ \\frac{\\partial }{\\partial \\omega}
      \\ln ( H( \\omega)) \\right\\}
      =-\\Im \\left\\{ \\frac{H'(\\omega)}{H(\\omega)} \\right\\}

Note: The last term contains the complex response :math:`H(\omega)`, not the
amplitude response :math:`H_A(\omega)`!

In the following, it will be shown that the derivative of birational functions
(like DT and CT filters) can be calculated very efficiently and from this the group
delay.


**J.O. Smith's basic algorithm for FIR filters ('scipy')**

An efficient form of calculating the group delay of FIR filters based on the
derivative of the logarithmic frequency response has been described in [JOS]_
and [Lyons08]_ for discrete time systems.

A FIR filter is defined via its polyome :math:`H(z) = \\sum_k b_k z^{-k}` and has
the following derivative:

.. math::

    \\frac{\\partial }{\\partial \\omega} H(z = e^{j \\omega T})
    = \\frac{\\partial }{\\partial \\omega} \\sum_{k = 0}^N b_k e^{-j k \\omega T}
    =  -jT \\sum_{k = 0}^{N} k b_{k} e^{-j k \\omega T}
    =  -jT H_R(e^{j \\omega T})

where :math:`H_R` is the "ramped" polynome, i.e. polynome :math:`H` multiplied
with a ramp :math:`k`, yielding

.. math::

    \\tau_g(e^{j \\omega T}) = -\\Im \\left\\{ \\frac{H'(e^{j \\omega T})}
                    {H(e^{j \\omega T})} \\right\\}
                    = -\\Im \\left\\{ -j T \\frac{H_R(e^{j \\omega T})}
                    {H(e^{j \\omega T})} \\right\\}
                    = T \\, \\Re \\left\\{\\frac{H_R(e^{j \\omega T})}
                    {H(e^{j \\omega T})} \\right\\}

scipy's grpdelay directly calculates the complex frequency response
:math:`H(e^{j\\omega T})` and its ramped function at the frequency points using
the polyval function.

When zeros of the frequency response are on or near the data points of the DFT, this
algorithm runs into numerical problems. Hence, it is neccessary to check whether
the magnitude of the denominator is less than e.g. 100 times the machine eps.
In this case, :math:`\\tau_g` is set to zero.

**J.O. Smith's basic algorithm for IIR filters ('scipy')**

IIR filters are defined by

.. math::

        H(z) = \\frac {B(z)}{A(z)} = \\frac {\\sum b_k z^k}{\\sum a_k z^k},

their group delay can be calculated numerically via the logarithmic frequency
response as well.

The derivative  of :math:`H(z)` w.r.t. :math:`\\omega` is calculated using the
quotient rule and by replacing the derivatives of numerator and denominator
polynomes with their ramp functions:

.. math::

    \\begin{align}
    \\frac{H'(e^{j \\omega T})}{H(e^{j \\omega T})}
    &= \\frac{\\left(B(e^{j \\omega T})/A(e^{j \\omega T})\\right)'}{B(e^{j \\omega T})/A(e^{j \\omega T})}
    = \\frac{B'(e^{j \\omega T}) A(e^{j \\omega T}) - A'(e^{j \\omega T})B(e^{j \\omega T})}
    { A(e^{j \\omega T}) B(e^{j \\omega T})}  \\\\
    &= \\frac {B'(e^{j \\omega T})} { B(e^{j \\omega T})}
      - \\frac { A'(e^{j \\omega T})} { A(e^{j \\omega T})}
    = -j T \\left(\\frac { B_R(e^{j \\omega T})} {B(e^{j \\omega T})} - \\frac { A_R(e^{j \\omega T})} {A(e^{j \\omega T})}\\right)
    \\end{align}

This result is substituted once more into the log. derivative from above:

.. math::

    \\begin{align}
    \\tau_g(e^{j \\omega T})
    =-\\Im \\left\\{ \\frac{H'(e^{j \\omega T})}{H(e^{j \\omega T})} \\right\\}
    &=-\\Im \\left\\{
        -j T \\left(\\frac { B_R(e^{j \\omega T})} {B(e^{j \\omega T})}
                    - \\frac { A_R(e^{j \\omega T})} {A(e^{j \\omega T})}\\right)
                     \\right\\} \\\\
        &= T \\Re \\left\\{\\frac { B_R(e^{j \\omega T})} {B(e^{j \\omega T})}
                    - \\frac { A_R(e^{j \\omega T})} {A(e^{j \\omega T})}
         \\right\\}
    \\end{align}


If the denominator of the computation becomes too small, the group delay
is set to zero.  (The group delay approaches infinity when
there are poles or zeros very close to the unit circle in the z plane.)

**J.O. Smith's algorithm for CT filters**

The same process can be applied for CT systems as well: The derivative of a CT
polynome :math:`P(s)` w.r.t. :math:`\\omega` is calculated by:

.. math::

    \\frac{\\partial }{\\partial \\omega} P(s = j \\omega)
    = \\frac{\\partial }{\\partial \\omega} \\sum_{k = 0}^N c_k (j \\omega)^k
    =  j \\sum_{k = 0}^{N-1} (k+1) c_{k+1} (j \\omega)^{k}
    =  j P_R(s = j \\omega)

where :math:`P_R` is the "ramped" polynome, i.e. its `k` th coefficient is
multiplied by the ramp `k` + 1, yielding the same form as for DT systems (but
the ramped polynome has to be calculated differently).

.. math::

    \\tau_g(\\omega) = -\\Im \\left\\{ \\frac{H'(\\omega)}{H(\\omega)} \\right\\}
                     = -\\Im \\left\\{j \\frac{H_R(\\omega)}{H(\\omega)} \\right\\}
                     = -\\Re \\left\\{\\frac{H_R(\\omega)}{H(\\omega)} \\right\\}


**J.O. Smith's improved algorithm for IIR filters ('jos')**

J.O. Smith gives the following speed and accuracy optimizations for the basic
algorithm:

    - convert the filter to a FIR filter with identical phase and group delay
      (but with different magnitude response)

    - use FFT instead of polyval to calculate the frequency response

The group delay of an IIR filter :math:`H(z) = B(z)/A(z)` can also
be calculated from an equivalent FIR filter :math:`C(z)` with the same phase
response (and hence group delay) as the original filter. This filter is obtained
by the following steps:

- The zeros of :math:`A(z)` are the poles of :math:`1/A(z)`, its phase response is
  :math:`\\angle A(z) = - \\angle 1/A(z)`.

- Transforming :math:`z \\rightarrow 1/z` mirrors the zeros at the unit circle,
  correcting the negative phase response. This can be performed numerically by "flipping"
  the order of the coefficients and multiplying by :math:`z^{-N}` where :math:`N`
  is the order of :math:`A(z)`. This operation also conjugates the coefficients (?)
  which mirrors the zeros at the real axis. This effect has to be compensated,
  yielding the polynome :math:`\\tilde{A}(z)`. It is the "flip-conjugate" or
  "Hermitian conjugate" of :math:`A(z)`.

  Frequently (e.g. in the scipy and until recently in the Matlab implementation)
  the conjugate operation is omitted which gives wrong results for complex
  coefficients.

- Finally, :math:`C(z) = B(z) \\tilde{A}(z)`:

.. math::

    C(z) = B(z)\\left[ z^{-N}{A}^{*}(1/z)\\right] = B(z)\\tilde{A}(z)

where

.. math::

    \\begin{align}
    \\tilde{A}(z) &=  z^{-N}{A}^{*}(1/z) = {a}^{*}_N + {a}^{*}_{N-1}z^{-1} + \ldots + {a}^{*}_1 z^{-(N-1)}+z^{-N}\\\\
    \Rightarrow \\tilde{A}(e^{j\omega T}) &=  e^{-jN \omega T}{A}^{*}(e^{-j\omega T}) \\\\
    \\Rightarrow \\angle\\tilde{A}(e^{j\omega T}) &= -\\angle A(e^{j\omega T}) - N\omega T
    \\end{align}


In Python, the coefficients of :math:`C(z)` are calculated efficiently by
convolving the coefficients of :math:`B(z)` and  :math:`\\tilde{A}(z)`:

.. code-block:: python

    c = np.convolve(b, np.conj(a[::-1]))

where :math:`b` and :math:`a` are the coefficient vectors of the original
numerator and denominator polynomes. The actual group delay is then calculated
from the equivalent FIR filter as described above.

Calculating the frequency response with the `np.polyval(p,z)` function at the
`NFFT` frequency points along the unit circle, :math:`z = \\exp(-j \\omega)`,
seems to be numerically less robust than using the FFT for the same task, it
is also much slower.

This measure fixes already most of the problems described for narrowband IIR
filters in scipy issues [Scipy_9310]_ and [Scipy_1175]_. In my experience, these problems
occur for all narrowband IIR response types.

**Shpak algorithm for IIR filters**

The algorithm described above is numerically efficient but not robust for
narrowband IIR filters. Especially for filters defined by second-order sections,
it is recommended to calculate the group delay using the D. J. Shpak's algorithm.

Code is available at [Endolith_5828333]_ (GPL licensed) or at [SPA]_ (MIT licensed).

This algorithm sums the group delays of the individual sections which is much
more robust as only second-order functions are involved. However, converting `(b,a)`
coefficients to SOS coefficients introduces inaccuracies.

Examples
--------
>>> b = [1,2,3] # Coefficients of H(z) = 1 + 2 z^2 + 3 z^3
>>> tau_g, td = pyfda_lib.grpdelay(b)
"""

    if not whole:
        nfft = 2*nfft
    w = fs * np.arange(0, nfft)/nfft  # create frequency vector

    tau_g = np.zeros_like(w)  # initialize tau_g

    # ----------------

    if alg == 'auto':
        if sos:
            alg = "shpak"
            if verbose:
                logger.info("Filter in SOS format, using Shpak algorithm for group delay.")

        elif fb.fil[0]['ft'] == 'IIR':
            alg = 'jos'  # TODO: use 'shpak' here as well?
            if verbose:
                logger.info("IIR filter, using J.O. Smith's algorithm for group delay.")
        else:
            alg = 'jos'
            if verbose:
                logger.info("FIR filter, using J.O. Smith's algorithm for group delay.")

    if sos and alg != "shpak":
        b, a = sig.sos2tf(b)

    time_0 = int(time.perf_counter() * 1e9)

    # ---------------------
    if alg == 'diff':
        w, H = sig.freqz(b, a, worN=nfft, whole=whole)
        # np.spacing(1) is equivalent to matlab "eps"
        singular = np.absolute(H) < n_eps * 10 * np.spacing(1)
        H[singular] = 0
        tau_g = -np.diff(np.unwrap(np.angle(H)))/np.diff(w)
        # differentiation returns one element less than its input
        w = w[:-1]

    # ---------------------
    elif alg == 'jos':
        b, a = map(np.atleast_1d, (b, a))  # when scalars, convert to 1-dim. arrays

        c = np.convolve(b, a[::-1])     # equivalent FIR polynome
                                        # c(z) = b(z) * a(1/z)*z^(-oa)
        cr = c * np.arange(c.size)      # multiply with ramp -> derivative of c wrt 1/z

        den = np.fft.fft(c, nfft)   # FFT = evaluate polynome around unit circle
        num = np.fft.fft(cr, nfft)  # and ramped polynome at NFFT equidistant points

        # Check for singularities i.e. where denominator (`den`) coefficients
        # approach zero or numerator (`num`) or denominator coefficients are
        # non-finite, i.e. `nan`, `ìnf` or `ninf`.
        singular = np.where(~np.isfinite(den) | ~np.isfinite(num) |
                            (abs(den) < n_eps * np.spacing(1)))[0]

        with np.errstate(invalid='ignore', divide='ignore'):
            # element-wise division of numerator and denominator FFTs
            tau_g = np.real(num / den) - a.size + 1

        # set group delay = 0 at each singularity
        tau_g[singular] = 0

        if verbose and np.any(singular):
            logger.warning('singularity -> setting to 0 at:')
            for i in singular:
                logger.warning('i = {0} '.format(i * fs/nfft))

        if not whole:
            nfft = nfft/2
            tau_g = tau_g[0:nfft]
            w = w[0:nfft]

        # if analog: # doesnt work yet
        #     a_b = np.convolve(a,b)
        #     if ob > 1:
        #         br_a = np.convolve(b[1:] * np.arange(1,ob), a)
        #     else:
        #         br_a = 0
        #     ar_b = np.convolve(a[1:] * np.arange(1,oa), b)

        #     num = np.fft.fft(ar_b - br_a, nfft)
        #     den = np.fft.fft(a_b,nfft)

    # ---------------------
    elif alg == "scipy":  # implementation as in scipy.signal
        w = np.atleast_1d(w)
        b, a = map(np.atleast_1d, (b, a))
        c = np.convolve(b, a[::-1])    # coefficients of equivalent FIR polynome
        cr = c * np.arange(c.size)     # and of the ramped polynome
        z = np.exp(-1j * w)            # complex frequency points around the unit circle
        den = np.polyval(c[::-1], z)   # evaluate polynome
        num = np.polyval(cr[::-1], z)  # and ramped polynome

        # Check for singularities i.e. where denominator (`den`) coefficients
        # approach zero or numerator (`num`) or denominator coefficients are
        # non-finite, i.e. `nan`, `ìnf` or `ninf`.
        singular = np.where(~np.isfinite(den) | ~np.isfinite(num) |
                            (abs(den) < n_eps * np.spacing(1)))[0]

        with np.errstate(invalid='ignore', divide='ignore'):
            # element-wise division of numerator and denominator FFTs
            tau_g = np.real(num / den) - a.size + 1

        # set group delay = 0 at each singularity
        tau_g[singular] = 0

        if verbose and np.any(singular):
            logger.warning('singularity -> setting to 0 at:')
            for i in singular:
                logger.warning('i = {0} '.format(i * fs/nfft))

        if not whole:
            nfft = nfft/2
            tau_g = tau_g[0:nfft]
            w = w[0:nfft]

    # ---------------------
    elif alg.lower() == "shpak":  # Use Shpak's algorith
        if sos:
            w, tau_g = sos_group_delayz(b, w, fs=fs)
        else:
            w, tau_g = group_delayz(b, a, w, fs=fs)

    else:
        logger.error('Unknown algorithm "{0}"!'.format(alg))
        tau_g = np.zeros_like(w)

    time_1 = int(time.perf_counter() * 1e9)
    delta_t = time_1 - time_0
    if verbose:
        logger.info(
            "grpdelay calculation ({0}): {1:.3g} ms".format(alg, delta_t/1.e6))
    return w, tau_g


# ------------------------------------------------------------------------------
def group_delayz(b, a, w, plot=None, fs=2*np.pi):
    """
    Compute the group delay of digital filter.

    Parameters
    ----------
    b : array_like
        Numerator of a linear filter.
    a : array_like
        Denominator of a linear filter.
    w : array_like
        Frequencies in the same units as `fs`.
    plot : callable
        A callable that takes two arguments. If given, the return parameters
        `w` and `gd` are passed to plot.
    fs : float, optional
        The angular sampling frequency of the digital system.

    Returns
    -------
    w : ndarray
        The frequencies at which `gd` was computed, in the same units as `fs`.
    gd : ndarray
        The group delay in seconds.
    """
    b, a = map(np.atleast_1d, (b, a))
    if len(a) == 1:
        # scipy.signal.group_delay returns gd in samples thus scaled by 1/fs
        gd = sig.group_delay((b, a), w=w, fs=fs)[1]
    else:
        sos = sig.tf2sos(b, a)
        gd = sos_group_delayz(sos, w, plot, fs)[1]
    if plot is not None:
        plot(w, gd)
    return w, gd


# ------------------------------------------------------------------------------
#
# The *_group_delayz routines and subroutines have been copied from
#
# https://github.com/spatialaudio/group-delay-of-filters
#
# committed by Nara Hahn under MIT license
#
# ------------------------------------------------------------------------------
def sos_group_delayz(sos, w, plot=None, fs=2*np.pi):
    """
    Compute group delay of digital filter in SOS format.

    Parameters
    ----------
    sos : array_like
        Array of second-order filter coefficients, must have shape
        ``(n_sections, 6)``. Each row corresponds to a second-order
        section, with the first three columns providing the numerator
        coefficients and the last three providing the denominator
        coefficients.
    w : array_like
        Frequencies in the same units as `fs`.
    plot : callable, optional
        A callable that takes two arguments. If given, the return parameters
        `w` and `gd` are passed to plot.
    fs : float, optional
        The sampling frequency of the digital system.

    Returns
    -------
    w : ndarray
        The frequencies at which `gd` was computed.
    gd : ndarray
        The group delay in seconds.
    """
    sos, n_sections = validate_sos(sos)
    if n_sections == 0:
        raise ValueError('Cannot compute group delay with no sections')
    gd = 0
    for biquad in sos:
        gd += quadfilt_group_delayz(biquad[:3], w, fs)[1]
        gd -= quadfilt_group_delayz(biquad[3:], w, fs)[1]
    if plot is not None:
        plot(w, gd)
    return w, gd


def quadfilt_group_delayz(b, w, fs=2*np.pi):
    """
    Compute group delay of 2nd-order digital filter.

    Parameters
    ----------
    b : array_like
        Coefficients of a 2nd-order digital filter.
    w : array_like
        Frequencies in the same units as `fs`.
    fs : float, optional
        The sampling frequency of the digital system.

    Returns
    -------
    w : ndarray
        The frequencies at which `gd` was computed.
    gd : ndarray
        The group delay in seconds.
    """
    W = 2 * pi * w / fs
    c1 = np.cos(W)
    c2 = np.cos(2*W)
    u0, u1, u2 = b**2  # b[0]**2, b[1]**2, b[2]**2
    v0, v1, v2 = b * np.roll(b, -1)  # b[0]*b[1], b[1]*b[2], b[2]*b[0]
    num = (u1+2*u2) + (v0+3*v1)*c1 + 2*v2*c2
    den = (u0+u1+u2) + 2*(v0+v1)*c1 + 2*v2*c2

    ratio = div_safe(num, den, n_eps=100, verbose=False)

    return w, 2 * pi / fs * ratio


def zpk_group_delay(z, p, k, w, plot=None, fs=2*np.pi):
    """
    Compute group delay of digital filter in zpk format.

    Parameters
    ----------
    z : array_like
        Zeroes of a linear filter
    p : array_like
        Poles of a linear filter
    k : scalar
        Gain of a linear filter
    w : array_like
        Frequencies in the same units as `fs`.
    plot : callable, optional
        A callable that takes two arguments. If given, the return parameters
        `w` and `gd` are passed to plot.
    fs : float, optional
        The sampling frequency of the digital system.

    Returns
    -------
    w : ndarray
        The frequencies at which `gd` was computed.
    gd : ndarray
        The group delay in seconds.
    """
    gd = 0
    for z_i in z:
        gd += zorp_group_delayz(z_i, w)[1]
    for p_i in p:
        gd -= zorp_group_delayz(p_i, w)[1]
    if plot is not None:
        plot(w, gd)
    return w, gd


def zorp_group_delayz(zorp, w, fs=1):
    """
    Compute group delay of digital filter with a single zero/pole.

    Parameters
    ----------
    zorp : complex
        Zero or pole of a 1st-order linear filter
    w : array_like
        Frequencies in the same units as `fs`.
    fs : float, optional
        The sampling frequency of the digital system.

    Returns
    -------
    w : ndarray
        The frequencies at which `gd` was computed.
    gd : ndarray
        The group delay in seconds.
    """
    W = 2 * pi * w / fs
    r, phi = np.abs(zorp), np.angle(zorp)
    r2 = r**2
    cos = np.cos(W - phi)
    return w, 2 * pi * (r2 - r*cos) / (r2 + 1 - 2*r*cos)
