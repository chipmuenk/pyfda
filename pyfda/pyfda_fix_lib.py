# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Fixpoint library for converting numpy scalars and arrays to quantized
numpy values and formatting reals in various formats
"""
#===========================================================================
from __future__ import division, print_function, unicode_literals

import re
import logging
logger = logging.getLogger(__name__)

import numpy as np
from pyfda.pyfda_lib import qstr

# TODO: Absolute value for WI is taken, no negative WI specifications possible
# TODO: Vecorization for hex / csd functions (frmt2float)

__version__ = 0.5

def bin2hex(bin_str, WI=0):
    """
    Convert number `bin_str` in binary format to hex formatted string.
    `bin_str` is prepended / appended with zeros until the number of bits before
    and after the radix point (position given by `WI`) is a multiple of 4.
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

    hex_str = ""

    if WI > 0:
        # slice string with integer bits and prepend with zeros to obtain a multiple of 4 length
        bin_i_str = bin_str[:WI+1]
        while (len(bin_i_str) % 4 != 0):
            bin_i_str = "0" + bin_i_str

        i = 0
        while (i < len(bin_i_str)): # map chunks of 4 binary bits to one hex digit
            hex_str = hex_str + wmap[bin_i_str[i:i + 4]]
            i = i + 4
    else:
        hex_str = bin_str[0] # copy MSB as sign bit

    WF = len(bin_str) - WI - 1
    # slice string with fractional bits and append with zeros to obtain a multiple of 4 length
    if WF > 0:
        hex_str = hex_str + '.'
        bin_f_str = bin_str[WI+1:]

        while (len(bin_f_str) % 4 != 0):
            bin_f_str = bin_f_str + "0"

        i = 0
        while (i < len(bin_f_str)): # map chunks of 4 binary bits to one hex digit
            hex_str = hex_str + wmap[bin_f_str[i:i + 4]]
            i = i + 4

    # hex_str = hex_str.lstrip("0") # remove leading zeros
    hex_str = "0" if len(hex_str) == 0 else hex_str
    return hex_str

bin2hex_vec = np.vectorize(bin2hex) # safer than frompyfunction()

