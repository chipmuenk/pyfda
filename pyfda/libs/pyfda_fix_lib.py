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
import copy

import pyfda.filterbroker as fb
import numpy as np
from numpy.lib.function_base import iterable
from pyfda.libs.pyfda_lib import is_numeric, pprint_log
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

__version__ = 0.6


def qstr(text):
    """ carefully replace qstr() function - only needed for Py2 compatibility """
    return str(text)


def bin2hex(bin_str: str, WI=0) -> str:
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


# ---------------------------------------------------------------------
def bin2oct(bin_str: str, WI=0) -> str:
    """
    Convert number `bin_str` in binary format to octal formatted string.
    `bin_str` is prepended / appended with zeros until the number of bits before
    and after the radix point (position given by `WI`) is a multiple of 3.
    """

    wmap = {
        '000': '0',
        '001': '1',
        '010': '2',
        '011': '3',
        '100': '4',
        '101': '5',
        '110': '6',
        '111': '7',
        }

    oct_str = ""

    # --- integer part ----------------------------
    if WI > 0:
        # slice string with integer bits and prepend with zeros to obtain a
        # multiple of 3 length:
        bin_i_str = bin_str[:WI+1]
        while (len(bin_i_str) % 3 != 0):
            bin_i_str = "0" + bin_i_str

        i = 0
        while (i < len(bin_i_str)):  # map chunks of 3 binary bits to one oct digit
            oct_str = oct_str + wmap[bin_i_str[i:i + 3]]
            i = i + 3
    else:
        oct_str = bin_str[0]  # copy MSB as sign bit

    # --- fractional part -------------------------
    WF = len(bin_str) - WI - 1
    # slice string with fractional bits and append with zeros to obtain a
    # multiple of 3 length:
    if WF > 0:
        oct_str = oct_str + '.'
        bin_f_str = bin_str[WI+1:]

        while (len(bin_f_str) % 3 != 0):
            bin_f_str = bin_f_str + "0"

        # map chunks of 3 binary bits to one octal digit
        i = 0
        while (i < len(bin_f_str)):
            oct_str = oct_str + wmap[bin_f_str[i:i + 3]]
            i = i + 3

    # oct_str = oct_str.lstrip("0") # remove leading zeros
    oct_str = "0" if len(oct_str) == 0 else oct_str
    return oct_str


