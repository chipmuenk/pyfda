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
import scipy.signal as sig
from importlib import import_module
import inspect
from PyQt4 import QtGui

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    import sys, os
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))
    import filterbroker as fb # importing filterbroker initializes all its globals
    
import pyfda_lib


# TODO: Order of A_XX is incorrect e.g. for BP
# TODO: Hilbert not working correctly yet
# TODO: Windows with parameters are missing

frmt = 'ba' # output format of filter design routines 'zpk' / 'ba' / 'sos'
            # currently, only 'ba' is supported for firwin routines

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
        #self.info_doc = [] is set in self.updateWindow()
        
        self.initUI()

        
    def initUI(self):
        
        # Additional subwidgets needed for design:
        # These subwidgets are instantiated where needed using the handle to
        # the filter object

        self.wdg = {'fo':'combo_firwin_alg', 'sf':'wdg_firwin_win'}
        # Combobox for selecting the algorithm to estimate minimum filter order
        self.combo_firwin_alg = QtGui.QComboBox()
        self.combo_firwin_alg.setObjectName('combo_firwin_alg')
        self.combo_firwin_alg.addItems(['ichige','kaiser','herrmann'])

        # Combobox for selecting the window used for filter design
        self.combo_firwin_win = QtGui.QComboBox()
        self.combo_firwin_win.setObjectName('combo_firwin_win')

        windows = ['Barthann','Bartlett','Blackman','Blackmanharris','Bohman',
                   'Boxcar','Chebwin','Flattop','General_Gaussian','Gaussian',
                   'Hamming','Hann','Kaiser','Nuttall','Parzen','Slepian','Triang']

        #kaiser (needs beta), gaussian (needs std), general_gaussian
        #(needs power, width), slepian (needs width), chebwin (needs attenuation)

        self.combo_firwin_win.addItems(windows)
        win_idx = self.combo_firwin_win.findText('Boxcar')
        self.combo_firwin_win.setCurrentIndex(win_idx)
        
        self.lbl_firwin_win1 = QtGui.QLabel("a")
        self.led_firwin_win1 = QtGui.QLineEdit()
        self.led_firwin_win1.setText("0.5")
        self.led_firwin_win1.setObjectName('led_firwin_win1')
        self.lbl_firwin_win1.setVisible(False)
        self.led_firwin_win1.setVisible(False)
               
        self.lbl_firwin_win2 = QtGui.QLabel("b")
        self.led_firwin_win2 = QtGui.QLineEdit()
        self.led_firwin_win2.setText("0.5")
        self.led_firwin_win2.setObjectName('led_firwin_win2')
        self.led_firwin_win2.setVisible(False)
        self.lbl_firwin_win2.setVisible(False)
        
        self.wdg_firwin_win = QtGui.QWidget()
        self.wdg_firwin_win.setObjectName('wdg_firwin_win')
        self.layGWin = QtGui.QGridLayout()
        self.layGWin.addWidget(self.combo_firwin_win,0,0,1,4)
        self.layGWin.addWidget(self.lbl_firwin_win1,1,0)
        self.layGWin.addWidget(self.led_firwin_win1,1,1)
        self.layGWin.addWidget(self.lbl_firwin_win2,1,2)
        self.layGWin.addWidget(self.led_firwin_win2,1,3)
        self.layGWin.setContentsMargins(0,0,0,0)
        self.wdg_firwin_win.setLayout(self.layGWin)

        # Basic size of comboboxes is minimum, this can be changed in the 
        # upper hierarchy level using layouts
        self.combo_firwin_alg.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.combo_firwin_win.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        self.combo_firwin_win.activated.connect(self.updateWindow)
        self.led_firwin_win1.editingFinished.connect(self.updateWindow)
        self.led_firwin_win2.editingFinished.connect(self.updateWindow)   
        
        self.combo_firwin_alg.activated.connect(self.updateWindow)

        self.updateWindow()
        

    def updateWindow(self):
        self.firWindow = str(self.combo_firwin_win.currentText()).lower()
        self.alg = str(self.combo_firwin_alg.currentText())

        mod_ = import_module('scipy.signal')
