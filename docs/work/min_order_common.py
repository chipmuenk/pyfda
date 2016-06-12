# -*- coding: utf-8 -*-
"""
Common design parameters for minimum order design methods

@author: Christian Muenker

"""
from __future__ import print_function, division, unicode_literals
#from importlib import import_module

#import filterbroker as fb

class min_order_common(object):
    
    def __init__(self):
        self.name = {'common':'Common filter params'}
        # message for min. filter order response types:            
        msg_min = ("Enter the maximum pass band ripple, minimum stop band "
                    "attenuation and the corresponding corner frequencies.")

        # VISIBLE widgets for all man. / min. filter order response types:     
        vis_min = ['fo','fspecs','aspecs'] # minimum filter order

        # ENABLED widgets for all man. / min. filter order response types:     
        enb_min = ['fo','fspecs','aspecs'] # minimum filter order

        # common parameters for all man. / min. filter order response types:    
        par_min = ['f_S', 'A_PB', 'A_SB'] # enabled widget for min. filt. order

        # Common data for all man. / min. filter order response types:
        # This data is merged with the entries for individual response types 
        # (common data comes first):
        self.com = {"min":{"enb":enb_min, "msg":msg_min, "par": par_min}}
        self.rt = {
            "LP": {"min":{"par":['f_S','A_PB','A_SB','F_PB','F_SB']}},
            "HP": {"min":{"par":['f_S','A_PB','A_SB','F_SB','F_PB']}},
            "BP": {"min":{"par":['f_S','A_PB','A_SB','A_SB2',
                                       'F_SB','F_PB','F_PB2','F_SB2']}},                                 
            "BS": {"min":{"par":['f_S','A_PB','A_SB','A_PB2',
                                       'F_PB','F_SB','F_SB2','F_PB2']}}
#            "HIL": {"man":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2','A_SB','A_PB','A_SB2']}}
          #"DIFF":
                   }

