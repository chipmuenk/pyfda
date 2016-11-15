# -*- coding: utf-8 -*-
"""
Design equiripple-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in coefficients format ('ba')
   
Author: Christian Muenker 2014 - 2016
"""
from __future__ import print_function, division, unicode_literals, absolute_import

#import pyfda.filterbroker as fb


rt_base = {
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


#------------------------------------------------------------------------------

if __name__ == '__main__':
    pass    