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
            ("m", "M", "<span><b>Manual</b> entry</span>"),
            ("a", "A",
             "<span><b>Automatic</b> worst case estimation from coefficients "
             "and input word formats.</span>")
            ]

        self.cmb_wq_coeffs_a_items = [
            "<span>Number of integer bits</span>",
            ("m", "M", "<span><b>Manual</b> entry</span>"),
            ("a", "A",
             "<span><b>Automatic</b> calculation from largest coefficient.</span>")
            ]

        self.cmb_wq_coeffs_b_items = [
            "<span>Number of integer bits</span>",
            ("m", "M", "<span><b>Manual</b> entry</span>"),
            ("a", "A",
             "<span><b>Automatic</b> calculation from largest coefficient.</span>")
            ]

        self._construct_UI()
        # Construct an instance of the fixpoint filter using the settings from
        # the 'fxq' quantizer dict:
        self.fx_filt = IIR_DF1_pyfixp(fb.fil[0]['fxq'])
        self.update_ovfl_cnt_all()  # initialize all overflow counters / display

    # --------------------------------------------------------------------------
    def _construct_UI(self):
        """
        Intitialize the UI with widgets for coefficient format and input and
        output quantization
        """
        # widget for quantization of coefficients 'b'
        if 'QCB' not in fb.fil[0]['fxq']:
            fb.fil[0]['fxq'].update({'QCB': {}})  # no coefficient settings in dict yet
            logger.warning("Empty dict / missing key 'fb.fil{0]['fxq']['QCB']'!")
        self.wdg_wq_coeffs_b = FX_UI_WQ(
            fb.fil[0]['fxq']['QCB'], objectName='fx_ui_wq_iir_df1_coeffs_b',
            label='<b>Coeff. Quantization <i>b<sub>I.F&nbsp;</sub></i>:</b>',
            MSB_LSB_vis='max', cmb_w_vis='on', cmb_w_items=self.cmb_wq_coeffs_b_items)
        layV_wq_coeffs_b = QVBoxLayout()
        layV_wq_coeffs_b.addWidget(self.wdg_wq_coeffs_b)

        # widget for quantization of coefficients 'a'
        if 'QCA' not in fb.fil[0]['fxq']:
            fb.fil[0]['fxq'].update({'QCA': {}})  # no coefficient settings in dict yet
            logger.warning("Empty dict / missing key 'fb.fil{0]['fxq']['QCA']'!")
        self.wdg_wq_coeffs_a = FX_UI_WQ(
            fb.fil[0]['fxq']['QCA'], objectName='fx_ui_wq_iir_df1_coeffs_a',
            label='<b>Coeff. Quantization <i>a<sub>I.F&nbsp;</sub></i>:</b>',
            MSB_LSB_vis='max', cmb_w_vis='on', cmb_w_items=self.cmb_wq_coeffs_a_items)
        layV_wq_coeffs_a = QVBoxLayout()
        layV_wq_coeffs_a.addWidget(self.wdg_wq_coeffs_a)
        # calculate wordlength needed for coefficients if required
        if qget_cmb_box(self.wdg_wq_coeffs_a.cmbW) == 'a':
            self.calc_wi_coeffs_a()
        if qget_cmb_box(self.wdg_wq_coeffs_b.cmbW) == 'a':
            self.calc_wi_coeffs_b()

        # widget for accumulator quantization
        if 'QACC' not in fb.fil[0]['fxq']:
            fb.fil[0]['fxq']['QACC'] = {}  # initialize dict settings
        set_dict_defaults(
            fb.fil[0]['fxq']['QACC'],
            {'WI': 0, 'WF': 31, 'ovfl': 'wrap', 'quant': 'floor', 'w_a_m': 'a',
             'N_over': 0})
        self.wdg_wq_accu = FX_UI_WQ(
            fb.fil[0]['fxq']['QACC'], objectName='fx_ui_wq_iir_df1_accu',
            label='<b>Accu Quantizer <i>Q<sub>ACC&nbsp;</sub></i>:</b>',
            cmb_w_vis='on', cmb_w_items=self.cmb_wq_accu_items)
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
          `{'data_changed': xxx}` update the UI via `self.dict2ui`.

        Ignore all other signals

        Note: If coefficient / accu quantization settings have been changed in the UI,
        the referenced dicts `fb.fil[0]['fxq']['QCB']`, `['QCA']` and `...['QACC']`
        have already been updated by the corresponding subwidgets `FX_UI_WQ`
        """
        logger.debug("sig_rx:\n{0}".format(pprint_log(dict_sig)))
        if dict_sig['id'] == id(self):
            logger.warning(f'Stopped infinite loop: "{first_item(dict_sig)}"')
            return

        if 'ui_local_changed' in dict_sig:
            # signal generated locally by modifying coefficient / accu format
            ui_changed = dict_sig['ui_local_changed']  # name of changed ui element
            if not dict_sig['sender_name']\
                    in {'fx_ui_wq_iir_df1_coeffs_b', 'fx_ui_wq_iir_df1_coeffs_a',
                        'fx_ui_wq_iir_df1_accu'}:
                logger.error(f"Unknown sender name '{dict_sig['sender_name']}' "
                             f"in '{__name__}' !")
                return

            # changes in accu widget
            elif dict_sig['sender_name'] == 'fx_ui_wq_iir_df1_accu':  # accu format updated
                if ui_changed in {'cmbW', 'WF', 'WI'}:
                    cmbW = qget_cmb_box(self.wdg_wq_accu.cmbW)
                    if cmbW == 'm':
                        if ui_changed == 'cmbW':
                            # returning to manual setting, don't do anything
                            return
                        else:
                            pass  # WI or WF have been edited, emit 'specs_changed'
                    elif cmbW == 'a':
                        # when switching to auto settings, run automatic accu calculation
                        # this also reverses manual edits of WI or WF wordlengths
                        # manual entry of word lengths cannot be disabled easily due to
                        # additional logic in the wdg_wq_accu widget (class FX_UI_WQ)
                        self.update_accu_settings()
                    else:
                        logger.error(f"Unknown accu combobox setting '{cmbW}'!")
                        return

            # changes in coeffs 'a' widget
            elif dict_sig['sender_name'] == 'fx_ui_wq_iir_df1_coeffs_a':
                if ui_changed in {'cmbW', 'WF', 'WI'}:
                    cmbW = qget_cmb_box(self.wdg_wq_coeffs_a.cmbW)
                    if cmbW == 'm':
                        if ui_changed == 'cmbW':
                            # returning to manual setting, don't do anything
                            return
                        else:
                            pass  # WI or WF have been edited, emit 'specs_changed'

                    elif cmbW == 'a':
                        # when switching to auto settings, run automatic calculation
                        # of required integer bits for coeffs a
                        # this also reverses manual edits of WI or WF wordlengths
                        self.calc_wi_coeffs_a()
                    else:
                        logger.error(f"Unknown coeff. combobox setting '{cmbW}'!")
                        return

                    # in case coefficient length has been changed, update accu as well
                    if qget_cmb_box(self.wdg_wq_accu.cmbW) == 'a':
                        self.update_accu_settings()

            # changes in coeffs 'b' widget
            elif dict_sig['sender_name'] == 'fx_ui_wq_iir_df1_coeffs_b':
                if ui_changed in {'cmbW', 'WF', 'WI'}:
                    cmbW = qget_cmb_box(self.wdg_wq_coeffs_b.cmbW)
                    if cmbW == 'm':
                        if ui_changed == 'cmbW':
                            # returning to manual setting, don't do anything
                            return
                        else:
                            pass  # WI or WF have been edited, emit 'specs_changed'

                    elif cmbW == 'a':
                        # when switching to auto settings, run automatic calculation
                        # of required integer bits for coeffs b
                        # this also reverses manual edits of WI or WF wordlengths
                        self.calc_wi_coeffs_b()
                    else:
                        logger.error(f"Unknown coeff. combobox setting '{cmbW}'!")
                        return

                    # in case coefficient length has been changed, update accu as well
                    if qget_cmb_box(self.wdg_wq_accu.cmbW) == 'a':
                        self.update_accu_settings()


            # emit signal, replace UI id with id of *this* widget
            self.emit({'fx_sim': 'specs_changed', 'id': id(self)})

        # quantization dictionary has been updated outside the widget, update UI
        elif 'data_changed' in dict_sig or\
                'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
            self.dict2ui()

    # --------------------------------------------------------------------------
    def calc_wi_coeffs_a(self):
        """
        Calculate required number of integer bits for the largest 'a' coefficient

        The new value is written to the fixpoint coefficient dict
        `fb.fil[0]['fxq']['QCA']` and the UI is updated.
        """
        WI_A = int(np.ceil(np.log2((np.abs(np.max(fb.fil[0]['ba'][1]))))))
        fb.fil[0]['fxq']['QCA']['WI'] = WI_A
        # update quantizer settings and UI
        self.wdg_wq_coeffs_a.dict2ui(fb.fil[0]['fxq']['QCA'])

    # --------------------------------------------------------------------------
    def calc_wi_coeffs_b(self):
        """
        Calculate required number of integer bits for the largest 'b' coefficient

        The new value is written to the fixpoint coefficient dict
        `fb.fil[0]['fxq']['QCB']` and the UI is updated.
        """
        WI_B = int(np.ceil(np.log2((np.abs(np.max(fb.fil[0]['ba'][0]))))))
        fb.fil[0]['fxq']['QCB']['WI'] = max(WI_B, 0)
        # update quantizer settings and UI
        self.wdg_wq_coeffs_b.dict2ui(fb.fil[0]['fxq']['QCB'])

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
        `fb.fil[0]['fxq']['QACC']` and the UI is updated.
        """
        # except BaseException as e: # Exception as e:
        #     logger.error("An error occured:", exc_info=True)
        #     return

        if qget_cmb_box(self.wdg_wq_accu.cmbW) == 'a':
            fb.fil[0]['fxq']['QACC']['WF'] = max(
                fb.fil[0]['fxq']['QI']['WF'] + fb.fil[0]['fxq']['QCB']['WF'],
                fb.fil[0]['fxq']['QO']['WF'] + fb.fil[0]['fxq']['QCA']['WF'])

            fb.fil[0]['fxq']['QACC']['WI'] = max(
                fb.fil[0]['fxq']['QI']['WI'] + fb.fil[0]['fxq']['QCB']['WI'],
                fb.fil[0]['fxq']['QO']['WI'] + fb.fil[0]['fxq']['QCA']['WI'])

        # update UI and Q.q_dict (quantization settings) from filter dict
        self.wdg_wq_accu.dict2ui(fb.fil[0]['fxq']['QACC'])

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

        self.wdg_wq_coeffs_b.dict2ui(fb.fil[0]['fxq']['QCB'])  # update coefficient quantization
        self.wdg_wq_coeffs_a.dict2ui(fb.fil[0]['fxq']['QCA'])  # settings
        # TODO: In the past, only 'QCB' was passed directly - why?!
        self.update_accu_settings()   # update accumulator settings and UI

    # --------------------------------------------------------------------------
    def update_ovfl_cnt_all(self):
        """
        Update the overflow counters of the UI after simulation has finished.

        This is usually called from one level above by
        :class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs`.
        """
        self.wdg_wq_coeffs_b.update_ovfl_cnt()
        self.wdg_wq_coeffs_a.update_ovfl_cnt()
        self.wdg_wq_accu.update_ovfl_cnt()

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
    fb.fil[0]['fx_sim'] = True  # enable fixpoint mode

    mainw = IIR_DF1_pyfixp_UI()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
