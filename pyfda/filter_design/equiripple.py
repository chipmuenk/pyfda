# -*- coding: utf-8 -*-
"""
Design equiripple-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in coefficients format ('ba')

Attention: 
This class is re-instantiated dynamically everytime the filter design method
is selected, calling the __init__ method.

Version info:   
    1.0: initial working release
    1.1: mark private methods as private
    1.2: new API using fil_save
    
Author: Christian Muenker 2014 - 2016
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import scipy.signal as sig
from PyQt4 import QtGui
import numpy as np

import pyfda.filterbroker as fb
from pyfda.pyfda_lib import fil_save, remezord, round_odd, ceil_even


# TODO: min order for Hilbert & Differentiator
# TODO: changing grid_density does not trigger sigSpecsChanged
# TODO: implement check-box for auto grid_density, using (lgrid*N)/(2*bw)
# TODO: fails (just as Matlab does) when manual order is too LARGE, remez would
#       need an update, see: Emmanouil Z. Psarakis and George V. Moustakides,
#         "A Robust Initialization Scheme for the Remez Exchange Algorithm",
#           IEEE SIGNAL PROCESSING LETTERS, VOL. 10, NO. 1, JANUARY 2003  

__version__ = "1.2"

frmt = 'ba' # output format of filter design routines 'zpk' / 'ba' / 'sos'
            # currently, only 'ba' is supported for equiripple routines

class equiripple(object):

    info ="""
**Equiripple filters**

have a constant ripple in pass- and
stop band, the tolerance bands are fully used. 

The minimum order to fulfill the target specifications is estimated
using Ichige's algorithm.

**Design routines:**

