# -*- coding: utf-8 -*-
"""
Created 2012 - 2017

@author: Christian Muenker
"""
#
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


from __future__ import division, print_function
import os, sys, re, time
import codecs
import logging
logger = logging.getLogger(__name__)
import numpy as np
from numpy import pi, log10, arctan

# Specify the backend of matplotlib to use pyQT4 to avoid conflicts on systems
# that default to pyQT5 (but have pyQt4 installed as well)
#import matplotlib
#matplotlib.use("Qt4Agg")

import scipy.signal as sig

#import logging
from distutils.version import LooseVersion


import pyfda.simpleeval as se

####### VERSIONS and related stuff ############################################
# ================ Required Modules ============================
# ==
# == When one of the following imports fails, terminate the program
from numpy import __version__ as VERSION_NP
from scipy import __version__ as VERSION_SCI
from matplotlib import __version__ as VERSION_MPL
from .compat import QT_VERSION_STR, QSysInfo # imports pyQt

VERSION = {}
VERSION.update({'python_long': sys.version})
VERSION.update({'python': ".".join(map(str, sys.version_info[:3]))})
VERSION.update({'matplotlib': VERSION_MPL})
VERSION.update({'pyqt': QT_VERSION_STR})
VERSION.update({'numpy': VERSION_NP})
VERSION.update({'scipy': VERSION_SCI})

# ================ Optional Modules ============================
try:
    from mayavi import __version__ as VERSION_MAYAVI
    VERSION.update({'mayavi': VERSION_MAYAVI})
except ImportError:
    logger.info("Module 'mayavi' not found.")
    
try:
    from myhdl import __version__ as VERSION_HDL
    VERSION.update({'myhdl': VERSION_HDL})
except ImportError:
    logger.info("Module 'myhdl' not found.")
    
try:
    from docutils import __version__ as VERSION_DOCUTILS
    VERSION.update({'docutils': VERSION_DOCUTILS})
except ImportError:
    logger.info("Module 'docutils' not found.")

def b(s):
    """
    Handle binary data in the same way under py2 and py3: 
    Py2: keep string data as string data
    Py3: convert string data to byte
    """
    if PY3:
        # first 256 characters of Latin 1 (ISO8859-1) are identical to the
        # first 256 characters of unicode
        return codecs.latin_1_encode(s)[0] # return as binary data
    else:
        return s # return as string


def cmp_version(mod, version):
    """
    Compare version number of installed module `mod` against string `version` and 
    return 1, 0 or -1 if the installed version is greater, equal or less than 
    the number in `version`.
    """
    if LooseVersion(VERSION[mod]) > LooseVersion(version):
        return 1
    elif  LooseVersion(VERSION[mod]) == LooseVersion(version):
        return 0
    else:
        return -1

def mod_version(mod = None):
    """
    Return the version of the module 'mod'. If the module is not found, return
    None. When no module is specified, return a string with all modules and 
    their versions sorted alphabetically.
    """
    if mod:
        if mod in VERSION:
            return LooseVersion(VERSION[mod])
        else:
            return None
    else:
        v = ""
        keys = sorted(list(VERSION.keys()))
        for k in keys:
            v += "{0: <11} : {1}\n".format(k, LooseVersion(VERSION[k]))
        return v   

SOS_AVAIL = cmp_version("scipy", "0.16") >= 0 # True when installed version = 0.16 or higher

PY3 = sys.version_info > (3,) # True for Python 3 

# Amplitude max, min values to prevent scipy aborts
# (Linear values)
MIN_PB_AMP = 0.00001
MAX_IPB_AMP = 0.85
MAX_FPB_AMP = 0.65
MIN_SB_AMP = 0.000001
MAX_ISB_AMP = 0.65
MAX_FSB_AMP = 0.45

print("Running on a")
if hasattr(QSysInfo, "WindowsVersion"):
    print("Windows System, version", QSysInfo.WindowsVersion)
    OS = "win"
    CRLF = "\r\n" # Windows: carriage return + line feed, Hex 0D 0A