#        mod = __import__('scipy.signal') # works, but not with the next line
        class_ = getattr(mod_, self.firWindow) # instantiate window class
        win_doc = getattr(class_, '__doc__') # read window docstring
        
        self.info_doc = []
        self.info_doc.append('firwin()\n========')
        self.info_doc.append(sig.firwin.__doc__)
        self.info_doc.append(self.firWindow + '()' +'\n' + 
                                        '=' * (len(self.firWindow) + 2))
        self.info_doc.append(win_doc)
        
        self.winArgs = inspect.getargspec(class_)[0] # return args of window
        # and remove standard args for all window types 'sym' and 'M':
        self.winArgs = [k for k in self.winArgs if k not in {'sym', 'M'}]
        #print(self.winArgs)
        N_args = len(self.winArgs)
        self.win_params = ""

        # make edit boxes for additional parameters visible if needed
        self.lbl_firwin_win1.setVisible(N_args > 0)
        self.led_firwin_win1.setVisible(N_args > 0)
        if N_args > 0 :
            self.lbl_firwin_win1.setText(self.winArgs[0])
            self.firWindow = (str(self.combo_firwin_win.currentText()).lower(),
                                      float(self.led_firwin_win1.text()))
            
        self.lbl_firwin_win2.setVisible(len(self.winArgs) > 1)
        self.led_firwin_win2.setVisible(len(self.winArgs) > 1)
        if N_args > 1 :
            self.lbl_firwin_win2.setText(self.winArgs[1])
            self.firWindow = (str(self.combo_firwin_win.currentText()).lower(),
                float(self.led_firwin_win1.text()), 
                float(self.led_firwin_win2.text()))
        #print(self.firWindow)           

            
    def deleteWidget(self):
        """
        Delete all dynamically created subwidgets
        When changing e.g. from LP to HP, Runtime Error occurs: 
        
            self.layHDynWdg.addWidget(a, stretch = 1)
        RuntimeError: wrapped C/C++ object of type QWidget has been deleted
        """
        pass          


    def get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N     = fil_dict['N'] + 1 # remez algorithms expects number of taps
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

#        self.alg = 'ichige' # algorithm for determining the minimum order
#        self.alg = self.combo_firwin_alg.currentText()
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
            fil_dict['N'] = self.N - 1 # yes, update filterbroker
        except AttributeError:
            pass

    def LPman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.firwin(self.N, self.F_PB,
                                       window = self.firWindow, nyq = 0.5))

    def LPmin(self, fil_dict):
        self.get_params(fil_dict)
        (self.N, F, A, W) = pyfda_lib.remezord([self.F_PB, self.F_SB], [1, 0],
            [self.A_PB, self.A_SB], Hz = 1, alg = self.alg)
        self.save(fil_dict, sig.firwin(self.N, self.F_PB, 
                                       window = self.firWindow, nyq = 0.5))

    def HPman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.firwin(self.N, self.F_PB, window = self.firWindow,
                                    pass_zero=False, nyq = 0.5))

    def HPmin(self, fil_dict):
        self.get_params(fil_dict)
        (N, F, A, W) = pyfda_lib.remezord([self.F_SB, self.F_PB], [0, 1],
            [self.A_SB, self.A_PB], Hz = 1, alg = self.alg)
        self.N = pyfda_lib.oddround(N)  # enforce odd length = even order
        self.save(fil_dict, sig.firwin(self.N, self.F_PB, window = self.firWindow,
                                    pass_zero=False, nyq = 0.5))
    # For BP and BS, F_PB and F_SB have two elements each
    def BPman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.firwin(self.N, [self.F_PB, self.F_PB2],
                                    window = self.firWindow, pass_zero=False))

    def BPmin(self, fil_dict):
        self.get_params(fil_dict)
        (self.N, F, A, W) = pyfda_lib.remezord([self.F_SB, self.F_PB,
                                self.F_PB2, self.F_SB2], [0, 1, 0],
            [self.A_SB, self.A_PB, self.A_SB2], Hz = 1, alg = self.alg)
        self.save(fil_dict, sig.firwin(self.N, [self.F_PB, self.F_PB2],
                            window = self.firWindow, pass_zero=False, nyq = 0.5))

    def BSman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.firwin(self.N, [self.F_SB, self.F_SB2],
                            window = self.firWindow, pass_zero=True, nyq = 0.5))

    def BSmin(self, fil_dict):
        self.get_params(fil_dict)
        (N, F, A, W) = pyfda_lib.remezord([self.F_PB, self.F_SB,
                                self.F_SB2, self.F_PB2], [1, 0, 1],
            [self.A_PB, self.A_SB, self.A_PB2], Hz = 1, alg = self.alg)
        self.N = pyfda_lib.oddround(N)  # enforce odd length = even order
        self.save(fil_dict, sig.firwin(self.N, [self.F_SB, self.F_SB2],
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
   
    
#
#
