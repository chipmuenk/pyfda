# -*- coding: utf-8 -*-
"""
Design windowed FIR filters (LP, HP, BP, BS) with fixed order, return
the filter design in coefficient ('ba') format

Attention: 
This class is re-instantiated dynamically everytime the filter design method
is selected, calling the __init__ method.

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals
import numpy as np
import scipy.signal as sig
from importlib import import_module
import inspect
from PyQt4 import QtGui, QtCore

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    import sys, os
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import filterbroker as fb # importing filterbroker initializes all its globals
import pyfda_lib


# TODO: Hilbert, differentiator, multiband are missing
# TODO: Use kaiserord, kaiser_beta & kaiser_atten to calculate params for 
#       kaiser window
# TODO: Improve calculation of F_C and F_C2 using the weights
# TODO: Automatic setting of density factor for remez calculation? 
#       Automatic switching to Kaiser / Hermann?

frmt = 'ba' # output format of filter design routines 'zpk' / 'ba' / 'sos'
            # currently, only 'ba' is supported for firwin routines

class firwin(object):

    def __init__(self):
        
        # The first part contains static information that is used to build
        # the filter tree:
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
        
        # additional dynamic widgets that need to be set in the main widgets
        self.wdg = {'fo':'cmb_firwin_alg', 'sf':'wdg_firwin_win'}
        
        self.hdl = None
        
        self.initUI()

        
    def initUI(self):
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
        self.cmb_firwin_win.activated.connect(self.updateUI)
        self.led_firwin_1.editingFinished.connect(self.updateUI)
        self.led_firwin_2.editingFinished.connect(self.updateUI)
        self.cmb_firwin_alg.activated.connect(self.updateUI)
        #----------------------------------------------------------------------

        self.loadEntries() # get initial / last setting from dictionary
        self.updateUI()


    def updateUI(self):
        """
        Update UI and info_doc when one of the comboboxes or line edits is 
        changed.
        """
        self.firWindow = str(self.cmb_firwin_win.currentText()).lower()
        self.alg = str(self.cmb_firwin_alg.currentText())

        mod_ = import_module('scipy.signal')
#        mod = __import__('scipy.signal') # works, but not with the next line
        
         # construct window class, e.g. scipy.signal.boxcar :
        class_ = getattr(mod_, self.firWindow)
        win_doc = getattr(class_, '__doc__') # read docstring attribute from class
        
        self.info_doc = []
        self.info_doc.append('firwin()\n========')
        self.info_doc.append(sig.firwin.__doc__)
        self.info_doc.append(self.firWindow + '()' +'\n' + 
                                        '=' * (len(self.firWindow) + 2))
        self.info_doc.append(win_doc)
        
        self.winArgs = inspect.getargspec(class_)[0] # return args of window
        # and remove common args for all window types ('sym' and 'M'):
        self.winArgs = [arg for arg in self.winArgs if arg not in {'sym', 'M'}]

        # print(scipy.signal.window.boxcar.func_code.co_varnames) # also works
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
            self.firWindow = (self.firWindow,
                                      float(self.led_firwin_1.text()), 
                                      float(self.led_firwin_2.text()))
        elif N_args > 0 :
            self.lbl_firwin_1.setText(self.winArgs[0] + ":")
            self.firWindow = (self.firWindow,
                                      float(self.led_firwin_1.text()))
        #print(self.firWindow)           

    def loadEntries(self):
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
        
        self.cmb_firwin_win.setCurrentIndex(win_idx) # set index
        self.cmb_firwin_alg.setCurrentIndex(alg_idx)

    def storeEntries(self):
        """
        Store window and alg. selection and parameter settings (if any) in filter
        dictionary.
        """
        fb.fil[0].update({'wdg_dyn':{'win':self.firWindow,
                                 'alg':self.alg}})


    def get_params(self, fil_dict):
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
        
        # remez amplitude specs are linear (not in dBs) and need to be
        # multiplied by a factor of two to obtain a "tight fit" (why??)
        self.A_PB  = (10.**(fil_dict['A_PB']/20.)-1) / (10**(fil_dict['A_PB']/20.)+1)*2
        self.A_PB2 = (10.**(fil_dict['A_PB2']/20.)-1)/(10**(fil_dict['A_PB2']/20.)+1)*2
        self.A_SB  = 10.**(-fil_dict['A_SB']/20.)
        self.A_SB2 = 10.**(-fil_dict['A_SB2']/20.)

#        self.alg = 'ichige' # algorithm for determining the minimum order
#        self.alg = self.cmb_firwin_alg.currentText()
#        print("===== firwin ====\n", self.alg)
#        print(self.firWindow)

    def save(self, fil_dict, arg):
        """
        Convert between poles / zeros / gain, filter coefficients (polynomes)
        and second-order sections and store all available formats in the passed
        dictionary 'fil_dict'.
        """
        pyfda_lib.save_fil(fil_dict, arg, frmt, __name__)

        try: # has the order been calculated by a "min" filter design?
            fil_dict['N'] = self.N # yes, update filterbroker
        except AttributeError:
            pass
        self.storeEntries()

    def LPmin(self, fil_dict):
        self.get_params(fil_dict)
        (self.N, F, A, W) = pyfda_lib.remezord([self.F_PB, self.F_SB], [1, 0],
            [self.A_PB, self.A_SB], Hz = 1, alg = self.alg)
        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2 # use average of calculated F_PB and F_SB
        self.save(fil_dict, sig.firwin(self.N, fil_dict['F_C'], 
                                       window = self.firWindow, nyq = 0.5))

    def LPman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.firwin(self.N, fil_dict['F_C'],
                                       window = self.firWindow, nyq = 0.5))

    def HPmin(self, fil_dict):
        self.get_params(fil_dict)
        (N, F, A, W) = pyfda_lib.remezord([self.F_SB, self.F_PB], [0, 1],
            [self.A_SB, self.A_PB], Hz = 1, alg = self.alg)
        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2 # use average of calculated F_PB and F_SB
        self.N = pyfda_lib.round_odd(N)  # enforce odd order
        self.save(fil_dict, sig.firwin(self.N, fil_dict['F_C'], 
                    window = self.firWindow, pass_zero=False, nyq = 0.5))

    def HPman(self, fil_dict):
        self.get_params(fil_dict)
        self.N = pyfda_lib.round_odd(self.N)  # enforce odd order
        self.save(fil_dict, sig.firwin(self.N, fil_dict['F_C'], 
            window = self.firWindow, pass_zero=False, nyq = 0.5))


    # For BP and BS, F_PB and F_SB have two elements each
    def BPmin(self, fil_dict):
        self.get_params(fil_dict)
        (self.N, F, A, W) = pyfda_lib.remezord([self.F_SB, self.F_PB,
                                self.F_PB2, self.F_SB2], [0, 1, 0],
            [self.A_SB, self.A_PB, self.A_SB2], Hz = 1, alg = self.alg)
        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2 # use average of calculated F_PB and F_SB
        fil_dict['F_C2'] = (self.F_SB2 + self.F_PB2)/2 # use average of calculated F_PB and F_SB
        self.save(fil_dict, sig.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']],
                            window = self.firWindow, pass_zero=False, nyq = 0.5))

    def BPman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']],
                            window = self.firWindow, pass_zero=False, nyq = 0.5))

    def BSmin(self, fil_dict):
        self.get_params(fil_dict)
        (N, F, A, W) = pyfda_lib.remezord([self.F_PB, self.F_SB,
                                self.F_SB2, self.F_PB2], [1, 0, 1],
            [self.A_PB, self.A_SB, self.A_PB2], Hz = 1, alg = self.alg)
        self.N = pyfda_lib.round_odd(N)  # enforce odd order
        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2 # use average of calculated F_PB and F_SB
        fil_dict['F_C2'] = (self.F_SB2 + self.F_PB2)/2 # use average of calculated F_PB and F_SB
        self.save(fil_dict, sig.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']],
                            window = self.firWindow, pass_zero=True, nyq = 0.5))

    def BSman(self, fil_dict):
        self.get_params(fil_dict)
        self.N = pyfda_lib.round_odd(self.N)  # enforce odd order
        self.save(fil_dict, sig.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']],
                            window = self.firWindow, pass_zero=True, nyq = 0.5))


#------------------------------------------------------------------------------

if __name__ == '__main__':
    
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

