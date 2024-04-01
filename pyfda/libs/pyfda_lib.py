# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Library with various general functions and variables needed by the pyfda routines
"""
import logging
logger = logging.getLogger(__name__)

import os, re, io
import sys, time
import struct
from contextlib import redirect_stdout
import numpy as np
from numpy import ndarray, pi, log10, sin, cos
import numexpr
import markdown

import scipy.signal as sig

from distutils.version import LooseVersion
import pyfda.filterbroker as fb
import pyfda.libs.pyfda_dirs as dirs
import pyfda.libs.pyfda_sig_lib as pyfda_sig_lib

# ###### VERSIONS and related stuff ############################################
# ================ Required Modules ============================
# ==
# == When one of the following imports fails, terminate the program
from scipy import __version__ as V_SCI
from matplotlib import __version__ as V_MPL
from .compat import QT_VERSION_STR as V_QT
from .compat import PYQT_VERSION_STR as V_PYQT
from markdown import __version__ as V_MD

V_NP = np.__version__
V_NUM = numexpr.__version__
V_NUM_MKL = numexpr.get_vml_version()
if V_NUM_MKL:
    MKL = f" (mkl: {V_NUM_MKL:s})"
else:
    MKL = " (no mkl)"

# # redirect stdio output of show_config to string
# f = io.StringIO()
# with redirect_stdout(f):
#     np.show_config()
# INFO_NP = f.getvalue()


# if 'mkl_info' in INFO_NP:
#     MKL = " (mkl)"
# else:
#     MKL = ""

# # logger.warning(INFO_NP)


__all__ = ['cmp_version', 'mod_version',
           'set_dict_defaults', 'clean_ascii', 'qstr', 'safe_eval',
           'dB', 'lin2unit', 'unit2lin',
           'cround', 'H_mag', 'cmplx_sort', 'unique_roots',
           'expand_lim', 'format_ticks', 'fil_save', 'fil_convert', 'sos2zpk',
           'round_odd', 'round_even', 'ceil_odd', 'floor_odd', 'ceil_even', 'floor_even',
           'to_html', 'calc_Hcomplex']

PY32_64 = struct.calcsize("P") * 8  # yields 32 or 64, depending on 32 or 64 bit Python

V_PY = ".".join(map(str, sys.version_info[:3])) + " (" + str(PY32_64) + " Bit)"

# ================ Required Modules ============================
MODULES = {'python':       {'V_PY': V_PY},
           'matplotlib':   {'V_MPL': V_MPL},
           'Qt5':          {'V_QT': V_QT},
           'pyqt':         {'V_PYQT': V_PYQT},
           'numpy':        {'V_NP': V_NP},
           'numexpr':      {'V_NUM': V_NUM},
           'scipy':        {'V_SCI': V_SCI + MKL},
           'markdown':     {'V_MD': V_MD}
           }

# ================ Optional Modules ============================
try:
    from docutils import __version__ as V_DOC
    MODULES.update({'docutils': {'V_DOC': V_DOC}})
except ImportError:
    MODULES.update({'docutils': {'V_DOC': "not found"}})

try:
    from mplcursors import __version__ as V_CUR
    MODULES.update({'mplcursors': {'V_CUR': V_CUR}})
except ImportError:
    MODULES.update({'mplcursors': {'V_CUR': "not found"}})

MODULES.update({'yosys': {'V_YO': dirs.YOSYS_VER}})

try:
    from xlwt import __version__ as V_XLWT
    MODULES.update({'xlwt': {'V_XLWT': V_XLWT}})
except ImportError:
    MODULES.update({'xlwt': {'V_XLWT': "not found"}})

try:
    from xlsxwriter import __version__ as V_XLSX
    MODULES.update({'xlsx': {'V_XLSX': V_XLSX}})
except ImportError:
    MODULES.update({'xlsx': {'V_XLSX': "not found"}})

try:
    from amaranth import __version__ as V_AM
    MODULES.update({'amaranth': {'V_AM': V_AM}})
except ImportError:
    MODULES.update({'amaranth': {'V_AM': "not found"}})


# Remove module names as keys and return a dict with items like
#  {'V_MPL':'3.3.1', ...}
MOD_VERSIONS = {}
for k in MODULES.keys():
    MOD_VERSIONS.update(MODULES[k])

CRLF = os.linesep  # Windows: "\r\n", Mac OS: "\r", *nix: "\n"


# ------------------------------------------------------------------------------
def cmp_version(mod, version):
    """
    Compare version number of installed module `mod` against string `version` and
    return 1, 0 or -1 if the installed version is greater, equal or less than
    the number in `version`. If `mod` is not installed, return -2.

    Parameters
    ----------

    mod : str
        name of the module to be compared

    version : str
        version number in the form e.g. "0.1.6"

    Returns
    -------

    result : int
        one of the following error codes:

         :-2: module is not installed

         :-1: version of installed module is lower than the specified version

         :0: version of installed module is equal to specied version

         :1: version of installed module is higher than specified version

    """
    try:
        if mod not in MODULES or not MODULES[mod].values():
            return -2
        else:
            # get dict value without knowing the key:
            inst_ver = list(MODULES[mod].values())[0]

        if LooseVersion(inst_ver) > LooseVersion(version):
            return 1
        elif LooseVersion(inst_ver) == LooseVersion(version):
            return 0
        else:
            return -1
    except (TypeError, KeyError) as e:
        logger.warning("Version number of {0} could not be determined.\n"
                       "({1})".format(mod, e))
        return -1


# ------------------------------------------------------------------------------
def mod_version(mod=None):
    """
    Return the version of the module 'mod'. If the module is not found, return
    None. When no module is specified, return a string with all modules and
    their versions sorted alphabetically.
    """
    if mod:
        if mod in MODULES:
            return LooseVersion(list(MODULES[mod].values())[0])
        else:
            return None
    else:
        v_md = ""
        with open(os.path.join(dirs.INSTALL_DIR, "module_versions.md"), 'r') as f:
            # return a list, split at linebreaks while keeping linebreaks
            v = f.read().splitlines(True)

        for k in v:
            try:
                # evaluate {V_...} from MOD_VERSIONS entries:
                v_md += k.format(**MOD_VERSIONS)
            except (KeyError) as e:  # encountered undefined {V_...}
                logger.warning("KeyError: {0}".format(e))  # simply drop the line

        v_html = markdown.markdown(v_md, output_format='html5',
                                   extensions=['markdown.extensions.tables'])
        # pyinstaller needs explicit definition of extensions path

        return v_html


# ------------------------------------------------------------------------------
logger.info(mod_version())

# Amplitude max, min values to prevent scipy aborts
# (Linear values)
MIN_PB_AMP  = 1e-5  # min pass band ripple
MAX_IPB_AMP = 0.85  # max pass band ripple IIR
MAX_FPB_AMP = 0.5  # max pass band ripple FIR
MIN_SB_AMP  = 1e-6  # max stop band attenuation
MAX_ISB_AMP = 0.65  # min stop band attenuation IIR
MAX_FSB_AMP = 0.45  # min stop band attenuation FIR


class ANSIcolors:
    """
    ANSI Codes for colors etc. in the console

    see https://stackoverflow.com/questions/4842424/list-of-ansi-color-escape-sequences
        https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    """
    if dirs.OS.lower() == "windows":
        os.system('color')  # needed to activate colored terminal in Windows

    CEND      = '\33[0m'
    CBOLD     = '\33[1m'
    CFAINT    = '\33[2m'
    CITALIC   = '\33[3m'
    CURL      = '\33[4m'  # underlined
    CBLINK    = '\33[5m'  # slow blink
    CBLINK2   = '\33[6m'  # fast blink
    CSELECTED = '\33[7m'  # reverse video

    # Foreground colors
    BLACK  = '\33[30m'
    RED    = '\33[31m'
    GREEN  = '\33[32m'
    YELLOW = '\33[33m'
    BLUE   = '\33[34m'
    VIOLET = '\33[35m'
    CYAN   = '\33[36m'
    WHITE  = '\33[37m'

    # Background colors
    BLACKBG  = '\33[40m'
    REDBG    = '\33[41m'
    GREENBG  = '\33[42m'
    YELLOWBG = '\33[43m'
    BLUEBG   = '\33[44m'
    VIOLETBG = '\33[45m'
    CYANBG   = '\33[46m'
    WHITEBG  = '\33[47m'

    # Bright foreground colors
    GREY2   = '\33[90m'
    RED2    = '\33[91m'
    GREEN2  = '\33[92m'
    YELLOW2 = '\33[93m'
    BLUE2   = '\33[94m'
    VIOLET2 = '\33[95m'
    CYAN2   = '\33[96m'
    WHITE2  = '\33[97m'

    # Bright foreground colors
    GREYBG    = '\33[100m'
    REDBG2    = '\33[101m'
    GREENBG2  = '\33[102m'
    YELLOWBG2 = '\33[103m'
    BLUEBG2   = '\33[104m'
    VIOLETBG2 = '\33[105m'
    CYANBG2   = '\33[106m'
    WHITEBG2  = '\33[107m'


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
    else:
        return arg


# ------------------------------------------------------------------------------
def qstr(text):
    """
    Convert text (QVariant, QString, string) or numeric object to plain string.

    In Python 3, python Qt objects are automatically converted to QVariant
    when stored as "data" (itemData) e.g. in a QComboBox and converted back when
    retrieving to QString.
    In Python 2, QVariant is returned when itemData is retrieved.
    This is first converted from the QVariant container format to a
    QString, next to a "normal" non-unicode string.

    Parameters
    ----------

    text: QVariant, QString, string or numeric data type that can be converted
      to string

    Returns
    -------

    The current `text` data as a unicode (utf8) string
    """
    return str(text)  # this should be sufficient for Python 3 ?!

###############################################################################
# General functions ###########################################################
###############################################################################

def is_numeric(a) -> bool:
    """
    Return True when a or a.dtype is of a numeric type (complex, float, int, ...)

    Parameters
    ----------
    a : array-like or scalar

    Returns
    -------
    is_num : bool
        True when dtype of a is a numeric subtype
    """
    if isinstance(a, np.ndarray):
        is_num = np.issubdtype(a.dtype, np.number)
    else:
        is_num = np.issubdtype(type(a), np.number)
    return is_num


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
    2-dimensional data. Otherwise, return None
    """
    d = np.ndim(data)
    if d == 0:
        return (0, 0)
    elif d == 1:
        return(len(data), 1)
    elif  d == 2:
        return np.shape(data)
    else:
        logger.warning("Unsuitable data shape with "
        f"{d} dimensions.")
        return (None, None)

