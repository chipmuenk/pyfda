# -*- coding: utf-8 -*-
#===========================================================================
#
# Fixpoint library for converting numpy scalars and arrays to quantized
# numpy values
#
# (c) 2015 - 2017 Christian Münker
#===========================================================================
from __future__ import division, print_function, unicode_literals

import re
import logging
logger = logging.getLogger(__name__)

import numpy as np
from pyfda.pyfda_qt_lib import qstr
import pyfda.filterbroker as fb

# TODO: Scaling parameter is not used yet
# TODO: int_places calculation for CSD doesn't always make sense
# TODO: Various errors related to radix point:
#       - Frmt2float for fractional hex yields wrong results
#       - WI > 0 yields wrong scaling for decimal?

__version__ = 0.5

def bin2hex(bin_str, frac=False):
    """
    Convert number `bin_str` in binary format to hex formatted string.
    When `frac=False` (default), `bin_str` is prepended with zeros until 
    the number of bits is a multiple of 4. For a fractional part (`frac = True`),
    zeros are appended.
    """

    wmap ={'0000': '0',
           '0001': '1',
           '0010': '2',
           '0011': '3',
           '0100': '4',
           '0101': '5',
           '0110': '6',
           '0111': '7',
           '1000': '8',
           '1001': '9',
           '1010': 'A',
           '1011': 'B',
           '1100': 'C',
           '1101': 'D',
           '1110': 'E',
           '1111': 'F'}

    i = 0
    hex_str = ""

    # append or prepend zeros to bin_str until the length is a multiple of 4 bits
    while (len(bin_str) % 4 != 0):
        if frac: # fractional part, append zeros
            bin_str = bin_str + "0"
        else: # integer, prepend zeros
            bin_str = "0" + bin_str

    while (i < len(bin_str)):
        hex_str = hex_str + wmap[bin_str[i:i + 4]]
        i = i + 4

    hex_str = hex_str.strip("0")
    hex_str = "0" if len(hex_str) == 0 else hex_str

    return hex_str


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

#------------------------------------------------------------------------------

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


def csd2dec(csd_str, int_places=0):
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

    illegal_chars = re.sub('[+-0 ]', '', csd_str) # test for illegal characters
    if illegal_chars:
        logger.warn("Invalid character(s) {0} for CSD string!".format(illegal_chars))
        return None

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

    * **'frmt'** : Output format, optional; default = 'float'

      - 'float' : (default)
      - 'int'  : decimal integer, scaled by :math:`2^{WF}`
      - 'bin'  : binary string, scaled by :math:`2^{WF}`
      - 'hex'  : hex string, scaled by :math:`2^{WF}`
      - 'csd'  : canonically signed digit string, scaled by :math:`2^{WF}`
      
    * **'point'** : Boolean, when True use / provide a radix point, when False
                    use an integer representation (default: False)
          
    * **'scale'** : Float, the factor between the fixpoint integer representation
                    and its floating point value. 
                    
      - `point = False`: Scale the integer representation by `2^{W} = 2^{WI + WF + 1}`
      - `point = True` : Scale the integer representation by `2^{WI}`

                    

    Instance Attributes
    -------------------
    q_obj : dict
        A copy of the quantization dictionary (see above)

    quant : string
        Quantization behaviour ('floor', 'round', ...)

    ovfl  : string
        Overflow behaviour ('wrap', 'sat', ...)

    frmt : string
        target output format ('float', 'dec', 'bin', 'hex', 'csd')
        
    point : boolean
        If True, use position of radix point for format conversion
        
    scale : float
        The factor between integer fixpoint representation and the floating point
        value.

    ovr_flag : integer or integer array (same shape as input argument)
        overflow flag   0 : no overflow

                        +1: positive overflow

                        -1: negative overflow

        has occured during last fixpoint conversion

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
            if key not in ['Q','WF','WI','quant','ovfl','frmt','scale']:
                raise Exception(u'Unknown Key "%s"!'%(key))

        # set default values for parameters if undefined:
        if 'Q' in q_obj:
            Q_str = str(q_obj['Q']).split('.',1)  # split 'Q':'1.4'
            q_obj['WI'] = int(Q_str[0])
            q_obj['WF'] = int(abs(Q_str[1]))
        else:
            if 'WI' not in q_obj: q_obj['WI'] = 0
            else: q_obj['WI'] = int(q_obj['WI'])
            if 'WF' not in q_obj: q_obj['WF'] = 15
            else: q_obj['WF'] = int(q_obj['WF'])
        self.WF = q_obj['WF']
        self.WI = q_obj['WI']
        self.W = self.WF + self.WI + 1            

        if 'quant' not in q_obj: q_obj['quant'] = 'floor'
        self.quant = str(q_obj['quant']).lower()
        
        if 'ovfl' not in q_obj: q_obj['ovfl'] = 'wrap'
        self.ovfl  = str(q_obj['ovfl']).lower()
        
        if 'frmt' not in q_obj: q_obj['frmt'] = 'float'
        self.frmt = str(q_obj['frmt']).lower()

        if not hasattr(self, 'scale') or not self.scale or 'scale' not in q_obj:
            q_obj['scale'] = 1.
        self.scale = float(q_obj['scale'])

        self.q_obj = q_obj # store quant. dict in instance

        #if self.point:
        self.LSB  = 2. ** -self.WF  # value of LSB = 2 ^ (-WF)
        self.MSB  = 2. ** self.WI   # value of MSB = 2 ^ WI
        #else:
        #    self.LSB = 1
        #    self.MSB = 2. ** (self.W-1)

        # Calculate required number of places for different bases from total 
        # number of bits:
        if self.frmt == 'dec':
            self.places = int(np.ceil(np.log10(self.W) * np.log10(2.)))
            self.base = 10
        elif self.frmt == 'bin':
            self.places = self.W
            self.base = 2
        elif self.frmt == 'csd':
            self.places = self.W
            self.base = 2
        elif self.frmt == 'hex':
            self.places = int(np.ceil(self.W / 4.))
            self.base = 16
        elif self.frmt == 'float':
            self.places = 4
            self.base = 0
        else:
            raise Exception(u'Unknown format "%s"!'%(self.frmt))

        self.ovr_flag = 0

