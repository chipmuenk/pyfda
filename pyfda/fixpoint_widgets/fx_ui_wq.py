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

import pyfda.filterbroker as fb
from pyfda.libs.tree_builder import merge_dicts_hierarchically
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
    Subwidget for selecting and displaying quantization / overflow options.

    A quantization dictionary `q_dict` is passed to the constructor.
    This can be a global quantization dict like `fb.fil[0]['fxqc']['QCB']` or a local
    dict.

    This widget allows the user to modify the values for the following keys:

    - `quant`   : quantization behaviour
    - `ovfl`    : overflow behaviour
    - `WI`      : number of integer bits
    - `WF`      : number of fractional bits
    - `w_a_m`   : automatic or manual update of word format

    These quantization settings are also stored in the instance quantizer object
    `self.QObj`.

    Widget (UI) settings are stored in the local `ui_dict` dictionary with the keys and
    their default settings described below. When instantiating the widget, these settings
    can be modified by corresponding keyword parameters, e.g.

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

    'label_ov'      : 'Ovfl.'                   # subwidget text label
    'cmb_ov'        : List with tooltip and combo box choices (default: 'wrap', 'sat')

    'fractional'    : True                      # Display WF, otherwise WF=0
    'lbl_sep'       : '.'                       # label between WI and WF field
    'max_led_width' : 30                        # max. length of lineedit field
    'WI_len'        : 2                         # max. number of integer *digits*
    'tip_WI'        : 'Number of integer bits'  # Mouse-over tooltip
    'WF_len'        : 2                         # max. number of frac. *digits*
    'tip_WF'        : 'Number of frac. bits'    # Mouse-over tooltip

    'lock_vis'      : 'off''                    # Pushbutton for locking visible
    'tip_lock'      : 'Sync input/output quant.'# Tooltip for  lock push button

    'cmb_w_vis'     : 'off'                     # Is Auto/Man. selection visible?
                                                #  ['a', 'm', 'f']
    'cmb_w_items'   : List with tooltip and combo box choices
    'count_ovfl_vis': 'on'                      # Is overflow counter visible?
                                                #   ['on', 'off', 'auto']
    'MSB_LSB_vis'   : 'off'                     # Are MSB / LSB settings visible?
    """
    # sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outcgoing
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, q_dict: dict, objectName='fx_ui_wq_inst', **kwargs) -> None:
        super().__init__()

        self.setObjectName(objectName)
        # default settings for q_dict
        q_dict_default = {'WI': 0, 'WF': 15, 'w_a_m': 'm', 'quant': 'round',
                          'ovfl': 'sat', 'wdg_name': 'unknown'}
        # merge 'q_dict_default' into 'q_dict', prioritizing 'q_dict' entries
        merge_dicts_hierarchically(q_dict, q_dict_default)
        self.q_dict = q_dict

        self._construct_UI(**kwargs)

    # This is not needed, it is called from one level above
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
        cmb_w = ["<span>Select word format manually / automatically</span>",
                ("m", "M", "<span><b>Manual</b> entry of integer and fractional "
                "word length.</span>"),
                ("a", "A", "<span><b>Automatic</b> estimation of required integer "
                 "and fractional word length.</span>")                 ]
        # default widget settings:
        ui_dict = {'wdg_name': 'fx_ui_wq', 'label': '',
                   'label_q': 'Quant.', 'cmb_q_items': cmb_q,
                   'label_ov': 'Ovfl.', 'cmb_ov_items': cmb_ov,
                   #
                   'lbl_sep': '.', 'max_led_width': 30,
                   'WI_len': 2, 'tip_WI': 'Number of integer bits',
                   'WF_len': 2, 'tip_WF': 'Number of fractional bits',
                   'fractional': True,
                   'cmb_w_vis': 'on', 'cmb_w_items': cmb_w,
                   'lock_vis': 'off',
                   'tip_lock':
                       '<span>Sync input and output quantization formats.</span>',
                   'count_ovfl_vis': 'auto', 'MSB_LSB_vis': 'off'
                   }

        # update local `ui_dict` with keyword arguments passed during construction
        for key, val in kwargs.items():
            if key not in ui_dict:
                logger.warning(f"Unknown key '{key}'")
            else:
                ui_dict.update({key: val})
        # ui_dict.update(map(kwargs)) # same as above?

        self.wdg_name = ui_dict['wdg_name']
        lbl_wdg = QLabel(ui_dict['label'], self)

        self.cmbQuant = QComboBox(self, objectName='quant')
        idx = qcmb_box_populate(self.cmbQuant, ui_dict['cmb_q_items'], self.q_dict['quant'])
        if idx == -1:
            logger.warning(
                f"""Initialization value "{self.q_dict['quant']}" was not found in """
                f"""'quant' combo box.""")

        self.cmbOvfl = QComboBox(self, objectName='ovfl')
        idx = qcmb_box_populate(self.cmbOvfl, ui_dict['cmb_ov_items'], self.q_dict['ovfl'])
        if idx == -1:
            logger.warning(
                f"""Initialization value "{self.q_dict['ovfl']}" was not found in """
                f"""'ovfl' combo box.""")

        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQuant.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbOvfl.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.cmbW = QComboBox(self, objectName="cmbW")
        idx = qcmb_box_populate(self.cmbW, ui_dict['cmb_w_items'], self.q_dict['w_a_m'])
        if idx == -1:
            logger.warning(
                f"""Initialization value "{self.q_dict['w_a_m']}" was not found in """
                f"""'auto/man' combo box.""")
        self.cmbW.setVisible(ui_dict['cmb_w_vis'] == 'on')

        self.butLock = QPushButton(self)
        self.butLock.setCheckable(True)
        self.butLock.setChecked(False)
        self.butLock.setVisible(ui_dict['lock_vis'] == 'on')
        self.butLock.setToolTip(ui_dict['tip_lock'])
        self.butLock.setFixedWidth(self.butLock.height())
        # retain size of lock widget even when hidden
        sp_retain = self.butLock.sizePolicy()
        sp_retain.setRetainSizeWhenHidden(True)
        self.butLock.setSizePolicy(sp_retain)

        self.ledWI = QLineEdit(self, objectName="WI")
        self.ledWI.setToolTip(ui_dict['tip_WI'])
        self.ledWI.setMaxLength(ui_dict['WI_len'])  # maximum of 2 digits
        self.ledWI.setFixedWidth(ui_dict['max_led_width'])  # width of lineedit in points

        self.lbl_sep1 = QLabel(to_html(ui_dict['lbl_sep'], frmt='b'), self)
        self.lbl_sep1.setVisible(ui_dict['fractional'])
        self.lbl_sep2 = QLabel(to_html(')', frmt='b'), self)
        self.lbl_sep2.setVisible(False)

        self.ledWF = QLineEdit(self, objectName="WF")
        self.ledWF.setToolTip(ui_dict['tip_WF'])
        self.ledWF.setMaxLength(ui_dict['WI_len'])  # maximum of 2 digits
        self.ledWF.setFixedWidth(ui_dict['max_led_width'])  # width of lineedit in points
        self.ledWF.setVisible(ui_dict['fractional'])

        self.count_ovfl_vis = ui_dict['count_ovfl_vis']
        self.lbl_ovfl_count = QLabel(to_html("N_ov = 0"))
        self.lbl_ovfl_count.setAutoFillBackground(True)

        self.MSB_LSB_vis = ui_dict['MSB_LSB_vis']

        # -------------------------------------------------------------------
        # MSB / LSB size
        # ---------------------------------------------------------------------
        self.lbl_MSB = QLabel(self)
        self.lbl_MSB.setText("undefined")

        self.lbl_LSB = QLabel(self)
        self.lbl_LSB.setText("undefined")

        layH_W = QHBoxLayout()
        layH_W.addWidget(self.ledWI)
        layH_W.addWidget(self.lbl_sep1)
        layH_W.addWidget(self.ledWF)
        layH_W.addWidget(self.lbl_sep2)
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
        WI = int(self.q_dict['WI'])
        WF = int(self.q_dict['WF'])
        W = WI + WF + 1
        self.ledWI.setText(str(WI))
        self.ledWF.setText(str(WF))

        self.q_dict.update({'ovfl': qget_cmb_box(self.cmbOvfl),
                            'quant': qget_cmb_box(self.cmbQuant),
                            'w_a_m': qget_cmb_box(self.cmbW),
                            'WI': WI, 'WF': WF})
        # create fixpoint quantization object from passed quantization dict
        self.QObj = fx.Fixed(self.q_dict)

        # initialize button icon
        self.but_lock_update_icon(self.butLock.isChecked())

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS
        # ----------------------------------------------------------------------
        # self.sig_rx.connect(self.process_sig_rx)
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.cmbOvfl.currentIndexChanged.connect(self.ui2dict)
        self.cmbQuant.currentIndexChanged.connect(self.ui2dict)
        self.ledWI.editingFinished.connect(self.ui2dict)
        self.ledWF.editingFinished.connect(self.ui2dict)
        self.cmbW.currentIndexChanged.connect(self.ui2dict)

        self.butLock.clicked.connect(self.but_lock_checked)

        # initialize the UI from the quantization and the global dictionary
        self.dict2ui()
        # initialize overflow counter and MSB / LSB display
        self.update_ovfl_cnt()

    # --------------------------------------------------------------------------
    def but_lock_checked(self, checked: bool) -> None:
        """
        Update the icon of the push button depending on its state (checked or not)
        and fire the signal {'ui_local_changed': 'butLock'}
        """
        self.but_lock_update_icon(checked)
        self.emit({'ui_local_changed': 'butLock'})

    # --------------------------------------------------------------------------
    def but_lock_update_icon(self, checked: bool) -> None:
        """
        Update the icon of the push button depending on its state
        """
        if checked:
            self.butLock.setIcon(QIcon(':/lock-locked.svg'))
        else:
            self.butLock.setIcon(QIcon(':/lock-unlocked.svg'))
        return

    # --------------------------------------------------------------------------
    def update_ovfl_cnt(self):
        """
        Update the overflow counter and MSB / LSB display (if visible)
        """
        # -------
        # frm = inspect.stack()[1]
        # logger.warning(f"update: {id(self)}|{id(self.q_dict)} | {self.wdg_name} :"
        #              f"{self.q_dict['N_over']} "
        #              f"{inspect.getmodule(frm[0]).__name__.split('.')[-1]}."
        #              f"{frm[3]}:{frm[2]}")

        if self.count_ovfl_vis == 'off':
            self.lbl_ovfl_count.setVisible(False)
        elif self.count_ovfl_vis == 'auto' and self.q_dict['N_over'] == 0:
            self.lbl_ovfl_count.setVisible(False)
        elif self.count_ovfl_vis == 'on' or\
                self.count_ovfl_vis == 'auto' and self.q_dict['N_over'] > 0:

            self.lbl_ovfl_count.setVisible(True)
            self.lbl_ovfl_count.setText(
                to_html(f"<b><i>&nbsp;&nbsp;N_ov </i>= {self.q_dict['N_over']}</b>"))
            if self.q_dict['N_over'] == 0:
                qstyle_widget(self.lbl_ovfl_count, "normal")
            else:
                qstyle_widget(self.lbl_ovfl_count, "failed")
        else:
            logger.error(f"Unknown option count_ovfl_vis = '{self.count_ovfl_vis}'")
        return

    # --------------------------------------------------------------------------
    def ui2dict(self) -> None:
        """
        Update the quantization dict `self.q_dict` (usually a reference to a part of a
        global quantization dict like `self.q_dict = fb.fil[0]['fxqc']['QCB']`)
        and the quantization object `self.QObj` from the UI.

        These are the subwidgets for `ovfl`, `quant`, `WI`, `WF` which also
        trigger this method when edited.

        Emit a signal with `{'ui_local_changed': <objectName of the sender>}`.
        """
        WF = int(safe_eval(self.ledWF.text(), self.QObj.q_dict['WF'], return_type="int",
                           sign='poszero'))
        self.ledWF.setText(str(WF))

        WI = int(safe_eval(self.ledWI.text(), self.QObj.q_dict['WI'] + WF + 1, return_type="int",
                           sign='poszero'))
        if fb.fil[0]['qfrmt'] == 'qint':
            if WI <= WF:
                logger.warning(f"Total word length has to be larger than Fractional scaling WF = {WF}!")
                WI = self.QObj.q_dict['WI'] + WF + 1

        self.ledWI.setText(str(WI))

        # In 'qint' mode, the WI field shows the total word lenghth W. Nevertheless, the value
        # for 'WI' is stored in the dicts.
        if fb.fil[0]['qfrmt'] == 'qint':
            WI = WI - WF - 1

        ovfl = qget_cmb_box(self.cmbOvfl)
        quant = qget_cmb_box(self.cmbQuant)
        w_a_m = qget_cmb_box(self.cmbW)
        if not w_a_m in {'m', 'a', 'f'}:
            logger.error(f"Unknown option '{w_a_m}' for cmbW combobox!")

        self.q_dict.update({'ovfl': ovfl, 'quant': quant, 'WI': WI, 'WF': WF, 'w_a_m': w_a_m})
        self.QObj.set_qdict(self.q_dict)  # set quant. object, update derived quantities
                                          # like W and Q and reset counters

        self.update_WI_WF()
        logger.error(f"ui2dict: WI = {WI} {self.QObj.q_dict['WI']} - {self.q_dict['WI']}")
        if self.sender():
            # logger.error(f"sender = {self.sender().objectName()}")
#             if self.sender().objectName() == 'cmbW':
#                self.enable_subwidgets()  # enable / disable WI and WF subwidgets
            dict_sig = {'sender_name': self.wdg_name,
                        'ui_local_changed': self.sender().objectName()}
            self.emit(dict_sig)
        else:
            logger.error("Sender has no object name!")

    # --------------------------------------------------------------------------
    def dict2ui(self, q_dict: dict = None) -> None:
        """
        Use the passed quantization dict `q_dict` to update:

        * UI subwidgets `WI`, `WF` `quant`, `ovfl`, `cmbW`
        * the instance quantization dict `self.q_dict` (usually a reference to some
          global quantization dict like `self.q_dict = fb.fil[0]['fxqc']['QCB']`)
        * the instance quantization object `self.QObj` from the instance quantization dict
        * overflow counters need to be updated from calling instance

        If `q_dict is None`, use data from the instance quantization dict `self.q_dict`
        instead, this can be used to update the UI.
        """
        if q_dict is None:
            q_dict = self.QObj.q_dict  # update UI from quantizer qdict
        else:
            for k in q_dict:
                if k not in {'wdg_name', 'quant', 'ovfl', 'WI', 'WF',
                             'w_a_m', 'N_over'}:
                    logger.warning(f"Unknown quantization dict key '{k}'")

        # Update all non-numeric instance quantization dict entries from passed `q_dict`
        # Auto-calculation of integer bits etc. needs to performed in parent subwidget!
        if 'w_a_m' in q_dict:
            i = qset_cmb_box(self.cmbW, q_dict['w_a_m'])
            if i < 0:
                logger.error(f"Unknown value q_dict['w_a_m'] = {q_dict['w_a_m']}")

        if 'quant' in q_dict:
            qset_cmb_box(self.cmbQuant, q_dict['quant'])
            if i < 0:
                logger.error(f"Unknown value q_dict['quant'] = {q_dict['quant']}")
            # q_dict.update({'quant': qget_cmb_box(self.cmbQuant)})

        if 'ovfl' in q_dict:
            qset_cmb_box(self.cmbOvfl, q_dict['ovfl'])
            if i < 0:
                logger.error(f"Unknown value q_dict['ovfl'] = {q_dict['ovfl']}")
            # q_dict.update({'ovfl': qget_cmb_box(self.cmbOvfl)})

        if fb.fil[0]['qfrmt'] not in {'qfrac', 'qint'}:
            logger.error(f"Unknown quantization format '{fb.fil[0]['qfrmt']}'")

        WI = safe_eval(
            q_dict['WI'], self.QObj.q_dict['WI'], return_type="int", sign='poszero')
        # q_dict.update({'WI': WI})

        self.ledWI.setText(str(WI))

        WF = safe_eval(
            q_dict['WF'], self.QObj.q_dict['WF'], return_type="int", sign='poszero')
        self.ledWF.setText(str(WF))
        # q_dict.update({'WF': WF})

        self.QObj.set_qdict(q_dict)  # update quantization object and derived parameters

        self.update_WI_WF()  # set WI / WF widgets visibility depending on 'w_a_m'
        logger.error(f"dict2ui: WI = {WI} {self.QObj.q_dict['WI']} - {q_dict['WI']}")

    # --------------------------------------------------------------------------
    def update_WI_WF(self):
        """
        Update display, visibility / writability of integer and fractional part of the
        quantization format. depending on `fb.fil[0]['fx_sim']` ...['qfrmt'] and
        ...['w_a_m'] settings
        """
        self.ledWI.setVisible(fb.fil[0]['fx_sim'])
        self.ledWF.setVisible(fb.fil[0]['fx_sim'])

        if not fb.fil[0]['fx_sim']:
            self.lbl_sep1.setText(to_html("---", frmt='b'))
            self.lbl_sep2.setVisible(False)
        elif fb.fil[0]['qfrmt'] == 'qint':
            self.lbl_sep1.setText(to_html("(", frmt='b'))
            self.ledWF.setToolTip("Scale factor 2<sup>-WF</sup>")
            self.ledWI.setText(str(self.q_dict['WI'] + self.q_dict['WF'] + 1))
            self.ledWI.setToolTip("Total number of bits")
            self.lbl_sep2.setVisible(True)

            LSB = 1.
            MSB = 2. ** (self.q_dict['WI'] + self.q_dict['WF'] - 1)
        elif fb.fil[0]['qfrmt'] == "qfrac":
            self.lbl_sep1.setText(to_html(".", frmt='b'))
            self.ledWF.setToolTip("Number of fractional bits")
            self.ledWI.setText(str(self.q_dict['WI']))
            self.ledWI.setToolTip("Number of integer bits")
            self.lbl_sep2.setVisible(False)

            LSB = 2 ** -self.q_dict['WF']
            MSB = 2. ** (self.q_dict['WI'] - 1)
        else:
            logger.error(f"Unknown quantization format '{fb.fil[0]['qfrmt']}'!")

        self.ledWF.setText(str(self.q_dict['WF']))


        if self.MSB_LSB_vis == 'off' or not fb.fil[0]['fx_sim']:
            # Don't show any data
            self.lbl_MSB.setVisible(False)
            self.lbl_LSB.setVisible(False)
        elif self.MSB_LSB_vis == 'max':
            # Show MAX and LSB data
            self.lbl_MSB.setVisible(True)
            self.lbl_LSB.setVisible(True)
            self.lbl_MSB.setText(
                "<b><i>&nbsp;&nbsp;Max</i><sub>10</sub> = </b>"
                f"{2. * MSB - LSB:.{params['FMT_ba']}g}")
            self.lbl_LSB.setText(
                f"<b><i>LSB</i><sub>10</sub> = </b>{LSB:.{params['FMT_ba']}g}")
        elif self.MSB_LSB_vis == 'msb':
            # Show MSB and LSB data
            self.lbl_MSB.setVisible(True)
            self.lbl_LSB.setVisible(True)
            self.lbl_MSB.setText(
                "<b><i>&nbsp;&nbsp;MSB</i><sub>10</sub> = </b>"
                f"{MSB:.{params['FMT_ba']}g}")
            self.lbl_LSB.setText(
                f"<b><i>LSB</i><sub>10</sub> = </b>{LSB:.{params['FMT_ba']}g}")
        else:
            logger.error(f"Unknown option MSB_LSB_vis = '{self.MSB_LSB_vis}'")

        self.enable_subwidgets()

    # --------------------------------------------------------------------------
    def enable_subwidgets(self):
        """
        Enable integer and fractional part of the quantization format, depending on 'qfrmt'
        and 'w_a_m' settings.
        """
        self.ledWI.setEnabled(self.q_dict['w_a_m'] == 'm')
        self.ledWF.setEnabled(self.q_dict['w_a_m'] == 'm')
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
