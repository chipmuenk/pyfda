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
            'LP': {'man':{'par':['F_PB','F_SB']},
                   'min':{'par':['F_PB','F_SB','A_PB','A_SB']},
                   '_targ':{'par':['F_PB','F_SB','A_PB','A_SB']}},
            'HP': {'man':{'par':['F_SB','F_PB']},
                   'min':{'par':['F_SB','F_PB','A_SB','A_PB']},
                   '_targ':{'par':['F_SB','F_PB','A_SB','A_PB']}},
            'BP': {'man':{'par':['F_SB', 'F_PB', 'F_PB2', 'F_SB2']},
                   'min':{'par':['F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'A_SB','A_PB','A_SB2']},
                   '_targ':{'par':['F_SB', 'F_PB','F_PB2','F_SB2',
                                   'A_SB', 'A_PB','A_SB2']}},
            'BS': {'man':{'par':['F_PB','F_SB','F_SB2','F_PB2']},
                   'min':{'par':['F_PB','F_SB','F_SB2','F_PB2', 'A_PB','A_SB','A_PB2']},
                   '_targ':{'par':['F_PB','F_SB','F_SB2','F_PB2',
                                 'A_PB','A_SB','A_PB2',]}}
                   }

        self.rt_equiripple = {
            'LP': {'man':{'par':['W_PB','W_SB','F_PB','F_SB']},
                   'min':{'par':['F_PB','F_SB','W_PB','W_SB', 'A_PB', 'A_SB']},
                   '_targ':{'par':['F_PB','F_SB','A_PB','A_SB']}},
            'HP': {'man':{'par':['W_SB','W_PB','F_SB','F_PB']},
                   'min':{'par':['F_SB','F_PB','W_SB','W_PB','A_SB','A_PB']},
                   '_targ':{'par':['F_SB','F_PB','A_SB','A_PB']}},
            'BP': {'man':{'par':['F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'W_SB','W_PB','W_SB2']},
                   'min':{'par':['F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'W_SB', 'W_PB','W_SB2','A_SB','A_PB','A_SB2']},
                   '_targ':{'par':['F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'A_SB', 'A_PB','A_SB2']}},
            'BS': {'man':{'par':['F_PB','F_SB','F_SB2','F_PB2', 'W_SB','W_PB','W_SB2'],
                          'msg':r"<br /><b>Note:</b> Order needs to be odd for a bandstop!"},
                   'min':{'par':['W_PB','W_SB','W_PB2',
                                 'F_PB','F_SB','F_SB2','F_PB2', 'A_PB','A_SB','A_PB2']},
                   '_targ':{'par':['F_PB','F_SB','F_SB2','F_PB2',
                                 'A_PB','A_SB','A_PB2',]}},
            'HIL': {'man':{'par':['F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'W_SB', 'W_PB', 'W_SB2'],
                           'vis':["fspecs"], }},
            'DIFF': {'man':{'par':['F_PB', 'W_PB'], 
                            'vis':["fspecs"]}}
                   }




                   
        self.rt_base_iir = {
            'LP': {'man':{'par':['F_C']},
                   'min':{'par':['F_C']},
                   '_targ':{'par':['F_PB','F_SB','A_PB','A_SB']}},
            'HP': {'man':{'par':['F_C']},
                   'min':{'par':['F_C']},
                   '_targ':{'par':['F_SB','F_PB','A_SB','A_PB']}},
            'BP': {'man':{'par':['F_C', 'F_C2']},
                   'min':{'par':['F_C', 'F_C2']},
                   '_targ':{'par':['F_SB', 'F_PB','F_PB2','F_SB2',
                                   'A_SB', 'A_PB']}},
            'BS': {'man':{'par':['F_C', 'F_C2']},
                   'min':{'par':['F_C', 'F_C2']},
                   '_targ':{'par':['F_PB','F_SB','F_SB2','F_PB2', 'A_PB','A_SB']}}
                   }
        


#------------------------------------------------------------------------------

if __name__ == '__main__':
    pass    