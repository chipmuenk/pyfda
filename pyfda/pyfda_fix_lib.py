# -*- coding: utf-8 -*-
#===========================================================================
#
# Fixpoint library for converting numpy scalars and arrays to quantized
# numpy values
#
# (c) 2015 - 2017 Christian Münker
#===========================================================================
from __future__ import division, print_function, unicode_literals

import logging
logger = logging.getLogger(__name__)

import numpy as np
from .pyfda_qt_lib import qstr
import pyfda.filterbroker as fb

# TODO: Overflows are not handled correctly
# TODO: Overflow errors can occur for very large numbers?
# TODO: Implment fractional point for int/hex/bin/csd?

__version__ = 0.5

def dec2hex(val, nbits):
    """
    Return `val` in hex format with a wordlength of `nbits` in two's complement
    format. The built-in hex function returns args < 0 as negative values.

    Parameters
    ----------
    val: integer
            The value to be converted in decimal integer format.

    nbits: integer
            The wordlength

    Returns
    -------
    A string in two's complement hex format
    """
    return "{0:x}".format(((val + (1 << nbits)) % (1 << nbits)).astype(np.int64))

def base2dec(val_str, nbits, base):
    """
    Convert `val_str` with base `base` and a wordlength of `nbits` to decimal format. In
    contrast to int(), `val_str` is treated as two's complement number, i.e. the MSB
    is regarded as a sign bit. 

    Parameters:
    -----------
    val: string
            The value to be converted

    nbits: integer
                wordlength

    base: integer
                numeric base

    Returns:
    --------
    integer
            The result, converted to (decimal) integer.
    """
    # TODO: add calculation of fractional formats?
    nbits = int(abs(nbits))
    base = int(abs(base))
    if base not in {2, 10, 16}:
        raise TypeError
        return None
    try:
    #  Find the number of places before the fractional point (if there is one)
        (int_str, _) = val_str.split('.') # split into integer and fractional bits
        val_str = val_str.replace('.','') # join integer and fractional bits to one string
    except ValueError: # no fractional part
        int_str = val_str

    int_places = len(int_str)-1 # this could be used to shift the result    
    try:
        i = int(val_str, base)
        if i <= 0 or i < (1 << (nbits-1)): # less than Max/2
            return i
        else:
            return i - (1 << nbits)
    except ValueError:
        logger.warn("Invalid literal {0:s}".format(val_str))
        return None


def dec2csd(dec_val, WF=0):
    """
    Convert the argument `dec_val` to a string in CSD Format.

    Parameters:
    -----------

    dec_val : scalar (integer or real)
              decimal value to be converted to CSD format

    WF: integer
        number of fractional places. Default is WF = 0 (integer number)

    Returns:
    --------
    A string with the CSD value

    Original author: Harnesser
    https://sourceforge.net/projects/pycsd/
    License: GPL2

    """

    logger.debug("Converting {0:f}:".format(dec_val))

    # figure out binary range, special case for 0
    if dec_val == 0 :
        return '0'
    if np.fabs(dec_val) < 1.0 :
        k = 0
    else:
        k = int(np.ceil(np.log2(np.abs(dec_val) * 1.5)))

    logger.debug("to {0:d}.{1:d} format".format(k, WF))

    # Initialize CSD calculation
    csd_digits = []
    remainder = dec_val
    prev_non_zero = False
    k -= 1 # current exponent in the CSD string under construction

    while( k >= -WF): # has the last fractional digit been reached

        limit = pow(2.0, k+1) / 3.0

        logger.debug("\t{0} - {1}".format(remainder, limit))

        # decimal point?
        if k == -1 :
            csd_digits.extend( ['.'] )

        # convert the number
        if prev_non_zero:
            csd_digits.extend( ['0'] )
            prev_non_zero = False

        elif remainder > limit :
            csd_digits.extend( ['+'] )
            remainder -= pow(2.0, k )
            prev_non_zero = True

        elif remainder < -limit :
            csd_digits.extend( ['-'] )
            remainder += pow(2.0, k )
            prev_non_zero = True

        else :
            csd_digits.extend( ['0'] )
            prev_non_zero = False

        k -= 1

        logger.debug(csd_digits)

    # Always have something before the point
    if np.fabs(dec_val) < 1.0:
        csd_digits.insert(0, '0')

    csd_str = "".join(csd_digits)

    return csd_str


