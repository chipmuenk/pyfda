# -*- coding: utf-8 -*-
"""
Design equiripple-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zeros, poles, gain (zpk) format
Created on Tue Nov 26 12:13:41 2013

@author: Christian Muenker

Expected changes in scipy 0.16:
https://github.com/scipy/scipy/pull/3717
https://github.com/scipy/scipy/issues/2444
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
import scipy.signal as sig
#import numpy as np
#from numpy import log10, pi, arctan
from PyQt4 import QtGui

if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import pyfda_lib

#import filterbroker as fb

# TODO: Order of A_XX is incorrect e.g. for BP
# TODO: Try HP with even order & type = Hilbert
# TODO: Hilbert not working correctly yet

frmt = 'ba' # set output format of filter design routines to 'zpk' or 'ba'
             # currently, only 'ba' is supported for equiripple routines

class equiripple(object):

    info ="""
    Equiripple filter have a constant ripple in pass- and 
    stop band, the tolerance bands are fully used. 
        
    The minimum order to fulfill the target specifications is estimated 
    using one of three algorithms.
    """
    
    def __init__(self):
        self.name = {'equiripple':'Equiripple'}

        # common messages for all man. / min. filter order response types:            
        msg_man = ("Enter desired order, corner frequencies and a weight "
            "value for each band.")
        msg_min = ("Enter the maximum pass band ripple, minimum stop band "
                    "attenuation and the corresponding corner frequencies.")

        # VISIBLE widgets for all man. / min. filter order response types:     
        vis_man = ['fo','fspecs','aspecs'] # manual filter order
        vis_min = ['fo','fspecs','aspecs'] # minimum filter order

        # ENABLED widgets for all man. / min. filter order response types:     
        enb_man = ['fo','fspecs','wspecs'] # manual filter order
        enb_min = ['fo','fspecs','aspecs'] # minimum filter order

        # common parameters for all man. / min. filter order response types:    
        par_man = ['N', 'f_S'] # enabled widget for man. filt. order
        par_min = ['f_S', 'A_PB', 'A_SB'] # enabled widget for min. filt. order

        # Common data for all man. / min. filter order response types:
        # This data is merged with the entries for individual response types 
        # (common data comes first):
        self.com = {"man":{"enb":enb_man, "msg":msg_man, "par": par_man},
                    "min":{"enb":enb_min, "msg":msg_min, "par": par_min}}
        self.ft = 'FIR'
        self.rt = {
            "LP": {"man":{"par":['W_PB','W_SB','F_PB','F_SB','A_PB','A_SB']},
                   "min":{"par":['F_PB','F_SB','W_PB','W_SB']}},
            "HP": {"man":{"par":['W_SB','W_PB','F_SB','F_PB','A_SB','A_PB'],
                          "msg":r"<br /><b>Note:</b> Order needs to be even (type I FIR filters)!"},
                   "min":{"par":['F_SB','F_PB','W_SB','W_PB']}},
            "BP": {"man":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'W_SB','W_PB','W_SB2','A_SB','A_PB','A_SB2']},
                   "min":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2', 
                                 'W_SB', 'W_PB','W_SB2','A_SB2']}},                                 
            "BS": {"man":{"par":['F_PB', 'F_SB', 'F_SB2', 'F_PB2',
                                 'W_PB', 'W_SB', 'W_PB2','A_PB','A_SB','A_PB2'],
                      "msg":r"<br /><b>Note:</b> Order needs to be even (type I FIR filters)!"},
                   "min":{"par":['A_PB2','W_PB','W_SB','W_PB2', 
                                 'F_PB','F_SB','F_SB2','F_PB2']}},
            "HIL": {"man":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'W_SB', 'W_PB', 'W_SB2','A_SB','A_PB','A_SB2']
                                 }}
          #"DIFF":
                   }
        self.info_doc = []
        self.info_doc.append('remez()\n=======')
        self.info_doc.append(sig.remez.__doc__)
    
        #----------------------------------------------------------------------
        # Additional subwidgets
#        self.wdg = {'fo':'combo_equirip_alg'} 
        #----------------------------------------------------------------------
        # Combobox for selecting the algorithm to estimate minimum filter order
#        self.combo_equirip_alg = QtGui.QComboBox()
#        self.combo_equirip_alg.setObjectName('combo_firwin_alg')
#        self.combo_equirip_alg.addItems(['ichige','kaiser','herrmann'])

    def get_params(self, specs):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N     = specs['N'] + 1 # remez algorithms expects number of taps
                                # which is larger by one than the order!!
        self.F_PB  = specs['F_PB'] 
        self.F_SB  = specs['F_SB'] 
        self.F_PB2 = specs['F_PB2']
        self.F_SB2 = specs['F_SB2']
        # remez amplitude specs are linear (not in dBs) and need to be 
        # multiplied by a factor of two to obtain a "tight fit" (why??)
        self.A_PB  = (10.**(specs['A_PB']/20.)-1) / (10**(specs['A_PB']/20.)+1)*2
        self.A_PB2 = (10.**(specs['A_PB2']/20.)-1)/(10**(specs['A_PB2']/20.)+1)*2
        self.A_SB  = 10.**(-specs['A_SB']/20.)
        self.A_SB2 = 10.**(-specs['A_SB2']/20.)

#        self.alg = str(self.combo_equirip_alg.currentText())
        self.alg = 'ichige'

    def save(self, specs, arg):
        """ 
        Convert between poles / zeros / gain, filter coefficients (polynomes) 
        and second-order sections and store all available formats in the passed
        dictionary 'specs'.
        """
        
        pyfda_lib.save_fil(specs, arg, frmt, __name__)

        try: # has the order been calculated by a "min" filter design?
            specs['N'] = self.N-1 # yes, update filterbroker
        except AttributeError:
            pass

    def LPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.remez(self.N,[0, self.F_PB, self.F_SB, 0.5],
               [1, 0], weight = [specs['W_PB'],specs['W_SB']],Hz = 1))

    def LPmin(self, specs):
        self.get_params(specs)
        (self.N, F, A, W) = pyfda_lib.remezord([self.F_PB, self.F_SB], [1, 0], 
            [self.A_PB, self.A_SB], Hz = 1, alg = self.alg)     
        specs['W_PB'] = W[0]
        specs['W_SB'] = W[1]
        self.save(specs, sig.remez(self.N, F, [1, 0], weight = W, Hz = 1))
                
    def HPman(self, specs):
        self.get_params(specs)
#        N = self.oddround(self.N) # enforce odd order 
        self.save(specs, sig.remez(self.N,[0, self.F_SB, self.F_PB, 0.5],
                [0, 1], weight = [specs['W_SB'],specs['W_PB']], Hz = 1))
        
    def HPmin(self, specs):
        self.get_params(specs)
        (N, F, A, W) = pyfda_lib.remezord([self.F_SB, self.F_PB], [0, 1], 
            [self.A_SB, self.A_PB], Hz = 1, alg = self.alg)
        self.N = pyfda_lib.oddround(N)  # enforce odd length = even order
        specs['W_SB'] = W[0]
        specs['W_PB'] = W[1]
        self.save(specs, sig.remez(self.N, F,[0, 1], weight = W, Hz = 1, type = 'bandpass'))

    # For BP and BS, F_PB and F_SB have two elements each
    def BPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.remez(self.N,[0, self.F_SB, self.F_PB, 
                self.F_PB2, self.F_SB2, 0.5],[0, 1, 0], 
                weight = [specs['W_SB'],specs['W_PB'], specs['W_SB2']], Hz = 1))

    def BPmin(self, specs):
        self.get_params(specs)
        (self.N, F, A, W) = pyfda_lib.remezord([self.F_SB, self.F_PB, 
                                self.F_PB2, self.F_SB2], [0, 1, 0], 
            [self.A_SB, self.A_PB, self.A_SB2], Hz = 1, alg = self.alg)
        specs['W_SB']  = W[0]
        specs['W_PB']  = W[1]
        specs['W_SB2'] = W[2]   
        self.save(specs, sig.remez(self.N,F,[0, 1, 0], weight = W, Hz = 1))

    def BSman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.remez(self.N,[0, self.F_PB, self.F_SB, 
                self.F_SB2, self.F_PB2, 0.5],[1, 0, 1], 
                weight = [specs['W_PB'],specs['W_SB'], specs['W_PB2']],Hz = 1))
                
    def BSmin(self, specs):
        self.get_params(specs)
        (N, F, A, W) = pyfda_lib.remezord([self.F_PB, self.F_SB, 
                                self.F_SB2, self.F_PB2], [1, 0, 1], 
            [self.A_PB, self.A_SB, self.A_PB2], Hz = 1, alg = self.alg)
        self.N = pyfda_lib.oddround(N)  # enforce odd length = even order
        specs['W_PB']  = W[0]
        specs['W_SB']  = W[1]
        specs['W_PB2'] = W[2]   
        self.save(specs, sig.remez(self.N,F,[1, 0, 1], weight = W, Hz = 1))

    def HILman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.remez(self.N,[0, self.F_SB, self.F_PB, 
                self.F_PB2, self.F_SB2, 0.5],[0, 1, 0], 
                weight = [specs['W_SB'],specs['W_PB'], specs['W_SB2']], Hz = 1,
                type = 'hilbert'))
                