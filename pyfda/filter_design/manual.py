# -*- coding: utf-8 -*-
"""
Dummy / template file for manual filter designs by entering P/Z or b/a. 
Targets for LP, HP, BP, BS are provided.
Returns nothing.

Attention: 
This class is re-instantiated dynamically everytime the filter design method
is selected, calling the __init__ method.

Version info:   
    1.0: initial working release
    1.1: mark private methods as private
    1.2: new API using fil_save
    1.3: new public methods destruct_UI + construct_UI (no longer called by __init__)    
    1.4: module attribute `filter_classes` contains class name and combo box name
         instead of class attribute `name`


Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals

__version__ = "1.4"

filter_classes = {'Manual_FIR':'Manual', 'Manual_IIR':'Manual'}

FRMT = 'ba' # default output format of filter design routines 'zpk' / 'ba' / 'sos'

class Manual_FIR(object):
    
    def __init__(self):

        # This part contains static information for building the filter tree

        # common messages for all man. / min. filter order response types:
        msg_man = ("Enter filter design using the P/Z or the b/a widget.")

        # VISIBLE widgets for all man. / min. filter order response types:
        vis_man = ['fspecs','tspecs'] # manual filter order

        # DISABLED widgets for all man. / min. filter order response types:
        dis_man = ['fo'] # manual filter order

        # common PARAMETERS for all man. / min. filter order response types:
        par_man = ['f_S']     #  manual filter order

        # Common data for all filter response types:
        # This data is merged with the entries for individual response types
        # (common data comes first):
        self.com = {"man":{"vis":vis_man, "dis":dis_man, "msg":msg_man, "par":par_man}}
                    
        self.ft = 'FIR'
        self.rt = {
            "LP": {"man":{"par":[]}},
            "HP": {"man":{"par":[],
                          "msg":r"<br /><b>Note:</b> Be careful!"}},
            "BP": {"man":{"par":['F_C2']}},
            "BS": {"man":{"par":['F_C2'],
                      "msg":r"<br /><b>Note:</b> Be extra careful!"}},
            "HIL": {"man":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2','A_SB','A_PB','A_SB2']}}
                   }

        
        self.info = """
        Manual entry of filters is great.
        """
        
        #------------------- end of static info for filter tree ---------------

        self.hdl = None
        
        
    def construct_UI(self):
        """
        No UI, nothing to construct here
        """
        pass


            
    def destruct_UI(self):
        """
        No UI, nothing to destruct here
        """
        pass


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

#############################################################################    
class Manual_IIR(object):
    
    def __init__(self):

        # This part contains static information for building the filter tree

        # common messages for all man. / min. filter order response types:
        msg_man = ("Enter filter design using the P/Z or the b/a widget.")

        # VISIBLE widgets for all man. / min. filter order response types:
        vis_man = ['fspecs','tspecs'] # manual filter order

        # DISABLED widgets for all man. / min. filter order response types:
        dis_man = [] # manual filter order

        # common PARAMETERS for all man. / min. filter order response types:
        par_man = ['f_S']     #  manual filter order

        # Common data for all filter response types:
        # This data is merged with the entries for individual response types
        # (common data comes first):
        self.com = {"man":{"vis":vis_man, "dis":dis_man, "msg":msg_man, "par":par_man}}
                    
        self.ft = 'IIR'
        self.rt = {
            "LP": {"man":{"par":[]}},
            "HP": {"man":{"par":[],
                          "msg":r"<br /><b>Note:</b> Be careful!"}},
            "BP": {"man":{"par":['F_C2']}},
            "BS": {"man":{"par":['F_C2'],
                      "msg":r"<br /><b>Note:</b> Be extra careful!"}},
            "HIL": {"man":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2','A_SB','A_PB','A_SB2']}}
                   }
        
        self.info = """
        Manual entry of filters is great.
        """
        self.info_doc = []
        self.info_doc.append('manual()\n========')
        
        #------------------- end of static info for filter tree ---------------
        
        self.hdl = None       
        
    def construct_UI(self):
        """
        No UI, nothing to construct here
        """
        pass

            
    def destruct_UI(self):
        """
        No UI, nothing to destruct here
        """
        pass


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


#------------------------------------------------------------------------------

if __name__ == '__main__':
    filt = Manual_IIR()    # instantiate filter
    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][FRMT]) # return results in default format
