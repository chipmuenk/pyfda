# -*- coding: utf-8 -*-
"""
filterbroker.py

Dynamic parameters and settings are exchanged via the dictionaries in this file.
Importing filterbroker.py runs the module once, defining all module variables.
Module variables are global like class variables. 


Author: Christian Muenker
"""

from __future__ import division, unicode_literals, print_function, absolute_import
from collections import defaultdict
from .frozendict import freeze_hierarchical
from .compat import QSysInfo
#import importlib
#import logging
#import six

#logger = logging.getLogger(__name__)
# Project base directory
base_dir = ""

# store old data when modifying a field for restoring if new data is invalid
data_old = ""

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

# The keys of this dictionary are all found class names, the values are the name
# to be displayed e.g. in the comboboxes and the fully qualified name of the module
# containing the class
fil_classes = {# IIR:
            'Butter':{'name':'Butterworth', 'mod':'pyfda.filter_design.butter'},
            'Cheby1':{'name':'Chebychev 1', 'mod':'pyfda.filter_design.cheby1'},
            'Cheby2':{'name':'Chebychev 2', 'mod':'pyfda.filter_design.cheby2'},
            'Bessel':{'name':'Bessel',      'mod':'pyfda.filter_design.bessel'},
            'Ellip' :{'name':'Elliptic',    'mod':'pyfda.filter_design.ellip'},

            # FIR:
            'Equiripple':{'name':'Equiripple',  'mod':'pyfda.filter_design.equiripple'},
            'MA'      :{'name':'Moving Average','mod':'pyfda.filter_design.ma'},
            'Firwin'    :{'name':'Windowed FIR','mod':'pyfda.filter_design.firwin'}
            }

# Dictionary describing the available combinations of response types (rt),
# filter types (ft), design methods (dm) and filter order (fo).

fil_tree = freeze_hierarchical({
    'LP':{
        'FIR':{
            'Equiripple':{
                 'man':{'fo':     ('a','N'),
                        'fspecs': ('a','F_C'),
                        'wspecs': ('a','W_PB','W_SB'),
                        'tspecs': ('u', {'frq':('u','F_PB','F_SB'), 
                                         'amp':('u','A_PB','A_SB')}),
                        'msg':    ('a',
                                     "Enter desired filter order <b><i>N</i></b>, corner "
        "frequencies of pass and stop band(s), <b><i>F<sub>PB</sub></i></b>"
        "&nbsp; and <b><i>F<sub>SB</sub></i></b>, and a weight "
        "value <b><i>W</i></b>&nbsp; for each band."
                                    )
                        },
                 'min':{'fo':     ('d','N'),
                        'fspecs': ('d','F_C'),
                        'wspecs': ('d','W_PB','W_SB'),
                        'tspecs': ('a', {'frq':('a','F_PB','F_SB'), 
                                         'amp':('a','A_PB','A_SB')}),
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
        'IIR':{
             'Cheby1':{
                 'man':{'fo':     ('a','N'),
                        'fspecs': ('a','F_C'),
                        'tspecs': ('u', {'frq':('u','F_PB','F_SB'), 
                                         'amp':('u','A_PB','A_SB')})
                        },
                 'min':{'fo':     ('d','N'),
                        'fspecs': ('d','F_C'),
                        'tspecs': ('a', {'frq':('a','F_PB','F_SB'), 
                                         'amp':('a','A_PB','A_SB')})
                        }
                }
            }  
        },
    'HP':{
        'FIR':{
            'Equiripple':{
                 'man':{'fo':     ('a','N'),
                        'fspecs': ('a','F_C'),
                        'wspecs': ('a','W_SB','W_PB'),
                        'tspecs': ('u', {'frq':('u','F_SB','F_PB'), 
                                         'amp':('u','A_SB','A_PB')})
                            },
                 'min':{'fo':     ('d','N'),
                        'wspecs': ('d','W_SB','W_PB'),
                        'fspecs': ('d','F_C'),
                        'tspecs': ('a', {'frq':('a','F_SB','F_PB'), 
                                         'amp':('a','A_SB','A_PB')})
                        }
                    }
              },
        'IIR':{
            'Cheby1':{
                 'man':{'fo':     ('a','N'),
                        'fspecs': ('a','F_C'),
                        'tspecs': ('u', {'frq':('u','F_SB','F_PB'), 
                                         'amp':('u','A_SB','A_PB')})
                        },
                 'min':{'fo':     ('d','N'),
                        'fspecs': ('d','F_C'),
                        'tspecs': ('a', {'frq':('a','F_SB','F_PB'), 
                                         'amp':('a','A_SB','A_PB')})
                        }
                    }  
                }
        },
    'BP':{
        'FIR':{
            'Equiripple':{
                 'man':{'fo':     ('a','N'),
                        'wspecs': ('a','W_SB','W_PB','W_SB2'),
                        'fspecs': ('a','F_C','F_C2'),
                        'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2'), 
                                         'amp':('u','A_SB','A_PB','A_SB2')})
                            },
                 'min':{'fo':     ('d','N'),
                        'fspecs': ('d','F_C','F_C2'),
                        'wspecs': ('d','W_SB','W_PB','W_SB2'),
                        'tspecs': ('a', {'frq':('a','F_SB','F_PB','F_PB2','F_SB2'), 
                                         'amp':('a','A_SB','A_PB','A_SB2')})
                        }
                    }
                }
          },
    'BS':{
        'FIR':{
            'Equiripple':{
                'man':{ 'fo':     ('a','N'),
                        'wspecs': ('a','W_PB','W_SB','W_PB2'),
                        'fspecs': ('a','F_C','F_C2'),
                        'tspecs': ('u', {'frq':('u','F_PB','F_SB','F_SB2','F_PB2'), 
                                         'amp':('u','A_PB','A_SB','A_PB2')})
                    },
                'min':{ 'fo':     ('d','N'),
                        'wspecs': ('d','W_PB','W_SB','W_PB2'),
                        'fspecs': ('d','F_C','F_C2'),
                        'tspecs': ('a', {'frq':('a','F_PB','F_SB','F_SB2','F_PB2'), 
                                         'amp':('a','A_PB','A_SB','A_PB2')})
                      }
                }
             }
        }
    })

