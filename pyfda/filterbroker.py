# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Dynamic parameters and settings are exchanged via the dictionaries in this file.
Importing ``filterbroker.py`` runs the module once, defining all module variables
which have a global scope like class variables and can be imported like

>>> import filterbroker as fb
>>> myfil = fb.fil[0]

The entries in this file are only used as initial / default entries and to
demonstrate the structure of the global dicts and lists.
These initial values are also handy for module-level testing where some useful
settings of the variables is required.

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
import logging

import copy
# import time
from collections import OrderedDict
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
# -----------------------------------------------------------------------------
# Dicts with class names found in the main configuration file,
# parsed in `tree_builder.build_class_dict()`. Those initial definitions
# are only meant as examples and for module test, they are overwritten during
# the initialization.
#------------------------------------------------------------------------------

plot_classes = OrderedDict(
    [('Plot_Hf', {'name': '|H(f)|', 'mod': 'pyfda.plot_widgets.plot_hf'}),
     ('Plot_Phi', {'name': 'φ(f)', 'mod': 'pyfda.plot_widgets.plot_phi'}),
     ('Plot_tau_g', {'name': 'tau_g', 'mod': 'pyfda.plot_widgets.plot_tau_g'}),
     ('Plot_PZ', {'name': 'P / Z', 'mod': 'pyfda.plot_widgets.plot_pz'}),
     ('Plot_Impz', {'name': 'h[n]', 'mod': 'pyfda.plot_widgets.plot_impz'}),
     ('Plot_3D', {'name': '3D', 'mod': 'pyfda.plot_widgets.plot_3d'})
     ])
input_classes = OrderedDict(
    [('Input_Specs', {'name': 'Specs', 'mod': 'pyfda.input_widgets.input_specs'}),
     ('Input_Coeffs', {'name': 'b,a', 'mod': 'pyfda.input_widgets.input_coeffs'}),
     ('Input_PZ', {'name': 'P/Z', 'mod': 'pyfda.input_widgets.input_pz'}),
     ('Input_Info', {'name': 'Info', 'mod': 'pyfda.input_widgets.input_info'}),
     ('Input_Files', {'name': 'Files', 'mod': 'pyfda.input_widgets.input_files'}),
     ('Input_Fixpoint_Specs', {'name': 'Fixpoint',
                               'mod': 'pyfda.input_widgets.input_fixpoint_specs'})
     ])

fixpoint_classes = OrderedDict(
    [('FIR_DF_wdg', {'name': 'FIR_DF',
                     'mod': 'pyfda.fixpoint_widgets.fir_df', 'opt': ['Equiripple', 'Firwin']}),
     ('Delay_wdg', {'name': 'Delay',
                    'mod': 'pyfda.fixpoint_widgets.delay1', 'opt': ['Equiripple']})
     ])

filter_classes = OrderedDict(
    [# IIR
     ('Bessel', {'name': 'Bessel', 'mod': 'pyfda.filter_widgets.bessel'}),
     ('Butter', {'name': 'Butterworth', 'mod': 'pyfda.filter_widgets.butter'}),
     ('Cheby1', {'name': 'Chebyshev 1', 'mod': 'pyfda.filter_widgets.cheby1'}),
     ('Cheby2', {'name': 'Chebyshev 2', 'mod': 'pyfda.filter_widgets.cheby2'}),
     ('Ellip', {'name': 'Elliptic', 'mod': 'pyfda.filter_widgets.ellip'}),
     ('EllipZeroPhz', {'name': 'EllipZeroPhz', 'mod': 'pyfda.filter_widgets.ellip_zero'}),
     # FIR
     ('Equiripple', {'name': 'Equiripple', 'mod': 'pyfda.filter_widgets.equiripple'}),
     ('Firwin', {'name': 'Windowed FIR', 'mod': 'pyfda.filter_widgets.firwin'}),
     ('MA', {'name': 'Moving Average', 'mod': 'pyfda.filter_widgets.ma'}),
     ('Manual_FIR', {'name': 'Manual', 'mod': 'pyfda.filter_widgets.manual'}),
     ('Manual_IIR', {'name': 'Manual', 'mod': 'pyfda.filter_widgets.manual'})
     ])
"""
The keys of this dictionary are the names of all found filter classes, the values
are the name to be displayed e.g. in the comboboxes and the fully qualified
name of the module containing the class.
"""

# Dictionary describing the available combinations of response types (rt),
# filter types (ft), design methods (dm) and filter order (fo). This dictionary
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
# in the [Config Settings] of `pyfda.conf`
# ------------------------------------------------------------------------------

conf_settings = {
    'THEME': 'light',
    'N_FFT':  8192  # number of FFT points for most widgets except y[n]
    }

