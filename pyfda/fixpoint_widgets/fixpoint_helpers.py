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
import numpy as np
import pyfda.filterbroker as fb
import pyfda.pyfda_fix_lib as fix

from ..compat import (QWidget, QLabel, QLineEdit, QComboBox,
                      QVBoxLayout, QHBoxLayout, QFrame)

from pyfda.pyfda_qt_lib import qget_cmb_box, qset_cmb_box
from pyfda.pyfda_rc import params
from pyfda.pyfda_lib import qstr, safe_eval, to_html


def build_coeff_dict(frmt=None):
    """
    Read and quantize the coefficients and return them as a dictionary.
    
    This is called every time one of the coefficient subwidgets is edited or changed.

    Parameters:
    -----------
    frmt: string

    One of the following options: 'dec' (default), 'hex', 'bin', 'csd'

    Returns:
    --------
    A dictionary with the followig keys and values:

        - WI: integer

        - WF: integer

        - scale: float

        - frmt: string

        - f_fix: np.array

        - a_fix: np.array

    """
    bf = fb.fil[0]['ba'][0] # get coefficients from 
    af = fb.fil[0]['ba'][1] # filter dict in float form
    # Create a coefficient quantizer instance using the quantization parameters dict
    # collected in `input_widgets/input_coeffs.py` (and stored in the central filter dict)
    Q_coeff = fix.Fixed(fb.fil[0]["q_coeff"])
    #Q_coeff.setQobj(fb.fil[0]['q_coeff']) # alternative: explicitly call setter
    if not frmt:
        Q_coeff.frmt = 'dec' # use decimal format for coefficients by default
    else:
        Q_coeff.frmt = frmt # use the function argument

    # quantize floating point coefficients and convert them to the
    # selected numeric format (hex, bin, dec ...) with the selected scale (WI.WF)
    c_dict = {}
    # convert list of float -> dec (np.int64).
    # item() converts np.int64 -> int 
    c_dict.update({'b':[b.item() for b in Q_coeff.float2frmt(bf)]}) # convert float -> fixp and
    c_dict.update({'a':[a.item() for a in Q_coeff.float2frmt(af)]}) # format it as bin, hex, ...
    c_dict.update({'WF':Q_coeff.WF}) # read parameters from quantizer instance
    c_dict.update({'WI':Q_coeff.WI}) # and pass them to the coefficient dict
    c_dict.update({'W':Q_coeff.W})
    c_dict.update({'scale':Q_coeff.scale}) # for later use 
    c_dict.update({'frmt':Q_coeff.frmt})

    return c_dict

