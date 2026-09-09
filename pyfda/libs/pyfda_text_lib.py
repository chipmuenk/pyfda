# -*- coding: utf-8 -*-
#
# This file is part of the pyfda project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyfda Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Library with various functions to handle text / strings / dicts, 
e.g. for logging, HTML formatting, ANSI colors etc.
"""
# pylint: disable=too-few-public-methods

import logging
import os
import re
import sys
import struct

from docutils import __version__ as V_DOC
from matplotlib import __version__ as V_MPL
import numpy as np
import numexpr
import markdown
from mplcursors import __version__ as V_CUR
from scipy import __version__ as V_SCI

from pyfda.libs.frozendict import FrozenDict
import pyfda.libs.pyfda_dirs as dirs

from .compat import QT_VERSION_STR as V_QT
from .compat import PYQT_VERSION_STR as V_PYQT

V_NUM_MKL = numexpr.get_vml_version()
if V_NUM_MKL:
    MKL = f" (mkl: {V_NUM_MKL:s})"
else:
    MKL = " (no mkl)"

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

# ===============================================================================
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
    # -----
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
    # open and read `module_infos.md` with module infos
    with open(os.path.join(dirs.INSTALL_DIR, "module_infos.md"), 'r',
              encoding="utf-8") as f:
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

###############################################################################
# Text related functions ######################################################
###############################################################################

def replace_mult(source: str|dict, repl_dict: dict) -> str|dict:
    """
    Replace all occurrences of the keys of `repl_dict` with their corresponding values
    in the string `string`.

    e.g.
    repl_dict = {
        'is': 'was',
        'does': 'did',
    '!': '?'
    }
    """
    # match every string to be replaced
    if isinstance(source, str):
        finder = re.compile("|".join(re.escape(k) for k in repl_dict.keys()))
        result = []
        pos = 0
        while True:
            match = finder.search(source, pos)
            if match:
                # cut off the part up until match
                result.append(source[pos : match.start()])
                # cut off the matched part and replace it in place
                result.append(repl_dict[source[match.start() : match.end()]])
                pos = match.end()
            else:
                # the rest after the last match
                result.append(source[pos:])
                break
        return "".join(result)

    if isinstance(source, dict):
        # Replace words only in string items of the dict
        for k, v in source.items():
            for old_str, new_val in repl_dict.items():
                if v == old_str:
                    source[k] = new_val
        return source

    logger.warning("replace_mult(): Unsupported type '%s' of %s for replacement.",
                    type(source).__name__, source)
    return source

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
        logger.warning("Dict %s was empty", d)
        d.update(default_dict)
    else:
        for k, v in default_dict.items():
            if k not in d:
                logger.warning("Key %s in dict %s was empty", k, d)
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
    if isinstance(d, (dict, FrozenDict)):
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
            s += f'Type: {type(d).__name__}'
    return s

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

        >>> to_html("f_sb", frmt='bi')
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

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # ==============================================================================
    logger.info(mod_version())
