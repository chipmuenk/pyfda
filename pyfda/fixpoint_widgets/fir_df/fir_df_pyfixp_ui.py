# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for specifying the parameters of a direct-form FIR filter
"""
import sys

import numpy as np
import pyfda.filterbroker as fb
from pyfda.libs.pyfda_lib import set_dict_defaults, pprint_log, first_item
from pyfda.libs.pyfda_qt_lib import qget_cmb_box

from pyfda.libs.compat import QWidget, QVBoxLayout, QFrame, pyqtSignal

from pyfda.fixpoint_widgets.fx_ui_wq import FX_UI_WQ
from pyfda.pyfda_rc import params

from .fir_df_pyfixp import FIR_DF_pyfixp

import logging
logger = logging.getLogger(__name__)

#  Dict containing {widget class name : display name}
classes = {'FIR_DF_pyfixp_UI': 'FIR_DF (pyfixp)'}  # widget class name : display name


# =============================================================================
class FIR_DF_pyfixp_UI(QWidget):
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
        # the 'fxqc' quantizer dict

    # --------------------------------------------------------------------------
    def _construct_UI(self):
        """
        Intitialize the UI with widgets for coefficient format and input and
        output quantization
        """
        # widget for quantization of coefficients 'b'
        if 'QCB' not in fb.fil[0]['fxqc']:
            fb.fil[0]['fxqc'].update({'QCB': {}})  # no coefficient settings in dict yet
            logger.warning("QCB key missing")
        self.wdg_wq_coeffs = FX_UI_WQ(
            fb.fil[0]['fxqc']['QCB'], wdg_name='wq_coeffs',
            label='<b>Coeff. Quantization <i>b<sub>I.F&nbsp;</sub></i>:</b>')
        layV_wq_coeffs = QVBoxLayout()
        layV_wq_coeffs.addWidget(self.wdg_wq_coeffs)
        self.frm_wq_coeffs = QFrame(self)
        self.frm_wq_coeffs.setLayout(layV_wq_coeffs)
        self.frm_wq_coeffs.setContentsMargins(*params['wdg_margins'])

        # widget for accumulator quantization
        if 'QA' not in fb.fil[0]['fxqc']:
            fb.fil[0]['fxqc']['QA'] = {}
        set_dict_defaults(fb.fil[0]['fxqc']['QA'],
                          {'WI': 0, 'WF': 31, 'W': 32, 'ovfl': 'wrap', 'quant': 'floor'})
        self.wdg_wq_accu = FX_UI_WQ(
            fb.fil[0]['fxqc']['QA'], wdg_name='wq_accu', cmb_w_vis='on',
            label='<b>Accu Format <i>Q<sub>A&nbsp;</sub></i>:</b>')
        layV_wq_accu = QVBoxLayout()
        layV_wq_accu.addWidget(self.wdg_wq_accu)
        self.frm_wq_accu = QFrame(self)
        self.frm_wq_accu.setLayout(layV_wq_accu)
        self.frm_wq_accu.setContentsMargins(*params['wdg_margins'])

        # initial setting for accumulator
        cmbW = qget_cmb_box(self.wdg_wq_accu.cmbW)
        self.wdg_wq_accu.ledWF.setEnabled(cmbW == 'man')
        self.wdg_wq_accu.ledWI.setEnabled(cmbW == 'man')

        # ----------------------------------------------------------------------
        layVWdg = QVBoxLayout()
        # margins are created in input_fixpoint_specs
        layVWdg.setContentsMargins(0, 0, 0, 0)
        layVWdg.addWidget(self.frm_wq_coeffs)
        layVWdg.addWidget(self.frm_wq_accu)
        self.setLayout(layVWdg)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs & EVENTFILTERS
        # ----------------------------------------------------------------------
        self.wdg_wq_coeffs.sig_tx.connect(self.process_sig_rx)
        self.wdg_wq_accu.sig_tx.connect(self.process_sig_rx)

    # --------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        logger.warning("sig_rx:\n{0}".format(pprint_log(dict_sig)))
        # check whether a signal was generated locally (key = 'ui'). If so:
        # - update the referenced quantization dictionary
        # - emit `{'fx_sim': 'specs_changed'}`
        # Update the ui when the quantization dictionary has been updated outside
        # (signal `{'fx_sim': 'specs_changed'}` received)
        if 'ui' in dict_sig:
            if dict_sig['wdg_name'] == 'wq_coeffs':  # coefficient format updated
                """
                Update coefficient quantization settings and coefficients.

                The new values are written to the fixpoint coefficient dict as
                `fb.fil[0]['fxqc']['QCB']` and  `fb.fil[0]['fxqc']['b']`.
                """
                pass

            elif dict_sig['wdg_name'] == 'wq_accu':  # accu format updated
                cmbW = qget_cmb_box(self.wdg_wq_accu.cmbW)
                self.wdg_wq_accu.ledWF.setEnabled(cmbW == 'man')
                self.wdg_wq_accu.ledWI.setEnabled(cmbW == 'man')
                if cmbW in {'full', 'auto'}\
                        or ('ui' in dict_sig and dict_sig['ui'] in {'WF', 'WI'}):
                    self.update_accu_settings()

                elif cmbW == 'man':  # switched to manual, don't do anything
                    pass

            else:
                logger.error(f"Unknown widget name '{dict_sig['wdg_name']}' "
                             f"in '{__name__}' !")
                return

            fb.fil[0]['fxqc'].update(self.ui2dict())
            self.emit({'fx_sim': 'specs_changed'})

        elif 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
            self.dict2ui()

    # --------------------------------------------------------------------------
    def update_q_coeff(self, dict_sig):
        """
        Update coefficient quantization settings and coefficients.

        The new values are written to the fixpoint coefficient dict as
        `fb.fil[0]['fxqc']['QCB']` and
        `fb.fil[0]['fxqc']['b']`.
        """
        logger.debug("update q_coeff - dict_sig:\n{0}".format(pprint_log(dict_sig)))
        # dict_sig.update({'ui':'C'+dict_sig['ui']})
        fb.fil[0]['fxqc'].update(self.ui2dict())
        logger.debug("b = {0}".format(pprint_log(fb.fil[0]['fxqc']['b'])))

        self.process_sig_rx(dict_sig)

    # --------------------------------------------------------------------------
    def update_accu_settings(self):
        """
        Calculate number of extra integer bits needed in the accumulator (bit
        growth) depending on the coefficient area (sum of absolute coefficient
        values) for `cmbW == 'auto'` or depending on the number of coefficients
        for `cmbW == 'full'`. The latter works for arbitrary coefficients but
        requires more bits.

        The new values are written to the fixpoint coefficient dict
        `fb.fil[0]['fxqc']['QA']`.
        """
        try:
            if qget_cmb_box(self.wdg_wq_accu.cmbW) == "full":
                A_coeff = int(np.ceil(np.log2(len(fb.fil[0]['fxqc']['b']))))
            elif qget_cmb_box(self.wdg_wq_accu.cmbW) == "auto":
                A_coeff = int(np.ceil(np.log2(np.sum(np.abs(fb.fil[0]['ba'][0])))))
            else:
                A_coeff = 0
        except Exception as e:
            logger.error(e)
            return

        if qget_cmb_box(self.wdg_wq_accu.cmbW) in {"full", "auto"}:
            fb.fil[0]['fxqc']['QA']['WF'] = fb.fil[0]['fxqc']['QI']['WF']\
                + fb.fil[0]['fxqc']['QCB']['WF']
            fb.fil[0]['fxqc']['QA']['WI'] = fb.fil[0]['fxqc']['QI']['WI']\
                + fb.fil[0]['fxqc']['QCB']['WI'] + A_coeff

        # calculate total accumulator word length and 'Q' format
        fb.fil[0]['fxqc']['QA']['W'] = fb.fil[0]['fxqc']['QA']['WI']\
            + fb.fil[0]['fxqc']['QA']['WF'] + 1
        fb.fil[0]['fxqc']['QA']['Q'] = str(fb.fil[0]['fxqc']['QA']['WI'])\
            + '.' + str(fb.fil[0]['fxqc']['QA']['WF'])

        # update quantization settings
        fb.fil[0]['fxqc']['QA'].update(self.wdg_wq_accu.q_dict)

        # update UI
        self.wdg_wq_accu.dict2ui()

    # --------------------------------------------------------------------------
    def dict2ui(self):
        """
        Update all parts of the UI that need to be updated when specs have been
        changed outside this class, e.g. coefficients and coefficient wordlength.
        This also provides the initial setting for the widgets when the filter has
        been changed.

        This is called from one level above by
        :class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs`.
        """
        fxqc_dict = fb.fil[0]['fxqc']
        if 'QA' not in fxqc_dict:
            fxqc_dict.update({'QA': {}})  # no accumulator settings in dict yet
            logger.warning("QA key missing")

        if 'QCB' not in fxqc_dict:
            fxqc_dict.update({'QCB': {}})  # no coefficient settings in dict yet
            logger.warning("QCB key missing")

        self.wdg_wq_coeffs.dict2ui()  # update coefficient wordlength
        self.update_accu_settings()                  # update accumulator settings

    # --------------------------------------------------------------------------
    def ui2dict(self):
        """
        Read out the quantization subwidgets and store their settings in the central
        fixpoint dictionary `fb.fil[0]['fxqc']` using the keys described below.

        Coefficients are quantized with these settings in the subdictionary under
        the key 'b'.

        Additionally, these subdictionaries are returned  to the caller
        (``input_fixpoint_specs``) where they are used to update ``fb.fil[0]['fxqc']``

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
        fxqc_dict = fb.fil[0]['fxqc']
        # fxqc_dict['QA'].update(self.wdg_wq_accu.q_dict)
        # fxqc_dict['QCB'].update(self.wdg_wq_coeffs.q_dict)

        fxqc_dict.update({'b': self.wdg_wq_coeffs.quant_coeffs(fb.fil[0]['ba'][0])})

        return fxqc_dict

    # --------------------------------------------------------------------------
    def init_filter(self):
        """
        Construct an instance of the fixpoint filter object using the settings from
        the 'fxqc' quantizer dict
        """
        p = fb.fil[0]['fxqc']  # parameter dictionary with coefficients etc.
        self.fx_filt = FIR_DF_pyfixp(p)

    # --------------------------------------------------------------------------
    def fxfilter(self, stimulus):

        return self.fx_filt.fxfilter(x=stimulus)[0]


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """ Run widget standalone with
    `python -m pyfda.fixpoint_widgets.fir_df.fir_df_pyfixp_ui`
    """
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = FIR_DF_pyfixp_UI()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