#------------------------------------------------------------------------------
class UI_W(QWidget):
    """
    Widget for entering integer and fractional bits. The result can be read out
    via the attributes `self.WI`, `self.WF` and `self.W`.
    
    The constructor accepts a dictionary for initial widget settings.
    The following keys are defined; default values are used for missing keys:

    'label'         : 'WI.WF'                   # widget label
    'lbl_sep'       : '.'                       # label between WI and WF field
    'max_led_width' : 30                        # max. length of lineedit field
    'WI'            : 0                         # number of frac. *bits*                
    'WI_len'        : 2                         # max. number of integer *digits*
    'tip_WI'        : 'Number of integer bits'  # Mouse-over tooltip
    'WF'            : 15                        # number of frac. *bits*
    'WF_len'        : 2                         # max. number of frac. *digits*
    'tip_WF'        : 'Number of frac. bits'    # Mouse-over tooltip
    'enabled'       : True                      # Is widget enabled?
    'visible'       : True                      # Is widget visible?
    'fractional'    : True                      # Display WF, otherwise WF=0
    """

    def __init__(self, parent, **kwargs):
        super(UI_W, self).__init__(parent)
        self._construct_UI(**kwargs)
        self.ui2dict()

    def _construct_UI(self, **kwargs):
        """ Construct widget from default settings, """

        # default settings
        dict_ui = {'label':'WI.WF', 'lbl_sep':'.', 'max_led_width':30,
                   'WI':0, 'WI_len':2, 'tip_WI':'Number of integer bits',
                   'WF':15,'WF_len':2, 'tip_WF':'Number of fractional bits',
                   'enabled':True, 'visible':True, 'fractional':True
                   } #: default values
        for k, v in kwargs.items():
            if k not in dict_ui:
                logger.warning("Unknown key {0}".format(k))
            else:
                dict_ui.update({k:v})
        # dict_ui.update(map(kwargs)) # same as above?

        if not dict_ui['fractional']:
            dict_ui['WF'] = 0
        self.WI = dict_ui['WI']
        self.WF = dict_ui['WF']

        lblW = QLabel(to_html(dict_ui['label'], frmt='bi'), self)
        self.ledWI = QLineEdit(self)
        self.ledWI.setToolTip(dict_ui['tip_WI'])
        self.ledWI.setMaxLength(dict_ui['WI_len']) # maximum of 2 digits
        self.ledWI.setFixedWidth(dict_ui['max_led_width']) # width of lineedit in points(?)

        lblDot = QLabel(dict_ui['lbl_sep'], self)
        lblDot.setVisible(dict_ui['fractional'])

        self.ledWF = QLineEdit(self)
        self.ledWF.setToolTip(dict_ui['tip_WF'])
        self.ledWF.setMaxLength(dict_ui['WI_len']) # maximum of 2 digits
        self.ledWF.setFixedWidth(dict_ui['max_led_width']) # width of lineedit in points(?)
        self.ledWF.setVisible(dict_ui['fractional'])
        
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
        self.ledWI.editingFinished.connect(self.ui2dict)
        self.ledWF.editingFinished.connect(self.ui2dict)

    #--------------------------------------------------------------------------
    def ui2dict(self): # was: save_ui
        """ 
        Update the attributes `self.WI`, `self.WF` and `self.W` when one of the QLineEdit
        widgets has been edited.
        
        Return a dict with the three parameters when called directly
        """
        self.WI = safe_eval(self.ledWI.text(), self.WI, return_type="int", sign='pos')
        self.ledWI.setText(qstr(self.WI))
        self.WF = safe_eval(self.ledWF.text(), self.WF, return_type="int", sign='pos')
        self.ledWF.setText(qstr(self.WF))
        self.W = self.WI + self.WF + 1
        return {'WI':self.WI, 'WF':self.WF, 'W':self.W}
        
    #--------------------------------------------------------------------------
    def dict2ui(self, w_dict):
        """ 
        Update the widgets `WI` and `WF` from the dict passed as the argument
        """
        if 'WI' in w_dict:
            self.WI = safe_eval(w_dict['WI'], self.WI, return_type="int", sign='pos')
            self.ledWI.setText(qstr(self.WI))
        else:
            logger.warning("No key 'WI' in dict!")

        if 'WF' in w_dict:
            self.WF = safe_eval(w_dict['WF'], self.WF, return_type="int", sign='pos')
            self.ledWF.setText(qstr(self.WF))
        else:
            logger.warning("No key 'WF' in dict!")

