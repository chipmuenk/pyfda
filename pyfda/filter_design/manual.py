# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Dummy / template file for manual filter designs by entering P/Z or b/a. 
Targets for LP, HP, BP, BS are provided.
Returns nothing.

Attention: 
This class is re-instantiated dynamically everytime the filter design method
is selected, calling the __init__ method.

API version info:   
    1.0: initial working release
    1.1: mark private methods as private
    1.2: new API using fil_save
    1.3: new public methods destruct_UI + construct_UI (no longer called by __init__)    
    1.4: module attribute `filter_classes` contains class name and combo box name
         instead of class attribute `name`
    2.0: Specify the parameters for each subwidget as tuples in a dict where the
         first element controls whether the widget is visible and / or enabled.
         This dict is now called self.rt_dict. When present, the dict self.rt_dict_add
         is read and merged with the first one.
    2.1: Remove empty methods construct_UI and destruct_UI and attributes 
         self.wdg and self.hdl
"""

from __future__ import print_function, division, unicode_literals

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals

__version__ = "2.0"

filter_classes = {'Manual_FIR':'Manual', 'Manual_IIR':'Manual'}

FRMT = 'ba' # default output format of filter design routines 'zpk' / 'ba' / 'sos'

msg_man = ('a', "Design the filter using the P/Z or the b/a widget. "
                "The target specs are only used for entering and displaying spec limits.")
                
info_str =\
"""
**Manual Filter Design** 

Manual filter design mode is selected automatically when entering / editing
poles and zeros ("P/Z" tab) or coefficients ("b,a" tab). Use the info tab
or the magnitude frequency response (select "Show Specs") to check whether
the designed filter fulfills the target specs.
"""

class Manual_FIR(object):
    
    def __init__(self):

        # This part contains static information for building the filter tree

        self.ft = 'FIR'

        self.rt_dict = {
            'COM':{'man':{'fo': ('d', 'N'),
                          'msg': msg_man}
                        },
            'LP': {'man':{'tspecs': ('u', {'frq':('u','F_PB','F_SB'), 
                                           'amp':('u','A_PB','A_SB')})
                         }},
            'HP': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB'), 
                                           'amp':('u','A_SB','A_PB')})
                        }},
            'BS': {'man':{'tspecs': ('u', {'frq':('u','F_PB','F_SB','F_SB2', 'F_PB2'), 
                                           'amp':('u','A_PB','A_SB','A_PB2')})
                        }},
            'BP': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2',), 
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                        }},
            'HIL': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2',), 
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                        }},
            'DIFF': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2',), 
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                        }}
                   }

        self.info = info_str
        self.info_doc = []
        self.info_doc.append('manual FIR\n==========')
        
    #------------------- end of static info for filter tree -------------------

    def _get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N     = fil_dict['N'] # remez algorithms expects number of taps
                                # which is larger by one than the order?!
        self.F_PB  = fil_dict['F_PB']
        self.F_SB  = fil_dict['F_SB']
        self.F_PB2 = fil_dict['F_PB2']
        self.F_SB2 = fil_dict['F_SB2']
        self.F_C   = fil_dict['F_C']
        self.F_C2  = fil_dict['F_C2']
        
        # firwin amplitude specs are linear (not in dBs)
        self.A_PB  = fil_dict['A_PB']
        self.A_PB2 = fil_dict['A_PB2']
        self.A_SB  = fil_dict['A_SB']
        self.A_SB2 = fil_dict['A_SB2']

    def LPman(self, fil_dict):
        pass

    def HPman(self, fil_dict):
        pass

    def BPman(self, fil_dict):
        pass

    def BSman(self, fil_dict):
        pass
    
    def HILman(self, fil_dict):
        pass

    def DIFFman(self, fil_dict):
        pass

#############################################################################    
class Manual_IIR(object):
    
    def __init__(self):

        # This part contains static information for building the filter tree
                    
        self.ft = 'IIR'

        self.rt_dict = {
            'COM':{'man':{'fo': ('d', 'N'),
                          'msg': msg_man}
                        },
            'LP': {'man':{'tspecs': ('u', {'frq':('u','F_PB','F_SB'), 
                                           'amp':('u','A_PB','A_SB')})
                         }},
            'HP': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB'), 
                                           'amp':('u','A_SB','A_PB')})
                        }},
            'BS': {'man':{'tspecs': ('u', {'frq':('u','F_PB','F_SB','F_SB2', 'F_PB2'), 
                                           'amp':('u','A_PB','A_SB','A_PB2')})
                        }},
            'BP': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2',), 
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                        }},
            'HIL': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2',), 
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                        }},
            'DIFF': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2',), 
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                        }}
                   }
        
        self.info = info_str
        self.info_doc = []
        self.info_doc.append('manual IIR\n==========')
        
        #------------------- end of static info for filter tree ---------------       
            
    def _get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N     = fil_dict['N'] # remez algorithms expects number of taps
                                # which is larger by one than the order?!
        self.F_PB  = fil_dict['F_PB']
        self.F_SB  = fil_dict['F_SB']
        self.F_PB2 = fil_dict['F_PB2']
        self.F_SB2 = fil_dict['F_SB2']
        self.F_C   = fil_dict['F_C']
        self.F_C2  = fil_dict['F_C2']
        
        # firwin amplitude specs are linear (not in dBs)
        self.A_PB  = fil_dict['A_PB']
        self.A_PB2 = fil_dict['A_PB2']
        self.A_SB  = fil_dict['A_SB']
        self.A_SB2 = fil_dict['A_SB2']

    def LPman(self, fil_dict):
        pass

    def HPman(self, fil_dict):
        pass

    def BPman(self, fil_dict):
        pass

    def BSman(self, fil_dict):
        pass

    def HILman(self, fil_dict):
        pass

    def DIFFman(self, fil_dict):
        pass


#------------------------------------------------------------------------------

if __name__ == '__main__':
    filt = Manual_IIR()    # instantiate filter
    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][FRMT]) # return results in default format
