# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for specifying the parameters of a direct-form DF1 FIR filter
"""
import sys

import numpy as np
from numpy.lib.function_base import iterable
import pyfda.filterbroker as fb
from pyfda.libs.pyfda_lib import set_dict_defaults, pprint_log
from pyfda.libs.pyfda_qt_lib import qget_cmb_box

from pyfda.libs.compat import QWidget, QVBoxLayout, pyqtSignal

import pyfda.libs.pyfda_fix_lib as fx
from pyfda.fixpoint_widgets.fixpoint_helpers import UI_W, UI_Q

import logging
logger = logging.getLogger(__name__)

classes = {'FIR_DF_wdg': 'FIR_DF_py'}  # widget class name : display name


# =============================================================================
class FIR_DF_wdg(QWidget):
    """
    Widget for entering word formats & quantization, also instantiates fixpoint
    filter class :class:`FilterFIR`.
    """
    sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outcgoing
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent=None):
        super(FIR_DF_wdg, self).__init__(parent)

        self.title = ("<b>Direct-Form (DF) FIR Filter</b><br />"
                      "Standard FIR topology.")
        self.img_name = "fir_df.png"

        self._construct_UI()
        # Construct an instance of the fixpoint filter using the settings from
        # the 'fxqc' quantizer dict
        # TODO: not needed, remove test in input_fixpoint_specs
        # self.construct_fixp_filter()
# ------------------------------------------------------------------------------

    def _construct_UI(self):
        """
        Intitialize the UI with widgets for coefficient format and input and
        output quantization
        """
        if 'QA' not in fb.fil[0]['fxqc']:
            fb.fil[0]['fxqc']['QA'] = {}
        set_dict_defaults(fb.fil[0]['fxqc']['QA'],
                          {'WI': 0, 'WF': 30, 'W': 32, 'ovfl': 'wrap', 'quant': 'floor'})

        self.wdg_w_coeffs = UI_W(self, fb.fil[0]['fxqc']['QCB'], wdg_name='w_coeff',
                                 label='Coeff. Format <i>B<sub>I.F&nbsp;</sub></i>:',
                                 tip_WI='Number of integer bits - edit in "b,a" tab',
                                 tip_WF='Number of fractional bits - edit in "b,a" tab',
                                 WI=fb.fil[0]['fxqc']['QCB']['WI'],
                                 WF=fb.fil[0]['fxqc']['QCB']['WF'])


#        self.wdg_q_coeffs = UI_Q(self, fb.fil[0]['fxqc']['QCB'],
#                                        cur_ov=fb.fil[0]['fxqc']['QCB']['ovfl'],
#                                        cur_q=fb.fil[0]['fxqc']['QCB']['quant'])
#        self.wdg_q_coeffs.sig_tx.connect(self.update_q_coeff)

        self.wdg_w_accu = UI_W(self, fb.fil[0]['fxqc']['QA'],
                               label='', wdg_name='w_accu',
                               fractional=True, combo_visible=True)

        self.wdg_q_accu = UI_Q(self, fb.fil[0]['fxqc']['QA'], wdg_name='q_accu',
                               label='Accu Format <i>Q<sub>A&nbsp;</sub></i>:')

        # initial setting for accumulator
        cmbW = qget_cmb_box(self.wdg_w_accu.cmbW, data=False)
        self.wdg_w_accu.ledWF.setEnabled(cmbW == 'man')
        self.wdg_w_accu.ledWI.setEnabled(cmbW == 'man')

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs & EVENTFILTERS
        # ----------------------------------------------------------------------
        self.wdg_w_coeffs.sig_tx.connect(self.update_q_coeff)
        self.wdg_w_accu.sig_tx.connect(self.process_sig_rx)
        self.wdg_q_accu.sig_tx.connect(self.process_sig_rx)
# ------------------------------------------------------------------------------

        layVWdg = QVBoxLayout()
        layVWdg.setContentsMargins(0, 0, 0, 0)

        layVWdg.addWidget(self.wdg_w_coeffs)
#        layVWdg.addWidget(self.wdg_q_coeffs)
        layVWdg.addWidget(self.wdg_q_accu)
        layVWdg.addWidget(self.wdg_w_accu)

        layVWdg.addStretch()

        self.setLayout(layVWdg)

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        logger.debug("sig_rx:\n{0}".format(pprint_log(dict_sig)))
        # check whether anything needs to be done locally
        # could also check here for 'quant', 'ovfl', 'WI', 'WF' (not needed at the moment)
        # if not, just pass the dict.
        if 'ui' in dict_sig:
            if dict_sig['wdg_name'] == 'w_coeff':  # coefficient format updated
                """
                Update coefficient quantization settings and coefficients.

                The new values are written to the fixpoint coefficient dict as
                `fb.fil[0]['fxqc']['QCB']` and  `fb.fil[0]['fxqc']['b']`.
                """

                fb.fil[0]['fxqc'].update(self.ui2dict())

            elif dict_sig['wdg_name'] == 'cmbW':
                cmbW = qget_cmb_box(self.wdg_w_accu.cmbW, data=False)
                self.wdg_w_accu.ledWF.setEnabled(cmbW == 'man')
                self.wdg_w_accu.ledWI.setEnabled(cmbW == 'man')
                if cmbW in {'full', 'auto'}:
                    self.dict2ui()
                    self.emit({'specs_changed': 'cmbW'})
                else:
                    return

            dict_sig.update({'id': id(self)})  # currently only local

        self.emit(dict_sig)

# ------------------------------------------------------------------------------
    def update_q_coeff(self, dict_sig):
        """
        Update coefficient quantization settings and coefficients.

        The new values are written to the fixpoint coefficient dict as
        `fb.fil[0]['fxqc']['QCB']` and
        `fb.fil[0]['fxqc']['b']`.
        """
        logger.debug("update q_coeff - dict_sig:\n{0}".format(pprint_log(dict_sig)))
        # dict_sig.update({'ui':'C'+dict_sig['ui']})
        fb.fil[0]['fxqc'].update(self.ui2dict())
        logger.debug("b = {0}".format(pprint_log(fb.fil[0]['fxqc']['b'])))

        self.process_sig_rx(dict_sig)

# ------------------------------------------------------------------------------
    def update_accu_settings(self):
        """
        Calculate number of extra integer bits needed in the accumulator (bit
        growth) depending on the coefficient area (sum of absolute coefficient
        values) for `cmbW == 'auto'` or depending on the number of coefficients
        for `cmbW == 'full'`. The latter works for arbitrary coefficients but
        requires more bits.

        The new values are written to the fixpoint coefficient dict
        `fb.fil[0]['fxqc']['QA']`.
        """
        try:
            if qget_cmb_box(self.wdg_w_accu.cmbW, data=False) == "full":
                A_coeff = int(np.ceil(np.log2(len(fb.fil[0]['fxqc']['b']))))
            elif qget_cmb_box(self.wdg_w_accu.cmbW, data=False) == "auto":
                A_coeff = int(np.ceil(np.log2(np.sum(np.abs(fb.fil[0]['ba'][0])))))
        except Exception as e:
            logger.error(e)
            return

        if qget_cmb_box(self.wdg_w_accu.cmbW, data=False) == "full" or\
                qget_cmb_box(self.wdg_w_accu.cmbW, data=False) == "auto":
            fb.fil[0]['fxqc']['QA']['WF'] = fb.fil[0]['fxqc']['QI']['WF']\
                + fb.fil[0]['fxqc']['QCB']['WF']
            fb.fil[0]['fxqc']['QA']['WI'] = fb.fil[0]['fxqc']['QI']['WI']\
                + fb.fil[0]['fxqc']['QCB']['WI'] + A_coeff

        # calculate total accumulator word length
        fb.fil[0]['fxqc']['QA']['W'] = fb.fil[0]['fxqc']['QA']['WI']\
            + fb.fil[0]['fxqc']['QA']['WF'] + 1

        # update quantization settings
        fb.fil[0]['fxqc']['QA'].update(self.wdg_q_accu.q_dict)

        self.wdg_w_accu.dict2ui(fb.fil[0]['fxqc']['QA'])

# ------------------------------------------------------------------------------
    def dict2ui(self):
        """
        Update all parts of the UI that need to be updated when specs have been
        changed outside this class, e.g. coefficients and coefficient wordlength.
        This also provides the initial setting for the widgets when the filter has
        been changed.

        This is called from one level above by
        :class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs`.
        """
        fxqc_dict = fb.fil[0]['fxqc']
        if 'QA' not in fxqc_dict:
            fxqc_dict.update({'QA': {}})  # no accumulator settings in dict yet
            logger.warning("QA key missing")

        if 'QCB' not in fxqc_dict:
            fxqc_dict.update({'QCB': {}})  # no coefficient settings in dict yet
            logger.warning("QCB key missing")

        self.wdg_w_coeffs.dict2ui(fxqc_dict['QCB'])  # update coefficient wordlength
        self.update_accu_settings()                  # update accumulator settings

# ------------------------------------------------------------------------------
    def ui2dict(self):
        """
        Read out the quantization subwidgets and store their settings in the central
        fixpoint dictionary `fb.fil[0]['fxqc']` using the keys described below.

        Coefficients are quantized with these settings in the subdictionary under
        the key 'b'.

        Additionally, these subdictionaries are returned  to the caller
        (``input_fixpoint_specs``) where they are used to update ``fb.fil[0]['fxqc']``

        Parameters
        ----------

        None

        Returns
        -------
        fxqc_dict : dict

           containing the following keys and values:

        - 'QCB': dictionary with coefficients quantization settings

        - 'QA': dictionary with accumulator quantization settings

        - 'b' : list of coefficients in integer format

        """
        fxqc_dict = fb.fil[0]['fxqc']
        if 'QA' not in fxqc_dict:
            # no accumulator settings in dict yet:
            fxqc_dict.update({'QA': self.wdg_w_accu.q_dict})
            logger.warning("Empty dict 'fxqc['QA]'!")
        else:
            fxqc_dict['QA'].update(self.wdg_w_accu.q_dict)

        if 'QCB' not in fxqc_dict:
            # no coefficient settings in dict yet
            fxqc_dict.update({'QCB': self.wdg_w_coeffs.q_dict})
            logger.warning("Empty dict 'fxqc['QCB]'!")
        else:
            fxqc_dict['QCB'].update(self.wdg_w_coeffs.q_dict)

        fxqc_dict.update({'b': self.wdg_w_coeffs.quant_coeffs(self.wdg_w_coeffs.q_dict,
                                                              fb.fil[0]['ba'][0])})
        return fxqc_dict

# ------------------------------------------------------------------------------
    def construct_fixp_filter(self):
        """
        Construct an instance of the fixpoint filter object using the settings from
        the 'fxqc' quantizer dict
        """
        p = fb.fil[0]['fxqc']  # parameter dictionary with coefficients etc.
        self.dut = FIR_DF(p)

# ------------------------------------------------------------------------------
    # def to_verilog(self, **kwargs):
    #     """
    #     Convert the migen description to Verilog
    #     """
    #     return verilog.convert(self.fixp_filter,
    #                            ios={self.fixp_filter.i, self.fixp_filter.o},
    #                            **kwargs)


    # ------------------------------------------------------------------------
    def run_sim(self, stimulus):

        return self.dut.fxfilter(stimulus)[0]


# =============================================================================
class FIR_DF(object):
    """
    Fixpoint filter object
    filt = FIR_DF(p) # Instantiate fixpoint filter object
    
    The fixpoint object contains two different quantizers:
    - b is an array with coefficients
    - q_mul describes requanitization after coefficient multiplication
      ('quant' and 'sat' can both be set to 'none' if there is none)
    - q_acc describes requantization after each summation in the accumulator
            (resp. in the common summation point)
    """
    def __init__(self, p):
        """
        Instantiate fixed point object parameter dict

        Parameters
        ----------

        p : dict
            dictionary with coefficients and quantizer settings with the following keys:

            - 'b', values: array-like, coefficients as integers

            - 'QA' value: dict with quantizer settings for the accumulator

            - 'q_mul' : dict with quantizer settings for the partial products (optional)

        """
        self.init(p)

    # ---------------------------------------------------------
    def init(self, p, zi: iterable = None) -> None:
        """
        Initialize filter with parameter dict `p` by initialising all registers
        and quantizers.
        This needs to be done every time quantizers or coefficients are updated.

        Parameters
        ----------
        p : dict
            dictionary with coefficients and quantizer settings (see docstring of
            `__init__()` for details)

        zi : array-like
            Initialize `L = len(b)` filter registers. Strictly speaking, `zi[0]` is
            not a register but the current input value.
            When `len(zi) != len(b)`, truncate or fill up with zeros.
            When `zi == None`, all registers are filled with zeros.

        Returns
        -------
        None.
        """
        logger.error(p)
        self.p = p  # parameter dictionary with coefficients etc.

        if 'q_mul' not in self.p or self.p['q_mul'] is None:
            q_mul = {'Q': '0.15', 'ovfl': 'none', 'quant': 'none'}
        else:
            q_mul = p['q_mul']

        self.b = self.p['b']  # coefficients
        self.L = len(self.b)  # filter length = number of taps
        self.Q_mul = fx.Fixed(q_mul)  # create quantizer for partial product
        self.Q_acc = fx.Fixed(self.p['QA'])  # create quantizer for accumulator
        self.N_over_filt = 0  # initialize overflow counter TODO: not used yet?

        # Initialize vectors (also speeds up calculation for large arrays)
        self.xbq = np.zeros(len(self.b))  # partial products

        if zi is None:
            self.zi = np.zeros(self.L - 1)
        else:  # initialize filter memory and fill up with zeros
            if len(zi) == self.L - 1:
                self.zi = zi
            elif len(zi) < self.L - 1:
                self.zi = np.concatenate((zi, np.zeros(self.L - 1 - len(zi))))
            else:
                self.zi = zi[:self.L - 1]

    # ---------------------------------------------------------
    def reset(self):
        """ resetting overflow counters """
        self.Q_mul.resetN()  # reset overflow counter of Q_mul
        self.Q_acc.resetN()  # reset overflow counter of Q_acc
        self.N_over_filt = 0  # total number of overflows in filter

    # ---------------------------------------------------------
    def fxfilter(self, b: iterable = None, x: iterable = None, zi: iterable = None) -> np.ndarray:
        """
        TODO: When len(x) < len(b), only zeros are returned because the for loop
        is never executed

        Calculate FIR filter (direct form) response via difference equation with
        quantization. Registers can be initialized with `zi`.

        Parameters
        ----------
        x :  array-like or scalar or None
             input value(s); when x is a scalar, calculate impulse response with the
             amplitude defined by the scalar. When `x == None`, calculate impulse
             response with amplitude one.

        b :  array-like
             filter coefficients; when `b == None`, the old coefficients are left untouched

        zi : array-like
             initial conditions; when `zi == None`, the register contents are used from
             the last run.

        Returns
        -------
        yq : ndarray
            The quantized input value(s) as an ndarray of np.float64
            and the same shape as `x resp. `b` (impulse response).
        """

        if not b is None and np.any(b != self.b): # update coefficients, reset filter
            self.p['b'] = self.b = b
            self.init(self.p)

        # When `zi` is specified, initialize filter memory with it and pad with zeros
        # When `zi == None`, use register contents from last run
        if zi is not None:
            if len(zi) == self.L - 1:   # use zi as it is
                self.zi = zi
            elif len(zi) < self.L - 1:  # append zeros
                self.zi = np.concatenate((zi, np.zeros(self.L - 1 - len(zi))))
            else:                       # truncate zi
                self.zi = zi[:self.L - 1]
                logger.warning("len(zi) > len(b) - 1, zi was truncated")

        if np.isscalar(x):
            A = x
            x = np.zeros(len(self.b))
            x[0] = A
        elif x is None: # calculate impulse response
            x = np.zeros(len(self.b))
            x[0] = 1

        # initialize quantized partial products and output arrays
        y_q = xb_q = np.zeros(len(x))

        # Calculate response by:
        # - append new stimuli `x` to register state `self.zi`
        # - slide a window with length `len(b)` over `self.zi`, starting at position `k`
        #   and multiply it with the coefficients `b`, yielding the partial products x*b
        #   TODO: Doing this for the last len(x) terms should be enough
        # - quantize the partial products x*b, yielding xb_q
        # - sum up the quantized partial products, yielding result y[k]
        # - quantize result, yielding y_q[k]

        self.zi = np.concatenate((self.zi, x))

        for k in range(len(x)):
            # weighted state-vector x at time k:
            xb_q = self.Q_mul.fixp(
                self.zi[k:k + len(self.b)] * self.b)
            # sum up x_bq to get accu[k]
            y_q[k] = self.Q_acc.fixp(np.sum(xb_q))

        self.zi = self.zi[-self.L:]  # store last L inputs (i.e. the L registers)
        self.N_over_filt = self.Q_acc.N_over + self.Q_mul.N_over

        return y_q[:len(x)], self.zi


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """ Run widget standalone with `python -m pyfda.fixpoint_widgets.fir_df.fir_df_ui` """
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    p = {'b':[1,2,3,2,1], 'QA':{'Q': '4.3', 'ovfl': 'wrap', 'quant': 'round'}}
    dut = FIR_DF(p)
    x = np.ones(4)
    y = dut.fxfilter(x=x)
    print(y)
    y = dut.fxfilter(x=np.zeros(5))
    print(y)



    # ------------ test ui ----------------
    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = FIR_DF_wdg()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
