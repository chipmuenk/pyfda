# -*- coding: utf-8 -*-
"""
Created on Mon Apr 30 10:29:42 2012

@author: Muenker_2
"""
#
# Copyright (c) 2011 Christopher Felton, Christian Münker
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

# The following is derived from the slides presented by
# Alexander Kain for CS506/606 "Special Topics: Speech Signal Processing"
# CSLU / OHSU, Spring Term 2011.

from __future__ import division, print_function
import os, sys
import numpy as np
from numpy import pi, asarray, log10, arctan,  mod

# Specify the backend of matplotlib to use pyQT4 to avoid conflicts on systems
# that default to pyQT5 (but have pyQt4 installed as well)
import matplotlib
matplotlib.use("Qt4Agg")

import scipy.signal as sig
from scipy import __version__ as _scipy_version

from  matplotlib import patches # TODO: should not be imported here?!
#import logging
from distutils.version import LooseVersion

SOS_AVAIL = LooseVersion(_scipy_version) >= LooseVersion("0.16")
#print("scipy:", _scipy_version)

#### General functions ########################################################
# taken from
# http://matplotlib.1069221.n5.nabble.com/Figure-with-pyQt-td19095.html
def valid(path):
    """ Check whether path is valid"""
    if path and os.path.isdir(path):
        return True
    return False
 
def env(name):
    """Get value for environment variable"""
    return os.environ.get( name, '' )
 
def get_home_dir():
    """Return the user's home directory"""
    if sys.platform != 'win32':
        return os.path.expanduser( '~' )
 
    homeDir = env( 'USERPROFILE' )
    if not valid(homeDir):
        homeDir = env( 'HOME' )
        if not valid(homeDir) :
            homeDir = '%s%s' % (env('HOMEDRIVE'),env('HOMEPATH'))
            if not valid(homeDir) :
                homeDir = env( 'SYSTEMDRIVE' )
                if homeDir and (not homeDir.endswith('\\')) :
                    homeDir += '\\'
                if not valid(homeDir) :
                    homeDir = 'C:\\'
    return homeDir


def dB(lin, power = False):
    """
    Calculate dB from linear value. If power = True, calculate 10 log ...,
    else calculate 20 log ...
    """
    if power:
        return 10. * np.log10(lin)
    else:
        return 20 * np.log10(lin)
        
def lin2unit(lin, filt_type, amp_label, unit = 'dB'):
    """
    Convert linear specification to dB or W, depending on filter type ('FIR' or
    'IIR') and passband 'PB' or stopband 'SB' :
    
    - Passband: 
        A_dB = -20 * log10(1 - spec_PB) [IIR]
        A_dB = 20 log10((1 + spec_PB)/(1 - spec_PB)) [FIR]
                
    - Stopband: 
        A_dB = -20 * log10(spec_SB)
    
    Returns the value as a string.
    """     
    if unit == 'dB':
        if "PB" in amp_label: # passband
            if filt_type == 'IIR':
                result = round(-20 * log10(1. - lin), 8)
            else:
                result = round(20 * log10((1. + lin)/(1 - lin)), 8)
        else: # stopband
            result = round(-20 * log10(lin), 8)
    elif unit == 'W':
        result = lin * lin
    else:
        result = lin
            
    return result



