# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

# Replace fb.fil[0]['some_key'] with fb_get('some_key') with the regular expression
#   fb.fil\[0\]\['([\s\S\r]*?)'\] -> fb_get('$1')

"""
Dynamic parameters and settings are exchanged via the dictionaries in this file.
Importing ``filterbroker.py`` runs the module once, defining all module variables
which have a global scope like class variables.

The entries in the global dict `fil[0]` contain the current filter design parameters, they
can be accessed and modified via the getter and setter `fb_get()` and `fb_set()`.

The entries in this file are only used as initial / default entries and to
demonstrate the structure of the global dicts and lists.
These initial values are also handy for module-level testing where some useful
setting of the variables is required.

Attributes
----------


Notes
-----

Alternative approaches for data persistence could be the packages `shelve` or pickleshare
More info on data persistence and storing / accessing global variables:

* http://stackoverflow.com/questions/13034496/using-global-variables-between-files-in-python
* http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
* http://pymotw.com/2/articles/data_persistence.html
* http://stackoverflow.com/questions/9058305/getting-attributes-of-a-class
* http://stackoverflow.com/questions/2447353/getattr-on-a-module
"""
import copy
import logging
from typing import Iterable

import numpy as np

logger = logging.getLogger(__name__)

base_dir = ""  #: Project base directory

# State of filter design: 'ok', 'changed', 'error', 'active'
design_filt_state = 'changed'

UNDO_LEN = 20  # depth of circular undo buffer
undo_step = 0  # number of undo steps, limited to UNDO_LEN
undo_ptr = 0  # pointer to current undo memory % UNDO_LEN

