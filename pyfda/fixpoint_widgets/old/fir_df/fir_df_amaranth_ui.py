# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for specifying the parameters of a direct-form DF1 FIR filter
"""
import sys

import numpy as np
import pyfda.filterbroker as fb
from pyfda.libs.pyfda_lib import set_dict_defaults, pprint_log
from pyfda.libs.pyfda_qt_lib import qget_cmb_box

from pyfda.libs.compat import QWidget, QVBoxLayout, pyqtSignal

from pyfda.fixpoint_widgets.fx_ui_wq import FX_UI_WQ

from .fir_df_nmigen import FIR_DF_amaranth
from pyfda.fixpoint_widgets.fixpoint_helpers import UI_W, UI_Q

#####################
from amaranth.back import verilog
from amaranth.sim import Simulator, Tick  # , Delay, Settle
#####################

import logging
logger = logging.getLogger(__name__)

#  Dict containing {widget class name : display name}
classes = {'FIR_DF_amaranth_UI': 'FIR_DF (Amaranth)'}


# =============================================================================
class FIR_DF_amaranth_UI(QWidget):
    """
    Widget for entering word formats & quantization, also instantiates fixpoint
    filter class :class:`FilterFIR`.
    """
    sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outcgoing
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self):
        super().__init__()

        self.title = ("<b>Direct-Form (DF) FIR Filter</b>")
        self.description = "Standard FIR topology, suitable for most use cases."
        self.img_name = "fir_df.png"

        self._construct_UI()
        # Construct an instance of the fixpoint filter using the settings from
        # the 'fxq' quantizer dict
# ------------------------------------------------------------------------------

    def _construct_UI(self):
        """
        Intitialize the UI with widgets for coefficient format and input and
        output quantization
        """
        if 'QA' not in fb.fil[0]['fxq']:
            fb.fil[0]['fxq']['QA'] = {}
        set_dict_defaults(fb.fil[0]['fxq']['QA'],
                          {'WI': 0, 'WF': 30, 'ovfl': 'wrap', 'quant': 'floor',
                           'w_a_m': 'a', 'N_over': 0, 'wdg_name': 'unknown'})

        self.wdg_w_coeffs = UI_W(self, fb.fil[0]['fxq']['QCB'], wdg_name='w_coeff',
                                 label='Coeff. Format <i>B<sub>I.F&nbsp;</sub></i>:',
                                 tip_WI='Number of integer bits - edit in "b,a" tab',
                                 tip_WF='Number of fractional bits - edit in "b,a" tab',
                                 WI=fb.fil[0]['fxq']['QCB']['WI'],
                                 WF=fb.fil[0]['fxq']['QCB']['WF'])


#        self.wdg_q_coeffs = UI_Q(self, fb.fil[0]['fxq']['QCB'],
#                                        cur_ov=fb.fil[0]['fxq']['QCB']['ovfl'],
#                                        cur_q=fb.fil[0]['fxq']['QCB']['quant'])
#        self.wdg_q_coeffs.sig_tx.connect(self.update_q_coeff)

        self.wdg_w_accu = UI_W(self, fb.fil[0]['fxq']['QA'],
                               label='', wdg_name='w_accu',
                               fractional=True, combo_visible=True)

        self.wdg_q_accu = UI_Q(self, fb.fil[0]['fxq']['QA'], wdg_name='q_accu',
                               label='Accu Format <i>Q<sub>A&nbsp;</sub></i>:')

        # initial setting for accumulator
        cmbW = qget_cmb_box(self.wdg_w_accu.cmbW, data=False)
        self.wdg_w_accu.ledWF.setEnabled(cmbW == 'm')
        self.wdg_w_accu.ledWI.setEnabled(cmbW == 'm')

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs & EVENTFILTERS
        # ----------------------------------------------------------------------
        self.wdg_w_coeffs.sig_tx.connect(self.update_q_coeff)
        self.wdg_w_accu.sig_tx.connect(self.process_sig_rx)
        self.wdg_q_accu.sig_tx.connect(self.process_sig_rx)
# ------------------------------------------------------------------------------

        layVWdg = QVBoxLayout()
        layVWdg.setContentsMargins(0, 0, 0, 0)

        layVWdg.addWidget(self.wdg_w_coeffs)
#        layVWdg.addWidget(self.wdg_q_coeffs)
        layVWdg.addWidget(self.wdg_q_accu)
        layVWdg.addWidget(self.wdg_w_accu)

        layVWdg.addStretch()

        self.setLayout(layVWdg)

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        logger.warning("sig_rx:\n{0}".format(pprint_log(dict_sig)))
        # check whether anything needs to be done locally
        # could also check here for 'quant', 'ovfl', 'WI', 'WF' (not needed at the moment)
        # if not, just emit the dict.
        if 'ui' in dict_sig:
            if dict_sig['wdg_name'] == 'w_coeff':  # coefficient format updated
                """
                Update coefficient quantization settings and coefficients.

                The new values are written to the fixpoint coefficient dict as
                `fb.fil[0]['fxq']['QCB']` and  `fb.fil[0]['fxq']['b']`.
                """

                fb.fil[0]['fxq'].update(self.ui2dict())

            elif dict_sig['wdg_name'] == 'w_accu':  # accu format updated
                cmbW = qget_cmb_box(self.wdg_w_accu.cmbW, data=False)
                self.wdg_w_accu.ledWF.setEnabled(cmbW == 'm')
                self.wdg_w_accu.ledWI.setEnabled(cmbW == 'm')
                if cmbW in {'f', 'a'}\
                        or ('ui' in dict_sig and dict_sig['ui'] in {'WF', 'WI'}):
                    pass

                elif cmbW == 'm':  # switched to manual, don't do anything
                    return

            # Accu quantization or overflow settings have been changed
            elif dict_sig['wdg_name'] == 'q_accu':
                pass

            else:
                logger.error(f"Unknown widget name '{dict_sig['wdg_name']}' "
                             f"in '{__name__}' !")
                return

            # - update fixpoint accu and coefficient quantization dict
            # - emit {'fx_sim': 'specs_changed'}
            fb.fil[0]['fxq'].update(self.ui2dict())
            self.emit({'fx_sim': 'specs_changed'})

        else:
            logger.error(f"Unknown key '{dict_sig['wdg_name']}' (should be 'ui')"
                         f"in '{__name__}' !")

# ------------------------------------------------------------------------------
    def update_q_coeff(self, dict_sig):
        """
        Update coefficient quantization settings and coefficients.

        The new values are written to the fixpoint coefficient dict as
        `fb.fil[0]['fxq']['QCB']` and
        `fb.fil[0]['fxq']['b']`.
        """
        logger.debug("update q_coeff - dict_sig:\n{0}".format(pprint_log(dict_sig)))
        # dict_sig.update({'ui':'C'+dict_sig['ui']})
        fb.fil[0]['fxq'].update(self.ui2dict())
        logger.debug("b = {0}".format(pprint_log(fb.fil[0]['fxq']['b'])))

        self.process_sig_rx(dict_sig)

# ------------------------------------------------------------------------------
    def update_accu_settings(self):
        """
        Calculate number of extra integer bits needed in the accumulator (bit
        growth) depending on the coefficient area (sum of absolute coefficient
        values) for `cmbW == 'auto'` or depending on the number of coefficients
        for `cmbW == 'full'`. The latter works for arbitrary coefficients but
        requires more bits.

        The new values are written to the fixpoint coefficient dict
        `fb.fil[0]['fxq']['QA']`.
        """
        try:
            if qget_cmb_box(self.wdg_w_accu.cmbW, data=False) == 'f':
                A_coeff = int(np.ceil(np.log2(len(fb.fil[0]['fxq']['b']))))
            elif qget_cmb_box(self.wdg_w_accu.cmbW, data=False) == 'a':
                A_coeff = int(np.ceil(np.log2(np.sum(np.abs(fb.fil[0]['ba'][0])))))
        except Exception as e:
            logger.error(e)
            return

        if qget_cmb_box(self.wdg_w_accu.cmbW, data=False) == 'f' or\
                qget_cmb_box(self.wdg_w_accu.cmbW, data=False) == 'a':
            fb.fil[0]['fxq']['QA']['WF'] = fb.fil[0]['fxq']['QI']['WF']\
                + fb.fil[0]['fxq']['QCB']['WF']
            fb.fil[0]['fxq']['QA']['WI'] = fb.fil[0]['fxq']['QI']['WI']\
                + fb.fil[0]['fxq']['QCB']['WI'] + A_coeff

        # calculate total accumulator word length
        fb.fil[0]['fxq']['QA']['W'] = fb.fil[0]['fxq']['QA']['WI']\
            + fb.fil[0]['fxq']['QA']['WF'] + 1

        # update quantization settings
        fb.fil[0]['fxq']['QA'].update(self.wdg_q_accu.q_dict)

        # update UI
        self.wdg_w_accu.dict2ui(fb.fil[0]['fxq']['QA'])

# ------------------------------------------------------------------------------
    def dict2ui(self):
        """
        Update all parts of the UI that need to be updated when specs have been
        changed outside this class, e.g. coefficients and coefficient wordlength.
        This also provides the initial setting for the widgets when the filter has
        been changed.

        This is called from one level above by
        :class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs`.
        """
        fxqc_dict = fb.fil[0]['fxq']
        if 'QA' not in fxqc_dict:
            fxqc_dict.update({'QA': {}})  # no accumulator settings in dict yet
            logger.warning("QA key missing")

        if 'QCB' not in fxqc_dict:
            fxqc_dict.update({'QCB': {}})  # no coefficient settings in dict yet
            logger.warning("QCB key missing")

        self.wdg_w_coeffs.dict2ui(fxqc_dict['QCB'])  # update coefficient wordlength
        self.update_accu_settings()                  # update accumulator settings

# ------------------------------------------------------------------------------
    def ui2dict(self):
        """
        Read out the quantization subwidgets and store their settings in the central
        fixpoint dictionary `fb.fil[0]['fxq']` using the keys described below.

        Coefficients are quantized with these settings in the subdictionary under
        the key 'b'.

        Additionally, these subdictionaries are returned  to the caller
        (``input_fixpoint_specs``) where they are used to update ``fb.fil[0]['fxq']``

        Parameters
        ----------

        None

        Returns
        -------
        fxqc_dict : dict

           containing the following keys and values:

        - 'QCB': dictionary with b coefficients quantization settings

        - 'QA': dictionary with accumulator quantization settings

        - 'b' : list of quantized b coefficients in format WI.WF

        """
        fxqc_dict = fb.fil[0]['fxq']
        if 'QA' not in fxqc_dict:
            # no accumulator settings in dict yet:
            fxqc_dict.update({'QA': self.wdg_w_accu.q_dict})
            logger.warning("Empty dict 'fb.fil{0]['fxq']['QA']'!")
        else:
            fxqc_dict['QA'].update(self.wdg_w_accu.q_dict)

        if 'QCB' not in fxqc_dict:
            # no coefficient settings in dict yet
            fxqc_dict.update({'QCB': self.wdg_w_coeffs.q_dict})
            logger.warning("Empty dict 'fb.fil{0]['fxq']['QCB']'!")
        else:
            fxqc_dict['QCB'].update(self.wdg_w_coeffs.q_dict)

        fxqc_dict.update({'b': self.wdg_w_coeffs.quant_coeffs(
            self.wdg_w_coeffs.q_dict, fb.fil[0]['ba'][0], to_int=True)})
        return fxqc_dict

# ------------------------------------------------------------------------------
    def init_filter(self):
        """
        Construct an instance of the fixpoint filter object using the settings from
        the 'fxq' quantizer dict
        """
        p = fb.fil[0]['fxq']  # parameter dictionary with coefficients etc.
        if not all(np.isfinite(p['b'])):
            logger.error("Coefficients contain non-finite values!")
            return
        if any(np.iscomplex(p['b'])):
            logger.error("Coefficients contain complex values!")
            return

        self.fx_filt = FIR_DF_amaranth(p)

# ------------------------------------------------------------------------------
    def to_hdl(self, **kwargs):
        """
        Convert the nmigen description to Verilog
        """
        return verilog.convert(self.fx_filt,
                               ports=[self.fx_filt.i, self.fx_filt.o],
                               **kwargs)

    # ------------------------------------------------------------------------------
    def fxfilter(self, stimulus):
        """
        Calculate the fixpoint filter response in float format for a frame of
        stimulus data (float).

        Parameters
        ----------
        stimulus : ndarray of float
            One frame of stimuli data (float) scaled as WI.WF

        Returns
        -------
        output : ndarray of float
            One frame of response data (float) scaled as WI.WF
        """
        def process():
            # convert stimulus to int by multiplying with 2 ^ WF
            input = np.round(stimulus * (1 << self.fx_filt.p['QI']['WF'])).astype(int)
            self.output = []
            for i in input:
                yield self.fx_filt.i.eq(int(i))
                yield Tick()
                self.output.append((yield self.fx_filt.o))

        sim = Simulator(self.fx_filt)

        sim.add_clock(1/48000)
        sim.add_process(process)
        sim.run()

        # convert output to ndarray of float by dividing the integer response by 2 ^ WF
        return np.array(self.output, dtype='f') / (1 << self.fx_filt.p['QO']['WF'])


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """ Run widget standalone with
        `python -m pyfda.fixpoint_widgets.fir_df.fir_df_amaranth_ui`
    """
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = FIR_DF_amaranth_UI()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
