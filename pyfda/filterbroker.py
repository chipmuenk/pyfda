# -*- coding: utf-8 -*-
"""
filterbroker.py

Dynamic parameters and settings are exchanged via the dictionaries in this file.
Importing filterbroker.py runs the module once, defining all module variables.
Module variables are global like class variables. 


Author: Christian Muenker
"""

from __future__ import division, unicode_literals, print_function, absolute_import
#import importlib
#import logging
#import six

#logger = logging.getLogger(__name__)
# Project base directory
base_dir = ""

# State of filter design: "ok", "changed", "error", "failed"
design_filt_state = "changed"

# module myhdl found?
MYHDL = False

# see http://stackoverflow.com/questions/9058305/getting-attributes-of-a-class
# see http://stackoverflow.com/questions/2447353/getattr-on-a-module


#==============================================================================
# The entries in this file are only used as initial / default entries and
# demonstrate the structure of the global dicts and lists.
# They are also handy for module-level testing.

#The actual entries are created resp. overwritten by
#
# ----- FilterTreeBuilder.__init__() ------
# ------                 .buildFilTree()
#
# Dictionary with filter design class name and full module name
fc_module_names = {"equiripple":"pyfda.filter_design.equiripple",
                  "cheby1":"pyfda.filter_design.cheby1",
                  "cheby2":"pyfda.filter_design.cheby2"}

# Dictionary with translations between short and long names for filter design classes
fc_names = {# IIR:
            "butter":"Butterworth", "cheby1":"Chebychev 1",
            "bessel":"Bessel", "cheby2":"Chebychev 2",
            # FIR:
            "equiripple":"Equiripple", "firls":"Least-Square",
            "firwin":"Windowed"}

# Dictionary describing the available combinations of response types (rt),
# filter types (ft), design methods (dm) and filter order (fo).
vis_man = ['fo','fspecs','tspecs'] # manual filter order
vis_min = ['fo','fspecs','tspecs'] # minimum filter order
dis_man = [] # manual filter order
dis_min = ['fspecs'] # minimum filter order
msg_min = "minimum"
msg_man = "maximum"
fil_tree = {
    'HP':
        {'FIR':
            {'equiripple':
                {'man': {"par":['N', 'A_PB', 'F_PB'],
                         "vis":vis_man, "dis":dis_man, "msg":msg_man},
                 'min': {"par":['A_SB', 'A_PB', 'F_SB', 'F_PB'],
                         "vis":vis_min, "dis":dis_min, "msg":msg_min}}},
         'IIR':
             {'cheby1':
                 {'man': {"par":['N', 'A_PB', 'F_PB'],
                          "vis":vis_man, "dis":dis_man, "msg":msg_man},
                  'min': {"par":['A_SB', 'A_PB', 'F_SB', 'F_PB'],
                          "vis":vis_min, "dis":dis_min, "msg":msg_min}},
              'cheby2':
                  {'man': {"par":['N', 'A_SB', 'F_SB'],
                           "vis":vis_man, "dis":dis_man, "msg":msg_man},
                   'min': {"par":['A_SB', 'A_PB', 'F_SB', 'F_PB'],
                           "vis":vis_min, "dis":dis_min, "msg":msg_min}}}},
    'BP':
        {'FIR':
            {'equiripple':
                {'man': {"par":['N', 'F_SB', 'F_PB', 'F_PB2', 'F_SB2', 'W_PB', 'W_SB', 'W_SB2'],
                         "vis":vis_man, "dis":dis_man, "msg":msg_man}}},
         'IIR':
             {'cheby1': {'man': {"par":['N', 'A_PB', 'F_PB', 'F_PB2'], 
                                 "vis":vis_man, "dis":dis_man, "msg":msg_man},
                         'min': {"par":['A_PB', 'A_SB', 'F_SB', 'F_PB', 'F_PB2', 'F_SB2'],
                                 "vis":vis_min, "dis":dis_min, "msg":msg_min}},
              'cheby2': {'man': {"par":['N', 'A_SB', 'F_SB', 'F_SB2'],
                                 "vis":vis_man, "dis":dis_man, "msg":msg_man},
                         'min': {"par":['A_PB', 'A_SB','F_SB',  'F_PB', 'F_PB2', 'F_SB2'],
                                 "vis":vis_min, "dis":dis_min, "msg":msg_min}}}},
    'LP':
        {'FIR':
            {'equiripple':
                {'man': {"par":['N', 'A_PB', 'F_PB'], 
                         "vis":vis_man, "dis":dis_man, "msg":msg_man},
                 'min': {"par":['A_PB', 'A_SB', 'F_PB', 'F_SB'],
                         "vis":vis_min, "dis":dis_min, "msg":msg_min}}},
         'IIR':
             {'cheby1':
                 {'man': {"par":['N', 'A_PB', 'F_PB'],
                          "vis":vis_man, "dis":dis_man, "msg":msg_man},
                  'min': {"par":['A_PB', 'A_SB', 'F_PB', 'F_SB'], 
                          "vis":vis_min, "dis":dis_min, "msg":msg_min}},
             'cheby2': {'man': {"par":['N', 'A_SB', 'F_SB'],
                                "vis":vis_man, "dis":dis_man, "msg":msg_man},
                        'min': {"par":['A_PB', 'A_SB', 'F_PB', 'F_SB'],
                                "vis":vis_min, "dis":dis_min, "msg":msg_min}
                        }
            }
        }
    }


# -----------------------------------------------------------------------------
# Dictionary containing current filter type, specifications, design and some
# auxiliary information, it is automatically overwritten by input widgets
# and design routines
#------------------------------------------------------------------------------

fil = [None] * 10 # create empty list with length 10 for multiple filter designs
# This functionality is not implemented yet, currently only fil[0] is used

fil[0] = {'rt':'LP', 'ft':'FIR', 'fc':'equiripple', 'fo':'man',
            'N':10, 'f_S':1,
            'A_PB':0.02, 'A_PB2': 0.01, 'F_PB':0.1, 'F_PB2':0.4, 'F_C': 0.2, 'F_N': 0.2,
            'A_SB':0.001, 'A_SB2': 0.0001, 'F_SB':0.2, 'F_SB2':0.3, 'F_C2': 0.4, 'F_N2': 0.4,
            'W_PB':1, 'W_PB2':1, 'W_SB':1, 'W_SB2':1,
            #
            'ba':([1, 1, 1], [3, 0, 2]), # tuple of bb, aa
            'zpk':([-0.5 + 3**0.5/2.j, -0.5 - 3**0.5/2.j],
                   [(2./3)**0.5 * 1j, -(2./3)**0.5 * 1j], 1),
            'q_coeff':{'QI':0, 'QF': 15, 'quant': 'round', 'ovfl': 'sat', 'frmt':'frac'},
            'sos': None,
            'creator':('ba','filterbroker'), #(format ['ba', 'zpk', 'sos'], routine)
            'amp_specs_unit':'dB',
            'freqSpecsRangeType':'Half',
            'freqSpecsRange': [0,0.5],
            'freq_specs_sort' : True,
            'freq_specs_unit' : 'f_S',
            'plt_fLabel':r'$f$ in Hz $\rightarrow$',
            'plt_fUnit':'Hz',
            'plt_tLabel':r'$n \; \rightarrow$',
            'plt_tUnit':'s',
            'plt_phiUnit': 'rad',
            'plt_phiLabel': r'$\angle H(\mathrm{e}^{\mathrm{j} \Omega})$  in rad ' + r'$\rightarrow $',
            'wdg_dyn':{'win':'hann'}
            }
