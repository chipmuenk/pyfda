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
# ===========================================================================
import re
import inspect

import numpy as np
from numpy.lib.function_base import iterable
try:
    import deltasigma as ds
    from deltasigma import simulateDSM, synthesizeNTF
    print("DS Backends:", ds.simulation_backends)
    DS = True
except ImportError:
    DS = False

import logging
logger = logging.getLogger(__name__)


# TODO: Absolute value for WI is taken, no negative WI specifications possible
# TODO: Vecorization for hex / csd functions (frmt2float)

__version__ = 0.6


def qstr(text):
    """ carefully replace qstr() function - only needed for Py2 compatibility """
    return str(text)


def bin2hex(bin_str, WI=0):
    """
    Convert number `bin_str` in binary format to hex formatted string.
    `bin_str` is prepended / appended with zeros until the number of bits before
    and after the radix point (position given by `WI`) is a multiple of 4.
    """

    wmap = {
        '0000': '0',
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
        '1111': 'F'
        }

    hex_str = ""

    if WI > 0:
        # slice string with integer bits and prepend with zeros to obtain a
        # multiple of 4 length:
        bin_i_str = bin_str[:WI+1]
        while (len(bin_i_str) % 4 != 0):
            bin_i_str = "0" + bin_i_str

        i = 0
        while (i < len(bin_i_str)):  # map chunks of 4 binary bits to one hex digit
            hex_str = hex_str + wmap[bin_i_str[i:i + 4]]
            i = i + 4
    else:
        hex_str = bin_str[0]  # copy MSB as sign bit

    WF = len(bin_str) - WI - 1
    # slice string with fractional bits and append with zeros to obtain a
    # multiple of 4 length:
    if WF > 0:
        hex_str = hex_str + '.'
        bin_f_str = bin_str[WI+1:]

        while (len(bin_f_str) % 4 != 0):
            bin_f_str = bin_f_str + "0"

        i = 0
        while (i < len(bin_f_str)):  # map chunks of 4 binary bits to one hex digit
            hex_str = hex_str + wmap[bin_f_str[i:i + 4]]
            i = i + 4

    # hex_str = hex_str.lstrip("0") # remove leading zeros
    hex_str = "0" if len(hex_str) == 0 else hex_str
    return hex_str


bin2hex_vec = np.vectorize(bin2hex)  # safer than frompyfunction()


# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
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
    if dec_val == 0:
        return '0'
    if np.abs(dec_val) < 1.0:
        k = 0
    else:
        k = int(np.ceil(np.log2(np.abs(dec_val) * 1.5)))

    # logger.debug("CSD: Converting {0:f} to {1:d}.{2:d} format".format(dec_val, k, WF))

    # Initialize CSD calculation
    csd_digits = []
    remainder = dec_val
    prev_non_zero = False
    k -= 1  # current exponent in the CSD string under construction

    while(k >= -WF):  # has the last fractional digit been reached
        limit = pow(2.0, k+1) / 3.0

        # logger.debug("\t{0} - {1}".format(remainder, limit))

        # decimal point?
        if k == -1:
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
                    csd_digits.extend(['0.'])
            else:
                csd_digits.extend(['.'])

        # convert the number
        if prev_non_zero:
            csd_digits.extend(['0'])
            prev_non_zero = False

        elif remainder > limit:
            csd_digits.extend(['+'])
            remainder -= pow(2.0, k)
            prev_non_zero = True

        elif remainder < -limit:
            csd_digits.extend(['-'])
            remainder += pow(2.0, k)
            prev_non_zero = True

        else:
            csd_digits.extend(['0'])
            prev_non_zero = False

        k -= 1

    # Always have something before the point
#    if np.abs(dec_val) < 1.0:
#        csd_digits.insert(0, '0')

    csd_str = "".join(csd_digits)

    # logger.debug("CSD result = {0}".format(csd_str))

#    if WF > 0:
#        csd_str = csd_str[:-WF] + "." + csd_str[-WF:]

    return csd_str


dec2csd_vec = np.frompyfunc(dec2csd, 2, 1)


# ------------------------------------------------------------------------------
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
    # logger.debug("Converting: {0}".format(csd_str))

    # Intialize calculation, start with the MSB (integer)
    msb_power = len(csd_str) - 1
    dec_val = 0.0

    # start from the MSB and work all the way down to the last digit
    for ii in range(len(csd_str)):

        power_of_two = 2.0**(msb_power-ii)

        if csd_str[ii] == '+':
            dec_val += power_of_two
        elif csd_str[ii] == '-':
            dec_val -= power_of_two
        # else
        #    ... all other values are ignored

        # logger.debug('  "{0:s}" (QI = {1:d}); 2**{2:d} = {3}; Num={4:f}'.format(
        #        csd_str[ii], len(csd_str), msb_power-ii, power_of_two, dec_val))

    return dec_val


