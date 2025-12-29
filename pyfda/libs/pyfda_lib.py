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
import os
import re
import sys
import struct
import traceback

from docutils import __version__ as V_DOC
# from markdown import __version__ as V_MD
from matplotlib import __version__ as V_MPL
import numpy as np
from numpy import pi, log10, sin, cos
import numexpr
import markdown
from mplcursors import __version__ as V_CUR
from scipy import __version__ as V_SCI

import pyfda.filterbroker as fb
import pyfda.libs.pyfda_dirs as dirs

from .compat import QT_VERSION_STR as V_QT
from .compat import PYQT_VERSION_STR as V_PYQT

V_NUM_MKL = numexpr.get_vml_version()
if V_NUM_MKL:
    MKL = f" (mkl: {V_NUM_MKL:s})"
else:
    MKL = " (no mkl)"

__all__ = ['cmp_version', 'mod_version',
           'set_dict_defaults', 'clean_ascii', 'safe_eval',
           'dB', 'lin2unit', 'unit2lin',
           'cround', 'H_mag', 'cmplx_sort', 'unique_roots',
           'expand_lim', 'format_ticks',
           'round_odd', 'round_even', 'ceil_odd', 'floor_odd', 'ceil_even', 'floor_even',
           'to_html']

logger = logging.getLogger(__name__)

PY32_64 = struct.calcsize("P") * 8  # yields 32 or 64, depending on 32 or 64 bit Python

V_PY = ".".join(map(str, sys.version_info[:3])) + " (" + str(PY32_64) + " Bit)"

# ================ Required Modules ============================
MODULES = {'python':       {'V_PY': V_PY},
           'matplotlib':   {'V_MPL': V_MPL},
           'Qt5':          {'V_QT': V_QT},
           'pyqt':         {'V_PYQT': V_PYQT},
           'numpy':        {'V_NP': np.__version__},
           'numexpr':      {'V_NUM': numexpr.__version__},
           'scipy':        {'V_SCI': V_SCI + MKL},
           'markdown':     {'V_MD': markdown.__version__},
           'docutils':     {'V_DOC': V_DOC},
           'mplcursors':   {'V_CUR': V_CUR},
           }

# ================ Optional Modules ============================
MODULES.update({'yosys': {'V_YO': dirs.YOSYS_VER}})

# try:
#     from xlwt import __version__ as V_XLWT
#     if V_XLWT == '':
#         V_XLWT = 'unknown'
#     MODULES.update({'xlwt': {'V_XLWT': V_XLWT}})
# except ImportError:
#     MODULES.update({'xlwt': {'V_XLWT': 'n.a.'}})

# try:
#     from xlsxwriter import __version__ as V_XLSX
#     if V_XLSX == '':
#         V_XLSX = 'unknown'
#     MODULES.update({'xlsx': {'V_XLSX': V_XLSX}})
# except ImportError:
#     MODULES.update({'xlsx': {'V_XLSX': 'n.a.'}})

try:
    from amaranth import __version__ as V_AM
    if V_AM == '':
        V_AM = 'unknown'
    MODULES.update({'amaranth': {'V_AM': V_AM}})
except ImportError:
    MODULES.update({'amaranth': {'V_AM': 'n.a.'}})


# Remove module names as keys and return a dict with items like
#  {'V_MPL':'3.3.1', ...}
MOD_VERSIONS = {}
for k in MODULES.keys():
    MOD_VERSIONS.update(MODULES[k])

CRLF = os.linesep  # Windows: "\r\n", Mac OS: "\r", *nix: "\n"


# ------------------------------------------------------------------------------
def cmp_version(mod: str, version: str) -> int:
    """
    Compare version number of installed module `mod` against value `version` (str) and
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

         :-3: version number could not be determined

         :-2: module is not installed

         :-1: version of installed module is lower than the specified version

         :0: version of installed module is equal to specied version

         :1: version of installed module is higher than specified version

    """
    def versiontuple(v):
        """Convert strings like "1.2.3" to tuples like (1,2,3) for comparisons."""
        return tuple(map(int, (v.split("."))))

    try:  # empty string / module not in list / returned '' as version number
        if not mod or mod not in MODULES\
                or list(MODULES[mod].values())[0] in {'', 'n.a.'}:
            return -2

        if dirs.PYINSTALLER:
            # pyfda is running from an self-extracting archive, version has to be ok
            return 1

        # get dict value without knowing the key:
        inst_ver = list(MODULES[mod].values())[0]
        if inst_ver == 'unknown':
            logger.warning(
                "Version number of module '%s' could not be determined.", mod)
            return -3

        if versiontuple(inst_ver) > versiontuple(version):
            return 1

        if versiontuple(inst_ver) == versiontuple(version):
            return 0

        return -1

    except (TypeError, KeyError) as e:
        logger.warning("Version number of '%s' could not be determined:\n%s", mod, e)
        return -1


# ------------------------------------------------------------------------------
def mod_version(mod: str = "") -> str:
    """
    Return the version of the module 'mod'. If the module is not found, return
    empty string. When no module is specified, return a string with all modules and
    their versions sorted alphabetically.
    """
    if mod:
        if mod in MODULES:
            return list(MODULES[mod].values())[0]

        return ""

    v_md = ""
    # open and read `module_versions.md` with module version infos
    with open(os.path.join(dirs.INSTALL_DIR, "module_versions.md"), 'r') as f:
        # return a list, split at linebreaks while keeping linebreaks
        v = f.read().splitlines(True)

    for k in v:
        try:
            # evaluate {V_...} from MOD_VERSIONS entries:
            v_md += k.format(**MOD_VERSIONS)
        except (KeyError) as e:  # encountered undefined {V_...}
            logger.warning("KeyError: %s", e)  # simply drop the line

    # pyinstaller needs explicit definition of extensions path
    return markdown.markdown(v_md, output_format='html5',
                             extensions=['markdown.extensions.tables'])

