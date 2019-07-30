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
from .fixpoint_helpers import UI_W, UI_W_coeffs, UI_Q, UI_Q_coeffs, rescale

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
        logger.warning("fb.fil[0]['fxqc']['QC']:{0}".format(pprint_log(fb.fil[0]['fxqc']['QC'])))        
        self.wdg_w_coeffs = UI_W_coeffs(self, fb.fil[0]['fxqc']['QC'],
                                        label='Coefficient Format:',
                                        tip_WI='Number of integer bits - edit in the "b,a" tab',
                                        tip_WF='Number of fractional bits - edit in the "b,a" tab',
                                        WI = fb.fil[0]['fxqc']['QC']['WI'],
                                        WF = fb.fil[0]['fxqc']['QC']['WF'])
        self.wdg_w_coeffs.sig_tx.connect(self.process_sig_rx)
        self.wdg_w_coeffs.setEnabled(False)
        
#        self.wdg_q_coeffs = UI_Q_coeffs(self, fb.fil[0]['fxqc']['QC'],
#                                        cur_ov=fb.fil[0]['fxqc']['QC']['ovfl'], 
#                                        cur_q=fb.fil[0]['fxqc']['QC']['quant'])
#        self.wdg_q_coeffs.sig_tx.connect(self.process_sig_rx)

        self.wdg_w_accu = UI_W(self, fb.fil[0]['fxqc']['QA'],
                               label='Accumulator Width <i>W<sub>A </sub></i>:',
                               fractional=True, combo_visible=True)
        self.wdg_w_accu.sig_tx.connect(self.process_sig_rx)

        #self.wdg_q_accu = UI_Q(self, fb.fil[0]['fxqc']['QA'])
        # initial setting for accumulator
        cmbW = qget_cmb_box(self.wdg_w_accu.cmbW, data=False)        
        self.wdg_w_accu.ledWF.setEnabled(cmbW=='man')
        self.wdg_w_accu.ledWI.setEnabled(cmbW=='man')
#------------------------------------------------------------------------------

        layVWdg = QVBoxLayout()
        layVWdg.setContentsMargins(0,0,0,0)
        
        layVWdg.addWidget(self.wdg_w_coeffs)
#        layVWdg.addWidget(self.wdg_q_coeffs)
        fb.fil[0]['fxqc'].update(self.wdg_w_coeffs.c_dict)
        layVWdg.addWidget(self.wdg_w_accu)

        layVWdg.addStretch()

        self.setLayout(layVWdg)

        
#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        logger.warning("RX:\n{0}".format(pprint_log(dict_sig)))
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
                
            elif dict_sig['ui'] == 'ledW':
                pass

            dict_sig.update({'sender':__name__})
            self.sig_tx.emit(dict_sig)
        else:
            self.sig_tx.emit(dict_sig)
        
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
            + fb.fil[0]['fxqc']['QC']['WF']
        fb.fil[0]['fxqc']['QA']['WI'] = fb.fil[0]['fxqc']['QI']['WI']\
            + fb.fil[0]['fxqc']['QC']['WI'] + A_coeff
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
            
        if not 'QC' in fxqc_dict:
            fxqc_dict.update({'QC':{}}) # no coefficient settings in dict yet 
            
        self.wdg_w_coeffs.dict2ui(fxqc_dict['QC']) # update coefficient wordlength

        self.update_accu_settings()        
#------------------------------------------------------------------------------
    def ui2dict(self):
        """
        Read out the subwidgets and return a dict with their settings
        
        Return a dictionary with infos for the fixpoint implementation
        concerning coefficients and their quantization format.
        
        This dictionary is merged with the input and output quantization settings
        that are entered in ``input_fixpoint_specs``.

        
        Parameters
        ----------
        
        None
        
        Returns
        -------
        fxqc_dict : dict

           containing the following keys:

               :'QC': dictionary with coefficients quantization settings
                
        """
   
#        fxqc_dict = {'QC':self.wdg_w_coeffs.c_dict}
        fxqc_dict = self.wdg_w_coeffs.c_dict

        
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

#--------------- Quantizer --------------------------------------
#        sum_full_q = Signal((WA, True))
#        if quant_o == 'round':
#            self.comb += sum_full_q.eq(sum_full + (1 << (self.WO - 1)))
#        else:
#            self.comb += sum_full_q.eq(sum_full)        
#        if ovfl_o == 'wrap':
#            self.comb += self.o.eq(sum_full_q >> (WA-self.WO)) # rescale for output width
#        else:
#            self.comb += \
#                If(sum_full_q[WA-2:] == 0b10,
#                    self.o.eq(MIN_o)
#                ).Elif(sum_full_q[WA-2:] == 0b01,
#                    self.o.eq(MAX_o)
#                ).Else(self.o.eq(sum_full_q >> (WA-self.WO-1))
#                )
#--------------- ------------------------------------------

        # rescale for output width
        self.comb += self.o.eq(rescale(self, sum_full, p['QA'], p['QO']))
#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = FIR_DF_wdg(None)
    mainw.show()

    app.exec_()
    
    # test using "python -m pyfda.fixpoint_widgets.fir_df_migen"