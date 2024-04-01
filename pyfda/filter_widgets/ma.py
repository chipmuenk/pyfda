# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Design Moving-Average-Filters (LP, HP) with fixed order, return
the filter design in coefficients format ('ba') or as poles/zeros ('zpk')

Attention:
This class is re-instantiated dynamically everytime the filter design method
is selected, calling the __init__ method.

API version info:
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
    2.1: Remove method destruct_UI and attributes self.wdg and self.hdl

   :2.2: Rename `filter_classes` -> `classes`, remove Py2 compatibility
"""
from pyfda.libs.compat import (QWidget, QLabel, QLineEdit, pyqtSignal, QCheckBox,
                      QVBoxLayout, QHBoxLayout)

import numpy as np

import pyfda.filterbroker as fb
from pyfda.libs.pyfda_lib import fil_save, fil_convert, ceil_odd, safe_eval
from pyfda.libs.pyfda_qt_lib import popup_warning
from pyfda.libs.pyfda_sig_lib import zeros_with_val

__version__ = "2.2"

classes = {'MA':'Moving Average'} #: Dict containing class name : display name

class MA(QWidget):

    FRMT = ('zpk', 'ba') # output format(s) of filter design routines 'zpk' / 'ba' / 'sos'


    info ="""
**Moving average filters**

can only be specified via their length and the number of cascaded sections.

The minimum order to obtain a certain attenuation at a given frequency is
calculated via the si function.

Moving average filters can be implemented very efficiently in hard- and software
as they require no multiplications but only addition and subtractions. Probably
only the lowpass is really useful, as the other response types only filter out resp.
leave components at ``f_S/4`` (bandstop resp. bandpass) resp. leave components
near ``f_S/2`` (highpass).

**Design routines:**

