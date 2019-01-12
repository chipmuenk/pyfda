# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Design windowed FIR filters (LP, HP, BP, BS) with fixed order, return
the filter design in coefficient ('ba') format

Attention: 
This class is re-instantiated dynamically everytime the filter design method
is selected, calling the __init__ method.

API version info:
    1.0: initial working release
    1.1: mark private methods as private
    1.2: new API using fil_save
    1.3: new public methods destruct_UI + construct_UI (no longer called by __init__)    
    1.4: module attribute `filter_classes` contains class name and combo box name
         instead of class attribute `name`
         `FRMT` is now a class attribute
    2.0: Specify the parameters for each subwidget as tuples in a dict where the
         first element controls whether the widget is visible and / or enabled.
         This dict is now called self.rt_dict. When present, the dict self.rt_dict_add
         is read and merged with the first one.
"""
from __future__ import print_function, division, unicode_literals

from ..compat import (Qt, QWidget, QLabel, QLineEdit, pyqtSignal, QComboBox,
                      QVBoxLayout, QGridLayout)

import numpy as np
import scipy.signal as sig
from importlib import import_module
import inspect

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import fil_save, round_odd, safe_eval
from pyfda.pyfda_qt_lib import qfilter_warning
from .common import Common, remezord


# TODO: Hilbert, differentiator, multiband are missing
# TODO: Use kaiserord, kaiser_beta & kaiser_atten to calculate params for 
#       kaiser window
# TODO: Improve calculation of F_C and F_C2 using the weights
# TODO: Automatic setting of density factor for remez calculation? 
#       Automatic switching to Kaiser / Hermann?
# TODO: Parameters for windows are not stored in fil_dict?

__version__ = "2.0"

filter_classes = {'Firwin':'Windowed FIR'}

class Firwin(QWidget):

    FRMT = 'ba' # output format(s) of filter design routines 'zpk' / 'ba' / 'sos'
                # currently, only 'ba' is supported for firwin routines
    
    sig_tx = pyqtSignal(object)

    def __init__(self):
        QWidget.__init__(self)

        self.ft = 'FIR'
                           
        c = Common()
        self.rt_dict = c.rt_base_iir
        
        self.rt_dict_add = {
            'COM':{'min':{'msg':('a',
                                  r"<br /><b>Note:</b> This is only a rough approximation!")},
                   'man':{'msg':('a',
                                 r"Enter desired filter order <b><i>N</i></b> and " 
                                  "<b>-6 dB</b> pass band corner "
                                  "frequency(ies) <b><i>F<sub>C</sub></i></b> .")},                                  
                                  },
            'LP': {'man':{}, 'min':{}},
            'HP': {'man':{'msg':('a', r"<br /><b>Note:</b> Order needs to be odd!")},
                   'min':{}},
            'BS': {'man':{'msg':('a', r"<br /><b>Note:</b> Order needs to be odd!")},
                   'min':{}},
            'BP': {'man':{}, 'min':{}},
            }
            
        
        self.info = """**Windowed FIR filters**
        
        are designed by truncating the
        infinite impulse response of an ideal filter with a window function.
        The kind of used window has strong influence on ripple etc. of the
        resulting filter.
        
        **Design routines:**

        ``scipy.signal.firwin()``

        """
        #self.info_doc = [] is set in self._update_UI()
        
        #------------------- end of static info for filter tree ---------------

        
        #----------------------------------------------------------------------        
    def construct_UI(self):
        """
        Create additional subwidget(s) needed for filter design:
        These subwidgets are instantiated dynamically when needed in 
        select_filter.py using the handle to the filter object, fb.filObj .
        """

        # Combobox for selecting the algorithm to estimate minimum filter order
        self.cmb_firwin_alg = QComboBox(self)
        self.cmb_firwin_alg.setObjectName('wdg_cmb_firwin_alg')
        self.cmb_firwin_alg.addItems(['ichige','kaiser','herrmann'])
        # Minimum size, can be changed in the upper hierarchy levels using layouts:
        self.cmb_firwin_alg.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmb_firwin_alg.hide()

        # Combobox for selecting the window used for filter design
        self.cmb_firwin_win = QComboBox(self)
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
        self.cmb_firwin_win.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.lbl_firwin_1 = QLabel("a", self)
        self.lbl_firwin_1.setObjectName('wdg_lbl_firwin_1')
        self.led_firwin_1 = QLineEdit(self)
        self.led_firwin_1.setText("0.5")
        self.led_firwin_1.setObjectName('wdg_led_firwin_1')
        self.lbl_firwin_1.setVisible(False)
        self.led_firwin_1.setVisible(False)
               
        self.lbl_firwin_2 = QLabel("b", self)
        self.lbl_firwin_2.setObjectName('wdg_lbl_firwin_2')
        self.led_firwin_2 = QLineEdit(self)
        self.led_firwin_2.setText("0.5")
        self.led_firwin_2.setObjectName('wdg_led_firwin_2')
        self.led_firwin_2.setVisible(False)
        self.lbl_firwin_2.setVisible(False)

        self.layGWin = QGridLayout()
        self.layGWin.setObjectName('wdg_layGWin')
        self.layGWin.addWidget(self.cmb_firwin_win,0,0,1,2)
        self.layGWin.addWidget(self.cmb_firwin_alg,0,2,1,2)
        self.layGWin.addWidget(self.lbl_firwin_1,1,0)
        self.layGWin.addWidget(self.led_firwin_1,1,1)
        self.layGWin.addWidget(self.lbl_firwin_2,1,2)
        self.layGWin.addWidget(self.led_firwin_2,1,3)
        self.layGWin.setContentsMargins(0,0,0,0)
        # Widget containing all subwidgets (cmbBoxes, Labels, lineEdits)
        self.wdg_fil = QWidget(self)
        self.wdg_fil.setObjectName('wdg_fil')
        self.wdg_fil.setLayout(self.layGWin)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.cmb_firwin_win.activated.connect(self._update_UI)
        self.led_firwin_1.editingFinished.connect(self._update_UI)
        self.led_firwin_2.editingFinished.connect(self._update_UI)
        self.cmb_firwin_alg.activated.connect(self._update_UI)
        #----------------------------------------------------------------------

        self._load_dict() # get initial / last setting from dictionary
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
                                      safe_eval(self.led_firwin_1.text(), return_type='float'), 
                                      safe_eval(self.led_firwin_2.text(), return_type='float'))
        elif N_args > 0 :
            self.lbl_firwin_1.setText(self.winArgs[0] + ":")
            self.firWindow = (self.fir_window_name,
                                      safe_eval(self.led_firwin_1.text(), return_type='float'))
        else:
            self.firWindow = self.fir_window_name

        # sig_tx -> select_filter -> filter_specs
        self.sig_tx.emit({'sender':__name__, 'filt_changed':'firwin'})
            
    def _load_dict(self):
        """
        Reload window selection and parameters from filter dictionary
        and set UI elements accordingly. load_dict() is called upon 
        initialization and when the filter is loaded from disk.
        """
        win_idx = 0
        alg_idx = 0
        if 'wdg_fil' in fb.fil[0] and 'firwin' in fb.fil[0]['wdg_fil']:
            wdg_fil_par = fb.fil[0]['wdg_fil']['firwin']

            if 'win' in wdg_fil_par:
                if np.isscalar(wdg_fil_par['win']): # true for strings (non-vectors) 
                    window = wdg_fil_par['win']
                else:
                    window = wdg_fil_par['win'][0]
                    self.led_firwin_1.setText(str(wdg_fil_par['win'][1]))
                    if len(wdg_fil_par['win']) > 2:
                        self.led_firwin_2.setText(str(wdg_fil_par['win'][2]))                       

                # find index for window string
                win_idx = self.cmb_firwin_win.findText(window, 
                                Qt.MatchFixedString) # case insensitive flag
                if win_idx == -1: # Key does not exist, use first entry instead
                    win_idx = 0
                    
            if 'alg' in wdg_fil_par:
                alg_idx = self.cmb_firwin_alg.findText(wdg_fil_par['alg'], 
                                Qt.MatchFixedString)
                if alg_idx == -1: # Key does not exist, use first entry instead
                    alg_idx = 0
        
        self.cmb_firwin_win.setCurrentIndex(win_idx) # set index for window and
        self.cmb_firwin_alg.setCurrentIndex(alg_idx) # and algorithm cmbBox

    def _store_entries(self):
        """
        Store window and alg. selection and parameter settings (part of 
        self.firWindow, if any) in filter dictionary.
        """
        if not 'wdg_fil' in fb.fil[0]:
            fb.fil[0].update({'wdg_fil':{}})
        fb.fil[0]['wdg_fil'].update({'firwin':
                                        {'win':self.firWindow,
                                         'alg':self.alg}
                                 })
            

    def _get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N     = fil_dict['N']
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

    def _test_N(self):
        """
        Warn the user if the calculated order is too high for a reasonable filter
        design.
        """
        if self.N > 1000:
            return qfilter_warning(self, self.N, "FirWin")
        else:
            return True


    def _save(self, fil_dict, arg):
        """
        Convert between poles / zeros / gain, filter coefficients (polynomes)
        and second-order sections and store all available formats in the passed
        dictionary 'fil_dict'.
        """
        fil_save(fil_dict, arg, self.FRMT, __name__)

        try: # has the order been calculated by a "min" filter design?
            fil_dict['N'] = self.N # yes, update filterbroker
        except AttributeError:
            pass
#        self._store_entries()
        
        
    def _firwin_ord(self, F, W, A, alg):
        #http://www.mikroe.com/chapters/view/72/chapter-2-fir-filters/
        delta_f = abs(F[1] - F[0]) * 2 # referred to f_Ny
        delta_A = np.sqrt(A[0] * A[1])
        if self.fir_window_name == 'kaiser':
            N, beta = sig.kaiserord(20 * np.log10(np.abs(fb.fil[0]['A_SB'])), delta_f)
            self.led_firwin_1.setText(str(beta))
            fb.fil[0]['wdg_fil'][1] = beta
            self._update_UI()
            #self._load_dict()
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
        if not self._test_N():
            return -1
        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2 # use average of calculated F_PB and F_SB
        self._save(fil_dict, sig.firwin(self.N, fil_dict['F_C'], 
                                       window = self.firWindow, nyq = 0.5))

    def LPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.firwin(self.N, fil_dict['F_C'],
                                       window = self.firWindow, nyq = 0.5))

    def HPmin(self, fil_dict):
        self._get_params(fil_dict)
        N = self._firwin_ord([self.F_SB, self.F_PB], [0, 1],
                            [self.A_SB, self.A_PB], alg = self.alg)
        self.N = round_odd(N)  # enforce odd order
        if not self._test_N():
            return -1
        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2 # use average of calculated F_PB and F_SB
        self._save(fil_dict, sig.firwin(self.N, fil_dict['F_C'], 
                    window = self.firWindow, pass_zero=False, nyq = 0.5))

    def HPman(self, fil_dict):
        self._get_params(fil_dict)
        self.N = round_odd(self.N)  # enforce odd order
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.firwin(self.N, fil_dict['F_C'], 
            window = self.firWindow, pass_zero=False, nyq = 0.5))


    # For BP and BS, F_PB and F_SB have two elements each
    def BPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N = remezord([self.F_SB, self.F_PB, self.F_PB2, self.F_SB2], [0, 1, 0],
            [self.A_SB, self.A_PB, self.A_SB2], Hz = 1, alg = self.alg)[0]
        if not self._test_N():
            return -1
        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2 # use average of calculated F_PB and F_SB
        fil_dict['F_C2'] = (self.F_SB2 + self.F_PB2)/2 # use average of calculated F_PB and F_SB
        self._save(fil_dict, sig.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']],
                            window = self.firWindow, pass_zero=False, nyq = 0.5))

    def BPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']],
                            window = self.firWindow, pass_zero=False, nyq = 0.5))

    def BSmin(self, fil_dict):
        self._get_params(fil_dict)
        N = remezord([self.F_PB, self.F_SB, self.F_SB2, self.F_PB2], [1, 0, 1],
            [self.A_PB, self.A_SB, self.A_PB2], Hz = 1, alg = self.alg)[0]
        self.N = round_odd(N)  # enforce odd order
        if not self._test_N():
            return -1
        fil_dict['F_C'] = (self.F_SB + self.F_PB)/2 # use average of calculated F_PB and F_SB
        fil_dict['F_C2'] = (self.F_SB2 + self.F_PB2)/2 # use average of calculated F_PB and F_SB
        self._save(fil_dict, sig.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']],
                            window = self.firWindow, pass_zero=True, nyq = 0.5))

    def BSman(self, fil_dict):
        self._get_params(fil_dict)
        self.N = round_odd(self.N)  # enforce odd order
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.firwin(self.N, [fil_dict['F_C'], fil_dict['F_C2']],
                            window = self.firWindow, pass_zero=True, nyq = 0.5))


#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys 
    from ..compat import QApplication, QFrame

    app = QApplication(sys.argv)
    
    # instantiate filter widget
    filt = Firwin()
    filt.construct_UI()
    wdg_firwin = getattr(filt, 'wdg_fil')

    layVDynWdg = QVBoxLayout()
    layVDynWdg.addWidget(wdg_firwin, stretch = 1)

    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][filt.FRMT]) # return results in default format

    frmMain = QFrame()
    frmMain.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
    frmMain.setLayout(layVDynWdg)    

    form = frmMain

    form.show()

    app.exec_()