def csd2dec(csd_str, radix_point=False):
    """
    Convert the CSD string `csd_str` to a decimal, `csd_str` may contain '+' or
    '-', indicating whether the current bit is meant to positive or negative.
    All other characters are simply ignored.

    `csd_str` may be an integer or fractional CSD number.

    Parameters:
    -----------

    csd_str : string

     A string with the CSD value to be converted, consisting of '+', '-', '.'
     and '0' characters.

    Returns:
    --------
    Real value of the CSD string

    Examples:
    ---------

    +00- = +2³ - 2⁰ = +7

    -0+0 = -2³ + 2¹ = -6

    +0.-0- = 2¹ - 1/2¹ - 1/2³ = 1.375

    """
    logger.debug("Converting: {0}".format(csd_str))

    #  Find out what the MSB power of two should be, keeping in
    #  mind we may have a fractional CSD number:
    try:
        (int_str, _) = csd_str.split('.') # split into integer and fractional bits
        csd_str = csd_str.replace('.','') # join integer and fractional bits to one csd string
    except ValueError: # no fractional part
        int_str = csd_str
        _ = ""

    # Intialize calculation, start with the MSB (integer)
    msb_power = len(int_str)-1 #
    dec_val = 0.0

    # start from the MSB and work all the way down to the last digit
    for ii in range( len(csd_str) ):

        power_of_two = 2.0**(msb_power-ii)

        if csd_str[ii] == '+' :
            dec_val += power_of_two
        elif csd_str[ii] == '-' :
            dec_val -= power_of_two
        # else
        #    ... all other values are ignored

        logger.debug('  "{0:s}" ({1:d}.{2:d}); 2**{3:d} = {4}; Num={5:f}'.format(
                csd_str[ii], len(int_str), len(_), msb_power-ii, power_of_two, dec_val))

    return dec_val


#==============================================================================
# Define ufuncs using numpys automatic type casting
#==============================================================================
#bin_u = np.frompyfunc(np.binary_repr, 2, 1)
#hex_tc_u = np.frompyfunc(hex_tc, 2, 1)
#base2dec_u = np.frompyfunc(base2dec, 3, 1)
#csd2dec_u = np.frompyfunc(csd2dec, 1, 1)
#dec2csd_u = np.frompyfunc(dec2csd, 2, 1)