# csd2dec_vec = np.frompyfunc(csd2dec, 1, 1)
csd2dec_vec = np.vectorize(csd2dec)  # safer than np.frompyfunc()


# ------------------------------------------------------------------------
class Fixed(object):
    """
    Implement binary quantization of signed scalar or array-like objects
    in the form `Q = WI.WF` where WI and WF are the wordlength of integer resp.
    fractional part; total wordlength is `W = WI + WF + 1` due to the sign bit.

    Examples
    --------

    Define a dictionary with the format options and pass it to the constructor:

    >>> q_dict = {'WI':1, 'WF':14, 'ovfl':'sat', 'quant':'round'} # or
    >>> q_dict = {'Q':'1.14', 'ovfl':'none', 'quant':'round'}
    >>> myQ = Fixed(q_dict)


    Parameters
    ----------
    q_dict : dict
        define quantization options with the following keys

    * **'WG'** : number of guard bits, default: 0

    * **'WI'** : number of integer bits, default: 0

    * **'WF'** : number of fractional bits; default: 15

    * **'W'**  : total word length; WI + WF + 1 = W (1 sign bit). When WI and / or
                 WF are missing, WI = W - 1 and WF = 0.

    * **'Q'**  : Quantization format as string, e.g. '0.15', it is translated
                 to`WI` and `WF`. When both `Q` and `WI` / `WF`
                 are given, `Q` is ignored

    * **'quant'** : Quantization method, optional; default = 'floor'

      - 'floor': (default) largest integer `I` such that :math:`I \\le x`
                 (= binary truncation)
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

    * **'fx_base'** : Output format, optional; default = 'float'

      - 'float' : (default)
      - 'dec'  : decimal integer, scaled by :math:`2^{WF}`
      - 'bin'  : binary string, scaled by :math:`2^{WF}`
      - 'hex'  : hex string, scaled by :math:`2^{WF}`
      - 'csd'  : canonically signed digit string, scaled by :math:`2^{WF}`

    * **'scale'** : Float or a keyword, the factor between the fixpoint integer
            representation (FXP) and its "real world" floating point value (RWV).
            If ``scale`` is a float, this value is used, RWV = FXP / scale.
            By default, scale = 1 << WI.

            Examples:
                WI.WF = 3.0, FXP = "b0110." = 6,   scale = 8 -> RWV = 6 / 8   = 0.75
                WI.WF = 1.2, FXP = "b01.10" = 1.5, scale = 2 -> RWV = 1.5 / 2 = 0.75

            Alternatively, if:

                - ``q_dict['scale'] == 'int'``:   scale = 1 << self.q_dict['WF']

                - ``q_dict['scale'] == 'norm'``:  scale = 2.**(-self.q_dict['WI'])
    * **quant** : str
        Quantization behaviour ('floor', 'round', ...)

    * **'ovfl'**  : str
        Overflow behaviour ('wrap', 'sat', ...)

    * **'fx_base'** : str
        target output format ('float', 'dec', 'bin', 'hex', 'csd')


    The following key: value pairs are calculated from other parameters and
    can / should be considered as read-only.

    * **'places'** : integer
        number of places required for printing in the selected number format.
        For binary formats, this is the same as the wordlength. Calculated
        from the numeric base 'self.base' (not used outside this class) and
        the total word length 'W'.

    * **'LSB'** : float
        value of LSB (smallest quantization step), calculated from `WI` and `WF`

    * **'MSB'** : float
        value of most significant bit (MSB), calculated from `WI` and `WF`

    * **'MIN'** : float
        most negative representable value, calculated from `WI` and `WF`

    * **'MAX'** : float
        largest representable value, calculated from `WI` and `WF`

    Overflow flags and counters are set in `self.fixp()` and reset in `self.reset_N()`

    * **'ovr_flag'** : integer or integer array (same shape as input argument)
        overflow flag, meaning:

                        0 : no overflow

                        +1: positive overflow

                        -1: negative overflow

        has occured during last fixpoint conversion.

    * **'N'** : integer
        total number of simulation data points

    * **'N_over'** : integer
        total number of overflows

    * **'N_over_neg'** : integer
        number of negative overflows

    * **'N_over_pos'** : integer
        number of positive overflows

    Attributes
    ----------
    q_dict : dict
        A reference to the quantization dictionary passed during construction
        (see above). This dictionary is updated here and can be accessed from
        outside.

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

    def __init__(self, q_dict):
        """
        Construct `Fixed` object with dict `q_dict`
        """
        # define valid keys and default values for quantization dict
        self.q_dict_default = {
            'WG': 0, 'WI': 0, 'WF': 15, 'W': 16, 'Q': '0.15', 'quant': 'round',
            'ovfl': 'sat', 'fx_base': 'float', 'qfrmt': 'qfrac', 'qfrmt_last': 'qfrac',
            'scale': 1}
        # these keys are calculated and should be regarded as read-only
        self.q_dict_default_ro = {
            'N': 0, 'ovr_flag': 0, 'N_over': 0, 'N_over_neg': 0, 'N_over_pos': 0,
            'MSB': 1, 'LSB': 6, 'MAX': 2, 'MIN': -2, 'places': 4}

        # test if all passed keys of quantizer object are valid
        self.verify_q_dict_keys(q_dict)

        # missing key-value pairs are taken from the default dict
        for k in self.q_dict_default.keys():  # loop over all defined keys
            if k not in q_dict.keys():  # key is not in passed dict, get k:v pair from ...
                q_dict[k] = self.q_dict_default[k]  # ... default dict

        # create a reference to the dict passed during construction as instance attribute
        self.q_dict = q_dict

        self.set_qdict({})  # trigger calculation of parameters
        self.resetN()       # initialize overflow-counter

        # arguments for regex replacement with illegal characters
        # ^ means "not", | means "or" and \ escapes
        self.FRMT_REGEX = {
                'bin': r'[^0|1|.|,|\-]',
                'csd': r'[^0|\+|\-|.|,]',
                'dec': r'[^0-9Ee|.|,|\-]',
                'hex': r'[^0-9A-Fa-f|.|,|\-]'
                        }
        # provide frmt2float function for arrays, swallow the `self` argument
        self.frmt2float_vec = np.vectorize(self.frmt2float_scalar, excluded='self')

    def verify_q_dict_keys(self, q_dict: dict) -> None:
        """
        Check against the merged `self.q_dict_default` and `self.q_dict_default_ro`
        dictionaries whether all keys in the passed `q_dict` dictionary are valid.

        Unknown keys throw an error message
        """
        for k in q_dict.keys():
            if k not in {**self.q_dict_default, **self.q_dict_default_ro}.keys():
                logger.error(u'Unknown Key "{0:s}"!'.format(k))

    def set_qdict(self, d: dict) -> None:
        """
        Update the instance quantization dict `self.q_dict` from parameter `d`:

        * Transform dict entries for `WF`, `WI`, `W` and `Q` into each other

        * Calculate parameters `MSB`, `LSB`, `MIN` and `MAX` from quantization params

        * Calculate number of places required for printing from `fx_base` and `W`

        When the passed dictionary `d` is empty, update the quantization dict from
        its `WF` and `WI` entries.

        Check the docstring of class `Fixed()` for details on quantization
        """
        q_d = d.copy()  # create local copy to avoid modification of passed dict

        self.verify_q_dict_keys(q_d)  # check whether all keys are valid

        # Transform `WG`,  `WI`, `WF`, `W` and `Q` parameters into each other
        if q_d == {}:
            q_d['W'] = self.q_dict['WG'] + self.q_dict['WI'] + self.q_dict['WF'] + 1
            q_d['Q'] = str(self.q_dict['WG'] + self.q_dict['WI']) + "."\
                + str(self.q_dict['WF'])
        elif 'WI' in q_d and 'WF' in q_d:
            if 'WG' in q_d:
                q_d['WG'] = abs(int(q_d['WG']))  # sanitize WG
            else:
                q_d['WG'] = 0
            q_d['WI'] = int(q_d['WI'])  # sanitize WI
            q_d['WF'] = abs(int(q_d['WF']))  # and WF
            q_d['W'] = q_d['WG'] + q_d['WI'] + q_d['WF'] + 1
            q_d['Q'] = str(q_d['WI']) + "." + str(q_d['WF'])
        elif 'W' in q_d:
            q_d['W'] = int(q_d['W'])  # sanitize W
            q_d['WG'] = 0
            q_d['WI'] = int(q_d['W']) - 1
            q_d['WF'] = 0
            q_d['Q'] = str(q_d['WI']) + ".0"
        elif 'Q' in q_d:
            Q_str = str(q_d['Q']).split('.', 1)  # split 'Q':'1.4'
            q_d['WG'] = 0
            q_d['WI'] = int(Q_str[0])
            q_d['WF'] = abs(int(Q_str[1]))
            q_d['W'] = q_d['WI'] + q_d['WF'] + 1

        self.q_dict.update(q_d)  # merge q_d into self.q_dict

        # Calculate min., max., LSB and MSB from word lengths
        self.q_dict['LSB'] = 2. ** -self.q_dict['WF']
        self.q_dict['MSB'] = 2. ** (self.q_dict['WG'] + self.q_dict['WI'] - 1)

        self.q_dict['MAX'] =  2. * self.q_dict['MSB'] - self.q_dict['LSB']
        self.q_dict['MIN'] = -2. * self.q_dict['MSB']

        # Calculate required number of places for different bases from total
        # number of bits:
        if self.q_dict['fx_base'] == 'dec':
            self.q_dict['places'] = int(
                np.ceil(np.log10(self.q_dict['W']) * np.log10(2.))) + 1
            self.base = 10
        elif self.q_dict['fx_base'] == 'bin':
            self.q_dict['places'] = self.q_dict['W'] + 1
            self.base = 2
        elif self.q_dict['fx_base'] == 'csd':
            self.q_dict['places'] = self.q_dict['W'] + 1
            self.base = 2
        elif self.q_dict['fx_base'] == 'hex':
            self.q_dict['places'] = int(np.ceil(self.q_dict['W'] / 4.)) + 1
            self.base = 16
        elif self.q_dict['fx_base'] == 'float':
            self.q_dict['places'] = 4
            self.base = 0
        else:
            raise Exception(
                u'Unknown number format "{0:s}"!'.format(self.q_dict['fx_base']))

# ------------------------------------------------------------------------------
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
                `y` is multiplied by `self.q_dict['scale'])` *before* quantizing / saturating
            **'div'**: int in, float out:
                `y` is divided by `scale` *after* quantizing / saturating.
            **'multdiv'**: float in, float out (default):
                both of the above

            For all other settings, `y` is transformed unscaled.

        Returns
        -------
        float scalar or ndarray
            with the same shape as `y`, in the range
            `-2*self.q_dict['MSB']` ... `2*self.q_dict['MSB']-self.q_dict['LSB']`

        Examples
        --------

        >>> q_obj_a = {'WI':1, 'WF':6, 'ovfl':'sat', 'quant':'round'}
        >>> myQa = Fixed(q_obj_a) # instantiate fixed-point object myQa
        >>> myQa.resetN()  # reset overflow counter
        >>> a = np.arange(0,5, 0.05) # create input signal

        >>> aq = myQa.fixed(a) # quantize input signal
        >>> plt.plot(a, aq) # plot quantized vs. original signal
        >>> print(myQa.q_dict('N_over'), "overflows!") # print number of overflows

        >>> # Convert output to same format as input:
        >>> b = np.arange(200, dtype = np.int16)
        >>> btype = np.result_type(b)
        >>> # MSB = 2**7, LSB = 2**(-2):
        >>> q_obj_b = {'WI':7, 'WF':2, 'ovfl':'wrap', 'quant':'round'}
        >>> myQb = Fixed(q_obj_b) # instantiate fixed-point object myQb
        >>> bq = myQb.fixed(b)
        >>> bq = bq.astype(btype) # restore original variable type
        """

        # ======================================================================
        # (1) : INITIALIZATION
        #       Convert input argument into proper floating point scalars /
        #       arrays and initialize flags
        # ======================================================================
        scaling = scaling.lower()
        # use values from dict for initialization
        N_over_neg = self.q_dict['N_over_neg']
        N_over_pos = self.q_dict['N_over_pos']
        N = self.q_dict['N']

        if np.shape(y):
            # Input is an array:
            #   Create empty arrays for result and overflows with same shape as y
            #   for speedup, test for invalid types
            SCALAR = False
            y = np.asarray(y)  # convert lists / tuples / ... to numpy arrays
            yq = np.zeros(y.shape)
            over_pos = over_neg = np.zeros(y.shape, dtype=bool)
            ovr_flag = np.zeros(y.shape, dtype=int)

            if np.issubdtype(y.dtype, np.number):  # numpy number type
                N += y.size
            elif y.dtype.kind in {'U', 'S'}:  # string or unicode
                try:
                    y = y.astype(np.float64)  # try to convert to float
                    N += y.size
                except (TypeError, ValueError):
                    try:
                        np.char.replace(y, ' ', '')  # remove all whitespace
                        y = y.astype(complex)  # try to convert to complex
                        N += y.size * 2
                    # try converting elements recursively:
                    except (TypeError, ValueError):
                        y = np.asarray(list(map(lambda y_scalar:
                                            self.fixp(y_scalar, scaling=scaling), y)))
                        N += y.size
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
                y = str(y)
                y = y.replace(' ', '')  # remove all whitespace
                try:
                    y = float(y)
                except (TypeError, ValueError):
                    try:
                        y = complex(y)
                    except (TypeError, ValueError) as e:
                        logger.error(f"'{y}' cannot be converted to a number.")
                        y = 0.0
            over_pos = over_neg = yq = 0
            ovr_flag = 0
            N += 1

        # convert pseudo-complex (imag = 0) and complex values to real
        y = np.real_if_close(y)
        if np.iscomplexobj(y):
            logger.warning("Casting complex values to real before quantization!")
            # quantizing complex objects is not supported yet
            y = y.real

        y_in = y  # y before scaling / quantizing
        # ======================================================================
        # (2) : INPUT SCALING
        #       Multiply by `scale` factor before requantization and saturation
        #       when `scaling=='mult'`or 'multdiv'
        # ======================================================================
        if scaling in {'mult', 'multdiv'}:
            y = y * self.q_dict['scale']

        # ======================================================================
        # (3) : QUANTIZATION
        #       Divide by LSB to obtain an intermediate format where the
        #       quantization step size = 1.
        #       Next, apply selected quantization method to convert
        #       floating point inputs to "fixpoint integers".
        #       Finally, multiply by LSB to restore original scale.
        # ======================================================================
        y = y / self.q_dict['LSB']

        if self.q_dict['quant'] == 'floor':
            yq = np.floor(y)  # largest integer i, such that i <= x (= binary truncation)
        elif self.q_dict['quant'] == 'round':
            yq = np.round(y)  # rounding, also = binary rounding
        elif self.q_dict['quant'] == 'fix':
            yq = np.fix(y)  # round to nearest integer towards zero ("Betragsschneiden")
        elif self.q_dict['quant'] == 'ceil':
            yq = np.ceil(y)  # smallest integer i, such that i >= x
        elif self.q_dict['quant'] == 'rint':
            yq = np.rint(y)  # round towards nearest int
        elif self.q_dict['quant'] == 'dsm':
            if DS:
                # Synthesize DSM loop filter,
                # TODO: parameters should be adjustable via quantizer dict
                H = synthesizeNTF(order=3, osr=64, opt=1)
                # Calculate DSM stream and shift/scale it from -1 ... +1 to
                # 0 ... 1 sequence
                yq = (simulateDSM(y*self.q_dict['LSB'], H)[0]+1)/(2*self.q_dict['LSB'])
                # returns four ndarrays:
                # v: quantizer output (-1 or 1)
                # xn: modulator states.
                # xmax: maximum value that each state reached during simulation
                # y: The quantizer input (ie the modulator output).
            else:
                raise Exception('"deltasigma" Toolbox not found.\n'
                                'Try installing it with "pip install deltasigma".')
        elif self.q_dict['quant'] == 'none':
            yq = y  # return unquantized value
        else:
            raise Exception(
                f'''Unknown Requantization type "{self.q_dict['quant']:s}"!''')
        yq = yq * self.q_dict['LSB']
        # logger.debug("y_in={0} | y={1} | yq={2}".format(y_in, y, yq))

        # ======================================================================
        # (4) : Handle Overflow / saturation w.r.t. to the MSB, returning a
        #       result in the range MIN = -2*MSB ... + 2*MSB-LSB = MAX
        # ====================================================================
        if self.q_dict['ovfl'] == 'none':
            pass
        else:
            # Bool. vectors with '1' for every neg./pos overflow:
            over_neg = (yq < self.q_dict['MIN'])
            over_pos = (yq > self.q_dict['MAX'])
            # create flag / array of flags for pos. / neg. overflows
            ovr_flag = over_pos.astype(int) - over_neg.astype(int)
            # No. of pos. / neg. / all overflows occured since last reset:
            N_over_neg += np.sum(over_neg)
            N_over_pos += np.sum(over_pos)
            N_over = N_over_neg + N_over_pos

            self.q_dict.update(
               {'N_over_pos': N_over_pos, 'N_over_neg': N_over_neg, 'N_over': N_over,
                'N': N, 'ovr_flag': ovr_flag})

            # Replace overflows with Min/Max-Values (saturation):
            if self.q_dict['ovfl'] == 'sat':
                yq = np.where(over_pos, self.q_dict['MAX'], yq)  # (cond, true, false)
                yq = np.where(over_neg, self.q_dict['MIN'], yq)
            # Replace overflows by two's complement wraparound (wrap)
            elif self.q_dict['ovfl'] == 'wrap':
                yq = np.where(
                    over_pos | over_neg,
                    yq - 4. * self.q_dict['MSB'] * np.fix(
                        (np.sign(yq) * 2 * self.q_dict['MSB'] + yq)
                            / (4 * self.q_dict['MSB'])), yq)
            else:
                raise Exception(
                    f"""Unknown overflow type "{self.q_dict['ovfl']:s}"!""")

        # ======================================================================
        # (5) : OUTPUT SCALING
        #       Divide result by `scale` factor when `scaling=='div'`or 'multdiv'
        #       to obtain correct scaling for floats
        #       - frmt2float() always returns float
        #       - input_coeffs when quantizing the coefficients
        #       float2frmt passes on the scaling argument
        # ======================================================================

        if scaling in {'div', 'multdiv'}:
            yq = yq / self.q_dict['scale']

        if SCALAR and isinstance(yq, np.ndarray):
            yq = yq.item()  # convert singleton array to scalar

        return yq

    # --------------------------------------------------------------------------
    def resetN(self):
        """ Reset counters and overflow-flag of Fixed object """
        frm = inspect.stack()[1]
        logger.debug("'reset_N' called from {0}.{1}():{2}.".
                     format(inspect.getmodule(frm[0]).__name__.split('.')[-1],
                            frm[3], frm[2]))
        self.q_dict.update(
            {'N': 0, 'N_over': 0, 'N_over_neg': 0, 'N_over_pos': 0, 'ovr_flag' : 0})

    # --------------------------------------------------------------------------
    def frmt2float(self, y, frmt=None):
        """
        Return floating point representation for fixpoint `y` (scalar or array)
        given in format `frmt`.

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
        y: scalar or string or array of scalars or strings in number format 'fx_base'

        frmt: string (optional)
            any of the formats `float`, `dec`, `bin`, `hex`, `csd`)
            When `frmt` is unspecified, the instance parameter `self.q_dict['fx_base']`
            is used.

        Returns
        -------
        Quantized floating point (`dtype=np.float64`) representation of input string
        of same shape as `y`.
        """

        # ----------------------------------------------------------------------
        if frmt is None:
            frmt = self.q_dict['fx_base']
        frmt = frmt.lower()

        if y is None:
            return 0
        elif np.isscalar(y):
            if not y:
                return 0
            else:
                if np.all((y == "")):
                    return np.zeros_like(y)
        if isinstance(y, np.str_):
            # logger.warning("Input format 'np.str_' not supported!\n\t{0}".format(y))
            y = str(y)

        y_float = y_dec = None

        if frmt == 'float32':
            float_frmt = np.float32
            # TODO: not implemented yet
        elif frmt == 'float16':
            # TODO: not implemented yet
            float_frmt = np.float16

        if frmt == 'float':
            # this handles floats, np scalars + arrays and strings / string arrays
            try:
                y_float = np.float64(y)
            except ValueError:
                try:
                    y_float = np.complex(y)
                except Exception:
                    y_float = 0.0
                    logger.warning(
                        f'\n\tCannot convert "{y}" of type "{type(y).__name__}" '
                        f'to float or complex, setting to zero.')
            return y_float

        elif np.isscalar(y):
            return self.frmt2float_scalar(y, frmt=frmt)
        else:
            return self.frmt2float_vec(y, frmt=frmt)

    # --------------------------------------------------------------------------
    def frmt2float_scalar(self, y, frmt=None):
        """
        Convert the formats 'dec', 'bin', 'hex', 'csd' to float

        Find the number of places before the first radix point (if there is one)
        and join integer and fractional parts
        when returned string is empty, skip general conversions and rely on
        error handling of individual routines,
        remove illegal characters and trailing zeros
        """
        val_str = re.sub(self.FRMT_REGEX[frmt], r'', str(y)).lstrip('0')
        if len(val_str) > 0:
            val_str = val_str.replace(',', '.')  # ',' -> '.' for German-style numbers
            if val_str[0] == '.':  # prepend '0' when the number starts with '.'
                val_str = '0' + val_str

            # count number of fractional places in string
            try:
                # split into integer and fractional places
                _, frc_str = val_str.split('.')
                frc_places = len(frc_str)
            except ValueError:  # no fractional part
                frc_places = 0

            raw_str = val_str.replace('.', '')  # join integer and fractional part

            # logger.debug(f"y={y}, val_str={val_str}, raw_str={raw_str}")
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
            # - Calculate the fixpoint representation for correct saturation /
            #   quantization
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
                if int_bits > self.q_dict['WI'] + 1:
                    if frmt == 'hex':
                        raw_str = np.binary_repr(int(raw_str, 16))
                    # discard the upper bits outside the valid range
                    raw_str = raw_str[int_bits - self.q_dict['WI'] - 1:]

                    # recalculate y_dec for truncated string
                    y_dec = int(raw_str, 2) / self.base**frc_places

                    if y_dec == 0:  # avoid log2(0) error in code below
                        return 0

                    int_bits = max(int(np.floor(np.log2(y_dec))) + 1, 0)
                # now, y_dec is in the correct range:
                if int_bits <= self.q_dict['WI']:  # positive number
                    pass
                elif int_bits == self.q_dict['WI'] + 1:
                    # negative, calculate 2's complement
                    y_dec = y_dec - (1 << int_bits)
                # quantize / saturate / wrap & scale the integer value:
                if neg_sign:
                    y_dec = -y_dec
                y_float = self.fixp(y_dec, scaling='div')
            except Exception as e:
                logger.warning(e)
                y_dec = y_float = None

            # logger.debug(f"MSB={self.q_dict['MSB']} | LSB={self.q_dict['LSB']} | scale={self.q_dict['scale'])}")
            # logger.debug(f"y_in={y} | y_dec={y_dec}")
        # ----
        elif frmt == 'csd':
            # - Glue integer and fractional part to a string without radix point
            # - Divide by 2 ** <number of fractional places> for correct scaling
            # - Calculate fixpoint representation for saturation / overflow effects

            y_dec = csd2dec_vec(raw_str)  # csd -> integer
            if y_dec is not None:
                y_float = self.fixp(y_dec / 2**frc_places, scaling='div')
        # ----
        else:
            logger.error(f'Unknown output format "{frmt}"!')

        # if frmt != "float":
            # logger.debug("MSB={0:g} |  scale={1:g} | raw_str={2} | val_str={3}"\
            #             .format(self.q_dict['MSB'], self.q_dict['scale']), raw_str, val_str))
            # logger.debug("y={0} | y_dec = {1} | y_float={2}".format(y, y_dec, y_float))

        if y_float is not None:
            return y_float
        else:
            return 0.0

    # --------------------------------------------------------------------------
    def float2frmt(self, y):
        """
        Called a.o. by `itemDelegate.displayText()` for on-the-fly number
        conversion. Returns fixpoint representation for `y` (scalar or array-like)
        with numeric format `self.frmt` and `self.q_dict['W']` bits. The result has the
        same shape as `y`.

        The float is multiplied by `self.q_dict['scale'])` and quantized / saturated
        using `self.fixp()` for all formats before it is converted to different number
        formats.

        Parameters
        ----------
        y: scalar or array-like
            y has to be an integer or float decimal number either numeric or in
            string format.

        Returns
        -------
        A string, a float or an ndarray of float or string is returned in the
        numeric format set in `self.q_dict['fx_base'])`. It has the same shape as `y`.
         For all formats except `float` a fixpoint representation with
         `self.q_dict['W']` binary digits is returned.


        Define vectorized functions using numpys automatic type casting:
        Vectorized functions for inserting binary point in string `bin_str`
        after position `pos`.

        Usage:  insert_binary_point(bin_str, pos)

        Parameters: bin_str : string
                    pos     : integer
        """
        insert_binary_point = np.vectorize(lambda bin_str, pos: (
                                    bin_str[:pos+1] + "." + bin_str[pos+1:]))

        binary_repr_vec = np.frompyfunc(np.binary_repr, 2, 1)
        # ======================================================================

        if self.q_dict['fx_base'] == 'float':  # return float input value unchanged (no string)
            return y
        elif self.q_dict['fx_base'] == 'float32':
            return np.float32(y)
        elif self.q_dict['fx_base'] == 'float16':
            return np.float16(y)

        elif self.q_dict['fx_base'] in {'hex', 'bin', 'dec', 'csd'}:
            # return a quantized & saturated / wrapped fixpoint (type float) for y
            y_fix = self.fixp(y, scaling='mult')

            if self.q_dict['fx_base'] == 'dec':
                if self.q_dict['WF'] == 0:
                    y_str = np.int64(y_fix)  # get rid of trailing zero
                    # y_str = np.char.mod('%d', y_fix)
                    # elementwise conversion from integer (%d) to string
                    # see https://docs.scipy.org/doc/numpy/reference/routines.char.html
                else:
                    # y_str = np.char.mod('%f',y_fix)
                    y_str = y_fix
            elif self.q_dict['fx_base'] == 'csd':
                y_str = dec2csd_vec(y_fix, self.q_dict['WF'])  # convert with WF fractional bits

            else:  # bin or hex
                # represent fixpoint number as integer in the range -2**(W-1) ... 2**(W-1)
                y_fix_int = np.int64(np.round(y_fix / self.q_dict['LSB']))
                # convert to (array of) string with 2's complement binary
                y_bin_str = binary_repr_vec(y_fix_int, self.q_dict['W'])

                if self.q_dict['fx_base'] == 'hex':
                    y_str = bin2hex_vec(y_bin_str, self.q_dict['WI'])

                else:  # self.q_dict['fx_base']t == 'bin':
                    # insert radix point if required
                    if self.q_dict['WF'] > 0:
                        y_str = insert_binary_point(y_bin_str, self.q_dict['WI'])
                    else:
                        y_str = y_bin_str

            if isinstance(y_str, np.ndarray) and np.ndim(y_str) < 1:
                y_str = y_str.item()  # convert singleton array to scalar

            return y_str
        else:
            raise Exception(f"""Unknown number format "{self.q_dict['fx_base']}"!""")

