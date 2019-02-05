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
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
import logging
logger = logging.getLogger(__name__)

#import numpy as np
import math
import pyfda.filterbroker as fb

from ..compat import QWidget, QLabel, QVBoxLayout, QHBoxLayout

import pyfda.pyfda_fix_lib as fx
from .fixpoint_helpers import UI_W, UI_W_coeffs, UI_Q, UI_Q_coeffs

import myhdl as hdl
from myhdl import Signal, intbv, always_seq, StopSimulation
from .support import Clock, Reset, Global, Samples, Signals
from .filter_hw import FilterHardware
  

# =============================================================================

class FIR_DF(QWidget):
    """
    Widget for entering word formats & quantization
    """
    def __init__(self, parent):
        super(FIR_DF, self).__init__(parent)

        self.title = ("<b>Direct-Form 1 (DF1) FIR Filter</b><br />"
                 "Simple topology.")
        self.img_name = "fir_df.png"

        self._construct_UI()
        self.construct_hdl_filter()

#------------------------------------------------------------------------------

    def _construct_UI(self):
        """
        Intitialize the UI with widgets for coefficient format and input and 
        output quantization
        """
        
        lblHBtnsMsg = QLabel("<b>Fixpoint signal / coeff. formats as WI.WF:</b>", self)
        self.layHBtnsMsg = QHBoxLayout()
        self.layHBtnsMsg.addWidget(lblHBtnsMsg)

        self.wdg_w_input = UI_W(self, label='Input Format <i>Q<sub>X </sub></i>:')
        self.wdg_q_input = UI_Q(self)
        
        self.wdg_w_coeffs = UI_W_coeffs(self, label='Coefficient Format:', enabled=False,
                                        tip_WI='Number of integer bits - edit in the "b,a" tab',
                                        tip_WF='Number of fractional bits - edit in the "b,a" tab',
                                        WI = fb.fil[0]['q_coeff']['WI'],
                                        WF = fb.fil[0]['q_coeff']['WF'])
        self.wdg_q_coeffs = UI_Q_coeffs(self, enabled=False,
                                        cur_ov=fb.fil[0]['q_coeff']['ovfl'], 
                                        cur_q=fb.fil[0]['q_coeff']['quant'])
        self.wdg_w_accu = UI_W(self, label='Accumulator Format <i>Q<sub>A </sub></i>:', WF=30)
        self.wdg_q_accu = UI_Q(self)
        self.wdg_w_output = UI_W(self, label='Output Format <i>Q<sub>Y </sub></i>:')
        self.wdg_q_output = UI_Q(self)
#------------------------------------------------------------------------------

        layVWdg = QVBoxLayout()
        layVWdg.setContentsMargins(0,0,0,0)

        layVWdg.addLayout(self.layHBtnsMsg)

        layVWdg.addWidget(self.wdg_w_input)
        layVWdg.addWidget(self.wdg_q_input)
        
        layVWdg.addWidget(self.wdg_w_coeffs)
        layVWdg.addWidget(self.wdg_q_coeffs)

        layVWdg.addWidget(self.wdg_w_accu)
        layVWdg.addWidget(self.wdg_q_accu)

        layVWdg.addWidget(self.wdg_w_output)
        layVWdg.addWidget(self.wdg_q_output)

        layVWdg.addStretch()

        self.setLayout(layVWdg)
        
#------------------------------------------------------------------------------
    def construct_hdl_filter(self):
        """
        Construct an instance of the HDL filter object
        """
        self.hdlfilter = FilterFIR()     # Standard DF1 filter - hdl_dict should be passed here

#------------------------------------------------------------------------------
    def update_hdl_filter(self):
        """
        TODO: move this to the filter class!
        
        Update the HDL filter object with new coefficients, quantization settings etc. when
        
        - it is constructed
        
        - filter design and hence coefficients change
        
        - quantization settings are updated in this widget
        """

        # build the dict with coefficients and fixpoint settings:
        self.hdl_dict = self.get_hdl_dict()
        # setup input and output quantizers
        self.q_i = fx.Fixed(self.hdl_dict['QI']) # setup quantizer for input quantization
        self.q_i.setQobj({'frmt':'dec'})#, 'scale':'int'}) # use integer decimal format
        self.q_o = fx.Fixed(self.hdl_dict['QO']) # setup quantizer for output quantization

        b = [ int(x) for x in self.hdl_dict['QC']['b']] # convert np.int64 to python int

        # call setup method of filter widget - this is not implemented (yet)
        # self.fx_wdg_inst.setup_HDL(self.hdl_dict)
        
        self.hdlfilter.set_coefficients(coeff_b = b)  # Coefficients for the filter

        # pass wordlength for coeffs, input, output
        # TODO: directly pass the hdl_dict here:
        self.hdlfilter.set_word_format(
                (self.hdl_dict['QC']['W'], self.hdl_dict['QC']['WI'], self.hdl_dict['QC']['WF']),
                (self.hdl_dict['QI']['W'], self.hdl_dict['QI']['WI'], self.hdl_dict['QI']['WF']),
                (self.hdl_dict['QO']['W'], self.hdl_dict['QO']['WI'], self.hdl_dict['QO']['WF'])
                )

