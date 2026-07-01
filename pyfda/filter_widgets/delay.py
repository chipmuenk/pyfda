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
import numpy as np

from pyfda.filterbroker import fb_get, fb_set
from pyfda.libs.pyfda_lib import safe_eval
from pyfda.libs.compat import QWidget, QLabel, QLineEdit, pyqtSignal, QVBoxLayout, QHBoxLayout
from pyfda.libs.pyfda_qt_lib import popup_warning, emit
from pyfda.libs.pyfda_sig_lib import fil_save

__version__ = "1.0"

classes = {'Delay':'Delay'} #: Dict containing class name : display name

class Delay(QWidget):
    """
    Create a dummy delay to demonstrate the effect of delays on the phase or to
    debug fixpoint quantizers.
    """

    FRMT = 'zpk' # output format of delay filter widget
    has_ui = True #: Flag whether the filter class has a UI or not
    info ="""
    **Delay widget**

    allows entering the number of **delays** :math:`N` :math:`T_S`. It is treated as a FIR filter,
    the number of delays is directly translated to a number of poles (:math:`N > 0`)
    or zeros (:math:`N < 0`).

    Obviously, there is no minimum design algorithm or no design algorithm at all :-)
    """

    sig_tx = pyqtSignal(object)

    def __init__(self):
        super().__init__()

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
        self.construct_ui()  # create subwidgets for filter design

    # -------------------------------------------------------------------------
    def emit(self, dict_sig: dict) -> None:
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    #--------------------------------------------------------------------------
    def construct_ui(self) -> None:
        """
        Create additional subwidget(s) needed for filter design:
        These subwidgets are instantiated dynamically when needed in
        select_filter.py using the handle to the filter instance.
        """

        self.lbl_delay = QLabel("Delays", self)
        self.lbl_delay.setObjectName('wdg_lbl_delays')
        self.led_delay = QLineEdit(self)
        self.led_delay.setText(str(self.N))
        self.led_delay.setObjectName('wdg_led_delay')
        self.led_delay.setToolTip("Number of delays, N > 0 produces poles, N < 0 zeros.")

        self.layHWin = QHBoxLayout()
        self.layHWin.setObjectName('wdg_layGWin')
        self.layHWin.addWidget(self.lbl_delay)
        self.layHWin.addWidget(self.led_delay)
        self.layHWin.setContentsMargins(0,0,0,0)
        # Widget containing all subwidgets (cmbBoxes, Labels, lineEdits)
        self.wdg_fil = QWidget(self)
        self.wdg_fil.setObjectName('wdg_fil')
        self.wdg_fil.setLayout(self.layHWin)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.led_delay.editingFinished.connect(self._update_UI)
        # fires when edited line looses focus or when RETURN is pressed
        #----------------------------------------------------------------------

        self.dict2filter_params() # get initial / last setting from dictionary
        self._update_UI()

    def _update_UI(self) -> None:
        """
        Update UI when line edit field is changed (here, only the text is read
        and converted to integer) and store parameter settings in filter
        dictionary
        """
        self.N = safe_eval(self.led_delay.text(), self.N,
                                      sign="poszero", return_type='int')
        self.led_delay.setText(str(self.N))

        fb_set('wdg_fil', 'N', self.N)  # store in filter dictionary
        # fb_set('filter_widgets', 'delay', {'N': self.N})  # store in filter widgets dict

        # sig_tx -> select_filter -> filter_specs
        self.emit({'filt_changed': 'delay'})

    def dict2filter_params(self) -> None:
        """
        Reload parameter(s) from filter dictionary (if they exist) and set
        corresponding UI elements. dict2filter_params() is called upon initialization
        and when the filter is loaded from disk.
        """
        wdg_fil_par = fb_get('filter_widgets', 'delay', verbose=False)
        if wdg_fil_par and 'N' in wdg_fil_par:
            self.N = wdg_fil_par['N']
            self.led_delay.setText(str(self.N))

    def _get_params(self) -> None:
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N = fb_get('N')  # filter order is translated to numb. of delays

    def _test_n(self) -> bool:
        """
        Warn the user if the calculated order is too high for a reasonable filter
        design.
        """
        if self.N > 2000:
            return popup_warning(self, self.N, "Delay")
        return True

    def _save(self, arg=None) -> None:
        """
        Convert between poles / zeros / gain, filter coefficients (polynomes)
        and second-order sections and store all available formats in the global
        filter dictionary.
        """
        if arg is None:
            arg = np.zeros(self.N)
            #arg =[[0], np.zeros(self.N), 1] # crashes coeff tab
        fil_save(arg, self.FRMT, __name__)

    def APman(self) -> int:
        """
        Design an allpass filter with parameters from global dict

        Returns
        -------
        int
            0: success, -1: error
        """
        self._get_params()
        if not self._test_n():
            return -1
        self._save()
        return 0

#------------------------------------------------------------------------------

if __name__ == '__main__':
    # Run this module standalone with 'python -m pyfda.filter_widgets.delay'
    import sys
    from pyfda.libs.compat import QApplication, QFrame

    app = QApplication(sys.argv)

    # instantiate filter widget
    filt = Delay()
    filt.construct_ui()

    layVDynWdg = QVBoxLayout()
    layVDynWdg.addWidget(filt.wdg_fil, stretch = 1)

    filt.APman()  # design a low-pass with parameters from global dict
    print(fb_get(filt.FRMT)) # return results in default format

    frm_main = QFrame()
    frm_main.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
    frm_main.setLayout(layVDynWdg)

    form = frm_main

    form.show()

    app.exec_()
