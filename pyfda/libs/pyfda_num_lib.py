# -*- coding: utf-8 -*-
#
# This file is part of the pyfda project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyfda Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Library with various general functions and variables needed by the pyfda routines
"""
import logging
import re
import traceback

import numpy as np
import numexpr

from pyfda.config_file_parser import ConfigFileParser as CFP

logger = logging.getLogger(__name__)

###############################################################################
# Numeric functions ###########################################################
###############################################################################

def clean_ascii(arg):
    """
    Remove non-ASCII-characters (outside range 0 ... x7F) from `arg` when it
    is a `str`. Otherwise, return `arg` unchanged.

    Parameters
    ----------
    arg: str
        This is a unicode string under Python 3

    Returns
    -------
    arg: str
         Input string, cleaned from non-ASCII characters when `arg` is a string

         or

         Unchanged parameter `arg` when not a string

    """
    if isinstance(arg, str):
        return re.sub(r'[^\x00-\x7f]', r'', arg)

    return arg

# -----------------------------------------------------------------------------
def is_numeric(a) -> bool:
    """
    Return True when a or a.dtype is of a numeric type (complex, float, int, ...)

    Parameters
    ----------
    a : array-like, list, tuple or scalar

    Returns
    -------
    is_num : bool
        True when dtype of a is a numeric subtype
    """
    if isinstance(a, np.ndarray):
        is_num = np.issubdtype(a.dtype, np.number)
    elif type(a) in {list, tuple} and len(a) > 0:
        is_num = np.issubdtype(type(a[0]), np.number)
    else:
        is_num = np.issubdtype(type(a), np.number)
    return is_num

# -----------------------------------------------------------------------------
def np_type(a):
    """
    Return the python type of `a`, either of the parameter itself or (if it's a
    numpy array) of its items.

    Parameters
    ----------
    a : Python or numpy data type
        DESCRIPTION.

    Returns
    -------
    a_type : class
        Type of the Python variable resp. of the items of the numpy array

    """
    if isinstance(a, np.ndarray):
        a_type = type(a.item())
    else:
        a_type = type(a)

    return a_type


# -----------------------------------------------------------------------------
def np_shape(data):
    """
    Return the shape of `data` as tuple (rows, columns) for up to
    2-dimensional data. Otherwise, return `(None, None)`
    """
    d = np.ndim(data)
    if d == 0:
        return (0, 0)

    if d == 1:
        return(len(data), 1)

    if  d == 2:
        return np.shape(data)

    logger.warning("Unsuitable data shape with %s dimensions.", d)
    return (None, None)


# -----------------------------------------------------------------------------
def iter2ndarray(iterable: np.ndarray | list | tuple, dtype=complex) -> np.ndarray | None:
    """
    Convert an iterable (tuple, list, dict) to a numpy ndarray, egalizing
    different lengths of sub-iterables by adding zeros. This prevents
    problems with inhomogeneous arrays.

    Return ndarray or None
    """
    if isinstance(iterable, np.ndarray):
        # no need to convert argument
        return iterable

    if isinstance(iterable, (tuple, list)):
        arrs = []  # empty list for sub-arrays
        max_l = 0  # maximum length of sub-arrays
        for i in range(len(iterable)):
            if np.isscalar(iterable[i]):
                arrs.append(np.array([iterable[i]]))
            else:
                arrs.append(np.array(iterable[i]))
            max_l = max(max_l, len(arrs[i]))

        # equalize lengths of sub-arrays by filling up with zeros and convert to arrays
        for i in range(len(iterable)):
            arrs[i] = np.asarray(np.append(arrs[i], np.zeros(max_l - len(arrs[i]))))

        # convert list of arrays to two-dimensional array
        return np.nan_to_num(np.array(arrs, dtype=dtype))

    logger.error("Unsupported type '{type(iterable)}' of %s for conversion to ndarray.", iterable)
    return None


# ------------------------------------------------------------------------------
def frmt2cmplx(string: str, default: float = 0.) -> complex:
    """
    Convert string to real or complex, cartesian or polar coordinates are processed
    with various angle formats:
    - 0.3<p/2 or 0.3<pi/2 or 0.3<π/2
    """
    def str2angle_rad(string: str) -> float:
        """
        Try to convert `string` to a corresponding angle in rad
            Use the following regular expressions:
            - 'P$' : matches P at the end of the string
            - '^P' : matches P at beginning of string
            - '|' : combine multiple matches with OR
        """
        scale = 1
        if string[0] == "-":
            scale = -1
            string = string[1:]
        else:
            scale = 1
        if re.search('°$|o$', string):
            # "°" or "o" at end of string -> angle in degrees
            scale *= np.pi / 180.
            string = re.sub('o$|°$', '', string)
        elif re.search('^π|^pi|^p', string):
            # replace pi at the start of string by 1 and set scale = pi
            scale *= np.pi
            string = re.sub('^π|^pi|^p', '1', string)
        elif re.search('π$|pi$|p$', string):
            # remove pi at the end of string and set scale = pi
            scale *= np.pi
            string = re.sub('π$|pi$|p$', '', string)
        elif re.search('π|pi|p', string):
            # replace pi everywhere by "*1" and set scale = pi
            scale *= np.pi
            string = re.sub('π|pi|p', '*1', string)
        else:
            # angle in rad, also works when angle is a pure number
            string = re.sub('rad$|r$', '', string)

        return safe_eval(string) * scale
    # -------------------------------------------

    string = str(string).replace(" ", "")  # remove all blanks
    # convert angle character to "<" and split string at "<"
    # When the "<" character is not found, this returns a list with 1 item
    polar_str = string.replace("\u2220", '<').replace('*', '').split('<', 1)
    if len(polar_str) == 1: # no angle found; real / imag / cartesian complex
        return safe_eval(string, default, return_type='auto')

    if len(polar_str) == 2 and polar_str[0] == "": # pure angle, r = 1
        phi = str2angle_rad(polar_str[1])
        x = np.cos(phi)
        y = np.sin(phi)
    else:  # r and angle found
        r = safe_eval(polar_str[0], sign='pos')
        phi = str2angle_rad(polar_str[1])
        x = r * np.cos(phi)
        y = r * np.sin(phi)

    if safe_eval.err > 0:
        x = default.real
        y = default.imag
        logger.warning("Expression '%s' could not be evaluated.", string)
    return x + 1j * y


# ------------------------------------------------------------------------------
def safe_numexpr_eval(expr: str, fallback=None,
                      local_dict: dict | None = None) -> np.ndarray:
    """
    Evaluate `numexpr.evaluate(expr)` and catch various errors. The input is either
    a string representing a numeric value or a formula.

    When an error occurs, error code and message are stored in the function attribute
    `safe_numexpr_eval.err` and `safe_numexpr_eval.err_msg`

    Parameters
    ----------
    expr : str
        String to be evaluated and converted to a numpy array

    fallback : array-like or tuple or None
        numpy array or scalar as a fallback when errors occur during evaluation,
        this also defines the expected shape of the returned numpy expression

        When fallback is a tuple (e.g. '(11,)'), provide an array of zeros with
        the passed shape. Currently, this is only used by the formula stimulus
        in y[n]

    local_dict : dict or None
        optional dict with variables passed to `numexpr.evaluate`

    Returns
    -------
    np_expr : array-like
        `expr` converted to a numpy array or scalar

    """
    # define local variables for numexpr
    if local_dict is None:
        local_dict = {'j': 1j, 'None': 0}
    else:
        local_dict.update({'j': 1j, 'None': 0})
    # function attributes, providing some sort of "memory" for previous errors
    safe_numexpr_eval.err = 0  # error code
    safe_numexpr_eval.err_msg = ""  # detailed error message

    # Replace ',' -> '.' for German-style numbers
    expr = expr.replace(',', '.')
    if expr[0] == '.':  # prepend '0' when the number starts with '.'
        expr = "0" + expr

    # replace non-string or empty inputs by "0.0"
    if expr in {"", None}:
        safe_numexpr_eval.err_msg = "numexpr: Replacing empty input with '0.0'."
        safe_numexpr_eval.err = 9
        logger.warning(safe_numexpr_eval.err_msg)
        expr = "0.0"
    elif not isinstance(expr, str):
        safe_numexpr_eval.err_msg =(
            f"numexpr: Replacing non-string input '{expr}' "
            f"of type '{type(expr).__name__}' with '0.0'.")
        safe_numexpr_eval.err = 10
        logger.warning(safe_numexpr_eval.err_msg)
        expr = "0.0"

    if isinstance(fallback, tuple):
        # output is expected to be a numpy array -> input is a formula
        np_expr = np.zeros(fallback)  # fallback defines the shape
        fallback_shape = fallback
    else:
        # output is expected to be a scalar, manual entry of numeric values
        # needs to be checked and cleaned more closely
        np_expr = fallback  # fallback is the default numpy return value or None
        fallback_shape = np.shape(fallback)

        # expressions like 1e3j are rejected by numexpr, replace them by 1e3*1j
        # numbers like 1e3*1j are converted to 1e3*1*1j which is reduced by numexpr
        if "e" in expr and "j" in expr:
            expr = expr.replace("j", "*1j")

        # check for polar complex expressions containing "<" or "∠"
        # like 0.3<p/2 or 0.3∠pi/2 or 0.3<π/2 and convert them to cartesian form
        if "<" in expr or "\u2220" in expr:
            return frmt2cmplx(expr)

        # Find one or more redundant zeros '0+' at the beginning '^' of a number '[0-9]'
        # Group the number(s) '(...)' and write it as '\1' to the resulting string.
        expr = re.sub(r'^0+([0-9])', r'\1', expr)

    try:
        np_expr = numexpr.evaluate(expr.strip(), local_dict=local_dict)

    except SyntaxError as e:
        safe_numexpr_eval.err_msg = f"numexpr: Syntax error in '{expr}':\n\t{e}"
        logger.warning(safe_numexpr_eval.err_msg)
        safe_numexpr_eval.err = 1
        debug_exception()
    except AttributeError as e:
        safe_numexpr_eval.err_msg = f"numexpr: Attribute error in '{expr}':\n\t{e}"
        logger.warning(safe_numexpr_eval.err_msg)
        safe_numexpr_eval.err = 2
        debug_exception()
    except KeyError as e:
        safe_numexpr_eval.err_msg = f"numexpr: Unknown variable in '{expr}':\n\t{e}"
        logger.warning(safe_numexpr_eval.err_msg)
        safe_numexpr_eval.err = 3
        debug_exception()
    except TypeError as e:
        safe_numexpr_eval.err_msg = f"numexpr: Type error in '{expr}':\n\t{e}"
        logger.warning(safe_numexpr_eval.err_msg)
        safe_numexpr_eval.err = 4
        debug_exception()
    except ValueError as e:
        safe_numexpr_eval.err_msg = f"numexpr: Value error in '{expr}':\n\t{e}"
        logger.warning(safe_numexpr_eval.err_msg)
        safe_numexpr_eval.err = 5
        debug_exception()
    except ZeroDivisionError:
        safe_numexpr_eval.err_msg = f"numexpr: Zero division error in '{expr}'"
        logger.warning(safe_numexpr_eval.err_msg)
        safe_numexpr_eval.err = 6
        debug_exception()

    if np_expr is None:
        return None  # no fallback, no error checking!

    # check if dimensions of converted string agree with expected dimensions
    if np.ndim(np_expr) != np.ndim(fallback):
        if np.ndim(np_expr) == 0:
            # np_expr is scalar, return array with shape of fallback of constant values
            np_expr = np.ones(fallback_shape) * np_expr
        else:
            # return array of zeros in the shape of the fallback
            safe_numexpr_eval.err_msg = (
                f"numexpr: Expression has unexpected number of dimensions {np.ndim(np_expr)}!")
            logger.warning(safe_numexpr_eval.err_msg)
            safe_numexpr_eval.err = 11

            np_expr = np.zeros(fallback_shape)

    if np.shape(np_expr) != fallback_shape:
        safe_numexpr_eval.err_msg = (
            f"numexpr: Expression has unsuitable length {np.shape(np_expr)[0]}!")
        logger.warning(safe_numexpr_eval.err_msg)
        safe_numexpr_eval.err = 12

        np_expr = np.zeros(fallback_shape)

    if type(np_expr.item(0)) not in {float, complex}:
        np_expr = np_expr.astype(float)

    return np_expr


# ------------------------------------------------------------------------------
def safe_eval(expr, alt_expr=0, return_type: str = 'float', sign: str = ''
              ) -> complex|float|int:
    """
    Try to safely evaluate `expr` using `numexpr.evaluate()` and return the
    result as float (default), complex or int, depending on `return_type`.
    The sign of the result can be enforced to be positive or negative using
    parameter `sign`.

    When evaluation fails or returns `None`, try evaluating `alt_expr`.
    When this also fails, return 0 to avoid errors further downstream.

    Parameters
    ----------
    expr: str or scalar
       Expression to be evaluated, is cast to a string

    alt_expr: str or scalar
        Expression to be evaluated when evaluation of first string fails, is
        cast to a string.

    return_type: str
        Type of returned variable ['float' (default) / 'cmplx' / 'int' / '' or 'auto']

    sign: str
        enforce positive / negative sign of result ['pos', 'poszero' / '' (default)
                                                    'negzero' / 'neg']

    Returns
    -------
    result : float / complex / int
        the evaluated result or 0 when neither `expr` nor `alt_expr` could be evaluated


    Function attribute `err` contains number of errors that have occurred during
    evaluation (0 / 1 / 2)
    """
    # convert to str and remove non-ascii characters
    expr = clean_ascii(str(expr))
    alt_expr = clean_ascii(str(alt_expr))

    result = None
    fallback = ""
    safe_eval.err = 0  # initialize function attribute

    for ex in [expr, alt_expr]:
        if ex == "":
            result = None
            logger.warning("Passed an empty string, nothing was changed!")
        else:
            if return_type not in {'float', 'int', 'cmplx', 'auto', ''}:
                logger.error('Unknown return type "%s", setting result to 0.', return_type)

            ex_num = safe_numexpr_eval(ex)
            if ex_num is not None:

                if return_type == 'cmplx':
                    result = ex_num.item()
                elif return_type == '' or return_type == 'auto':
                    result = np.real_if_close(ex_num).item()
                else:  # return_type == 'float' or 'int'
                    result = ex_num.real.item()

                if sign == '':  # no sign enforcement
                    pass
                elif sign in {'pos', 'poszero'}:
                    result = np.abs(result)
                elif sign in {'neg', 'negzero'}:
                    result = -np.abs(result)
                else:
                    logger.error('Unknown sign enforcement "%s".', sign)

                if result == 0 and sign in {'pos', 'neg'}:
                    logger.warning('%sArgument must not be zero.', fallback)
                    result = None

                if return_type == 'int' and result is not None:
                    # convert to standard int type, not np.int64
                    result = int(result.real)

        if result is not None:
            break  # break out of for loop when evaluation has succeeded
        fallback = "Fallback: "
        safe_eval.err += 1

    if result is None:
        result = 0
    return result


# ------------------------------------------------------------------------------
def debug_exception(msg: str = "") -> None:
    """
    React to an exception depending on the debug level. When debug level is high,
    use the traceback module for full traceback. Otherwise, keep quiet.
    """
    if CFP.conf_settings['EXCEPTION_LEVEL'] >= 1:
        logger.info("debug_exception(): Level %s.", CFP.conf_settings['EXCEPTION_LEVEL'])
        # get current stack trace as a list of strings. Each string consists of
        #   "  File '...'\n, line ..., in ...\n"
        err_list = traceback.format_stack()
        err_str = msg + "\n\t"
        # skip the first entries and the last two (it's this function and the caller)
        for s in err_list[4:-2]:
            err_str += s.strip(' \t\n').replace("\n", "\n\t\t") + "\n\t" # indent traceback lines
        logger.error(err_str)
    if CFP.conf_settings['EXCEPTION_LEVEL'] >= 2:
        raise SystemExit("from debug_exception!")


# ------------------------------------------------------------------------------
def expand_lim(ax, eps_x: float, eps_y: float = None) -> None:

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
    None
    """

    if not eps_y:
        eps_y = eps_x
    xmin, xmax, ymin, ymax = ax.axis()
    dx = (xmax - xmin) * eps_x
    dy = (ymax - ymin) * eps_y
    ax.axis((xmin-dx, xmax+dx, ymin-dy, ymax+dy))