# -----------------------------------------------------------------------------
def iter2ndarray(iterable, dtype=complex) -> ndarray:
    """
    Convert an iterable (tuple, list, dict) to a numpy ndarray, egalizing
    different lengths of sub-iterables by adding zeros. This prevents
    problems with inhomogeneous arrays.
    """
    try:
        # logger.warning(iterable)
        if type(iterable) == np.ndarray:
            # no need to convert argument
            return iterable
        elif type(iterable) in {tuple, list}:
            arrs = []  # empty list for sub-arrays
            max_l = 0  # maximum length of sub-arrays
            for i in range(len(iterable)):
                if np.isscalar(iterable[i]):
                    arrs.append(np.array([iterable[i]]))
                else:
                    arrs.append(np.array(iterable[i]))
                max_l = max(max_l, len(arrs[i]))

            # equalize lengths of sub-arrays by filling up with zeros
            for i in range(len(iterable)):
                arrs[i] = np.append(arrs[i], np.zeros(max_l - len(arrs[i])))

            return np.nan_to_num(np.array(arrs, dtype=dtype))  # convert list of arrays to two-dimensional array
        else:
            logger.error(f"Unsupported type '{type(iterable)}' for conversion to ndarray.")
            return None
    except Exception as e:
        logger.error(f"Error '{e}'\nfor iterable =\n{iterable}")
        return None


