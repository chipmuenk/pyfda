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
from collections import OrderedDict
from pyfda.libs.frozendict import freeze_hierarchical

clipboard = None
""" Handle to central clipboard instance """

base_dir = ""  #: Project base directory

# State of filter design: "ok", "changed", "error", "failed", "active"
design_filt_state = "changed"

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
     ('Input_Fixpoint_Specs', {'name': 'Fixpoint', 'mod': 'pyfda.input_widgets.input_fixpoint_specs'})
     ])

fixpoint_classes = OrderedDict(
    [('FIR_DF_wdg', {'name': 'FIR_DF', 'mod': 'pyfda.fixpoint_widgets.fir_df', 'opt': ['Equiripple', 'Firwin']}),
     ('Delay_wdg', {'name': 'Delay', 'mod': 'pyfda.fixpoint_widgets.delay1', 'opt': ['Equiripple']})
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
# filter types (ft), design methods (dm) and filter order (fo):
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
# Dictionary containing current filter type, specifications, design and some
# auxiliary information, the initial definition here is overwritten by
# input widgets and design routines:
# ------------------------------------------------------------------------------
fil_init = {'rt': 'LP', 'ft': 'IIR', 'fc': 'Cheby1', 'fo': 'man',  # filter type
            'N': 10,  # filter order
            'f_S': 1, 'T_S': 1,  # current sampling frequency and period
            'f_S_wav': 16000,  # sampling frequency for wav files
            'f_S_prev': 1,  # previous sampling frequency
            'freq_locked': False,  # don't update absolute frequencies when f_S is changed
            'f_S_scale': 1,  #
            'f_max': 1,
            'freqSpecsRangeType': 'Half',
            'freqSpecsRange': [0, 0.5],
            'freq_specs_sort': True,  # sort freq. specs in ascending order
            'freq_specs_unit': 'f_S',
            'plt_fLabel': r'$F = 2f \, / \, f_S = \Omega \, / \, \mathrm{\pi} \; \rightarrow$',
            'plt_fUnit': 'f_S',
            'plt_tLabel': r'$n \; \rightarrow$',
            'plt_tUnit': 's',
            'A_PB': 0.02, 'A_PB2': 0.01, 'F_PB': 0.1, 'F_PB2': 0.4, 'F_C': 0.2, 'F_N': 0.2,
            'A_SB': 0.001, 'A_SB2': 0.0001, 'F_SB': 0.2, 'F_SB2': 0.3, 'F_C2': 0.4, 'F_N2': 0.4,
            'W_PB': 1, 'W_PB2': 1, 'W_SB': 1, 'W_SB2': 1,
            #
            'ba': ([1, 1, 1], [1, 0.1, 0.5]),  # (bb, aa) tuple coefficient lists
            # causal zeros/poles/gain
            'zpk': ([-0.5 + 3**0.5/2.j, -0.5 - 3**0.5/2.j],
                   [(2./3)**0.5 * 1j, -(2./3)**0.5 * 1j], 1),
            #
            'sos': [],
            # input, output, accu, coeffs, ... fixpoint word formats and quantizer
            # settings:
            'fxqc':
                {'QI': {'WI': 0, 'WF': 15, 'W': 16, 'ovfl': 'sat',  'quant': 'round'},
                 'QO': {'WI': 0, 'WF': 15, 'W': 16, 'ovfl': 'wrap', 'quant': 'floor'},
                 'QACC': {'WI': 0, 'WF': 31, 'W': 32, 'ovfl': 'wrap', 'quant': 'floor'},
                 'QCB': {'WI': 0, 'WF': 15, 'W': 16, 'ovfl': 'wrap', 'quant': 'floor',
                         'scale': 1, 'fx_base': 'float'},
                 'QCA': {'WI': 2, 'WF': 13, 'W': 16, 'ovfl': 'wrap', 'quant': 'floor',
                         'scale': 1, 'fx_base': 'float'}
                },
                # 'b': [32768, 32768, 32768],
                # 'a': [65536, 6553, 0]
                # },
            'fx_sim': False,  # fixpoint simulation mode 
            'creator': ('ba', 'filterbroker'),  #(format ['ba', 'zpk', 'sos'], routine)
            'amp_specs_unit': 'dB',

            'plt_phiUnit': 'rad',
            'plt_phiLabel': r'$\angle H(\mathrm{e}^{\mathrm{j} \Omega})$  in rad '\
                    + r'$\rightarrow $',
            'time_designed': -1,
            'wdg_dyn': {'win': 'hann'},
            # Parameters for spectral analysis window function
            'win_fft':
                {'name': 'Kaiser',  # Window name
                 'fn_name': 'kaiser',  # function name or array with values
                 'par': [{'name': '&beta;',
                          'name_tex': r'$\beta$',
                          'val': 10,
                          'min': 0,
                          'max': 30,
                          'tooltip':
                              ("<span>Shape parameter; lower values reduce main lobe width, "
                              "higher values reduce side lobe level, typ. in the range "
                              "5 ... 20.</span>")}],
                 'n_par': 1,   # number of window parameters
                 'info': "",     # Docstring for the window
                 'win_len': 1024,
                 },
            # Parameters for filter design window function
            'win_fir':
                {'name': 'Hann',  # Window name
                 'fn_name': 'hann',  # function name or array with values
                 'par': [],    # set of list of window parameters
                 'n_par': 0,   # number of window parameters
                 'info': "",   # Docstring for the window
                 'win_len': 1024
                 }
            }

fil = [None] * 10  # create empty list with length 10 for multiple filter designs
# This functionality is not implemented yet, currently only fil[0] is used

# define fil[0] as a dict with "built-in" default. The argument defines the default
# factory that is called when a key is missing. Here, lambda simply returns a float.
# When e.g. list is given as the default_factory, an empty list is returned.
# fil[0] = defaultdict(lambda: 0.123)
fil[0] = {}
# Now, copy each key-value pair into the defaultdict
for k in fil_init:
    fil[0].update({k: fil_init[k]})

# Define dictionary with default settings for  FiXpoint Quantization and Coefficients:
# 'fxqc'
