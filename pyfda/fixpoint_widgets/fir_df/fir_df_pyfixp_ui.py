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
        self.init_filter()
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
            label='<b>Coeff. Quantization <i>b<sub>I.F&nbsp;</sub></i>:</b>',
            MSB_LSB_vis='max')
        layV_wq_coeffs = QVBoxLayout()
        layV_wq_coeffs.addWidget(self.wdg_wq_coeffs)

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

        # initial setting for accumulator
        cmbW = qget_cmb_box(self.wdg_wq_accu.cmbW)
        self.wdg_wq_accu.ledWF.setEnabled(cmbW == 'man')
        self.wdg_wq_accu.ledWI.setEnabled(cmbW == 'man')

        # ----------------------------------------------------------------------
        layVWdg = QVBoxLayout()
        # margins are created in input_fixpoint_specs
        layVWdg.setContentsMargins(0, 0, 0, 0)
        layVWdg.addLayout(layV_wq_coeffs)
        layVWdg.addLayout(layV_wq_accu)
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

        # self.update()  # initial setting of overflow counters
    # --------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        logger.error("sig_rx:\n{0}".format(pprint_log(dict_sig)))

        # check whether a signal was generated locally (key = 'ui'). If so:
        # - update the referenced quantization dictionary

        if 'ui' in dict_sig:
            # Some settings in the local UI have been changed. Coefficient and accu
            # quantization settings have already been updated in the referenced dicts 
            # `fb.fil[0]['fxqc']['QCB']` and `fb.fil[0]['fxqc']['QA']` by the
            # corresponding subwidgets `FX_UI_WQ`
            #
            # - update accu wordlengths for 'auto' or 'full' settings
            # - emit `{'fx_sim': 'specs_changed'}`
            if dict_sig['wdg_name'] == 'wq_coeffs':  # coefficient format updated
                pass

            elif dict_sig['wdg_name'] == 'wq_accu':  # accu format updated
                cmbW = qget_cmb_box(self.wdg_wq_accu.cmbW)
                self.wdg_wq_accu.ledWF.setEnabled(cmbW == 'man')
                self.wdg_wq_accu.ledWI.setEnabled(cmbW == 'man')
                if cmbW in {'full', 'auto'}\
                        or ('ui' in dict_sig and dict_sig['ui'] in {'WF', 'WI'}):
                    self.update_accu_settings()

                elif cmbW == 'man':  # switched to manual, don't do anything
                    return

            else:
                logger.error(f"Unknown widget name '{dict_sig['wdg_name']}' "
                             f"in '{__name__}' !")
                return

            self.emit({'fx_sim': 'specs_changed'})

        # Update the ui when the quantization dictionary has been updated outside
        # the widget (signal `{'fx_sim': 'specs_changed'}` received)
        elif 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
            self.dict2ui()

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
        self.update_accu_settings()   # update accumulator settings and ui

    # --------------------------------------------------------------------------
    def update(self):
        """
        Update the overflow counters etc. of the UI after simulation has finished.

        This is usually called from one level above by
        :class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs`.
        """
        self.wdg_wq_coeffs.update()
        self.wdg_wq_accu.update()

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