# -----------------------------------------------------------------------------
# Dictionary containing current filter type, specifications, design and some
# auxiliary information, it is automatically overwritten by input widgets
# and design routines
#------------------------------------------------------------------------------


# Initial filter dictionary
fil_init = {'rt':'LP', 'ft':'FIR', 'fc':'equiripple', 'fo':'man',
            'N':10, 'f_S':1,
            'A_PB':0.02, 'A_PB2': 0.01, 'F_PB':0.1, 'F_PB2':0.4, 'F_C': 0.2, 'F_N': 0.2,
            'A_SB':0.001, 'A_SB2': 0.0001, 'F_SB':0.2, 'F_SB2':0.3, 'F_C2': 0.4, 'F_N2': 0.4,
            'W_PB':1, 'W_PB2':1, 'W_SB':1, 'W_SB2':1,
            #
            'ba':([1, 1, 1], [3, 0, 2]), # tuple of bb, aa
            'zpk':([-0.5 + 3**0.5/2.j, -0.5 - 3**0.5/2.j],
                   [(2./3)**0.5 * 1j, -(2./3)**0.5 * 1j], 1),
            'q_coeff':{'WI':0, 'WF': 15, 'quant': 'round', 'ovfl': 'sat', 'frmt':'float', 'point':False},
            'sos': [],
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
            'time_designed' : -1,
            'wdg_dyn':{'win':'hann'}
            }


fil = [None] * 10 # create empty list with length 10 for multiple filter designs
# This functionality is not implemented yet, currently only fil[0] is used

# define fil[0] as a dict with "built-in" default. The argument defines the default
# factory that is called when a key is missing. Here, lambda simply returns a float.
# When e.g. list is given as the default_factory, an empty list is returned.
fil[0] = defaultdict(lambda: 0.123) 

# Now, copy each key-value pair into the defaultdict
for k in fil_init:
    fil[0].update({k:fil_init[k]})
    

"""
Find out which OS and which OS version the application runs under
"""
if hasattr(QSysInfo, "WindowsVersion"):
    OS = "WIN"
    OS_ver = QSysInfo.WindowsVersion
    cr = "\r\n" # Windows: carriage return + line feed
elif hasattr(QSysInfo, "MacintoshVersion"):
    OS = "MAC"
    OS_ver = QSysInfo.MacintoshVersion
    cr = "\r" # Mac: carriage return only
else:
    OS = "UNIX"
    OS_ver = None
    #TODO: Add some info about unix version
    cr = "\n" # *nix: line feed only
print(OS, OS_ver)       



