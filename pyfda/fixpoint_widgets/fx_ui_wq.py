# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Helper classes and functions for generating and simulating fixpoint filters
"""
import sys
import inspect

# from numpy.lib.function_base import iterable

import pyfda.libs.pyfda_fix_lib as fx

from pyfda.libs.compat import (
    Qt, QWidget, QLabel, QLineEdit, QComboBox, QPushButton, QIcon,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, pyqtSignal)

from pyfda.libs.pyfda_qt_lib import (
    qcmb_box_populate, qget_cmb_box, qset_cmb_box, qstyle_widget)
from pyfda.pyfda_rc import params
from pyfda.libs.pyfda_lib import safe_eval, to_html

import logging
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
class FX_UI_WQ(QWidget):
    """
    Widget for selecting quantization / overflow options.

    A reference to a quantization dictionary `q_dict` is passed to the constructor.
    This can be a global quantization dict like `fb.fil[0]['fxqc']['QCB']` or a local
    dict.

    This widget allows the user to modify the values for the following keys:

    - `quant`   : quantization behaviour
    - `ovfl`    : overflow behaviour
    - `WI`      : number of integer bits
    - `WF`      : number of fractional bits
    - `scale`   : scaling factor between real world value and integer representation

    These quantization settings are also stored in the instance quantizer object
    `self.QObj`.

    Widget settings are stored in the local `dict_ui` dictionary with the keys and their
    default settings described below. When instantiating the widget, these settings can
    be modified by corresponding keyword parameters, e.g.

    ```
        self.wdg_wq_accu = UI_WQ(
            fb.fil[0]['fxqc']['QACC'], wdg_name='wq_accu',
            label='<b>Accu Quantizer <i>Q<sub>A&nbsp;</sub></i>:</b>')
    ```

    All labels support HTML formatting.

    'wdg_name'      : 'fx_ui_wq'                # widget name, used to discern between
                                                # multiple instances
    'label'         : ''                        # widget text label, usually set by the

    'label_q'       : 'Quant.'                  # subwidget text label
    'cmb_q'         : List with tooltip and combo box choices (default: 'round', 'fix',
                        'floor'), see `pyfda_qt_lib.qcmb_box_populate()` or code below
    'quant'         : 'round'                   # initial / current setting

    'label_ov'      : 'Ovfl.'                   # subwidget text label
    'cmb_ov'        : List with tooltip and combo box choices (default: 'wrap', 'sat')
    'ovfl'          : 'wrap'                    # initial / current setting

    'fractional'    : True                      # Display WF, otherwise WF=0
    'lbl_sep'       : '.'                       # label between WI and WF field
    'max_led_width' : 30                        # max. length of lineedit field
    'WI'            : 0                         # number of frac. *bits*
    'WI_len'        : 2                         # max. number of integer *digits*
    'tip_WI'        : 'Number of integer bits'  # Mouse-over tooltip
    'WF'            : 15                        # number of frac. *bits*
    'WF_len'        : 2                         # max. number of frac. *digits*
    'tip_WF'        : 'Number of frac. bits'    # Mouse-over tooltip

    'lock_vis'      : 'off''                    # Pushbutton for locking visible
    'tip_lock'      : 'Sync input/output quant.'# Tooltip for  lock push button

    'cmb_w_vis'     : 'off'                     # Integrated combo widget visible?
    'cmb_w_items'   : List with tooltip and combo box choices
    'cmb_w_init'    : 'man'                     # initial setting
    'count_ovfl_vis': 'on'                      # Is overflow counter visible?
                                                #   ['on', 'off', 'auto']
    'MSB_LSB_vis'   : 'off'                     # Are MSB / LSB settings visible?
    """
    # sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outcgoing
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, q_dict: dict, **kwargs) -> None:
        super().__init__()

        self.q_dict = q_dict
        self._construct_UI(**kwargs)

    # # --------------------------------------------------------------------------
    # def process_sig_rx(self, dict_sig=None):
    #     """ Update the UI when the quantization dictionary has been updated outside
    #         (signal `{'fx_sim': 'specs_changed'}` received)"""

    #     logger.warning("sig_rx:\n{0}".format(dict_sig))

    #     if 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
    #         self.dict2ui()

    # --------------------------------------------------------------------------
    def _construct_UI(self, **kwargs):
        """ Construct widget """
        cmb_q = ["Select the kind of quantization.",
                 ("round", "Round",
                  "<span>Round towards nearest representable number</span>"),
                 ("fix", "Fix", "Round towards zero"),
                 ("floor", "Floor", "<span>Round towards negative infinity / "
                  "two's complement truncation.</span>"),
                 ("none", "None",
                  "<span>No quantization (only for debugging)</span>")]
        cmb_ov = ["<span>Select overflow behaviour.</span>",
                  ("wrap", "Wrap", "Two's complement wrap around"),
                  ("sat", "Sat",
                   "<span>Saturation, i.e. limit at min. / max. value</span>"),
                  ("none", "None",
                   "<span>No overflow behaviour (only for debugging)</span>")]
        cmb_w = ["<span>Set Accumulator word format</span>",
                 ("man", "M", "<span><b>Manual</b> entry of accumulator format.</span>"),
                 ("auto", "A",
                  "<span><b>Automatic</b> calculation for given input word format "
                  "and coefficients (<i>coefficient area</i>).</span>"),
                 ("full", "F",
                  "<span><b>Full</b> accumulator width for given input word format "
                  "and arbitrary coefficients.</span>")
                 ]
        # default widget settings:
        dict_ui = {'wdg_name': 'fx_ui_wq', 'label': '',
                   'label_q': 'Quant.', 'cmb_q_items': cmb_q, 'quant': 'round',
                   'label_ov': 'Ovfl.', 'cmb_ov_items': cmb_ov, 'ovfl': 'wrap',
                   #
                   'lbl_sep': '.', 'max_led_width': 30,
                   'WG': 0, 'WG_len': 2, 'tip_WG': 'Number of guard bits',
                   'WI': 0, 'WI_len': 2, 'tip_WI': 'Number of integer bits',
                   'WF': 15, 'WF_len': 2, 'tip_WF': 'Number of fractional bits',
                   'fractional': True,
                   'cmb_w_vis': 'off', 'cmb_w_items': cmb_w, 'cmb_w_init': 'man',
                   'lock_vis': 'off',
                   'tip_lock':
                       '<span>Sync input and output quantization formats.</span>',
                   'count_ovfl_vis': 'auto', 'MSB_LSB_vis': 'off'
                   }

        # update local `dict_ui` with keyword arguments passed during construction
        for key, val in kwargs.items():
            if key not in dict_ui:
                logger.warning(f"Unknown key '{key}'")
            else:
                dict_ui.update({key: val})
        # dict_ui.update(map(kwargs)) # same as above?

        self.wdg_name = dict_ui['wdg_name']
        lbl_wdg = QLabel(dict_ui['label'], self)

        self.cmbQuant = QComboBox(self)
        qcmb_box_populate(self.cmbQuant, dict_ui['cmb_q_items'], dict_ui['quant'])
        self.cmbQuant.setObjectName('quant')

        self.cmbOvfl = QComboBox(self)
        qcmb_box_populate(self.cmbOvfl, dict_ui['cmb_ov_items'], dict_ui['ovfl'])
        self.cmbOvfl.setObjectName('ovfl')

        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQuant.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbOvfl.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.cmbW = QComboBox(self)
        qcmb_box_populate(self.cmbW, dict_ui['cmb_w_items'], dict_ui['cmb_w_init'])
        self.cmbW.setVisible(dict_ui['cmb_w_vis'] == 'on')
        self.cmbW.setObjectName("cmbW")

        self.butLock = QPushButton(self)
        self.butLock.setCheckable(True)
        self.butLock.setChecked(False)
        self.butLock.setVisible(dict_ui['lock_vis'] == 'on')
        self.butLock.setToolTip(dict_ui['tip_lock'])
        self.butLock.setFixedWidth(self.butLock.height())
        # retain size of lock widget even when hidden
        sp_retain = self.butLock.sizePolicy()
        sp_retain.setRetainSizeWhenHidden(True)
        self.butLock.setSizePolicy(sp_retain)

        self.ledWG = QLineEdit(self)
        self.ledWG.setToolTip("<span>Number of guard bits</span>")
        self.ledWG.setMaxLength(dict_ui['WI_len'])  # maximum of 2 digits
        self.ledWG.setFixedWidth(dict_ui['max_led_width'])  # width of lineedit in points
        self.ledWG.setVisible(False)
        self.ledWG.setObjectName("WG")

        self.lblPlus = QLabel("+", self)
        self.lblPlus.setVisible(False)

        self.ledWI = QLineEdit(self)
        self.ledWI.setToolTip(dict_ui['tip_WI'])
        self.ledWI.setMaxLength(dict_ui['WI_len'])  # maximum of 2 digits
        self.ledWI.setFixedWidth(dict_ui['max_led_width'])  # width of lineedit in points
        self.ledWI.setObjectName("WI")

        self.lblDot = QLabel(dict_ui['lbl_sep'], self)
        self.lblDot.setVisible(dict_ui['fractional'])

        self.ledWF = QLineEdit(self)
        self.ledWF.setToolTip(dict_ui['tip_WF'])
        self.ledWF.setMaxLength(dict_ui['WI_len'])  # maximum of 2 digits
        self.ledWF.setFixedWidth(dict_ui['max_led_width'])  # width of lineedit in points
        self.ledWF.setVisible(dict_ui['fractional'])
        self.ledWF.setObjectName("WF")

        self.count_ovfl_vis = dict_ui['count_ovfl_vis']
        self.lbl_ovfl_count = QLabel(to_html("N_ov = 0", frmt='i'))
        self.lbl_ovfl_count.setAutoFillBackground(True)

        self.MSB_LSB_vis = dict_ui['MSB_LSB_vis']

        # -------------------------------------------------------------------
        # MSB / LSB size
        # ---------------------------------------------------------------------
        self.lbl_MSB = QLabel(self)
        self.lbl_MSB.setText("undefined")

        self.lbl_LSB = QLabel(self)
        self.lbl_LSB.setText("undefined")

        layH_W = QHBoxLayout()
        layH_W.addWidget(self.ledWG)
        layH_W.addWidget(self.lblPlus)
        layH_W.addWidget(self.ledWI)
        layH_W.addWidget(self.lblDot)
        layH_W.addWidget(self.ledWF)
        layH_W.setContentsMargins(0, 0, 0, 0)

        layG = QGridLayout()
        layG.setColumnStretch(1, 10)
        # first row
        layG.addWidget(lbl_wdg, 0, 0)
        layG.addWidget(self.butLock, 0, 3)
        layG.addWidget(self.cmbW, 0, 4)
        layG.addLayout(layH_W, 0, 5)
        # second row
        layG.addWidget(self.lbl_ovfl_count, 1, 0)
        layG.addWidget(self.cmbOvfl, 1, 3, 1, 2)
        layG.addWidget(self.cmbQuant, 1, 5)
        # third row - MSB / LSB
        layG.addWidget(self.lbl_MSB, 2, 0, 1, 2)
        layG.addWidget(self.lbl_LSB, 2, 3, 1, 3, Qt.AlignRight)
        layG.setContentsMargins(5, 5, 5, 5)

        frmMain = QFrame(self)
        frmMain.setLayout(layG)

        layVMain = QVBoxLayout()  # Widget main layout
        layVMain.addWidget(frmMain)
        layVMain.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layVMain)

        # ----------------------------------------------------------------------
        # INITIAL SETTINGS OF UI AND FIXPOINT QUANTIZATION OBJECT
        # ----------------------------------------------------------------------
        WG = int(dict_ui['WG'])
        WI = int(dict_ui['WI'])
        WF = int(dict_ui['WF'])
        W = WI + WF + 1
        self.ledWG.setText(str(WG))
        self.ledWI.setText(str(WI))
        self.ledWF.setText(str(WF))
        ovfl = qget_cmb_box(self.cmbOvfl)
        quant = qget_cmb_box(self.cmbQuant)

        self.q_dict.update({'ovfl': ovfl, 'quant': quant, 'WI': WI, 'WF': WF,
                            'WG': WG, 'W': W})
        # create fixpoint quantization object from passed quantization dict
        self.QObj = fx.Fixed(self.q_dict)

        # initialize button icon
        self.butLock_clicked(self.butLock.isChecked())

        # initialize overflow counter and MSB / LSB display
        self.update_disp()

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS
        # ----------------------------------------------------------------------
        # self.sig_rx.connect(self.process_sig_rx)
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.cmbOvfl.currentIndexChanged.connect(self.ui2dict)
        self.cmbQuant.currentIndexChanged.connect(self.ui2dict)
        self.ledWG.editingFinished.connect(self.ui2dict)
        self.ledWI.editingFinished.connect(self.ui2dict)
        self.ledWF.editingFinished.connect(self.ui2dict)
        self.cmbW.currentIndexChanged.connect(self.ui2dict)

        self.butLock.clicked.connect(self.butLock_clicked)

    # --------------------------------------------------------------------------
    def butLock_clicked(self, clicked):
        """
        Update the icon of the push button depending on its state
        """
        if clicked:
            self.butLock.setIcon(QIcon(':/lock-locked.svg'))
        else:
            self.butLock.setIcon(QIcon(':/lock-unlocked.svg'))

        dict_sig = {'wdg_name': self.wdg_name, 'ui_local_changed': 'butLock'}
        self.emit(dict_sig)

    # --------------------------------------------------------------------------
    def update_disp(self):
        """
        Update the overflow counter and MSB / LSB display (if visible)
        """
        if self.MSB_LSB_vis == 'off':
            self.lbl_MSB.setVisible(False)
            self.lbl_LSB.setVisible(False)
        elif self.MSB_LSB_vis == 'max':
            self.lbl_MSB.setVisible(True)
            self.lbl_LSB.setVisible(True)
            self.lbl_MSB.setText(
                "<b><i>&nbsp;&nbsp;Max</i><sub>10</sub> = </b>"
                f"{self.QObj.q_dict['MAX']:.{params['FMT_ba']}g}")
            self.lbl_LSB.setText(
                "<b><i>LSB</i><sub>10</sub> = </b>"
                f"{self.QObj.q_dict['LSB']:.{params['FMT_ba']}g}")
        elif self.MSB_LSB_vis == 'msb':
            self.lbl_MSB.setVisible(True)
            self.lbl_LSB.setVisible(True)
            self.lbl_MSB.setText(
                "<b><i>&nbsp;&nbsp;MSB</i><sub>10</sub> = </b>"
                f"{self.QObj.q_dict['MSB']:.{params['FMT_ba']}g}")
            self.lbl_LSB.setText(
                "<b><i>LSB</i><sub>10</sub> = </b>"
                f"{self.QObj.q_dict['LSB']:.{params['FMT_ba']}g}")
        else:
            logger.error(f"Unknown option MSB_LSB_vis = '{self.MSB_LSB_vis}'")
        # -------
        frm = inspect.stack()[1]
        logger.debug(f"update: {id(self)}|{id(self.q_dict)} | {self.wdg_name} :"
                     f"{self.q_dict['N_over']} "
                     f"{inspect.getmodule(frm[0]).__name__.split('.')[-1]}."
                     f"{frm[3]}:{frm[2]}")

        if self.count_ovfl_vis == 'off':
            self.lbl_ovfl_count.setVisible(False)
        elif self.count_ovfl_vis == 'auto' and self.q_dict['N_over'] == 0:
            self.lbl_ovfl_count.setVisible(False)
        elif self.count_ovfl_vis == 'on' or\
                self.count_ovfl_vis == 'auto' and self.q_dict['N_over'] > 0:

            self.lbl_ovfl_count.setVisible(True)
            self.lbl_ovfl_count.setText(
                to_html(f"<b><i>&nbsp;&nbsp;N</i>_ov = </b>{self.q_dict['N_over']}"))
            if self.q_dict['N_over'] == 0:
                qstyle_widget(self.lbl_ovfl_count, "normal")
            else:
                qstyle_widget(self.lbl_ovfl_count, "failed")
        else:
            logger.error(f"Unknown option count_ovfl_vis = '{self.count_ovfl_vis}'")
        return

    # --------------------------------------------------------------------------
    def ui2dict(self):
        """
        Update the entries in the quantization dict from the UI for `ovfl`, `quant`,
        'WG', `WI`, `WF`, `W` when one of the widgets has been edited.

        Emit a signal with `{'ui_local_changed': <objectName of the sender>}`.
        """
        WG = int(safe_eval(self.ledWG.text(), self.QObj.q_dict['WG'], return_type="int",
                           sign='poszero'))
        self.ledWG.setText(str(WG))
        WI = int(safe_eval(self.ledWI.text(), self.QObj.q_dict['WI'], return_type="int",
                           sign='poszero'))
        self.ledWI.setText(str(WI))
        WF = int(safe_eval(self.ledWF.text(), self.QObj.q_dict['WF'], return_type="int",
                           sign='poszero'))
        self.ledWF.setText(str(WF))

        # W = int(WG + WI + WF + 1)

        ovfl = qget_cmb_box(self.cmbOvfl)
        quant = qget_cmb_box(self.cmbQuant)

        self.q_dict.update({'ovfl': ovfl, 'quant': quant, 'WG': WG, 'WI': WI, 'WF': WF})
        self.QObj.set_qdict(self.q_dict)  # set quant. object, update derived quantities
                                          # like W and Q and reset counter

        if self.sender():
            dict_sig = {'wdg_name': self.wdg_name,
                        'ui_local_changed': self.sender().objectName()}
            # logger.warning(f"ui2dict:emit {dict_sig}")
            self.emit(dict_sig)
        else:
            logger.error("Sender has no object name!")

    # --------------------------------------------------------------------------
    def dict2ui(self, q_dict=None):
        """
        Use the passed dict `q_dict` to update:

        * UI widgets `WI`, `WF` `quant` and `ovfl`
        * the instance quantization dict `self.q_dict` (usually a reference to some
          global quantization dict like `fb.fil[0]['fxqc']['QCB']`)
        * the `scale` setting of the instance quantization dict if WF / WI require this
        * the instance quantization object `self.QObj` from the instance quantization dict
        * overflow counters need to be updated from calling instance

        If `q_dict is None`, use data from the instance quantization dict `self.q_dict`
        instead.
        """

        if q_dict is None:
            q_dict = self.q_dict
        else:
            for k in q_dict:
                if k not in {'quant', 'quant_last', 'ovfl', 'WI', 'WF', 'qfrmt'}:
                    logger.warning(f"Unknown quantization option '{k}'")

        if 'qfrmt' in q_dict:
            err = False
            qfrmt = q_dict['qfrmt']
            if 'qfrmt_last' not in q_dict:
                q_dict['qfrmt_last'] = qfrmt

            # logger.warning(f"qfrmt = {q_dict['qfrmt']} (was: {q_dict['qfrmt_last']})")

            if qfrmt == 'qint':  # integer format
                if self.q_dict['qfrmt_last'] != 'qint':  # convert to int
                    self.q_dict.update({'WG': self.q_dict['WI'], 'WI': self.q_dict['WF'],
                                        'WF': 0, 'scale': 1 << self.q_dict['WF']})
            elif qfrmt == 'q31':  # Q0.31
                self.q_dict.update({'WG': 0, 'WI': 0, 'WF': 31, 'scale': 1})
            elif qfrmt == 'q15':  # Q0.15
                self.q_dict.update({'WG': 0, 'WI': 0, 'WF': 15, 'scale': 1})

            else:
                if self.q_dict['qfrmt_last'] == 'qint':  # convert from int
                    self.q_dict.update({'WF': self.q_dict['WI'], 'WI': self.q_dict['WG']})

                self.q_dict.update({'scale': 1, 'WG': 0})

                if qfrmt == 'qnfrac':  # normalized fractional format
                    self.q_dict.update({'WI': 0, 'WF': self.q_dict['W'] - 1})
                elif qfrmt in {'qfrac', 'float'}:
                    pass

                else:
                    logger.warning(f"Unknown quantization format '{qfrmt}'")
                    err = True

            if not err:
                self.ledWF.setEnabled(qfrmt in {'qnfrac', 'qfrac'})
                self.ledWF.setVisible(qfrmt != 'qint')
                self.ledWG.setVisible(qfrmt == 'qint')
                self.ledWG.setEnabled(True)
                self.lblPlus.setVisible(qfrmt == 'qint')
                self.lblDot.setVisible(qfrmt != 'qint')
                self.ledWI.setEnabled(qfrmt in {'qint', 'qfrac'})
                self.ledWG.setText(str(self.q_dict['WG']))
                self.ledWF.setText(str(self.q_dict['WF']))
                self.ledWI.setText(str(self.q_dict['WI']))

        q_dict['qfrmt_last'] = qfrmt  # store current setting

        if 'quant' in q_dict:
            qset_cmb_box(self.cmbQuant, q_dict['quant'])
            self.q_dict.update({'quant': qget_cmb_box(self.cmbQuant)})

        if 'ovfl' in q_dict:
            qset_cmb_box(self.cmbOvfl, q_dict['ovfl'])
            self.q_dict.update({'ovfl': qget_cmb_box(self.cmbOvfl)})

        if 'WG' in q_dict:
            WG = safe_eval(
                q_dict['WG'], self.QObj.q_dict['WG'], return_type="int", sign='poszero')
            self.ledWG.setText(str(WG))
            self.q_dict.update({'WG': WG})

        if 'WI' in q_dict:
            WI = safe_eval(
                q_dict['WI'], self.QObj.q_dict['WI'], return_type="int", sign='poszero')
            self.ledWI.setText(str(WI))
            self.q_dict.update({'WI': WI})

        if 'WF' in q_dict:
            WF = safe_eval(
                q_dict['WF'], self.QObj.q_dict['WF'], return_type="int", sign='poszero')
            self.ledWF.setText(str(WF))
            self.q_dict.update({'WF': WF})

        # logger.error(f"Bef: WG = {self.q_dict['WG']}, WI = {self.q_dict['WI']}, "
        #             f"WF = {self.q_dict['WF']}, W = {self.q_dict['W']}")

        self.q_dict.update(
            {'W': self.q_dict['WG'] + self.q_dict['WI'] + self.q_dict['WF'] + 1})

        self.QObj.set_qdict(self.q_dict)  # update instance q_dict
        # logger.error(f"Aft: WG = {self.q_dict['WG']}, WI = {self.q_dict['WI']}, "
        #              f"WF = {self.q_dict['WF']}, W = {self.q_dict['W']}")


# ==============================================================================
if __name__ == '__main__':
    """ Run widget standalone with `python -m pyfda.fixpoint_widgets.fx_ui_wq` """

    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)

    mainw = FX_UI_WQ({}, label='<b>Quantizer</b>', label_2="for the masses")
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