# -----------------------------------------------------------------------------
# Reference dictionary containing current filter type, specifications, design
# and some auxiliary information, the initial definition here is copied into
# fil[0] ... [9] which can be modified by input widgets and design routines
# -----------------------------------------------------------------------------
fil_ref = {
    '_id': [], # a list with the keyword 'pyfda' and the version, e.g. ['pyfda', 1]
    # amplitude specs (linear units)
    'A_PB': 0.2056717652757185,
    'A_PB2': 0.01,
    'A_SB': 0.001,
    'A_SB2': 0.0001,
    # frequency specs (normalized to F_S)
    'F_C': 0.1,
    'F_C2': 0.4,
    'F_N': 0.2,
    'F_N2': 0.4,
    'F_PB': 0.1,
    'F_PB2': 0.3,
    'F_SB': 0.2,
    'F_SB2': 0.4,
    'N': 4,  # filter order
    'T_S': 1.0,  # sample time
    # weights for pass- and stopbands
    'W_PB': 1.0,
    'W_PB2': 1.0,
    'W_SB': 1.0,
    'W_SB2': 1.0,
    #
    'amp_specs_unit': 'dB',
    # [b, a] coefficients:
    'ba': np.array([
        [
            0.005009993265049969,
            0.002969044992011087,
            0.007446465726559892,
            0.0029690449920110867,
            0.00500999326504997
        ],
        [
            1.0,
            -3.18194574253062,
            4.1391887955869535,
            -2.567503107299107,
            0.639724627220979
        ]
    ]),
    'creator': [
        'sos',
        'pyfda.filter_widgets.ellip'
    ],
    'f_S': 1.0,
    'f_S_prev': 1.0,  # previous sampling frequency
    # 'f_s_wav': 16000,  # sampling frequency for wav files
    'f_max': 1.0,
    'f_s_scale': 1.0,
    'fc': 'Ellip',  # filter class
    # Window parameters for frequency domain analysis of transient signals
    'tran_freq_win': {
        'id': 'rectangular',  # window id
        'disp_name': 'Rectangular',  # display name
        'par_val': [],    # list of window parameters
        'win_len': 32  # window length for window viewer
    },
    # parameter(s) of dynamically instantiated filter widgets
    'filter_widgets': {
        # Equiripple FIR filters
        'equiripple': {'grid_density': 16},
        # Windowed FIR filters
        'firwin':
            {'id': 'kaiser', # Window id
             'disp_name': 'Kaiser', # display name
             'par_val': [10],    # list of window parameters
             'win_len': 32  # window length for window viewer
            },
        # Moving Average filters
        'ma':
            {'delays': 5,
             'stages': 2,
             'normalize': True}
        },
    'fo': 'man',  # filter order, man or min
    'freqSpecsRange': [
        0,
        0.5
    ],
    'freqSpecsRangeType': 'half',
    'freq_locked': False, # don't update absolute frequencies when f_S is changed
    'freq_specs_sort': True,  # sort freq. specs in ascending order
    'freq_specs_unit': 'f_S',
    'ft': 'IIR',  # filter type
    'fx_base': 'dec', # global number format for fx display {'dec', 'hex', 'bin', 'oct', 'csd'}
    # string with current fixpoint module and class
    'fx_mod_class_name': 'pyfda.fixpoint_widgets.iir_df1.iir_df1_pyfixp_ui',
    # Settings for quantization subwidgets
    # ---------------------------------------------------------------------------
    #  Sub-dicts for quantization of
    #   'QI':input, 'QO': output, 'QCA': coeffs a, 'QCB': coeffs b, 'QACC': accumulator
    #    (more subwidgets can be added by fixpoint widget if needed)
    #  Keys:
    #   'N_over': number of overflows during last quantization process
    #   'WF': fractional bits, 'WI': integer bits
    #   'ovfl': overflow behaviour, 'quant': quantizer behaviour
    #   'w_a_m': word length automatic / manual calculation (not needed for 'QI', 'QO')
    'fxq':{
        # accumulator quantization
        'QACC': {
            'N_over': 0,
            'WF': 28,
            'WI': 3,
            'ovfl': 'wrap',
            'quant': 'floor',
            'w_a_m': 'a'
        },
        # 'a' coefficient quantization
        'QCA': {
            'N_over': 0,
            'WF': 12,
            'WI': 3,
            'ovfl': 'wrap',
            'quant': 'floor',
            'w_a_m': 'a'
        },
        # 'b' coefficient quantization
        'QCB': {
            'N_over': 0,
            'WF': 15,
            'WI': 0,
            'ovfl': 'wrap',
            'quant': 'floor',
            'w_a_m': 'a'
        },
        # input quantization
        'QI': {
            'N_over': 0,
            'WF': 15,
            'WI': 0,
            'ovfl': 'sat',
            'quant': 'round',
            'w_a_m': 'm'
        },
        # output quantization
        'QO': {
            'N_over': 0,
            'WF': 15,
            'WI': 0,
            'ovfl': 'wrap',
            'quant': 'floor',
            'w_a_m': 'm'
        }
    },
    'info': 'Ellip. LP (default)',
    'plt_fLabel': '$F = f\\, /\\, f_S = \\Omega \\, /\\,  2 \\mathrm{\\pi} \\; \\rightarrow$',
    'plt_fUnit': 'f_S',
    'plt_phiLabel': '$\\angle H(\\mathrm{e}^{\\mathrm{j} \\Omega})$ in rad $\\rightarrow $',
    'plt_phiUnit': 'rad',
    'plt_tLabel': '$n = t\\, /\\, T_S \\; \\rightarrow$',
    'plt_tUnit': 'T_S',

    'qfrmt': 'float64',  # global quantization format {'float64', 'float32', 'qint', 'qfrac'}
    'qfrmt_float_last': 'float64',  # last used float format
    'qfrmt_fx_last': 'qfrac',  # last used fixpoint format

    'rt': 'LP',  # filter response type
    # coefficients as second order sections
    'sos': np.array([
        [
            0.005009993265049969,
            0.005370024900373368,
            0.00500999326504997,
            1.0,
            -1.6295801387915057,
            0.7159415650206529
        ],
        [
            1.0,
            -0.47923815089965677,
            1.0,
            1.0,
            -1.5523656037391145,
            0.8935430745699543
        ]
    ]),
    'timestamp': 1717151329.1387591,  # time when filter was created
    # 'timestamp': time.time(),

    # causal zeros/poles/gain
    'zpk': np.array([
        [
            -0.5359313492330422+0.8442615642733304j,
            -0.5359313492330422-0.8442615642733304j,
            0.23961907544982838+0.9708669830005394j,
            0.23961907544982838-0.9708669830005394j
        ],
        [
            0.8147900693957527+0.22816377415075598j,
            0.8147900693957527-0.22816377415075598j,
            0.7761828018695571+0.539521392209686j,
            0.7761828018695571-0.539521392209686j
        ],
        [
            0.005009993265049969+0.0j,
            0.0+0.0j,
            0.0+0.0j,
            0.0+0.0j
        ]
    ]),
    # Tab-specific infos
    'tab_yn':{
        'display_index_k': False
    }
}

  # create empty lists with length 10 for multiple filter designs and undo memory
fil = [None] * 10
fil_undo = [None] * UNDO_LEN

# Copy fil_ref to fil[0] ... fil[9] to initialize all memories
for f in fil:
    f = copy.deepcopy(fil_ref)

# -------------------------
def restore_fil() -> int:
    """
    Restore current global dict `fil[0]` from undo memory `fil_undo`

    Returns
    -------
    int
        -1: undo buffer empty, nothing restored
         0: successful restore
    """
    global undo_step
    global undo_ptr

    # undo buffer is empty, don't copy anything
    if undo_step < 1:
        undo_step = 0
        return -1

    fil[0] = copy.deepcopy(fil_undo[undo_ptr])
    undo_step -= 1
    undo_ptr = (undo_ptr + UNDO_LEN - 1) % UNDO_LEN
    return 0