# -----------------------------------------------------------------------------
# Dictionary containing current filter type, specifications, design and some
# auxiliary information, the initial definition here is copied into fil[0] ... [9]
# which can be modified by input widgets and design routines
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
    'fo': 'man',  # filter order, manual or min
    'freqSpecsRange': [
        0,
        0.5
    ],
    'freqSpecsRangeType': 'half',
    'freq_locked': False, # don't update absolute frequencies when f_S is changed
    'freq_specs_sort': True,  # sort freq. specs in ascending order
    'freq_specs_unit': 'f_S',
    'ft': 'IIR',  # filter type
    'fx_base': 'dec', # number format for fx display {'dec', 'hex', 'bin', 'oct', 'csd'}
    # string with current fixpoint module and class
    'fx_mod_class_name': 'pyfda.fixpoint_widgets.iir_df1.iir_df1_pyfixp_ui',
    # Settings for quantization subwidgets:
    #   'QI':input, 'QO': output, 'QCA': coeffs a, 'QCB': coeffs b, 'QACC': accumulator
    #    (more subwidgets can be added by fixpoint widget if needed)
    #  Keys:
    #   'WI': integer bits, 'WF': fractional bits,
    #   'w_a_m': word length automatic / manual calculation (not needed for 'QI', 'QO')
    #   'ovfl': overflow behaviour, 'quant': quantizer behaviour
    #   'N_over': number of overflows during last quantization process
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
for l in range(len(fil)):
    fil[l] = copy.deepcopy(fil_ref)

# -------------------------
def restore_fil():
    """
    Restore current global dict `fb.fil[0]` from undo memory `fil_undo`
    """
    global undo_step
    global undo_ptr

    # undo buffer is empty, don't copy anything
    if undo_step < 1:
        undo_step = 0
        return -1
    else:
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
def key_list_to_dict(keys: list) -> dict:
    """
    Convert a list or tuple of keys (str) to access a nested dict that can be
    read or written to and return that dict.

    The nested dict is always based on `fb.fil[0]`. In order to set or get the value
    of the nested dict, use the key for the lowest nesting level on the returned
    dict `d`, i.e. `d[keys[-1]] = arg` resp. `arg = d[keys[-1]]`.
    """
    # global fil
    if len(keys) == 0:
        raise KeyError("List of keys was empty!")

    if len(keys) == 1:
        d = fil[0]
    elif len(keys) == 2:
        d = fil[0][keys[0]]
    elif len(keys) == 3:
        d = fil[0][keys[0]][keys[1]]
    else:
        raise KeyError(
            "Creating dicts nested more than 3 keys deep is not supported yet!")
    return d

# -------------------------
def is_fx()-> bool:
    """
    Check if fixpoint mode is active
    """
    return fb_get('qfrmt') in ['qint', 'qfrac']

# -------------------------
def fx_set(fx: bool)-> None:
    """
    Set fixpoint mode by restoring previous fixpoint format
    when `fx == True`, otherwise restore previous float format.
    """
    if fx:
        fb_set('qfrmt', fb_get('qfrmt_fx_last'))
    else:
        fb_set('qfrmt', fb_get('qfrmt_float_last'))

# -------------------------
def fb_get(*args, fil_dict=fil[0]) -> str:
    """
    Get the value of a key in the global dict `fil[0]`. Multiple arguments
    access nested dicts:
    fb_get('qfrmt') == fb.fil[0]['qfrmt']
    fb_get('ba', 0) == fb.fil[0]['ba'][0]

    TODO: Keys need to be protected from accidental overwriting by
    the user. This will be done by prepending the keys with an underscore
    (e.g. `_f_S`) once all direct accesses have been changed.
    """
    if len(args) == 0:
        raise KeyError("'fb_get()' called without argument")

    if len(args) == 1:
        ret = fil_dict[args[0]]
        # ret = fil_dict['_' + args[0]]
    elif len(args) == 2:
        ret = fil_dict[args[0]][args[1]]
    elif len(args) == 3:
        ret = fil_dict[args[0]][args[1]][args[2]]
    else:
        raise KeyError(
            "Accessing dicts nested more than 3 keys deep is not supported yet!")

    if ret is None:
        logger.warning("Key '%s' not found in filter dict!", args[-1])
    return ret

# -------------------------
def fb_set(*args, backup: bool = True, fil_dict=fil[0]) -> None:
    """
    Set the value of a key in the global dict `fil[0]`
    """
    if type(args) != tuple or len(args) < 2:
        logger.error("No dictionary can be built from '%s'", args)
        return -1

    val = args[-1]  # last element is the value to be set

    try:
        d = key_list_to_dict(args[:-1])  # create nested dict from the other arguments
        _ =  d[args[-2]]  # try accessing dictionary
        if backup:
            store_fil()  # backup old setting

        if args[-2] =='qfrmt' and len(args) == 2:
            # remember current fixpoint / float format
            if is_fx():
                fil_dict['qfrmt_fx_last'] = fil[0]['qfrmt']
            else:
                fil[0]['qfrmt_float_last'] = fil[0]['qfrmt']
            # and set new format
            fil_dict['qfrmt'] = val
        else:
            d[args[-2]] = val  # store new value if valid
    except KeyError:
        dict_str = 'fb.fil[0]'  # create a string for the failed dict
        if len(args) < 3:  # only one level dictionary, args[-1] is already the key
            dict_str += '[' + args[-2] + ']'
        else:
            for i, s in enumerate(args[:-1]):
                dict_str += '[' + s[i] + ']'
        logger.error(f"Dict '%s' does not exist!", dict_str)
        return -1

    return 0

# Comparing nested dicts
# https://stackoverflow.com/questions/27265939/comparing-python-dictionaries-and-nested-dictionaries