``scipy.signal.remez()``\n
``pyfda_lib.remezord()``
    """

    def __init__(self):
        self.name = {'equiripple':'Equiripple'}

        # common messages for all man. / min. filter order response types:
        msg_man = ("Enter desired filter order <b><i>N</i></b>, corner "
        "frequencies of pass and stop band(s), <b><i>F<sub>PB</sub></i></b>"
        "&nbsp; and <b><i>F<sub>SB</sub></i></b>, and a weight "
        "value <b><i>W</i></b>&nbsp; for each band.")
        msg_min = ("Enter the maximum pass band ripple <b><i>A<sub>PB</sub></i></b>, "
                    "minimum stop band attenuation <b><i>A<sub>SB</sub></i></b> "
                    "and the corresponding corner frequencies of pass and "
                    "stop band(s), <b><i>F<sub>PB</sub></i></b>&nbsp; and "
                    "<b><i>F<sub>SB</sub></i></b> .")

        # VISIBLE widgets for all man. / min. filter order response types:
        vis_man = ['fo','wspecs', 'tspecs'] # manual filter order
        vis_min = ['fo','wspecs', 'tspecs'] # minimum filter order

        # DISABLED widgets for all man. / min. filter order response types:
        dis_man = [] # manual filter order
        dis_min = ['wspecs'] # minimum filter order

        # common PARAMETERS for all man. / min. filter order response types:
        par_man = ['N', 'f_S'] # manual filter order
        par_min = ['f_S', 'A_PB', 'A_SB'] # minimum filter order

        # Common data for all man. / min. filter order response types:
        # This data is merged with the entries for individual response types
        # (common data comes first):
        self.com = {"man":{"vis":vis_man, "dis":dis_man, "msg":msg_man, "par": par_man},
                    "min":{"vis":vis_min, "dis":dis_min, "msg":msg_min, "par": par_min}}
        self.ft = 'FIR'
        self.rt = {
            "LP": {"man":{"par":['W_PB','W_SB','F_PB','F_SB','A_PB','A_SB']},
                   "min":{"par":['F_PB','F_SB','W_PB','W_SB']}},
            "HP": {"man":{"par":['W_SB','W_PB','F_SB','F_PB','A_SB','A_PB']},
                   "min":{"par":['F_SB','F_PB','W_SB','W_PB']}},
            "BP": {"man":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'W_SB','W_PB','W_SB2','A_SB','A_PB','A_SB2']},
                   "min":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'W_SB', 'W_PB','W_SB2','A_SB2']}},
            "BS": {"man":{"par":['F_PB', 'F_SB', 'F_SB2', 'F_PB2',
                                 'W_PB', 'W_SB', 'W_PB2','A_PB','A_SB','A_PB2'],
                      "msg":r"<br /><b>Note:</b> Order needs to be odd for a bandstop!"},
                   "min":{"par":['A_PB2','W_PB','W_SB','W_PB2',
                                 'F_PB','F_SB','F_SB2','F_PB2']}},
            "HIL": {"man":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'W_SB', 'W_PB', 'W_SB2'],
                                 "vis":["fspecs"], }},
            "DIFF": {"man":{"par":['F_PB', 'W_PB'], "vis":["fspecs"]}}
                   }
        self.info_doc = []
        self.info_doc.append('remez()\n=======')
        self.info_doc.append(sig.remez.__doc__)
        self.info_doc.append('remezord()\n==========')
        self.info_doc.append(remezord.__doc__)
        # additional dynamic widgets that need to be set in the main widgets
        self.wdg = {'sf':'wdg_remez'}
        
        self.hdl = None
        #----------------------------------------------------------------------

        self._init_UI()


    def _init_UI(self):
        """
        Create additional subwidget(s) needed for filter design with the 
        names given in self.wdg :
        These subwidgets are instantiated dynamically when needed in 
        input_filter.py using the handle to the filter instance, fb.fil_inst.
        """

        self.lbl_remez_1 = QtGui.QLabel("Grid Density")
        self.lbl_remez_1.setObjectName('wdg_lbl_remez_1')
        self.led_remez_1 = QtGui.QLineEdit()
        self.led_remez_1.setText("16")
        self.led_remez_1.setObjectName('wdg_led_remez_1')
        self.led_remez_1.setToolTip("Set number of frequency grid points for ")
               
        # Widget containing all subwidgets (cmbBoxes, Labels, lineEdits)        
        self.wdg_remez = QtGui.QWidget()
        self.wdg_remez.setObjectName('wdg_remez')
        self.layHWin = QtGui.QHBoxLayout()
        self.layHWin.setObjectName('wdg_layGWin')
        self.layHWin.addWidget(self.lbl_remez_1)
        self.layHWin.addWidget(self.led_remez_1)
        self.layHWin.setContentsMargins(0,0,0,0)
        self.wdg_remez.setLayout(self.layHWin)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.led_remez_1.editingFinished.connect(self._update_UI)
        # fires when edited line looses focus or when RETURN is pressed
        #----------------------------------------------------------------------

        self._load_entries() # get initial / last setting from dictionary
        self._update_UI()
        
    def _update_UI(self):
        """
        Update UI when line edit field is changed (here, only the text is read
        and converted to integer.)
        """
        self.grid_density = int(abs(round(float(self.led_remez_1.text()))))
        self.led_remez_1.setText(str(self.grid_density))
        """
        Store parameter settings in filter dictionary.
        """
        fb.fil[0].update({'wdg_dyn':{'grid_density':self.grid_density}})

    def destruct_UI(self):
        """
        - Disconnect all signal-slot connections to avoid crashes upon exit
        - Delete dynamic widgets
        """
        self.led_remez_1.editingFinished.disconnect()


        
    def _load_entries(self):
        """
        Reload parameter(s) from filter dictionary and set UI elements 
        when filter is loaded from disk.
        """
        try:
            dyn_wdg_par = fb.fil[0]['wdg_dyn']
            if 'grid_density' in dyn_wdg_par:
                self.grid_density = dyn_wdg_par['grid_density']
                self.led_remez_1.setText(str(self.grid_density))
        except KeyError as e:
            print("Key Error:",e)


#    def _store_entries(self):
#        """
#        Store parameter settings in filter dictionary.
#        """
#        fb.fil[0].update({'wdg_dyn':{'grid_density':self.grid_density}})



    def _get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N     = fil_dict['N'] + 1  # remez algorithms expects number of taps
                                        # which is larger by one than the order!!
        self.F_PB  = fil_dict['F_PB']
        self.F_SB  = fil_dict['F_SB']
        self.F_PB2 = fil_dict['F_PB2']
        self.F_SB2 = fil_dict['F_SB2']
        # remez amplitude specs are linear (not in dBs)
        self.A_PB  = fil_dict['A_PB']
        self.A_PB2 = fil_dict['A_PB2']
        self.A_SB  = fil_dict['A_SB']
        self.A_SB2 = fil_dict['A_SB2']
        
        self.alg = 'ichige'
        

    def _save(self, fil_dict, arg):
        """
        Convert between poles / zeros / gain, filter coefficients (polynomes)
        and second-order sections and store all available formats in the passed
        dictionary 'fil_dict'.
        """

        fil_save(fil_dict, arg, frmt, __name__)

        if str(fil_dict['fo']) == 'min': 
            fil_dict['N'] = self.N - 1  # yes, update filterbroker


    def LPman(self, fil_dict):
        self._get_params(fil_dict)
        self._save(fil_dict, 
                  sig.remez(self.N,[0, self.F_PB, self.F_SB, 0.5], [1, 0],
                        weight = [fil_dict['W_PB'],fil_dict['W_SB']], Hz = 1,
                        grid_density = self.grid_density))

    def LPmin(self, fil_dict):
        self._get_params(fil_dict)
        (self.N, F, A, W) = remezord([self.F_PB, self.F_SB], [1, 0],
            [self.A_PB, self.A_SB], Hz = 1, alg = self.alg)
        fil_dict['W_PB'] = W[0]
        fil_dict['W_SB'] = W[1]
        self._save(fil_dict, sig.remez(self.N, F, [1, 0], weight = W, Hz = 1,
                        grid_density = self.grid_density))


    def HPman(self, fil_dict):
        self._get_params(fil_dict)
        if (self.N % 2 == 0): # even order, use odd symmetry (type III)
            self._save(fil_dict, 
                  sig.remez(self.N,[0, self.F_SB, self.F_PB, 0.5], [0, 1],
                        weight = [fil_dict['W_SB'],fil_dict['W_PB']], Hz = 1,
                        type = 'hilbert', grid_density = self.grid_density))
        else: # odd order, 
            self._save(fil_dict, 
                  sig.remez(self.N,[0, self.F_SB, self.F_PB, 0.5], [0, 1],
                        weight = [fil_dict['W_SB'],fil_dict['W_PB']], Hz = 1,
                        type = 'bandpass', grid_density = self.grid_density))

    def HPmin(self, fil_dict):
        self._get_params(fil_dict)
        (self.N, F, A, W) = remezord([self.F_SB, self.F_PB], [0, 1],
            [self.A_SB, self.A_PB], Hz = 1, alg = self.alg)