def dec2hex(val, nbits, WF=0):
    """
    --- currently not used, no unit test ---

    Return `val` in hex format with a wordlength of `nbits` in two's complement
    format. The built-in hex function returns args < 0 as negative values.
    When val >= 2**nbits, it is "wrapped" around to the range 0 ... 2**nbits-1

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

    return "{0:X}".format(np.int64((val + (1 << nbits)) % (1 << nbits)))
#------------------------------------------------------------------------------

def dec2csd(dec_val, WF=0):
    """
    Convert the argument `dec_val` to a string in CSD Format.

    Parameters
    ----------

    dec_val : scalar (integer or real)
              decimal value to be converted to CSD format

    WF: integer
        number of fractional places. Default is WF = 0 (integer number)

    Returns
    -------
    string
        containing the CSD value

    Original author: Harnesser
    https://sourceforge.net/projects/pycsd/
    License: GPL2

    """
    # figure out binary range, special case for 0
    if dec_val == 0 :
        return '0'
    if np.abs(dec_val) < 1.0 :
        k = 0
    else:
        k = int(np.ceil(np.log2(np.abs(dec_val) * 1.5)))

    logger.debug("CSD: Converting {0:f} to {1:d}.{2:d} format".format(dec_val, k, WF))

    # Initialize CSD calculation
    csd_digits = []
    remainder = dec_val
    prev_non_zero = False
    k -= 1 # current exponent in the CSD string under construction

    while( k >= -WF): # has the last fractional digit been reached


        limit = pow(2.0, k+1) / 3.0

        # logger.debug("\t{0} - {1}".format(remainder, limit))

        # decimal point?
        if k == -1 :
            if csd_digits == []:
                if dec_val > limit:
                    remainder -= 1
                    csd_digits.extend(['+.'])
                    prev_non_zero = True
                elif dec_val < -limit:
                    remainder += 1
                    csd_digits.extend(['-.'])
                    prev_non_zero = True
                else:
                    csd_digits.extend( ['0.'] )
            else:
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

    # Always have something before the point
#    if np.abs(dec_val) < 1.0:
#        csd_digits.insert(0, '0')

    csd_str = "".join(csd_digits)

    logger.debug("CSD result = {0}".format(csd_str))

#    if WF > 0:
#        csd_str = csd_str[:-WF] + "." + csd_str[-WF:]

    return csd_str

dec2csd_vec = np.frompyfunc(dec2csd, 2, 1)

def csd2dec(csd_str):
    """
    Convert the CSD string `csd_str` to a decimal, `csd_str` may contain '+' or
    '-', indicating whether the current bit is meant to positive or negative.
    All other characters are simply ignored (= replaced by zero).

    `csd_str` has to be an integer CSD number.

    Parameters
    ----------

    csd_str : string

     A string with the CSD value to be converted, consisting of '+', '-', '.'
     and '0' characters.

    Returns
    -------
    decimal (integer) value of the CSD string

    Examples
    --------

    +00- = +2³ - 2⁰ = +7

    -0+0 = -2³ + 2¹ = -6

    """
    logger.debug("Converting: {0}".format(csd_str))

    # Intialize calculation, start with the MSB (integer)
    msb_power = len(csd_str)-1 #
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

        logger.debug('  "{0:s}" (QI = {1:d}); 2**{2:d} = {3}; Num={4:f}'.format(
                csd_str[ii], len(csd_str), msb_power-ii, power_of_two, dec_val))

    return dec_val

#csd2dec_vec = np.frompyfunc(csd2dec, 1, 1)
csd2dec_vec = np.vectorize(csd2dec) # safer than np.frompyfunc()

#------------------------------------------------------------------------
class Fixed(object):
    """
    Implement binary quantization of signed scalar or array-like objects
    in the form `Q = WI.WF` where WI and WF are the wordlength of integer resp.
    fractional part; total wordlength is `W = WI + WF + 1` due to the sign bit.

    Examples
    --------

    Define a dictionary with the format options and pass it to the constructor:

    >>> q_obj = {'WI':1, 'WF':14, 'ovfl':'sat', 'quant':'round'} # or
    >>> q_obj = {'Q':'1.14', 'ovfl':'none', 'quant':'round'}
    >>> myQ = Fixed(q_obj)


    Parameters
    ----------
    q_obj : dict
        define quantization options with the following keys

    * **'WI'** : integer word length, default: 0

    * **'WF'** : fractional word length; default: 15

    * **'W'**  : total word length; WI + WF + 1 = W (1 sign bit). When WI and / or
                 W are missing, WI = W - 1 and WF = 0.

    * **'Q'**  : Quantization format as string, e.g. '0.15', it is translated
                 to`WI` and `WF`. When both `Q` and `WI` / `WF`
                 are given, `Q` is ignored

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
      - 'dec'  : decimal integer, scaled by :math:`2^{WF}`
      - 'bin'  : binary string, scaled by :math:`2^{WF}`
      - 'hex'  : hex string, scaled by :math:`2^{WF}`
      - 'csd'  : canonically signed digit string, scaled by :math:`2^{WF}`

    * **'scale'** : Float or a keyword, the factor between the fixpoint integer
            representation and its floating point value. If ``scale`` is a float,
            this value is used. Alternatively, if:

                - ``q_obj['scale'] == 'int'``:   scale = 1 << self.WF

                - ``q_obj['scale'] == 'norm'``:  scale = 2.**(-self.WI)


    Attributes
    ----------
    q_obj : dict
        A copy of the quantization dictionary (see above)

    WI : integer
        number of integer bits

    WF : integer
        number of fractional bits

    W : integer
        total wordlength

    Q : string
        quantization format, e.g. '2.13'

    quant : string
        Quantization behaviour ('floor', 'round', ...)

    ovfl  : string
        Overflow behaviour ('wrap', 'sat', ...)

    frmt : string
        target output format ('float', 'dec', 'bin', 'hex', 'csd')

    scale : float
        The factor between integer fixpoint representation and the floating point
        value.

    LSB : float
        value of LSB (smallest quantization step)

    MSB : float
        value of most significant bit (MSB)

    digits : integer
        number of digits required for selected number format and wordlength

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


    Example
    -------
    class `Fixed()` can be used like Matlabs quantizer object / function from the
    fixpoint toolbox, see (Matlab) 'help round' and 'help quantizer/round' e.g.

    >>> q_dsp = quantizer('fixed', 'round', [16 15], 'wrap'); % Matlab
    >>> yq = quantize(q_dsp, y)

    >>> q_dsp = {'Q':'0.15', 'quant':'round', 'ovfl':'wrap'} # Python
    >>> my_q = Fixed(q_dsp)
    >>> yq = my_q.fixp(y)

    """

    def __init__(self, q_obj):
        """
        Initialize fixed object with dict q_obj
        """
        # test if all passed keys of quantizer object are defined
        self.setQobj(q_obj)
        self.resetN() # initialize overflow-counter

        # arguments for regex replacement with illegal characters
        # ^ means "not", | means "or" and \ escapes
        self.FRMT_REGEX = {
                'bin' : r'[^0|1|.|,|\-]',
                'csd' : r'[^0|\+|\-|.|,]',
                'dec' : r'[^0-9|.|,|\-]',
                'hex' : r'[^0-9A-Fa-f|.|,|\-]'
                        }

    def setQobj(self, q_obj):
        """
        Analyze quantization dict, complete and transform it if needed and
        store it as instance attribute.

        Check the docstring of class `Fixed()` for  details.
        """
        for key in q_obj.keys():
            if key not in ['Q','WF','WI','W','quant','ovfl','frmt','scale']:
                raise Exception(u'Unknown Key "%s"!'%(key))

        q_obj_default = {'WI':0, 'WF':15, 'quant':'round', 'ovfl':'sat',
                         'frmt':'float', 'scale':1}

        if 'WI' in q_obj and 'WF' in q_obj:
            pass # everything's defined already
        elif 'W' in q_obj:
            q_obj['WI'] = int(q_obj['W']) - 1
            q_obj['WF'] = 0
        elif 'Q' in q_obj:
            Q_str = str(q_obj['Q']).split('.',1)  # split 'Q':'1.4'
            q_obj['WI'] = int(Q_str[0])
            q_obj['WF'] = abs(int(Q_str[1]))

        # missing key-value pairs are either taken from default dict or from
        # instance attributes
        for k in q_obj_default.keys():
            if k not in q_obj.keys():
                if not hasattr(self, k):
                    q_obj[k] = q_obj_default[k]
                else:
                    q_obj[k] = getattr(self, k)

        # store parameters as class attributes
        self.WI    = int(q_obj['WI'])
        self.WF    = int(abs(q_obj['WF']))
        self.quant = str(q_obj['quant']).lower()
        self.ovfl  = str(q_obj['ovfl']).lower()
        self.frmt  = str(q_obj['frmt']).lower()

        q_obj['W'] = int(self.WF + self.WI + 1)
        self.W     = q_obj['W']
        q_obj['Q'] = str(self.WI) + '.' + str(self.WF)
        self.Q     = q_obj['Q']

        try:
            self.scale = np.float64(q_obj['scale'])
        except ValueError:
            if q_obj['scale'] == 'int':
                self.scale = 1 << self.WF
            elif q_obj['scale'] == 'norm':
                self.scale = 2.**(-self.WI)
            else:
                raise ValueError

        self.q_obj = q_obj # store quant. dict in instance

        self.LSB = 2. ** -self.WF  # value of LSB
        self.MSB = 2. ** (self.WI - 1)   # value of MSB

        self.MAX =  2. * self.MSB - self.LSB
        self.MIN = -2. * self.MSB

        # Calculate required number of places for different bases from total
        # number of bits:
        if self.frmt == 'dec':
            self.places = int(np.ceil(np.log10(self.W) * np.log10(2.))) + 1
            self.base = 10
        elif self.frmt == 'bin':
            self.places = self.W + 1
            self.base = 2
        elif self.frmt == 'csd':
            self.places = self.W + 1
            self.base = 2
        elif self.frmt == 'hex':
            self.places = int(np.ceil(self.W / 4.)) + 1
            self.base = 16
        elif self.frmt == 'float':
            self.places = 4
            self.base = 0
        else:
            raise Exception(u'Unknown format "%s"!'%(self.frmt))

        self.ovr_flag = 0 # initialize to allow reading when freshly initialized

#------------------------------------------------------------------------------
    def fixp(self, y, scaling='mult'):
        """
        Return fixed-point integer or fractional representation for `y`
        (scalar or array-like) with the same shape as `y`.

        Saturation / two's complement wrapping happens outside the range +/- MSB,
        requantization (round, floor, fix, ...) is applied on the ratio `y / LSB`.

        Parameters
        ----------
        y: scalar or array-like object
            input value (floating point format) to be quantized

        scaling: String
            Determine the scaling before and after quantizing / saturation

            *'mult'* float in, int out:
                `y` is multiplied by `self.scale` *before* quantizing / saturating
            **'div'**: int in, float out:
                `y` is divided by `self.scale` *after* quantizing / saturating.
            **'multdiv'**: float in, float out (default):
                both of the above

            For all other settings, `y` is transformed unscaled.

        Returns
        -------
        float scalar or ndarray
            with the same shape as `y`, in the range
            `-2*self.MSB` ... `2*self.MSB-self.LSB`

        Examples
        --------

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
        >>> # MSB = 2**7, LSB = 2**(-2):
        >>> q_obj_b = {'WI':7, 'WF':2, 'ovfl':'wrap', 'quant':'round'}
        >>> myQb = Fixed(q_obj_b) # instantiate fixed-point object myQb
        >>> bq = myQb.fixed(b)
        >>> bq = bq.astype(btype) # restore original variable type
        """

        #======================================================================
        # (1) : INITIALIZATION
        #       Convert input argument into proper floating point scalars /
        #       arrays and initialize flags
        #======================================================================
        scaling = scaling.lower()
        if np.shape(y):
            # Input is an array:
            #   Create empty arrays for result and overflows with same shape as y
            #   for speedup, test for invalid types
            SCALAR = False
            y = np.asarray(y) # convert lists / tuples / ... to numpy arrays
            yq = np.zeros(y.shape)
            over_pos = over_neg = np.zeros(y.shape, dtype = bool)
            self.ovr_flag = np.zeros(y.shape, dtype = int)

            if np.issubdtype(y.dtype, np.number):
                pass
            elif y.dtype.kind in {'U', 'S'}: # string or unicode
                try:
                    y = y.astype(np.float64) # try to convert to float
                except (TypeError, ValueError):
                    try:
                        np.char.replace(y, ' ', '') # remove all whitespace
                        y = y.astype(complex) # try to convert to complex
                    except (TypeError, ValueError) as e: # try converting elements recursively
                        y = list(map(lambda y_scalar:
                            self.fixp(y_scalar, scaling=scaling), y))
            else:
                logger.error("Argument '{0}' is of type '{1}',\n"
                             "cannot convert to float.".format(y, y.dtype))
                y = np.zeros(y.shape)
        else:
            # Input is a scalar
            SCALAR = True
            # get rid of errors that have occurred upstream
            if y is None or str(y) == "":
                y = 0
            # If y is not a number, remove whitespace and try to convert to
            # to float and or to complex format:
            elif not np.issubdtype(type(y), np.number):
                y = qstr(y)
                y = y.replace(' ','') # remove all whitespace
                try:
                    y = float(y)
                except (TypeError, ValueError):
                    try:
                        y = complex(y)
                    except (TypeError, ValueError) as e:
                        logger.error("Argument '{0}' yields \n {1}".format(y,e))
                        y = 0.0
            over_pos = over_neg = yq = 0
            self.ovr_flag = 0

        # convert pseudo-complex (imag = 0) and complex values to real
        y = np.real_if_close(y)
        if np.iscomplexobj(y):
            logger.warning("Casting complex values to real before quantization!")
            # quantizing complex objects is not supported yet
            y = y.real

        y_in = y # y before scaling / quantizing
        #======================================================================
        # (2) : INPUT SCALING
        #       Multiply by `scale` factor before requantization and saturation
        #       when `scaling=='mult'`or 'multdiv'
        #======================================================================
        if scaling in {'mult', 'multdiv'}:
            y = y * self.scale

        #======================================================================
        # (3) : QUANTIZATION
        #       Divide by LSB to obtain an intermediate format where the
        #       quantization step size = 1.
        #       Next, apply selected quantization method to convert
        #       floating point inputs to "fixpoint integers".
        #       Finally, multiply by LSB to restore original scale.
        #=====================================================================
        y = y / self.LSB

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

        yq = yq * self.LSB
        logger.debug("y_in={0} | y={1} | yq={2}".format(y_in, y, yq))

        #======================================================================
        # (4) : Handle Overflow / saturation w.r.t. to the MSB, returning a
        #       result in the range MIN = -2*MSB ... + 2*MSB-LSB = MAX
        #=====================================================================
        if   self.ovfl == 'none':
            pass
        else:
            # Bool. vectors with '1' for every neg./pos overflow:
            over_neg = (yq < self.MIN)
            over_pos = (yq > self.MAX)
            # create flag / array of flags for pos. / neg. overflows
            self.ovr_flag = over_pos.astype(int) - over_neg.astype(int)
            # No. of pos. / neg. / all overflows occured since last reset:
            self.N_over_neg += np.sum(over_neg)
            self.N_over_pos += np.sum(over_pos)
            self.N_over = self.N_over_neg + self.N_over_pos

            # Replace overflows with Min/Max-Values (saturation):
            if self.ovfl == 'sat':
                yq = np.where(over_pos, self.MAX, yq) # (cond, true, false)
                yq = np.where(over_neg, self.MIN, yq)
            # Replace overflows by two's complement wraparound (wrap)
            elif self.ovfl == 'wrap':
                yq = np.where(over_pos | over_neg,
                    yq - 4. * self.MSB*np.fix((np.sign(yq) * 2 * self.MSB+yq)/(4*self.MSB)), yq)
            else:
                raise Exception('Unknown overflow type "%s"!'%(self.ovfl))
                return None
        #======================================================================
        # (5) : OUTPUT SCALING
        #       Divide result by `scale` factor when `scaling=='div'`or 'multdiv'
        #       to obtain correct scaling for floats
        #       - frmt2float() always returns float
        #       - input_coeffs when quantizing the coefficients
        #       float2frmt passes on the scaling argument
        #======================================================================

        if scaling in {'div', 'multdiv'}:
            yq = yq / self.scale

        if SCALAR and isinstance(yq, np.ndarray):
            yq = yq.item() # convert singleton array to scalar

        return yq

#------------------------------------------------------------------------------
    def resetN(self):
        """ Reset overflow-counters of Fixed object"""
        self.N_points = 0
        self.N_over = 0
        self.N_over_neg = 0
        self.N_over_pos = 0


#------------------------------------------------------------------------------
    def frmt2float(self, y, frmt=None):
        """
        Return floating point representation for fixpoint scalar `y` given in
        format `frmt`.

        When input format is float, return unchanged.

        Else:

        - Remove illegal characters and leading '0's
        - Count number of fractional places `frc_places` and remove radix point
        - Calculate decimal, fractional representation `y_dec` of string,
          using the base and the number of fractional places
        - Calculate two's complement for `W` bits (only for negative bin and hex numbers)
        - Calculate fixpoint float representation `y_float = fixp(y_dec, scaling='div')`,
          dividing the result by `scale`.

        Parameters
        ----------
        y: scalar or string
            to be quantized with the numeric base specified by `frmt`.

        frmt: string (optional)
            any of the formats `float`, `dec`, `bin`, `hex`, `csd`)
            When `frmt` is unspecified, the instance parameter `self.frmt` is used

        Returns
        -------
        quantized floating point (`dtype=np.float64`) representation of input string
        """
        if y == "":
            return 0

        if frmt is None:
            frmt = self.frmt
        frmt = frmt.lower()
        y_float = y_dec = None

        if frmt == 'float32':
            float_frmt = np.float32
        elif frmt == 'float16':
            float_frmt = np.float16

        if frmt == 'float':
            # this handles floats, np scalars + arrays and strings / string arrays
            try:
                y_float = np.float64(y)
            except ValueError:
                try:
                    y_float = np.complex(y).real
                except Exception as e:
                    y_float = None
                    logger.warning("Can't convert {0}: {1}".format(y,e))
            return y_float

        else: # {'dec', 'bin', 'hex', 'csd'}
         # Find the number of places before the first radix point (if there is one)
         # and join integer and fractional parts
         # when returned string is empty, skip general conversions and rely on error handling
         # of individual routines
         # remove illegal characters and trailing zeros
            val_str = re.sub(self.FRMT_REGEX[frmt],r'', qstr(y)).lstrip('0')
            if len(val_str) > 0:
                val_str = val_str.replace(',','.') # ',' -> '.' for German-style numbers
                if val_str[0] == '.': # prepend '0' when the number starts with '.'
                    val_str = '0' + val_str

                # count number of fractional places in string
                try:
                    _, frc_str = val_str.split('.') # split into integer and fractional places
                    frc_places = len(frc_str)
                except ValueError: # no fractional part
                    frc_places = 0

                raw_str = val_str.replace('.','') # join integer and fractional part

                logger.debug("y={0}, val_str={1}, raw_str={2} ".format(y, val_str, raw_str))
            else:
                return 0.0

        # (1) calculate the decimal value of the input string using np.float64()
        #     which takes the number of decimal places into account.
        # (2) quantize and saturate
        # (3) divide by scale
        if frmt == 'dec':
            # try to convert string -> float directly with decimal point position
            try:
                y_dec = y_float = self.fixp(val_str, scaling='div')
            except Exception as e:
                logger.warning(e)

        elif frmt in {'hex', 'bin'}:
            # - Glue integer and fractional part to a string without radix point
            # - Check for a negative sign, use this information only in the end
            # - Divide by <base> ** <number of fractional places> for correct scaling
            # - Strip MSBs outside fixpoint range
            # - Transform numbers in negative 2's complement to negative floats.
            # - Calculate the fixpoint representation for correct saturation / quantization
            neg_sign = False
            try:
                if raw_str[0] == '-':
                    neg_sign = True
                    raw_str = raw_str.lstrip('-')

                y_dec = abs(int(raw_str, self.base) / self.base**frc_places)

                if y_dec == 0:  # avoid log2(0)
                    return 0

                int_bits = max(int(np.floor(np.log2(y_dec))) + 1, 0)
                # When number is outside fixpoint range, discard MSBs:
                if int_bits > self.WI + 1:
                    if frmt == 'hex':
                        raw_str = np.binary_repr(int(raw_str, 16))
                    # discard the upper bits outside the valid range
                    raw_str = raw_str[int_bits - self.WI - 1:]

                    # recalculate y_dec for truncated string
                    y_dec = int(raw_str, 2) / self.base**frc_places

                    if y_dec == 0: # avoid log2(0) error in code below
                        return 0

                    int_bits = max(int(np.floor(np.log2(y_dec))) + 1, 0) # ... and int_bits
                # now, y_dec is in the correct range:
                if int_bits <= self.WI: # positive number
                    pass
                elif int_bits == self.WI + 1: # negative, calculate 2's complemente
                    y_dec = y_dec - (1 << int_bits)
                # quantize / saturate / wrap & scale the integer value:
                if neg_sign:
                    y_dec = -y_dec
                y_float = self.fixp(y_dec, scaling='div')
            except Exception as e:
                logger.warning(e)
                y_dec = y_float = None

            logger.debug("MSB={0} | LSB={1} | scale={2}".format(self.MSB, self.LSB, self.scale))
            logger.debug("y_in={0} | y_dec={1}".format(y, y_dec))
        # ----
        elif frmt == 'csd':
            # - Glue integer and fractional part to a string without radix point
            # - Divide by 2 ** <number of fractional places> for correct scaling
            # - Calculate fixpoint representation for saturation / overflow effects

            y_dec = csd2dec_vec(raw_str) # csd -> integer
            if y_dec is not None:
                y_float = self.fixp(y_dec / 2**frc_places, scaling='div')
        # ----
        else:
            logger.error('Unknown output format "%s"!'.format(frmt))

        if frmt != "float":
            logger.debug("MSB={0:g} |  scale={1:g} | raw_str={2} | val_str={3}"\
                         .format(self.MSB, self.scale, raw_str, val_str))
            logger.debug("y={0} | y_dec = {1} | y_float={2}".format(y, y_dec, y_float))


        if y_float is not None:
            return y_float
        else:
            return 0.0

#------------------------------------------------------------------------------
    def float2frmt(self, y):
        """
        Called a.o. by `itemDelegate.displayText()` for on-the-fly number
        conversion. Returns fixpoint representation for `y` (scalar or array-like)
        with numeric format `self.frmt` and `self.W` bits. The result has the
        same shape as `y`.

        The float is multiplied by `self.scale` and quantized / saturated
        using fixp() for all formats before it is converted to different number
        formats.

        Parameters
        ----------
        y: scalar or array-like
            y has to be an integer or float decimal number either numeric or in
            string format.

        Returns
        -------
        A string, a float or an ndarray of float or string is returned in the
        numeric format set in `self.frmt`. It has the same shape as `y`. For all
        formats except `float` a fixpoint representation with `self.W` binary
        digits is returned.
        """

        """
        Define vectorized functions using numpys automatic type casting:
        Vectorized functions for inserting binary point in string `bin_str`
        after position `pos`.

        Usage:  insert_binary_point(bin_str, pos)

        Parameters: bin_str : string
                    pos     : integer
        """
        insert_binary_point = np.vectorize(lambda bin_str, pos:(
                                    bin_str[:pos+1] + "." + bin_str[pos+1:]))

        binary_repr_vec = np.frompyfunc(np.binary_repr, 2, 1)
        #======================================================================

        if self.frmt == 'float': # return float input value unchanged (no string)
            return y
        elif self.frmt == 'float32':
            return np.float32(y)
        elif self.frmt == 'float16':
            return np.float16(y)

        elif self.frmt in {'hex', 'bin', 'dec', 'csd'}:
            # return a quantized & saturated / wrapped fixpoint (type float) for y
            y_fix = self.fixp(y, scaling='mult')

            if self.frmt == 'dec':
                if self.WF == 0:
                    y_str = np.int64(y_fix) # get rid of trailing zero
                    # y_str = np.char.mod('%d', y_fix)
                    # elementwise conversion from integer (%d) to string
                    # see https://docs.scipy.org/doc/numpy/reference/routines.char.html
                else:
                    # y_str = np.char.mod('%f',y_fix)
                    y_str = y_fix
            elif self.frmt == 'csd':
                y_str = dec2csd_vec(y_fix, self.WF) # convert with WF fractional bits

            else: # bin or hex
                # represent fixpoint number as integer in the range -2**(W-1) ... 2**(W-1)
                y_fix_int = np.int64(np.round(y_fix / self.LSB))
                # convert to (array of) string with 2's complement binary
                y_bin_str = binary_repr_vec(y_fix_int, self.W)

                if self.frmt == 'hex':
                    y_str = bin2hex_vec(y_bin_str, self.WI)

                else: # self.frmt == 'bin':
                    # insert radix point if required
                    if self.WF > 0:
                        y_str = insert_binary_point(y_bin_str, self.WI)
                    else:
                        y_str = y_bin_str

            if isinstance(y_str, np.ndarray) and np.ndim(y_str) < 1:
                y_str = y_str.item() # convert singleton array to scalar

            return y_str
        else:
            raise Exception('Unknown output format "%s"!'%(self.frmt))
            return None

########################################
if __name__=='__main__':
    """
    Run a simple test with python -m pyfda.pyfda_fix_lib
    or a more elaborate one with
    python -m pyfda.tests.test_pyfda_fix_lib
    """
    import pprint

    q_obj = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'scale': 1}
    myQ = Fixed(q_obj) # instantiate fixpoint object with settings above
    y_list = [-1.1, -1.0, -0.5, 0, 0.5, 0.99, 1.0]

    myQ.setQobj(q_obj)

    print("\nTesting float2frmt()\n====================")
    pprint.pprint(q_obj)
    for y in y_list:
        print("y = {0}\t->\ty_fix = {1}".format(y, myQ.float2frmt(y)))

    print("\nTesting frmt2float()\n====================")
    q_obj = {'WI':3, 'WF':3, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'scale': 2}
    pprint.pprint(q_obj)
    myQ.setQobj(q_obj)
    dec_list = [-9, -8, -7, -4.0, -3.578, 0, 0.5, 4, 7, 8]
    for dec in dec_list:
        print("y={0}\t->\ty_fix={1} ({2})".format(dec, myQ.frmt2float(dec), myQ.frmt))
