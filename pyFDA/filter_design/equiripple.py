# -*- coding: utf-8 -*-
"""
Design equiripple-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in coefficients format ('ba')

Attention: 
This class is re-instantiated dynamically everytime the filter design method
is selected, calling the __init__ method.
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import scipy.signal as sig
from PyQt4 import QtGui
import numpy as np

if __name__ == "__main__":
    import sys, os
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb
import pyfda_lib


# TODO: min order for Hilbert & Differentiator
# TODO: implement check-box for auto grid_density, using (lgrid*N)/(2*bw)
# TODO: fails (just as Matlab does) when manual order is too LARGE, remez would
#       need an update, see: Emmanouil Z. Psarakis and George V. Moustakides,
#         "A Robust Initialization Scheme for the Remez Exchange Algorithm",
#           IEEE SIGNAL PROCESSING LETTERS, VOL. 10, NO. 1, JANUARY 2003  

frmt = 'ba' #output format of filter design routines 'zpk' / 'ba' / 'sos'
             # currently, only 'ba' is supported for equiripple routines

class equiripple(object):

    info ="""
    Equiripple filter have a constant ripple in pass- and
    stop band, the tolerance bands are fully used.

    The minimum order to fulfill the target specifications is estimated
    using Ichige's algorithm.
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
                                 'W_SB', 'W_PB', 'W_SB2','A_SB','A_PB','A_SB2']}},
            "DIFF": {"man":{"par":['F_PB', 'W_PB']}}
                   }
        self.info_doc = []
        self.info_doc.append('remez()\n=======')
        self.info_doc.append(sig.remez.__doc__)

        # additional dynamic widgets that need to be set in the main widgets
        self.wdg = {'sf':'wdg_remez'}
        #----------------------------------------------------------------------
        self.initUI()


    def initUI(self):
        """
        Create additional subwidget(s) needed for filter design with the 
        names given in self.wdg :
        These subwidgets are instantiated dynamically when needed in 
        input_filter.py using the handle to the filter object, fb.filObj .
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
        self.led_remez_1.editingFinished.connect(self.updateUI)
        #----------------------------------------------------------------------

        self.loadEntries() # get initial / last setting from dictionary
        self.updateUI()
        
    def updateUI(self):
        """
        Update UI when line edit field is changed (here, only the text is read
        and converted to integer.)
        """
        self.grid_density = abs(round(float(self.led_remez_1.text())))
        self.led_remez_1.setText(str(self.grid_density))
        
    def loadEntries(self):
        """
        Reload parameter(s) from filter dictionary and set UI elements 
        when filter is loaded from disk.
        """
        try:
            dyn_wdg_par = fb.fil[0]['wdg_dyn']
            if 'grid_density' in dyn_wdg_par:
                self.led_remez_1.setText(str(dyn_wdg_par['grid_density']))
        except KeyError as e:
            print("Key Error:",e)


    def storeEntries(self):
        """
        Store parameter settings in filter dictionary.
        """
        fb.fil[0].update({'wdg_dyn':{'grid_density':self.grid_density}})



    def get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N     = fil_dict['N'] # remez algorithms expects number of taps
                                # which is larger by one than the order!!
        self.F_PB  = fil_dict['F_PB']
        self.F_SB  = fil_dict['F_SB']
        self.F_PB2 = fil_dict['F_PB2']
        self.F_SB2 = fil_dict['F_SB2']
        # remez amplitude specs are linear (not in dBs) and need to be
        # multiplied by a factor of two to obtain a "tight fit" (why??)
        self.A_PB  = (10.**(fil_dict['A_PB']/20.)-1) / (10**(fil_dict['A_PB']/20.)+1)*2
        self.A_PB2 = (10.**(fil_dict['A_PB2']/20.)-1)/(10**(fil_dict['A_PB2']/20.)+1)*2
        self.A_SB  = 10.**(-fil_dict['A_SB']/20.)
        self.A_SB2 = 10.**(-fil_dict['A_SB2']/20.)

        self.alg = 'ichige'
#        print("Ellip: F_PB - F_SB - F_SB2 - P_PB2\n", self.F_PB, self.F_SB, self.F_SB2, self.F_PB2 )


    def save(self, fil_dict, arg):
        """
        Convert between poles / zeros / gain, filter coefficients (polynomes)
        and second-order sections and store all available formats in the passed
        dictionary 'fil_dict'.
        """

        pyfda_lib.save_fil(fil_dict, arg, frmt, __name__)

        try: # has the order been calculated by a "min" filter design?
            fil_dict['N'] = self.N  # yes, update filterbroker
        except AttributeError:
            pass

    def LPman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, 
                  sig.remez(self.N,[0, self.F_PB, self.F_SB, 0.5], [1, 0],
                        weight = [fil_dict['W_PB'],fil_dict['W_SB']], Hz = 1,
                        grid_density = self.grid_density))

    def LPmin(self, fil_dict):
        self.get_params(fil_dict)
        (self.N, F, A, W) = pyfda_lib.remezord([self.F_PB, self.F_SB], [1, 0],
            [self.A_PB, self.A_SB], Hz = 1, alg = self.alg)
        fil_dict['W_PB'] = W[0]
        fil_dict['W_SB'] = W[1]
        self.save(fil_dict, sig.remez(self.N, F, [1, 0], weight = W, Hz = 1,
                        grid_density = self.grid_density))


    def HPman(self, fil_dict):
        self.get_params(fil_dict)
        if (self.N % 2 == 0): # even order, use odd symmetry (type III)
            self.save(fil_dict, 
                  sig.remez(self.N,[0, self.F_SB, self.F_PB, 0.5], [0, 1],
                        weight = [fil_dict['W_SB'],fil_dict['W_PB']], Hz = 1,
                        type = 'hilbert', grid_density = self.grid_density))
        else: # odd order, 
            self.save(fil_dict, 
                  sig.remez(self.N,[0, self.F_SB, self.F_PB, 0.5], [0, 1],
                        weight = [fil_dict['W_SB'],fil_dict['W_PB']], Hz = 1,
                        type = 'bandpass', grid_density = self.grid_density))

    def HPmin(self, fil_dict):
        self.get_params(fil_dict)
        (self.N, F, A, W) = pyfda_lib.remezord([self.F_SB, self.F_PB], [0, 1],
            [self.A_SB, self.A_PB], Hz = 1, alg = self.alg)
#        self.N = pyfda_lib.ceil_odd(N)  # enforce odd order
        fil_dict['W_SB'] = W[0]
        fil_dict['W_PB'] = W[1]
        if (self.N % 2 == 0): # even order
            self.save(fil_dict, sig.remez(self.N, F,[0, 1], weight = W, Hz = 1, 
                        type = 'hilbert', grid_density = self.grid_density))
        else:
            self.save(fil_dict, sig.remez(self.N, F,[0, 1], weight = W, Hz = 1, 
                        type = 'bandpass', grid_density = self.grid_density))

    # For BP and BS, F_PB and F_SB have two elements each
    def BPman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict,
                 sig.remez(self.N,[0, self.F_SB, self.F_PB,
                self.F_PB2, self.F_SB2, 0.5],[0, 1, 0],
                weight = [fil_dict['W_SB'],fil_dict['W_PB'], fil_dict['W_SB2']],
                Hz = 1, grid_density = self.grid_density))

    def BPmin(self, fil_dict):
        self.get_params(fil_dict)
        (self.N, F, A, W) = pyfda_lib.remezord([self.F_SB, self.F_PB,
                                self.F_PB2, self.F_SB2], [0, 1, 0],
            [self.A_SB, self.A_PB, self.A_SB2], Hz = 1, alg = self.alg)
        fil_dict['W_SB']  = W[0]
        fil_dict['W_PB']  = W[1]
        fil_dict['W_SB2'] = W[2]
        self.save(fil_dict, sig.remez(self.N,F,[0, 1, 0], weight = W, Hz = 1,
                                      grid_density = self.grid_density))

    def BSman(self, fil_dict):
        self.get_params(fil_dict)
#        self.N = pyfda_lib.ceil_odd(self.N) # enforce odd order
        self.save(fil_dict, sig.remez(self.N,[0, self.F_PB, self.F_SB,
            self.F_SB2, self.F_PB2, 0.5],[1, 0, 1],
            weight = [fil_dict['W_PB'],fil_dict['W_SB'], fil_dict['W_PB2']],
            Hz = 1, grid_density = self.grid_density))

    def BSmin(self, fil_dict):
        self.get_params(fil_dict)
        (N, F, A, W) = pyfda_lib.remezord([self.F_PB, self.F_SB,
                                self.F_SB2, self.F_PB2], [1, 0, 1],
            [self.A_PB, self.A_SB, self.A_PB2], Hz = 1, alg = self.alg)
        self.N = pyfda_lib.ceil_odd(N)  # enforce odd order
        fil_dict['W_PB']  = W[0]
        fil_dict['W_SB']  = W[1]
        fil_dict['W_PB2'] = W[2]
        self.save(fil_dict, sig.remez(self.N,F,[1, 0, 1], weight = W, Hz = 1,
                                      grid_density = self.grid_density))

    def HILman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.remez(self.N,[0, self.F_SB, self.F_PB,
                self.F_PB2, self.F_SB2, 0.5],[0, 1, 0],
                weight = [fil_dict['W_SB'],fil_dict['W_PB'], fil_dict['W_SB2']],
                Hz = 1, type = 'hilbert', grid_density = self.grid_density))

    def DIFFman(self, fil_dict):
        self.get_params(fil_dict)
        self.N = pyfda_lib.ceil_even(self.N) # enforce even order
        self.save(fil_dict, sig.remez(self.N,[0, self.F_PB],[np.pi*fil_dict['W_PB']],
                Hz = 1, type = 'differentiator', grid_density = self.grid_density))


#------------------------------------------------------------------------------

if __name__ == '__main__':
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