def cround(x, n_dig = 0):
    """
    Round complex number to n_dig digits. If n_dig == 0, don't round at all,
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

def H_mag(num, den, z, H_max, H_min = None, log = False, div_by_0 = 'ignore'):
    """
    Calculate `|H(z)|` at the complex frequency(ies) `z` (scalar or
    array-like).  The function `H(z)` is given in polynomial form with numerator and
    denominator. When log = True, `20 log_10 (|H(z)|)` is returned.

    The result is clipped at H_min, H_max; clipping can be disabled by passing
    None as the argument.

    Parameters
    ----------
    num : float or array-like
        The numerator polynome of H(z).
    den : float or array-like
        The denominator polynome of H(z).
    z : float or array-like
        The complex frequency(ies) where `H(z)` is to be evaluated
    H_max : float
        The maximum value to which the result is clipped
    H_min : float, optional
        The minimum value to which the result is clipped (default: 0)
    log : boolean, optional
        When true, return 20 * log10 (|H(z)|). The clipping limits have to
        be given as dB in this case.
    div_by_0 : string, optional
        What to do when division by zero occurs during calculation (default:
        'ignore'). As the denomintor of H(z) becomes 0 at each pole, warnings
        are suppressed by default. This parameter is passed to numpy.seterr(),
        hence other valid options are 'warn', 'raise' and 'print'.

    Returns
    -------
    H_mag : float or ndarray
        The magnitude |`H(z)`| for each value of `z`.
    """

    try: len(num)
    except TypeError:
        num_val = abs(num) # numerator is a scalar
    else:
        num_val = abs(np.polyval(num, z)) # evaluate numerator at z
    try: len(den)
    except TypeError:
        den_val = abs(den) # denominator is a scalar
    else:
        den_val = abs(np.polyval(den, z)) # evaluate denominator at z

    olderr = np.geterr()  # store current floating point error behaviour
    # turn off divide by zero warnings, just return 'inf':
    np.seterr(divide = 'ignore')

    H_val = np.nan_to_num(num_val / den_val) # remove nan and inf
    if log:
        H_val = 20 * np.log10(H_val)


    np.seterr(**olderr) # restore previous floating point error behaviour

    # clip result to H_min / H_max
    return np.clip(H_val, H_min, H_max)

#----------------------------------------------
# from scipy.sig.signaltools.py:
def cmplx_sort(p):
    "sort roots based on magnitude."
    p = np.asarray(p)
    if np.iscomplexobj(p):
        indx = np.argsort(abs(p))
    else:
        indx = np.argsort(p)
    return np.take(p, indx, 0), indx

# adapted from scipy.signal.signaltools.py:
# TODO:  comparison of real values has several problems (5 * tol ???)
# TODO: speed improvements
def unique_roots(p, tol=1e-3, magsort = False, rtype='min', rdist='euclidian'):
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
    
    """

    def manhattan(a,b):
        """
        Manhattan distance between a and b
        """
        return np.abs(a.real - b.real) + np.abs(a.imag - b.imag)

    def euclid(a,b):
        """
        Euclidian distance between a and b
        """
        return np.abs(a - b)

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

    mult = [] # initialize list for multiplicities
    pout = [] # initialize list for reduced output list of roots

    tol = abs(tol)
    p = np.atleast_1d(p) # convert p to at least 1D array
    if len(p) == 0:
        return pout, mult

    elif len(p) == 1:
        pout = p
        mult = [1]
        return pout, mult

    else:
        pout = p[np.isnan(p)].tolist() # copy nan elements to pout, convert to list
        mult = len(pout) * [1] # generate an (empty) list with a "1" for each nan
        p = p[~np.isnan(p)]    # delete nan elements from p, convert to list

        if len(p) == 0:
            pass

        elif (np.iscomplexobj(p) and not magsort):
            while len(p):
                # calculate distance of first root against all others and itself
                # -> multiplicity is at least 1, first root is always deleted
                tolarr = np.less(dist_roots(p[0], p), tol)                               # assure multiplicity is at least one
                mult.append(np.sum(tolarr)) # multiplicity = number of "hits"
                pout.append(comproot(p[tolarr])) # pick the roots within the tolerance

                p = p[~tolarr]  # and delete them

        else:
            sameroots = [] # temporary list for roots within the tolerance
            p,indx = cmplx_sort(p)
            indx = len(mult)-1
            curp = p[0] + 5 * tol # needed to avoid "self-detection" ?
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

##### original code ####
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




def zplane(b=None, a=1, z=None, p=None, k =1,  pn_eps=1e-3, analog=False, plt_ax = None,
          verbose=False, style='square', anaCircleRad=0, lw=2,
          mps = 10, mzs = 10, mpc = 'r', mzc = 'b', plabel = '', zlabel = ''):
    """
    Plot the poles and zeros in the complex z-plane either from the
    coefficients (`b,`a) of a discrete transfer function `H`(`z`) (zpk = False)
    or directly from the zeros and poles (z,p) (zpk = True).

    When only b is given, an FIR filter with all poles at the origin is assumed.

    Parameters
    ----------
    b :  array_like
         Numerator coefficients (transversal part of filter)
         When b is not None, poles and zeros are determined from the coefficients
         b and a

    a :  array_like (optional, default = 1 for FIR-filter)
         Denominator coefficients (recursive part of filter)
         
    z :  array_like, default = None
         Zeros
         When b is None, poles and zeros are taken directly from z and p

    p :  array_like, default = None
         Poles

    analog : boolean (default: False)
        When True, create a P/Z plot suitable for the s-plane, i.e. suppress
        the unit circle (unless anaCircleRad > 0) and scale the plot for
        a good display of all poles and zeros.

    pn_eps : float (default : 1e-2)
         Tolerance for separating close poles or zeros
         
    plt_ax : handle to axes for plotting (default: None)
        When no axes is specified, the current axes is determined via plt.gca()

    pltLib :  string (default: 'matplotlib')
         Library for plotting the P/Z plane. Currently, only matplotlib is
         implemented. When pltLib = 'none' or when matplotlib is not
         available, only pass the poles / zeros and their multiplicity

    verbose : boolean (default: False)
        When verbose == True, print poles / zeros and their multiplicity.

    style : string (default: 'square')
        Style of the plot, for style == 'square' make scale of x- and y-
        axis equal.

    mps : integer  (default: 10)
        Size for pole marker
        
    mzs : integer (default: 10)
        Size for zero marker
        
    mpc : char (default: 'r')
        Pole marker colour
        
    mzc : char (default: 'b')
        Zero marker colour
        
    lw : integer (default:  2)
        Linewidth for unit circle

    plabel, zlabel : string (default: '')
        This string is passed to the plot command for poles and zeros and
        can be displayed by legend()


    Returns
    -------
    z, p, k : ndarray


    Notes
    -----

    """
    # TODO:
    # - polar option
    # - add keywords for size, color etc. of markers and circle -> **kwargs
    # - add option for multi-dimensional arrays and zpk data

    # make sure that all inputs are arrays
    b = np.atleast_1d(b) 
    a = np.atleast_1d(a)
    z = np.atleast_1d(z) # make sure that p, z  are arrays
    p = np.atleast_1d(p)

    if b.any(): # coefficients were specified
        zpk = False
        if len(b) < 2 and len(a) < 2:
            raise TypeError(
            'No proper filter coefficients: both b and a are scalars!')
        # The coefficients are less than 1, normalize the coeficients
        if np.max(b) > 1:
            kn = np.max(b)
            b = b / float(kn) 
        else:
            kn = 1.

        if np.max(a) > 1:
            kd = np.max(a)
            a = a / abs(kd)
        else:
            kd = 1.

        # Calculate the poles, zeros and scaling factor
        p = np.roots(a)
        z = np.roots(b)
        k = kn/kd
    elif p.any() or z.any(): # P/Z were specified
        zpk = True
    else:
        raise TypeError(
        'No proper filter coefficients: Either b,a or z,p must be specified!')          


    # find multiple poles and zeros and their multiplicities
    if len(p) < 2: # single pole, [None] or [0]
        if not p or p == 0: # only zeros, create equal number of poles at origin
            p = np.array(0,ndmin=1) # 
            num_p = np.atleast_1d(len(z))
        else:
            num_p = [1.] # single pole != 0
    else:
        #p, num_p = sig.signaltools.unique_roots(p, tol = pn_eps, rtype='avg')
        p, num_p = unique_roots(p, tol = pn_eps, rtype='avg')
