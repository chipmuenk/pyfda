# -*- coding: utf-8 -*-
"""
Design windowed FIR filters (LP, HP, BP, BS) with fixed order, return
the filter design in zeros, poles, gain (zpk) format
Created on Tue Nov 26 12:13:41 2013

@author: Christian Muenker

Expected changes in scipy 0.16:
https://github.com/scipy/scipy/pull/3717
https://github.com/scipy/scipy/issues/2444
"""
from __future__ import print_function, division, unicode_literals
from importlib import import_module
#import scipy
import scipy.signal as sig
import numpy as np
from numpy import log10, pi, arctan
from PyQt4 import QtGui
import pyfda_lib

#import filterbroker as fb

# TODO: Order of A_XX is incorrect e.g. for BP
# TODO: Hilbert not working correctly yet
# TODO: Windows with parameters are missing

frmt = 'ba' # set output format of filter design routines to 'zpk' or 'ba'
             # currently, only 'ba' is supported for equiripple routines

class firwin(object):
    
    def __init__(self):
        self.name = {'firwin':'Windowed FIR'}
#        print(scipy.signal.windows.boxcar.__doc__)

        # common messages for all man. / min. filter order response types:            
        msg_man = (r"Enter desired order and corner frequencies. <br />"
                    "<b>Note: </b> Corner frequencies are <b>-6 dB</b> "
                    " frequencies.")
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
            "LP": {"man":{"par":['F_PB','F_SB','A_PB','A_SB']},
                   "min":{"par":['F_PB','F_SB']}},
            "HP": {"man":{"par":['F_SB','F_PB','A_SB','A_PB'],
                          "msg":r"<br /><b>Note:</b> Order needs to be even (type I FIR filters)!"},
                   "min":{"par":['F_SB','F_PB']}},
            "BP": {"man":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'A_SB','A_PB','A_SB2']},
                   "min":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2', 
                                 'A_SB2']}},                                 
            "BS": {"man":{"par":['F_PB', 'F_SB', 'F_SB2', 'F_PB2',
                                 'A_PB','A_SB','A_PB2'],
                      "msg":r"<br /><b>Note:</b> Order needs to be even (type I FIR filters)!"},
                   "min":{"par":['A_PB2','F_PB','F_SB','F_SB2','F_PB2']}}
#            "HIL": {"man":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2','A_SB','A_PB','A_SB2']}}
          #"DIFF":
                   }
        self.info = """Windowed FIR filters are designed by truncating the
        infinite impulse response of an ideal filter with a window function.
        The kind of selected window has great influence on ripple etc. of the
        resulting filter.
        """
        self.info_doc = []
        self.info_doc.append('firwin()\n========')
        self.info_doc.append(sig.firwin.__doc__)
#        self.info_doc.append(getattr(sig.windows, self.firWindow + '__doc__'))

        # Additional subwidgets needed for design:
        # These subwidgets are instantiated where needed using the handle to 
        # the filter object

        self.wdg = {'fo':'combo_firwin_alg', 'sf':'combo_firwin_win'} 
        # Combobox for selecting the algorithm to estimate minimum filter order
        self.combo_firwin_alg = QtGui.QComboBox()
        self.combo_firwin_alg.setObjectName('combo_firwin_alg')
        self.combo_firwin_alg.addItems(['ichige','kaiser','herrmann'])
        
        

        # Combobox for selecting the window used for filter design
        self.combo_firwin_win = QtGui.QComboBox()
        self.combo_firwin_win.setObjectName('combo_firwin_win')
        
        #TODO: Eigennamen mit Großbuchstaben beginnen?
        windows = ['boxcar','triang','blackman','hamming','hann','bartlett', 
                   'flattop', 'parzen', 'bohman', 'blackmanharris', 'nuttall',
                   'barthann']
                   
        #kaiser (needs beta), gaussian (needs std), general_gaussian 
        #(needs power, width), slepian (needs width), chebwin (needs attenuation)
        self.combo_firwin_win.addItems(windows)
        self.combo_firwin_win.setCurrentIndex(0)
        
        """EDIT WinMic"""
        #groeße der ComboBoxen dynamisch.
        #koennen aber durch ein Layout auf fixer groeße gehalten werden
        self.combo_firwin_alg.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.combo_firwin_win.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)        
        """END"""
        
        self.combo_firwin_win.activated.connect(self.updateWindow)
        self.combo_firwin_alg.activated.connect(self.updateWindow)

        self.updateWindow()
        
    def updateWindow(self):
        self.firWindow = str(self.combo_firwin_win.currentText())
        self.alg = str(self.combo_firwin_alg.currentText())
        print(self.firWindow)