# -------------------------
def store_fil():
    """
    Store current global dict `fb.fil[0]` to undo memory `fil_undo`
    """
    global undo_step
    global undo_ptr

    # prevent buffer overflow
    undo_step += 1
    undo_step = min(undo_step, UNDO_LEN)
    # increase buffer pointer, allowing for circular wrap around
    undo_ptr = (undo_ptr + 1) % UNDO_LEN
    fil_undo[undo_ptr] = copy.deepcopy(fil[0])

# -------------------------
def _print_dict(key_list: list | tuple, top_dict_str = "fil[0]") -> str:
    """
    Print a (nested) dict, defined by the list or tuple of strings `key_list`. The last
    element of `key_list` is not included in the printed string, as it is the value to
    be set. This is used to issue meaningful error messages.

    Parameters
    ----------
    key_list : list or tuple
        List of keys to create the nested dictionary.
    top_dict_str : str
        The top-level dictionary string to use for printing.

    Returns
    -------
    str
        The string representation of the (nested) dictionary.

    Example
    -------
    key_list = ['fxq', 'QCA', 'WF'] returns "fil[0]['fxq']['QCA']['WF']"

    """
    if len(key_list) < 2:
        raise KeyError("Not enough arguments to define a dictionary!")

    dict_str = top_dict_str
    if len(key_list) < 3:  # only one level dictionary, key_list[-1] is already the key
        dict_str += '[' + key_list[-2] + ']'
    else:
        for k in key_list[:-1]:
            dict_str += '[' + k + ']'
    return dict_str


# -------------------------
def _traverse_dict(key_list: list | tuple, fil_dict: dict) -> dict:
    """
    Use the list or tuple of strings `key_list` to traverse the (nested) dict `fil_dict`
    and return the addressed subdictionary.

    In order to set the value of the returned dict, use the key for the lowest
    nesting level on the returned dict `d`, i.e. `d[key_list[-1]] = arg` .

    Parameters
    ----------
    key_list : list or tuple
        List of keys to traverse the nested dictionary.

    fil_dict : dict
        The dictionary to traverse.

    Returns
    -------
    dict
        A copy of the the traversed dictionary at the specified (usually lowest) level.

    Raises
    ------
    KeyError
        If a key does not exist in the dictionary or is not of type string
    TypeError
        If a key does not point to another dictionary
    """
    if not key_list:
        raise KeyError("List of keys was empty!")

    d = fil_dict
    for k in key_list[:-1]:  # Traverse all keys except the last one
        if k not in d or not isinstance(k, str):
            raise KeyError(f"Key '{k}' not found or is not a dictionary!")
        if not isinstance(d[k], dict):
            raise TypeError(f"Key '{k}' points to '{d[k]}' which is not a dict!")
        d = d[k]
    return d

# -------------------------
def get_fx()-> bool:
    """
    Check if a fixpoint mode is active globally by checking the current

    Returns
    -------
    bool
        True if qfrmt is one of the fixpoint formats 'qint' or 'qfrac'
        False if qfrmt is one of the floating point formats 'float32' or 'float64'

    Raises
    ------
    KeyError
        If qfrmt is not one of the expected values above
    """
    qfrmt = fb_get('qfrmt')
    if qfrmt not in ['qint', 'qfrac', 'float32', 'float64']:
        raise KeyError("Invalid value for qfrmt!")

    return qfrmt in ['qint', 'qfrac']

# -------------------------
def set_fx(fx: bool)-> None:
    """
    Set fixpoint mode by restoring previous fixpoint format
    when `fx == True`, otherwise restore previous float format.
    """
    if fx:
        fb_set('qfrmt', fb_get('qfrmt_fx_last'))
    else:
        fb_set('qfrmt', fb_get('qfrmt_float_last'))

# -------------------------
def fb_get(*key_list: list | tuple, fil_dict: dict = fil[0], verbose: bool = True)\
    -> str | int | float | Iterable | None:
    """
    Get the value of a key in the global dict `fil[0]`. Multiple arguments
    access nested dicts:
    fb_get('qfrmt') == fb.fil[0]['qfrmt']
    fb_get('ba', 0) == fb.fil[0]['ba'][0]

    Parameters
    ----------
    key_list : list or tuple
        List of tuple of keys for traversing the nested dictionary.
    fil_dict : dict
        The dictionary to traverse, the default is the global `fil[0]`.
    verbose : bool
        Whether to log errors and warnings, default is True. Setting this to False
        can be used to detect silently whether a key exists in the dictionary

    Returns
    -------
    str | int | float | Iterable | None
        The value of the specified key in the dictionary, or None if the key
        does not exist.
    """
    if len(key_list) == 0:
        # called without arguments, return a copy of the whole dict
        return copy.deepcopy(fil_dict)

    ret = fil_dict
    try:
        for key in key_list:
            ret = ret[key]
            # ret = fil_dict[key_list[0]][key_list[1]][key_list[2]] ...
    except (KeyError, IndexError, TypeError):
        # create a meaningful error message with a string of the failed dict
        if verbose:
            logger.error("Dict '%s' does not exist!", _print_dict(key_list))
        return None

    if ret is None and verbose:
        logger.warning("Key '%s' not found in filter dict!", key_list[-1])
    return ret

