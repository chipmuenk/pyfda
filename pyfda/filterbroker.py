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

from pyfda.libs.frozendict import freeze_hierarchical

logger = logging.getLogger(__name__)

clipboard = None
""" Handle to central clipboard instance """

base_dir = ""  #: Project base directory

# State of filter design: 'ok', 'changed', 'error', 'active'
design_filt_state = 'changed'

UNDO_LEN = 20  # depth of circular undo buffer
undo_step = 0  # number of undo steps, limited to UNDO_LEN
undo_ptr = 0  # pointer to current undo memory % UNDO_LEN

#==============================================================================

# Dictionary describing the available combinations of response types (rt),
# filter types (ft), filter class (fc) and filter order (fo). This dictionary
# is also overwritten during initialization:
fil_tree = freeze_hierarchical({
    'LP': {
        'FIR': {
            'Equiripple': {
                'man':{'fo':     ('a', 'N'),
                       'fspecs': ('a', 'F_C'),
                       'wspecs': ('a', 'W_PB', 'W_SB'),
                       'tspecs': ('u', {'frq': ('u', 'F_PB', 'F_SB'),
                                        'amp': ('u', 'A_PB', 'A_SB')}),
                       'msg':    ('a',
                                  "Enter desired filter order <b><i>N</i></b>, corner "
        "frequencies of pass and stop band(s), <b><i>F<sub>PB</sub></i></b>"
        "&nbsp; and <b><i>F<sub>SB</sub></i></b>, and a weight "
        "value <b><i>W</i></b>&nbsp; for each band."
                                 )
                        },
                'min':{'fo':     ('d', 'N'),
                       'fspecs': ('d', 'F_C'),
                       'wspecs': ('d', 'W_PB', 'W_SB'),
                       'tspecs': ('a', {'frq': ('a', 'F_PB', 'F_SB'),
                                        'amp': ('a', 'A_PB', 'A_SB')}),
                       'msg':    ('a',
            "Enter maximum pass band ripple <b><i>A<sub>PB</sub></i></b>, "
            "minimum stop band attenuation <b><i>A<sub>SB</sub> </i></b>"
            "&nbsp;and the corresponding corner frequencies of pass and "
            "stop band(s), <b><i>F<sub>PB</sub></i></b>&nbsp; and "
            "<b><i>F<sub>SB</sub></i></b> ."
                                    )
                       },
                }
            },
        'IIR': {
            'Cheby1': {
                'man':{'fo':     ('a', 'N'),
                       'fspecs': ('a', 'F_C'),
                       'tspecs': ('u', {'frq': ('u', 'F_PB', 'F_SB'),
                                        'amp': ('u', 'A_PB', 'A_SB')})
                       },
                'min':{'fo':     ('d', 'N'),
                       'fspecs': ('d', 'F_C'),
                       'tspecs': ('a', {'frq': ('a', 'F_PB', 'F_SB'),
                                        'amp': ('a', 'A_PB', 'A_SB')})
                       }
                }
            }
        },
    'HP': {
        'FIR': {
            'Equiripple': {
                'man':{'fo':     ('a', 'N'),
                       'fspecs': ('a', 'F_C'),
                       'wspecs': ('a', 'W_SB', 'W_PB'),
                       'tspecs': ('u', {'frq': ('u', 'F_SB', 'F_PB'),
                                        'amp': ('u', 'A_SB', 'A_PB')})
                      },
                'min':{'fo':     ('d', 'N'),
                       'wspecs': ('d', 'W_SB', 'W_PB'),
                       'fspecs': ('d', 'F_C'),
                       'tspecs': ('a', {'frq': ('a', 'F_SB', 'F_PB'),
                                        'amp': ('a', 'A_SB', 'A_PB')})
                       }
                    }
              },
        'IIR': {
            'Cheby1': {
                'man':{'fo':     ('a', 'N'),
                       'fspecs': ('a', 'F_C'),
                       'tspecs': ('u', {'frq': ('u', 'F_SB', 'F_PB'),
                                        'amp': ('u', 'A_SB', 'A_PB')})
                       },
                'min':{'fo':     ('d', 'N'),
                       'fspecs': ('d', 'F_C'),
                       'tspecs': ('a', {'frq': ('a', 'F_SB', 'F_PB'),
                                        'amp': ('a', 'A_SB', 'A_PB')})
                       }
                    }
                }
        },
    'BP': {
        'FIR': {
            'Equiripple': {
                'man':{'fo':     ('a', 'N'),
                       'wspecs': ('a', 'W_SB', 'W_PB', 'W_SB2'),
                       'fspecs': ('a', 'F_C', 'F_C2'),
                       'tspecs': ('u', {'frq': ('u', 'F_SB', 'F_PB', 'F_PB2', 'F_SB2'),
                                        'amp': ('u', 'A_SB', 'A_PB', 'A_SB2')})
                       },
                'min':{'fo':     ('d', 'N'),
                       'fspecs': ('d', 'F_C', 'F_C2'),
                       'wspecs': ('d', 'W_SB', 'W_PB', 'W_SB2'),
                       'tspecs': ('a', {'frq': ('a', 'F_SB', 'F_PB', 'F_PB2', 'F_SB2'),
                                        'amp': ('a', 'A_SB', 'A_PB', 'A_SB2')})
                       }
                    }
                }
            },
    'BS': {
        'FIR': {
            'Equiripple': {
                'man':{'fo':     ('a', 'N'),
                       'wspecs': ('a', 'W_PB', 'W_SB', 'W_PB2'),
                       'fspecs': ('a', 'F_C', 'F_C2'),
                       'tspecs': ('u', {'frq': ('u', 'F_PB', 'F_SB', 'F_SB2', 'F_PB2'),
                                        'amp': ('u', 'A_PB', 'A_SB', 'A_PB2')})
                       },
                'min':{'fo':     ('d', 'N'),
                       'wspecs': ('d', 'W_PB', 'W_SB', 'W_PB2'),
                       'fspecs': ('d', 'F_C', 'F_C2'),
                       'tspecs': ('a', {'frq': ('a', 'F_PB', 'F_SB', 'F_SB2', 'F_PB2'),
                                        'amp': ('a', 'A_PB', 'A_SB', 'A_PB2')})
                       }
                          }
                }
        }
    })