#        p = np.array(p); num_p = np.ones(len(p))
    if len(z) > 0:
        z, num_z = unique_roots(z, tol = pn_eps, rtype='avg')
#        z = np.array(z); num_z = np.ones(len(z))
        #z, num_z = sig.signaltools.unique_roots(z, tol = pn_eps, rtype='avg')
    else:
        num_z = []


    ax = plt_ax#.subplot(111)
    if analog == False:
        # create the unit circle for the z-plane
        uc = patches.Circle((0,0), radius=1, fill=False,
                            color='grey', ls='solid', zorder=1)
        ax.add_patch(uc)
        if style == 'square':
            r = 1.1
            ax.axis([-r, r, -r, r], 'equal')
            ax.axis('equal')
    #    ax.spines['left'].set_position('center')
    #    ax.spines['bottom'].set_position('center')
    #    ax.spines['right'].set_visible(True)
    #    ax.spines['top'].set_visible(True)

    else: # s-plane
        if anaCircleRad > 0:
            # plot a circle with radius = anaCircleRad
            uc = patches.Circle((0,0), radius=anaCircleRad, fill=False,
                                color='grey', ls='solid', zorder=1)
            ax.add_patch(uc)
        # plot real and imaginary axis
        ax.axhline(lw=2, color = 'k', zorder=1)
        ax.axvline(lw=2, color = 'k', zorder=1)

    # Plot the zeros
    ax.scatter(z.real, z.imag, s=mzs*mzs, zorder=2, marker = 'o',
               facecolor = 'none', edgecolor = mzc, lw = lw, label=zlabel)
#        t1 = plt.plot(z.real, z.imag, 'go', ms=10, label=label)
#        plt.setp( t1, markersize=mzs, markeredgewidth=2.0,
#                  markeredgecolor=mzc, markerfacecolor='none')
    # Plot the poles
    ax.scatter(p.real, p.imag, s=mps*mps, zorder=2, marker='x',
               color=mpc, lw=lw, label=plabel)

     # Print multiplicity of poles / zeros
    for i in range(len(z)):
        if verbose == True: print('z', i, z[i], num_z[i])
        if num_z[i] > 1:
            ax.text(np.real(z[i]), np.imag(z[i]),'  (' + str(num_z[i]) +')',va = 'bottom')

    for i in range(len(p)):
        if verbose == True: print('p', i, p[i], num_p[i])
        if num_p[i] > 1:
            ax.text(np.real(p[i]), np.imag(p[i]), '  (' + str(num_p[i]) +')',va = 'bottom')

        # increase distance between ticks and labels
        # to give some room for poles and zeros
    for tick in ax.get_xaxis().get_major_ticks():
        tick.set_pad(12.)
        tick.label1 = tick._get_text1()
    for tick in ax.get_yaxis().get_major_ticks():
        tick.set_pad(12.)
        tick.label1 = tick._get_text1()

    xl = ax.get_xlim(); Dx = max(abs(xl[1]-xl[0]), 0.05)
    yl = ax.get_ylim(); Dy = max(abs(yl[1]-yl[0]), 0.05)
    ax.set_xlim((xl[0]-Dx*0.05, max(xl[1]+Dx*0.05,0)))
    ax.set_ylim((yl[0]-Dy*0.05, yl[1] + Dy*0.05))
#    print(ax.get_xlim(),ax.get_ylim())


    return z, p, k

#
#==================================================================
def impz(b, a=1, FS=1, N=0, step = False):
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