# -------------------------
def fb_set(*key_list: list | tuple, backup: bool = True, new_key: bool = False,
           fil_dict: dict = fil[0]) -> int:
    """
    Use the items of `key_list` to access a nested dict `fil_dict`
    (default: `fil[0]`) and write the last item in `key_list` to the dict.

    In order to set the value of the returned nested dict, use the key for the lowest
    nesting level on the returned dict `d`, i.e. `d[key_list[-1]] = arg` .

    Parameters
    ----------
    key_list : list or tuple
        List or tuple of keys for traversing the (nested) dictionary, the last element
        is the value to be set.
    backup : bool
        Whether the previous state of the filter dict should be backed up
    new_key : bool
        Whether a new key:value pair should be added to the dictionary
    fil_dict : dict
        The dictionary to traverse.

    Returns
    -------
    int
        The error code; 0 for successful operation, -1 for an error

    Raises
    ------
    KeyError
        If a key does not exist in the dictionary or the tuple of keys is empty

    TypeError
        If `key_list` is not of type List or Tuple or if it has less than two items

    TODO: Dict entries need to be protected from accidental overwriting by
    the user. This will be done by prepending the keys with an underscore
    (e.g. `_f_S`) once all direct accesses have been removed.
    """
    # if not key_list:
    #     raise KeyError("Key_list is empty!")

    if not isinstance(key_list, (tuple, list)):
        raise TypeError(
            "A tuple or list of keys is needed for traversing the filter dict, not a '%s'!",
            type(key_list).__name__)

    if len(key_list) < 2:
        raise KeyError("Not enough arguments for setting a dictionary value!")

    set_val = key_list[-1]  # last element is the value to be set
    set_key = key_list[-2]  # second last element is the key for setting

    try:
        if backup:
            store_fil()  # backup old setting

        # traverse nested dict 'fil_dict' using tuple of keys and access subdictionary
        d = _traverse_dict(key_list[:-1], fil_dict)
        # Test accessing the dictionary and whether the accessed item is a dict.
        # This could be dangerous because the keys in this sub-dictionary could be altered!
        if new_key:
            if set_key in d:
                logger.warning("Overwriting existing key '%s' in dictionary \n"
                               "\twith '%s'!", d[set_key], set_key)
            d[set_key] = set_val  # set new key:value pair
            return 0

        if isinstance(d[set_key], dict):
            # keys1 = d[set_key].keys()
            logger.warning(
                "Danger! Overwriting the dict '%s'\n\t%s with \n\t%s",
                _print_dict(key_list), d[set_key], set_val)

        if set_key =='qfrmt':
            if len(key_list) > 2:
                raise KeyError("Too many arguments for setting 'qfrmt'!")
            # store current fixpoint / float format
            if get_fx():  # fixpoint mode, store old fixpoint format
                fil_dict['qfrmt_fx_last'] = fil_dict['qfrmt']
            else:  # float mode, store current float format
                fil[0]['qfrmt_float_last'] = fil_dict['qfrmt']
            # and set new format
            fil_dict['qfrmt'] = set_val
            return 0

        if type(set_val) is not type(d[set_key]):
            types = {type(set_val).__name__, type(d[set_key]).__name__}
            if types.issubset({'float', 'float64'}):
                pass
            elif types.issubset({'list', 'tuple', 'ndarray'}):
                logger.warning("Possible type mismatch: Setting\n\t'%s' of type '%s' with value "
                                "of similar type '%s'", _print_dict(key_list),
                                type(d[set_key]).__name__, type(set_val).__name__)
            else:
                raise ValueError
        d[set_key] = set_val  # update key with new value

    except KeyError:
        # create a meaningful error message with a string of the name of the failed dict
        logger.error("No key %s in dict '%s'!", set_key, _print_dict(key_list))
        if backup:
            restore_fil()
        return -1
    except ValueError:
        logger.error("Type mismatch: Refusing to set\n\t'dict[%s]' of type '%s' "
                     "with value of type '%s'",
                     set_key, type(d[set_key]).__name__, type(set_val).__name__)
        if backup:
            restore_fil()
        return -1

    return 0

# Comparing nested dicts
# https://stackoverflow.com/questions/27265939/comparing-python-dictionaries-and-nested-dictionaries
