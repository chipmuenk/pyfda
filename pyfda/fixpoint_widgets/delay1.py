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
from migen import Signal, Module, run_simulation
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
        self.construct_hdlfilter()
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
    def construct_hdlfilter(self):
        """
        Construct an instance of the HDL filter object using the settings from
        the quantizer dict
        """
        self.hdlfilter = Delay() # construct HDL filter instance
#------------------------------------------------------------------------------
    def to_verilog(self):
        """
        Convert the HDL description to Verilog
        """
        return verilog.convert(self.hdlfilter,
                               ios={self.hdlfilter.i, self.hdlfilter.o}) 
#------------------------------------------------------------------------------

    def fir_tb_stim(self, stimulus, inputs, outputs):
        """ use stimulus list from widget as input to filter """
        for x in stimulus:
            yield self.hdlfilter.i.eq(int(x)) # pass one stimulus value to filter
            inputs.append(x) # and append it to input list
            outputs.append((yield self.hdlfilter.o)) # append filter output to output list
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
        
        testbench = self.fir_tb_stim(stimulus, inputs, response) 
            
        run_simulation(self.hdlfilter, testbench)
        
        return response
###############################################################################

###############################################################################
# A synthesizable FIR filter.
class Delay(Module):
    def __init__(self):
        p = fb.fil[0]['fxqc']
        logger.debug(p)

        # ------------- Define I/Os -------------------------------------------
        self.i = Signal((p['QI']['W'], True)) # input signal
        self.o = Signal((p['QO']['W'], True)) # output signal
        self.response = []

        src = self.i
        for c in range(3):
            sreg = Signal((p['QI']['W'], True)) # registers for input signal 
            self.sync += sreg.eq(src)
            src = sreg
#        sum_full = Signal((p['QA']['W'], True))
        self.comb += self.o.eq(sreg >> (p['QI']['W']-p['QO']['W'])) # rescale for output width

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = Delay_wdg(None)
    mainw.show()

    app.exec_()
    
    # test using "python -m pyfda.fixpoint_filters.delay1"