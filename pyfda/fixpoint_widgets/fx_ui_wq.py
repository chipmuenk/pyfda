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

from numpy.lib.function_base import iterable

import pyfda.libs.pyfda_fix_lib as fx

from pyfda.libs.compat import (
    QWidget, QLabel, QLineEdit, QComboBox, QPushButton, QIcon, QSpacerItem,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, pyqtSignal, QColor)

from pyfda.libs.pyfda_qt_lib import (
    qcmb_box_populate, qget_cmb_box, qset_cmb_box, qstyle_widget)
# from pyfda.pyfda_rc import params
from pyfda.libs.pyfda_lib import qstr, safe_eval, to_html

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
            fb.fil[0]['fxqc']['QA'], wdg_name='wq_accu',
            label='<b>Accu Quantizer <i>Q<sub>A&nbsp;</sub></i>:</b>')
    ```

    All labels support HTML formatting.

    'wdg_name'      : 'fx_ui_wq'                # widget name, used to discern between
                                                # multiple instances
    'label'         : ''                        # widget text label, usually set by the
    'label_2'       : ''                        # instance, and part 2 (below part 1)

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

    'lock_vis'      : False                     # Pushbutton for locking visible
    'tip_lock'      : 'Sync input/output quant.'# Tooltip for  lock push button

    'cmb_w_vis'     : False                     # Integrated combo widget visible?
    'cmb_w_items'   : List with tooltip and combo box choices
    'cmb_w_init'    : 'man'                     # initial setting
    'count_ovfl_vis': True                      # Is overflow counter visible?
    """
    # incoming,
    # sig_rx = pyqtSignal(object)
    # outcgoing
    sig_tx = pyqtSignal(object)
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, q_dict: dict, **kwargs) -> None:
        super().__init__()

        self.q_dict = q_dict
        self._construct_UI(**kwargs)

    def _construct_UI(self, **kwargs):
        """ Construct widget """
        cmb_q = ["Select the kind of quantization.",
                 ("round", "Round",
                  "<span>Round towards nearest representable number</span>"),
                 ("fix", "Fix", "Round towards zero"),
                 ("floor", "Floor", "<span>Round towards negative infinity / "
                  "two's complement truncation.</span>")]
        cmb_ov = ["<span>Select overflow behaviour.</span>",
                  ("wrap", "Wrap", "Two's complement wrap around"),
                  ("sat", "Sat",
                   "<span>Saturation, i.e. limit at min. / max. value</span>")]
        cmb_w = ["<span>Set Accumulator word format</span>",
                 ("man", "Man", "<span>Manual entry of word format.</span>"),
                 ("auto", "Auto",
                  "<span>Automatic calculation from coefficients and input word formats "
                  "taking coefficients area into account.</span>"),
                 ("full", "Full",
                  "<span>Automatic calculation from coefficients and input word formats "
                  "for arbitrary coefficients.</span>")
                 ]
        # default widget settings:
        dict_ui = {'wdg_name': 'fx_ui_wq', 'label': '', 'label_2': '',
                   'label_q': 'Quant.', 'cmb_q_items': cmb_q, 'quant': 'round',
                   'label_ov': 'Ovfl.', 'cmb_ov_items': cmb_ov, 'ovfl': 'wrap',
                   'enabled': True, 'visible': True,
                   #
                   'label_w': '<i>WI.WF</i>&nbsp;:', 'lbl_sep': '.', 'max_led_width': 30,
                   'WI': 0, 'WI_len': 2, 'tip_WI': 'Number of integer bits',
                   'WF': 15, 'WF_len': 2, 'tip_WF': 'Number of fractional bits',
                   'fractional': True,
                   'cmb_w_vis': False, 'cmb_w_items': cmb_w, 'cmb_w_init': 'man',
                   'lock_vis': False, 'tip_lock': 'Sync input and output quantization.',
                   'count_ovfl_vis': True
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
        lbl_wdg_2 = QLabel(dict_ui['label_2'], self)

        self.cmbQuant = QComboBox(self)
        qcmb_box_populate(self.cmbQuant, dict_ui['cmb_q_items'], dict_ui['quant'])
        self.cmbQuant.setObjectName('quant')

        self.cmbOvfl = QComboBox(self)
        qcmb_box_populate(self.cmbOvfl, dict_ui['cmb_ov_items'], dict_ui['ovfl'])
        self.cmbOvfl.setObjectName('ovfl')

        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQuant.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbOvfl.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        lbl_W = QLabel(to_html(dict_ui['label_w']), self)

        self.cmbW = QComboBox(self)
        qcmb_box_populate(self.cmbW, dict_ui['cmb_w_items'], dict_ui['cmb_w_init'])
        self.cmbW.setVisible(dict_ui['cmb_w_vis'])
        self.cmbW.setObjectName("cmbW")

        self.butLock = QPushButton(self)
        self.butLock.setCheckable(True)
        self.butLock.setChecked(False)
        self.butLock.setVisible(dict_ui['lock_vis'])
        self.butLock.setToolTip(dict_ui['tip_lock'])
        self.butLock.setFixedWidth(self.butLock.height())

        lay_H_stretch = QHBoxLayout()
        lay_H_stretch.addStretch()

        self.ledWI = QLineEdit(self)
        self.ledWI.setToolTip(dict_ui['tip_WI'])
        self.ledWI.setMaxLength(dict_ui['WI_len'])  # maximum of 2 digits
        self.ledWI.setFixedWidth(dict_ui['max_led_width'])  # width of lineedit in points
        self.ledWI.setObjectName("WI")

        lblDot = QLabel(dict_ui['lbl_sep'], self)
        lblDot.setVisible(dict_ui['fractional'])

        self.ledWF = QLineEdit(self)
        self.ledWF.setToolTip(dict_ui['tip_WF'])
        self.ledWF.setMaxLength(dict_ui['WI_len'])  # maximum of 2 digits
        self.ledWF.setFixedWidth(dict_ui['max_led_width'])  # width of lineedit in points
        self.ledWF.setVisible(dict_ui['fractional'])
        self.ledWF.setObjectName("WF")

        self.lbl_ovfl_count = QLabel(to_html("N_ov = 0", frmt='i'))
        self.lbl_ovfl_count.setAutoFillBackground(True)
        self.lbl_ovfl_count.setVisible(dict_ui['count_ovfl_vis'])
        color = QColor(233, 10, 150)
        alpha = 140
        # values = "{r}, {g}, {b}, {a}".format(
        #     r=color.red(), g=color.green(), b=color.blue(), a=alpha)
        # self.lbl_ovfl_cntr.setStyleSheet("QLabel { background-color: rgba("+values+"); }")

        layH_W = QHBoxLayout()
        layH_W.addStretch()
        layH_W.addWidget(self.ledWI)
        layH_W.addWidget(lblDot)
        layH_W.addWidget(self.ledWF)
        layH_W.setContentsMargins(0, 0, 0, 0)

        layG = QGridLayout()
        # first row
        layG.addWidget(lbl_wdg, 0, 0)
        layG.addWidget(self.butLock, 0, 2)
        layG.addLayout(layH_W, 0, 3)
        layG.addWidget(self.cmbW, 0, 4)
        # second row
        layG.addWidget(self.lbl_ovfl_count, 1, 0)
        layG.addLayout(lay_H_stretch, 1, 1)
        layG.addWidget(self.cmbQuant, 1, 3)
        layG.addWidget(self.cmbOvfl, 1, 4)
        layG.setContentsMargins(0, 0, 0, 0)

        frmMain = QFrame(self)
        frmMain.setLayout(layG)

        layVMain = QVBoxLayout()  # Widget main layout
        layVMain.addWidget(frmMain)
        layVMain.setContentsMargins(0, 0, 0, 0)  # *params['wdg_margins'])

        self.setLayout(layVMain)

        # ----------------------------------------------------------------------
        # INITIAL SETTINGS OF UI AND FIXPOINT QUANTIZATION OBJECT
        # ----------------------------------------------------------------------
        WI = int(dict_ui['WI'])
        WF = int(dict_ui['WF'])
        W = WI + WF + 1
        self.ledWI.setText(str(WI))
        self.ledWF.setText(str(WF))
        ovfl = qget_cmb_box(self.cmbOvfl)
        quant = qget_cmb_box(self.cmbQuant)

        self.q_dict.update({'ovfl': ovfl, 'quant': quant, 'WI': WI, 'WF': WF, 'W': W})
        # create fixpoint quantization object from passed quantization dict
        self.QObj = fx.Fixed(self.q_dict)

        # initialize button icon
        self.butLock_clicked(self.butLock.isChecked())

        frmMain.setEnabled(dict_ui['enabled'])
        frmMain.setVisible(dict_ui['visible'])

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.cmbOvfl.currentIndexChanged.connect(self.ui2dict)
        self.cmbQuant.currentIndexChanged.connect(self.ui2dict)
        self.ledWI.editingFinished.connect(self.ui2dict)
        self.ledWF.editingFinished.connect(self.ui2dict)
        self.cmbW.currentIndexChanged.connect(self.ui2dict)

        self.butLock.clicked.connect(self.butLock_clicked)

    # --------------------------------------------------------------------------
    def quant_coeffs(self, coeffs: iterable) -> list:
        """
        Quantize the coefficients, scale and convert them to a list of integers,
        using the quantization settings of `self.q_dict`.

        This is called every time one of the coefficient subwidgets is edited
        or changed,that's why overflow counters are reset.

        Parameters
        ----------
        coeffs: iterable
           a list or ndarray of coefficients to be quantized

        Returns
        -------
        A list of integer coeffcients, quantized and scaled with the settings
        of the local quantization dict

        """
        self.QObj.frmt = 'dec'  # always use decimal format for coefficient quantization
        self.QObj.resetN()  # reset all overflow counters

        if coeffs is None:
            logger.error("Coeffs empty!")
        # quantize floating point coefficients with the selected scale (WI.WF),
        # next convert array float  -> array of fixp
        #                           -> list of int (scaled by 2^WF) when `to_int == True`
        if self.QObj.qfrmt == 'int':
            self.QObj.scale = 1 << self.QObj.WF
        return list(self.QObj.fixp(coeffs))
    # --------------------------------------------------------------------------

    def butLock_clicked(self, clicked):
        """
        Update the icon of the push button depending on its state
        """
        if clicked:
            self.butLock.setIcon(QIcon(':/lock-locked.svg'))
        else:
            self.butLock.setIcon(QIcon(':/lock-unlocked.svg'))

        # TODO: WTF?!
        q_icon_size = self.butLock.iconSize()  # <- uncomment this for manual sizing
        self.butLock.setIconSize(q_icon_size)

        dict_sig = {'wdg_name': self.wdg_name, 'ui': 'butLock'}
        self.emit(dict_sig)

    # --------------------------------------------------------------------------
    def ui2dict(self):
        """
        Update the entries in the quantization dict from the UI for `ovfl`, `quant`,
        `WI`, `WF`, `W` when one of the widgets has been edited.

        Emit a signal with `{'ui'<objectName of the sender>}`.
        """
        WI = int(safe_eval(self.ledWI.text(), self.QObj.WI, return_type="int",
                           sign='poszero'))
        self.ledWI.setText(str(WI))
        WF = int(safe_eval(self.ledWF.text(), self.QObj.WF, return_type="int",
                           sign='poszero'))
        self.ledWF.setText(str(WF))
        W = int(WI + WF + 1)

        ovfl = qget_cmb_box(self.cmbOvfl)
        quant = qget_cmb_box(self.cmbQuant)

        self.q_dict.update({'ovfl': ovfl, 'quant': quant, 'WI': WI, 'WF': WF, 'W': W})
        self.QObj.setQobj(self.q_dict)

        if self.sender():
            obj_name = self.sender().objectName()
            dict_sig = {'wdg_name': self.wdg_name, 'ui': obj_name}
            self.emit(dict_sig)
        else:
            logger.error("Sender has no object name!")

    # --------------------------------------------------------------------------
    def dict2ui(self, q_dict=None):
        """
        Use the passed dict `q_dict` to update

        * UI widgets `WI`, `WF` `quant` and `ovfl`
        * the instance quantization dict `self.q_dict` (usually a reference to some
          global quantization dict like `fb.fil[0]['fxqc']['QCB']`)
        * the `scale` setting of the instance quantization dict if WF / WI require this
        * the instance quantization object `self.QObj` from the instance quantization dict

        If `q_dict is None`, use data from the instance quantization dict `self.q_dict`
        instead.
        """

        if q_dict is None:
            q_dict = self.q_dict
        else:
            for k in q_dict:
                if k not in {'quant', 'ovfl', 'WI', 'WF', 'qfrmt'}:
                    logger.warning(f"Unknown quantization option '{k}'")

        if 'qfrmt' in q_dict:
            err = False
            qfrmt = q_dict['qfrmt']

            if qfrmt == 'qint':  # integer format
                self.q_dict.update({'WI': self.q_dict['WI'] + self.q_dict['WF'], 'WF': 0,
                                   'scale': 1 << (self.q_dict['WI'] + self.q_dict['WF'])})
            elif qfrmt == 'qnfrac':  # normalized fractional format
                self.q_dict.update({'WF': self.q_dict['WI'] + self.q_dict['WF'], 'WI': 0,
                                    'scale': 1})
            elif qfrmt in {'qfrac', 'float'}:
                self.q_dict.update({'scale': 1})
            elif qfrmt == 'q31':
                self.q_dict.update({'WI': 0, 'WF': 31, 'scale': 1})
            else:
                logger.warning(f"Unknown quantization format '{qfrmt}'")
                err = True

            if not err:
                self.ledWF.setEnabled(qfrmt in {'qnfrac', 'qfrac'})
                self.ledWI.setEnabled(qfrmt in {'qint', 'qfrac'})
                self.ledWF.setText(str(self.q_dict['WF']))
                self.ledWI.setText(str(self.q_dict['WI']))
                self.q_dict.update({'qfrmt': qfrmt})

        if 'quant' in q_dict:
            qset_cmb_box(self.cmbQuant, q_dict['quant'])
            self.q_dict.update({'quant': qget_cmb_box(self.cmbQuant)})

        if 'ovfl' in q_dict:
            qset_cmb_box(self.cmbOvfl, q_dict['ovfl'])
            self.q_dict.update({'ovfl': qget_cmb_box(self.cmbOvfl)})

        if 'WI' in q_dict:
            WI = safe_eval(q_dict['WI'], self.QObj.WI, return_type="int", sign='poszero')
            self.ledWI.setText(str(WI))
            self.q_dict.update({'WI': WI})

        if 'WF' in q_dict:
            WF = safe_eval(q_dict['WF'], self.QObj.WF, return_type="int", sign='poszero')
            self.ledWF.setText(str(WF))
            self.q_dict.update({'WF': WF})

        if self.lbl_ovfl_count.isVisible():
            self.lbl_ovfl_count.setText(
                to_html("<i>N_ov</i> = {0}".format(self.QObj.N_over)))
            if self.QObj.N_over == 0:
                qstyle_widget(self.lbl_ovfl_count, "normal")
            else:
                qstyle_widget(self.lbl_ovfl_count, "changed")

        self.q_dict.update({'W': self.q_dict['WI'] + self.q_dict['WF'] + 1})
        self.QObj.setQobj(self.q_dict)


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