#------------------------------------------------------------------------------
    def update_UI(self):
        """
        Update all parts of the UI that need to be updated when specs have been
        changed outside this class, e.g. coefficients and coefficient wordlength.

        This is called from one level above by 
        :class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs`.
        """
        self.wdg_w_coeffs.load_ui() # update coefficient wordlength
        self.wdg_q_coeffs.load_ui() # update coefficient quantization settings

#==============================================================================
    def get_hdl_dict(self):
        """
        Build the dictionary for passing infos to the fixpoint implementation
        for coefficients, input and output quantization.
        
        Parameters
        ----------
        
        None
        
        Returns
        -------
        hdl_dict : dict

           containing the following keys:

               :'QC': dictionary with coefficients quantization settings
               
               :'QI': dictionary with input quantizer settings
               
               :'QO': dictionary with output quantizer settings
        """
        # quantized coefficients in decimal format
        hdl_dict = {'QC':self.wdg_w_coeffs.c_dict}
        # input quantization parameters
        hdl_dict.update({'QI':{'WI':self.wdg_w_input.WI,
                               'WF':self.wdg_w_input.WF,
                               'W':self.wdg_w_input.W,
                               'ovfl': self.wdg_q_input.ovfl,
                               'quant': self.wdg_q_input.quant
                               }
                        })
        # output quantization parameters
        hdl_dict.update({'QO':{'WI':self.wdg_w_output.WI,
                               'WF':self.wdg_w_output.WF,
                               'W':self.wdg_w_output.W,
                               'ovfl': self.wdg_q_output.ovfl,
                               'quant': self.wdg_q_output.quant
                               }
                        })
    
        return hdl_dict
    
###############################################################################
        
