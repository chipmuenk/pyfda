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
import logging
logger = logging.getLogger(__name__)

import numpy as np
import pyfda.filterbroker as fb
from pyfda.pyfda_lib import set_dict_defaults, pprint_log
from pyfda.pyfda_qt_lib import qget_cmb_box

from ..compat import QWidget, QVBoxLayout, pyqtSignal

#import pyfda.pyfda_fix_lib as fx
from .fixpoint_helpers import UI_W, UI_Q, rescale

#####################
from functools import reduce
from operator import add

from migen import Signal, Module, run_simulation
from migen.fhdl import verilog
################################

classes = {'FIR_DF_wdg':'FIR_DF'} #: Dict containing widget class name : display name

# =============================================================================

class FIR_DF_wdg(QWidget):
    """
    Widget for entering word formats & quantization, also instantiates fixpoint
    filter class :class:`FilterFIR`.
    """
    # incoming, 
    sig_rx = pyqtSignal(object)
    # outcgoing
    sig_tx = pyqtSignal(object)


    def __init__(self, parent):
        super(FIR_DF_wdg, self).__init__(parent)

        self.title = ("<b>Direct-Form (DF) FIR Filter</b><br />"
                      "Standard FIR topology.")
        self.img_name = "fir_df.png"
        
        self._construct_UI()
        # Construct an instance of the fixpoint filter using the settings from
        # the 'fxqc' quantizer dict
        self.construct_fixp_filter()
#------------------------------------------------------------------------------

    def _construct_UI(self):
        """
        Intitialize the UI with widgets for coefficient format and input and 
        output quantization
        """
        if not 'QA' in fb.fil[0]['fxqc']:
            fb.fil[0]['fxqc']['QA'] = {}
        set_dict_defaults(fb.fil[0]['fxqc']['QA'], 
                          {'WI':0, 'WF':30, 'W':32, 'ovfl':'wrap', 'quant':'floor'})
      
        self.wdg_w_coeffs = UI_W(self, fb.fil[0]['fxqc']['QCB'],
                                        label='Coeff. Format <i>B<sub>I.F&nbsp;</sub></i>:',
                                        tip_WI='Number of integer bits - edit in the "b,a" tab',
                                        tip_WF='Number of fractional bits - edit in the "b,a" tab',
                                        WI = fb.fil[0]['fxqc']['QCB']['WI'],
                                        WF = fb.fil[0]['fxqc']['QCB']['WF'])
        self.wdg_w_coeffs.sig_tx.connect(self.update_q_coeff)
#        self.wdg_w_coeffs.setEnabled(False)
        
#        self.wdg_q_coeffs = UI_Q_coeffs(self, fb.fil[0]['fxqc']['QCB'],
#                                        cur_ov=fb.fil[0]['fxqc']['QCB']['ovfl'], 
#                                        cur_q=fb.fil[0]['fxqc']['QCB']['quant'])
#        self.wdg_q_coeffs.sig_tx.connect(self.process_sig_rx)

        self.wdg_w_accu = UI_W(self, fb.fil[0]['fxqc']['QA'],
                               label='Accu Format <i>A<sub>I.F&nbsp;</sub></i>:',
                               fractional=True, combo_visible=True)
        self.wdg_w_accu.sig_tx.connect(self.process_sig_rx)

        self.wdg_q_accu = UI_Q(self, fb.fil[0]['fxqc']['QA'])
        self.wdg_q_accu.sig_tx.connect(self.process_sig_rx)
        # initial setting for accumulator
        cmbW = qget_cmb_box(self.wdg_w_accu.cmbW, data=False)        
        self.wdg_w_accu.ledWF.setEnabled(cmbW=='man')
        self.wdg_w_accu.ledWI.setEnabled(cmbW=='man')
#------------------------------------------------------------------------------

        layVWdg = QVBoxLayout()
        layVWdg.setContentsMargins(0,0,0,0)
        
        layVWdg.addWidget(self.wdg_w_coeffs)
#        layVWdg.addWidget(self.wdg_q_coeffs)
        layVWdg.addWidget(self.wdg_w_accu)
        layVWdg.addWidget(self.wdg_q_accu)

        layVWdg.addStretch()

        self.setLayout(layVWdg)

