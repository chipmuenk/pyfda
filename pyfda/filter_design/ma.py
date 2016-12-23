# -*- coding: utf-8 -*-
"""
Design Moving-Average-Filters (LP, HP) with fixed order, return
the filter design in coefficients format ('ba') or as poles/zeros ('zpk')

Attention: 
This class is re-instantiated dynamically everytime the filter design method
is selected, calling the __init__ method.

Version info:   
    1.0: initial working release
    1.1: mark private methods as private
    1.2: - new API using fil_save & fil_convert (allow multiple formats, 
                save 'ba' _and_ 'zpk' precisely)
         - include method _store_entries in _update_UI
    1.3: new public methods destruct_UI + construct_UI (no longer called by __init__)         
    1.4: module attribute `filter_classes` contains class name and combo box name
         instead of class attribute `name`
        `FRMT` is now a class attribute
    2.0: Specify the parameters for each subwidget as tuples in a dict where the
         first element controls whether the widget is visible and / or enabled.
         This dict is now called self.rt_dict. When present, the dict self.rt_dict_add
         is read and merged with the first one.

Author: Christian Muenker 2014 - 2016
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import logging
logger = logging.getLogger(__name__)

from ..compat import (QWidget, QLabel, QLineEdit, pyqtSignal, QFrame, QCheckBox,
                      QVBoxLayout, QHBoxLayout)

import numpy as np

import pyfda.filterbroker as fb
from pyfda.pyfda_lib import fil_save, fil_convert, ceil_even

__version__ = "2.0"

filter_classes = {'MA':'Moving Average'}   
         
class MA(QWidget):
        
    FRMT = ('zpk', 'ba') # output format(s) of filter design routines 'zpk' / 'ba' / 'sos'


    info ="""
**Moving average filters**

can only be specified via their length and the number of cascaded sections. 

The minimum order to obtain a minimum attenuation at
a given frequency can be calculated via the si function (not implemented yet).

**Design routines:**