#------------------------------------------------------------------------------
        """
        Return fixed-point integer or fractional representation for `y` 
        (scalar or array-like) with the same shape as `y`.

        Saturation / two's complement wrapping happens outside the range +/- MSB,  
        requantization (round, floor, fix, ...) is applied on the ratio `y / LSB`.

        Parameters
        ----------
        y: scalar or array-like object
            in floating point format to be quantized

        scaling: Boolean
            When `True` (default), `y` is multiplied by `self.scale` before 
            requantizing and saturating.

        Returns
        -------
        integer scalar or ndarray
            with the same shape as `y`, in the range `-self.MSB` ... `self.MSB`

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
            self.ovr_flag = np.zeros(y.shape, dtype = int)
        else:
            SCALAR = True
            # get rid of errors that have occurred upstream
            if y is None or str(y) == "":
                y = 0
            # If y is not a number, convert to string, remove whitespace and convert
            # to complex format:
            elif not np.issubdtype(type(y), np.number):
                y = qstr(y)
                y = y.replace(' ','') # whitespace is not allowed in complex number
                try:
                    y = complex(y)
                except ValueError as e:
                    logger.error("Argument '{0}' yields \n {1}".format(y,e))
            over_pos = over_neg = yq = 0
            self.ovr_flag = 0

        # convert pseudo-complex (imag = 0) and complex values to real
        y = np.real_if_close(y)
        if np.iscomplexobj(y):
            logger.warn("Casting complex values to real before quantization!")
            # quantizing complex objects is not supported yet
            y = y.real

        y = y * self.scale
        # Quantize input in relation to LSB
        if   self.quant == 'floor':  yq = np.floor(y)
             # largest integer i, such that i <= x (= binary truncation)
        elif self.quant == 'round':  yq = np.round(y)
             # rounding, also = binary rounding
        elif self.quant == 'fix':    yq = np.fix(y)
             # round to nearest integer towards zero ("Betragsschneiden")
        elif self.quant == 'ceil':   yq = np.ceil(y)
             # smallest integer i, such that i >= x
        elif self.quant == 'rint':   yq = np.rint(y)
             # round towards nearest int
        elif self.quant == 'none':   yq = y
            # return unquantized value
        else:
            raise Exception('Unknown Requantization type "%s"!'%(self.quant))

        # Handle Overflow / saturation in relation to MSB
        if   self.ovfl == 'none':
            pass
        else:
            # Bool. vectors with '1' for every neg./pos overflow:
            over_neg = (yq < -self.MSB)
            over_pos = (yq >= self.MSB)
            # create flag / array of flags for pos. / neg. overflows
            self.ovr_flag = over_pos.astype(int) - over_neg.astype(int)
            # No. of pos. / neg. / all overflows occured since last reset:
            self.N_over_neg += np.sum(over_neg)
            self.N_over_pos += np.sum(over_pos)
            self.N_over = self.N_over_neg + self.N_over_pos

            # Replace overflows with Min/Max-Values (saturation):
            if self.ovfl == 'sat':
                yq = np.where(over_pos, (self.MSB-1), yq) # (cond, true, false)
                yq = np.where(over_neg, -self.MSB, yq)
            # Replace overflows by two's complement wraparound (wrap)
            elif self.ovfl == 'wrap':
                yq = np.where(over_pos | over_neg,
                    yq - 2. * self.MSB*np.fix((np.sign(yq) * self.MSB+yq)/(2*self.MSB)), yq)
            else:
                raise Exception('Unknown overflow type "%s"!'%(self.ovfl))
                return None

        if to_float:
            yq = yq / self.MSB
        else:
            yq = yq.astype(np.int64)

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
    def frmt2float(self, y, frmt=None):
        """
        Return floating point representation for fixpoint scalar `y` given in 
        format `frmt`.    
        
        - Construct string representation without radix point, count number of
          fractional places.
        - Calculate integer representation of string, taking the base into account
        (- When result is negative, calculate two's complement for `W` bits)
        - Scale with `2** -W`
        - Scale with the number of fractional places (depending on format!)

        Parameters
        ----------
        y: scalar or string
            to be quantized with the numeric base specified by `frmt`.

        frmt: string (optional)
            any of the formats `float`, `dec`, `bin`, `hex`, `csd`)
            When `frmt` is unspecified, the instance parameter `self.frmt` is used

        Returns
        -------
        floating point (`dtype=np.float64`) representation of fixpoint input.
        """
        if y == "":
            return 0

        if frmt is None:
            frmt = self.frmt
        frmt = frmt.lower()

        if frmt == 'float':
            if y.dtype.char in {'S', 'U'}: # string / unicode data type
                try:
                    y_float = float(y)
                except ValueError as e:
                    y_float = None
                return y_float
                # TODO: what about complex strings?
            else:
                y_float = y

        else: # {'dec', 'bin', 'hex', 'csd'}
         # Find the number of places before the first radix point (if there is one)
         # and join integer and fractional parts:
            val_str = qstr(y).replace(' ','') # just to be sure ...
            val_str = val_str.replace(',','.') # ',' -> '.' for German-style numbers

            if val_str[0] == '.': # prepend '0' when the number starts with '.'
                val_str = '0' + val_str
            try:
                int_str, _ = val_str.split('.') # split into integer and fractional places
            except ValueError: # no fractional part
                int_str = val_str

            frmt_regex = {'bin' : '[0|1]',
                     'csd' : '0|\+|\-',
                     'dec' : '[0-9]',
                     'hex' : '[0-9A-Fa-f]'
                     }
            frmt_scale = {'bin' : 2,
                          'csd' : 2,
                          'dec' : 1,
                          'hex' : 16}

            # count number of valid digits in string, using regex pattern
            int_places = len(re.findall(frmt_regex[frmt], int_str)) - 1
            raw_str = val_str.replace('.','') # join integer and fractional part  
            
            logger.debug("frmt, int_places", frmt, int_places)
            logger.debug("y, raw_str = ", y, val_str)

        # (1) calculate the decimal value of the input string using float()
        #     which takes the number of decimal places into account.
        # (2) divide by scale
        if frmt == 'dec':
            try:
                # try to convert string -> float directly usingg decimal point position
                y_float = float(val_str)
                y_float = y_float / self.MSB

            except Exception as e:
                logger.warn(e)
                y_float = None

        elif frmt in {'hex', 'bin'}:
            try:
                y_int = int(raw_str, self.base)
                # check for negative (two's complement) numbers
                if y_int >= (1 << (self.W-1)):
                    y_int = y_int - (1 << self.W)
                # quantize / saturate / wrap the integer value:

# TODO:                 # y_float = self.fix(y_int * self.LSB) * self.LSB
                y_float = self.fix(y_int, from_float = False) / self.MSB
                # scale integer fixpoint value
                #y_float = y_fix / self.MSB#2**(self.W-1)

            except Exception as e:
                logger.warn(e)
                y_int = None
                y_float = None

            print("MSB = {0} |  LSB = {1} | scale = {2}\n"
              "y = {3} | y_int = {4} | y_float = {5}".format(self.MSB, self.LSB, self.scale, y, y_int, y_float))

        elif frmt == 'csd':
            y_float = csd2dec(raw_str, int_places)
            if y_float is not None:
                y_float = y_float / 2**(self.W-1)

            logger.debug("MSB = {0} |  scale = {1}\n"
              "y = {2}  | y_float = {3}".format(self.MSB, self.scale, y, y_float))

        else:
            raise Exception('Unknown output format "%s"!'%(frmt))
            return None

        if y_float is not None:
            return y_float
        elif fb.data_old is not None:
            return fb.data_old
        else:
            return 0


#------------------------------------------------------------------------------
    def float2frmt(self, y):
        """
        Called a.o. by `itemDelegate.displayText()` for on-the-fly number 
        conversion, return fixpoint representation for `y` (scalar or array-like) 
        with numeric format `self.frmt` and `self.W` bits. The result has the 
        same shape as `y`.

        When `point = False` (use integer arithmetic), the floating point value
        is multiplied by self.MSB (2**W-1, shift right by W-1 bits). 

        When `point = True` (use radix point), the fractional representation is
        scaled by 2**WI (= shift left by WI bits).

        Parameters
        ----------
        y: scalar or array-like object (numeric or string) in fractional format
            to be transformed

        Returns
        -------
        A string, a float or an ndarray of float or string is returned in the 
        numeric format set in `self.frmt`. It has the same shape as `y`. For all
        formats except `float` a fixpoint representation with `self.W` binary 
        digits is returned.
        """
        if self.frmt == 'float': # return float input value unchanged
            return y

        elif self.frmt in {'hex', 'bin', 'dec', 'csd'}:
            # quantize & treat overflows of y (float), returning a float
            y_fix = self.fix(y)
            y_fix_lsb = y_fix * self.LSB

            # fixpoint format, transform to string
            yi = np.round(np.modf(y_fix_lsb)[1]).astype(int) # integer part
            yf = np.round(np.modf(y_fix_lsb)[0] * (1 << self.WF)).astype(int) # frac part as integer

            logger.debug("y_fix={0}, yi={1}, yf={2}".format(y_fix_lsb, yi, yf))

            if self.frmt == 'dec':
                y_str = str(y_fix_lsb) # use fixpoint number as returned by fix()

            elif self.frmt == 'hex':
                if self.WF > 0:
                    y_str_bin_i = np.binary_repr(y_fix, self.W)[:self.WI+1]
                    y_str_bin_f = np.binary_repr(y_fix, self.W)[self.WI+1:]
                    y_str = bin2hex(y_str_bin_i) + "." + bin2hex(y_str_bin_f, frac=True)
                else:
                    y_str = dec2hex(yi, self.W)
            elif self.frmt == 'bin':
                # calculate binary representation of fixpoint integer
                y_str = np.binary_repr(y_fix, self.W)
                if self.WF > 0:
                    # ... and insert the radix point if required
                    y_str = y_str[:self.WI+1] + "." + y_str[self.WI+1:]
            else: # self.frmt = 'csd'
                if self.WF > 0:
                    y_str = dec2csd(y_fix_lsb, self.WF) # yes, use fractional bits WF
                else:
                    y_str = dec2csd(y_fix, 0) # no, treat as integer

            return y_str
        else:
            raise Exception('Unknown output format "%s"!'%(self.frmt))
            return None

########################################
# If called directly, do some examples #
########################################
if __name__=='__main__':
    import pprint

    q_obj = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'point': False}
    myQ = Fixed(q_obj) # instantiate fixpoint object with settings above
    
    y_list = [-1.1, -1.0, -0.5, 0, 0.5, 0.99, 1.0]
    print("W = ", myQ.W, myQ.LSB, myQ.MSB)

    for point in [False, True]:
        q_obj['point'] = point
        myQ.setQobj(q_obj)
        print("point = ", point)
        for y in y_list:
            print("y -> y_fix", y, "->", myQ.fix(y))
            print(myQ.frmt, myQ.float2frmt(y))
            
    print("\nTesting frmt2float()\n====================\n")
    q_obj = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'point': False}
    pprint.pprint(q_obj)
    myQ.setQobj(q_obj)
    dec_list = [-9, -8, -7, -4.0, -3.578, 0, 0.5, 4, 7, 8]
    for dec in dec_list:
        print("{0} -> {1} ({2})".format(dec, myQ.frmt2float(dec), myQ.frmt))