elif hasattr(QSysInfo, "MacintoshVersion"):
    print("Macintosh, version", QSysInfo.MacintoshVersion)
    OS = "mac"
    CRLF = "\r" # Mac: carriage return only, Hex 0D
else:
    print("Unix / Linux system.")
    OS = "unix"
    CRLF = "\n" # Unix / Linux: line feed only, Hex 0A

        
logger.info(mod_version())
print(mod_version())

###############################################################################
#### General functions ########################################################

def safe_eval(expr, alt_expr=0):
    """
    Try ... except wrapper around simple_eval to catch various errors
    When evaluation fails or returns `None`, try evaluating `alt_expr`. When this also fails,
    return 0 to avoid errors further downstream.

    Parameters:
    -----------
    expr: string
        String to be evaluated

    alt_expr: string
        String to be evaluated when evaluation of first string fails.

    Returns
    -------
    float: the evaluated result or 0 when both arguments fail.
    """
    fail_1 = fail_2 = False
    result = None
    
    if expr == "":
        expr = None
        logger.warn("Empty string not allowed as argument!")
    else:
        try:
            # eliminate very small imaginary components due to rounding errors
            result = np.asscalar(np.real_if_close(se.simple_eval(expr), tol = 100))
        except Exception as e:
            logger.warn(e)
            fail_1 = True
            
    if fail_1 or result is None:
        if expr == "":
            expr = None
            logger.warn("Fallback argument: Empty string not allowed!")
        else:
            try:
                result = np.asscalar(np.real_if_close(se.simple_eval(alt_expr), tol = 100))
            except Exception as e:
                #(SyntaxError, ZeroDivisionError, IndexError, se.NameNotDefined) as e:
                logger.warn("Fallback argument:", e)
                fail_2 = True
        if fail_2 or result is None:
            result = 0
    return result


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
    
#------------------------------------------------------------------------------
def prune_file_ext(file_type):
    """
    Prune file extension, e.g. '(*.txt)' from file type description returned
    by QFileDialog
    """
    # regular expression: re.sub(pattern, repl, string) 
    #  Return the string obtained by replacing the leftmost non-overlapping 
    #  occurrences of the pattern in string by repl
    #   '.' means any character
    #   '+' means one or more
    #   '[^a]' means except for 'a'
    # '([^)]+)' : match '(', gobble up all characters except ')' till ')'
    # '(' must be escaped as '\('

    return re.sub('\([^\)]+\)', '', file_type)

#------------------------------------------------------------------------------        
def extract_file_ext(file_type):
    """
    Extract list with file extension(s), e.g. '.vhd' from type description 
    (e.g. 'VHDL (*.vhd)') returned by QFileDialog 
    """

    ext_list = re.findall('\([^\)]+\)', file_type) # extract '(*.txt)'
    return [t.strip('(*)') for t in ext_list] # remove '(*)'

#------------------------------------------------------------------------------
def qstr(text):
    """
    Convert text object (QVariant, QSTring, string) to string.

    In Python 3, python Qt objects are automatically converted to QVariant
    when stored as "data" e.g. in a QComboBox and converted back when
    retrieving. In Python 2, QVariant is returned when itemData is retrieved.
    This is first converted from the QVariant container format to a
    QString, next to a "normal" non-unicode string.

    Returns:
    
    The current text / QVariant data as a string
    """
    if "QString" in str(type(text)):
        # Python 3: convert QString -> str
        string = str(text)
#    elif not isinstance(text, six.text_type):
    elif "QVariant" in str(type(text)):
        # Python 2: convert QVariant -> QString -> str
        string = str(text.toString())
    else:
        # `text` is of type str already
        string = text
    return string


