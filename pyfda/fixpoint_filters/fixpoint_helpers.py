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
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
import logging
logger = logging.getLogger(__name__)

import pyfda.filterbroker as fb
import pyfda.pyfda_fix_lib as fix

from ..compat import (QWidget, QLabel, QLineEdit, QComboBox,
                      QVBoxLayout, QHBoxLayout, QFrame)

from pyfda.pyfda_qt_lib import qstr, qget_cmb_box
from pyfda.pyfda_rc import params
from pyfda.pyfda_lib import safe_eval, to_html


def build_coeff_dict(frmt=None):
    """
    Read and quantize the coefficients and return them as a dictionary

    Parameters:
    -----------
    frmt: string

    One of the following options: 'dec' (default), 'hex', 'bin', 'csd'

    Returns:
    --------
    A dictionary with the followig keys and values:

        - WI: integer

        - WF: integer

        - scale:

        - frmt:

        - f_fix: np.array

        - a_fix: np.array

    """
    b = fb.fil[0]['ba'][0]
    a = fb.fil[0]['ba'][1]
    # update the coefficient quantizer object
    Q_coeff = fix.Fixed(fb.fil[0]["q_coeff"])
    Q_coeff.setQobj(fb.fil[0]['q_coeff'])
    if not frmt:
        Q_coeff.frmt = 'dec' # use decimal format for coefficients by default
    else:
        Q_coeff.frmt = frmt # use the function argument

    # quantize floating point coefficients and converts them to the
    # selected numeric format (hex, bin, dec ...)
    c_dict = {}
    c_dict.update({'b':list(Q_coeff.float2frmt(b))})
    c_dict.update({'a':list(Q_coeff.float2frmt(a))})
    c_dict.update({'WF':Q_coeff.WF})
    c_dict.update({'WI':Q_coeff.WI})
    c_dict.update({'scale':Q_coeff.scale})
    c_dict.update({'frmt':Q_coeff.frmt})

    return c_dict

#------------------------------------------------------------------------------
class UI_WI_WF(QWidget):
    """
    Widget for entering integer and fractional bits. The result can be read out
    via the attributes `self.WI` and `self.WF`.
    """

    def __init__(self, parent, **kwargs):
        super(UI_WI_WF, self).__init__(parent)
        self._construct_UI(**kwargs)

    def _construct_UI(self, **kwargs):
        """ Construct widget """

        dict_ui = {'label':'WI.WF', 'max_led_width':30,
                   'WI':0, 'WI_len':2, 'tip_WI':'Number of integer bits',
                   'WF':15,'WF_len':2, 'tip_WF':'Number of fractional bits',
                   'enabled':True, 'visible':True
                   }
        for key, val in kwargs.items():
            dict_ui.update({key:val})
        # dict_ui.update(map(kwargs)) # same as above?
        self.WI = dict_ui['WI']
        self.WF = dict_ui['WF']

        lblW = QLabel(to_html(dict_ui['label'], frmt='bi'), self)
        self.ledWI = QLineEdit(self)
        self.ledWI.setToolTip(dict_ui['tip_WI'])
        self.ledWI.setMaxLength(dict_ui['WI_len']) # maximum of 2 digits
        self.ledWI.setFixedWidth(dict_ui['max_led_width']) # width of lineedit in points(?)

        lblDot = QLabel(".", self)

        self.ledWF = QLineEdit(self)
        self.ledWF.setToolTip(dict_ui['tip_WF'])
        self.ledWF.setMaxLength(dict_ui['WI_len']) # maximum of 2 digits
        self.ledWF.setFixedWidth(dict_ui['max_led_width']) # width of lineedit in points(?)

        layH = QHBoxLayout()
        layH.addWidget(lblW)
        layH.addStretch()
        layH.addWidget(self.ledWI)
        layH.addWidget(lblDot)
        layH.addWidget(self.ledWF)
        layH.setContentsMargins(0,0,0,0)

        frmMain = QFrame(self)
        frmMain.setLayout(layH)

        layVMain = QVBoxLayout() # Widget main layout
        layVMain.addWidget(frmMain)
        layVMain.setContentsMargins(0,5,0,0)#*params['wdg_margins'])

        self.setLayout(layVMain)
        
        #----------------------------------------------------------------------
        # INITIAL SETTINGS
        #----------------------------------------------------------------------
        self.ledWI.setText(qstr(dict_ui['WI']))
        self.ledWF.setText(qstr(dict_ui['WF']))

        frmMain.setEnabled(dict_ui['enabled'])
        frmMain.setVisible(dict_ui['visible'])

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.ledWI.editingFinished.connect(self._update_ui)
        self.ledWF.editingFinished.connect(self._update_ui)

    #--------------------------------------------------------------------------
    def _update_ui(self):
        """ Update the attributes `self.WI` and `self.WF` """
        self.WI = safe_eval(self.ledWI.text(), self.WI, return_type="int", sign='pos')
        self.ledWI.setText(qstr(self.WI))
        self.WF = safe_eval(self.ledWF.text(), self.WF, return_type="int", sign='pos')
        self.ledWF.setText(qstr(self.WF))