Returns
-------
hn : ndarray with length N (see above)
td : ndarray containing the time steps with same


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

    if N == 0: # set number of data points automatically
        if IIR:
            N = 100 # TODO: IIR: more intelligent algorithm needed
        else:
            N = min(len(b),  100) # FIR: N = number of coefficients (max. 100)

    impulse = np.zeros(N)
    impulse[0] =1.0 # create dirac impulse as input signal
    hn = np.array(sig.lfilter(b, a, impulse)) # calculate impulse response
    td = np.arange(len(hn)) / FS

    if step: # calculate step response
        hn = np.cumsum(hn)

    return hn, td

#==================================================================
def grpdelay(b, a=1, nfft=512, whole=False, analog=False, verbose=True, fs=2.*pi, use_scipy = True):
#==================================================================
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
    Print warnings about frequency point with undefined group delay (amplitude = 0)

nfft :  integer (optional, default: 512)
     Number of FFT-points

fs : float (optional, default: fs = 2*pi)
     Sampling frequency.


Returns
-------
tau_g : ndarray
    The group delay


w : ndarray
    The angular frequency points where the group delay was computed

Notes
-----
The group delay :math:`\\tau_g(\\omega)` of discrete and continuous time
systems is defined by

.. math::

    \\tau_g(\\omega) = -  \\phi'(\\omega)
        = -\\frac{\\partial \\phi(\\omega)}{\\partial \\omega}
        = -\\frac{\\partial }{\\partial \\omega}\\angle H( \\omega)

A useful form for calculating the group delay is obtained by deriving the
*logarithmic* frequency response in polar form as described in [JOS]_ for
discrete time systems:

.. math::

    \\ln ( H( \\omega))
      = \\ln \\left({H_A( \\omega)} e^{j \\phi(\\omega)} \\right)
      = \\ln \\left({H_A( \\omega)} \\right) + j \\phi(\\omega)

      \\Rightarrow \\; \\frac{\\partial }{\\partial \\omega} \\ln ( H( \\omega))
      = \\frac{H_A'( \\omega)}{H_A( \\omega)} +  j \\phi'(\\omega)

where :math:`H_A(\\omega)` is the amplitude response. :math:`H_A(\\omega)` and
its derivative :math:`H_A'(\\omega)` are real-valued, therefore, the group
delay can be calculated from

.. math::

      \\tau_g(\\omega) = -\\phi'(\\omega) =
      -\\Im \\left\\{ \\frac{\\partial }{\\partial \\omega}
      \\ln ( H( \\omega)) \\right\\}
      =-\\Im \\left\\{ \\frac{H'(\\omega)}{H(\\omega)} \\right\\}

The derivative of a polynome :math:`P(s)` (continuous-time system) or :math:`P(z)`
(discrete-time system) w.r.t. :math:`\\omega` is calculated by:

.. math::

    \\frac{\\partial }{\\partial \\omega} P(s = j \\omega)
    = \\frac{\\partial }{\\partial \\omega} \\sum_{k = 0}^N c_k (j \\omega)^k
    =  j \\sum_{k = 0}^{N-1} (k+1) c_{k+1} (j \\omega)^{k}
    =  j P_R(s = j \\omega)

    \\frac{\\partial }{\\partial \\omega} P(z = e^{j \\omega T})
    = \\frac{\\partial }{\\partial \\omega} \\sum_{k = 0}^N c_k e^{-j k \\omega T}
    =  -jT \\sum_{k = 0}^{N} k c_{k} e^{-j k \\omega T}
    =  -jT P_R(z = e^{j \\omega T})

where :math:`P_R` is the "ramped" polynome, i.e. its `k` th coefficient is
multiplied by `k` resp. `k` + 1.

yielding:

.. math::

    \\tau_g(\\omega) = -\\Im \\left\\{ \\frac{H'(\\omega)}{H(\\omega)} \\right\\}
    \\quad \\text{ resp. } \\quad
    \\tau_g(\\omega) = -\\Im \\left\\{ \\frac{H'(e^{j \\omega T})}
                    {H(e^{j \\omega T})} \\right\\}


where::

                    (H'(e^jwT))       (    H_R(e^jwT))        (H_R(e^jwT))
    tau_g(w) = -im  |---------| = -im |-jT ----------| = T re |----------|
                    ( H(e^jwT))       (    H(e^jwT)  )        ( H(e^jwT) )

where :math:`H(e^{j\\omega T})` is calculated via the DFT at NFFT points and
the derivative
of the polynomial terms :math:`b_k z^{-k}` using 

.. math::

    \\frac{\\partial} {\\partial \\omega} b_k e^{-jk\\omega T} = -b_k jkT e^{-jk\\omega T}.
    
This is equivalent to muliplying the polynome with a ramp `k`,
yielding the "ramped" function :math:`H_R(e^{j\\omega T})`.



For analog functions with :math:`b_k s^k` the procedure is analogous, but there is no
sampling time and the exponent is positive.



.. [JOS] Julius O. Smith III, "Numerical Computation of Group Delay" in
    "Introduction to Digital Filters with Audio Applications",
    Center for Computer Research in Music and Acoustics (CCRMA),
    Stanford University, http://ccrma.stanford.edu/~jos/filters/Numerical_Computation_Group_Delay.html, referenced 2014-04-02,

.. [Lyons] Richard Lyons, "Understanding Digital Signal Processing", 3rd Ed.,
    Prentice Hall, 2010.

Examples
--------
>>> b = [1,2,3] # Coefficients of H(z) = 1 + 2 z^2 + 3 z^3
>>> tau_g, td = pyFDA_lib.grpdelay(b)


"""
## If the denominator of the computation becomes too small, the group delay
## is set to zero.  (The group delay approaches infinity when
## there are poles or zeros very close to the unit circle in the z plane.)
##
## Theory: group delay, g(w) = -d/dw [arg{H(e^jw)}],  is the rate of change of
## phase with respect to frequency.  It can be computed as:
##
##               d/dw H(e^-jw)
##        g(w) = -------------
##                 H(e^-jw)
##
## where
##         H(z) = B(z)/A(z) = sum(b_k z^k)/sum(a_k z^k).
##
## By the quotient rule,
##                    A(z) d/dw B(z) - B(z) d/dw A(z)
##        d/dw H(z) = -------------------------------
##                               A(z) A(z)
## Substituting into the expression above yields:
##                A dB - B dA
##        g(w) =  ----------- = dB/B - dA/A
##                    A B
##
## Note that,
##        d/dw B(e^-jw) = sum(k b_k e^-jwk)
##        d/dw A(e^-jw) = sum(k a_k e^-jwk)
## which is just the FFT of the coefficients multiplied by a ramp.
##
## As a further optimization when nfft>>length(a), the IIR filter (b,a)
## is converted to the FIR filter conv(b,fliplr(conj(a))).
    if not whole:
        nfft = 2*nfft

#
    w = fs * np.arange(0, nfft)/nfft # create frequency vector
    minmag = 10. * np.spacing(1) # equivalent to matlab "eps"

#    if not use_scipy:
#        try: len(a)
#        except TypeError:
#            a = 1; oa = 0 # a is a scalar or empty -> order of a = 0
#            c = b
#            try: len(b)
#            except TypeError: print('No proper filter coefficients: len(a) = len(b) = 1 !')
#        else:
#            oa = len(a)-1               # order of denom. a(z) resp. a(s)
#            c = np.convolve(b,a[::-1])  # a[::-1] reverses denominator coeffs a
#                                        # c(z) = b(z) * a(1/z)*z^(-oa)
#        try: len(b)
#        except TypeError: b=1; ob=0     # b is a scalar or empty -> order of b = 0
#        else:
#            ob = len(b)-1             # order of b(z)
#    
#        if analog:
#            a_b = np.convolve(a,b)
#            if ob > 1:
#                br_a = np.convolve(b[1:] * np.arange(1,ob), a)
#            else:
#                br_a = 0
#            ar_b = np.convolve(a[1:] * np.arange(1,oa), b)
#    
#            num = np.fft.fft(ar_b - br_a, nfft)
#            den = np.fft.fft(a_b,nfft)
#        else:
#            oc = oa + ob                  # order of c(z)
#            cr = c * np.arange(0,oc+1) # multiply with ramp -> derivative of c wrt 1/z
#    
#            num = np.fft.fft(cr,nfft) #
#            den = np.fft.fft(c,nfft)  #
#    #
#        polebins = np.where(abs(den) < minmag)[0] # find zeros of denominator
#    #    polebins = np.where(abs(num) < minmag)[0] # find zeros of numerator
#        if np.size(polebins) > 0 and verbose:  # check whether polebins array is empty
#            print('*** grpdelay warning: group delay singular -> setting to 0 at:')
#            for i in polebins:
#                print ('f = {0} '.format((fs*i/nfft)))
#                num[i] = 0
#                den[i] = 1
#    
#        if analog: # this doesn't work yet
#            tau_g = np.real(num / den)
#        else:
#            tau_g = np.real(num / den) - oa
#    #
#        if not whole:
#            nfft = nfft/2
#            tau_g = tau_g[0:nfft]
#            w = w[0:nfft]
#    
#        return w, tau_g
#
#    else:

###############################################################################
#
# group_delay implementation copied and adapted from scipy.signal (0.16)
#
###############################################################################

    if w is None:
        w = 512

    if isinstance(w, int):
        if whole:
            w = np.linspace(0, 2 * pi, w, endpoint=False)
        else:
            w = np.linspace(0, pi, w, endpoint=False)

    w = np.atleast_1d(w)
    b, a = map(np.atleast_1d, (b, a))
    c = np.convolve(b, a[::-1])
    cr = c * np.arange(c.size)
    z = np.exp(-1j * w)
    num = np.polyval(cr[::-1], z)
    den = np.polyval(c[::-1], z)
    singular = np.absolute(den) < 10 * minmag
    if np.any(singular) and verbose:
        singularity_list = ", ".join("{0:.3f}".format(ws/(2*pi)) for ws in w[singular])
        print("pyfda_lib.py:grpdelay:\n"
            "The group delay is singular at F = [{0:s}], setting to 0".format(singularity_list)
        )

    gd = np.zeros_like(w)
    gd[~singular] = np.real(num[~singular] / den[~singular]) - a.size + 1
    return w, gd


#==================================================================
def format_ticks(ax, xy, scale=1., format="%.1f"):
#==================================================================
    """
Reformat numbers at x or y - axis. The scale can be changed to display
e.g. MHz instead of Hz. The number format can be changed as well.

Parameters
----------

ax : axes object

xy : string, either 'x', 'y' or 'xy'
     select corresponding axis (axes) for reformatting

scale : real (default: 1.)
        rescaling factor for the axes

format : string (default: %.1f)
         define C-style number formats

Returns
-------
nothing


Examples
--------
Scale all numbers of x-Axis by 1000, e.g. for displaying ms instead of s.

>>> format_ticks('x',1000.)

Two decimal places for numbers on x- and y-axis

>>> format_ticks('xy',1., format = "%.2f")

"""
    if xy == 'x' or xy == 'xy':
#        locx,labelx = ax.get_xticks(), ax.get_xticklabels() # get location and content of xticks
        locx = ax.get_xticks()
        ax.set_xticks(locx, map(lambda x: format % x, locx*scale))
    if xy == 'y' or xy == 'xy':
        locy = ax.get_yticks() # get location and content of xticks
        ax.set_yticks(locy, map(lambda y: format % y, locy*scale))

#==============================================================================

def fil_save(fil_dict, arg, format_in, sender, convert = True):
    """
    Convert between poles / zeros / gain, filter coefficients (polynomes)
    and second-order sections and store all available formats in the passed
    dictionary 'fil_dict'.
    
    Filter coefficients in FIR format (b, one dimensional) are automatically converted
    to IIR format (b, a).
    """
#    print("fil_save: arg = ", arg)
#    print("\nfil_save: shape(arg) = ", np.ndim(arg), np.shape(arg), len(arg))
#    print("\nfil_save: arg[0]:", np.shape(arg[0]))
    if format_in == 'zpk': # arg = [z,p,k]
        format_error = False
        if np.ndim(arg) == 1:
            if np.ndim(arg[0]) == 0: # list / array with z only
                z = arg
                p = np.zeros(len(z))
                k = 1
                fil_dict['zpk'] = [z, p, k]
            elif np.ndim(arg[0]) == 1: # list of lists
                if np.shape(arg)[0] == 3:
                    fil_dict['zpk'] = [arg[0], arg[1], arg[2]]
                else:
                    format_error = True
            else:
                format_error = True
        else:
            format_error = True

        if format_error:        
            raise ValueError("Unknown 'zpk' format {0}".format(arg))

    elif 'sos' in format_in and SOS_AVAIL:
            fil_dict['sos'] = arg
            
    elif format_in == 'ba': 
        if np.ndim(arg) == 1: # arg = [b]
            b = np.asarray(arg)
            a = np.zeros(len(b))
            a[0] = 1

        else: # arg = [b,a]
            b = arg[0]
            a = arg[1]

        fil_dict['ba'] = [b, a]

    else:
        raise ValueError("Unknown input format {0:s}".format(format_in))
    
    fil_dict['creator'] = (format_in, sender)
    
    if convert:    
        fil_convert(fil_dict, format_in)

#==============================================================================
def fil_convert(fil_dict, format_in):
    """
    Convert between poles / zeros / gain, filter coefficients (polynomes)
    and second-order sections and store all formats not generated by the filter
    design routine in the passed dictionary 'fil_dict'.

    Parameters
    ----------
    fil_dict :  dictionary
         filter dictionary
    
    format_in :  string or set of strings
         format(s) generated by the filter design routine. Must be one of
         'zpk': [z,p,k] where z is the array of zeros, p the array of poles and
             k is a scalar with the gain
         'ba' : [b, a] where b and a are the polynomial coefficients
         'sos' : a list of second order sections
    

    """
    
    if 'zpk' in format_in: # z, p, k have been generated,convert to other formats
        zpk = fil_dict['zpk']
        if 'ba' not in format_in:
            fil_dict['ba'] = sig.zpk2tf(zpk[0], zpk[1], zpk[2])
        if 'sos' not in format_in and SOS_AVAIL:
            try:
                fil_dict['sos'] = sig.zpk2sos(zpk[0], zpk[1], zpk[2])
            except ValueError:
                fil_dict['sos'] = 'None'
                print("WARN (pyfda_lib): Complex-valued coefficients, could not convert to SOS.")

    elif 'sos' in format_in and SOS_AVAIL:
        if 'zpk' not in format_in:
            fil_dict['zpk'] = list(sig.sos2zpk(fil_dict['sos']))
        if 'ba' not in format_in:
            fil_dict['ba'] = sig.sos2tf(fil_dict['sos'])

    elif 'ba' in format_in: # arg = [b,a]
        b, a = fil_dict['ba'][0], fil_dict['ba'][1]
        fil_dict['zpk'] = list(sig.tf2zpk(b,a))
        if SOS_AVAIL:
            try:
                fil_dict['sos'] = sig.tf2sos(b,a)
            except ValueError:
                fil_dict['sos'] = 'None'
                print("WARN (pyfda_lib): Complex-valued coefficients, could not convert to SOS.")


    else:
        raise ValueError("Unknown input format {0:s}".format(format_in))


#========================================================
"""Supplies remezord method according to Scipy Ticket #475
was: http://projects.scipy.org/scipy/ticket/475
now: https://github.com/scipy/scipy/issues/1002
https://github.com/thorstenkranz/eegpy/blob/master/eegpy/filter/remezord.py
"""

def remezord(freqs,amps,rips,Hz=1,alg='ichige'):
    """
    Filter parameter selection for the Remez exchange algorithm.

    Calculate the parameters required by the Remez exchange algorithm to
    construct a finite impulse response (FIR) filter that approximately
    meets the specified design.
    
    Parameters
    ----------
    
    freqs : list
        A monotonic sequence of band edges specified in Hertz. All elements
        must be non-negative and less than 1/2 the sampling frequency as
        given by the Hz parameter. The band edges "0" and "f_S / 2" do not
        have to be specified, hence  2 * number(amps) - 2 freqs are needed.

    amps : list
        A sequence containing the amplitudes of the signal to be
        filtered over the various bands, e.g. 1 for the passband, 0 for the
        stopband and 0.42 for some intermediate band.

    rips : list
        A list with the peak ripples (linear, not in dB!) for each band. For
        the stop band this is equivalent to the minimum attenuation.

    Hz : float
        Sampling frequency

    alg : string
        Filter length approximation algorithm. May be either 'herrmann',
        'kaiser' or 'ichige'. Depending on the specifications, some of
        the algorithms may give better results than the others.
    
    Returns
    -------
    
    numtaps,bands,desired,weight -- See help for the remez function.
    
    Examples
    --------
        We want to design a lowpass with the band edges of 40 resp. 50 Hz and a
        sampling frequency of 200 Hz, a passband peak ripple of 10%
        and a stop band ripple of 0.01 or 40 dB.
        
        >>> (L, F, A, W) = remezord([40, 50], [1, 0], [0.1, 0.01], Hz = 200)
    
    """

    # Make sure the parameters are floating point numpy arrays:
    freqs = np.asarray(freqs,'d')
    amps = np.asarray(amps,'d')
    rips = np.asarray(rips,'d')

    # Scale ripples with respect to band amplitudes:
    rips /= (amps+(amps==0.0))

    # Normalize input frequencies with respect to sampling frequency:
    freqs /= Hz

    # Select filter length approximation algorithm:
    if alg == 'herrmann':
        remlplen = remlplen_herrmann
    elif alg == 'kaiser':
        remlplen = remlplen_kaiser
    elif alg == 'ichige':
        remlplen = remlplen_ichige
    else:
        raise ValueError('Unknown filter length approximation algorithm.')

    # Validate inputs:
    if any(freqs > 0.5):
        raise ValueError('Frequency band edges must not exceed the Nyquist frequency.')
    if any(freqs < 0.0):
        raise ValueError('Frequency band edges must be nonnegative.')
    if any(rips <= 0.0):
        raise ValueError('Ripples must be nonnegative and non-zero.')
    if len(amps) != len(rips):
        raise ValueError('Number of amplitudes must equal number of ripples.')
    if len(freqs) != 2*(len(amps)-1):
        raise ValueError('Number of band edges must equal 2*(number of amplitudes-1)')


    # Find the longest filter length needed to implement any of the
    # low-pass or high-pass filters with the specified edges:
    f1 = freqs[0:-1:2]
    f2 = freqs[1::2]
    L = 0
    for i in range(len(amps)-1):
        L = max((L,
                 remlplen(f1[i],f2[i],rips[i],rips[i+1]),
                 remlplen(0.5-f2[i],0.5-f1[i],rips[i+1],rips[i])))

    # Cap the sequence of band edges with the limits of the digital frequency
    # range:
    bands = np.hstack((0.0,freqs,0.5))

    # The filter design weights correspond to the ratios between the maximum
    # ripple and all of the other ripples:
    weight = max(rips)/rips

    return [L,bands,amps,weight]

#------------------------------------------------------------------------------
#    abs = np.absolute

def round_odd(x):
    """Return the nearest odd integer from x. x can be integer or float."""
    return int(x-np.mod(x,2)+1)


def round_even(x):
    """Return the nearest even integer from x. x can be integer or float."""
    return int(x-np.mod(x,2))


def ceil_odd(x):
    """
    Return the smallest odd integer not less than x. x can be integer or float.
    """
    return round_odd(x+1)


def ceil_even(x):
    """
    Return the smallest odd integer not less than x. x can be integer or float.
    """
    return round_even(x+1)


def remlplen_herrmann(fp,fs,dp,ds):
    """
    Determine the length of the low pass filter with passband frequency
    fp, stopband frequency fs, passband ripple dp, and stopband ripple ds.
    fp and fs must be normalized with respect to the sampling frequency.
    Note that the filter order is one less than the filter length.
    
    Uses approximation algorithm described by Herrmann et al.:
    
    O. Herrmann, L.R. Raviner, and D.S.K. Chan, Practical Design Rules for
    Optimum Finite Impulse Response Low-Pass Digital Filters, Bell Syst. Tech.
    Jour., 52(6):769-799, Jul./Aug. 1973.
    """

    dF = fs-fp
    a = [5.309e-3,7.114e-2,-4.761e-1,-2.66e-3,-5.941e-1,-4.278e-1]
    b = [11.01217, 0.51244]
    Dinf = log10(ds)*(a[0]*log10(dp)**2+a[1]*log10(dp)+a[2])+ \
           a[3]*log10(dp)**2+a[4]*log10(dp)+a[5]
    f = b[0]+b[1]*(log10(dp)-log10(ds))
    N1 = Dinf/dF-f*dF+1

    return int(N1)
    #------------------------------------------------------------------------------

def remlplen_kaiser(fp,fs,dp,ds):
    """
    Determine the length of the low pass filter with passband frequency
    fp, stopband frequency fs, passband ripple dp, and stopband ripple ds.
    fp and fs must be normalized with respect to the sampling frequency.
    Note that the filter order is one less than the filter length.
    
    Uses approximation algorithm described by Kaiser:
    
    J.F. Kaiser, Nonrecursive Digital Filter Design Using I_0-sinh Window
    function, Proc. IEEE Int. Symp. Circuits and Systems, 20-23, April 1974.
    """

    dF = fs-fp
    N2 = (-20*log10(np.sqrt(dp*ds))-13.0)/(14.6*dF)+1.0

    return int(N2)
#------------------------------------------------------------------------------

def remlplen_ichige(fp,fs,dp,ds):
    """
    Determine the length of the low pass filter with passband frequency
    fp, stopband frequency fs, passband ripple dp, and stopband ripple ds.
    fp and fs must be normalized with respect to the sampling frequency.
    Note that the filter order is one less than the filter length.
    Uses approximation algorithm described by Ichige et al.:
    K. Ichige, M. Iwaki, and R. Ishii, Accurate Estimation of Minimum
    Filter Length for Optimum FIR Digital Filters, IEEE Transactions on
    Circuits and Systems, 47(10):1008-1017, October 2000.
    """
#        dp_lin = (10**(dp/20.0)-1) / (10**(dp/20.0)+1)*2
    dF = fs-fp
    v = lambda dF,dp:2.325*((-log10(dp))**-0.445)*dF**(-1.39)
    g = lambda fp,dF,d:(2.0/pi)*arctan(v(dF,dp)*(1.0/fp-1.0/(0.5-dF)))
    h = lambda fp,dF,c:(2.0/pi)*arctan((c/dF)*(1.0/fp-1.0/(0.5-dF)))
    Nc = np.ceil(1.0+(1.101/dF)*(-log10(2.0*dp))**1.1)
    Nm = (0.52/dF)*log10(dp/ds)*(-log10(dp))**0.17
    N3 = np.ceil(Nc*(g(fp,dF,dp)+g(0.5-dF-fp,dF,dp)+1.0)/3.0)
    DN = np.ceil(Nm*(h(fp,dF,1.1)-(h(0.5-dF-fp,dF,0.29)-1.0)/2.0))
    N4 = N3+DN

    return int(N4)
    
#-------------------------------------------------------------
def rt_label(label):
    """
    Rich text label: Format label with italic + bold HTML tags and
     replace '_' by HTML subscript tags

     Parameters
     ----------

    label : string
        Name for the label to be converted, containing '_' for subsripts
        
    Returns
    -------
    
    html_label
    
    Examples
    --------
        
        >>> rt_label("F_SB")
        <b><i>F<sub>SB</sub></i></b>
         
    """
    #"<b><i>{0}</i></b>".format(newLabels[i])) # update label
    if "_" in label:
        label = label.replace('_', '<sub>')
        label += "</sub>"
    html_label = "<b><i>"+label+"</i></b>"
    return html_label



#######################################
# If called directly, do some example #
#######################################
if __name__=='__main__':
    import matplotlib.pyplot as plt
#    from matplotlib import patches
    ax1 = plt.figure(1).add_subplot(111)
    print(zplane(b=[1,0,0,1], a = 1, plt_ax = ax1))
    ax2 = plt.figure(2).add_subplot(111)
    print(zplane(z=1, plt_ax = ax2))
    ax3 = plt.figure(3).add_subplot(111)
    print(zplane(b=[1,1], plt_ax = ax3))
    format_ticks(ax3, 'xy', format="%2.2f", scale = 5)
    
    ax4 = plt.figure(4).add_subplot(111)
    print(zplane(b=[1,0], plt_ax = ax4))
    ax5 = plt.figure(5).add_subplot(111)
    print(zplane(b=[1,1,1,1,1], plt_ax = ax5))
    ax6 = plt.figure(6).add_subplot(111)
    print(zplane(b=np.convolve([1,1,1,1,1], [1,1,1,1,1]), a = [1,1], plt_ax = ax6))
#    ax7 = plt.figure(7).add_subplot(111)
#    print(zplane(b=1, plt_ax = ax7))
    plt.show()