#        self.N = ceil_odd(N)  # enforce odd order
        fil_dict['W_SB'] = W[0]
        fil_dict['W_PB'] = W[1]
        if (self.N % 2 == 0): # even order
            self._save(fil_dict, sig.remez(self.N, F,[0, 1], weight = W, Hz = 1, 
                        type = 'hilbert', grid_density = self.grid_density))
        else:
            self._save(fil_dict, sig.remez(self.N, F,[0, 1], weight = W, Hz = 1, 
                        type = 'bandpass', grid_density = self.grid_density))

    # For BP and BS, F_PB and F_SB have two elements each
    def BPman(self, fil_dict):
        self._get_params(fil_dict)
        self._save(fil_dict,
                 sig.remez(self.N,[0, self.F_SB, self.F_PB,
                self.F_PB2, self.F_SB2, 0.5],[0, 1, 0],
                weight = [fil_dict['W_SB'],fil_dict['W_PB'], fil_dict['W_SB2']],
                Hz = 1, grid_density = self.grid_density))

    def BPmin(self, fil_dict):
        self._get_params(fil_dict)
        (self.N, F, A, W) = remezord([self.F_SB, self.F_PB,
                                self.F_PB2, self.F_SB2], [0, 1, 0],
            [self.A_SB, self.A_PB, self.A_SB2], Hz = 1, alg = self.alg)
        fil_dict['W_SB']  = W[0]
        fil_dict['W_PB']  = W[1]
        fil_dict['W_SB2'] = W[2]
        self._save(fil_dict, sig.remez(self.N,F,[0, 1, 0], weight = W, Hz = 1,
                                      grid_density = self.grid_density))

    def BSman(self, fil_dict):
        self._get_params(fil_dict)
        self.N = round_odd(self.N) # enforce odd order
        self._save(fil_dict, sig.remez(self.N,[0, self.F_PB, self.F_SB,
            self.F_SB2, self.F_PB2, 0.5],[1, 0, 1],
            weight = [fil_dict['W_PB'],fil_dict['W_SB'], fil_dict['W_PB2']],
            Hz = 1, grid_density = self.grid_density))

    def BSmin(self, fil_dict):
        self._get_params(fil_dict)
        (N, F, A, W) = remezord([self.F_PB, self.F_SB,
                                self.F_SB2, self.F_PB2], [1, 0, 1],
            [self.A_PB, self.A_SB, self.A_PB2], Hz = 1, alg = self.alg)
        self.N = round_odd(N)  # enforce odd order
        fil_dict['W_PB']  = W[0]
        fil_dict['W_SB']  = W[1]
        fil_dict['W_PB2'] = W[2]
        self._save(fil_dict, sig.remez(self.N,F,[1, 0, 1], weight = W, Hz = 1,
                                      grid_density = self.grid_density))

    def HILman(self, fil_dict):
        self._get_params(fil_dict)
        self._save(fil_dict, sig.remez(self.N,[0, self.F_SB, self.F_PB,
                self.F_PB2, self.F_SB2, 0.5],[0, 1, 0],
                weight = [fil_dict['W_SB'],fil_dict['W_PB'], fil_dict['W_SB2']],
                Hz = 1, type = 'hilbert', grid_density = self.grid_density))

    def DIFFman(self, fil_dict):
        self._get_params(fil_dict)
        self.N = ceil_even(self.N) # enforce even order
        self._save(fil_dict, sig.remez(self.N,[0, self.F_PB],[np.pi*fil_dict['W_PB']],
                Hz = 1, type = 'differentiator', grid_density = self.grid_density))


#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    filt = equiripple()        # instantiate filter
    grid_density = getattr(filt, filt.wdg['sf'])

    layVDynWdg = QtGui.QVBoxLayout()
    layVDynWdg.addWidget(grid_density, stretch = 1)
    
    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][frmt]) # return results in default format

    frmDynWdg = QtGui.QFrame()
    frmDynWdg.setLayout(layVDynWdg)
    
    layVAllWdg = QtGui.QVBoxLayout()
    layVAllWdg.addWidget(frmDynWdg)

    frmMain = QtGui.QFrame()
    frmMain.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
    frmMain.setLayout(layVAllWdg)    

    form = frmMain

    form.show()
    

    app.exec_()
    #------------------------------------------------------------------------------

