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

import numpy as np
import pyfda.filterbroker as fb
from pyfda.libs.pyfda_lib import set_dict_defaults, pprint_log, first_item
from pyfda.libs.pyfda_qt_lib import qget_cmb_box

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

        self.cmb_wq_accu_items = [
            "<span>Set Accumulator word format</span>",
            ("man", "M", "<span><b>Manual</b> entry</span>"),
            ("auto", "A",
             "<span><b>Automatic</b> estimation from coefficients and input word "
             "formats (worst case estimation).</span>")
            ]
        self.cmb_wq_accu_init = 'man'

        self.cmb_wq_coeffs_a_items = [
            "<span>Number of integer bits</span>",
            ("man", "M", "<span><b>Manual</b> entry</span>"),
            ("auto", "A",
             "<span><b>Automatic</b> calculation from largest coefficient.</span>")
            ]
        self.cmb_wq_coeffs_a_init = 'auto'

        self._construct_UI()
        # Construct an instance of the fixpoint filter using the settings from
        # the 'fxqc' quantizer dict:
        self.fx_filt = IIR_DF1_pyfixp(fb.fil[0]['fxqc'])
        self.update_disp()  # initial setting of overflow counter display

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
            MSB_LSB_vis='max', cmb_w_vis='on', cmb_w_items=self.cmb_wq_coeffs_a_items,
            cmb_w_init=self.cmb_wq_coeffs_a_init)
        layV_wq_coeffs_a = QVBoxLayout()
        layV_wq_coeffs_a.addWidget(self.wdg_wq_coeffs_a)
        self.update_coeffs_settings()

        # widget for accumulator quantization
        if 'QACC' not in fb.fil[0]['fxqc']:
            fb.fil[0]['fxqc']['QACC'] = {}
        set_dict_defaults(fb.fil[0]['fxqc']['QACC'],
                          {'WI': 0, 'WF': 31, 'W': 32, 'ovfl': 'wrap', 'quant': 'floor'})
        self.wdg_wq_accu = FX_UI_WQ(
            fb.fil[0]['fxqc']['QACC'], wdg_name='wq_accu',
            label='<b>Accu Quantizer <i>Q<sub>A&nbsp;</sub></i>:</b>',
            cmb_w_vis='on', cmb_w_items=self.cmb_wq_accu_items,
            cmb_w_init=self.cmb_wq_accu_init)
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
        - For locally generated signals (key = 'ui_local_changed'), emit
          `{'fx_sim': 'specs_changed'}` with local id.
        - For external changes, i.e. `{'fx_sim': 'specs_changed'}` or
          `{'data_changed': xxx}` update the UI via `self.dict_ui`.

        Ignore all other signals

        Note: If coefficient / accu quantization settings have been changed in the UI,
        the referenced dicts `fb.fil[0]['fxqc']['QCB']`, `['QCA']` and `...['QACC']`
        have already been updated by the corresponding subwidgets `FX_UI_WQ`
        """
        logger.debug("sig_rx:\n{0}".format(pprint_log(dict_sig)))
        if dict_sig['id'] == id(self):
            logger.warning(f'Stopped infinite loop: "{first_item(dict_sig)}"')
            return

        if 'ui_local_changed' in dict_sig:
            # signal generated locally by modifying coefficient / accu format
            ui_changed = dict_sig['ui_local_changed']  # name of changed ui element
            if not dict_sig['wdg_name'] in {'wq_coeffs_b', 'wq_coeffs_a', 'wq_accu'}:
                logger.error(f"Unknown widget name '{dict_sig['wdg_name']}' "
                             f"in '{__name__}' !")
                return

            elif dict_sig['wdg_name'] == 'wq_accu':  # accu format updated
                if ui_changed in {'cmbW', 'WF', 'WI'}:
                    cmbW = qget_cmb_box(self.wdg_wq_accu.cmbW)
                    if cmbW == 'man':
                        if ui_changed == 'cmbW':
                            # returning to manual setting, don't do anything
                            return
                        else:
                            pass  # WI or WF have been edited, emit 'specs_changed'
                    elif cmbW == 'auto':
                        # when switching to auto settings, run automatic accu calculation
                        # this also reverses manual edits of WI or WF wordlengths
                        # manual entry of word lengths cannot be disabled easily due to
                        # additional logic in the wdg_wq_accu widget (class FX_UI_WQ)
                        self.update_accu_settings()
                    else:
                        logger.error(f"Unknown accu combobox setting '{cmbW}'!")
                        return

            elif dict_sig['wdg_name'] in {'wq_coeffs_a', 'wq_coeffs_b'}:  # coeffs updated
                if ui_changed in {'cmbW', 'WF', 'WI'}:
                    cmbW = qget_cmb_box(self.wdg_wq_coeffs_a.cmbW)
                    if cmbW == 'man':
                        if ui_changed == 'cmbW':
                            # returning to manual setting, don't do anything
                            return
                        else:
                            pass  # WI or WF have been edited, emit 'specs_changed'

                    elif cmbW == 'auto':
                        # when switching to auto settings, run automatic calculation
                        # of required integer bits for coeffs a
                        # this also reverses manual edits of WI or WF wordlengths
                        # manual entry of word lengths cannot be disabled easily due to
                        # additional logic in the wdg_wq_accu widget (class FX_UI_WQ)
                        self.update_coeffs_settings()
                    else:
                        logger.error(f"Unknown coeff. combobox setting '{cmbW}'!")
                        return

                    # in case coefficient length has been changed, update accu as well
                    if qget_cmb_box(self.wdg_wq_accu.cmbW) == 'auto':
                        self.update_accu_settings()

            # emit signal, replace UI id with id of *this* widget
            self.emit({'fx_sim': 'specs_changed', 'id': id(self)})

        # quantization dictionary has been updated outside the widget, update UI
        elif 'data_changed' in dict_sig or\
                'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
            self.dict2ui()

    # --------------------------------------------------------------------------
    def update_coeffs_settings(self):
        """
        Calculate required number of integer bits for the largest coefficient

        The new value is written to the fixpoint coefficient dict
        `fb.fil[0]['fxqc']['QCA']` and the UI is updated.
        """
        WI_A = int(np.ceil(np.log2((np.abs(np.max(fb.fil[0]['ba'][1]))))))
        fb.fil[0]['fxqc']['QCA']['WI'] = WI_A
        # update quantization settings ('W', 'Q', ...) and UI
        self.wdg_wq_coeffs_a.QObj.set_qdict({})  # update `self.wdg_wq_coeffs_a.q_dict`
        self.wdg_wq_coeffs_a.dict2ui()

    # --------------------------------------------------------------------------
    def update_accu_settings(self):
        """
        Calculate required number of fractional bits for the accumulator from
        the sum of coefficient and input resp. output fractional bits, using
        the maximum of both.

        Calculate number of extra integer bits for the accumulator (guard bits)
        for `cmbW == 'auto'` from the sum of the integer part of recursive
        coefficients and output signal resp. the integer part of non-recursive
        coefficients and input signal, depending on which one is larger.

        The new values are written to the fixpoint coefficient dict
        `fb.fil[0]['fxqc']['QACC']`.
        """
        # except BaseException as e: # Exception as e:
        #     logger.error("An error occured:", exc_info=True)
        #     return

        if qget_cmb_box(self.wdg_wq_accu.cmbW) == "auto":
            fb.fil[0]['fxqc']['QACC']['WF'] = max(
                fb.fil[0]['fxqc']['QI']['WF'] + fb.fil[0]['fxqc']['QCB']['WF'],
                fb.fil[0]['fxqc']['QO']['WF'] + fb.fil[0]['fxqc']['QCA']['WF'])

            fb.fil[0]['fxqc']['QACC']['WI'] = max(
                fb.fil[0]['fxqc']['QI']['WI'] + fb.fil[0]['fxqc']['QCB']['WI'],
                fb.fil[0]['fxqc']['QO']['WI'] + fb.fil[0]['fxqc']['QCA']['WI'])

        # update quantization settings like 'Q', 'W' etc. and UI
        self.wdg_wq_accu.QObj.set_qdict({})  # update `self.wdg_wq_accu.q_dict`
        self.wdg_wq_accu.dict2ui()

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

    # --------------------------------------------------------------------------
    def update_disp(self):
        """
        Update the overflow counters etc. of the UI after simulation has finished.

        This is usually called from one level above by
        :class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs`.
        """
        self.wdg_wq_coeffs_b.update_disp()
        self.wdg_wq_coeffs_a.update_disp()
        self.wdg_wq_accu.update_disp()

    # --------------------------------------------------------------------------
    def fxfilter(self, stimulus):
        """
        Provide  wrapper around fixpoint filter simulation method:
        * takes stimulus (iterable or float or None) as parameter
        * returns fixpoint response (ndarray of float)
        """
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