# -----------------------------------------------------------------------------
def set_dict_defaults(d: dict, default_dict: dict) -> None:
    """
    Add the key:value pairs of `default_dict` to dictionary `d` in-place for
    all missing keys.
    """
    # Create a list of keys to avoid "dictionary size changed" runtime error
    for k in list(d.keys()):
        if k not in default_dict:
            d.pop(k)
            logger.warning(f"Deleted key '{k}' (not part of default dict).")
    if d == {}:
        d.update(default_dict)
    else:
        for k, v in default_dict.items():
            if k not in d:
                d[k] = v


# -------------------------------------------------------------------------------
def sanitize_imported_dict(new_dict: dict) -> list:

    def compare_dictionaries(
            ref_dict: dict, new_dict: dict, path: str = "") -> list:
        """
        Compare recursively a new dictionary `new_dict` to a reference dictionary `ref_dict`.
        Keys in `new_dict` that are not contained in `ref_dict` are deleted from `new_dict`,
        keys in `ref_dict` missing in `new_dict` are copied with their value to `new_dict`.

        Params
        ------
        ref_dict: dict
            reference dictionary
        new_dict: dict
            new dictionary
        path: str
            current path while traversing through the dictionaries

        Returns
        -------
        key_errs: list
            `key_errs[0]` contains all keys copied from `ref_dict` to `new_dict`.
            `key_errs[1]` contains all discarded keys from `new_dict`.
        """
        key_errs = [[], []]
        old_path = path

        for k in ref_dict:
            path = old_path + f"'{k}'"
            if not k in new_dict:
                key_errs[0].append(path)
                new_dict.update({k: ref_dict[k]})
            else:
                if isinstance(ref_dict[k], dict) and isinstance(new_dict[k], dict):
                    key_errs.append(compare_dictionaries(ref_dict[k], new_dict[k], path))

        # emulate slightly inefficient Python 2 way of copying the dict keys to a list
        # to avoid runtime error "dictionary changed size during iteration" due to new_dict.pop(k)
        for k in list(new_dict):
            path = old_path + f"'{k}'"
            if not k in ref_dict:
                key_errs[1].append(path)
                new_dict.pop(k)

        return key_errs
    # ----------------------------------------
    key_errs = compare_dictionaries(fb.fil_ref, new_dict)
    key_errs[0].sort()
    key_errs[1].sort()

    return key_errs[0], key_errs[1]


# -----------------------------------------------------------------------------
def first_item(d: dict) -> str:
    """
    Return the first item of the dictionary as a string. This only works in a
    reproducible fashion for Python 3.7 and above.
    """
    k = next(iter(d))
    return str(k) + ": " + str(d[k])


# ------------------------------------------------------------------------------
def pprint_log(d, N: int = 10, tab: str = "\t", debug: bool = False) -> str:
    """
    Provide pretty printed logging messages for dicts or lists.

    Convert dict `d` to string, inserting a CR+Tab after each key:value pair.

    If the value of dict key `d[k]` is a list or ndarray with more than `N` items,
    truncate it to `N` items.

    Parameters
    ----------
    d : iterable
        A dict or an array-like object with one or two dimensions
        to be pretty-printed

    N : int
        maximum number of items to be printed per dimension

    tab : str
        tabulator character / string, default: '\t'

    debug : bool
        add debug info to output string, default: False

    Returns
    -------
    s : str
        formatted and truncated iterable as a string
    """
    cr = os.linesep
    s = tab
    first = True
    if debug:
        logger.info(f"Data: {type(d).__name__}[{type(d[0]).__name__}], "
                    f"ndim={np.ndim(d)}")
    if type(d) == dict:
        for k in d:
            if not first:
                s += cr + tab
            if type(d[k]) in {list, np.ndarray}:
                s += k + ' (L=' + str(len(d[k])) + '): '\
                                + str(d[k][: min(N-1, len(d[k]))]) + ' ...'
            else:
                s += k + ' : ' + str(d[k])
            first = False
        return s
    if type(d) in {list, tuple}:
        try:
            _ = np.asarray(d)
        except (TypeError, ValueError) as e:
            logger.warning(f"pprint_log(): Could not transform data to array:\n{e}")
            return ""

    if type(d) in {list, np.ndarray, tuple}:
        if np.ndim(d) == 0: # iterable with a single element
            s = str(d) + f' of type: {type(d).__name__}'
        elif np.ndim(d) == 1:
            s = cr + tab + str(d[: min(N-1, len(d))])
            if len(d) > N-1:
                s += ' ...'
            s += (cr + tab + f'Type: {type(d).__name__} of {type(d[0]).__name__}, '
                  f'with shape = ({len(d)},)')
        elif np.ndim(d) == 2:
            rows, cols = np.shape(d)
            s += (f'Type: {type(d).__name__} of {type(d[0][0]).__name__}, '
                  f'shape = (r{rows} x c{cols})' + cr + tab)
            #  x.dtype.kind returns general information on numpy data (e.g. "iufc","SU")
            for r in range(min(N, rows)):
                if not first:
                    s += cr + tab
                # logger.warning(f'rows={rows}; min(N-1, rows)={min(N, rows)}\n'
                #                f'd={d[c][:min(N, rows)]}')
                s += str(d[r][:min(N, cols)])
                if cols > N-1:
                    s += ' ...'
                first = False
            if rows > N-1:
                    s += cr + tab + ' ...'
        else:
            logger.warning(f"pprint_log(): Object with ndim = {np.ndim(d)} cannot be processed.")
            return ""
    else:  # scalar, string or None
        if type(d) is None:
            s += ('Type: None')
        elif type(d) is str:
            s += (f' Type: str, length = {len(d)}' +  cr + tab + d[: min(N-1, len(d))])
            if len(d) > N-1:
                s += ' ...'
        elif np.isscalar(d):
            s = str(d) + f' of type: {type(d).__name__}'
        else:
            s += 'Type: {type(d).__name__}'
    return s