########################################

# --------------------------------------------------------------------------
def quant_coeffs(coeffs: iterable, QObj, recursive: bool = False) -> list:
    """
    Quantize the coefficients, scale and convert them to a list of integers,
    using the quantization settings of `Fixed()` instance QObj.

    Parameters
    ----------
    coeffs: iterable
        a list or ndarray of coefficients to be quantized

    QObj: dict
        instance of Fixed object containing quantization dict `q_dict`

    recursive: bool
        When `False` (default), process all coefficients. When `True`,
        The first coefficient is ignored (must be 1)

    Returns
    -------
    A list of integer coeffcients, quantized and scaled with the settings
    of the quantization object dict

    """
    logger.debug("quant_coeffs")
    # always use decimal display format for coefficient quantization
    disp_frmt_tmp = QObj.q_dict['fx_base']
    QObj.q_dict['fx_base'] = 'dec'
    QObj.resetN()  # reset all overflow counters

    if coeffs is None:
        logger.error("Coeffs empty!")
    # quantize floating point coefficients with the selected scale (WI.WF),
    # next convert array float  -> array of fixp
    #                           -> list of int (scaled by 2^WF) when `to_int == True`
    if QObj.q_dict['qfrmt'] == 'int':
        QObj.q_dict['scale'] = 1 << QObj.q_dict['WF']
    if recursive:
        # quantize coefficients except for first
        coeff_q = [1] + list(QObj.fixp(coeffs[1:]))
    else:
        # quantize all coefficients
        coeff_q = list(QObj.fixp(coeffs))

    # self.update_disp()  # update display of overflow counter and MSB / LSB

    QObj.q_dict['fx_base'] = disp_frmt_tmp  # restore previous display setting
    return coeff_q