#------------------------------------------------------------------------------
class UI_W_coeffs(UI_W):
    """
    Widget for entering word format (integer and fractional bits) for the 
    oefficients. The result can be read out via the attributes `self.WI` and 
    `self.WF`. This class inherits from `UI_WI_WF`, overloading the methods `load_ui()`
    and `ui2dict()` for loading / saving the UI from / to the filter dict.
    """
    def __init__(self, parent, **kwargs):
        super(UI_W_coeffs, self).__init__(parent, **kwargs)
        # __init__ method of parent is used, additionally initialize coefficient dict
        self.c_dict = build_coeff_dict()
        
    #--------------------------------------------------------------------------
    def ui2dict(self):
        """ 
        Update the attributes `self.WI` and `self.WF` and the filter dict 
        when one of the QLineEdit widgets has been edited.
        """
        self.WI = safe_eval(self.ledWI.text(), self.WI, return_type="int", sign='pos')
        self.ledWI.setText(qstr(self.WI))
        self.WF = safe_eval(self.ledWF.text(), self.WF, return_type="int", sign='pos')
        self.ledWF.setText(qstr(self.WF))
        fb.fil[0]["q_coeff"].update({'WI':self.WI, 'WF':self.WF})
        self.W = self.WI + self.WF + 1

    def dict2ui(self, c_dict=None):
        """ 
        Update the ui and the attributes `self.WI` and `self.WF` from the filter
        dict. `dict2ui()` has to be called when the coefficients or the word
        format has been changed outside the class, e.g. by a new filter design or
        by changing the coefficient format in `input_coeffs.py`.
        """
        if not c_dict:
            c_dict = fb.fil[0]['q_coeff']
        self.WI = c_dict['WI']
        self.WF = c_dict['WF']
        self.ledWI.setText(qstr(self.WI))
        self.ledWF.setText(qstr(self.WF))
        self.W = self.WI + self.WF + 1

        self.c_dict = build_coeff_dict()
        
#==============================================================================
class UI_Q(QWidget):
    """
    Widget for selecting quantization / overflow options. The result can be read out
    via the attributes `self.ovfl` and `self.quant`.
    
    The constructor accepts a dictionary for initial widget settings.
    The following keys are defined; default values are used for missing keys:

    'label_q'  : 'Quant.'                           # widget label
    'tip_q'    : 'Select the kind of quantization.' # Mouse-over tooltip
    'enabled'  : True                               # Is widget enabled?
    'visible'  : True                               # Is widget visible?
    """

    def __init__(self, parent, **kwargs):
        super(UI_Q, self).__init__(parent)
        self._construct_UI(**kwargs)

    def _construct_UI(self, **kwargs):
        """ Construct widget """

        dict_ui = {'label_q':'Quant.', 'tip_q':'Select the kind of quantization.',
                   'cmb_q':['round', 'fix', 'floor'], 'cur_q':'round',
                   'label_ov':'Ovfl.', 'tip_ov':'Select overflow behaviour.',
                   'cmb_ov':['wrap', 'sat'], 'cur_ov':'wrap',
                   'enabled':True, 'visible':True
                   } #: default widget settings
        for key, val in kwargs.items():
            dict_ui.update({key:val})
        # dict_ui.update(map(kwargs)) # same as above?

        lblQuant = QLabel(dict_ui['label_q'], self)
        self.cmbQuant = QComboBox(self)
        self.cmbQuant.addItems(dict_ui['cmb_q'])
        qset_cmb_box(self.cmbQuant, dict_ui['cur_q'])
        self.cmbQuant.setToolTip(dict_ui['tip_q'])

        lblOvfl = QLabel(dict_ui['label_ov'], self)
        self.cmbOvfl = QComboBox(self)
        self.cmbOvfl.addItems(dict_ui['cmb_ov'])
        qset_cmb_box(self.cmbOvfl, dict_ui['cur_ov'])
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
        self.cmbOvfl.currentIndexChanged.connect(self.ui2dict)
        self.cmbQuant.currentIndexChanged.connect(self.ui2dict)

    #--------------------------------------------------------------------------
    def ui2dict(self):
        """ Update the attributes `self.ovfl` and `self.quant` from the UI"""
        self.ovfl = self.cmbOvfl.currentText()
        self.quant = self.cmbQuant.currentText()

    #--------------------------------------------------------------------------
    def dict2ui(self, q_dict):
        """ Update UI from passed dictionary """
        pass