class FilterFIR(FilterHardware): # from filter_blocks.fda.fir
    def __init__(self, b = None, a = None):
        """Contains FIR filter parameters. Parent Class : FilterHardware
            Args:
                b (list of int): list of numerator coefficients.
                a (list of int): list of denominator coefficients.
                word format (tuple of int): (W, WI, WF)
                filter_type:
                filter_form_type:
                response (list): list of filter output in int format.
            """
        super(FilterFIR, self).__init__(b, a)
        self.filter_type = 'direct_form'
        self.direct_form_type = 1
        self.response = []


    def get_response(self):
        """Return filter output.

        returns:
            response(numpy int array) : returns filter output as numpy array
        """
        return self.response

    def run_sim(self):
        """Run filter simulation"""

        testfil = self.filter_block()
        testfil.run_sim()


    def convert(self, **kwargs):
        """Convert the HDL description to Verilog and VHDL.
        """
        w = self.input_word_format
        w_out = self.output_word_format
        omax = 2**(w_out[0]-1)
        imax = 2**(w[0]-1)

        # small top-level wrapper
        def filter_fir_top(hdl , clock, reset, x, xdv, y, ydv):
            sigin = Samples(x.min, x.max, self.input_word_format)
            sigin.data, sigin.data_valid = x, xdv
            sigout = Samples(y.min, y.max, self.output_word_format)
            sigout.data, sigout.data_valid = y, ydv
            clk = clock
            rst = reset
            glbl = Global(clk, rst)
            
            #choose appropriate filter
            fir_hdl = filter_fir

            fir = fir_hdl(glbl, sigin, sigout, self.b, self.coef_word_format,
                          shared_multiplier=self._shared_multiplier)
            
            fir.convert(**kwargs)


        clock = Clock(0, frequency=50e6)
        reset = Reset(1, active=0, async=True)
        x = Signal(intbv(0, min=-imax, max=imax))
        y = Signal(intbv(0, min=-omax, max=omax))
        xdv, ydv = Signal(bool(0)), Signal(bool(0))
        

        if self.hdl_target.lower() == 'verilog':
            filter_fir_top(hdl, clock, reset, x, xdv, y, ydv)
 
        elif self.hdl_target.lower() == 'vhdl':
            filter_fir_top(hdl, clock, reset, x, xdv, y, ydv)
        else:
            raise ValueError('incorrect target HDL {}'.format(self.hdl_target))


    @hdl.block
    def filter_block(self):
        """
        This elaboration code was supposed to select the different structure 
        and implementations
        
        This will be handled by individual classes / blocks now.
        """

        w = self.input_word_format
        w_out = self.output_word_format
        #print(self.input_word_format)
        #print(self.coef_word_format)
        ymax = 2**(w[0]-1)
        vmax = 2**(2*w[0])
        omax = 2**(w_out[0]-1)
        xt = Samples(min=-ymax, max=ymax, word_format=self.input_word_format)
        yt = Samples(min=-omax, max=omax, word_format=self.output_word_format)
        #yt = Samples(min=-vmax, max=vmax)
        xt.valid = bool(1)
        clock = Clock(0, frequency=50e6)
        reset = Reset(1, active=0, async=True)
        glbl = Global(clock, reset)
        tbclk = clock.process()
        numsample = 0
        
        # set numsample 
        numsample = len(self.sigin)
        #process to record output in buffer
        rec_insts = yt.process_record(clock, num_samples=numsample)

        dfilter = filter_fir

        @hdl.instance
        def stimulus():
            "record output in numpy array yt.sample_buffer"
            for k in self.sigin:
                xt.data.next = int(k)
                xt.valid = bool(1)

                yt.record = True
                yt.valid = True
                yield clock.posedge
                #Collect a sample from each filter
                yt.record = False
                yt.valid = False

            print(yt.sample_buffer)
            self.response = yt.sample_buffer

            raise StopSimulation()

        return hdl.instances()
############################################################################### 
@hdl.block
def filter_fir(glbl, sigin, sigout, b, coef_w, shared_multiplier=False):
    """Basic FIR direct-form filter.

    Ports:
        glbl (Global): global signals.
        sigin (Samples): input digital signal.
        sigout (Samples): output digitla signal.

    Args:
        b (tuple): numerator coefficents.

    Returns:
        inst (myhdl.Block, list):
    """
    assert isinstance(sigin, Samples)
    assert isinstance(sigout, Samples)
    assert isinstance(b, tuple)
    # All the coefficients need to be an `int`
    rb = [isinstance(bb, int) for bb in b]
    assert all(rb)

    w = sigin.word_format
    w_out = sigout.word_format
    ntaps = len(b)-1
    ymax = 2 ** (w[0]-1)
    sum_abs_b = (sum([abs(x) for x in b]))/2.**(coef_w[0]-1)
    acc_bits = w[0] + coef_w[0] + math.ceil(math.log(sum_abs_b, 2))
    amax = 2**(acc_bits-1)
    qd = acc_bits
    q = acc_bits-w_out[0]

    if q < 0:
        q = 0

    clock, reset = glbl.clock, glbl.reset
    xdv = sigin.valid
    y, ydv = sigout.data, sigout.valid
    x = Signal(intbv(0, min=-ymax, max=ymax))
    # Delay elements, list-of-signals
    ffd = Signals(intbv(0, min=-ymax, max=ymax), ntaps)
    yacc = Signal(intbv(0, min=-amax, max=amax))
    dvd = Signal(bool(0))

    @hdl.always(clock.posedge)
    def beh_direct_form_one():
        if sigin.valid:
            x.next = sigin.data

            for i in range(ntaps-1):
                ffd[i+1].next = ffd[i]

            ffd[0].next = x
            # sum-of-products loop
            c = b[0]
            sop = x * c

            for ii in range(ntaps):
                c = b[ii+1]
                sop = sop + (c * ffd[ii])
            yacc.next = sop

    @always_seq(clock.posedge, reset=reset)
    def beh_output():
        dvd.next = xdv
        y.next = yacc[qd:q].signed()
        ydv.next = dvd

    return beh_direct_form_one, beh_output

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = FIR_DF(None)
    mainw.show()

    app.exec_()
    
    # test using "python -m pyfda.fixpoint_widgets.fir_df1"