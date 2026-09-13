# -*- coding: utf-8 -*-
#
# This file is part of the pyfda project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyfda Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Store some data externally
"""

import numpy as np

# -----------------------------------------------------------------------------
# Reference dictionary containing current filter type, specifications, design
# and some auxiliary information, the initial definition here is copied into
# fil[0] ... [9] which can be modified by input widgets and design routines
# -----------------------------------------------------------------------------
fil_ref = {
    '_id': [], # a list with the keyword 'pyfda' and the version, e.g. ['pyfda', 1]
    # amplitude specs (linear units)
    'a_pb': 0.2056717652757185,
    'a_pb2': 0.01,
    'a_sb': 0.001,
    'a_sb2': 0.0001,
    # frequency specs (normalized to F_S)
    'f_c': 0.1,
    'f_c2': 0.4,
    'f_pb': 0.1,
    'f_pb2': 0.3,
    'f_sb': 0.2,
    'f_sb2': 0.4,
    'N': 4,  # filter order
    'T_S': 1.0,  # sample time
    # weights for pass- and stopbands
    'w_pb': 1.0,
    'w_pb2': 1.0,
    'w_sb': 1.0,
    'w_sb2': 1.0,
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
    'f_s_prev': 1.0,  # previous sampling frequency
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
    'freq_specs_range': [
        0,
        0.5
    ],
    'freq_specs_range_type': 'half',
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
    'plt_f_label': '$F = f\\, /\\, f_S = \\Omega \\, /\\,  2 \\mathrm{\\pi} \\; \\rightarrow$',
    'plt_f_unit': 'f_S',
    'plt_phi_label': '$\\angle H(\\mathrm{e}^{\\mathrm{j} \\Omega})$ in rad $\\rightarrow $',
    'plt_phi_unit': 'rad',
    'plt_t_label': '$n = t\\, /\\, T_S \\; \\rightarrow$',
    'plt_t_unit': 'T_S',

    'qfrmt': 'float64',  # global quantization format {'float64', 'float32', 'qint', 'qfrac'}
    'qfrmt_float_last': 'float64',  # last used float format
    'qfrmt_fx_last': 'qfrac',  # last used fixpoint format

    'rt': 'lp',  # filter response type
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