#------------------------------------------------------------------------------
def get_cmb_box(cmb_box, data=True):
    """
    Get current itemData or Text of comboBox and convert it to string.

    In Python 3, python Qt objects are automatically converted to QVariant
    when stored as "data" e.g. in a QComboBox and converted back when
    retrieving. In Python 2, QVariant is returned when itemData is retrieved.
    This is first converted from the QVariant container format to a
    QString, next to a "normal" non-unicode string.

    Returns:
    
    The current text or data of combobox as a string
    """
    if data:
        idx = cmb_box.currentIndex()
        cmb_data = cmb_box.itemData(idx)
        cmb_str = qstr(cmb_data) # convert QVariant, QString, string to plain string
    else:
        cmb_str = cmb_box.currentText()
  
    cmb_str = str(cmb_str)

    return cmb_str

#------------------------------------------------------------------------------
def set_cmb_box(cmb_box, string, data=False):
    """
    Set combobox to the index corresponding to `string` in a text field (data = False)
    or in a data field (data=True). When `string` is not found in the combobox entries,
     select the first entry. Signals are blocked during the update of the combobox.
     
    Returns: the index of the found entry
    """
    if data:
        idx = cmb_box.findData(str(string)) # find index for data = string
    else:
        idx = cmb_box.findText(str(string)) # find index for text = string    

    ret = idx

    if idx == -1: # data does not exist, use first entry instead
        idx = 0
        
    cmb_box.blockSignals(True)
    cmb_box.setCurrentIndex(idx) # set index
    cmb_box.blockSignals(False)
    
    return ret

#------------------------------------------------------------------------------
def style_widget(widget, state):
    """
    Apply the "state" defined in pyfda_rc.py to the widget, e.g.:  
    Color the >> DESIGN FILTER << button according to the filter design state:
    
    - "normal": default, no color styling
    - "ok":  green, filter has been designed, everything ok
    - "changed": yellow, filter specs have been changed
    - "error" : red, an error has occurred during filter design
    - "failed" : orange, filter fails to meet target specs
    - "unused": grey
    """
    state = str(state)
    if state == 'u':
        state = "unused"
    elif state == 'a':
        state = "active"
    elif state == 'd':
        state = "disabled"
    widget.setProperty("state", state)
    #fb.design_filt_state = state
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
    
    #------------------------------------------------------------------------------


def dB(lin, power = False):
    """
    Calculate dB from linear value. If power = True, calculate 10 log ...,
    else calculate 20 log ...
    """
    if power:
        return 10. * np.log10(lin)
    else:
        return 20 * np.log10(lin)
        
def lin2unit(lin_value, filt_type, amp_label, unit = 'dB'):
    """
    Convert linear amplitude specification to dB or W, depending on filter 
    type ('FIR' or 'IIR') and whether the specifications belong to passband
    or stopband. This is determined by checking whether amp_label contains
    the strings 'PB' or 'SB' :
    
    - Passband: 
       IIR: A_dB = -20 log10(1 - lin_value) 
       
       FIR: A_dB =  20 log10((1 + lin_value)/(1 - lin_value)) 
                
    - Stopband: 
        A_dB = -20 log10(lin_value)
    
    Returns the result as a float.
    """     
    if unit == 'dB':
        if "PB" in amp_label: # passband
            if filt_type == 'IIR':
                unit_value = -20 * log10(1. - lin_value)
            else:
                unit_value = 20 * log10((1. + lin_value)/(1 - lin_value))
        else: # stopband
            unit_value = -20 * log10(lin_value)
    elif unit == 'W':
        unit_value = lin_value * lin_value
    else:
        unit_value = lin_value
            
    return unit_value


