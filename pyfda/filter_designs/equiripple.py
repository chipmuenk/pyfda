# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Design equiripple-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in coefficients format ('ba')

Attention: 
This class is re-instantiated dynamically every time the filter design method
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
    2.1: Remove method destruct_UI and attributes self.wdg and self.hdl
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import logging
logger = logging.getLogger(__name__)

from ..compat import QWidget, QLabel, QLineEdit, pyqtSignal, QVBoxLayout, QHBoxLayout

import scipy.signal as sig
import numpy as np

import pyfda.filterbroker as fb
from pyfda.pyfda_qt_lib import qfilter_warning
from pyfda.pyfda_lib import fil_save, round_odd, ceil_even, safe_eval
from .common import remezord 

__version__ = "2.0"

filter_classes = {'Equiripple':'Equiripple'}

class Equiripple(QWidget):

    FRMT = 'ba' # output format of filter design routines 'zpk' / 'ba' / 'sos'
            # currently, only 'ba' is supported for equiripple routines

    info ="""
**Equiripple filters**

have the steepest rate of transition between the frequency response’s passband
and stopband of all FIR filters. This comes at the expense of a constant ripple
(equiripple) :math:`A_PB` and :math:`A_SB` in both pass and stop band.

The filter-coefficients are calculated in such a way that the transfer function
minimizes the maximum error (**Minimax** design) between the desired gain and the
realized gain in the specified frequency bands using the **Remez** exchange algorithm.
The filter design algorithm is known as **Parks-McClellan** algorithm, in
Matlab (R) it is called ``firpm``.

Manual filter order design requires specifying the frequency bands (:math:`F_PB`,
:math:`f_SB` etc.), the filter order :math:`N` and weight factors :math:`W_PB`,
:math:`W_SB` etc.) for individual bands.

The minimum order and the weight factors needed to fulfill the target specifications
is estimated from frequency and amplitude specifications using Ichige's algorithm.

**Design routines:**

``scipy.signal.remez()``, ``pyfda_lib.remezord()``
    """

    sig_tx = pyqtSignal(object)

    def __init__(self):
        QWidget.__init__(self)

        self.grid_density = 16

        self.ft = 'FIR'
        
        self.rt_dicts = ('com',)

        self.rt_dict = {
            'COM': {'man': {'fo':('a', 'N'),
                            'msg':('a', 
                                "<span>Enter desired filter order <b><i>N</i></b>, corner "
                                "frequencies of pass and stop band(s), <b><i>F<sub>PB</sub></i></b>"
                                "&nbsp; and <b><i>F<sub>SB</sub></i></b>&nbsp;, and relative weight "
                                "values <b><i>W&nbsp; </i></b> (1 ... 10<sup>6</sup>) to specify how well "
                                "the bands are approximated.</span>")
                            },
                    'min': {'fo':('d', 'N'),
                            'msg': ('a',
                                "<span>Enter the maximum pass band ripple <b><i>A<sub>PB</sub></i></b>, "
                                "minimum stop band attenuation <b><i>A<sub>SB</sub></i></b> "
                                "and the corresponding corner frequencies of pass and "
                                "stop band(s), <b><i>F<sub>PB</sub></i></b>&nbsp; and "
                                "<b><i>F<sub>SB</sub></i></b> .</span>")
                            }
                },
            'LP': {'man':{'wspecs': ('a','W_PB','W_SB'),
                          'tspecs': ('u', {'frq':('a','F_PB','F_SB'), 
                                           'amp':('u','A_PB','A_SB')})
                          },
                   'min':{'wspecs': ('d','W_PB','W_SB'),
                          'tspecs': ('a', {'frq':('a','F_PB','F_SB'), 
                                           'amp':('a','A_PB','A_SB')})
                        }
                },
            'HP': {'man':{'wspecs': ('a','W_SB','W_PB'),
                          'tspecs': ('u', {'frq':('a','F_SB','F_PB'), 
                                           'amp':('u','A_SB','A_PB')})
                         },
                   'min':{'wspecs': ('d','W_SB','W_PB'),
                          'tspecs': ('a', {'frq':('a','F_SB','F_PB'), 
                                           'amp':('a','A_SB','A_PB')})
                         }
                    },
            'BP': {'man':{'wspecs': ('a','W_SB','W_PB','W_SB2'),
                          'tspecs': ('u', {'frq':('a','F_SB','F_PB','F_PB2','F_SB2'), 
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                         },
                   'min':{'wspecs': ('d','W_SB','W_PB','W_SB2'),
                          'tspecs': ('a', {'frq':('a','F_SB','F_PB','F_PB2','F_SB2'), 
                                           'amp':('a','A_SB','A_PB','A_SB2')})
                         },
                    },
            'BS': {'man':{'wspecs': ('a','W_PB','W_SB','W_PB2'),
                          'tspecs': ('u', {'frq':('a','F_PB','F_SB','F_SB2','F_PB2'), 
                                           'amp':('u','A_PB','A_SB','A_PB2')})
                          },
                   'min':{'wspecs': ('d','W_PB','W_SB','W_PB2'),
                          'tspecs': ('a', {'frq':('a','F_PB','F_SB','F_SB2','F_PB2'), 
                                           'amp':('a','A_PB','A_SB','A_PB2')})
                        }
                },
            'HIL': {'man':{'wspecs': ('a','W_SB','W_PB','W_SB2'),
                           'tspecs': ('u', {'frq':('a','F_SB','F_PB','F_PB2','F_SB2'), 
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                         }
                    },
            'DIFF': {'man':{'wspecs': ('a','W_PB'),
                            'tspecs': ('u', {'frq':('a','F_PB'), 
                                           'amp':('i',)}),
                            'msg':('a',"Enter the max. frequency up to where the differentiator "
                                        "works.")
                          }
                    }
            }

        self.info_doc = []
        self.info_doc.append('remez()\n=======')
        self.info_doc.append(sig.remez.__doc__)
        self.info_doc.append('remezord()\n==========')
        self.info_doc.append(remezord.__doc__)

    #--------------------------------------------------------------------------
    def construct_UI(self):
        """
        Create additional subwidget(s) needed for filter design:
        These subwidgets are instantiated dynamically when needed in 
        select_filter.py using the handle to the filter instance, fb.fil_inst.
        """
        self.lbl_remez_1 = QLabel("Grid Density", self)
        self.lbl_remez_1.setObjectName('wdg_lbl_remez_1')
        self.led_remez_1 = QLineEdit(self)
        self.led_remez_1.setText(str(self.grid_density))
        self.led_remez_1.setObjectName('wdg_led_remez_1')
        self.led_remez_1.setToolTip("Number of frequency points for Remez algorithm. Increase the\n"
                                    "number to reduce frequency overshoot in the transition region.")

        self.layHWin = QHBoxLayout()
        self.layHWin.setObjectName('wdg_layGWin')
        self.layHWin.addWidget(self.lbl_remez_1)
        self.layHWin.addWidget(self.led_remez_1)
        self.layHWin.setContentsMargins(0,0,0,0)
        # Widget containing all subwidgets (cmbBoxes, Labels, lineEdits)
        self.wdg_fil = QWidget(self)
        self.wdg_fil.setObjectName('wdg_fil')
        self.wdg_fil.setLayout(self.layHWin)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.led_remez_1.editingFinished.connect(self._update_UI)
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
        self.grid_density = safe_eval(self.led_remez_1.text(), self.grid_density, 
                                      return_type='int', sign='pos' )
        self.led_remez_1.setText(str(self.grid_density))

        if not 'wdg_fil' in fb.fil[0]:
            fb.fil[0].update({'wdg_fil':{}})
        fb.fil[0]['wdg_fil'].update({'equiripple':
                                        {'grid_density':self.grid_density}
                                    })
        
        # sig_tx -> select_filter -> filter_specs   
        self.sig_tx.emit({'sender':__name__, 'filt_changed':'equiripple'})


    def _load_dict(self):
        """
        Reload parameter(s) from filter dictionary (if they exist) and set 
        corresponding UI elements. _load_dict() is called upon initialization
        and when the filter is loaded from disk.
        """
        if 'wdg_fil' in fb.fil[0] and 'equiripple' in fb.fil[0]['wdg_fil']:
            wdg_fil_par = fb.fil[0]['wdg_fil']['equiripple']
            if 'grid_density' in wdg_fil_par:
                self.grid_density = wdg_fil_par['grid_density']
                self.led_remez_1.setText(str(self.grid_density))


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
        
    def _test_N(self):
        """
        Warn the user if the calculated order is too high for a reasonable filter
        design.
        """
        if self.N > 2000:
            return qfilter_warning(self, self.N, "Equiripple")
        else:
            return True

    def _save(self, fil_dict, arg):
        """
        Convert between poles / zeros / gain, filter coefficients (polynomes)
        and second-order sections and store all available formats in the passed
        dictionary 'fil_dict'.
        """

        fil_save(fil_dict, arg, self.FRMT, __name__)

        if str(fil_dict['fo']) == 'min': 
            fil_dict['N'] = self.N - 1  # yes, update filterbroker


    def LPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, 
                  sig.remez(self.N,[0, self.F_PB, self.F_SB, 0.5], [1, 0],
                        weight = [fil_dict['W_PB'],fil_dict['W_SB']], Hz = 1,
                        grid_density = self.grid_density))

    def LPmin(self, fil_dict):
        self._get_params(fil_dict)
        (self.N, F, A, W) = remezord([self.F_PB, self.F_SB], [1, 0],
            [self.A_PB, self.A_SB], Hz = 1, alg = self.alg)
        if not self._test_N():
            return -1
        fil_dict['W_PB'] = W[0]
        fil_dict['W_SB'] = W[1]
        self._save(fil_dict, sig.remez(self.N, F, [1, 0], weight = W, Hz = 1,
                        grid_density = self.grid_density))


    def HPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
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
        if not self._test_N():
            return -1
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
        if not self._test_N():
            return -1
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
        if not self._test_N():
            return -1
        fil_dict['W_SB']  = W[0]
        fil_dict['W_PB']  = W[1]
        fil_dict['W_SB2'] = W[2]
        self._save(fil_dict, sig.remez(self.N,F,[0, 1, 0], weight = W, Hz = 1,
                                      grid_density = self.grid_density))

    def BSman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
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
        if not self._test_N():
            return -1
        fil_dict['W_PB']  = W[0]
        fil_dict['W_SB']  = W[1]
        fil_dict['W_PB2'] = W[2]
        self._save(fil_dict, sig.remez(self.N,F,[1, 0, 1], weight = W, Hz = 1,
                                      grid_density = self.grid_density))

    def HILman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.remez(self.N,[0, self.F_SB, self.F_PB,
                self.F_PB2, self.F_SB2, 0.5],[0, 1, 0],
                weight = [fil_dict['W_SB'],fil_dict['W_PB'], fil_dict['W_SB2']],
                Hz = 1, type = 'hilbert', grid_density = self.grid_density))

    def DIFFman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self.N = ceil_even(self.N) # enforce even order
        self._save(fil_dict, sig.remez(self.N,[0, self.F_PB],[np.pi*fil_dict['W_PB']],
                Hz = 1, type = 'differentiator', grid_density = self.grid_density))


#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from ..compat import QApplication, QFrame

    app = QApplication(sys.argv)
    
    # instantiate filter widget
    filt = Equiripple()
    filt.construct_UI()
    wdg_equiripple = getattr(filt, 'wdg_fil')

    layVDynWdg = QVBoxLayout()
    layVDynWdg.addWidget(wdg_equiripple, stretch = 1)
    
    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][filt.FRMT]) # return results in default format

    frmMain = QFrame()
    frmMain.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
    frmMain.setLayout(layVDynWdg)    

    form = frmMain

    form.show()

    app.exec_()
    #------------------------------------------------------------------------------