#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        logger.debug("sig_rx:\n{0}".format(pprint_log(dict_sig)))
        # check whether anything needs to be done locally
        # could also check here for 'quant', 'ovfl', 'WI', 'WF' (not needed at the moment)
        if 'ui' in dict_sig:
            if dict_sig['ui'] == 'cmbW':
                cmbW = qget_cmb_box(self.wdg_w_accu.cmbW, data=False)
                self.wdg_w_accu.ledWF.setEnabled(cmbW=='man')
                self.wdg_w_accu.ledWI.setEnabled(cmbW=='man')
                if cmbW in {'full', 'auto'}:
                    self.dict2ui()
                    self.sig_tx.emit({'sender':__name__, 'specs_changed':'cmbW'})
                else:
                    return

            dict_sig.update({'sender':__name__})

        self.sig_tx.emit(dict_sig)
        
    def update_q_coeff(self, dict_sig):
        """
        Update coefficient quantization settings and coefficients.
        
        The new values are written to the fixpoint coefficient dict as
        `fb.fil[0]['fxqc']['QCB']` and
        `fb.fil[0]['fxqc']['b']`.
        """  
        logger.error("update q_coeff - dict_sig:\n{0}".format(pprint_log(dict_sig)))
        dict_sig.update({'ui':'C'+dict_sig['ui']})
        fb.fil[0]['fxqc'].update(self.ui2dict())
        
        self.process_sig_rx(dict_sig)

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
        if qget_cmb_box(self.wdg_w_accu.cmbW, data=False) == "full":
            A_coeff = int(np.ceil(np.log2(len(fb.fil[0]['fxqc']['b']))))
        elif qget_cmb_box(self.wdg_w_accu.cmbW, data=False) == "auto":
            A_coeff = int(np.ceil(np.log2(np.sum(np.abs(fb.fil[0]['ba'][0])))))
        else:
            return
        fb.fil[0]['fxqc']['QA']['WF'] = fb.fil[0]['fxqc']['QI']['WF']\
            + fb.fil[0]['fxqc']['QCB']['WF']
        fb.fil[0]['fxqc']['QA']['WI'] = fb.fil[0]['fxqc']['QI']['WI']\
            + fb.fil[0]['fxqc']['QCB']['WI'] + A_coeff
        fb.fil[0]['fxqc']['QA']['W'] = fb.fil[0]['fxqc']['QA']['WI']\
            + fb.fil[0]['fxqc']['QA']['WF'] + 1

        self.wdg_w_accu.dict2ui(fb.fil[0]['fxqc']['QA'])

#------------------------------------------------------------------------------
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
        if not 'QA' in fxqc_dict:
            fxqc_dict.update({'QA':{}}) # no accumulator settings in dict yet
            logger.warning("empty QA")
            
        if not 'QCB' in fxqc_dict:
            fxqc_dict.update({'QCB':{}}) # no coefficient settings in dict yet 
            
        self.wdg_w_coeffs.dict2ui(fxqc_dict['QCB']) # update coefficient wordlength

        self.update_accu_settings()        
#------------------------------------------------------------------------------
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
        if not 'QA' in fxqc_dict:
            fxqc_dict.update({'QA':{}}) # no accumulator settings in dict yet
            logger.warning("Empty dict 'fxqc['QA]'!")
        else:
            fxqc_dict['QA'].update(self.wdg_w_accu.q_dict)
            
        if not 'QCB' in fxqc_dict:
            fxqc_dict = {'QCB':self.wdg_w_coeffs.q_dict} # no coefficient settings in dict yet
            logger.warning("Empty dict 'fxqc['QCB]'!")
        else:
            fxqc_dict['QCB'].update(self.wdg_w_coeffs.q_dict)
   
        fxqc_dict.update({'b':self.wdg_w_coeffs.quant_coeffs(self.wdg_w_coeffs.q_dict,
                                                        fb.fil[0]['ba'][0])})
        return fxqc_dict
    
#------------------------------------------------------------------------------
    def construct_fixp_filter(self):
        """
        Construct an instance of the fixpoint filter object using the settings from
        the 'fxqc' quantizer dict
        """
        self.fixp_filter = FIR()
#------------------------------------------------------------------------------
    def to_verilog(self):
        """
        Convert the migen description to Verilog
        """
        return verilog.convert(self.fixp_filter,
                               ios={self.fixp_filter.i, self.fixp_filter.o}) 
#------------------------------------------------------------------------------
    def tb_wdg_stim(self, stimulus, inputs, outputs):
        """ use stimulus list from widget as input to filter """
        for x in stimulus:
            yield self.fixp_filter.i.eq(int(x)) # pass one stimulus value to filter
            inputs.append(x) # and append it to input list
            outputs.append((yield self.fixp_filter.o)) # append filter output to output list
            yield # ??


#------------------------------------------------------------------------------           
    def run_sim(self, stimulus):
        """
        Pass stimuli and run filter simulation, see 
        https://reconfig.io/2018/05/hello_world_migen
        https://github.com/m-labs/migen/blob/master/examples/sim/fir.py        
        """
    
        inputs = []
        response = []
        
        testbench = self.tb_wdg_stim(stimulus, inputs, response) 
            
        run_simulation(self.fixp_filter, testbench)
        
        return response
###############################################################################
# A synthesizable FIR filter.
class FIR(Module):
    def __init__(self):
        p = fb.fil[0]['fxqc']

        # ------------- Define I/Os -------------------------------------------
        self.WI = p['QI']['W']
        self.WO = p['QO']['W']
        # saturation logic doesn't make much sense with a FIR filter, this is 
        # just for demonstration
        WA = p['QA']['W']

        self.i = Signal((self.WI, True)) # input signal
        self.o = Signal((self.WO, True)) # output signal

        ###
        muls = []
        src = self.i

        for b in p['b']:
            sreg = Signal((self.WI, True)) # registers for input signal 
            self.sync += sreg.eq(src)
            src = sreg
            muls.append(int(b)*sreg)
        sum_full = Signal((WA, True))
        self.sync += sum_full.eq(reduce(add, muls)) # sum of multiplication products

        # rescale for output width
        self.comb += self.o.eq(rescale(self, sum_full, p['QA'], p['QO']))
#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = FIR_DF_wdg(None)
    mainw.show()

    app.exec_()
    
    # test using "python -m pyfda.fixpoint_widgets.fir_df"