``ma.calc_ma()``
    """
    sig_tx = pyqtSignal(object)
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, objectName='ma_inst'):
        QWidget.__init__(self)

        self.setObjectName(objectName)
        self.delays = 12 # number of delays per stage
        self.stages = 1 # number of stages

        self.ft = 'FIR'

        self.rt_dicts = ()
        # Common data for all filter response types:
        # This data is merged with the entries for individual response types
        # (common data comes first):

        self.rt_dict = {
            'COM':{'man':{'fo': ('d', 'N'),
                          'msg':('a',
                   "Enter desired order (= delays) <b><i>M</i></b> per stage and"
                    " the number of <b>stages</b>. Target frequencies and amplitudes"
                    " are only used for comparison, not for the design itself.")
                        },
                    'min':{'fo': ('d', 'N'),
                          'msg':('a',
                   "Enter desired attenuation <b><i>A<sub>SB</sub></i></b> at "
                   "the corner of the stop band <b><i>F<sub>SB</sub></i></b>. "
                   "Choose the number of <b>stages</b>, the minimum order <b><i>M</i></b> "
                   "per stage will be determined. Passband specs are not regarded.")
                        }
                    },
            'LP': {'man':{'tspecs': ('u', {'frq':('u','F_PB','F_SB'),
                                           'amp':('u','A_PB','A_SB')})
                          },
                   'min':{'tspecs': ('a', {'frq':('a','F_PB','F_SB'),
                                           'amp':('a','A_PB','A_SB')})
                   }
                },
            'HP': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB'),
                                           'amp':('u','A_SB','A_PB')})
                         },
                   'min':{'tspecs': ('a', {'frq':('a','F_SB','F_PB'),
                                           'amp':('a','A_SB','A_PB')})
                         },
                },
            'BS': {'man':{'tspecs': ('u', {'frq':('u','F_PB','F_SB','F_SB2', 'F_PB2'),
                                           'amp':('u','A_PB','A_SB','A_PB2')}),
                    'msg': ('a', "\nThis is not a proper band stop, it only lets pass"
                            " frequency components around DC and <i>f<sub>S</sub></i>/2."
                            " The order needs to be odd."),
                        }},
            'BP': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2',),
                                           'amp':('u','A_SB','A_PB','A_SB2')}),
                    'msg': ('a', "\nThis is not a proper band pass, it only lets pass"
                            " frequency components around <i>f<sub>S</sub></i>/4."
                            " The order needs to be odd."),

                        }},
                }


        self.info_doc = []
#        self.info_doc.append('remez()\n=======')
#        self.info_doc.append(sig.remez.__doc__)
#        self.info_doc.append('remezord()\n==========')
#        self.info_doc.append(remezord.__doc__)

    #--------------------------------------------------------------------------
    def construct_UI(self):
        """
        Create additional subwidget(s) needed for filter design:
        These subwidgets are instantiated dynamically when needed in
        select_filter.py using the handle to the filter instance, fb.fil_inst.
        """

        self.lbl_delays = QLabel("<b><i>M =</ i></ b>", self)
        self.lbl_delays.setObjectName('wdg_lbl_ma_0')
        self.led_delays = QLineEdit(self)
        try:
            self.led_delays.setText(str(fb.fil[0]['N']))
        except KeyError:
            self.led_delays.setText(str(self.delays))
        self.led_delays.setObjectName('wdg_led_ma_0')
        self.led_delays.setToolTip("Set number of delays per stage")

        self.lbl_stages = QLabel("<b>Stages =</ b>", self)
        self.lbl_stages.setObjectName('wdg_lbl_ma_1')
        self.led_stages = QLineEdit(self)
        self.led_stages.setText(str(self.stages))

        self.led_stages.setObjectName('wdg_led_ma_1')
        self.led_stages.setToolTip("Set number of stages ")

        self.chk_norm = QCheckBox("Normalize", self)
        self.chk_norm.setChecked(True)
        self.chk_norm.setObjectName('wdg_chk_ma_2')
        self.chk_norm.setToolTip("Normalize to| H_max = 1|")

        self.layHWin = QHBoxLayout()
        self.layHWin.setObjectName('wdg_layGWin')
        self.layHWin.addWidget(self.lbl_delays)
        self.layHWin.addWidget(self.led_delays)
        self.layHWin.addStretch(1)
        self.layHWin.addWidget(self.lbl_stages)
        self.layHWin.addWidget(self.led_stages)
        self.layHWin.addStretch(1)
        self.layHWin.addWidget(self.chk_norm)
        self.layHWin.setContentsMargins(0,0,0,0)
        # Widget containing all subwidgets (cmbBoxes, Labels, lineEdits)
        self.wdg_fil = QWidget(self)
        self.wdg_fil.setObjectName('wdg_fil')
        self.wdg_fil.setLayout(self.layHWin)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.led_delays.editingFinished.connect(self._update_UI)
        self.led_stages.editingFinished.connect(self._update_UI)
        # fires when edited line looses focus or when RETURN is pressed
        self.chk_norm.clicked.connect(self._update_UI)
        #----------------------------------------------------------------------

        self._load_dict() # get initial / last setting from dictionary
        self._update_UI()


    def _load_dict(self):
        """
        Reload parameter(s) from filter dictionary (if they exist) and set
        corresponding UI elements. load_dict() is called upon initialization
        and when the filter is loaded from disk.
        """
        if 'wdg_fil' in fb.fil[0] and 'ma' in fb.fil[0]['wdg_fil']:
            wdg_fil_par = fb.fil[0]['wdg_fil']['ma']
            if 'delays' in wdg_fil_par:
                self.delays = wdg_fil_par['delays']
                self.led_delays.setText(str(self.delays))
            if 'stages' in wdg_fil_par:
                self.stages = wdg_fil_par['stages']
                self.led_stages.setText(str(self.stages))
            if 'normalize' in wdg_fil_par:
                self.chk_norm.setChecked(wdg_fil_par['normalize'])


    def _update_UI(self):
        """
        Update UI when line edit field is changed (here, only the text is read
        and converted to integer) and resize the textfields according to content.
        """
        self.delays = safe_eval(self.led_delays.text(), self.delays, return_type='int', sign='pos')
        self.led_delays.setText(str(self.delays))
        self.stages = safe_eval(self.led_stages.text(), self.stages, return_type='int', sign='pos')
        self.led_stages.setText(str(self.stages))

        self._store_entries()

    def _store_entries(self):

        """
        Store parameter settings in filter dictionary. Called from _update_UI()
        and _save()
        """
        if not 'wdg_fil' in fb.fil[0]:
            fb.fil[0].update({'wdg_fil':{}})
        fb.fil[0]['wdg_fil'].update({'ma':
                                        {'delays':self.delays,
                                         'stages':self.stages,
                                         'normalize':self.chk_norm.isChecked()}
                                    })
        # sig_tx -> select_filter -> filter_specs
        self.emit({'filt_changed': 'ma'})


    def _get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        # N is total order, L is number of taps per stage
        self.F_SB  = fil_dict['F_SB']
        self.A_SB  = fil_dict['A_SB']


    def _save(self, fil_dict):
        """
        Save MA-filters both in 'zpk' and 'ba' format; no conversion has to be
        performed except maybe deleting an 'sos' entry from an earlier
        filter design.
        """
        if 'zpk' in self.FRMT:
            fil_save(fil_dict, self.zpk, 'zpk', __name__, convert = False)

        if 'ba' in self.FRMT:
            fil_save(fil_dict, self.b, 'ba', __name__, convert = False)

        fil_convert(fil_dict, self.FRMT)

        # always update filter dict and LineEdit, in case the design algorithm
        # has changed the number of delays:
        fil_dict['N'] = self.delays * self.stages # updated filter order
        self.led_delays.setText(str(self.delays)) # updated number of delays

        self._store_entries()


    def calc_ma(self, fil_dict, rt='LP'):
        """
        Calculate coefficients and P/Z for moving average filter based on
        filter length L = N + 1 and number of cascaded stages and save the
        result in the filter dictionary.
        """
        b = 1.
        k = 1.
        L = self.delays + 1

        if rt == 'LP':
            b0 = np.ones(L) #  h[n] = {1; 1; 1; ...}
            i = np.arange(1, L)

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
            i = np.delete(i, [0, L // 2]) + L / 4

            norm = np.sum(abs(b0))

        elif rt == 'BS':
            # N is even, L is odd
            b0 = np.ones(L)
            b0[1::2] = 0

            L = L + 1
            i = np.arange(L) # create N + 2 zeros around the unit circle and ...
            i = np.delete(i, [0, L // 2]) # ... remove first and middle element

            norm = np.sum(b0)

        if self.delays > 1000:
            if not popup_warning(None, self.delays*self.stages, "Moving Average"):
                return -1


        z0 = np.exp(-2j*np.pi*i/L)
        # calculate filter for multiple cascaded stages
        for i in range(self.stages):
            b = np.convolve(b0, b)
        z = np.repeat(z0, self.stages)

        # normalize filter to |H_max| = 1 if checked:
        if self.chk_norm.isChecked():
            b = b / (norm ** self.stages)
            k = 1./norm ** self.stages
        p = np.zeros(len(z))

        gain = zeros_with_val(len(z), k)

        # store in class attributes for the _save method
        self.zpk = [z,p,gain]
        self.b = b
        self._save(fil_dict)


    def LPman(self, fil_dict):
        self._get_params(fil_dict)
        self.calc_ma(fil_dict, rt = 'LP')

    def LPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.delays = int(np.ceil(1 / (self.A_SB **(1/self.stages) *
                                                     np.sin(self.F_SB * np.pi))))
        self.calc_ma(fil_dict, rt = 'LP')

    def HPman(self, fil_dict):
        self._get_params(fil_dict)
        self.calc_ma(fil_dict, rt = 'HP')

    def HPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.delays = int(np.ceil(1 / (self.A_SB **(1/self.stages) *
                                              np.sin((0.5 - self.F_SB) * np.pi))))
        self.calc_ma(fil_dict, rt = 'HP')

    def BSman(self, fil_dict):
        self._get_params(fil_dict)
        self.delays = ceil_odd(self.delays)  # enforce odd order
        self.calc_ma(fil_dict, rt = 'BS')

    def BPman(self, fil_dict):
        self._get_params(fil_dict)
        self.delays = ceil_odd(self.delays)  # enforce odd order
        self.calc_ma(fil_dict, rt = 'BP')

#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from pyfda.libs.compat import QApplication, QFrame

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

# test using "python -m pyfda.filter_widgets.ma"