# -----------------------------------------------------------------------------
# Dictionary containing configuration settings for pyfda which can be modified
# in the [Config Settings] of `pyfda.conf` and from the UI
# ------------------------------------------------------------------------------

conf_settings = {
    'EXCEPTION_LEVEL': 0,  # 0: quiet, 1: print error stack, 2: end pyfda
    'THEME': 'light',
    'N_FFT':  8192  # number of FFT points for most widgets except y[n]
    }

# -----------------------------------------------------------------------------
# Reference dictionary containing current filter type, specifications, design
# and some auxiliary information, the initial definition here is copied into
# fil[0] ... [9] which can be modified by input widgets and design routines
# ------------------------------------------------------------------------------
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
    'W_PB': 1,
    'W_PB2': 1,
    'W_SB': 1,
    'W_SB2': 1,
    #
    'amp_specs_unit': 'dB',
    # [b, a] coefficients:
    'ba': [
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
    ],
    'creator': [
        'sos',
        'pyfda.filter_widgets.ellip'
    ],
    'f_S': 1.0,
    'f_S_prev': 1,  # previous sampling frequency
    # 'f_s_wav': 16000,  # sampling frequency for wav files
    'f_max': 1.0,
    'f_s_scale': 1,
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
    'sos': [
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
    ],
    'timestamp': 1717151329.1387591,  # time when filter was created
    # 'timestamp': time.time(),

    # causal zeros/poles/gain
    'zpk': [
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
    ],
    # Tab-specific infos
    'tab_yn':{
        'display_index_k': False
    }
}

  # create empty lists with length 10 for multiple filter designs and undo functions
fil = [None] * 10
fil_undo = [None] * UNDO_LEN

# https://nedbatchelder.com/text/names.html :
# define fil[0] as a dict with "built-in" default. The argument defines the default
# factory that is called when a key is missing. Here, lambda simply returns a float.
# When e.g. list is given as the default_factory, an empty list is returned.
# fil[0] = defaultdict(lambda: 0.123)
fil[0] = {}

# Copy fil_ref to fil[0] ... fil[9] to initialize all memories
for i in range(len(fil)):
    fil[i] = copy.deepcopy(fil_ref)

