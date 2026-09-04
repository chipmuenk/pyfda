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

API version info
----------------

    1.0: initial working release
    1.1: mark private methods as private
    1.2: new API using fil_save
    1.4: module attribute `filter_classes` contains class name and combo box name
         instead of class attribute `name`
         `FRMT` is now a class attribute
    2.0: Specify the parameters for each subwidget as tuples in a dict where the
         first element controls whether the widget is visible and / or enabled.
         This dict is now called self.rt_dict. When present, the dict self.rt_dict_add
         is read and merged with the first one.
    2.1: Remove method destruct_ui and attributes self.wdg and self.hdl
    2.2: Rename `filter_classes` -> `classes`, remove Py2 compatibility
    2.3: Add `has_ui` attribute to filter classes
"""
import logging

from scipy.signal import remez
import numpy as np

from pyfda.libs.compat import QWidget, QLabel, QLineEdit, pyqtSignal, QVBoxLayout, QHBoxLayout
from pyfda.filterbroker import fb_get, fb_set
from pyfda.libs.pyfda_qt_lib import popup_warning, emit
from pyfda.libs.pyfda_lib import safe_eval # debug_exception
from pyfda.libs.special_functions import round_odd, ceil_even
from pyfda.libs.pyfda_sig_lib import fil_save
from .common import remezord

logger = logging.getLogger(__name__)

__version__ = "2.3"

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
    (equiripple) :math:`a_pb` and :math:`a_sb` in both pass and stop band.

    The filter-coefficients are calculated in such a way that the transfer function
    minimizes the maximum error (**Minimax** design) between the desired gain and the
    realized gain in the specified frequency bands using the **Remez** exchange algorithm.
    The filter design algorithm is known as **Parks-McClellan** algorithm, in
    Matlab (R) it is called ``firpm``.

    Manual filter order design requires specifying the frequency bands (:math:`f_pb`,
    :math:`f_SB` etc.), the filter order :math:`N` and weight factors :math:`w_pb`,
    :math:`w_sb` etc.) for individual bands.

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
            'lp': {'man':{'wspecs': ('a','w_pb','w_sb'),
                          'tspecs': ('u', {'frq':('a','f_pb','f_sb'),
                                           'amp':('u','a_pb','a_sb')})
                          },
                   'min':{'wspecs': ('d','w_pb','w_sb'),
                          'tspecs': ('a', {'frq':('a','f_pb','f_sb'),
                                           'amp':('a','a_pb','a_sb')})
                        }
                },
            'hp': {'man':{'wspecs': ('a','w_sb','w_pb'),
                          'tspecs': ('u', {'frq':('a','f_sb','f_pb'),
                                           'amp':('u','a_sb','a_pb')})
                         },
                   'min':{'wspecs': ('d','w_sb','w_pb'),
                          'tspecs': ('a', {'frq':('a','f_sb','f_pb'),
                                           'amp':('a','a_sb','a_pb')})
                         }
                    },
            'bp': {'man':{'wspecs': ('a','w_sb','w_pb','w_sb2'),
                          'tspecs': ('u', {'frq':('a','f_sb','f_pb','f_pb2','f_sb2'),
                                           'amp':('u','a_sb','a_pb','a_sb2')})
                         },
                   'min':{'wspecs': ('d','w_sb','w_pb','w_sb2'),
                          'tspecs': ('a', {'frq':('a','f_sb','f_pb','f_pb2','f_sb2'),
                                           'amp':('a','a_sb','a_pb','a_sb2')})
                         },
                    },
            'bs': {'man':{'wspecs': ('a','w_pb','w_sb','w_pb2'),
                          'tspecs': ('u', {'frq':('a','f_pb','f_sb','f_sb2','f_pb2'),
                                           'amp':('u','a_pb','a_sb','a_pb2')})
                          },
                   'min':{'wspecs': ('d','w_pb','w_sb','w_pb2'),
                          'tspecs': ('a', {'frq':('a','f_pb','f_sb','f_sb2','f_pb2'),
                                           'amp':('a','a_pb','a_sb','a_pb2')})
                        }
                },
            'hil': {'man':{'wspecs': ('a','w_sb','w_pb','w_sb2'),
                           'tspecs': ('u', {'frq':('a','f_sb','f_pb','f_pb2','f_sb2'),
                                           'amp':('u','a_sb','a_pb','a_sb2')})
                         }
                    },
            'diff': {'man':{'wspecs': ('a','w_pb'),
                            'tspecs': ('u', {'frq':('a','f_pb'),
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

        self._construct_ui()

    # -------------------------------------------------------------------------
    def emit(self, dict_sig):
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    #--------------------------------------------------------------------------
    def _construct_ui(self):
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

        self.lay_h_win = QHBoxLayout()
        self.lay_h_win.setObjectName('wdg_layGWin')
        self.lay_h_win.addWidget(self.lbl_remez_1)
        self.lay_h_win.addWidget(self.led_remez_1)
        self.lay_h_win.setContentsMargins(0,0,0,0)
        # Widget containing all subwidgets (cmbBoxes, Labels, lineEdits)
        self.wdg_fil = QWidget(self)
        self.wdg_fil.setObjectName('wdg_fil')
        self.wdg_fil.setLayout(self.lay_h_win)

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
        self.f_pb  = fb_get('f_pb')
        self.f_sb  = fb_get('f_sb')
        self.f_pb2 = fb_get('f_pb2')
        self.f_sb2 = fb_get('f_sb2')
        # remez amplitude specs are linear (not in dBs)
        self.a_pb  = fb_get('a_pb')
        self.a_pb2 = fb_get('a_pb2')
        self.a_sb  = fb_get('a_sb')
        self.a_sb2 = fb_get('a_sb2')

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

        # try:
        #     fil_save(arg, self.FRMT, __name__)
        # except Exception as e:
        #     # catch exception due to malformatted coefficients:
        #     logger.error("While saving the equiripple filter design, "
        #                  "the following error occurred:\n%s", e)
        #     debug_exception()
        #     return -1

        fil_save(arg, self.FRMT, __name__)

        if fb_get('fo') == 'min':
            fb_set('N', self.N - 1)  # yes, update filterbroker
        return 0

    def lp_man(self) -> int:
        """
        Design a low-pass FIR filter with given order using the Remez exchange algorithm.

        The corner frequencies and the weights for passband and stopband are contained in the
        instance parameters and in the filter dict, they are retrieved using `fb_get()`.


        - 'w_pb': Weight for the passband.
        - 'w_sb': Weight for the stopband.
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
            remez(self.N,[0, self.f_pb, self.f_sb, 0.5], [1, 0],
                  weight = [fb_get('w_pb'), fb_get('w_sb')], fs = 1,
                  grid_density = self.grid_density))
    def lp_min(self) -> int:
        """
        Design a low-pass FIR filter using the Remez exchange algorithm.

        This function computes the filter order, frequency bands, desired
        amplitudes, and weights using the `remezord` utility, and then
        designs the filter using the `remez` function. The designed filter
        coefficients are saved in the provided filter dictionary.

        Filter specifications are read from the filter dictionary with `fb_get()`,
        These are passeband and stopband frequencies (`f_pb`, `f_sb`),
        passband and stopband ripple (`a_pb`, `a_sb`), and other parameters.

        Returns
        -------
        err_code: int
            Returns -1 if the computed filter order is invalid, otherwise the
            filter coefficients are saved in the filter dictionary using `fb_set()`.
        """
        self._get_params()
        (self.N, F, A, W) = remezord([self.f_pb, self.f_sb], [1, 0],
                                     [self.a_pb, self.a_sb], fs = 1, alg = self.alg)
        # A is always [1, 0] for LP filters
        fb_set('w_pb', W[0])
        fb_set('w_sb', W[1])
        return self._save(
            remez(self.N, F, A, weight = W, fs = 1, grid_density = self.grid_density))

    def hp_man(self) -> int:
        """
        Design a low-pass FIR filter with given order using the Remez exchange algorithm.
        For more details, see the `lp_man` method.
        """
        self._get_params()
        if self.N % 2 == 0: # even order, use odd symmetry (type III)
            return self._save(
                remez(self.N,[0, self.f_sb, self.f_pb, 0.5], [0, 1],
                      weight = [fb_get('w_sb'), fb_get('w_pb')], fs = 1,
                      type = 'hilbert', grid_density = self.grid_density))
        # odd order,
        return self._save(
            remez(self.N,[0, self.f_sb, self.f_pb, 0.5], [0, 1],
                    weight = [fb_get('w_sb'), fb_get('w_pb')], fs = 1,
                    type = 'bandpass', grid_density = self.grid_density))

    def hp_min(self) -> int:
        """
        Design a high-pass FIR filter with minimum order using the Remez exchange algorithm.
        For more details, see the `lp_min` method.
        """
        self._get_params()
        (self.N, F, A, W) = remezord([self.f_sb, self.f_pb], [0, 1],
                                     [self.a_sb, self.a_pb], fs = 1, alg = self.alg)
        # A is always [0, 1] for HP filters

        # self.N = ceil_odd(N)  # enforce odd order
        fb_set('w_sb', W[0])
        fb_set('w_pb', W[1])
        if self.N % 2 == 0: # even order
            return self._save(
                remez(self.N, F, A, weight = W, fs = 1, type = 'hilbert',
                      grid_density = self.grid_density))
        # odd order
        return self._save(
            remez(self.N, F, A, weight = W, fs = 1, type = 'bandpass',
                    grid_density = self.grid_density))

    # For BP and BS, f_pb and f_sb have two elements each
    def bp_man(self) -> int:
        """
        Design a band-pass FIR filter with given order using the Remez exchange algorithm.
        For more details, see the `lp_man` method.
        """
        self._get_params()
        return self._save(
            remez(self.N, [0, self.f_sb, self.f_pb, self.f_pb2, self.f_sb2, 0.5], [0, 1, 0],
                  weight = [fb_get('w_sb'), fb_get('w_pb'), fb_get('w_sb2')], fs = 1,
                  grid_density = self.grid_density))

    def bp_min(self) -> int:
        """
        Design a band-pass FIR filter with minimum order using the Remez exchange algorithm.
        For more details, see the `lp_min` method.
        """
        self._get_params()
        (self.N, F, A, W) = remezord([self.f_sb, self.f_pb, self.f_pb2, self.f_sb2], [0, 1, 0],
                                     [self.a_sb, self.a_pb, self.a_sb2], fs = 1, alg = self.alg)
        # A is always [0, 1, 0] for BP filters
        fb_set('w_sb', W[0])
        fb_set('w_pb', W[1])
        fb_set('w_sb2', W[2])
        return self._save(
            remez(self.N, F, A, weight = W, fs = 1, grid_density = self.grid_density))

    def bs_man(self) -> int:
        """
        Design a band-stop FIR filter with given order using the Remez exchange algorithm.
        For more details, see the `lp_man` method.
        """
        self._get_params()
        self.N = round_odd(self.N) # enforce odd order
        return self._save(
            remez(self.N,[0, self.f_pb, self.f_sb, self.f_sb2, self.f_pb2, 0.5], [1, 0, 1],
                  weight = [fb_get('w_pb'), fb_get('w_sb'), fb_get('w_pb2')], fs = 1,
                  grid_density = self.grid_density))

    def bs_min(self) -> int:
        """
        Design a band-stop FIR filter with minimum order using the Remez exchange algorithm.
        For more details, see the `lp_min` method.
        """
        self._get_params()
        (self.N, F, A, W) = remezord([self.f_pb, self.f_sb, self.f_sb2, self.f_pb2], [1, 0, 1],
                                [self.a_pb, self.a_sb, self.a_pb2], fs = 1, alg = self.alg)
        # A is always [1, 0, 1] for BS filters
        fb_set('w_pb', W[0])
        fb_set('w_sb', W[1])
        fb_set('w_pb2', W[2])
        return self._save(
            remez(self.N, F, A, weight = W, fs = 1, grid_density = self.grid_density))

    def hil_man(self) -> int:
        """
        Design a Hilbert FIR filter with given order using the Remez exchange algorithm.
        The Hilbert filter is a special case of the band-pass filter with a wide passband,
        used to shift the phase of the input signal by 90 degrees.
        """
        self._get_params()
        return self._save(
            remez(self.N,[0, self.f_sb, self.f_pb, self.f_pb2, self.f_sb2, 0.5], [0, 1, 0],
                  weight = [fb_get('w_sb'), fb_get('w_pb'), fb_get('w_sb2')], fs = 1,
                  type = 'hilbert', grid_density = self.grid_density))

    def diff_man(self) -> int:
        """
        Design a FIR differentiator with given order using the Remez exchange algorithm.
        """
        self._get_params()
        self.N = ceil_even(self.N) # enforce even order
        if self.f_pb < 0.1:
            logger.warning(
                "Relative bandwidth %s for pass band is too low, "
                "inreasing to 0.1.", self.f_pb)
            self.f_pb = 0.1
            fb_set('f_pb', self.f_pb)
            self.emit({'specs_changed': 'equiripple'})

        return self._save(
            remez(self.N, [0, self.f_pb], [np.pi * fb_get('w_pb')], fs = 1,
                  type = 'differentiator', grid_density = self.grid_density))

#------------------------------------------------------------------------------

if __name__ == '__main__':
    # run module standalone using "python -m pyfda.filter_widgets.equiripple"
    import sys
    from pyfda.libs.compat import QApplication, QFrame

    app = QApplication(sys.argv)

    # instantiate filter widget
    filt = Equiripple()

    lay_v_dyn_wdg = QVBoxLayout()
    lay_v_dyn_wdg.addWidget(filt.wdg_fil, stretch = 1)

    filt.lp_man()  # design a low-pass with parameters from global dict
    print(fb_get(filt.FRMT)) # return results in default format

    frm_main = QFrame()
    frm_main.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
    frm_main.setLayout(lay_v_dyn_wdg)

    form = frm_main

    form.show()

    app.exec_()