#------------------------------------------------------------------------
class Fixed(object):
    """
    Implement binary quantization of signed scalar or array-like objects
    in the form yq = WI.WF where WI and WF are the wordlength of integer resp.
    fractional part; total wordlength is W = WI + WF + 1 due to the sign bit.

    q_obj = {'WI':1, 'WF':14, 'ovfl':'sat', 'quant':'round'} or

    q_obj = {'Q':'1.14', 'ovfl':'sat', 'quant':'round'}

    myQ = Fixed(q_obj) # instantiate fixed-point object


    Parameters
    ----------
    q_obj : dict
        defining quantization operation with the keys

    * **'WI'** : integer word length, default: 0

    * **'WF'** : fractional word length; default: 15; WI + WF + 1 = W (1 sign bit)

    * **'quant'** : Quantization method, optional; default = 'floor'

      - 'floor': (default) largest integer `I` such that :math:`I \\le x` (= binary truncation)
      - 'round': (binary) rounding
      - 'fix': round to nearest integer towards zero ('Betragsschneiden')
      - 'ceil': smallest integer `I`, such that :math:`I \\ge x`
      - 'rint': round towards nearest int
      - 'none': no quantization

    * **'ovfl'** : Overflow method, optional; default = 'wrap'

      - 'wrap': do a two's complement wrap-around
      - 'sat' : saturate at minimum / maximum value
      - 'none': no overflow; the integer word length is ignored
      
    Additionally, the following keys define the base / display format for the 
    fixpoint number:

    * **'frmt'** : Output format, optional; default = 'frac'

      - 'frac' : (default) decimal fraction
      - 'int'  : decimal integer, scaled by :math:`2^{WF}`
      - 'bin'  : binary string, scaled by :math:`2^{WF}`
      - 'hex'  : hex string, scaled by :math:`2^{WF}`
      - 'csd'  : canonically signed digit string, scaled by :math:`2^{WF}`
      
    * **'point'** : Boolean, when True use / provide a radix point (default: False)
    
      - False: Scale the result of the quantization by `2^{W} = 2^{WI + WF + 1}`
      - True : Scale the result of the quantization by `2^{WI}`


    Instance Attributes
    -------------------
    q_obj : dict
        A copy of the quantization dictionary (see above)

    quant : string
        Quantization behaviour ('floor', 'round', ...)

    ovfl  : string
        Overflow behaviour ('wrap', 'sat', ...)

    frmt : string
        target output format ('frac', 'int', 'bin', 'hex')
        
    point : boolean
        If True, use position of radix point for format conversion

    N_over : integer
        total number of overflows

    N_over_neg : integer
        number of negative overflows

    N_over_pos : integer
        number of positive overflows

    LSB : float
        value of LSB (smallest quantization step)

    MSB : float
        value of most significant bit (MSB)

    digits : integer (read only)
        number of digits required for selected number format and wordlength

    Notes
    -----
    class Fixed() can be used like Matlabs quantizer object / function from the
    fixpoint toolbox, see (Matlab) 'help round' and 'help quantizer/round' e.g.

    q_dsp = quantizer('fixed', 'round', [16 15], 'wrap'); % Matlab

    q_dsp = {'Q':'0.15', 'quant':'round', 'ovfl':'wrap'} # Python


    """
    def __init__(self, q_obj):
        """
        Initialize fixed object with dict q_obj
        """
        # test if all passed keys of quantizer object are known
        self.setQobj(q_obj)
        self.resetN() # initialize overflow-counter

    def setQobj(self, q_obj):
        """
        Analyze quantization dict, complete and transform it if needed and
        store it as instance attribute
        """
        for key in q_obj.keys():
            if key not in ['Q','WF','WI','quant','ovfl','frmt','point']:
                raise Exception(u'Unknown Key "%s"!'%(key))

        # set default values for parameters if undefined:
        if 'Q' in q_obj:
            Q_str = str(q_obj['Q']).split('.',1)  # split 'Q':'1.4'
            q_obj['WI'] = int(Q_str[0])
            q_obj['WF'] = int(Q_str[1])
        else:
            if 'WI' not in q_obj: q_obj['WI'] = 0
            else: q_obj['WI'] = int(q_obj['WI'])
            if 'WF' not in q_obj: q_obj['WF'] = 15
            else: q_obj['WF'] = int(q_obj['WF'])
        if 'quant' not in q_obj: q_obj['quant'] = 'floor'
        if 'ovfl' not in q_obj: q_obj['ovfl'] = 'wrap'
        if 'frmt' not in q_obj: q_obj['frmt'] = 'frac'
        if 'point' not in q_obj: q_obj['point'] = 'false'

        self.q_obj = q_obj # store quant. dict in instance
        self.quant = str(q_obj['quant']).lower()
        self.ovfl  = str(q_obj['ovfl']).lower()
        self.frmt = str(q_obj['frmt']).lower()
        self.point = q_obj['point']
        self.WF = q_obj['WF']
        self.WI = q_obj['WI']
        self.W = self.WF + self.WI + 1

        self.LSB  = 2. ** (-q_obj['WF']) # value of LSB = 2 ^ (-WF)
        self.MSB  = 2. ** q_obj['WI']    # value of MSB = 2 ^ WI

        if self.frmt == 'int':
            self.digits = int(np.ceil(np.log10(self.W) * np.log10(2.))) # required number of digits for dec. repr.
            self.base = 10
        elif self.frmt == 'bin':
            self.digits = self.W # required number of digits for bin. repr.
            self.base = 2
        elif self.frmt == 'csd':
            self.digits = self.W # required number of digits for bin. repr.
            self.base = 2
        elif self.frmt == 'hex':
            self.digits = int(np.ceil(self.W / 4.)) # required number of digits for hex. repr.
            self.base = 16
        elif self.frmt == 'frac':
            self.digits = 4
            self.base = 0
        else:
            raise Exception(u'Unknown format "%s"!'%(self.frmt))