def unit2lin(unit_value, filt_type, amp_label, unit = 'dB'):
    """
    Convert amplitude specification in dB or W to linear specs:
    
    - Passband: 
       IIR: A_PB_lin = 1 - 10 ** (-unit_value/20)
       
       FIR: A_PB_lin = (10 ** (unit_value/20) - 1)/ (10 ** (unit_value/20) + 1)
       
    - Stopband: 
       A_SB_lin = -10 ** (-unit_value/20)
       
    Returns the result as a float.
    """

    # Add limits to avoid errors
    valChange = False
    if (unit_value < 0): valChange = True
    unit_value = abs(unit_value)
    if unit == 'dB':
        if "PB" in amp_label: # passband
            if filt_type == 'IIR':
                lin_value = 1. - 10.**(-unit_value / 20.)
                if (lin_value > MAX_IPB_AMP): lin_value = MAX_IPB_AMP; valChange=True
            else: 
                lin_value = (10.**(unit_value / 20.) - 1) / (10.**(unit_value / 20.) + 1)
                if (lin_value > MAX_FPB_AMP): lin_value = MAX_FPB_AMP; valChange=True
        else: # stopband
            lin_value = 10.**(-unit_value / 20)
            if (lin_value < MIN_SB_AMP): lin_value = MIN_SB_AMP; valChange=True
            if filt_type == 'IIR':
                if (lin_value > MAX_ISB_AMP): lin_value = MAX_ISB_AMP; valChange=True
            else:
                if (lin_value > MAX_FSB_AMP): lin_value = MAX_FSB_AMP; valChange=True
    elif unit == 'W':
        lin_value = np.sqrt(unit_value)
        if (lin_value < MIN_PB_AMP): lin_value = MIN_PB_AMP; valChange=True
        if (lin_value > MAX_FPB_AMP): lin_value = MAX_FPB_AMP; valChange=True
    else:
        lin_value = unit_value
        if (lin_value < MIN_PB_AMP): lin_value = MIN_PB_AMP; valChange=True
        if "PB" in amp_label: # passband
            if (lin_value > MAX_FPB_AMP): lin_value = MAX_FPB_AMP; valChange=True
        else:
            if (lin_value > MAX_FSB_AMP): lin_value = MAX_FSB_AMP; valChange=True

    if (valChange): logger.warning("We changed an Amplitude Spec to be reasonable")
    return lin_value


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
def expand_lim(ax, eps_x, eps_y = None):
#==================================================================
    """
    Expand the xlim and ylim-values of passed axis by eps
    
    Parameters
    ----------
    
    ax : axes object
    
    eps_x : float
            factor by which x-axis limits are expanded
            
    eps_y : float
            factor by which y-axis limits are expanded. If eps_y is None, eps_x
            is used for eps_y as well.
    
    
    Returns
    -------
    nothing
    """
    
    if not eps_y:
        eps_y = eps_x
    xmin,xmax,ymin,ymax = ax.axis()                            
    dx = (xmax - xmin) * eps_x
    dy = (ymax - ymin) * eps_y
    ax.axis((xmin-dx,xmax+dx,ymin-dy,ymax+dy))      

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
    Save filter design ``arg`` in the format specified as ``format_in`` in
    the dictionary ``fil_dict``. The format can be either poles / zeros / gain,
    filter coefficients (polynomes) or second-order sections.
    
    Convert the filter design to the other formats if ``convert`` is True.
    
    Parameters
    ----------
    
    fil_dict : dict
        The dictionary where the filter design is saved to.
    
    arg : various formats
        The actual filter design
        
    format_in : string
        Specifies how the filter design in 'arg' is passed:
            
        - 'ba' : Coefficient form: Filter coefficients in FIR format 
                 (b, one dimensional) are automatically converted to IIR format (b, a).
        
        - 'zpk' : Zero / pole / gain format: When only zeroes are specified,
                  poles and gain are added automatically.
        
        - 'sos' : Second-order sections
        
    sender : string
        The name of the method that calculated the filter. This name is stored
        in ``fil_dict`` together with ``format_in``.
        
    convert : boolean
        When convert = True, convert arg to the other formats.
    """
    
    if format_in == 'sos':
            fil_dict['sos'] = arg
            fil_dict['ft'] = 'IIR'

    elif format_in == 'zpk':
        format_error = False
        if np.ndim(arg) == 1:
            if np.ndim(arg[0]) == 0: # list / array with z only -> FIR
                z = arg
                p = np.zeros(len(z))
                k = 1
                fil_dict['zpk'] = [z, p, k]
                fil_dict['ft'] = 'FIR'
            elif np.ndim(arg[0]) == 1: # list of lists
                if np.shape(arg)[0] == 3:
                    fil_dict['zpk'] = [arg[0], arg[1], arg[2]]
                    if np.any(arg[1]): # non-zero poles -> IIR
                        fil_dict['ft'] = 'IIR'
                    else:
                        fil_dict['ft'] = 'FIR'
                else:
                    format_error = True
            else:
                format_error = True
        else:
            format_error = True

        if format_error:        
            raise ValueError("Unknown 'zpk' format {0}".format(arg))

            
    elif format_in == 'ba': 
        if np.ndim(arg) == 1: # arg = [b] -> FIR
            b = np.asarray(arg)
            a = np.zeros(len(b))
        else: # arg = [b,a]
            b = arg[0]
            a = arg[1]

        if len(b) < 2: # no proper coefficients, initialize with a default
            b = np.asarray([1,0])
        if len(a) < 2: # no proper coefficients, initialize with a default
            a = np.asarray([1,0])

        a[0] = 1 # first coefficient of recursive filter parts always = 1

        # Determine whether it's a FIR or IIR filter and set fil_dict accordingly
        # Test whether all elements except the first one are zero
        if not np.any(a[1:]):
            #  same as:   elif np.all(a[1:] == 0)
            fil_dict['ft'] = 'FIR'
        else:
            fil_dict['ft'] = 'IIR'
            
        # equalize if b and a subarrays have different lengths:
        D = len(b) - len(a)
        if D > 0: # b is longer than a -> fill up a with zeros
            a = np.append(a, np.zeros(D))
        elif D < 0: # a is longer than b -> fill up b with zeros
            if fil_dict['ft'] == 'IIR':
                b = np.append(b, np.zeros(-D)) # make filter causal, fill up b with zeros
            else:
                a = a[:D] # discard last D elements of a (only zeros anyway)

        fil_dict['ba'] = [b, a]

    else:
        raise ValueError("Unknown input format {0:s}".format(format_in))
    
    fil_dict['creator'] = (format_in, sender)
    fil_dict['time_designed'] = time.time()
    
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
         'sos' : a list of second order sections - all other formats can easily
                 be derived from this format
         'zpk': [z,p,k] where z is the array of zeros, p the array of poles and
             k is a scalar with the gain - the polynomial form can be derived 
             from this format quite accurately
         'ba' : [b, a] where b and a are the polynomial coefficients - finding
                   the roots of the a and b polynomes may fail for higher orders
    """
    
    if 'sos' in format_in:
        if 'zpk' not in format_in:
            try:
                fil_dict['zpk'] = list(sig.sos2zpk(fil_dict['sos']))
            except Exception as e:
                logger.error(e)
            # check whether sos conversion has created a additional (superfluous)
            # pole and zero at the origin and delete them:
            z_0 = np.where(fil_dict['zpk'][0] == 0)[0]
            p_0 = np.where(fil_dict['zpk'][1] == 0)[0]
            if p_0 and z_0: # eliminate z = 0 and p = 0 from list:
                fil_dict['zpk'][0] = np.delete(fil_dict['zpk'][0],z_0)
                fil_dict['zpk'][1] = np.delete(fil_dict['zpk'][1],p_0)

        if 'ba' not in format_in:
            try:
                fil_dict['ba'] = list(sig.sos2tf(fil_dict['sos']))
            except Exception as e:
                logger.error(e)
            # check whether sos conversion has created additional (superfluous)
            # highest order polynomial with coefficient 0 and delete them
            if fil_dict['ba'][0][-1] == 0 and fil_dict['ba'][1][-1] == 0:
                fil_dict['ba'][0] = np.delete(fil_dict['ba'][0],-1) 
                fil_dict['ba'][1] = np.delete(fil_dict['ba'][1],-1) 

    elif 'zpk' in format_in: # z, p, k have been generated,convert to other formats
        zpk = fil_dict['zpk']
        if 'ba' not in format_in:
            try:
                fil_dict['ba'] = sig.zpk2tf(zpk[0], zpk[1], zpk[2])
            except Exception as e:
                logger.error(e)
        if 'sos' not in format_in:
            fil_dict['sos'] = [] # don't convert zpk -> SOS due to numerical inaccuracies
