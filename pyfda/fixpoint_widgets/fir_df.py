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

import pyfda.filterbroker as fb
from pyfda.pyfda_lib import set_dict_defaults

from ..compat import QWidget, QVBoxLayout, pyqtSignal

#import pyfda.pyfda_fix_lib as fx
from .fixpoint_helpers import UI_W, UI_W_coeffs, UI_Q, UI_Q_coeffs

#####################
from functools import reduce
from operator import add

from math import cos, pi
#from scipy import signal

from migen import Signal, Module, If, run_simulation
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

        self.fxqc_dict = fb.fil[0]['fxqc']
        
        self._construct_UI()
        # Construct an instance of the HDL filter object
        self.construct_fixp_filter() # construct instance self.hdlfilter with dummy data
#------------------------------------------------------------------------------

    def _construct_UI(self):
        """
        Intitialize the UI with widgets for coefficient format and input and 
        output quantization
        """
        if not 'QA' in self.fxqc_dict:
            self.fxqc_dict['QA'] = {}
        set_dict_defaults(self.fxqc_dict['QA'], 
                          {'WI':30, 'WF':0, 'W':31, 'ovfl':'wrap', 'quant':'floor'})
        
        self.wdg_w_coeffs = UI_W_coeffs(self, fb.fil[0]['q_coeff'],
                                        label='Coefficient Format:',
                                        tip_WI='Number of integer bits - edit in the "b,a" tab',
                                        tip_WF='Number of fractional bits - edit in the "b,a" tab',
                                        WI = fb.fil[0]['q_coeff']['WI'],
                                        WF = fb.fil[0]['q_coeff']['WF'])
        self.wdg_q_coeffs = UI_Q_coeffs(self, fb.fil[0]['q_coeff'],
                                        cur_ov=fb.fil[0]['q_coeff']['ovfl'], 
                                        cur_q=fb.fil[0]['q_coeff']['quant'])
        self.wdg_w_accu = UI_W(self, self.fxqc_dict['QA'],
                               label='Accumulator Width <i>W<sub>A </sub></i>:',
                               fractional=False)
        self.wdg_w_accu.sig_tx.connect(self.sig_tx)       

        #self.wdg_q_accu = UI_Q(self, self.fxqc_dict['QA'])
#------------------------------------------------------------------------------

        layVWdg = QVBoxLayout()
        layVWdg.setContentsMargins(0,0,0,0)
        
        layVWdg.addWidget(self.wdg_w_coeffs)
        layVWdg.addWidget(self.wdg_q_coeffs)
        self.fxqc_dict.update({'QC':self.wdg_w_coeffs.c_dict})

        layVWdg.addWidget(self.wdg_w_accu)

        layVWdg.addStretch()

        self.setLayout(layVWdg)
        
#------------------------------------------------------------------------------
    def dict2ui(self, fxqc_dict):
        """
        Update all parts of the UI that need to be updated when specs have been
        changed outside this class, e.g. coefficients and coefficient wordlength.
        This also provides the initial setting for the widgets when the filter has
        been changed.

        This is called from one level above by 
        :class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs`.
        """
        if not 'QA' in fxqc_dict:
            fxqc_dict.update({'QA':{}}) # no accumulator settings in dict yet
            logger.warning("empty QA")
        else:
            logger.warning("QA:{0}".format(fxqc_dict['QA']))
            
        if not 'QC' in fxqc_dict:
            fxqc_dict.update({'QC':{}}) # no coefficient settings in dict yet 
            
        self.wdg_w_coeffs.dict2ui(fxqc_dict['QC']) # update coefficient wordlength
        self.wdg_q_coeffs.dict2ui(fxqc_dict['QC']) # update coefficient quantization settings
        
        self.wdg_w_accu.dict2ui(fxqc_dict['QA'])
        
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
   
        fxqc_dict = {'QC':self.wdg_w_coeffs.c_dict}
        
        return fxqc_dict
    
#------------------------------------------------------------------------------
    def construct_fixp_filter(self):
        """
        Construct an instance of the fixpoint filter object using the settings from
        the quantizer dict
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

    def tb_pulse(self, stimulus, inputs, outputs):
        """ unit pulse stimulus signal """
        fscale = 2**(self.fixp_filter.WI - 1)-1
        for t in range(len(stimulus)):
            #v = 0.1*cos(2*pi*0.1*t)*fscale
            if t == 0:
                v = fscale
            else:
                v = 0
            yield self.fixp_filter.i.eq(int(v))
            inputs.append(v)
            outputs.append((yield self.fixp_filter.o))
            yield


    def tb_cos(self, stimulus, inputs, outputs):
        """ cosine test signal """
        fscale = 2**(self.fixp_filter.WI - 1)-1
        for t in range(len(stimulus)):
            v = 0.1*cos(2*pi*0.1*t)*fscale
            yield self.fixp_filter.i.eq(int(v))
            inputs.append(v)
            outputs.append((yield self.fixp_filter.o))
            yield

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
        # -------------- Get generics -----------------------------------------
#        p = {}
#           # new Key , Key 1 und 2 in fxqc_dict, default value
#        p_list = [['WI', 'QI','W', 16],
#                    ['WO', 'QO','W', 16],
#                    ['WA', 'QA','W', 31],
#                    ['WC', 'QC','W', 16],
#                    ['b',  'QC','b', [1,1,1]]
#                    ]
        #Automatic : p['WA'] = p['WC'] + p['WI'] =- 1
#        for l in p_list:
#            try:
#                p[l[0]] = fxqc_dict[l[1]][l[2]]
#            except (KeyError, TypeError) as e:
#                logger.warning("Error [{0}][{1}]:\n{2}".format(l[1],l[2],e))
#                p[l[0]] = l[3]
        # ------------- Define I/Os -------------------------------------------
        ovfl_o = p['QO']['ovfl']
        quant_o = p['QO']['quant']
        logger.warning(quant_o)

        self.WI = p['QI']['W']
        self.WO = p['QO']['W']
        # saturation logic doesn't make much sense with a FIR filter, this is 
        # just for demonstration
        if ovfl_o == 'wrap':
            WA = p['QA']['W']
        else:
            WA = p['QA']['W'] + 1 # add one guard bit
        self.i = Signal((self.WI, True)) # input signal
        self.o = Signal((self.WO, True)) # output signal
        MIN_o = - 1 << (self.WO - 1)
        MAX_o = -MIN_o - 1
        self.response = []

        ###
        muls = []
        src = self.i
        for c in p['QC']['b']:
            sreg = Signal((self.WI, True)) # registers for input signal 
            self.sync += sreg.eq(src)
            src = sreg
            muls.append(c*sreg)
        sum_full = Signal((WA, True))
        sum_full_q = Signal((WA, True))
        self.sync += sum_full.eq(reduce(add, muls)) # sum of multiplication products
        if quant_o == 'round':
            self.comb += sum_full_q.eq(sum_full + (1 << (self.WO - 1)))
        else:
            self.comb += sum_full_q.eq(sum_full)        
        if ovfl_o == 'wrap':
            self.comb += self.o.eq(sum_full_q >> (WA-self.WO)) # rescale for output width
        else:
            self.comb += \
                If(sum_full_q[WA-2:] == 0b10,
                    self.o.eq(MIN_o)
                ).Elif(sum_full_q[WA-2:] == 0b01,
                    self.o.eq(MAX_o)
                ).Else(self.o.eq(sum_full_q >> (WA-self.WO-1))
                )

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = FIR_DF_wdg(None)
    mainw.show()

    app.exec_()
    
    # test using "python -m pyfda.fixpoint_widgets.fir_df_migen"