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
from pyfda.libs.compat import QWidget, QLabel, QLineEdit, pyqtSignal, QVBoxLayout, QHBoxLayout

import scipy.signal as sig
import numpy as np

import pyfda.filterbroker as fb
from pyfda.libs.pyfda_qt_lib import popup_warning
from pyfda.libs.pyfda_lib import fil_save, safe_eval

__version__ = "1.0"

classes = {'Delay':'Delay'} #: Dict containing class name : display name

class Delay(QWidget):

    FRMT = 'zpk' # output format of delay filter widget

    info ="""
**Delay widget**

allows entering the number of **delays** :math:`N` :math:`T_S`. It is treated as a FIR filter,
the number of delays is directly translated to a number of poles (:math:`N > 0`) 
or zeros (:math:`N < 0`).

Obviously, there is no minimum design algorithm or no design algorithm at all :-)

    """

    sig_tx = pyqtSignal(object)
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self):
        QWidget.__init__(self)

        self.N = 5

        self.ft = 'FIR'
        
        self.rt_dicts = ('com',)

        self.rt_dict = {
            'COM': {'man': {'fo':('a', 'N'),
                            'msg':('a', 
                                "<span>Enter desired number of delays <b><i>N</i></b>.</span>")
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
        pass
# =============================================================================
#         self.lbl_delay = QLabel("Delays", self)
#         self.lbl_delay.setObjectName('wdg_lbl_delays')
#         self.led_delay = QLineEdit(self)
#         self.led_delay.setText(str(self.N))
#         self.led_delay.setObjectName('wdg_led_delay')
#         self.led_delay.setToolTip("Number of delays, N > 0 produces poles, N < 0 zeros.")
# 
#         self.layHWin = QHBoxLayout()
#         self.layHWin.setObjectName('wdg_layGWin')
#         self.layHWin.addWidget(self.lbl_delay)
#         self.layHWin.addWidget(self.led_delay)
#         self.layHWin.setContentsMargins(0,0,0,0)
#         # Widget containing all subwidgets (cmbBoxes, Labels, lineEdits)
#         self.wdg_fil = QWidget(self)
#         self.wdg_fil.setObjectName('wdg_fil')
#         self.wdg_fil.setLayout(self.layHWin)
# 
#         #----------------------------------------------------------------------
#         # SIGNALS & SLOTs
#         #----------------------------------------------------------------------
#         self.led_delay.editingFinished.connect(self._update_UI)
#         # fires when edited line looses focus or when RETURN is pressed
#         #----------------------------------------------------------------------
# 
#         self._load_dict() # get initial / last setting from dictionary
#         self._update_UI()
# =============================================================================
        
# =============================================================================
#     def _update_UI(self):
#         """
#         Update UI when line edit field is changed (here, only the text is read
#         and converted to integer) and store parameter settings in filter 
#         dictionary
#         """
#         self.N = safe_eval(self.led_delay.text(), self.N, 
#                                       sign="poszero", return_type='int')
#         self.led_delay.setText(str(self.N))
# 
#         if not 'wdg_fil' in fb.fil[0]:
#             fb.fil[0].update({'wdg_fil':{}})
#         fb.fil[0]['wdg_fil'].update({'delay':
#                                         {'N':self.N}
#                                     })
#         
#         # sig_tx -> select_filter -> filter_specs   
#         self.emit({'filt_changed': 'delay'})
# =============================================================================


    def _load_dict(self):
        """
        Reload parameter(s) from filter dictionary (if they exist) and set 
        corresponding UI elements. _load_dict() is called upon initialization
        and when the filter is loaded from disk.
        """
        if 'wdg_fil' in fb.fil[0] and 'delay' in fb.fil[0]['wdg_fil']:
            wdg_fil_par = fb.fil[0]['wdg_fil']['delay']
            if 'N' in wdg_fil_par:
                self.N = wdg_fil_par['N']
                self.led_delay.setText(str(self.N))


    def _get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N     = fil_dict['N']  # filter order is translated to numb. of delays
                                        
        
    def _test_N(self):
        """
        Warn the user if the calculated order is too high for a reasonable filter
        design.
        """
        if self.N > 2000:
            return popup_warning(self, self.N, "Delay")
        else:
            return True

    def _save(self, fil_dict, arg=None):
        """
        Convert between poles / zeros / gain, filter coefficients (polynomes)
        and second-order sections and store all available formats in the passed
        dictionary 'fil_dict'.
        """
        if arg is None:
            arg = np.zeros(self.N)
            #arg =[[0], np.zeros(self.N), 1] # crashes coeff tab
        fil_save(fil_dict, arg, self.FRMT, __name__)

    def APman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict)

#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from pyfda.libs.compat import QApplication, QFrame

    app = QApplication(sys.argv)
    
    # instantiate filter widget
    filt = Delay()
    filt.construct_UI()
    wdg_delay = getattr(filt, 'wdg_fil')

    layVDynWdg = QVBoxLayout()
    layVDynWdg.addWidget(wdg_delay, stretch = 1)
    
    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][filt.FRMT]) # return results in default format

    frmMain = QFrame()
    frmMain.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
    frmMain.setLayout(layVDynWdg)    

    form = frmMain

    form.show()

    app.exec_()
    #------------------------------------------------------------------------------