#            try:
#                fil_dict['sos'] = sig.zpk2sos(zpk[0], zpk[1], zpk[2])
#            except ValueError:
#                fil_dict['sos'] = []
#                print("WARN (pyfda_lib): Complex-valued coefficients, could not convert to SOS.")
                
    elif 'ba' in format_in: # arg = [b,a]
        b, a = fil_dict['ba'][0], fil_dict['ba'][1]
        try:
            fil_dict['zpk'] = list(sig.tf2zpk(b,a))
        except Exception as e:
            logger.error(e)
        fil_dict['sos'] = [] # don't convert ba -> SOS due to numerical inaccuracies
#        if SOS_AVAIL:
#            try:
#                fil_dict['sos'] = sig.tf2sos(b,a)
#            except ValueError:
#                fil_dict['sos'] = []
#                print("WARN (pyfda_lib): Complex-valued coefficients, could not convert to SOS.")

    else:
        raise ValueError("Unknown input format {0:s}".format(format_in))

        
def sos2zpk(sos):
    """
    - Taken from scipy/signal/filter_design.py - edit to eliminate first 
    order section 
    
    Return zeros, poles, and gain of a series of second-order sections
    Parameters
    ----------
    sos : array_like
        Array of second-order filter coefficients, must have shape
        ``(n_sections, 6)``. See `sosfilt` for the SOS filter format
        specification.
    Returns
    -------
    z : ndarray
        Zeros of the transfer function.
    p : ndarray
        Poles of the transfer function.
    k : float
        System gain.
    Notes
    -----
    .. versionadded:: 0.16.0
    """
    sos = np.asarray(sos)
    n_sections = sos.shape[0]
    z = np.empty(n_sections*2, np.complex128)
    p = np.empty(n_sections*2, np.complex128)
    k = 1.
    for section in range(n_sections):
        print(sos[section])
        zpk = sig.tf2zpk(sos[section, :3], sos[section, 3:])