#------------------------------------------------------------------------------
class UI_WI_WF_coeffs(UI_WI_WF):
    """
    Widget for entering word format (integer and fractional bits) for the 
    oefficients. The result can be read out via the attributes `self.WI` and 
    `self.WF`.
    """
    def __init__(self, parent, **kwargs):
        super(UI_WI_WF_coeffs, self).__init__(parent)
        self._construct_UI(**kwargs)
        
    def update(self):
        self.c_dict = build_coeff_dict()
        
#==============================================================================

class UI_Q_Ovfl(QWidget):
    """
    Widget for selecting quantization / overflow options. The result can be read out
    via the attributes `self.x` and `self.y`.
    """

    def __init__(self, parent, **kwargs):
        super(UI_Q_Ovfl, self).__init__(parent)
        self._construct_UI(**kwargs)

    def _construct_UI(self, **kwargs):
        """ Construct widget """

        dict_ui = {'label_q':'Quant.', 'tip_q':'Select the kind of quantization.',
                   'cmb_q':['round', 'fix', 'floor'],
                   'label_ov':'Ovfl.', 'tip_ov':'Select overflow behaviour.',
                   'cmb_ov':['wrap', 'sat'],
                   'enabled':True, 'visible':True
                   }
        for key, val in kwargs.items():
            dict_ui.update({key:val})
        # dict_ui.update(map(kwargs)) # same as above?

        lblQuant = QLabel(dict_ui['label_q'], self)
        self.cmbQuant = QComboBox(self)
        self.cmbQuant.addItems(dict_ui['cmb_q'])
        self.cmbQuant.setToolTip(dict_ui['tip_q'])

        lblOvfl = QLabel(dict_ui['label_ov'], self)
        self.cmbOvfl = QComboBox(self)
        self.cmbOvfl.addItems(dict_ui['cmb_ov'])
        self.cmbOvfl.setToolTip(dict_ui['tip_ov'])

        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQuant.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbOvfl.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        layH = QHBoxLayout()
        layH.addWidget(lblOvfl)
        layH.addWidget(self.cmbOvfl)
        layH.addStretch()
        layH.addWidget(lblQuant)
        layH.addWidget(self.cmbQuant)
        layH.setContentsMargins(0,0,0,0)

        frmMain = QFrame(self)
        frmMain.setLayout(layH)

        layVMain = QVBoxLayout() # Widget main layout
        layVMain.addWidget(frmMain)
        layVMain.setContentsMargins(5,0,0,0)#*params['wdg_margins'])

        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # INITIAL SETTINGS
        #----------------------------------------------------------------------
        self.ovfl = qget_cmb_box(self.cmbOvfl, data=False)
        self.quant = qget_cmb_box(self.cmbQuant, data=False)
        
        frmMain.setEnabled(dict_ui['enabled'])
        frmMain.setVisible(dict_ui['visible'])

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.cmbOvfl.currentIndexChanged.connect(self._update_ui)
        self.cmbQuant.currentIndexChanged.connect(self._update_ui)

    #--------------------------------------------------------------------------
    def _update_ui(self):
        """ Update the attributes `self.ovfl` and `self.quant` """
        self.ovfl = self.cmbOvfl.currentText()
        self.quant = self.cmbQuant.currentText()

#==============================================================================

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = UI_WI_WF(None)
    mainw.show()

    app.exec_()