########################################
if __name__ == '__main__':
    """
    Run a simple test with python -m pyfda.libs.pyfda_fix_lib
    or a more elaborate one with
    python -m pyfda.tests.test_pyfda_fix_lib
    """
    import pprint

    q_dict = {'WI': 0, 'WF': 3, 'ovfl': 'sat', 'quant': 'round', 'fx_base': 'dec', 'scale': 1}
    myQ = Fixed(q_dict)  # instantiate fixpoint object with settings above
    y_list = [-1.1, -1.0, -0.5, 0, 0.5, 0.99, 1.0]

    myQ.set_qdict(q_dict)

    print("\nTesting float2frmt()\n====================")
    pprint.pprint(q_dict)
    for y in y_list:
        print("y = {0}\t->\ty_fix = {1}".format(y, myQ.float2frmt(y)))

    print("\nTesting frmt2float()\n====================")
    q_dict = {'WI': 3, 'WF': 3, 'ovfl': 'sat', 'quant': 'round', 'fx_base': 'dec', 'scale': 2}
    pprint.pprint(q_dict)
    myQ.set_qdict(q_dict)
    dec_list = [-9, -8, -7, -4.0, -3.578, 0, 0.5, 4, 7, 8]
    for dec in dec_list:
        print("y={0}\t->\ty_fix={1} ({2})".format(dec, myQ.frmt2float(dec), myQ.frmt))