# ==============================================================================
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

        return np.nan_to_num(np.array(arrs, dtype=dtype))  # convert list of arrays to two-dimensional array

    logger.error("Unsupported type '{type(iterable)}' of %s for conversion to ndarray.", iterable)
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
            logger.warning("Deleted key '%s' (not part of default dict).", k)
    if d == {}:
        d.update(default_dict)
    else:
        for k, v in default_dict.items():
            if k not in d:
                d[k] = v


# -------------------------------------------------------------------------------
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
        `key_errs[0]` contains all keys copied from `ref_dict` to `new_dict`
            (i.e. missing in `new_dict`).
        `key_errs[1]` contains all discarded keys from `new_dict`
            (i.e. missing in `ref_dict`).
    """
    key_errs = [[], []]
    old_path = path

    for k in ref_dict:
        path = old_path + f"'{k}'"
        if k not in new_dict:
            key_errs[0].append(path)
            new_dict.update({k: ref_dict[k]})
        else:
            if isinstance(ref_dict[k], dict) and isinstance(new_dict[k], dict):
                key_errs.append(compare_dictionaries(ref_dict[k], new_dict[k], path))

    # emulate slightly inefficient Python 2 way of copying the dict keys to a list
    # to avoid runtime error "dictionary changed size during iteration" due to new_dict.pop(k)
    for k in list(new_dict):
        path = old_path + f"'{k}'"
        if k not in ref_dict:
            key_errs[1].append(path)
            new_dict.pop(k)

    return key_errs


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
        logger.info("Data: %s [%s], ndim=%d", type(d).__name__, type(d[0]).__name__, np.ndim(d))
    if isinstance(d, dict):
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
            logger.warning("pprint_log(): Could not transform data to array:\n%s", e)
            return ""

    if type(d) in {list, np.ndarray, tuple}:
        if np.ndim(d) == 0: # iterable with a single element
            s = str(d) + f' of type: {type(d).__name__}'
        elif np.ndim(d) == 1:
            s = cr + tab + str(d[: min(N-1, len(d))])
            if len(d) > N-1:
                s += ' ...'
            s += (cr + tab + f'Type: {type(d).__name__} of {type(d[0]).__name__} '
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
            logger.warning("pprint_log(): Object with ndim = %s cannot be processed.", np.ndim(d))
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
              ):  # -> complex|float|int: only works with py3.10 upawards
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
def debug_exception(msg: str = "") -> None:
    """
    React to an exception depending on the debug level. When debug level is high,
    use the traceback module for full traceback. Otherwise, keep quiet.
    """
    if fb.conf_settings['EXCEPTION_LEVEL'] >= 1:
        logger.info("debug_exception(): Level %s.", fb.conf_settings['EXCEPTION_LEVEL'])
        # get current stack trace as a list of strings. Each string consists of
        #   "  File '...'\n, line ..., in ...\n"
        err_list = traceback.format_stack()
        err_str = msg + "\n\t"
        # skip the first entries and the last two (it's this function and the caller)
        for s in err_list[4:-2]:
            err_str += s.strip(' \t\n').replace("\n", "\n\t\t") + "\n\t" # indent traceback lines
        logger.error(err_str)
    if fb.conf_settings['EXCEPTION_LEVEL'] >= 2:
        raise SystemExit("from debug_exception!")


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

    return 20 * np.log10(lin)


# ------------------------------------------------------------------------------
def lin2unit(lin_value: float, filt_type: str, amp_label: str,
             unit: str = 'dB') -> float:
    r"""
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
    r"""
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
            "Amplitude spec for %s is %s using %.4g %s instead.", amp_label, msg,
            lin2unit(lin_value, filt_type=filt_type, amp_label=amp_label, unit=unit), unit)
    return lin_value


# ------------------------------------------------------------------------------
def cround(x, n_dig: int = 0) -> complex | float:
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
def sawtooth_bl(t: np.ndarray) -> np.ndarray:
    """
    Bandlimited sawtooth function as a direct replacement for `scipy.signal.sawtooth`.
    It is calculated by Fourier synthesis, i.e. by summing up all sine wave components
    up to the Nyquist frequency.

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
def triang_bl(t: np.ndarray) -> np.ndarray:
    """
    Bandlimited triangle function as a direct replacement for `scipy.signal.sawtooth(width=0.5)`.
    It is calculated by Fourier synthesis, i.e. by summing up all sine wave components up to
    the Nyquist frequency.

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
def rect_bl(t: np.ndarray, duty: float | int = 0.5) -> np.ndarray:
    """
    Bandlimited rectangular function as a direct replacement for `scipy.signal.square`.
    It is derived from sawtooth_bl() which is calculated by Fourier synthesis, i.e.
    by summing up all sine wave components up to the Nyquist frequency.

    By Endolith, https://gist.github.com/endolith/407991
    """
    return sawtooth_bl(t - duty*2*pi) - sawtooth_bl(t) + 2*duty-1


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
    r"""
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

    # handle scalars
    tol = abs(tol)
    p = np.atleast_1d(p)  # convert p to at least 1D array
    if len(p) == 0:
        return pout, mult

    if len(p) == 1:
        pout = p
        mult = [1]
        return pout, mult

    # handle lists / arrays
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
if __name__ == '__main__':
    pass