#------------------------------------------------------------------------------
    def fix(self, y):
        """
        Return fixed-point representation `yq` of `y` (scalar or array-like),
        yq.shape = y.shape

        Parameters
        ----------
        y: scalar or array-like object
            to be quantized in fractional format

        Returns
        -------
        yq: float or ndarray
            with the same shape as `y`.
            The quantized input value(s) as a scalar or ndarray with `dtype=np.float64`.

        Examples:
        ---------

        >>> q_obj_a = {'WI':1, 'WF':6, 'ovfl':'sat', 'quant':'round'}
        >>> myQa = Fixed(q_obj_a) # instantiate fixed-point object myQa
        >>> myQa.resetN()  # reset overflow counter
        >>> a = np.arange(0,5, 0.05) # create input signal

        >>> aq = myQa.fixed(a) # quantize input signal
        >>> plt.plot(a, aq) # plot quantized vs. original signal
        >>> print(myQa.N_over, "overflows!") # print number of overflows

        >>> # Convert output to same format as input:
        >>> b = np.arange(200, dtype = np.int16)
        >>> btype = np.result_type(b)
        >>> # MSB = 2**7, LSB = 2**2:
        >>> q_obj_b = {'WI':7, 'WF':-2, 'ovfl':'wrap', 'quant':'round'}
        >>> myQb = Fixed(q_obj_b) # instantiate fixed-point object myQb
        >>> bq = myQb.fixed(b)
        >>> bq = bq.astype(btype) # restore original variable type
        >>>

        """

        if np.shape(y):
            # create empty arrays for result and overflows with same shape as y for speedup
            SCALAR = False
            y = np.asarray(y) # convert lists / tuples / ... to numpy arrays
            if y.dtype.type is np.string_:
                np.char.replace(y, ' ', '') # remove all whitespace
                y = y.astype(complex) # ensure that is y is a numeric type
            yq = np.zeros(y.shape)
            over_pos = over_neg = np.zeros(y.shape, dtype = bool)
        else:
            SCALAR = True
            # If y is not a number, convert to string, remove whitespace and convert
            # to complex format:
            if not np.issubdtype(type(y), np.number):
                y = qstr(y)
                y = y.replace(' ','') # whitespace is not allowed in complex number
                try:
                    y = complex(y)
                except ValueError as e:
                    logger.error(y, '\n', e)
            over_pos = over_neg = yq = 0

        # convert pseudo-complex (imag = 0) and complex values to real
        y = np.real_if_close(y)
        if np.iscomplexobj(y):
            logger.warn("Casting complex values to real before quantization!")
            # quantizing complex objects is not supported yet
            y = y.real

        # Quantize inputs
        if   self.quant == 'floor':  yq = self.LSB * np.floor(y / self.LSB)
             # largest integer i, such that i <= x (= binary truncation)
        elif self.quant == 'round':  yq = self.LSB * np.round(y / self.LSB)
             # rounding, also = binary rounding
        elif self.quant == 'fix':    yq = self.LSB * np.fix(y / self.LSB)
             # round to nearest integer towards zero ("Betragsschneiden")
        elif self.quant == 'ceil':   yq = self.LSB * np.ceil(y / self.LSB)
             # smallest integer i, such that i >= x
        elif self.quant == 'rint':   yq = self.LSB * np.rint(y / self.LSB)
             # round towards nearest int
        elif self.quant == 'none':   yq = y
        else:
            raise Exception('Unknown Requantization type "%s"!'%(self.quant))

        # Handle Overflow / saturation
        if   self.ovfl == 'none':
            pass
        else:
            # Bool. vectors with '1' for every neg./pos overflow:
            over_neg = (yq < -self.MSB)
            over_pos = (yq >= self.MSB)
            # No. of pos. / neg. / all overflows occured since last reset:
            self.N_over_neg += np.sum(over_neg)
            self.N_over_pos += np.sum(over_pos)
            self.N_over = self.N_over_neg + self.N_over_pos

            # Replace overflows with Min/Max-Values (saturation):
            if self.ovfl == 'sat':
                yq = np.where(over_pos, self.MSB-self.LSB, yq) # (cond, true, false)
                yq = np.where(over_neg, -self.MSB, yq)
            # Replace overflows by two's complement wraparound (wrap)
            elif self.ovfl == 'wrap':
                yq = np.where(over_pos | over_neg,
                    yq - 2. * self.MSB*np.fix((np.sign(yq) * self.MSB+yq)/(2*self.MSB)),
                    yq)
            else:
                raise Exception('Unknown overflow type "%s"!'%(self.overfl))
                return None

        if SCALAR and isinstance(yq, np.ndarray):
            yq = yq.item() # convert singleton array to scalar

        return yq

