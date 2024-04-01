# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Design a simple delay for demonstrating the effect of latency and for debugging

Attention: 
This class is re-instantiated dynamically every time the filter design method
is selected, calling the __init__ method.

API version info:   
    1.0: initial working release
"""
import logging
logger = logging.getLogger(__name__)

from pyfda.libs.compat import QWidget, QLabel, QLineEdit, pyqtSignal, QVBoxLayout, QHBoxLayout

import scipy.signal as sig
import numpy as np

import pyfda.filterbroker as fb
from pyfda.libs.pyfda_qt_lib import popup_warning
from pyfda.libs.pyfda_lib import fil_save, safe_eval

__version__ = "1.0"

classes = {'AllpPZ':'Allpass (P)'} #: Dict containing class name : display name

class AllpPZ(QWidget):

    FRMT = 'zpk' # output format of delay filter widget

    info ="""
**Allpass widget**

allows entering the two **poles** :math:`p`. **zeros** are calculated from the 
reciprocal values of the poles. There is no minimum algorithm, only the two 
poles can be entered manually.

    """

    sig_tx = pyqtSignal(object)
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self):
        QWidget.__init__(self)

        self.p = [0.5, 0.5j]
        
        self.ft = 'IIR'
        
        # the following defines which subwidgets are "a"ctive, "i"nvisible or "d"eactivated
        self.rt_dicts = ('com',)
        self.rt_dict = {
            'COM': {'man': {'fo':('d', 'N'),
                            'msg':('a', 
                                "<span>Enter poles  <b><i>p</i></b> for allpass function,"
                                "zeros will be calculated.</span>")
                            },
                },
            'AP': {'man':{}
                    }
            }

        self.info_doc = []

    #--------------------------------------------------------------------------
    def construct_UI(self):
        """
        Create additional subwidget(s) needed for filter design:
        These subwidgets are instantiated dynamically when needed in 
        select_filter.py using the handle to the filter instance, fb.fil_inst.
        """
        self.lbl_pole1 = QLabel("Pole 1", self)
        self.lbl_pole1.setObjectName('wdg_lbl_pole1')
        self.led_pole1 = QLineEdit(self)
        self.led_pole1.setText(str(self.p[0]))
        self.led_pole1.setObjectName('wdg_led_pole1')
        self.led_pole1.setToolTip("Pole 1 for allpass filter")
        
        self.lbl_pole2 = QLabel("Pole 2", self)
        self.lbl_pole2.setObjectName('wdg_lbl_pole2')
        self.led_pole2 = QLineEdit(self)
        self.led_pole2.setText(str(self.p[1]))
        self.led_pole2.setObjectName('wdg_led_pole2')
        self.led_pole2.setToolTip("Pole 2 for allpass filter")

        self.layHWin = QHBoxLayout()
        self.layHWin.setObjectName('wdg_layGWin')
        self.layHWin.addWidget(self.lbl_pole1)
        self.layHWin.addWidget(self.led_pole1)
        self.layHWin.addWidget(self.lbl_pole2)
        self.layHWin.addWidget(self.led_pole2)        
        self.layHWin.setContentsMargins(0,0,0,0)
        # Widget containing all subwidgets (cmbBoxes, Labels, lineEdits)
        self.wdg_fil = QWidget(self)
        self.wdg_fil.setObjectName('wdg_fil')
        self.wdg_fil.setLayout(self.layHWin)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.led_pole1.editingFinished.connect(self._update_UI)
        self.led_pole2.editingFinished.connect(self._update_UI)
        # fires when edited line looses focus or when RETURN is pressed
        #----------------------------------------------------------------------

        self._load_dict() # get initial / last setting from dictionary
        self._update_UI()
        
    def _update_UI(self):
        """
        Update UI when line edit field is changed (here, only the text is read
        and converted to integer) and store parameter settings in filter 
        dictionary
        """
        self.p[0] = safe_eval(self.led_pole1.text(), self.p[0], return_type='cmplx')
        self.led_pole1.setText(str(self.p[0]))

        self.p[1] = safe_eval(self.led_pole2.text(), self.p[1], return_type='cmplx')
        self.led_pole2.setText(str(self.p[1]))

        if not 'wdg_fil' in fb.fil[0]:
            fb.fil[0].update({'wdg_fil':{}})
        fb.fil[0]['wdg_fil'].update({'poles':{'p1':self.p[0], 'p2':self.p[1]}
                                    })
        
        # sig_tx -> select_filter -> filter_specs   
        self.emit({'filt_changed': 'pole_1_2'})


    def _load_dict(self):
        """
        Reload parameter(s) from filter dictionary (if they exist) and set 
        corresponding UI elements. _load_dict() is called upon initialization
        and when the filter is loaded from disk.
        """
        if 'wdg_fil' in fb.fil[0] and 'poles' in fb.fil[0]['wdg_fil']:
            wdg_fil_par = fb.fil[0]['wdg_fil']['poles']
            if 'p1' in wdg_fil_par:
                self.p1 = wdg_fil_par['p1']
                self.led_pole1.setText(str(self.p1))
            if 'p2' in wdg_fil_par:
                self.p2 = wdg_fil_par['p2']
                self.led_pole2.setText(str(self.p2))

    def _get_params(self, fil_dict):
        """
        Get parameters needed for filter design from the passed dictionary and 
        translate them to instance parameters, scaling / transforming them if needed.
        """
        #self.p1     = fil_dict['zpk'][1][0]  # get the first and second pole
        #self.p2     = fil_dict['zpk'][1][1]  # from central filter dect
        logger.info(fil_dict['zpk'])
        
    def _test_poles(self):
        """
        Warn the user if one of the poles is outside the unit circle
        """
        if abs(self.p[0]) >= 1 or abs(self.p[1])  >=1:
            return popup_warning(self, self.p[0], "Delay")
        else:
            return True

    def _save(self, fil_dict, arg=None):
        """
        Convert between poles / zeros / gain, filter coefficients (polynomes)
        and second-order sections and store all available formats in the passed
        dictionary 'fil_dict'.
        """
        if arg is None:
            logger.error("Passed empty filter dict")
        logger.info(arg)
        fil_save(fil_dict, arg, self.FRMT, __name__)
        
        fil_dict['N'] = len(self.p)


#------------------------------------------------------------------------------
# Filter design routines
#------------------------------------------------------------------------------
# The method name MUST be "FilterType"+"MinMan", e.g. LPmin or BPman

    def APman(self, fil_dict):
        """
        Calculate z =1/p* for a given set of poles p. If p=0, set z=0.
        The gain factor k is calculated from z and p at z = 1.
        """
        self._get_params(fil_dict) # not needed here
        if not self._test_poles():
            return -1
        self.z=[0,0]
        if self.p[0] != 0:
            self.z[0] = np.conj(1/self.p[0])
        if type(self.p[0]) == complex:
            pass
        if self.p[1] != 0:
            self.z[1] = np.conj(1/self.p[1])
        
        k = np.abs(np.polyval(np.poly(self.p),1) / np.polyval(np.poly(self.z),1))
        zpk_list = [self.z,self.p,k]

        self._save(fil_dict, zpk_list)

#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from pyfda.libs.compat import QApplication, QFrame

    app = QApplication(sys.argv)
    
    # instantiate filter widget
    filt = AllpPZ()
    filt.construct_UI()
    wdg_allpass = getattr(filt, 'wdg_fil')

    layVDynWdg = QVBoxLayout()
    layVDynWdg.addWidget(wdg_allpass, stretch = 1)
    
    filt.APman(fb.fil[0])  # design an all pass filter with parameters from global dict
    print(fb.fil[0][filt.FRMT]) # return results in default format

    frmMain = QFrame()
    frmMain.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
    frmMain.setLayout(layVDynWdg)    

    form = frmMain

    form.show()

    app.exec_()
    #------------------------------------------------------------------------------