``ma.calc()``
    """

    sigFiltChanged = pyqtSignal()

    def __init__(self):
        QWidget.__init__(self)       

        
        self.ft = 'FIR'

        self.rt_dicts = ()
        # Common data for all filter response types:
        # This data is merged with the entries for individual response types
        # (common data comes first):

        self.rt_dict = {
            'COM':{'man':{'fo': ('a', 'N'),
                          'msg':('a',
                   "Enter desired order (= delays) <b><i>N</i></b> per stage and"
                    " the number of <b>stages</b>. Target frequencies and amplitudes"
                    " are only used for comparison, not for the design itself.")
                        }
                    },
            'LP': {'man':{'tspecs': ('u', {'frq':('u','F_PB','F_SB'), 
                                           'amp':('u','A_PB','A_SB')})
                          } 
                },
            'HP': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB'), 
                                           'amp':('u','A_SB','A_PB')})
                         },
                },
            'BS': {'man':{'tspecs': ('u', {'frq':('u','F_PB','F_SB','F_SB2', 'F_PB2'), 
                                           'amp':('u','A_PB','A_SB','A_PB2')})
                        }},
            'BP': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2',), 
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                        }},
                }


        self.info_doc = []
#        self.info_doc.append('remez()\n=======')
#        self.info_doc.append(sig.remez.__doc__)
#        self.info_doc.append('remezord()\n==========')
#        self.info_doc.append(remezord.__doc__)
        
        self.wdg = True # has additional dynamic widget 'wdg_fil'
        
        self.hdl = ('ma', 'cic')
        #----------------------------------------------------------------------

    def construct_UI(self):
        """
        Create additional subwidget(s) needed for filter design with the 
        names given in self.wdg :
        These subwidgets are instantiated dynamically when needed in 
        select_filter.py using the handle to the filter instance, fb.fil_inst.
        """

        self.lbl_ma_1 = QLabel("<b>Stages:</ b>")
        self.lbl_ma_1.setObjectName('wdg_lbl_ma_1')
        self.led_ma_1 = QLineEdit()
        self.led_ma_1.setText("1")
        self.led_ma_1.setObjectName('wdg_led_ma_1')
        self.led_ma_1.setToolTip("Set number of stages ")
        
        self.lbl_ma_2 = QLabel("Normalize:")
        self.lbl_ma_2.setObjectName('wdg_lbl_ma_2')
        self.chk_ma_2 = QCheckBox()
        self.chk_ma_2.setChecked(True)
        self.chk_ma_2.setObjectName('wdg_chk_ma_2')
        self.chk_ma_2.setToolTip("Normalize to| H_max = 1|")
        
        self.layHWin = QHBoxLayout()
        self.layHWin.setObjectName('wdg_layGWin')
        self.layHWin.addWidget(self.lbl_ma_1)
        self.layHWin.addWidget(self.led_ma_1)
        self.layHWin.addWidget(self.lbl_ma_2)
        self.layHWin.addWidget(self.chk_ma_2)
        self.layHWin.setContentsMargins(0,0,0,0)
        # Widget containing all subwidgets (cmbBoxes, Labels, lineEdits)
        self.wdg_fil = QWidget()
        self.wdg_fil.setObjectName('wdg_fil')
        self.wdg_fil.setLayout(self.layHWin)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.led_ma_1.editingFinished.connect(self._update_UI)
        # fires when edited line looses focus or when RETURN is pressed
        self.chk_ma_2.clicked.connect(self._update_UI)
        #----------------------------------------------------------------------

        self._load_entries() # get initial / last setting from dictionary
        self._update_UI()
        
    def _update_UI(self):
        """
        Update UI when line edit field is changed (here, only the text is read
        and converted to integer.)
        """
        self.ma_stages = int(abs(round(float(self.led_ma_1.text()))))
        self.led_ma_1.setText(str(self.ma_stages))
        """
        Store parameter settings in filter dictionary.
        """
        fb.fil[0].update({'wdg_dyn':{'ma_stages':self.ma_stages,
                                     'ma_normalize':self.chk_ma_2.isChecked()}})
        self.sigFiltChanged.emit() # -> input_filt -> input_specs                                     


    def destruct_UI(self):
        """
        - Disconnect all signal-slot connections to avoid crashes upon exit
        - Delete dynamic widgets
        (empty method, nothing to do in this filter)
        """
        self.led_ma_1.editingFinished.disconnect()
        self.chk_ma_2.clicked.disconnect()

        
    def _load_entries(self):
        """
        Reload parameter(s) from filter dictionary and set UI elements 
        when filter is loaded from disk.
        """
        try:
            dyn_wdg_par = fb.fil[0]['wdg_dyn']
            if 'ma_stages' in dyn_wdg_par:
                self.ma_stages = dyn_wdg_par['ma_stages']
                self.led_ma_1.setText(str(self.ma_stages))
                self.chk_ma_2.setChecked(dyn_wdg_par['ma_normalize'])
        except KeyError as e:
            print("Key Error:",e)


#    def _store_entries(self):
#        """
#        Store parameter settings in filter dictionary.
#        """
#        fb.fil[0].update({'wdg_dyn':{'ma_stages':self.ma_stages,
#                                     'ma_normalize':self.chk_ma_2.isChecked()}})



    def _get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N     = fil_dict['N']
        self.F_SB  = fil_dict['F_SB']
        self.A_SB  = fil_dict['A_SB']
        

    def _save(self, fil_dict):
        """
        Convert between poles / zeros / gain, filter coefficients (polynomes)
        and second-order sections and store all available formats in the passed
        dictionary 'fil_dict'.
        """
        if 'zpk' in self.FRMT:        
            fil_save(fil_dict, self.zpk, 'zpk', __name__, convert = False)
        if 'ba' in self.FRMT:
            fil_save(fil_dict, self.b, 'ba', __name__, convert = False)
        fil_convert(fil_dict, self.FRMT)

#        if str(fil_dict['fo']) == 'min': 
        fil_dict['N'] = self.N  # yes, update filterbroker