#==============================================================================
class UI_Q_coeffs(UI_Q):
    """
    Widget for selecting quantization / overflow options. The result can be read out
    via the attributes `self.ovfl` and `self.quant`. This class inherits from `UI_Q`,
    overloading the method `load_ui()` for updating the UI from the filter dict.
    """
    def __init__(self, parent, **kwargs):
        super(UI_Q_coeffs, self).__init__(parent, **kwargs)

        # __init__ method of parent is used, additionally initialize coefficient dict
        self.c_dict = build_coeff_dict()
               
    #--------------------------------------------------------------------------
    def load_ui(self):
        """ Update UI from filter dict """
        self.ovfl = fb.fil[0]['q_coeff']['ovfl']
        self.quant = fb.fil[0]['q_coeff']['quant']
        qset_cmb_box(self.cmbOvfl,self.ovfl)
        qset_cmb_box(self.cmbQuant,self.quant)

        self.c_dict = build_coeff_dict()


class FilterHardware(object):
    def __init__(self, b=None, a=None):
        """
        Helper class with common attributes and methods for all filters
        
        Arguments
        ---------
        b (list of int): list of numerator coefficients.
        a (list of int): list of denominator coefficients.

        Attributes
        ----------
        coef_word_format (tuple of int): word format (W,WI,WF).
        n_cascades (int):
        sigin (numpy int array):
        nfft (int):
        hdl_name (str):
        hdl_directory (str):
        hdl_target (str):
        """
        # numerator coefficient
        if b is not None:
            self.b = tuple(b)

        # denominator coefficients
        if a is not None:
            self.a = tuple(a)

        # TODO: need a default word format, the coefficient
        #       can be determined from the coefficients if passed
        #       use an arbitrary value of the input and output
        self.coef_word_format = (24, 0, 23)
        self.input_word_format = (16, 0, 15)
        self.output_word_format = (16, 0, 15)

        self.n_cascades = 0
        self.sigin = np.array([])
        self._shared_multiplier = False
        self._sample_rate = 1
        self._clock_frequency = 1

        self.nfft = 1024

        self.hdl_name = 'name'
        self.hdl_directory = 'directory'
        self.hdl_target = 'verilog'

        # A reference to the HDL block
        self.hardware = None
        
    def setup(self, fx_dict):
        """
        Setup coefficients, word lengths etc.

        Returns
        -------
        None

        Arguments
        ---------
        fx_dict (dict): dictionary with filter parameters:
            
            - coef_w (tuple of int): word format (W, WI, WF)
            
            - input_w (tuple of int): word format (W, WI, WF)
            
            - output_w (tuple of int): word format (W, WI, WF)
        """
        self.coef_word_format  = (fx_dict['QC']['W'], fx_dict['QC']['WI'], fx_dict['QC']['WF'])
        self.input_word_format = (fx_dict['QI']['W'], fx_dict['QI']['WI'], fx_dict['QI']['WF'])
        self.output_word_format = (fx_dict['QO']['W'], fx_dict['QO']['WI'], fx_dict['QO']['WF'])
        
        self.b = tuple(fx_dict['QC']['b'])
        self.a = tuple(fx_dict['QC']['a'])
        if 'sos' in fx_dict['QC']:
            self.sos =  tuple(fx_dict['QC']['sos'])


    def set_coefficients(self, coeff_b = None, coeff_a = None, sos = None):
        """Set filter coefficients.

        Args:
            coeff_b (list): list of numerator filter coefficients
            coeff_a (list): list of denominator filter coefficients
        """
        if coeff_b is not None:
            self.b = tuple(coeff_b)

        if coeff_a is not None:
            self.a = tuple(coeff_a)

        if sos is not None:
            self.sos = sos

    def set_stimulus(self, sigin):
        """Set filter stimulus

        Args:
            sigin (np array int): numpy array of filter stimulus 
            bits (int) : no of bits
        """
        self.sigin = sigin.tolist()

    def set_cascade(self, n_cascades):
        """Set number of filter cascades

        Args:
            n_cascades (int): no of filter sections connected together
        """
        self.n_cascades = n_cascades

#==============================================================================

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = UI_W(None)
    mainw.show()

    app.exec_()