#        if sos[section, 3] == 0: # first order section
        z[2*section:2*(section+1)] = zpk[0]
#        if sos[section, -1] == 0: # first order section
        p[2*section:2*(section+1)] = zpk[1]
        k *= zpk[2]
        
    return z, p, k


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
    
def floor_odd(x):
    """
    Return the largest odd integer not larger than x. x can be integer or float.
    """
    return round_odd(x-1)


def ceil_even(x):
    """
    Return the smallest even integer not less than x. x can be integer or float.
    """
    return round_even(x+1)
    
def floor_even(x):
    """
    Return the largest even integer not larger than x. x can be integer or float.
    """
    return round_even(x-1)


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
def rt_label(label, it = True):
    """
    Rich text label: Format label with italic + bold HTML tags and
     replace '_' by HTML subscript tags

     Parameters
     ----------

    label : string
        Name for the label to be converted, containing '_' for subscripts
        
    Returns
    -------
    
    html_label : string
        HTML - formatted label
    
    Examples
    --------
        
        >>> rt_label("F_SB")
        <b><i>F<sub>SB</sub></i></b>
         
    """
    if "_" in label:
        label = label.replace('_', '<sub>')
        label += "</sub>"
    if it:    
        html_label = "<b><i>"+label+"</i></b>"
    else:
        html_label = "<b>"+label+"</b>"
    return html_label

#------------------------------------------------------------------------------

if __name__=='__main__':
    pass