#------------------------------------------------------------------------------
    def resetN(self):
        """ Reset overflow-counters of Fixed object"""
        self.N_over = 0
        self.N_over_neg = 0
        self.N_over_pos = 0

#------------------------------------------------------------------------------
    def base2frac(self, y, frmt=None, radix_point=False):
        """
        Return fractional representation `yq` of `y` (scalar)

        Parameters
        ----------
        y: scalar
            to be quantized with the numeric base specified by `frmt`.

        frmt: string (optional)
            any of the formats `frac`, `int`, `bin`, `hex`, `csd`)
            When `frmt` is unspecified, the instance parameter `self.frmt` is used

        Returns
        -------
        yq: float in fractional format
            The quantized input value(s) as a scalar or ndarray with `dtype=np.float64`.
        """
        if frmt is None:
            frmt = self.frmt
        frmt = frmt.lower()
        if frmt == 'frac':
            f = self.fix(y)
            if f is not None:
                return f
            elif fb.data_old is not None:
                return fb.data_old
            else:
                return 0

        elif frmt in {'hex', 'bin', 'int'}:
            int_ = base2dec(y, self.W, self.base)
            if int_ is not None:
                return int_ / (1 << self.WF)
            elif fb.data_old is not None:
                return fb.data_old
            else:
                return 0.

        elif frmt == 'csd':
            return csd2dec(y) / (1 << self.WF)
        else:
            raise Exception('Unknown output format "%s"!'%(frmt))
            return None

#------------------------------------------------------------------------------
    def repr_fix(self, y, radix_point=False):
        """
        Return representation `yf` of `y` (scalar or array-like) in selected format
        `yf.shape = y.shape`

        Parameters
        ----------
        y: scalar or array-like object in fractional format
            to be transformed

        Returns
        -------
        yf: string, float or ndarray of float of string
            with the same shape as `y`.
            `yf` is formatted as set in `self.frmt` with `self.W` digits
        """
        # round / clip numbers: yf is fractional with the required range and resolution
        yf = self.fix(y)
        if self.frmt == 'frac': # return quantized fractional value
            return yf
        # no fractional format, scale with 2^WF to obtain integer representation
        if self.frmt in {'hex', 'bin', 'int', 'csd'}:
            yi = (np.round(yf * (1 << self.WF))).astype(int) # shift left by WF bits
        if self.frmt == 'int':
            return yi
        elif self.frmt == 'hex':
            return dec2hex(yi, self.W)
        elif self.frmt == 'bin':
            return np.binary_repr(yi, self.W)
        elif self.frmt == 'csd':
            if radix_point:
                return dec2csd(yi, self.WF) # yes, use fractional bits WF
            else:
                return dec2csd(yi, 0) # no, treat as integer
        else:
            raise Exception('Unknown output format "%s"!'%(self.frmt))
            return None


