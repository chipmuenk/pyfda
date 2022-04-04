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
            logger.warning("Empty dict / missing key 'fxqc['QCB]'!")
        self.wdg_wq_coeffs_b = FX_UI_WQ(
            fb.fil[0]['fxqc']['QCB'], wdg_name='wq_coeffs_b',
            label='<b>Coeff. Quantization <i>b<sub>I.F&nbsp;</sub></i>:</b>',
            MSB_LSB_vis='on')

        # widget for quantization of coefficients 'a'
        if 'QCA' not in fb.fil[0]['fxqc']:
            fb.fil[0]['fxqc'].update({'QCA': {}})  # no coefficient settings in dict yet
            logger.warning("Empty dict / missing key 'fxqc['QCA]'!")
        self.wdg_wq_coeffs_a = FX_UI_WQ(
            fb.fil[0]['fxqc']['QCA'], wdg_name='wq_coeffs_a',
            label='<b>Coeff. Quantization <i>a<sub>I.F&nbsp;</sub></i>:</b>',
            MSB_LSB_vis='max')

        # widget for accumulator quantization
        if 'QA' not in fb.fil[0]['fxqc']:
            fb.fil[0]['fxqc']['QA'] = {}
        set_dict_defaults(fb.fil[0]['fxqc']['QA'],
                          {'WI': 0, 'WF': 31, 'W': 32, 'ovfl': 'wrap', 'quant': 'floor'})
        self.wdg_wq_accu = FX_UI_WQ(
            fb.fil[0]['fxqc']['QA'], wdg_name='wq_accu',
            label='<b>Accu Quantizer <i>Q<sub>A&nbsp;</sub></i>:</b>',
            cmb_w_vis='max')

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

        # ----------------------------------------------------------------------
        layVWdg = QVBoxLayout()
        layVWdg.setContentsMargins(0, 0, 0, 0)
        layVWdg.addWidget(self.wdg_wq_coeffs_b)
        layVWdg.addWidget(self.wdg_wq_coeffs_a)
        layVWdg.addWidget(self.wdg_wq_accu)
        layVWdg.addStretch()
        self.setLayout(layVWdg)

    # --------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        logger.warning("sig_rx:\n{0}".format(pprint_log(dict_sig)))
        # check whether anything needs to be done locally
        # could also check here for 'quant', 'ovfl', 'WI', 'WF' (not needed at the moment)
        # if not, just emit the dict.
        if 'ui' in dict_sig:
            if dict_sig['wdg_name'] in {'wq_coeffs_b', 'wq_coeffs_a'}:  # coeffs format
                """
                Update coefficient quantization settings and coefficients.
                This is performed inside the quantization widgets `FX_UI_WQ`

                The new values are written to the fixpoint coefficient dict as
                `fb.fil[0]['fxqc']['QCB']` and  `fb.fil[0]['fxqc']['b']` and
                `fb.fil[0]['fxqc']['QCA']` and  `fb.fil[0]['fxqc']['a']`.
                """
                pass

            elif dict_sig['wdg_name'] == 'wq_accu':  # accu format updated
                pass
                # TODO: process quantization settings here?

            else:
                logger.error(f"Unknown widget name '{dict_sig['wdg_name']}' "
                             f"in '{__name__}' !")
                return

            # - update fixpoint accu and coefficient quantization dict
            # - emit {'fx_sim': 'specs_changed'}
            fb.fil[0]['fxqc'].update(self.ui2dict())
            self.emit({'fx_sim': 'specs_changed'})

        elif 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
            self.dict2ui()

        else:
            logger.error(f"Unknown key '{first_item(dict_sig)}' (should be 'ui')"
                         f"in '{__name__}' !")

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
        logger.warning("called dict2ui")
        self.wdg_wq_coeffs_b.dict2ui()  # update coefficient quantization
        self.wdg_wq_coeffs_a.dict2ui()  # settings
        self.wdg_wq_accu.dict2ui()

    # --------------------------------------------------------------------------
    def ui2dict(self):
        """
        Read out the quantization subwidgets and store their settings in the central
        fixpoint dictionary `fb.fil[0]['fxqc']` using the keys described below.

        Coefficients are quantized with these settings in the subdictionary under
        the keys 'b' and 'a'.

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
        - 'QCA': dictionary with a coefficients quantization settings
        - 'QA': dictionary with accumulator quantization settings
        - 'b' : list of quantized b coefficients in format WI.WF
        - 'a' : list of quantized a coefficients in format WI.WF
        """
        fxqc_dict = fb.fil[0]['fxqc']
        # fxqc_dict['QA'].update(self.wdg_wq_accu.q_dict)
        # fxqc_dict['QCB'].update(self.wdg_wq_coeffs_b.q_dict)
        # fxqc_dict['QCA'].update(self.wdg_wq_coeffs_a.q_dict)

        fxqc_dict.update({'b': self.wdg_wq_coeffs_b.quant_coeffs(fb.fil[0]['ba'][0])})
        fxqc_dict.update({'a': self.wdg_wq_coeffs_a.quant_coeffs(fb.fil[0]['ba'][1])})

        return fxqc_dict

    # --------------------------------------------------------------------------
    def init_filter(self):
        """
        Construct an instance of the fixpoint filter object using the settings from
        the 'fxqc' quantizer dict
        """
        p = fb.fil[0]['fxqc']  # parameter dictionary with coefficients etc.
        self.fx_filt = IIR_DF1_pyfixp(p)

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