#        self._store_entries()
        
        
    def _create_ma(self, fil_dict, rt='LP'):
        """
        Calculate coefficients and P/Z for moving average filter based on
        filter length L = N + 1 and number of cascaded stages and save the 
        result in the filter dictionary.
        """
        b = 1.
        k = 1.
        L = self.N + 1
        
        if rt == 'LP':
            b0 = np.ones(L) #  h[n] = {1; 1; 1; ...}
            i = np.arange(1,L)

            norm = L

        elif rt == 'HP':
            b0 = np.ones(L)
            b0[::2] = -1. # h[n] = {1; -1; 1; -1; ...}
            
            i = np.arange(L)
            if (L % 2 == 0): # even order, remove middle element
                i = np.delete(i ,round(L/2.))
            else: # odd order, shift by 0.5 and remove middle element
                i = np.delete(i, int(L/2.)) + 0.5

            norm = L
            
        elif rt == 'BP':
            # N is even, L is odd
            b0 = np.ones(L)
            b0[1::2] = 0
            b0[::4] = -1 # h[n] = {1; 0; -1; 0; 1; ... }
            
            L = L + 1
            i = np.arange(L) # create N + 2 zeros around the unit circle, ...
            # ... remove first and middle element and rotate by L / 4 
            i = np.delete(i, [0, (L) // 2]) + L / 4         

            norm = np.sum(abs(b0))

        elif rt == 'BS':
            # N is even, L is odd
            b0 = np.ones(L)
            b0[1::2] = 0

            L = L + 1
            i = np.arange(L) # create N + 2 zeros around the unit circle and ...
            i = np.delete(i, [0, (L) // 2]) # ... remove first and middle element

            norm = np.sum(b0)

        z0 = np.exp(-2j*np.pi*i/L)            
        # calculate filter for multiple cascaded stages    
        for i in range(self.ma_stages):
            b = np.convolve(b0, b)
        z = np.repeat(z0, self.ma_stages)
        
        # normalize filter to |H_max| = 1 if checked:
        if self.chk_ma_2.isChecked():
            b = b / (norm ** self.ma_stages)
            k = 1./norm ** self.ma_stages
        p = np.zeros(len(z))
        
        # store in class attributes for the _save method
        self.zpk = [z,p,k]
        self.b = b
        self._save(fil_dict)
            

    def LPman(self, fil_dict):
        self._get_params(fil_dict)
        self._create_ma(fil_dict)
                   
#    def LPmin(self, fil_dict):
#        self._get_params(fil_dict)
#        (self.N, F, A, W) = remezord([self.F_PB, self.F_SB], [1, 0],
#            [self.A_PB, self.A_SB], Hz = 1, alg = self.alg)
#
#        self._save(fil_dict, sig.remez(self.N, F, [1, 0], weight = W, Hz = 1,
#                        grid_density = self.grid_density))

    def HPman(self, fil_dict):
        self._get_params(fil_dict)
        self._create_ma(fil_dict, rt = 'HP')
        
    def BSman(self, fil_dict):
        self._get_params(fil_dict)
        self.N = ceil_even(self.N)  # enforce even order
        self._create_ma(fil_dict, rt = 'BS')     
        
    def BPman(self, fil_dict):
        self._get_params(fil_dict)
        self.N = ceil_even(self.N)  # enforce even order
        self._create_ma(fil_dict, rt = 'BP')     

#    def HPmin(self, fil_dict):
#        self._get_params(fil_dict)
#        (self.N, F, A, W) = remezord([self.F_SB, self.F_PB], [0, 1],
#            [self.A_SB, self.A_PB], Hz = 1, alg = self.alg)
##        
#
#        if (self.N % 2 == 0): # even order
#            self._save(fil_dict, sig.remez(self.N, F,[0, 1], weight = W, Hz = 1, 
#                        type = 'hilbert', grid_density = self.grid_density))
#        else:
#            self._save(fil_dict, sig.remez(self.N, F,[0, 1], weight = W, Hz = 1, 
#                        type = 'bandpass', grid_density = self.grid_density))


#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from ..compat import QApplication
   
    app = QApplication(sys.argv)
    
    # instantiate filter widget
    filt = MA()
    filt.construct_UI()
    wdg_ma = getattr(filt, 'wdg_fil')

    layVDynWdg = QVBoxLayout()
    layVDynWdg.addWidget(wdg_ma, stretch = 1)

    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0]['zpk']) # return results in default format

    form = QFrame()
    form.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
    form.setLayout(layVDynWdg)    

    form.show()
    

    app.exec_()
    #------------------------------------------------------------------------------

