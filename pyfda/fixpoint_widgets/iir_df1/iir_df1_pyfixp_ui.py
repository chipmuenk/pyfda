# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for specifying the parameters of a direct-form DF1 IIR filter
"""
import sys

import pyfda.filterbroker as fb
from pyfda.libs.pyfda_lib import set_dict_defaults, pprint_log, first_item

from pyfda.libs.compat import QWidget, QVBoxLayout, pyqtSignal

from pyfda.fixpoint_widgets.fx_ui_wq import FX_UI_WQ

from .iir_df1_pyfixp import IIR_DF1_pyfixp

import logging
logger = logging.getLogger(__name__)

#  Dict containing {widget class name : display name}
classes = {'IIR_DF1_pyfixp_UI': 'IIR_DF1 (pyfixp)'}  # widget class name : display name


# =============================================================================
class IIR_DF1_pyfixp_UI(QWidget):
    """
    Widget for entering word formats & quantization, also instantiates fixpoint
    filter class :class:`FilterFIR`.
    """
    sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outcgoing
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self):
        super().__init__()

        self.title = ("<b>Direct-Form 1 (DF1) IIR Filter</b>")
        self.description = ("Topology with one accumulator, more robust against "
                            "overflows than DF2. Only suitable for low-order filters.")
        self.img_name = "iir_df1.png"

        self._construct_UI()
        # Construct an instance of the fixpoint filter using the settings from
        # the 'fxqc' quantizer dict:
        self.fx_filt = IIR_DF1_pyfixp(fb.fil[0]['fxqc'])
        self.update()  # initial setting of overflow counter display

    # --------------------------------------------------------------------------
    def _construct_UI(self):
        """
        Intitialize the UI with widgets for coefficient format and input and
        output quantization
        """
        # widget for quantization of coefficients 'b'
        if 'QCB' not in fb.fil[0]['fxqc']:
            fb.fil[0]['fxqc'].update({'QCB': {}})  # no coefficient settings in dict yet
            logger.warning("Empty dict / missing key 'fxqc['QCB]'!")
        self.wdg_wq_coeffs_b = FX_UI_WQ(
            fb.fil[0]['fxqc']['QCB'], wdg_name='wq_coeffs_b',
            label='<b>Coeff. Quantization <i>b<sub>I.F&nbsp;</sub></i>:</b>',
            MSB_LSB_vis='msb')
        layV_wq_coeffs_b = QVBoxLayout()
        layV_wq_coeffs_b.addWidget(self.wdg_wq_coeffs_b)

        # widget for quantization of coefficients 'a'
        if 'QCA' not in fb.fil[0]['fxqc']:
            fb.fil[0]['fxqc'].update({'QCA': {}})  # no coefficient settings in dict yet
            logger.warning("Empty dict / missing key 'fxqc['QCA]'!")
        self.wdg_wq_coeffs_a = FX_UI_WQ(
            fb.fil[0]['fxqc']['QCA'], wdg_name='wq_coeffs_a',
            label='<b>Coeff. Quantization <i>a<sub>I.F&nbsp;</sub></i>:</b>',
            MSB_LSB_vis='max')
        layV_wq_coeffs_a = QVBoxLayout()
        layV_wq_coeffs_a.addWidget(self.wdg_wq_coeffs_a)

        # widget for accumulator quantization
        if 'QA' not in fb.fil[0]['fxqc']:
            fb.fil[0]['fxqc']['QA'] = {}
        set_dict_defaults(fb.fil[0]['fxqc']['QA'],
                          {'WI': 0, 'WF': 31, 'W': 32, 'ovfl': 'wrap', 'quant': 'floor'})
        self.wdg_wq_accu = FX_UI_WQ(
            fb.fil[0]['fxqc']['QA'], wdg_name='wq_accu',
            label='<b>Accu Quantizer <i>Q<sub>A&nbsp;</sub></i>:</b>',
            cmb_w_vis='max')
        layV_wq_accu = QVBoxLayout()
        layV_wq_accu.addWidget(self.wdg_wq_accu)

        # ----------------------------------------------------------------------
        layVWdg = QVBoxLayout()
        # margins are created in input_fixpoint_specs widget
        layVWdg.setContentsMargins(0, 0, 0, 0)
        layVWdg.addLayout(layV_wq_coeffs_b)
        layVWdg.addLayout(layV_wq_coeffs_a)
        layVWdg.addLayout(layV_wq_accu)
        self.setLayout(layVWdg)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs & EVENTFILTERS
        # ----------------------------------------------------------------------
        self.wdg_wq_coeffs_b.sig_tx.connect(self.process_sig_rx)
        self.wdg_wq_coeffs_a.sig_tx.connect(self.process_sig_rx)
        self.wdg_wq_accu.sig_tx.connect(self.process_sig_rx)

    # --------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Check whether a signal was generated locally (key = 'ui'). If so:
        - update the referenced quantization dictionary
        - emit `{'fx_sim': 'specs_changed'}` with local id

        When a `{'fx_sim': 'specs_changed'}` or `{'data_changed': xxx}`
        signal is received, update the ui via `self.dict_ui`.

        Ignore all other signals
        """
        logger.info("sig_rx:\n{0}".format(pprint_log(dict_sig)))
        if dict_sig['id'] == id(self):
            logger.warning(f'Stopped infinite loop: "{first_item(dict_sig)}"')
            return

        """
        Update of coefficient quantization settings has been performed inside
        the quantization widgets `FX_UI_WQ`. Now, update the quantization counters
        """
        if 'ui' in dict_sig:
            # signal generated locally by modifying coefficient format
            if not dict_sig['wdg_name'] in {'wq_coeffs_b', 'wq_coeffs_a', 'wq_accu'}:
                logger.error(f"Unknown widget name '{dict_sig['wdg_name']}' "
                             f"in '{__name__}' !")
                return

            # emit signal, replace ui id with id of *this* widget
            self.emit({'fx_sim': 'specs_changed', 'id': id(self)})

        # quantization dictionary has been updated outside the widget
        # (signal `{data_changed: xxx}` or `{'fx_sim': 'specs_changed'}` received)
        elif 'data_changed' in dict_sig or\
            'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
            self.dict2ui()

    # --------------------------------------------------------------------------
    def dict2ui(self):
        """
        Update all parts of the UI that need to be updated when specs or data have been
        changed outside this class, e.g. coefficients and coefficient quantization
        settings. This also provides the initial setting for the widgets when
        the filter has been changed.

        This is called from one level above by
        :class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs`.
        """
        self.wdg_wq_coeffs_b.dict2ui()  # update coefficient quantization
        self.wdg_wq_coeffs_a.dict2ui()  # settings
        self.wdg_wq_accu.dict2ui()
        logger.warning(f"dict2ui: b_q = {fb.fil[0]['fxqc']['QCB']}")

    # --------------------------------------------------------------------------
    def update(self):
        """
        Update the overflow counters etc. of the UI after simulation has finished.

        This is usually called from one level above by
        :class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs`.
        """
        self.wdg_wq_coeffs_b.update()
        self.wdg_wq_coeffs_a.update()
        self.wdg_wq_accu.update()

    # --------------------------------------------------------------------------
    def fxfilter(self, stimulus):

        return self.fx_filt.fxfilter(x=stimulus)[0]


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """ Run widget standalone with
    `python -m pyfda.fixpoint_widgets.iir_df1.iir_df1_pyfixp_ui`
    """
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = IIR_DF1_pyfixp_UI()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
