# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for specifying the parameters of a direct-form 1 (DF1) filter
"""
import sys
import logging
logger = logging.getLogger(__name__)

import pyfda.filterbroker as fb

from ..compat import QWidget#, QLabel, QVBoxLayout, QHBoxLayout

#from .fixpoint_helpers import UI_W, UI_W_coeffs, UI_Q, UI_Q_coeffs
from migen import Signal, Module, If, run_simulation
from migen.fhdl import verilog
################################


classes = {'Delay_wdg':'Delay'} #: Dict containing class name : display name

class Delay_wdg(QWidget):
    """
    Widget for entering word formats & quantization
    """
    def __init__(self, parent, fxqc_widget={}):
        super(Delay_wdg, self).__init__(parent)

        self.title = ("<b>Unit Delay</b><br />"
                 "Just a delay with quantization for testing fixpoint quantization,"
                 "simulation and HDL generation.")
        self.img_name = "delay.png"
        
        self.fxqc_dict = fb.fil[0]['fxqc']

        self._construct_UI()
        # Construct an instance of the HDL filter object
        self.construct_fixp_filter()
#------------------------------------------------------------------------------

    def _construct_UI(self):
        """
        Intitialize the UI and instantiate hdl_filter class
        """
        pass
        
#        lblHBtnsMsg = QLabel("<b>Fixpoint signal / coeff. formats as WI.WF:</b>", self)
#        self.layHBtnsMsg = QHBoxLayout()
#        self.layHBtnsMsg.addWidget(lblHBtnsMsg)
#
#        self.wdg_w_input = UI_W(self, label='Input Format <i>Q<sub>X </sub></i>:')
#        self.wdg_q_input = UI_Q(self)
#        
##------------------------------------------------------------------------------
#
#        layVWdg = QVBoxLayout()
#        layVWdg.setContentsMargins(0,0,0,0)
#
#        layVWdg.addLayout(self.layHBtnsMsg)
#
#        layVWdg.addWidget(self.wdg_w_input)
#        layVWdg.addWidget(self.wdg_q_input)
#        
#        layVWdg.addStretch()
#
#        self.setLayout(layVWdg)
#------------------------------------------------------------------------------
    def construct_fixp_filter(self):
        """
        Construct an instance of the HDL filter object using the settings from
        the quantizer dict
        """
        self.fixp_filter = Delay() # construct HDL filter instance
#------------------------------------------------------------------------------
    def to_verilog(self):
        """
        Convert the HDL description to Verilog
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

###############################################################################
# A synthesizable FIR filter.
class Delay(Module):
    def __init__(self):
        p = fb.fil[0]['fxqc']
        # ------------- Define I/Os -------------------------------------------
        ovfl_o = p['QO']['ovfl']
        quant_o = p['QO']['quant']

        self.WI = p['QI']['W']
        self.WO = p['QO']['W']
        N = len(p['QC']['b']) - 1 # number of coefficients = Order + 1
        # ------------- Define I/Os -------------------------------------------
        self.i = Signal((self.WI, True)) # input signal
        self.o = Signal((self.WO, True)) # output signal
        MIN_o = - 1 << (self.WO - 1)
        MAX_o = -MIN_o - 1

        src = self.i
        for c in range(N):
            sreg = Signal((self.WI, True)) # registers for input signal 
            self.sync += sreg.eq(src)
            src = sreg
#        sum_full = Signal((p['QA']['W'], True))
#        self.comb += self.o.eq(sreg >> (WI-WO)) # rescale for output width

#        delayed = Signal((self.WI, True))
#        delayed_q = Signal((self.WI, True))
#        if quant_o == 'round':
#            self.comb += delayed_q.eq(delayed + (1 << (self.WO - 1)))
#        else:
#            self.comb += delayed_q.eq(delayed)        
#        if ovfl_o == 'wrap':
#            self.comb += self.o.eq(delayed_q >> (self.WI-self.WO)) # rescale for output width
#        else:
#            self.comb += \
#                If(delayed_q[self.WO-2:] == 0b10,
#                    self.o.eq(MIN_o)
#                ).Elif(delayed_q[self.WO-2:] == 0b01,
#                    self.o.eq(MAX_o)
#                ).Else(self.o.eq(delayed_q >> (self.WI-self.WO-1))
#                )
#
#        self.comb += self.o.eq(self.i) # rescale for output width
            
        self.comb += self.o.eq(self.test(self.i))
        
    def test(self, sig_in):
        MIN_o = - 1 << (self.WO - 1) 
        sig_o = Signal((self.WO, True))
        self.comb += sig_o.eq(sig_in)
        return sig_o

    def sat_quant(self, sig_in, quant_o, ovfl_o):
        MIN_o = - 1 << (self.WO - 1)
        MAX_o = -MIN_o - 1

        sig_in_q = Signal((self.WI, True))
        sig_o = Signal((self.WO, True))
        if quant_o == 'round':
            self.comb += sig_in_q.eq(sig_in + (1 << (self.WO - 1)))
        else:
            self.comb += sig_in_q.eq(sig_in)        
        if ovfl_o == 'wrap':
            self.comb += sig_o.eq(sig_in_q >> (self.WI-self.WO)) # rescale for output width
        else:
            self.comb += \
                If(sig_o[self.WO-2:] == 0b10,
                    sig_o.eq(MIN_o)
                ).Elif(sig_o[self.WO-2:] == 0b01,
                    sig_o.eq(MAX_o)
                ).Else(sig_o.eq(sig_in_q >> (self.WI-self.WO-1))
                )
        return sig_o

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = Delay_wdg(None)
    mainw.show()

    app.exec_()
    
    # test using "python -m pyfda.fixpoint_filters.delay1"