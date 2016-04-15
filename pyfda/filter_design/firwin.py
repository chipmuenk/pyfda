# -*- coding: utf-8 -*-
"""
Design windowed FIR filters (LP, HP, BP, BS) with fixed order, return
the filter design in coefficient ('ba') format

Attention: 
This class is re-instantiated dynamically everytime the filter design method
is selected, calling the __init__ method.

Version info:   
    1.0: initial working release
    1.1: mark private methods as private
    1.2: new API using fil_save


Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals
import numpy as np
import scipy.signal as sig
from importlib import import_module
import inspect
from PyQt4 import QtGui, QtCore

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import fil_save, remezord, round_odd


# TODO: Hilbert, differentiator, multiband are missing
# TODO: Use kaiserord, kaiser_beta & kaiser_atten to calculate params for 
#       kaiser window
# TODO: Improve calculation of F_C and F_C2 using the weights
# TODO: Automatic setting of density factor for remez calculation? 
#       Automatic switching to Kaiser / Hermann?
# TODO: Parameters for windows are not stored in fil_dict?

__version__ = "1.2"

FRMT = 'ba' # output format of filter design routines 'zpk' / 'ba' / 'sos'
            # currently, only 'ba' is supported for firwin routines

class firwin(object):

    def __init__(self):
        
        # This part contains static information for building the filter tree
        self.name = {'firwin':'Windowed FIR'}

        # common messages for all man. / min. filter order response types:
        msg_man = (r"Enter desired filter order <b><i>N</i></b> and <b>-6 dB</b> pass band corner "
                    "frequency(ies) <b><i>F<sub>C</sub></i></b> .")
        msg_min = ("Enter the maximum pass band ripple <b><i>A<sub>PB</sub></i></b>, "
                "minimum stop band attenuation <b><i>A<sub>SB</sub></i></b> "
                "and the corresponding frequencies <b><i>F<sub>PB</sub></i></b>"
                "&nbsp; and <b><i>F<sub>SB</sub></i></b> ."
                "<br /><b>Note:</b> This is only a rough approximation!")

        # VISIBLE widgets for all man. / min. filter order response types:
        vis_man = ['fo','fspecs','tspecs'] # manual filter order
        vis_min = ['fo','fspecs','tspecs'] # minimum filter order

        # DISABLED widgets for all man. / min. filter order response types:
        dis_man = [] # manual filter order
        dis_min = ['fspecs'] # minimum filter order

        # common PARAMETERS for all man. / min. filter order response types:
        par_man = ['N', 'f_S', 'F_C']     #  manual filter order
        par_min = ['f_S', 'A_PB', 'A_SB'] #  minimum filter order

        # Common data for all filter response types:
        # This data is merged with the entries for individual response types
        # (common data comes first):
        self.com = {"man":{"vis":vis_man, "dis":dis_man, "msg":msg_man, "par":par_man},
                    "min":{"vis":vis_min, "dis":dis_min, "msg":msg_min, "par":par_min}}
                    
        self.ft = 'FIR'
        self.rt = {
            "LP": {"man":{"par":[]},
                   "min":{"par":['F_PB','F_SB']}},
            "HP": {"man":{"par":[],
                          "msg":r"<br /><b>Note:</b> Order needs to be odd!"},
                   "min":{"par":['F_SB','F_PB']}},
            "BP": {"man":{"par":['F_C2']},
                   "min":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2', 'A_SB2']}},
            "BS": {"man":{"par":['F_C2'],
                      "msg":r"<br /><b>Note:</b> Order needs to be odd!"},
                   "min":{"par":['A_PB2','F_PB','F_SB','F_SB2','F_PB2']}}
#            "HIL": {"man":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2','A_SB','A_PB','A_SB2']}}
          #"DIFF":
                   }
        
        self.info = """Windowed FIR filters are designed by truncating the
        infinite impulse response of an ideal filter with a window function.
        The kind of used window has strong influence on ripple etc. of the
        resulting filter.
        """
        #self.info_doc = [] is set in self.updateWindow()
        
        #------------------- end of static info for filter tree ---------------

        
        # additional dynamic widgets that need to be set in the main widgets
        # input_filter ('sf') and input_order ('fo')
        self.wdg = {'fo':'cmb_firwin_alg', 'sf':'wdg_firwin_win'}
        
        self.hdl = None
        
        
        self._init_UI()

        
    def _init_UI(self):
        """
        Create additional subwidget(s) needed for filter design with the 
        names given in self.wdg :
        These subwidgets are instantiated dynamically when needed in 
        input_filter.py using the handle to the filter object, fb.filObj .
        """

        # Combobox for selecting the algorithm to estimate minimum filter order
        self.cmb_firwin_alg = QtGui.QComboBox()
        self.cmb_firwin_alg.setObjectName('wdg_cmb_firwin_alg')
        self.cmb_firwin_alg.addItems(['ichige','kaiser','herrmann'])
        # Minimum size, can be changed in the upper hierarchy levels using layouts:
        self.cmb_firwin_alg.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        # Combobox for selecting the window used for filter design
        self.cmb_firwin_win = QtGui.QComboBox()
        self.cmb_firwin_win.setObjectName('wdg_cmb_firwin_win')

        windows = ['Barthann','Bartlett','Blackman','Blackmanharris','Bohman',
                   'Boxcar','Chebwin','Cosine','Flattop','General_Gaussian',
                   'Gaussian','Hamming','Hann','Kaiser','Nuttall','Parzen',
                   'Slepian','Triang']
        #=== Windows with parameters =======
        # kaiser - needs beta
        # gaussian needs std
        # general_gaussian - needs power, width
        # slepian - needs width
        # chebwin - needs attenuation

        self.cmb_firwin_win.addItems(windows)
        # Minimum size, can be changed in the upper hierarchy levels using layouts:
        self.cmb_firwin_win.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        self.lbl_firwin_1 = QtGui.QLabel("a")
        self.lbl_firwin_1.setObjectName('wdg_lbl_firwin_1')
        self.led_firwin_1 = QtGui.QLineEdit()
        self.led_firwin_1.setText("0.5")
        self.led_firwin_1.setObjectName('wdg_led_firwin_1')
        self.lbl_firwin_1.setVisible(False)
        self.led_firwin_1.setVisible(False)
               
        self.lbl_firwin_2 = QtGui.QLabel("b")
        self.lbl_firwin_2.setObjectName('wdg_lbl_firwin_2')
        self.led_firwin_2 = QtGui.QLineEdit()
        self.led_firwin_2.setText("0.5")
        self.led_firwin_2.setObjectName('wdg_led_firwin_2')
        self.led_firwin_2.setVisible(False)
        self.lbl_firwin_2.setVisible(False)

        # Widget containing all subwidgets (cmbBoxes, Labels, lineEdits)        
        self.wdg_firwin_win = QtGui.QWidget()
        self.wdg_firwin_win.setObjectName('wdg_firwin_win')
        self.layGWin = QtGui.QGridLayout()
        self.layGWin.setObjectName('wdg_layGWin')
        self.layGWin.addWidget(self.cmb_firwin_win,0,0,1,4)
        self.layGWin.addWidget(self.lbl_firwin_1,1,0)
        self.layGWin.addWidget(self.led_firwin_1,1,1)
        self.layGWin.addWidget(self.lbl_firwin_2,1,2)
        self.layGWin.addWidget(self.led_firwin_2,1,3)
        self.layGWin.setContentsMargins(0,0,0,0)
        self.wdg_firwin_win.setLayout(self.layGWin)


        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.cmb_firwin_win.activated.connect(self._update_UI)
#        self.led_firwin_1.editingFinished.connect(self._store_entries)
#        self.led_firwin_2.editingFinished.connect(self._store_entries)

        self.led_firwin_1.editingFinished.connect(self._update_UI)
        self.led_firwin_2.editingFinished.connect(self._update_UI)
        self.cmb_firwin_alg.activated.connect(self._update_UI)
        #----------------------------------------------------------------------

        self._load_entries() # get initial / last setting from dictionary
        self._update_UI()


    def _update_UI(self):
        """
        Update UI and info_doc when one of the comboboxes or line edits is 
        changed.
        """
        self.fir_window_name = str(self.cmb_firwin_win.currentText()).lower()
        self.alg = str(self.cmb_firwin_alg.currentText())

        mod_ = import_module('scipy.signal')
#        mod = __import__('scipy.signal') # works, but not with the next line
        
         # construct window class, e.g. scipy.signal.boxcar :
        class_ = getattr(mod_, self.fir_window_name)
        win_doc = getattr(class_, '__doc__') # read docstring attribute from class
        
        self.info_doc = []
        self.info_doc.append('firwin()\n========')
        self.info_doc.append(sig.firwin.__doc__)
        self.info_doc.append(self.fir_window_name + '()' +'\n' + 
                                        '=' * (len(self.fir_window_name) + 2))
        self.info_doc.append(win_doc)
        
        self.winArgs = inspect.getargspec(class_)[0] # return args of window
        # and remove common args for all window types ('sym' and 'M'):
        self.winArgs = [arg for arg in self.winArgs if arg not in {'sym', 'M'}]

        
        # make edit boxes and labels for additional parameters visible if needed
        # and construct self.firWindow as a tuple consisting of a string with 
        # the window name and optionally one or two float parameters. 
        # If there are no additional parameters, just pass the window name string.
        N_args = len(self.winArgs)
        self.lbl_firwin_1.setVisible(N_args > 0)
        self.led_firwin_1.setVisible(N_args > 0)
        self.lbl_firwin_2.setVisible(N_args > 1)
        self.led_firwin_2.setVisible(N_args > 1)
            
        if N_args > 1 :
            self.lbl_firwin_2.setText(self.winArgs[1] + ":")
            self.firWindow = (self.fir_window_name,
                                      float(self.led_firwin_1.text()), 
                                      float(self.led_firwin_2.text()))
        elif N_args > 0 :
            self.lbl_firwin_1.setText(self.winArgs[0] + ":")
            self.firWindow = (self.fir_window_name,
                                      float(self.led_firwin_1.text()))
        else:
            self.firWindow = self.fir_window_name 
            
    def destruct_UI(self):
        """
        - Disconnect all signal-slot connections to avoid crashes upon exit
        - Delete dynamic widgets
        """
        self.cmb_firwin_win.activated.disconnect()
        self.led_firwin_1.editingFinished.disconnect()
        self.led_firwin_2.editingFinished.disconnect()
        self.cmb_firwin_alg.activated.disconnect()


    def _load_entries(self):
        """
        Reload window selection and parameters from filter dictionary
        and set UI elements accordingly (when filter is loaded from disk).
        """
        win_idx = 0
        alg_idx = 0
        try:
            dyn_wdg_par = fb.fil[0]['wdg_dyn']
            if 'win' in dyn_wdg_par:
                if np.isscalar(dyn_wdg_par['win']): # true for strings (non-vectors) 
                    window = dyn_wdg_par['win']
                else:
                    window = dyn_wdg_par['win'][0]
                    self.led_firwin_1.setText(str(dyn_wdg_par['win'][1]))
                    if len(dyn_wdg_par['win']) > 2:
                        self.led_firwin_2.setText(str(dyn_wdg_par['win'][2]))                       

                # find index for window string
                win_idx = self.cmb_firwin_win.findText(window, 
                                QtCore.Qt.MatchFixedString) # case insensitive flag
                if win_idx == -1: # Key does not exist, use first entry instead
                    win_idx = 0
                    
            if 'alg' in dyn_wdg_par:
                alg_idx = self.cmb_firwin_alg.findText(dyn_wdg_par['alg'], 
                                QtCore.Qt.MatchFixedString)
                if alg_idx == -1: # Key does not exist, use first entry instead
                    alg_idx = 0
                
        except KeyError as e:
            print("Key Error:",e)
        
        self.cmb_firwin_win.setCurrentIndex(win_idx) # set index for window and
        self.cmb_firwin_alg.setCurrentIndex(alg_idx) # and algorithm cmbBox

    def _store_entries(self):
        """
        Store window and alg. selection and parameter settings (part of 
        self.firWindow, if any) in filter dictionary.
        """
            
            
        fb.fil[0].update({'wdg_dyn':{'win':self.firWindow,
                                 'alg':self.alg}})


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

#        self.alg = 'ichige' # algorithm for determining the minimum order
#        self.alg = self.cmb_firwin_alg.currentText()
#        print("===== firwin ====\n", self.alg)
#        print(self.firWindow)

    def _save(self, fil_dict, arg):
        """
        Convert between poles / zeros / gain, filter coefficients (polynomes)
        and second-order sections and store all available formats in the passed
        dictionary 'fil_dict'.
        """
        fil_save(fil_dict, arg, FRMT, __name__)

        try: # has the order been calculated by a "min" filter design?
            fil_dict['N'] = self.N # yes, update filterbroker
        except AttributeError:
            pass
#        self._store_entries()
        
        
    def _firwin_ord(self, F, W, A, alg):
        #http://www.mikroe.com/chapters/view/72/chapter-2-fir-filters/
        delta_f = abs(F[1] - F[0])
        delta_A = np.sqrt(A[0] * A[1])
        if self.fir_window_name == 'kaiser':
            N, beta = sig.kaiserord(fb.fil[0]['A_SB'], delta_f)
            self.led_firwin_1.setText(str(beta))
            fb.fil[0]['wdg_dyn'][1] = beta
            self.firWindow[1] = beta
            self._load_entries()
            return N
        
        if self.firWindow == 'hann':
            gamma = 3.11
            sidelobe = 44
        elif self.firWindow == 'hamming':
            gamma = 3.32
            sidelobe = 53
        elif self.firWindow == 'blackman':
            gamma = 5.56
            sidelobe = 75
        else:
            gamma = 1
        N = remezord(F, W, A, Hz = 1, alg = alg)[0]
        return N

    def LPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N = self._firwin_ord([self.F_PB, self.F_SB], [1, 0],
                                 [self.A_PB, self.A_SB], alg = self.alg)
        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2 # use average of calculated F_PB and F_SB
        self._save(fil_dict, sig.firwin(self.N, fil_dict['F_C'], 
                                       window = self.firWindow, nyq = 0.5))

    def LPman(self, fil_dict):
        self._get_params(fil_dict)
        self._save(fil_dict, sig.firwin(self.N, fil_dict['F_C'],
                                       window = self.firWindow, nyq = 0.5))

    def HPmin(self, fil_dict):
        self._get_params(fil_dict)
        N = self._firwin_ord([self.F_SB, self.F_PB], [0, 1],
                            [self.A_SB, self.A_PB], alg = self.alg)
        self.N = round_odd(N)  # enforce odd order
        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2 # use average of calculated F_PB and F_SB
        self._save(fil_dict, sig.firwin(self.N, fil_dict['F_C'], 
                    window = self.firWindow, pass_zero=False, nyq = 0.5))

    def HPman(self, fil_dict):
        self._get_params(fil_dict)
        self.N = round_odd(self.N)  # enforce odd order
        self._save(fil_dict, sig.firwin(self.N, fil_dict['F_C'], 
            window = self.firWindow, pass_zero=False, nyq = 0.5))


    # For BP and BS, F_PB and F_SB have two elements each
    def BPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N = remezord([self.F_SB, self.F_PB, self.F_PB2, self.F_SB2], [0, 1, 0],
            [self.A_SB, self.A_PB, self.A_SB2], Hz = 1, alg = self.alg)[0]
        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2 # use average of calculated F_PB and F_SB
        fil_dict['F_C2'] = (self.F_SB2 + self.F_PB2)/2 # use average of calculated F_PB and F_SB
        self._save(fil_dict, sig.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']],
                            window = self.firWindow, pass_zero=False, nyq = 0.5))

    def BPman(self, fil_dict):
        self._get_params(fil_dict)
        self._save(fil_dict, sig.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']],
                            window = self.firWindow, pass_zero=False, nyq = 0.5))

    def BSmin(self, fil_dict):
        self._get_params(fil_dict)
        N = remezord([self.F_PB, self.F_SB, self.F_SB2, self.F_PB2], [1, 0, 1],
            [self.A_PB, self.A_SB, self.A_PB2], Hz = 1, alg = self.alg)[0]
        self.N = round_odd(N)  # enforce odd order
        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2 # use average of calculated F_PB and F_SB
        fil_dict['F_C2'] = (self.F_SB2 + self.F_PB2)/2 # use average of calculated F_PB and F_SB
        self._save(fil_dict, sig.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']],
                            window = self.firWindow, pass_zero=True, nyq = 0.5))

    def BSman(self, fil_dict):
        self._get_params(fil_dict)
        self.N = round_odd(self.N)  # enforce odd order
        self._save(fil_dict, sig.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']],
                            window = self.firWindow, pass_zero=True, nyq = 0.5))


#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
  
    filt = firwin()  # instantiate filter
    win_type = getattr(filt, filt.wdg['sf'])
 #   print(filt.firWindow)
#
    filt_alg = getattr(filt, filt.wdg['fo'])
    
    layVDynWdg = QtGui.QVBoxLayout()
    layVDynWdg.addWidget(win_type, stretch = 1)
    layVDynWdg.addWidget(filt_alg, stretch = 1)
    
    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][FRMT]) # return results in default format

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

