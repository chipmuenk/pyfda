# -*- coding: utf-8 -*-
"""
Design equiripple-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in coefficients format ('ba')
   
Author: Christian Muenker 2014 - 2016
"""
from __future__ import print_function, division, unicode_literals, absolute_import

#import pyfda.filterbroker as fb

class Common(object):
    
    def __init__(self):
    
        self.rt_base_fir = {
            'LP': {'man':{'par':('F_PB','F_SB')},
                   'min':{'par':('F_PB','F_SB','A_PB','A_SB')},
                   '_targ':{'par':('F_PB','F_SB','A_PB','A_SB')}},
            'HP': {'man':{'par':('F_SB','F_PB')},
                   'min':{'par':('F_SB','F_PB','A_SB','A_PB')},
                   '_targ':{'par':('F_SB','F_PB','A_SB','A_PB')}},
            'BP': {'man':{'par':('F_SB', 'F_PB', 'F_PB2', 'F_SB2')},
                   'min':{'par':('F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'A_SB','A_PB','A_SB2')},
                   '_targ':{'par':('F_SB', 'F_PB','F_PB2','F_SB2',
                                   'A_SB', 'A_PB','A_SB2')}},
            'BS': {'man':{'par':('F_PB','F_SB','F_SB2','F_PB2')},
                   'min':{'par':('F_PB','F_SB','F_SB2','F_PB2', 'A_PB','A_SB','A_PB2')},
                   '_targ':{'par':('F_PB','F_SB','F_SB2','F_PB2',
                                 'A_PB','A_SB','A_PB2',)}}
                   }

        self.rt_equiripple = {
            'LP': {'man':{'par':('W_PB','W_SB','F_PB','F_SB')},
                   'min':{'par':('F_PB','F_SB','W_PB','W_SB', 'A_PB', 'A_SB')},
                   '_targ':{'par':('F_PB','F_SB','A_PB','A_SB')}},
            'HP': {'man':{'par':('W_SB','W_PB','F_SB','F_PB')},
                   'min':{'par':('F_SB','F_PB','W_SB','W_PB','A_SB','A_PB')},
                   '_targ':{'par':('F_SB','F_PB','A_SB','A_PB')}},
            'BP': {'man':{'par':('F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'W_SB','W_PB','W_SB2')},
                   'min':{'par':('F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'W_SB', 'W_PB','W_SB2','A_SB','A_PB','A_SB2')},
                   '_targ':{'par':('F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'A_SB', 'A_PB','A_SB2')}},
            'BS': {'man':{'par':('F_PB','F_SB','F_SB2','F_PB2', 'W_SB','W_PB','W_SB2'),
                          'msg':(r"<br /><b>Note:</b> Order needs to be odd for a bandstop!",)},
                   'min':{'par':('W_PB','W_SB','W_PB2',
                                 'F_PB','F_SB','F_SB2','F_PB2', 'A_PB','A_SB','A_PB2')},
                   '_targ':{'par':('F_PB','F_SB','F_SB2','F_PB2',
                                 'A_PB','A_SB','A_PB2',)}},
            'HIL': {'man':{'par':('F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'W_SB', 'W_PB', 'W_SB2'),
                           'vis':("fspecs",)}},
            'DIFF': {'man':{'par':('F_PB', 'W_PB'), 
                            'vis':("fspecs",)}}
                   }


        self.rt_targ = {
            'LP': {'_targ':{'par':('F_PB','F_SB','A_PB','A_SB')}},
            'HP': {'_targ':{'par':('F_SB','F_PB','A_SB','A_PB')}},
            'BP': {'_targ':{'par':('F_SB','F_PB','F_PB2','F_SB2','A_SB','A_PB')}},
            'BS': {'_targ':{'par':('F_PB','F_SB','F_SB2','F_PB2','A_PB','A_SB')}}
                   }

                   
        self.rt_base_iir = {
            'LP': {'man':{'par':('F_C','A_PB','A_SB')},
                   'min':{'par':('F_C','A_PB','A_SB')},
                   '_targ':{'par':('F_PB','F_SB','A_PB','A_SB')}},
            'HP': {'man':{'par':('F_C','A_SB','A_PB')},
                   'min':{'par':('F_C','A_SB','A_PB')},
                   '_targ':{'par':('F_SB','F_PB','A_SB','A_PB')}},
            'BP': {'man':{'par':('F_C', 'F_C2','A_SB', 'A_PB')},
                   'min':{'par':('F_C', 'F_C2','A_SB', 'A_PB')},
                   '_targ':{'par':('F_SB', 'F_PB','F_PB2','F_SB2',
                                   'A_SB', 'A_PB')}},
            'BS': {'man':{'par':('F_C', 'F_C2', 'A_PB','A_SB')},
                   'min':{'par':('F_C', 'F_C2', 'A_PB','A_SB')},
                   '_targ':{'par':('F_PB','F_SB','F_SB2','F_PB2', 'A_PB','A_SB')}}
                   }

                   
        self.base_iir_new = {
            'COM':{'man':{'fo':       ('a', 'N')},
                   'min':{'fo':       ('d', 'N')},
                   'msg':(
                   "Enter maximum pass band ripple <b><i>A<sub>PB</sub></i></b>, "
                    "minimum stop band attenuation <b><i>A<sub>SB</sub> </i></b>"
                    "&nbsp;and the corresponding corner frequencies of pass and "
                    "stop band(s), <b><i>F<sub>PB</sub></i></b>&nbsp; and "
                    "<b><i>F<sub>SB</sub></i></b> .",)
                       },
            'LP': {'man':{'fspecs':   ('a','F_C'),
                          'ftargs:f': ('u','F_PB','F_SB'),
                          'ftargs:a': ('u','A_PB','A_SB')},
                   'min':{'fspecs':   ('d','F_C'),
                          'ftargs:f': ('a','F_PB','F_SB'),
                          'ftargs:a': ('a','A_PB','A_SB')}},
            'HP': {'man':{'fspecs':   ('a','F_C'),
                          'ftargs:f': ('u','F_SB','F_PB'),
                          'ftargs:a': ('u','A_SB','A_PB')},
                   'min':{'fspecs':   ('d','F_C'),
                          'ftargs:f': ('a','F_SB','F_PB'),
                          'ftargs:a': ('a','A_SB','A_PB')}},
            'BP': {'man':{'fspecs':   ('a','F_C', 'F_C2'),
                          'ftargs:f': ('u','F_SB','F_PB','F_PB2','F_SB2'),
                          'ftargs:a': ('u','A_SB','A_PB')},
                   'min':{'fspecs':   ('d','F_C'),
                          'ftargs:f': ('a','F_SB', 'F_PB','F_PB2','F_SB2'),
                          'ftargs:a': ('a','A_SB', 'A_PB')}},
            'BS': {'man':{'fspecs':   ('a','F_C', 'F_C2'),
                          'ftargs:f': ('u','F_PB','F_SB','F_SB2','F_PB2'),
                          'ftargs:a': ('u','A_PB','A_SB')},
                   'min':{'fspecs':   ('d','F_C'),
                          'ftargs:f': ('a','F_PB','F_SB','F_SB2','F_PB2'),
                          'ftargs:a': ('a','A_PB', 'A_SB')}}
            }
        


#------------------------------------------------------------------------------

if __name__ == '__main__':
    pass    