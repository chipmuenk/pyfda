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
    1.3: new public methods destruct_ui + construct_ui (no longer called by __init__)
    1.4: module attribute `filter_classes` contains class name and combo box name
         instead of class attribute `name`
         `FRMT` is now a class attribute
    2.0: Specify the parameters for each subwidget as tuples in a dict where the
         first element controls whether the widget is visible and / or enabled.
         This dict is now called self.rt_dict. When present, the dict self.rt_dict_add
         is read and merged with the first one.
    2.1: Remove method destruct_ui and attributes self.wdg and self.hdl

   :2.2: Rename `filter_classes` -> `classes`, remove Py2 compatibility
"""
import logging

from scipy.signal import remez
import numpy as np

from pyfda.libs.compat import QWidget, QLabel, QLineEdit, pyqtSignal, QVBoxLayout, QHBoxLayout
from pyfda.filterbroker import fb_get, fb_set
from pyfda.libs.pyfda_qt_lib import popup_warning, emit
from pyfda.libs.pyfda_lib import round_odd, ceil_even, safe_eval, debug_exception
from pyfda.libs.pyfda_sig_lib import fil_save
from .common import remezord

logger = logging.getLogger(__name__)

__version__ = "2.2"

classes = {'Equiripple':'Equiripple'} #: Dict containing class name : display name

class Equiripple(QWidget):
    """
    Design digital FIR Equiripple filters (LP, HP, BP, BS) with fixed or minimum
    order, return the filter design in 'ba' format.
    This is more or less a wrapper around the ``scipy.signal.remez()`` and
    ``libs.pyfda_lib.remezord()`` routines.
    """

    FRMT = 'ba' # output format of filter design routines ('zpk' / 'ba' / 'sos')
            # currently, only 'ba' is supported for equiripple routines
    has_ui = True #: Flag whether the filter class has a UI or not
    info = """
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

    ``scipy.signal.remez()``, ``libs.pyfda_lib.remezord()``
    """

    sig_tx = pyqtSignal(object)

    def __init__(self, objectName='equiripple_inst'):
        super().__init__()

        self.setObjectName(objectName)
        self.grid_density = 16

        self.ft = 'FIR'

        self.rt_dicts = ('com',)

        self.rt_dict = {
            'COM': {'man': {'fo':('a', 'N'),
                            'msg':('a',
                                "<span>Enter desired filter order <b><i>N</i></b>, corner "
                                "frequencies of pass and stop band(s), <b><i>F<sub>PB</sub>"
                                "</i></b>&nbsp; and <b><i>F<sub>SB</sub></i></b>&nbsp;, and "
                                "relative weight values <b><i>W&nbsp; </i></b> (1 ... 10<sup>6"
                                "</sup>) to specify how well the bands are approximated."
                                "</span>")
                            },
                    'min': {'fo':('d', 'N'),
                            'msg': ('a',
                                "<span>Enter the maximum pass band ripple <b><i>A<sub>PB</sub>"
                                "</i></b>, minimum stop band attenuation <b><i>A<sub>SB</sub></i>"
                                "</b> and the corresponding corner frequencies of pass and "
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
        self.info_doc.append(remez.__doc__)
        self.info_doc.append('remezord()\n==========')
        self.info_doc.append(remezord.__doc__)

        self.construct_ui()

    # -------------------------------------------------------------------------
    def emit(self, dict_sig):
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    #--------------------------------------------------------------------------
    def construct_ui(self):
        """
        Create additional subwidget(s) needed for filter design:
        These subwidgets are instantiated dynamically when needed in
        select_filter.py using the handle to the filter instance.
        """
        self.lbl_remez_1 = QLabel("Grid Density", self)
        self.lbl_remez_1.setObjectName('wdg_lbl_remez_1')
        self.led_remez_1 = QLineEdit(self)
        self.led_remez_1.setText(str(self.grid_density))
        self.led_remez_1.setObjectName('wdg_led_remez_1')
        self.led_remez_1.setToolTip(
            "Number of frequency points for Remez algorithm. Increase the\n"
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
        self.led_remez_1.editingFinished.connect(self.ui2dict)
        # fires when edited line looses focus or when RETURN is pressed
        #----------------------------------------------------------------------

        self.dict2filter_params() # get initial / last setting from dictionary

    def ui2dict(self):
        """
        Update filter dict when line edit field is changed
        """
        self.grid_density = safe_eval(self.led_remez_1.text(), self.grid_density,
                                      return_type='int', sign='pos' )
        self.led_remez_1.setText(str(self.grid_density))

        fb_set('filter_widgets', 'equiripple', {'grid_density': self.grid_density})

        # sig_tx -> select_filter -> filter_specs
        self.emit({'filt_changed': 'equiripple'})


    def dict2filter_params(self):
        """
        Reload parameter(s) from filter dictionary (if they exist) and set
        corresponding UI elements. dict2filter_params() is called upon initialization
        and when the filter is loaded from disk.
        """
        if 'equiripple' in fb_get('filter_widgets')\
                and 'grid_density' in fb_get('filter_widgets', 'equiripple'):
            self.grid_density = fb_get('filter_widgets', 'equiripple', 'grid_density')
        else:
            self.grid_density = 16
            fb_set('filter_widgets', 'equiripple', {'grid_density': 16})

        self.led_remez_1.setText(str(self.grid_density))


    def _get_params(self) -> None:
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N     = fb_get('N') + 1  # remez algorithms expects number of taps
                                        # which is larger by one than the order!!
        self.F_PB  = fb_get('F_PB')
        self.F_SB  = fb_get('F_SB')
        self.F_PB2 = fb_get('F_PB2')
        self.F_SB2 = fb_get('F_SB2')
        # remez amplitude specs are linear (not in dBs)
        self.A_PB  = fb_get('A_PB')
        self.A_PB2 = fb_get('A_PB2')
        self.A_SB  = fb_get('A_SB')
        self.A_SB2 = fb_get('A_SB2')

        self.alg = 'ichige'

    def _test_n(self) -> bool:
        """
        Warn the user if the calculated order is too high for a reasonable filter
        design.
        """
        if self.N > 2000:
            return popup_warning(self, self.N, "Equiripple")
        return True

    def _save(self, arg) -> int:
        """
        Convert between poles / zeros / gain, filter coefficients (polynomes)
        and second-order sections and store all available formats in the filter
        dictionary .
        """
        # verify whether filter order is low enough
        if not self._test_n():
            return -1
        try:
            fil_save(arg, self.FRMT, __name__)
        except Exception as e:
            # catch exception due to malformatted coefficients:
            logger.error("While saving the equiripple filter design, "
                         "the following error occurred:\n%s", e)
            debug_exception()
            return -1

        if fb_get('fo') == 'min':
            fb_set('N', self.N - 1)  # yes, update filterbroker
        return 0

    def LPman(self) -> int:
        """
        Design a low-pass FIR filter with given order using the Remez exchange algorithm.

        The corner frequencies and the weights for passband and stopband are contained in the
        instance parameters and in the filter dict, they are retrieved using `fb_get()`.


        - 'W_PB': Weight for the passband.
        - 'W_SB': Weight for the stopband.
        - Other keys required by `_get_params`.

        Returns:
            int: Returns -1 if the filter order (`self.N`) is too high or another error occurs,
                otherwise the designed filter coefficients are saved in the filter dict.

        Notes:
            - The method `_get_params` is used to extract parameters from the filter dictionary.
            - The method `_test_n` is used to validate the filter order (`self.N`).
            - The filter design uses a normalized frequency range [0, 0.5].
            - The `grid_density` attribute controls the density of the frequency grid
              used in the Remez algorithm.
        """
        self._get_params()
        return self._save(
            remez(self.N,[0, self.F_PB, self.F_SB, 0.5], [1, 0],
                  weight = [fb_get('W_PB'), fb_get('W_SB')], fs = 1,
                  grid_density = self.grid_density))
    def LPmin(self) -> int:
        """
        Design a low-pass FIR filter using the Remez exchange algorithm.

        This function computes the filter order, frequency bands, desired
        amplitudes, and weights using the `remezord` utility, and then
        designs the filter using the `remez` function. The designed filter
        coefficients are saved in the provided filter dictionary.

        Filter specifications are read from the filter dictionary with `fb_get()`,
        These are passeband and stopband frequencies (`F_PB`, `F_SB`),
        passband and stopband ripple (`A_PB`, `A_SB`), and other parameters.

        Returns
        -------
        err_code: int
            Returns -1 if the computed filter order is invalid, otherwise the
            filter coefficients are saved in the filter dictionary using `fb_set()`.
        """
        self._get_params()
        (self.N, F, A, W) = remezord([self.F_PB, self.F_SB], [1, 0],
                                     [self.A_PB, self.A_SB], fs = 1, alg = self.alg)
        # A is always [1, 0] for LP filters
        fb_set('W_PB', W[0])
        fb_set('W_SB', W[1])
        return self._save(
            remez(self.N, F, A, weight = W, fs = 1, grid_density = self.grid_density))

    def HPman(self) -> int:
        """
        Design a low-pass FIR filter with given order using the Remez exchange algorithm.
        For more details, see the `LPman` method.
        """
        self._get_params()
        if self.N % 2 == 0: # even order, use odd symmetry (type III)
            return self._save(
                remez(self.N,[0, self.F_SB, self.F_PB, 0.5], [0, 1],
                      weight = [fb_get('W_SB'), fb_get('W_PB')], fs = 1,
                      type = 'hilbert', grid_density = self.grid_density))
        # odd order,
        return self._save(
            remez(self.N,[0, self.F_SB, self.F_PB, 0.5], [0, 1],
                    weight = [fb_get('W_SB'), fb_get('W_PB')], fs = 1,
                    type = 'bandpass', grid_density = self.grid_density))

    def HPmin(self) -> int:
        """
        Design a high-pass FIR filter with minimum order using the Remez exchange algorithm.
        For more details, see the `LPmin` method.
        """
        self._get_params()
        (self.N, F, A, W) = remezord([self.F_SB, self.F_PB], [0, 1],
                                     [self.A_SB, self.A_PB], fs = 1, alg = self.alg)
        # A is always [0, 1] for HP filters

        # self.N = ceil_odd(N)  # enforce odd order
        fb_set('W_SB', W[0])
        fb_set('W_PB', W[1])
        if self.N % 2 == 0: # even order
            return self._save(
                remez(self.N, F, A, weight = W, fs = 1, type = 'hilbert',
                      grid_density = self.grid_density))
        # odd order
        return self._save(
            remez(self.N, F, A, weight = W, fs = 1, type = 'bandpass',
                    grid_density = self.grid_density))

    # For BP and BS, F_PB and F_SB have two elements each
    def BPman(self) -> int:
        """
        Design a band-pass FIR filter with given order using the Remez exchange algorithm.
        For more details, see the `LPman` method.
        """
        self._get_params()
        return self._save(
            remez(self.N, [0, self.F_SB, self.F_PB, self.F_PB2, self.F_SB2, 0.5], [0, 1, 0],
                  weight = [fb_get('W_SB'), fb_get('W_PB'), fb_get('W_SB2')], fs = 1,
                  grid_density = self.grid_density))

    def BPmin(self) -> int:
        """
        Design a band-pass FIR filter with minimum order using the Remez exchange algorithm.
        For more details, see the `LPmin` method.
        """
        self._get_params()
        (self.N, F, A, W) = remezord([self.F_SB, self.F_PB, self.F_PB2, self.F_SB2], [0, 1, 0],
                                     [self.A_SB, self.A_PB, self.A_SB2], fs = 1, alg = self.alg)
        # A is always [0, 1, 0] for BP filters
        fb_set('W_SB', W[0])
        fb_set('W_PB', W[1])
        fb_set('W_SB2', W[2])
        return self._save(
            remez(self.N, F, A, weight = W, fs = 1, grid_density = self.grid_density))

    def BSman(self) -> int:
        """
        Design a band-stop FIR filter with given order using the Remez exchange algorithm.
        For more details, see the `LPman` method.
        """
        self._get_params()
        self.N = round_odd(self.N) # enforce odd order
        return self._save(
            remez(self.N,[0, self.F_PB, self.F_SB, self.F_SB2, self.F_PB2, 0.5], [1, 0, 1],
                  weight = [fb_get('W_PB'), fb_get('W_SB'), fb_get('W_PB2')], fs = 1,
                  grid_density = self.grid_density))

    def BSmin(self) -> int:
        """
        Design a band-stop FIR filter with minimum order using the Remez exchange algorithm.
        For more details, see the `LPmin` method.
        """
        self._get_params()
        (self.N, F, A, W) = remezord([self.F_PB, self.F_SB, self.F_SB2, self.F_PB2], [1, 0, 1],
                                [self.A_PB, self.A_SB, self.A_PB2], fs = 1, alg = self.alg)
        # A is always [1, 0, 1] for BS filters
        fb_set('W_PB', W[0])
        fb_set('W_SB', W[1])
        fb_set('W_PB2', W[2])
        return self._save(
            remez(self.N, F, A, weight = W, fs = 1, grid_density = self.grid_density))

    def HILman(self) -> int:
        """
        Design a Hilbert FIR filter with given order using the Remez exchange algorithm.
        The Hilbert filter is a special case of the band-pass filter with a wide passband,
        used to shift the phase of the input signal by 90 degrees.
        """
        self._get_params()
        return self._save(
            remez(self.N,[0, self.F_SB, self.F_PB, self.F_PB2, self.F_SB2, 0.5], [0, 1, 0],
                  weight = [fb_get('W_SB'), fb_get('W_PB'), fb_get('W_SB2')], fs = 1,
                  type = 'hilbert', grid_density = self.grid_density))

    def DIFFman(self) -> int:
        """
        Design a FIR differentiator with given order using the Remez exchange algorithm.
        """
        self._get_params()
        self.N = ceil_even(self.N) # enforce even order
        if self.F_PB < 0.1:
            logger.warning(
                "Relative bandwidth %s for pass band is too low, "
                "inreasing to 0.1.", self.F_PB)
            self.F_PB = 0.1
            fb_set('F_PB', self.F_PB)
            self.emit({'specs_changed': 'equiripple'})

        return self._save(
            remez(self.N, [0, self.F_PB], [np.pi * fb_get('W_PB')], fs = 1,
                  type = 'differentiator', grid_density = self.grid_density))

#------------------------------------------------------------------------------

if __name__ == '__main__':
    # run module standalone using "python -m pyfda.filter_widgets.equiripple"
    import sys
    from pyfda.libs.compat import QApplication, QFrame

    app = QApplication(sys.argv)

    # instantiate filter widget
    filt = Equiripple()

    layVDynWdg = QVBoxLayout()
    layVDynWdg.addWidget(filt.wdg_fil, stretch = 1)

    filt.LPman()  # design a low-pass with parameters from global dict
    print(fb_get(filt.FRMT)) # return results in default format

    frm_main = QFrame()
    frm_main.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
    frm_main.setLayout(layVDynWdg)

    form = frm_main

    form.show()

    app.exec_()