# ------------------------------------------------------------------------------
def safe_numexpr_eval(expr: str, fallback=None,
                      local_dict: dict = {}) -> ndarray:
    """
    Evaluate `numexpr.evaluate(expr)` and catch various errors.

    Parameters
    ----------
    expr : str
        String to be evaluated and converted to a numpy array

    fallback : array-like or tuple
        numpy array or scalar as a fallback when errors occur during evaluation,
        this also defines the expected shape of the returned numpy expression

        When fallback is a tuple (e.g. '(11,)'), provide an array of zeros with
        the passed shape.

    local_dict : dict
        dict with variables passed to `numexpr.evaluate`

    Returns
    -------
    np_expr : array-like
        `expr` converted to a numpy array or scalar

    """
    safe_numexpr_eval.err = 0  # function attribute, providing some sort of "memory"
    local_dict.update({'j': 1j, 'None': 0})
    if type(fallback) == tuple:
        np_expr = np.zeros(fallback)  # fallback defines the shape
        fallback_shape = fallback
    else:
        np_expr = fallback  # fallback is the default numpy return value or None
        fallback_shape = np.shape(fallback)

    if type(expr) != str or expr == "None":
        logger.warning(f"numexpr: Unsuitable input '{expr}' of type "
                       f"'{type(expr).__name__}', replacing with zero.")
        safe_numexpr_eval.err = 10
        expr = "0.0"

    # Find one or more redundant zeros '0+' at the beginning '^' leading a number [0-9]
    # Group the number(s) '(...)' and write it '\1' to the resulting string.
    expr = re.sub(r'^0+([0-9])', r'\1', expr)
    if len(expr) == 0:
        expr = "0"
    else:
        expr = expr.replace(',', '.')  # ',' -> '.' for German-style numbers
        if expr[0] == '.':  # prepend '0' when the number starts with '.'
            expr = "0" + expr
    try:
        np_expr = numexpr.evaluate(expr.strip(), local_dict=local_dict)
    except SyntaxError as e:
        logger.warning(f"numexpr: Syntax error:\n\t{e}")
        safe_numexpr_eval.err = 1
    except AttributeError as e:
        logger.warning(f"numexpr: Attribute error:\n\t{e}")
        safe_numexpr_eval.err = 2
    except KeyError as e:
        logger.warning(f"numexpr: Unknown variable {e}")
        safe_numexpr_eval.err = 3
    except TypeError as e:
        logger.warning(f"numexpr: Type error\n\t{e}")
        safe_numexpr_eval.err = 4
    except ValueError as e:
        logger.warning(f"numexpr: Value error:\n\t{e}")
        safe_numexpr_eval.err = 5
    except ZeroDivisionError:
        logger.warning("numexpr: Zero division error in formula.")
        safe_numexpr_eval.err = 6

    if np_expr is None:
        return None  # no fallback, no error checking!

    # check if dimensions of converted string agrees with expected dimensions
    elif np.ndim(np_expr) != np.ndim(fallback):
        if np.ndim(np_expr) == 0:
            # np_expr is scalar, return array with shape of fallback of constant values
            np_expr = np.ones(fallback_shape) * np_expr
        else:
            # return array of zeros in the shape of the fallback
            logger.warning(
                f"numexpr: Expression has unexpected dimension {np.ndim(np_expr)}!")
            safe_numexpr_eval.err = 11

            np_expr = np.zeros(fallback_shape)

    if np.shape(np_expr) != fallback_shape:
        logger.warning(
            f"numexpr: Expression has unsuitable length {np.shape(np_expr)[0]}!")
        safe_numexpr_eval.err = 12

        np_expr = np.zeros(fallback_shape)

    if not type(np_expr.item(0)) in {float, complex}:
        np_expr = np_expr.astype(float)

    return np_expr


