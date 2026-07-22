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
import logging

import numpy as np

import pyfda.filterbroker as fb
from pyfda.filterbroker import fb_get
from pyfda.filterbroker import set_fx
from pyfda.libs.pyfda_lib import set_dict_defaults, pprint_log, first_item
from pyfda.libs.pyfda_qt_lib import qget_cmb_box, emit
from pyfda.libs.compat import QWidget, QVBoxLayout, pyqtSignal

from pyfda.fixpoint_widgets.fx_ui_wq import FX_UI_WQ

from .fir_df_pyfixp import FIR_DF_pyfixp


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

    def __init__(self):
        super().__init__()

        self.title = "<b>Direct-Form (DF) FIR Filter</b>"
        self.description = "Standard FIR topology without pipeling."
        self.img_name = "fir_df.png"

        self.cmb_wq_accu_items = [
            "<span>Calculate word format manually / automatically</span>",
            ("m", "M", "<span><b>Manual</b> entry of accumulator format.</span>"),
            ("a", "A",
            "<span><b>Automatic</b> calculation for given input word format "
            "and coefficients (<i>coefficient area</i>).</span>"),
            ("f", "F",
            "<span><b>Full</b> accumulator width for given input word format "
            "and arbitrary coefficients.</span>")
            ]

        self._construct_ui()
        # Construct an instance of the fixpoint filter using the settings from
        # the 'fxq' quantizer dict
        self.fx_filt = FIR_DF_pyfixp(fb_get('fxq'))
        self.update_ovfl_cnt_all()  # initialize all overflow counters / display

    # -------------------------------------------------------------------------
    def emit(self, dict_sig):
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    # --------------------------------------------------------------------------
    def _construct_ui(self) -> None:
        """
        Intitialize the UI with widgets for coefficient format and input and
        output quantization
        """
        # widget for quantization of coefficients 'b'
        # Attention: fil[0]['fxq']['QCB'] is self.wdg_wq_coeffs.q_dict
        if 'QCB' not in fb_get('fxq'):
            fb.fil[0]['fxq'].update({'QCB': {}})  # no coefficient settings in dict yet
            logger.warning("QCB key missing")
        self.wdg_wq_coeffs = FX_UI_WQ(
            fb_get('fxq', 'QCB'), objectName='fx_ui_wq_fir_df_coeffs_b',
            label='<b>Coeff. Quantization <i>b<sub>I.F&nbsp;</sub></i>:</b>',
            MSB_LSB_vis='max')
        lay_v_wq_coeffs = QVBoxLayout()
        lay_v_wq_coeffs.addWidget(self.wdg_wq_coeffs)

        # widget for accumulator quantization
        # Attention: fil[0]['fxq']['QACC'] is self.wdg_wq_accu.q_dict
        if 'QACC' not in fb_get('fxq'):
            fb.fil[0]['fxq']['QACC'] = {}
        set_dict_defaults(fb.fil[0]['fxq']['QACC'],
            {'WI': 0, 'WF': 31, 'ovfl': 'wrap', 'quant': 'floor', 'w_a_m': 'a',
             'N_over': 0})
        self.wdg_wq_accu = FX_UI_WQ(
            fb.fil[0]['fxq']['QACC'], objectName='fx_ui_wq_fir_df_accu',
            cmb_w_vis='on', cmb_w_items=self.cmb_wq_accu_items,
            label='<b>Accu Format <i>Q<sub>ACC&nbsp;</sub></i>:</b>')
        lay_v_wq_accu = QVBoxLayout()
        lay_v_wq_accu.addWidget(self.wdg_wq_accu)

        # ----------------------------------------------------------------------
        lay_v_wdg = QVBoxLayout()
        # margins are created in input_fixpoint_specs widget
        lay_v_wdg.setContentsMargins(0, 0, 0, 0)
        lay_v_wdg.addLayout(lay_v_wq_coeffs)
        lay_v_wdg.addLayout(lay_v_wq_accu)
        self.setLayout(lay_v_wdg)

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
        """
        - For locally generated signals (key = 'ui_local_changed'), emit
          `{'fx_sim': 'specs_changed'}` with local id.
          Update accu wordlengths for 'auto' or 'full' settings

        - For external changes, i.e. `{'fx_sim': 'specs_changed'}` or
          `{'data_changed': xxx}` update the UI via `self.dict2ui`.

        Ignore all other signals

        Note: If coefficient / accu quantization settings have been changed in the UI,
        the referenced dicts `fil[0]['fxq']['QCB']` and `...['QACC']` have already
        been updated by the corresponding subwidgets `FX_UI_WQ`
        """
        logger.debug("sig_rx:\n%s", pprint_log(dict_sig))
        if dict_sig['id'] == id(self):
            logger.warning('Stopped infinite loop: "%s"', first_item(dict_sig))
            return

        if 'ui_local_changed' in dict_sig:
            # signal generated locally by modifying coefficient / accu format
            if dict_sig['sender_name'] not in\
                    {'fx_ui_wq_fir_df_coeffs_b', 'fx_ui_wq_fir_df_accu'}:
                logger.error(
                    "Unknown widget name '%s' in '%s' !", dict_sig['sender_name'], __name__)
                return

            if dict_sig['sender_name'] == 'fx_ui_wq_fir_df_accu':  # accu format updated
                cmbW = qget_cmb_box(self.wdg_wq_accu.cmbW)
                if cmbW in {'f', 'a'}\
                        or dict_sig['ui_local_changed'] in {'WF', 'WI'}:
                    self.update_accu_settings()
                elif cmbW == 'm':  # switched to manual, don't do anything
                    # self.wdg_wq_accu.dict2ui()?
                    return

            # emit signal, replace id with id of *this* widget
            self.emit({'fx_sim': 'specs_changed', 'id': id(self)})

        # quantization dictionary has been updated outside the widget, update UI
        elif 'data_changed' in dict_sig or\
                'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
            self.dict2ui()

    # --------------------------------------------------------------------------
    def update_accu_settings(self):
        """
        Calculate required number of fractional bits for the accumulator from
        the sum of coefficient and input fractional bits.

        Calculate number of extra integer bits for the accumulator (guard bits)
        depending on the coefficient area (sum of absolute coefficient
        values) for `cmbW == 'auto'` or depending on the number of coefficients
        for `cmbW == 'full'`. The latter works for arbitrary coefficients but
        requires more bits.

        The new values are written to the fixpoint coefficient dict
        `fil[0]['fxq']['QACC']` and the UI is updated.
        """
        # try:
        if qget_cmb_box(self.wdg_wq_accu.cmbW) == 'f':
            A_coeff = int(np.ceil(np.log2(len(fb_get('ba', 0)))))
        elif qget_cmb_box(self.wdg_wq_accu.cmbW) == 'a':
            A_coeff = int(np.ceil(np.log2(np.sum(np.abs(fb_get('ba', 0))))))
        else:
            A_coeff = 0
        # except BaseException as e: # Exception as e:
        #     logger.error("An error occured:", exc_info=True)
        #     return

        # calculate required accumulator word format and update filter dict
        if qget_cmb_box(self.wdg_wq_accu.cmbW) in {'f', 'a'}:
            fb.fil[0]['fxq']['QACC']['WF'] = fb_get('fxq', 'QI', 'WF')\
                + fb_get('fxq', 'QCB', 'WF')
            fb.fil[0]['fxq']['QACC']['WI'] = fb_get('fxq', 'QI', 'WI')\
                + fb_get('fxq', 'QCB', 'WI') + A_coeff

        # update UI and Q.q_dict (quantization settings) from filter dict
        self.wdg_wq_accu.dict2ui(fb_get('fxq', 'QACC'))

    # --------------------------------------------------------------------------
    def dict2ui(self) -> None:
        """
        Update all parts of the UI that need to be updated when specs have been
        changed outside this class, e.g. coefficients and coefficient wordlength.
        This also provides the initial setting for the widgets when the filter has
        been changed.

        This is called from one level above by
        :class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs`.
        """
        self.wdg_wq_coeffs.dict2ui(fb_get('fxq', 'QCB'))  # update coefficient wordlength
        self.update_accu_settings()   # update accumulator q settings and UI

    # --------------------------------------------------------------------------
    def update_ovfl_cnt_all(self):
        """
        Update all overflow counters of the UI after simulation has finished
        (except for coefficient quantizers).

        This is usually called from one level above by
        :class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs`.
        """
        self.wdg_wq_coeffs.update_ovfl_cnt()
        self.wdg_wq_accu.update_ovfl_cnt()

    # --------------------------------------------------------------------------
    def fxfilter(self, stimulus):
        """
        Provide wrapper around fixpoint filter simulation method:
        * takes stimulus (iterable or float or None) as parameter
        * returns fixpoint response (ndarray of float)
        """
        return self.fx_filt.fxfilter(x=stimulus)[0]


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # Run widget standalone with `python -m pyfda.fixpoint_widgets.fir_df.fir_df_pyfixp_ui`
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.QSS_RC)
    set_fx(True)  # enable fixpoint mode

    mainw = FIR_DF_pyfixp_UI()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