class FIX_filt_MA(Fixed):
    """
    Usage:
    Q = FIX_filt_MA(q_mul, q_acc) # Instantiate fixpoint filter object
    x_bq = self.Q_mul.fxp_filt(x[k:k + len(bq)] * bq)

    The fixpoint object has two different quantizers:
    - q_mul describes requanitization after coefficient multiplication
    - q_acc describes requanitization after each summation in the accumulator
            (resp. in the common summation point)

    """
    def __init__(self, q_mul, q_acc):
        """
        Initialize fixed object with q_obj
        """
        # test if all passed keys of quantizer object are known
        self.Q_mul = Fixed(q_mul)
        self.Q_mul.resetN() # reset overflow counter of Q_mul
        self.Q_acc = Fixed(q_acc)
        self.Q_acc.resetN() # reset overflow counter of Q_acc
        self.resetN() # reset filter overflow-counter


    def fxp_filt_df(self, x, bq, verbose = True):
        """
        Calculate filter (direct form) response via difference equation with
        quantization

        Parameters
        ----------
        x : scalar or array-like
            input value(s)

        bq : array-like
            filter coefficients

        Returns
        -------
        yq : ndarray
            The quantized input value(s) as an ndarray with np.float64. If this is
            not what you want, see examples.


        """

        # Initialize vectors (also speeds up calculation)
        yq = accu_q = np.zeros(len(x))
        x_bq = np.zeros(len(bq))

        for k in range(len(x) - len(bq)):
            # weighted state-vector x at time k:
            x_bq = self.Q_mul.fix(x[k:k + len(bq)] * bq)
            # sum up x_bq to get accu[k]
            accu_q[k] = self.Q_acc.fix(sum(x_bq))
        yq = accu_q # scaling at the output of the accumulator

        if (self.Q_mul.N_over and verbose): print('Overflows in Multiplier:  ',
                Fixed.Q_mul.N_over)
        if (self.Q_acc.N_over and verbose): print('Overflows in Accumulator: ',
                self.Q_acc.N_over)
        self.N_over = self.Q_mul.N_over + self.Q_acc.N_over

        return yq

# nested loop would be much slower!
#  for k in range(Nx - len(bq)):
#	for i in len(bq):
#	  accu_q[k] = fixed(q_acc, (accu_q[k] + fixed(q_mul, x[k+i]*bq[i+1])))

#----------------------------------------------------------------------
#============ not working yet =================================================
# class FIX_filt_MA(Fixed):
#     """
#     yq = FIX_filt_MA.fixFilt(x,aq,bq,gq)
# 	FIR-Filter mit verschiedenen internen Quantisierungen:
# 	q_mul beschreibt Requantisierung nach Koeffizientenmultiplikation
# 	q_acc beschreibt Requantisierung bei jeder Summation im Akkumulator
# 	(bzw. gemeinsamen Summenpunkt)
#     """
#     def __init__(self, q_mul, q_acc):
#         """
#         Initialize fixed object with q_obj
#         """
#         # test if all passed keys of quantizer object are known
#         self.setQobj(q_mul)
#         self.resetN() # initialize overflow-counter
#
#
# # Calculate filter response via difference equation with quantization:
#
#     def fixFilt(x, bq, aq, gq, q_mul, q_acc, verbose = True):
#
#         # Initialize vectors (also speeds up calculation)
#     #    Nx = len(x)
#     #    s = zeros(Nx) # not needed in this filter
#         yq = accu_q = np.zeros(len(x))
#     #    bq_len = len(bq)
#         x_bq = np.zeros(len(bq))
#
#         for k in range(len(x) - len(bq)):
#             # weighted state-vector x at time k:
#             x_bq, N_over_m = Fixed.fix(q_mul, x[k:k + len(bq)] * bq)
#             # sum up x_bq to get accu[k]
#             accu_q[k], N_over_a = Fixed.fix(q_acc, sum(x_bq))
#         yq = accu_q * gq # scaling at the output of the accumulator
#         s = x # copy state-vector
#         if (N_over_m and verbose): print('Overflows in Multiplier:  ', N_over_m)
#         if (N_over_a and verbose): print('Overflows in Accumulator: ', N_over_a)
#
#       return yq
#
#==============================================================================



#######################################
# If called directly, do some example #
#######################################
if __name__=='__main__':
    pass