# ------------------------------------------------------------------------------
def safe_eval(expr, alt_expr=0, return_type: str = "float", sign: str = None
              ):  # -> complex|float|int: only works with py3.10 upawards
    """
    Try ... except wrapper around numexpr to catch various errors
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
        enforce positive / negative sign of result ['pos', 'poszero' / None (default)
                                                    'negzero' / 'neg']

    Returns
    -------
    the evaluated result or 0 when both arguments fail: float (default) / complex / int


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
                logger.error(
                    'Unknown return type "{0}", setting result to 0.'.format(return_type))

            ex_num = safe_numexpr_eval(ex)
            if ex_num is not None:

                if return_type == 'cmplx':
                    result = ex_num.item()
                elif return_type == '' or return_type == 'auto':
                    result = np.real_if_close(ex_num).item()
                else:  # return_type == 'float' or 'int'
                    result = ex_num.real.item()

                if sign in {'pos', 'poszero'}:
                    result = np.abs(result)
                elif sign in {'neg', 'negzero'}:
                    result = -np.abs(result)

                if result == 0 and sign in {'pos', 'neg'}:
                    logger.warning(fallback + 'Argument must not be zero.')
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
def to_html(text: str, frmt: str = None) -> str:
    """
    Convert text to HTML format:
        - pretty-print logger messages
        - convert "\\n" to "<br />
        - convert "< " and "> " to "&lt;" and "&gt;"
        - format strings with italic and / or bold HTML tags, depending on
          parameter `frmt`. When `frmt=None`, put the returned string between
          <span> tags to enforce HTML rendering downstream
        - replace '_' by HTML subscript tags. Numbers 0 ... 9 are never set to
          italic format

    Parameters
    ----------

    text: str
        Text to be converted

    frmt: str
        define text style

        - 'b' : bold text
        - 'i' : italic text
        - 'bi' or 'ib' : bold and italic text

    Returns
    -------

    str
        HTML - formatted text

    Examples
    --------

        >>> to_html("F_SB", frmt='bi')
        "<b><i>F<sub>SB</sub></i></b>"
        >>> to_html("F_1", frmt='i')
        "<i>F</i><sub>1</sub>"
    """
    # see https://danielfett.de/de/tutorials/tutorial-regulare-ausdrucke/
    # arguments for regex replacement with illegal characters
    # [a-dA-D] list of characters
    # \w : meta character for [a-zA-Z0-9_]
    # \s : meta character for all sorts of whitespace
    # [123][abc] test for e.g. '2c'
    # '^' means "not", '|' means "or" and '\' escapes, '.' means any character,
    # '+' means once or more, '?' means zero or once, '*' means zero or more
    #   '[^a]' means except for 'a'
    # () defines a group that can be referenced by \1, \2, ...
    #
    # '([^)]+)' : match '(', gobble up all characters except ')' till ')'
    # '(' must be escaped as '\('

    # mappings text -> HTML formatted logging messages

    if frmt == 'log':
        # only in logging messages replace e.g. in <class> the angled brackets
        # by HTML code
        mapping = [('<', '&lt;'), ('>', '&gt;')]
        for k, v in mapping:
            text = text.replace(k, v)

    mapping = [('< ', '&lt;'), ('> ', '&gt;'), ('\n', '<br />'),
               ('\t', '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'),
               ('[  DEBUG]', '<b>[  DEBUG]</b>'),
               ('[   INFO]', '<b style="color:darkgreen;">[   INFO]</b>'),
               ('[WARNING]', '<b style="color:orange;">[WARNING]</b>'),
               ('[  ERROR]', '<b style="color:red">[  ERROR]</b>')
               ]

    for k, v in mapping:
        text = text.replace(k, v)
    html = text
    if frmt in {'i', 'bi', 'ib'}:
        html = "<i>" + html + "</i>"
    if frmt in {'b', 'bi', 'ib'}:
        html = "<b>" + html + "</b>"
    if frmt is None:
        html = "<span>" + html + "</span>"

    if frmt != 'log':  # this is a label, not a logger message
        # replace _xxx (where xxx are alphanumeric, non-space characters \w) by <sub> xxx </sub> ()
        if "<i>" in html:  # make subscripts non-talic
            html = re.sub(r'_(\w+)', r'</i><sub>\1</sub><i>', html)
        else:
            html = re.sub(r'_(\w+)', r'<sub>\1</sub>', html)

    return html


# ##############################################################################
# ###     Scipy-like    ########################################################
# ##############################################################################
def dB(lin: float, power: bool = False) -> float:
    """
    Calculate dB from linear value. If power = True, calculate 10 log ...,
    else calculate 20 log ...
    """
    if power:
        return 10. * np.log10(lin)
    else:
        return 20 * np.log10(lin)


# ------------------------------------------------------------------------------
def lin2unit(lin_value: float, filt_type: str, amp_label: str,
             unit: str = 'dB') -> float:
    """
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
    """
    Convert amplitude specification in dB or W to linear specs:

    - Passband:
        .. math::

            \\text{IIR:}\quad A_{PB,lin} &= 1 - 10 ^{-unit\_value/20}

            \\text{FIR:}\quad A_{PB,lin} &= \\frac{10 ^ {unit\_value/20} - 1}{10 ^ {unit\_value/20} + 1}

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
            "Amplitude spec for {0} is ".format(amp_label) + msg
            + "using {0:.4g} {1} instead."
            .format(
                lin2unit(lin_value, filt_type=filt_type, amp_label=amp_label, unit=unit),
                unit))

    return lin_value


# ------------------------------------------------------------------------------
def cround(x, n_dig=0):
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


# ------------------------------------------------------------------------------
def sawtooth_bl(t):
    """
    Bandlimited sawtooth function as a direct replacement for
    `scipy.signal.sawtooth`. It is calculated by Fourier synthesis, i.e.
    by summing up all sine wave components up to the Nyquist frequency.

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
def triang_bl(t):
    """
    Bandlimited triangle function as a direct replacement for
    `scipy.signal.sawtooth(width=0.5)`. It is calculated by Fourier synthesis, i.e.
    by summing up all sine wave components up to the Nyquist frequency.

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
def rect_bl(t, duty=0.5):
    """
    Bandlimited rectangular function as a direct replacement for
    `scipy.signal.square`. It is calculated by Fourier synthesis, i.e.
    by summing up all sine wave components up to the Nyquist frequency.

    By Endolith, https://gist.github.com/endolith/407991
    """
    if t.dtype.char in ['fFdD']:
        ytype = t.dtype.char
    else:
        ytype = 'd'
    y = np.zeros(t.shape, ytype)
    # Get sampling frequency from timebase
    # Sum all multiple sine waves up to the Nyquist frequency:
    y = sawtooth_bl(t - duty*2*pi) - sawtooth_bl(t) + 2*duty-1
    return y


# ------------------------------------------------------------------------------
def comb_bl(t):
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
def H_mag(num, den, z, H_max, H_min=None, log=False, div_by_0='ignore'):
    """
    Calculate `\|H(z)\|` at the complex frequency(ies) `z` (scalar or
    array-like).  The function `H(z)` is given in polynomial form with numerator and
    denominator. When ``log == True``, :math:`20 \log_{10} (|H(z)|)` is returned.

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
    H_mag : float or ndarray
        The magnitude `\|H(z)\|` for each value of `z`.
    """

    try:
        len(num)
    except TypeError:
        num_val = abs(num)  # numerator is a scalar
    else:
        num_val = abs(np.polyval(num, z))  # evaluate numerator at z
    try:
        len(den)
    except TypeError:
        den_val = abs(den)  # denominator is a scalar
    else:
        den_val = abs(np.polyval(den, z))  # evaluate denominator at z

    olderr = np.geterr()  # store current floating point error behaviour
    # turn off divide by zero warnings, just return 'inf':
    np.seterr(divide='ignore')

    H_val = np.nan_to_num(num_val / den_val)  # remove nan and inf
    if log:
        H_val = 20 * np.log10(H_val)

    np.seterr(**olderr)  # restore previous floating point error behaviour

    # clip result to H_min / H_max
    return np.clip(H_val, H_min, H_max)


# ------------------------------------------------------------------------------
# from scipy.sig.signaltools.py:
def cmplx_sort(p):
    "sort roots based on magnitude."
    p = np.asarray(p)
    if np.iscomplexobj(p):
        indx = np.argsort(abs(p))
    else:
        indx = np.argsort(p)
    return np.take(p, indx, 0), indx


# ------------------------------------------------------------------------------
# adapted from scipy.signal.signaltools.py:
# TODO:  comparison of real values has several problems (5 * tol ???)
# TODO: speed improvements
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

    """

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

    tol = abs(tol)
    p = np.atleast_1d(p)  # convert p to at least 1D array
    if len(p) == 0:
        return pout, mult

    elif len(p) == 1:
        pout = p
        mult = [1]
        return pout, mult

    else:
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
def calc_ssb_spectrum(A: ndarray) -> ndarray:
    """
    Calculate the single-sideband spectrum from a double-sideband
    spectrum by doubling the spectrum below fS/2 (leaving the DC-value
    untouched). This approach is wrong when the spectrum is not symmetric.

    The alternative approach of  adding the mirrored conjugate complex of the
    second half of the spectrum to the first doesn't work, spectra of either
    sine-like or cosine-like signals are cancelled out.

    When len(A) is even, A[N//2] represents half the sampling frequencvy
    and is discarded (Q: also for the power calculation?).

    Parameters
    ----------
    A : array-like
        double-sided spectrum, usually complex. The sequence is as follows:

            [0, 1, 2, ..., 4, -5, -4, ... , -1] for len(A) = 10

    Returns
    -------
    A_SSB : array-like
        single-sided spectrum with half the number of input values

    """
    N = len(A)

    A_SSB = np.insert(A[1:N//2] * 2, 0, A[0])
    # A_SSB = np.insert(A[1:N//2] + A[-1:-(N//2):-1].conj(),0, A[0]) # doesn't work

    return A_SSB


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
        ax.set_xticks(locx, map(lambda x: format % x, locx*scale))
    if xy == 'y' or xy == 'xy':
        locy = ax.get_yticks()  # get location and content of xticks
        ax.set_yticks(locy, map(lambda y: format % y, locy*scale))


# ------------------------------------------------------------------------------
def fil_save(fil_dict: dict, arg, format_in: str, sender: str,
             convert: bool = True) -> None:
    """
    Save filter design ``arg`` given in the format specified as ``format_in`` in
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

        :'ba': Coefficient form: Filter coefficients in FIR format
                 (b, one dimensional) are automatically converted to IIR format (b, a).

        :'zpk': Zero / pole / gain format: When only zeroes are specified,
                  poles and gain are added automatically.

        :'sos': Second-order sections

    sender : string
        The name of the method that calculated the filter. This name is stored
        in ``fil_dict`` together with ``format_in``.

    convert : boolean
        When ``convert = True``, convert arg to the other formats.

    Returns
    -------
    None
    """

    if format_in == 'sos':
        fil_dict['sos'] = arg
        fil_dict['ft'] = 'IIR'

    elif format_in == 'zpk':
        format_error = False
        if isinstance(arg, np.ndarray) and np.ndim(arg) == 1:
            frmt = "nd1" #  one-dimensional numpy array
            logger.info(f"Format (zpk) is '{frmt}', shape = {np.shape(arg)}")
        elif isinstance(arg, np.ndarray) and np.ndim(arg) == 2:
            frmt = "nd2" #  two-dimensional numpy array
            # logger.info(f"Format (zpk) is '{frmt}', shape = {np.shape(arg)}")
        # elif any(isinstance(el, list) for el in arg):
        #     frmt = "lol"  # list or ndarray or tuple of lists
        elif any(isinstance(el, np.ndarray) for el in arg):
            frmt = "lon"  # list or tuple of ndarrays
            logger.warning(f"Format (zpk) is '{frmt}'.")
        else:
            format_error = True

        if frmt == "nd2":
            fil_dict['zpk'] = arg
            if np.any(arg[1]):  # non-zero poles -> IIR
                fil_dict['ft'] = 'IIR'
            else:
                fil_dict['ft'] = 'FIR'

        elif frmt == 'nd1':  # list / array with z only -> FIR
            z = arg
            p = np.zeros(len(z))
            gain = pyfda_sig_lib.zeros_with_val(len(z))  # create gain vector [1, 0, 0, ...]
            fil_dict['zpk'] = np.array([z, p, gain])
            fil_dict['ft'] = 'FIR'

        elif frmt == 'lon':  # list of  ndarrays
            if len(arg) == 3:
                fil_dict['zpk'] = np.array([arg[0], arg[1], arg[2]])
                if np.any(arg[1]):  # non-zero poles -> IIR
                    fil_dict['ft'] = 'IIR'
                else:
                    fil_dict['ft'] = 'FIR'
            else:
                logger.error(f"{len(arg)} rows instead of 3!")
                format_error = True
        else:
            format_error = True

# =============================================================================
#         if np.ndim(arg) == 1:
#             if np.ndim(arg[0]) == 0: # list / array with z only -> FIR
#                 z = arg
#                 p = np.zeros(len(z))
#                 k = 1
#                 fil_dict['zpk'] = [z, p, k]
#                 fil_dict['ft'] = 'FIR'
#             elif np.ndim(arg[0]) == 1: # list of lists
#                 if np.shape(arg)[0] == 3:
#                     fil_dict['zpk'] = [arg[0], arg[1], arg[2]]
#                     if np.any(arg[1]): # non-zero poles -> IIR
#                         fil_dict['ft'] = 'IIR'
#                     else:
#                         fil_dict['ft'] = 'FIR'
#                 else:
#                     format_error = True
#             else:
#                 format_error = True
#         else:
#             format_error = True
#
# =============================================================================
        if format_error:
            raise ValueError("\t'fil_save()': Unknown 'zpk' format {0}".format(arg))

    elif format_in == 'ba':
        if np.ndim(arg) == 1:  # arg = [b] -> FIR
            # convert to type array, trim trailing zeros which correspond to
            # (superfluous) highest order polynomial with coefficient 0 as they
            # cause trouble when converting to zpk format
            b = np.trim_zeros(np.asarray(arg))
            a = np.zeros(len(b))
        else:  # arg = [b,a]
            b = arg[0]
            a = arg[1]

        if len(b) < 2:  # no proper coefficients, initialize with a default
            b = np.asarray([1, 0])
        if len(a) < 2:  # no proper coefficients, initialize with a default
            a = np.asarray([1, 0])

        a[0] = 1  # first coefficient of recursive filter parts always = 1

        # Determine whether it's a FIR or IIR filter and set fil_dict accordingly
        # Test whether all elements except the first one are zero
        if not np.any(a[1:]):
            fil_dict['ft'] = 'FIR'
        else:
            fil_dict['ft'] = 'IIR'

        # equalize if b and a subarrays have different lengths:
        D = len(b) - len(a)
        if D > 0:  # b is longer than a -> fill up a with zeros
            a = np.append(a, np.zeros(D))
        elif D < 0:  # a is longer than b -> fill up b with zeros
            if fil_dict['ft'] == 'IIR':
                b = np.append(b, np.zeros(-D))  # make filter causal, fill up b with zeros
            else:
                a = a[:D]  # discard last D elements of a (only zeros anyway)

        fil_dict['N'] = len(b) - 1  # correct filter order accordingly
        fil_dict['ba'] = [np.array(b, dtype=complex), np.array(a, dtype=complex)]

    else:
        raise ValueError("\t'fil_save()':Unknown input format {0:s}".format(format_in))

    fil_dict['creator'] = (format_in, sender)
    fil_dict['timestamp'] = time.time()

    if convert:
        fil_convert(fil_dict, format_in)


# ------------------------------------------------------------------------------
def fil_convert(fil_dict: dict, format_in) -> None:
    """
    Convert between poles / zeros / gain, filter coefficients (polynomes)
    and second-order sections and store all formats not generated by the filter
    design routine in the passed dictionary ``fil_dict``.

    Parameters
    ----------
    fil_dict :  dict
         filter dictionary containing a.o. all formats to be read and written.

    format_in :  string or set of strings

         format(s) generated by the filter design routine. Must be one of

         :'sos': a list of second order sections - all other formats can easily
                 be derived from this format
         :'zpk': [z,p,k] where z is the array of zeros, p the array of poles and
             k is a scalar with the gain - the polynomial form can be derived
             from this format quite accurately
         :'ba': [b, a] where b and a are the polynomial coefficients - finding
                   the roots of the a and b polynomes may fail for higher orders

    Returns
    -------
    None

    Exceptions
    ----------
    ValueError for Nan / Inf elements or other unsuitable parameters
    """
    if 'sos' in format_in:
        # check for bad coeffs before converting IIR filt
        # this is the same defn used by scipy (tolerance of 1e-14)
        if (fil_dict['ft'] == 'IIR'):
            chk = np.asarray(fil_dict['sos'])
            chk = np.absolute(chk)
            n_sections = chk.shape[0]
            for section in range(n_sections):
                b1 = chk[section, :3]
                a1 = chk[section, 3:]
                if ((np.amin(b1)) < 1e-14 and np.amin(b1) > 0):
                    raise ValueError(
                        "\t'fil_convert()': Bad coefficients, Order N is too high!")

        if 'zpk' not in format_in:
            try:
                # returns a tuple (zeros, poles, gain) where gain is scalar:
                zpk = list(sig.sos2zpk(fil_dict['sos']))
            except Exception as e:
                raise ValueError(e)
            # check whether sos conversion has created a additional (superfluous)
            # pole and zero at the origin and delete them:
            z_0 = np.where(zpk[0] == 0)[0]
            p_0 = np.where(zpk[1] == 0)[0]
            if p_0 and z_0:  # eliminate z = 0 and p = 0 from list:
                zpk[0] = np.delete(zpk[0], z_0)
                zpk[1] = np.delete(zpk[1], p_0)
            fil_dict['zpk'] = np.array(
                [zpk[0], zpk[1], pyfda_sig_lib.zeros_with_val(len(zpk[0]), zpk[2])],
                dtype=complex)

        if 'ba' not in format_in:
            try:
                fil_dict['ba'] = list(sig.sos2tf(fil_dict['sos']))
            except Exception as e:
                raise ValueError(e)
            # check whether sos conversion has created additional (superfluous)
            # highest order polynomial with coefficient 0 and delete them
            if fil_dict['ba'][0][-1] == 0 and fil_dict['ba'][1][-1] == 0:
                fil_dict['ba'][0] = np.delete(fil_dict['ba'][0], -1)
                fil_dict['ba'][1] = np.delete(fil_dict['ba'][1], -1)

    elif 'zpk' in format_in:  # z, p, k have been generated,convert to other formats
        zpk = fil_dict['zpk']
        if 'ba' not in format_in:
            try:
                fil_dict['ba'] = sig.zpk2tf(zpk[0], zpk[1], zpk[2][0])
            except Exception as e:
                raise ValueError(e)
        if 'sos' not in format_in:
            fil_dict['sos'] = []  # don't convert zpk -> SOS due to numerical inaccuracies
#            try:
#                fil_dict['sos'] = sig.zpk2sos(zpk[0], zpk[1], zpk[2])
#            except ValueError:
#                fil_dict['sos'] = []
#                logger.warning("Complex-valued coefficients, could not convert to SOS.")

    elif 'ba' in format_in:  # arg = [b,a]
        b, a = fil_dict['ba'][0], fil_dict['ba'][1]
        if np.all(np.isfinite([b, a])):
            zpk = sig.tf2zpk(b, a)
            if len(zpk[0]) != len(zpk[1]):
                logger.warning("Bad coefficients, some values of b are too close to zero,"
                               "\n\tresults may be inaccurate.")
            zpk_arr = pyfda_sig_lib.zpk2array(zpk)
            if not type(zpk_arr) is np.ndarray:  # an error has ocurred, error string is returned
                logger.error(zpk_arr)
                return
            else:
                fil_dict['zpk'] = zpk_arr
        else:
            raise ValueError(
                "\t'fil_convert()': Cannot convert coefficients with NaN or Inf elements "
                "to zpk format!")
            zpk = None
        fil_dict['sos'] = []  # don't convert ba -> SOS due to numerical inaccuracies
#        if SOS_AVAIL:
#            try:
#                fil_dict['sos'] = sig.tf2sos(b,a)
#            except ValueError:
#                fil_dict['sos'] = []
#                logger.warning("Complex-valued coefficients, could not convert to SOS.")

    else:
        raise ValueError(f"\t'fil_convert()': Unknown input format {format_in:s}")

    # eliminate complex coefficients created by numerical inaccuracies
    # `tol` is specified in multiples of machine eps
    fil_dict['ba'] = np.real_if_close(fil_dict['ba'], tol=100)


# ------------------------------------------------------------------------------
def sos2zpk(sos):
    """
    Taken from scipy/signal/filter_design.py - edit to eliminate first
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
        logger.info(sos[section])
        zpk = sig.tf2zpk(sos[section, :3], sos[section, 3:])
#        if sos[section, 3] == 0: # first order section
        z[2*section:2*(section+1)] = zpk[0]
#        if sos[section, -1] == 0: # first order section
        p[2*section:2*(section+1)] = zpk[1]
        k *= zpk[2]

    return z, p, k


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


# ------------------------------------------------------------------------------
def calc_Hcomplex(fil_dict, worN, wholeF, fs=2*np.pi):
    """
    A wrapper around `signal.freqz()` for calculating the complex frequency
    response H(f) for antiCausal systems as well. The filter coefficients are
    are extracted from the filter dictionary.

    Parameters
    ----------

    fil_dict: dict
        dictionary with filter data (coefficients etc.)

    worN: {None, int or array-like}
        number of points or frequencies where the frequency response is calculated

    wholeF: bool
        when True, calculate frequency response from 0 ... f_S, otherwise
        calculate between 0 ... f_S/2

    fs: float
        sampling frequency, used for calculation of the frequency vector.
        The default is 2*pi

    Returns
    -------

    w: ndarray
        The frequencies at which h was computed, in the same units as fs.
        By default, w is normalized to the range [0, pi) (radians/sample).

    h: ndarray
        The frequency response, as complex numbers.

    Examples
    --------

    """
    # causal poles/zeros
    bc = fil_dict['ba'][0]
    ac = fil_dict['ba'][1]

    # standard call to signal freqz
    W, H = sig.freqz(bc, ac, worN=worN, whole=wholeF, fs=fs)

    # test for NonCausal filter
    if ('rpk' in fil_dict):
        # Grab causal, anticausal ba's from dictionary
        ba = fil_dict['baA'][0]
        aa = fil_dict['baA'][1]
        ba = ba.conjugate()
        aa = aa.conjugate()

        # Evaluate transfer function of anticausal half on the same freq grid.
        # This is done by conjugating a and b prior to the call, and conjugating
        # h after the call.

        wa, ha = sig.freqz(ba, aa, worN=worN, whole=True, fs=fs)
        ha = ha.conjugate()

        # Total transfer function is the product of causal response and antiCausal
        # response
        H = H * ha

    return (W, H)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    pass