#        mod = import_module(scipy.signal) # doesn't work
#        print(sig.boxcar.__doc__) # this works
#        met = getattr(sig.boxcar, '.__doc__'  )



#        print(type(self.firWindow))
#        self.firWindow = 'hann'
        #self.alg = self.combo_firwin_alg.currentText()


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

#        self.alg = 'ichige' # algorithm for determining the minimum order
#        self.alg = self.combo_firwin_alg.currentText()
        print("===== firwin ====\n", self.alg)
        print(self.firWindow)

    def save(self, specs, arg):
        """ 
        Convert between poles / zeros / gain, filter coefficients (polynomes) 
        and second-order sections and store all available formats in the passed
        dictionary 'specs'.
        """
        pyfda_lib.save_fil(specs, arg, frmt, __name__)

        try: # has the order been calculated by a "min" filter design?
            specs['N'] = self.N - 1 # yes, update filterbroker
        except AttributeError:
            pass

    def LPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.firwin(self.N, self.F_PB, 
                                    window = self.firWindow, nyq = 0.5))

    def LPmin(self, specs):
        self.get_params(specs)
        (self.N, F, A, W) = pyfda_lib.remezord([self.F_PB, self.F_SB], [1, 0], 
            [self.A_PB, self.A_SB], Hz = 1, alg = self.alg)     
        self.save(specs, sig.firwin(self.N, self.F_PB, window = self.firWindow, nyq = 0.5))
                
    def HPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.firwin(self.N, self.F_PB, window = self.firWindow,
                                    pass_zero=False, nyq = 0.5))
        
    def HPmin(self, specs):
        self.get_params(specs)
        (N, F, A, W) = pyfda_lib.remezord([self.F_SB, self.F_PB], [0, 1], 
            [self.A_SB, self.A_PB], Hz = 1, alg = self.alg)
        self.N = pyfda_lib.oddround(N)  # enforce odd length = even order
        self.save(specs, sig.firwin(self.N, self.F_PB, window = self.firWindow,
                                    pass_zero=False, nyq = 0.5))
    # For BP and BS, F_PB and F_SB have two elements each
    def BPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.firwin(self.N, [self.F_PB, self.F_PB2], 
                                    window = self.firWindow, pass_zero=False))
        
    def BPmin(self, specs):
        self.get_params(specs)
        (self.N, F, A, W) = pyfda_lib.remezord([self.F_SB, self.F_PB, 
                                self.F_PB2, self.F_SB2], [0, 1, 0], 
            [self.A_SB, self.A_PB, self.A_SB2], Hz = 1, alg = self.alg)
        self.save(specs, sig.firwin(self.N, [self.F_PB, self.F_PB2], 
                            window = self.firWindow, pass_zero=False, nyq = 0.5))

    def BSman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.firwin(self.N, [self.F_SB, self.F_SB2], 
                            window = self.firWindow, pass_zero=True, nyq = 0.5))
                
    def BSmin(self, specs):
        self.get_params(specs)
        (N, F, A, W) = pyfda_lib.remezord([self.F_PB, self.F_SB, 
                                self.F_SB2, self.F_PB2], [1, 0, 1], 
            [self.A_PB, self.A_SB, self.A_PB2], Hz = 1, alg = self.alg)
        self.N = pyfda_lib.oddround(N)  # enforce odd length = even order
        self.save(specs, sig.firwin(self.N, [self.F_SB, self.F_SB2], 
                            window = self.firWindow, pass_zero=True, nyq = 0.5))