bin2oct_vec = np.vectorize(bin2oct)  # safer than frompyfunction()


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
    in the form WI.WF where WI and WF are the wordlength of integer resp.
    fractional part; total wordlength is `W = WI + WF + 1` due to the sign bit.

    Examples
    --------

    Define a dictionary with the format options and pass it to the constructor:

    >>> q_dict = {'WI':1, 'WF':14, 'ovfl':'sat', 'quant':'round'}
    >>> myQ = Fixed(q_dict)  # instantiate fixpoint quantizer
    >>> WI = myQ.q_dict['WI']  # access quantizer parameters
    >>> myQ.set_qdict({'WF': 13, 'WI': 2})  # update quantizer parameters


    Parameters
    ----------
    q_dict : dict
        define quantization options with the following keys

    * **'WI'** : number of integer bits, default: 0

    * **'WF'** : number of fractional bits; default: 15

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

    * **N_over** : integer
        total number of overflows (should be considered as read-only
        except for when an external quantizer is used)

    Additionally, the following keys from global dict `fb.fil[0]` define the
    number base and quantization/overflow behaviour for fixpoint numbers:

    * **`'fx_sim'`** : Flag for fixpoint mode, default = False (floating point)

    * **`'fx_base'`** : Display format for fixpoint number base; default = 'dec'

      - 'dec'   : decimal (base = 10)
      - 'bin'   : binary (base = 2)
      - 'hex'   : hexadecimal (base = 16)
      - 'oct'   : octal (base = 8)
      - 'csd'   : canonically signed digit (base = "3")

    * **`'qfrmt'`** : Quantization / overflow behaviour, default = 'qfrac'

      - 'qint'   : fixpoint integer format
      - 'qfrac'  : fractional fixpoint format

    Attributes
    ----------
    q_dict : dict
        A reference to the quantization dictionary passed during construction
        (see above). This dictionary is updated here and can be accessed from
        outside.

    LSB : float
        value of LSB (smallest quantization step), `self.LSB = 2 ** -q_dict['WF']`

    MSB : float
        value of most significant bit (MSB),  `self.MSB = 2 ** (q_dict['WI'] - 1)`

    MIN : float
        most negative representable value, `self.MIN = -2 * self.MSB`

    MAX : float
        largest representable value, `self.MAX = 2 * self.MSB - self.LSB`

    N : integer
        total number of simulation data points

    N_over_neg : integer
        number of negative overflows (commented out)

    N_over_pos : integer
        number of positive overflows (commented out)

    ovr_flag: integer or integer array (same shape as input argument)
        overflow flag, meaning:

            0 : no overflow

            +1: positive overflow

            -1: negative overflow

        has occured during last fixpoint conversion.

    places : integer
        number of places required for printing in the selected 'fx_base' format.
        For binary formats, this is the same as the wordlength. Calculated
        from the numeric base 'fx_base' and the total word length WI + WF + 1.

    Overflow flags and counters are set in `self.fixp()` and reset in `self.reset_N()`

    Example
    -------
    class `Fixed()` can be used like the Matlab `quantizer()` object / function from
    the fixpoint toolbox, see (Matlab) 'help round' and 'help quantizer/round' e.g.

    **MATLAB**

    >>> q_dsp = quantizer('fixed', 'round', [16 15], 'wrap');
    >>> yq = quantize(q_dsp, y)

    **PYTHON**
    >>> q_dsp = {'WI':0, 'WF': 15, 'quant':'round', 'ovfl':'wrap'}
    >>> my_q = Fixed(q_dsp)
    >>> yq = my_q.fixp(y)
    """

    def __init__(self, q_dict):
        """
        Construct `Fixed` object with dict `q_dict`
        """
        # define valid keys and default values for quantization dict
        self.q_dict_default = {
            'WI': 0, 'WF': 15, 'w_a_m': 'm', 'quant': 'round', 'ovfl': 'sat',
        # these keys are calculated and should normally be regarded as read-only
            'N_over': 0}
        # these attributes are calculated and should be regarded as read-only
        self.LSB = 2. ** -self.q_dict_default['WF']
        self.MSB = 2. ** (self.q_dict_default['WI'] - 1)
        self.MAX = 2 * self.MSB - self.LSB
        self.MIN = -2 * self.MSB

        self.N = 0

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
                'dec': r'[^0-9Ee|.|,|\-]',
                'bin': r'[^0|1|.|,|\-]',
                'oct': r'[^0-7|.|,|\-]',
                'hex': r'[^0-9A-Fa-f|.|,|\-]',
                'csd': r'[^0|\+|\-|.|,]'
                        }
        # --------------------------------------------------------------------------
        # vectorize frmt2float function for arrays, swallow the `self` argument
        self.frmt2float_vec = np.vectorize(self.frmt2float_scalar, excluded='self')

    def verify_q_dict_keys(self, q_dict: dict) -> None:
        """
        Check against `self.q_dict_default` dictionary
        whether all keys in the passed `q_dict` dictionary are valid.

        Unknown keys throw an error message.
        """
        for k in q_dict.keys():
            if k not in self.q_dict_default:
                logger.error(u'Unknown Key "{0:s}"!'.format(k))

# ------------------------------------------------------------------------------
    def set_qdict(self, d: dict) -> None:
        """
        Update the instance quantization dict `self.q_dict` from passed dict `d`:

        * Sanitize `WI` and `WF`
        * Calculate attributes `MSB`, `LSB`, `MIN` and `MAX`
        * Calculate number of places needed for printing from `qfrmt`,`fx_base` and `W`
          and store it as attribute `self.places`

        Check the docstring of class `Fixed()` for details on quantization
        """
        self.verify_q_dict_keys(d)  # check whether all keys are valid
        self.q_dict.update(d)  # merge d into self.q_dict

        # sanitize WI and WF
        self.q_dict['WI'] = int(self.q_dict['WI'])
        self.q_dict['WF'] = abs(int(self.q_dict['WF']))

        # Calculate min., max., LSB and MSB from word lengths
        if fb.fil[0]['qfrmt'] == 'qint':
            # LSB = 1, MSB = 2 ** (W - 1)
            self.LSB = 1
            self.MSB = 2 ** (self.q_dict['WI'] + self.q_dict['WF']- 1)
        else:
            self.LSB = 2. ** -self.q_dict['WF']
            self.MSB = 2. ** (self.q_dict['WI'] - 1)

        self.MAX =  2. * self.MSB - self.LSB
        self.MIN = -2. * self.MSB

        # Calculate required number of places for different bases from total
        # number of bits:
        W = self.q_dict['WI'] + self.q_dict['WF'] + 1
        #
        if not fb.fil[0]['fx_sim']:  # float format
            self.places = 4
        elif fb.fil[0]['fx_base'] == 'dec':
            self.places = int(
                np.ceil(np.log10(W) * np.log10(2.))) + 1
        elif fb.fil[0]['fx_base'] == 'bin':
            self.places = W + 1
        elif fb.fil[0]['fx_base'] == 'csd':
            self.places = int(np.ceil(W / 1.5)) + 1
        elif fb.fil[0]['fx_base'] == 'hex':
            self.places = int(np.ceil(W / 4.)) + 1
        elif fb.fil[0]['fx_base'] == 'oct':
            self.places = int(np.ceil(W / 3.)) + 1
        else:
            raise Exception(
                u'Unknown number format "{0:s}"!'.format(fb.fil[0]['fx_base']))

# ------------------------------------------------------------------------------
    def fixp(self, y, in_frmt: str = 'qfrac', out_frmt: str = 'qfrac'):
        """
        Return a quantized copy `yq` for `y` (scalar or array-like) with the same
        shape as `y`. The returned data is always in float format, use float2frmt()
        to obtain different number formats.

        This is used a.o. by the following methods / classes:

        - `frmt2float()`: always returns a float with RWV
        - `float2frmt()`: starts with RWV, passes on the scaling argument
        - input_coeffs: uses both methods above when quantizing coefficients

        Saturation / two's complement wrapping happens outside the range +/- MSB,
        requantization (round, floor, fix, ...) is applied on the ratio `y / LSB`.

        **Fractional number format WI.WF** (`fb.fil[0]['qfrmt'] = 'qfrac'`):
        `LSB =  2 ** -WF`

        - Multiply float input by `1 / self.LSB = 2**WF`, obtaining integer scale
        - Quantize
        - Scale back by multiplying with `self.LSB` to restore fractional point
        - Find pos. and neg. overflows and replace them by wrapped or saturated
          values

        **Integer number format W = 1 + WI + WF** (`fb.fil[0]['qfrmt'] = 'qint'`):
        `LSB = 1`

        - Multiply float input by `2 ** WF` to obtain integer scale
        - Quantize and treat overflows in integer scale

        Parameters
        ----------
        y: scalar or array-like object of float
            input value (floating point format) to be quantized

        in_frmt: str
            Determine the scaling *before* quantizing / saturation
            *'qfrac'* (default): fractional float input,
            `y` is multiplied by `2 ** WF` *before* quantizing / saturating.

            For all other settings, `y` is transformed unscaled.

        out_frmt: str
            Determine the scaling *after* quantizing / saturation
            **'qfrac'** (default): fractional fixpoint output format,
            `y` is divided by `2 ** WF` *after* quantizing / saturating.

            For all other settings, `y` is transformed unscaled.

        Returns
        -------
        yq: float scalar or ndarray
            with the same shape as `y`, in the range
            `-2 * self.MSB` ... `2 * self.MSB - self.LSB`

        Examples
        --------

        >>> q_obj_a = {'WI':1, 'WF':6, 'ovfl':'sat', 'quant':'round'}
        >>> myQa = Fixed(q_obj_a) # instantiate fixed-point object myQa
        >>> myQa.resetN()  # reset overflow counter
        >>> a = np.arange(0,5, 0.05) # create input signal

        >>> aq = myQa.fixp(a) # quantize input signal
        >>> plt.plot(a, aq) # plot quantized vs. original signal
        >>> print(myQa.q_dict('N_over'), "overflows!") # print number of overflows

        >>> # Convert output to same format as input:
        >>> b = np.arange(200, dtype = np.int16)
        >>> btype = np.result_type(b)
        >>> # MSB = 2**7, LSB = 2**(-2):
        >>> q_obj_b = {'WI':7, 'WF':2, 'ovfl':'wrap', 'quant':'round'}
        >>> myQb = Fixed(q_obj_b) # instantiate fixed-point object myQb
        >>> bq = myQb.fixp(b)
        >>> bq = bq.astype(btype) # restore original variable type
        """

        # ======================================================================
        # (1) : INITIALIZATION
        #       Convert input argument into proper floating point scalars /
        #       arrays and initialize flags
        # ======================================================================
        if not fb.fil[0]['fx_sim']:
            logger.warning(
                "fixp() should only be called for fixpoint number format - returning floats!")
            return y

        if not in_frmt in {'qfrac', 'qint'}:
            logger.error(f"Unknown input format {in_frmt}")
        if not out_frmt in {'qfrac', 'qint'}:
            logger.error(f"Unknown output format {out_frmt}")

        # logger.error(f"fixp in: y = {pprint_log(y, N=4)}")

        if np.shape(y):
            # Input is an array:
            #   Create empty arrays for result and overflows with same shape as y
            #   for speedup, test for invalid types
            SCALAR = False
            y = np.asarray(y)  # convert lists / tuples / ... to numpy arrays
            yq = np.zeros(y.shape)
            over_pos = over_neg = np.zeros(y.shape, dtype=bool)
            self.ovr_flag = np.zeros(y.shape, dtype=int)

            if np.issubdtype(y.dtype, np.number):
                # numpy number type (usual case), proceed with test for complex value
                self.N += y.size
            elif y.dtype.kind in {'U', 'S'}:  # string or unicode
                try:
                    y = y.astype(np.float64)  # try to convert to float
                    self.N += y.size
                except (TypeError, ValueError):
                    try:
                        np.char.replace(y, ' ', '')  # remove all whitespace
                        y = y.astype(complex)  # try to convert to complex
                        self.N += y.size * 2
                    # try converting elements recursively:
                    except (TypeError, ValueError) as e:
                        yq = np.asarray(
                            list(map(lambda y_scalar:\
                                     self.fixp(y_scalar, in_frmt=in_frmt, out_frmt=out_frmt),
                                     y)))
                        self.N += y.size
                        return yq
            else:
                logger.error(f"Argument '{y}' is of type '{y.dtype}',\n"
                             "cannot convert to float or complex.")
                y = np.zeros(y.shape)
        else:
            # Input is a scalar
            SCALAR = True
            # get rid of errors that have occurred upstream
            if y is None or str(y) == "":
                y = 0
            # If y is not a number, remove whitespace and try to convert to
            # float and or to complex format:
            elif not np.issubdtype(type(y), np.number):
                # logger.error(f"Quantize string {y}")
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
            self.N += 1

        # convert pseudo-complex (imag = 0) to real
        y = np.real_if_close(y)
        # quantize complex values separately and recursively
        if np.iscomplexobj(y):
            yq = self.fixp(y.real, in_frmt=in_frmt, out_frmt=out_frmt) +\
                 self.fixp(y.imag, in_frmt=in_frmt, out_frmt=out_frmt) * 1j
            return yq

        # ======================================================================
        # logger.error(f"fixp: in_frmt = '{in_frmt}', out_frmt = '{out_frmt}'")

        # ======================================================================
        # (2) : QUANTIZATION
        #       For `in_frmt=='qfrac'`, multiply by 2**WF = 1/LSB to obtain an
        #       intermediate format with quantization step size of 1.
        #       Next, apply selected quantization method to convert
        #       floating point inputs to "fixpoint integers".
        # ======================================================================
        if in_frmt == 'qfrac':
            y = y * (2. ** self.q_dict['WF'])

        # logger.error(f"fixp (in:scaled): {pprint_log(y, N=4)}")

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
                yq = (simulateDSM(y*self.LSB, H)[0]+1)/(2*self.LSB)
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

        # ========================================================================
        # (3) : OVERFLOW / SATURATION
        #       Handle Overflow / saturation w.r.t. to the MSB = 2 ** (W - 2),
        #       returning a result in the range MIN = -2*MSB ... + 2*MSB-LSB = MAX
        # ========================================================================
        LSB = 1
        MSB = 1 << (self.q_dict['WI'] + self.q_dict['WF'] - 1)  # 2 ** (W - 2)
        MAX = 2 * MSB - LSB  # 2 ** (W - 1) - 1
        MIN = - 2 * MSB

        if self.q_dict['ovfl'] == 'none':
            # set all overflow flags to zero
            self.N_over = 0  # self.N_over_neg = self.N_over_pos =
        else:
            # Bool. vectors with '1' for every neg./pos overflow:
            over_neg = (yq < MIN)
            over_pos = (yq > MAX)
            # create flag / array of flags for pos. / neg. overflows
            self.ovr_flag = over_pos.astype(int) - over_neg.astype(int)
            # No. of pos. / neg. / all overflows occured since last reset:
            # self.N_over_neg += np.sum(over_neg)
            # self.N_over_pos += np.sum(over_pos)
            self.N_over += np.sum(over_neg) + np.sum(over_pos)

            # Replace overflows with Min/Max-Values (saturation):
            if self.q_dict['ovfl'] == 'sat':
                yq = np.where(over_pos, MAX, yq)  # (cond, true, false)
                yq = np.where(over_neg, MIN, yq)
            # Replace overflows by two's complement wraparound (wrap)
            elif self.q_dict['ovfl'] == 'wrap':
                yq = np.where(
                    over_pos | over_neg, yq - 4. * MSB * np.fix(
                        (np.sign(yq) * 2 * MSB + yq) / (4 * MSB)), yq)
            else:
                raise Exception(
                    f"""Unknown overflow type "{self.q_dict['ovfl']:s}"!""")

        self.q_dict.update({'N_over': self.N_over})

        # ======================================================================
        # (4) : OUTPUT SCALING
        #       Divide result by `2 ** WF` factor for `out_frmt=='qint'` to obtain
        #       quantized fractional number
        # ======================================================================
        if out_frmt == 'qfrac':
            yq = yq / (2. ** self.q_dict['WF'])

        # logger.error(f"fixp: (out:scaled) = {pprint_log(yq, N=4)}")

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
        self.q_dict.update({'N_over': 0})

        self.ovr_flag = 0
        # self.N_over_pos = 0
        # self.N_over_neg = 0
        self.N_over = 0
        self.N = 0

    # --------------------------------------------------------------------------
    def requant(self, x_i, QI):
        """
        Change word length of input signal `x_i` with fractional and integer widths
        defined by 'QI' to the word format defined by `self.q_dict` using the
        quantization and saturation methods specified by `self.q_dict['quant']` and
        `self.q_dict['ovfl']`.

        **Input and output word are aligned at their binary points.**

        Parameters
        ----------
        self: Fixed() object
            `self.qdict()` is the quantizer dict that specifies the output word format
            and the requantizing / saturation methods to be used.

        x_i: int, float or complex scalar or array-like
            signal to be requantized with quantization format defined in quantizer QI

        QI: quantizer
            Quantizer for input word, only the keys 'WI' and 'WF' for integer
            and fractional wordlength are evaluated.
            `QI.q_dict['WI'] = 2` and `QI.q_dict['WF'] = 13` e.g. define Q-Format '2.13'
            with 2 integer, 13 fractional bits and 1 implied sign bit = 16 bits total.

        Returns
        -------

        y: any
            requantized output data with same shape as input data, quantized as specified
            in `self.qdict`.

        Example
        --------

        The following shows an example of rescaling an input word from Q2.4 to Q0.3
        using wrap-around and truncation. It's easy to see that for simple wrap-around
        logic, the sign of the result may change.

        ::

            S | WI1 | WI0 * WF0 | WF1 | WF2 | WF3  :  WI = 2, WF = 4, W = 7
            0 |  1  |  0  *  1  |  0  |  1  |  1   =  43 (dec) or 43/16 = 2 + 11/16 (float)
                        *
                    |  S  * WF0 | WF1 | WF2        :  WI = 0, WF = 3, W = 4
                    0  *  1  |  0  |  1         =  7 (dec) or 7/8 (float)


        When the input is integer format, the fractional value is calculated as an
        intermediate representation by multiplying the integer value by 2 ** (-WF).
        Integer and fractional part are truncated / extended to the output
        quantization specifications.

        Changes in the number of integer bits `dWI` and fractional bits `dWF` are
        handled separately.

        When operating on bit level in hardware, the following operations are used:

        **Fractional Bits**

        - For reducing the number of fractional bits by `dWF`, simply right-shift the
          integer number by `dWF`. For rounding, add '1' to the bit below the truncation
          point before right-shifting.

        - Extend the number of fractional bits by left-shifting the integer by `dWF`,
          LSB's are filled with zeros.

        **Integer Bits**

        - For reducing the number of integer bits by `dWI`, simply right-shift the
          integer by `dWI`.

        - The number of fractional bits is SIGN-EXTENDED by filling up the left-most
          bits with the sign bit.
        """

        WI_F = QI.q_dict['WF']  # number of fractional bits of input signal

        # Convert input signal to fractional format if needed for aligning at fractional point
        if fb.fil[0]['qfrmt'] == 'qint':
            x_i_frac = x_i / (1 << WI_F)
        else:
            x_i_frac = x_i

        # Quantize and saturate / overflow based on fractional output format and return
        # either fractional or integer format, depending on `fb.fil[0]['qfrmt']`.
        return self.fixp(x_i_frac, out_frmt=fb.fil[0]['qfrmt'])

    # --------------------------------------------------------------------------
    def frmt2float(self, y):
        """
        Return floating point representation for fixpoint `y` (scalar or array)
        given in format `fb.fil[0]['fx_base']`.

        When input format is float, return unchanged.

        Else:

        - Remove illegal characters and leading '0's
        - Count number of fractional places `frc_places` and remove radix point
        - Calculate decimal, fractional representation `y_dec` of string,
          using the base and the number of fractional places
        - Calculate two's complement for `W` bits (only for negative bin and hex numbers)
        - Calculate fixpoint float representation `y_float = fixp(y_dec, out_frmt='qfrmt')`,
          dividing the result by `2**WF`.

        Parameters
        ----------
        y: scalar or string or array of scalars or strings in number format float or
            `fb.fil[0]['fx_base']` ('dec', 'hex', 'oct', 'bin' or 'csd')

        Returns
        -------
        Quantized floating point (`dtype=np.float64`) representation of input string
        of same shape as `y`.
        """

        if y is None:
            return 0
        elif np.isscalar(y):
            if not y:
                return 0
            else:
                if np.all((y == "")):
                    return np.zeros_like(y)
        if isinstance(y, np.str_):
            # Convert 'np.str_' to "regular" string
            y = str(y)

        y_float = None

        if not fb.fil[0]['fx_sim']:
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
        # Convert various fixpoint formats to float
        elif np.isscalar(y):
            return self.frmt2float_scalar(y)
        else:
            return self.frmt2float_vec(y)

    # --------------------------------------------------------------------------
    def frmt2float_scalar(self, y: str) -> float:
        """
        Convert a string in 'dec', 'bin', 'oct', 'hex', 'csd' numeric format
        to float.

        - format is taken from the global `fb.fil[0]['fx_base']`
        - maximum wordlength is determined from the local quantization dict keys
          `self.q_dict['WI']` and `self.q_dict['WF']`
        - negative numbers can be represented by a '-' sign or in two's complement
        - represented numbers may be fractional and / or complex.
        - the result is divided by 2**WF for `fb.fil[0]['qfrmt'] == 'qint'` in `fixp()`

        Parameters
        ----------
        y: str
            A string formatted as a decimal, binary, octal, hex or csd
            number representation. The number string may contain a '.'
            or ',' to represent fractal numbers. When the string contains a 'j'm
            it is tried to split the string into real and imaginary part.

        Returns
        --------
        float or complex
            The float / complex representation of the string

        """
        # -----------------------------------------------------
        def split_complex_str(y: str) -> tuple:
            """
            Parameters
            ----------
            y: str
                A string containing a 'j', indicating a complex number
                representation. Format can be decimal, binary or hex.
                csd is not supported.

            Returns
            --------
            tuple of str: (y_re, y_im)

            Split string `y` into two parts at the + or - sign, separating
            real and imaginary part. The sign at the beginning of the string
            is ignored. Real and imaginary part are returned as a tuple.
            """
            # only keep allowed characters incl. 'j' and '+',
            # remove leading zero(s) and convert to lower case
            y = re.sub(self.FRMT_REGEX[frmt].replace(']', '|j\+]'),
                       r'', str(y)).lstrip('0').lower()

            # (?!^) : any position other than start of string
            # (...) split without deleting the delimiter
            # (?= ...) Matches if ... matches next, but doesn’t consume any
            #          of the string (lookahead assertion).
            # [+-][\d]: +/-[0 ... 9 or A ... F or .]
            y1 = re.split(r"(?!^)(?=[+-][\.\da-fA-F])", y)

            if len(y1) == 2:
                if not 'j' in y1[0] and 'j' in y1[1]:  # re + im
                    return y1[0], y1[1].replace('j','')
                elif 'j' in y1[0] and not 'j' in y1[1]:  # im + re
                    return y1[1], y1[0].replace('j','')
                else:  # both parts are imaginary, combine them
                    y_im = self.frmt2float(y1[0].replace('j',''))\
                        + self.frmt2float(y1[1].replace('j',''))
                    return "0", self.float2frmt(y_im)
            elif len(y1) == 1: # purely imaginary, return 0 for re part
                return "0", y1[0].replace('j', '')
            else:
                logger.error(
                    f"String split into {len(y1)} parts - that's too many!")
                return "0", "0"
        # -----------------------------------------
        y = str(y)
        frmt = fb.fil[0]['fx_base']
        # ======================================================================
        # (1) : COMPLEX NUMBERS
        #       Split strings containing 'j' into real and imaginary part,
        #       calling `frmt2float` recursively
        # ======================================================================
        if 'j' in y:
            y_re, y_im = split_complex_str(y)
            return self.frmt2float(y_re) + self.frmt2float(y_im) * 1j

        # ======================================================================
        # (2) : CLEAN UP INPUT STRING
        #       - remove illegal characters (depending on selected number format
        #         defined in FRMT_REGEX(frmt)) from input string
        #       - remove all leading '0' to sanitize cases like '0001' or '00.23'
        #       - replace ',' by '.' for German style numbers
        # ======================================================================
        val_str = re.sub(
            self.FRMT_REGEX[frmt], r'', y).lstrip('0').replace(',', '.')

        # ======================================================================
        # (3) : FRACTIONAL PLACES
        #       - prepend '0' if string starts with '.' and store as `val_str`
        #       - store number of fractional places in `frc_places` (all number
        #         formats)
        #       - store fractional part as `frc_str` and whole string without '.'
        #         as `raw_str`
        # ======================================================================
        if len(val_str) > 0:
            if val_str[0] == '.':
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

        # ======================================================================
        # (4a): CONVERSION (DEC)
        #       - calculate the decimal value of `val_str` directly using `fixp()`
        #         which quantizes and calculates overflows
        #       - divide by scale
        # ======================================================================
        if frmt == 'dec':
            # try to convert string -> float directly with decimal point position
            try:
                y_dec = y_float = self.fixp(val_str, in_frmt=fb.fil[0]['qfrmt'])
            except Exception as e:
                logger.warning(e)
                return 0.0

        # ======================================================================
        # (4b): CONVERSION (BIN, HEX, OCT)
        #       - Use `raw_string` without radix point for calculation
        #       - Check for a negative sign and remove it, use this information only
        #         in the end
        #       - Calculate decimal value of `raw_str` without '-' using
        #        `int(raw_str, base)`
        #       - divide by `base ** frc_places` for correct scaling
        #       - calculate number of bits required for binary representation. If this
        #         number exceeds word length, convert to binary string, strip
        #         leading bits and convert back to float.
        #       - transform numbers in negative 2's complement to negative floats.
        #       - calculate the fixpoint representation using `fixp()` for correct
        #            saturation / quantization
        # TODO: Shouldn't `fixp()` be enough for handling number of bits etc?
        # ======================================================================
        elif frmt in {'hex', 'bin', 'oct'}:
            neg_sign = False
            if fb.fil[0]['qfrmt'] == 'qint':
                W = self.q_dict['WI'] + self.q_dict['WF'] + 1
            else:
                W = self.q_dict['WI'] + 1
            try:
                if raw_str[0] == '-':
                    neg_sign = True
                    raw_str = raw_str.lstrip('-')

                if frmt == 'hex':
                    base = 16
                elif frmt == 'oct':
                    base = 8
                else:  # 'bin'
                    base = 2

                y_dec = int(raw_str, base) / base ** frc_places

                if y_dec == 0:  # avoid log2(0)
                    return 0
                int_bits = max(int(np.floor(np.log2(y_dec))) + 1, 0)

                # When number is outside fixpoint range, discard MSBs:
                if int_bits > W:
                    # convert non-binary numbers to binary string for
                    # discarding bits bit-wise
                    if frmt != 'bin':
                        raw_str = np.binary_repr(int(raw_str, base))
                    # discard the upper bits outside the valid range
                    raw_str = raw_str[int_bits - W:]

                    # recalculate y_dec for truncated string
                    y_dec = int(raw_str, 2) / base ** frc_places

                    if y_dec == 0:  # avoid log2(0) error in code below
                        return 0.0
                    int_bits = max(int(np.floor(np.log2(y_dec))) + 1, 0)

                # now, y_dec is in the correct range:
                if int_bits <= W - 1:  # positive number
                    pass
                else: # int_bits == W -> negative, calculate 2's complement
                    # int_bits > W has been treated above
                    y_dec = y_dec - (1 << int_bits)
                # quantize / saturate / wrap & scale the integer value:
                if neg_sign:
                    y_dec = -y_dec
                y_float = self.fixp(y_dec, out_frmt='qfrac')
            except Exception as e:
                logger.warning(e)
                return 0.0

        # ======================================================================
        # (4c): CONVERSION (CSD)
        #       - use `raw_string` without radix point for calculation
        #       - divide by 2 ** <number of fractional places> for correct scaling
        #       - calculate the fixpoint representation using `fixp()` for correct
        #            saturation / quantization
        # ======================================================================
        elif frmt == 'csd':
            y_dec = csd2dec_vec(raw_str)  # csd -> integer
            if y_dec is not None:
                y_float = self.fixp(y_dec / 2 ** frc_places, out_frmt='qfrac')
        # ----
        else:
            logger.error(f'Unknown output format "{frmt}"!')
            return 0.0

        if y_float is not None:
            return y_float
        else:
            return 0.0

    # --------------------------------------------------------------------------
    def float2frmt(self, y) -> str:
        """
        Convert an array or single value of float / complex / string to a quantized
        representation in one of the formats float / int / bin / hex / csd.

        Called a.o. by `itemDelegate.displayText()` for on-the-fly number
        conversion. Returns fixpoint representation for `y` (scalar or array-like)
        with numeric format `self.frmt` and a total wordlength of
        `W = self.q_dict['WI'] + self.q_dict['WF'] + 1` bits.
        The result has the same shape as `y`.

        The float is always quantized / saturated using `self.fixp()` before it is
        converted to different fixpoint number bases.

        Parameters
        ----------
        y: scalar or array-like
            y has to be an integer, float or complex decimal number

        Returns
        -------
        str, float or an ndarray of float or string
            The numeric format is set in `fb.fil[0]['fx_base'])`. It has the same shape as `y`.
            For all formats except `float` a fixpoint representation with
            a total number of W = WI + WF + 1 binary digits is returned.
        """

        insert_binary_point = np.vectorize(
            lambda bin_str, pos: (bin_str[:pos+1] + "." + bin_str[pos+1:]))
        """
            Define vectorized functions using numpys automatic type casting:
            Vectorized functions for inserting binary point in string `bin_str`
            after position `pos`.

            Usage:  insert_binary_point(bin_str, pos)

            Parameters
            ----------
            bin_str : str
                String in binary format (only '0' and '1')
            pos     : int
                Position of binary point to be inserted
        """

        binary_repr_vec = np.frompyfunc(np.binary_repr, 2, 1)

        def binary_repr(y_int, W):
            """
            Convert a scalar, array, list or tuple of integer values
            to the binary representation using `np.binary_repr()` or
            the vectorized form.
            """

            if type(y_int) in {np.ndarray, list, tuple}:
                return binary_repr_vec(y_int, W).astype('U')
            elif isinstance(y_int, (int, np.integer)):
                return np.binary_repr(y_int, W)
            else:
                logger.error(f"Unsupported data type '{type(y_int)}'!")
                return "0"

        # ======================================================================
        # logger.warning(f"float2frmt: y = {y}")
        if not is_numeric(y):
            logger.error(f"float2frmt() received a non-numeric argument '{y}'!")
            return 0.0
        if not fb.fil[0]['fx_sim']:  # return float input value unchanged (no string)
            return y

        if np.iscomplexobj(y):  # convert complex arguments recursively
            y_re = self.float2frmt(y.real)
            y_im = self.float2frmt(y.imag)
            if fb.fil[0]['fx_base'] == 'csd':
                logger.error(
                    "Complex CSD coefficients are not supported yet, casting  to real. "
                    "\n\tPlease create an issue if you need this feature.")
                # CSD coefficients differ in length and require an array with dtype 'object'
                # which does not support arithmetic or string operations.
                return y_re
            elif is_numeric(y_re) and is_numeric(y_im):  # return in numeric format
                return y_re + y_im * 1j
            elif not (is_numeric(y_re) or is_numeric(y_im)):  # return string (array)
                # logger.error(
                #     f"real part:\n{y_re}\n{type(y_re)} ({y_re.dtype})\n"
                #     f"imag. part\n{y_im}\n{type(y_im)} ({y_im.dtype}).")
                y_str = np.char.add(np.char.add(y_re, '+'), np.char.add(y_im,'j'))
                # logger.warning(f"ystr={y_str}")
                return y_str
            else:
                logger.error(f"Cannot combine real part ({y_re.dtype}) and imag. part ({y_im.dtype}).")
                return "0"

        # return a quantized & saturated / wrapped fixpoint (type float) for y (int or frac format)
        y_fix = self.fixp(y, out_frmt=fb.fil[0]['qfrmt'])

        if fb.fil[0]['fx_base'] == 'dec':
            if self.q_dict['WF'] == 0 or fb.fil[0]['qfrmt'] == 'qint':
                # TODO: need to convert to str?
                y_str = np.int64(y_fix)  # get rid of trailing zero
                # y_str = np.char.mod('%d', y_fix)
                # elementwise conversion from integer (%d) to string
                # see https://docs.scipy.org/doc/numpy/reference/routines.char.html
            else:
                # y_str = np.char.mod('%f',y_fix)
                y_str = y_fix
        elif fb.fil[0]['fx_base'] == 'csd':
            if fb.fil[0]['qfrmt'] == 'qint':
                # integer case, convert with 0 fractional bits
                y_str = dec2csd_vec(y_fix, 0)
            else:
                # fractional case, convert with WF fractional bits
                y_str = dec2csd_vec(y_fix, self.q_dict['WF'])

        elif fb.fil[0]['fx_base'] in {'bin', 'oct', 'hex'}:
            # represent fixpoint number as integer in the range -2**(W-1) ... 2**(W-1)
            y_fix_int = np.int64(np.round(y_fix / self.LSB))
            W = self.q_dict['WI'] + self.q_dict['WF'] + 1
            # convert to (array of) string with 2's complement binary
            y_bin_str = binary_repr(y_fix_int, W)

            if fb.fil[0]['qfrmt'] == 'qint':
                WI = self.q_dict['WI'] + self.q_dict['WF'] + 1
                # TODO: Is the "+ 1" correct?
            else:
                WI = self.q_dict['WI']
            if fb.fil[0]['fx_base'] == 'hex':
                y_str = bin2hex_vec(y_bin_str, WI)
            elif fb.fil[0]['fx_base'] == 'oct':
                y_str = bin2oct_vec(y_bin_str, WI)
            else:  # 'bin'
                # insert radix point if required
                if fb.fil[0]['qfrmt'] == 'qint':
                    y_str = y_bin_str
                else:
                    y_str = insert_binary_point(y_bin_str, WI)
        else:
            raise Exception(f"""Unknown number format "{fb.fil[0]['fx_base']}"!""")

        if isinstance(y_str, np.ndarray) and np.ndim(y_str) < 1:
            y_str = y_str.item()  # convert singleton array to scalar

        # logger.warning(f"float2frmt: y_str = {y_str}")
        return y_str

########################################

# --------------------------------------------------------------------------
def quant_coeffs(coeffs: iterable, Q, recursive: bool = False, out_frmt: str = ""
                 ) -> np.ndarray:
    """
    Quantize the coefficients, scale and convert them to a list of integers,
    using the quantization settings of `Fixed()` instance `Q` and global setting
    `fb.fil[0]['qfrmt']` (`'qfrac'` or `'qint'`) and `fb.fil[0]['fx_sim']` (`True`
    or `False`)

    Parameters
    ----------
    coeffs: iterable
        An iterable of coefficients to be quantized

    Q: object
        Instance of Fixed object containing quantization dict `q_dict`

    recursive: bool
        When `False` (default), process all coefficients. When `True`,
        The first coefficient is ignored (must be 1)

    out_frmt: str
        Output quantization format ("qint" or "qfrac"). When nothing is specified,
        use the global setting from `fb.fil[0]['qfrmt']`.

    Returns
    -------
    A numpy array of integer coeffcients, quantized and scaled with the
    settings of the quantization object dict.

    """
    disp_frmt_tmp = fb.fil[0]['fx_base']  # temporarily store fx display format and
    # always use decimal display format for coefficient quantization
    fb.fil[0]['fx_base'] = 'dec'
    if out_frmt == "":
        out_frmt=fb.fil[0]['qfrmt']
    elif out_frmt not in {"qint", "qfrac"}:
        logger.error(f"Unknown quantization format '{out_frmt}', using default.")
        out_frmt=fb.fil[0]['qfrmt']

    Q.resetN()  # reset all overflow counters

    if coeffs is None:
        logger.error("Coeffs empty!")
        return None

    # quantize floating point coefficients with the selected scale (WI.WF),
    # next, convert array float  -> array of fixp
    #                            -> list of int (scaled by 2^WF) when `'qfrmt':'qint'`
    if recursive:
        # recursive coefficients: quantize coefficients except for first (= 1)
        coeff_q = np.concatenate(([1], Q.fixp(coeffs[1:], out_frmt=out_frmt)))
    else:
        # quantize all coefficients
        coeff_q = Q.fixp(coeffs, out_frmt=out_frmt)

    # self.update_ovfl_cnt()  # update display of overflow counter and MSB / LSB

    fb.fil[0]['fx_base'] = disp_frmt_tmp  # restore previous display setting
    return coeff_q


########################################
if __name__ == '__main__':
    """
    Run a simple test with python -m pyfda.libs.pyfda_fix_lib
    or a more elaborate one with
    python -m pyfda.tests.test_pyfda_fix_lib
    """
    import pprint

    q_dict = {'WI': 0, 'WF': 3, 'ovfl': 'sat', 'quant': 'round'}
    myQ = Fixed(q_dict)  # instantiate fixpoint object with settings above
    y_list = [-1.1, -1.0, -0.5, 0, 0.5, 0.99, 1.0]

    myQ.set_qdict(q_dict)

    print("\nTesting float2frmt()\n====================")
    pprint.pprint(q_dict)
    for y in y_list:
        print("y = {0}\t->\ty_fix = {1}".format(y, myQ.float2frmt(y)))

    print("\nTesting frmt2float()\n====================")
    q_dict = {'WI': 3, 'WF': 3, 'ovfl': 'sat', 'quant': 'round'}
    pprint.pprint(q_dict)
    myQ.set_qdict(q_dict)
    dec_list = [-9, -8, -7, -4.0, -3.578, 0, 0.5, 4, 7, 8]
    for dec in dec_list:
        print("y={0}\t->\ty_fix={1} ({2})".format(dec, myQ.frmt2float(dec), myQ.frmt))