# ------------------------------------------------------------------------------
def format_ticks(ax, xy: str, scale: float = 1., format: str = "%.1f") -> None:
    """
    Reformat numbers at x or y - axis. The scale can be changed to display
    e.g. MHz instead of Hz. The number format can be changed as well.

    Parameters
    ----------

    ax : axes object

    xy : string, either 'x', 'y' or 'xy'
         select corresponding axis (axes) for reformatting

    scale : float (default: 1.)
            rescaling factor for the axes

    format : string (default: %.1f)
             define C-style number formats

    Returns
    -------
    None


    Examples
    --------
    Scale all numbers of x-Axis by 1000, e.g. for displaying ms instead of s.

    >>> format_ticks('x',1000.)

    Two decimal places for numbers on x- and y-axis

    >>> format_ticks('xy',1., format = "%.2f")

    """
    if xy == 'x' or xy == 'xy':
        # get location and content of xticks
        # locx,labelx = ax.get_xticks(), ax.get_xticklabels()
        locx = ax.get_xticks()
        ax.set_xticks(locx)
        ax.set_xtticklabels([format % x for x in locx*scale])
        # ax.set_xticks(locx, map(lambda x: format % x, locx*scale))

    if xy == 'y' or xy == 'xy':
        locy = ax.get_yticks()  # get location and content of xticks
        ax.set_yticks(locy)
        ax.set_yticklabels([format % y for y in locy*scale])

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # ==============================================================================
    pass