# -------------------------
def restore_fil() -> int:
    """
    Restore current global dict `fb.fil[0]` from undo memory `fil_undo`

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
def traverse_dict(key_list: list | tuple, fil_dict: dict) -> dict:
    """
    Use the list or tuple of strings `key_list` to traverse the (nested) dict `fil_dict`
    and return the addressed subdictionary.

    In order to set the value of the returned dict, use the key for the lowest
    nesting level on the returned dict `d`, i.e. `d[keys_tuple[-1]] = arg` .

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
        If a key does not exist in the dictionary or does not point to another dictionary
    """
    if not key_list:
        raise KeyError("List of keys was empty!")

    d = fil_dict
    for k in key_list[:-1]:  # Traverse all keys except the last one
        if k not in d or not isinstance(d[k], dict):
            raise KeyError(f"Key '{k}' not found or is not a dictionary!")
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
def fb_get(*keys_tuple, fil_dict=fil[0], verbose=True) -> str | int | float | Iterable | None:
    """
    Get the value of a key in the global dict `fil[0]`. Multiple arguments
    access nested dicts:
    fb_get('qfrmt') == fb.fil[0]['qfrmt']
    fb_get('ba', 0) == fb.fil[0]['ba'][0]

    Parameters
    ----------
    keys_tuple : tuple
        Tuple of keys for traversing the nested dictionary.
    fil_dict : dict
        The dictionary to traverse, the default is the global `fil[0]`.
    verbose : bool
        Whether to log errors and warnings, default is True. Setting this to False
        can be used to detect silently whether a key exists in the dictionary

    TODO: Keys need to be protected from accidental overwriting by
    the user. This will be done by prepending the keys with an underscore
    (e.g. `_f_S`) once all direct accesses have been removed.
    """
    if len(keys_tuple) == 0:
        # called without arguments, return a copy of the whole dict
        return copy.deepcopy(fil_dict)

    ret = fil_dict
    try:
        for key in keys_tuple:
            ret = ret[key]
            # ret = fil_dict[keys_tuple[0]][keys_tuple[1]][keys_tuple[2]] ...
    except (KeyError, IndexError, TypeError):
        # create a meaningful error message with a string of the failed dict
        if verbose:
            dict_str = fil_dict
            if len(keys_tuple) < 3:  # only one level dictionary, keys_tuple[-1] is already the key
                logger.warning(keys_tuple)
                dict_str += '[' + keys_tuple[-2] + ']'
            else:
                for k in keys_tuple[:-1]:
                    dict_str += '[' + k + ']'
            logger.error("Dict '%s' does not exist!", dict_str)
        return None

    if ret is None and verbose:
        logger.warning("Key '%s' not found in filter dict!", keys_tuple[-1])
    return ret

# -------------------------
def fb_set(*keys_tuple, backup: bool = True, update: bool = False, fil_dict: dict = fil[0]) -> None:
    """
    Use the items of `keys_tuple` to access a nested dict `fil_dict`
    (default: `fil[0]`) and write the last item in `keys_tuple` to the dict.

    In order to set the value of the returned nested dict, use the key for the lowest
    nesting level on the returned dict `d`, i.e. `d[keys_tuple[-1]] = arg` .

    Parameters
    ----------
    keys_tuple : tuple
        Tuple of keys for traversing the nested dictionary, the last element is the value
        to be set.
    backup : bool
        Whether the previous state of the filter dict should be backed up
    update : bool
        Whether the dictionary should be updated with the new value or set
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
        If `keys_tuple` is not of type Tuple or if the tuple contains less than two items
    """

    # TODO: Check whether nested dicts can be partially overwritten

    if not keys_tuple:
        raise KeyError("Tuple of keys is empty!")
    if not isinstance(keys_tuple, tuple):
        raise TypeError("Keys container needs to be a Tuple, not a '%s'!", type(keys_tuple))
        # logger.error("Wrong type of arguments collection '%s'", type(keys_tuple))
        # return -1
    if len(keys_tuple) < 2:
        raise TypeError("Not enough arguments for setting a dictionary value!")

    val = keys_tuple[-1]  # last element is not a key but the value to be set

    try:
        d = key_list_to_dict(keys_tuple[:-1], fil_dict)  # create nested dict from the other arguments
        _ =  d[keys_tuple[-2]]  # test accessing the dictionary
        if backup:
            store_fil()  # backup old setting

        if keys_tuple[-2] =='qfrmt' and len(keys_tuple) == 2:
            # remember current fixpoint / float format
            if get_fx():  # store old fixpoint format
                fil_dict['qfrmt_fx_last'] = fil_dict['qfrmt']
            else:  # store old float format
                fil[0]['qfrmt_float_last'] = fil_dict['qfrmt']
            # and set new format
            fil_dict['qfrmt'] = val
        elif not update:
            d[keys_tuple[-2]] = val  # set new value
        else:
            d[keys_tuple[-2]].update(val)  # update dict with new value

    except KeyError:
        # create a meaningful error message with a string of the failed dict
        dict_str = 'fb.fil[0]'
        if len(keys_tuple) < 3:  # only one level dictionary, keys_tuple[-1] is already the key
            dict_str += '[' + keys_tuple[-2] + ']'
        else:
            for k in keys_tuple[:-1]:
                dict_str += '[' + k + ']'
        logger.error("Dict '%s' does not exist!", dict_str)
        return -1

    return 0

# Comparing nested dicts
# https://stackoverflow.com/questions/27265939/comparing-python-dictionaries-and-nested-dictionaries
