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
#from pyfda.filter_blocks.fda import fir
  

# =============================================================================

class FIR_DF(QWidget):
    """
    Widget for entering word formats & quantization, also instantiates fixpoint
    filter class :class:`FilterFIR`.
    """
    def __init__(self, parent):
        super(FIR_DF, self).__init__(parent)

        self.title = ("<b>Direct-Form (DF) FIR Filter</b><br />"
                      "Standard FIR topology.")
        self.img_name = "fir_df.png"

        self._construct_UI()
        # Construct an instance of the HDL filter object
        self.hdlfilter = FilterFIR()
        #self.hdlfilter = fir.FilterFIR()
#------------------------------------------------------------------------------

    def _construct_UI(self):
        """
        Intitialize the UI with widgets for coefficient format and input and 
        output quantization
        """
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
#------------------------------------------------------------------------------

        layVWdg = QVBoxLayout()
        layVWdg.setContentsMargins(0,0,0,0)
        
        layVWdg.addWidget(self.wdg_w_coeffs)
        layVWdg.addWidget(self.wdg_q_coeffs)

        layVWdg.addWidget(self.wdg_w_accu)
        layVWdg.addWidget(self.wdg_q_accu)

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
        fxqc_dict = {}    
        fxqc_dict.update({'QC':self.wdg_w_coeffs.c_dict})
        
        fxqc_dict.update({'QA': self.wdg_w_accu.ui2dict()})
        
        return fxqc_dict
        
#------------------------------------------------------------------------------
#    def update_hdl_filter(self, fxqc_dict=None):
#        """
#        This is called from :class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs`.
#        
#        Update the HDL filter object with new coefficients, quantization settings etc. when
#        
#        - it is constructed
#        
#        - filter design and hence coefficients change
#        
#        - quantization settings are updated in this widget
#        
#        TODO: outdated, check coefficient passing mechanism!
#        """
#
#        # build the dict with coefficients and fixpoint settings:
#        self.hdl_dict = self.get_hdl_dict()
#        # setup input and output quantizers
##        self.q_i = fx.Fixed(self.hdl_dict['QI']) # setup quantizer for input quantization
##        self.q_i.setQobj({'frmt':'dec'})#, 'scale':'int'}) # use integer decimal format
#        self.q_o = fx.Fixed(self.hdl_dict['QO']) # setup quantizer for output quantization
#
#        b = [ int(x) for x in self.hdl_dict['QC']['b']] # convert np.int64 to python int
#
#        # call setup method of filter widget - this is not implemented (yet)
#        # self.fx_wdg_inst.setup_HDL(self.hdl_dict)
#        
#        self.hdlfilter.set_coefficients(coeff_b = b)  # Coefficients for the filter
#
#        # pass wordlength for coeffs, input, output
#        # TODO: directly pass the hdl_dict here:
#        self.hdlfilter.set_word_format(
#                (self.hdl_dict['QC']['W'], self.hdl_dict['QC']['WI'], self.hdl_dict['QC']['WF']),
#                (self.hdl_dict['QI']['W'], self.hdl_dict['QI']['WI'], self.hdl_dict['QI']['WF']),
#                (self.hdl_dict['QO']['W'], self.hdl_dict['QO']['WI'], self.hdl_dict['QO']['WF'])
#                )

###############################################################################
        
class FilterFIR(FilterHardware): # from filter_blocks.fda.fir
    def __init__(self, b = None, a = None):
        """
        Contains FIR filter parameters. Parent Class : FilterHardware

        Arguments
        ---------
        
        b (list of int): list of numerator coefficients.
        a (list of int): list of denominator coefficients.
        word format (tuple of int): (W, WI, WF)
            
        response (list): list of filter output in int format.
        """
        super(FilterFIR, self).__init__(b, a)
        self.response = []

    def get_response(self):
        """
        Return filter output.

        Returns
        -------
        response(numpy int array) : returns filter output as numpy array
        """
        return self.response
            
    def run_sim(self):
        """
        Run filter simulation
        """

        testfil = self.filter_block()
        testfil.run_sim() # -> myhdl/_block


    def convert(self, **kwargs):
        """
        Convert the HDL description to Verilog and VHDL.
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

            fir = filter_fir(glbl, sigin, sigout, self.b, self.coef_word_format,
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
        and implementations. This will be handled by individual classes / blocks now.
        
        Check myhdl._block for how to use attributes etc
        """

        w_in = self.input_word_format
        w_out = self.output_word_format
        imax = 1 << (w_in[0]-1)
        omax = 1 << (w_out[0]-1)

        xt = Samples(min=-imax, max=imax, word_format=self.input_word_format)
        yt = Samples(min=-omax, max=omax, word_format=self.output_word_format)
        xt.valid = bool(1)
        clock = Clock(0, frequency=50e6)
        reset = Reset(1, active=0, async=True)
        glbl = Global(clock, reset)
        tbclk = clock.process()
        
        #process to record output in buffer
        _t = yt.process_record(clock, num_samples=len(self.sigin)) # was: rec_insts = ...
        
        # was: filter_insts, it seems the assigned name doesn't matter?!
        _ = filter_fir(glbl, xt, yt, self.b, self.coef_word_format) # was: filter_insts = ...

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

            logger.warning("samp_bufy : {0}".format(yt.sample_buffer))
            self.response = yt.sample_buffer

            raise StopSimulation()

        return hdl.instances()
############################################################################### 
@hdl.block
def filter_fir(glbl, sigin, sigout, b, coef_w, shared_multiplier=False):
    """
    Basic FIR direct-form filter.

    Ports:
        glbl (Global): global signals.
        sigin (Samples): input digital signal.
        sigout (Samples): output digital signal.

    Arguments
    ---------
        b (tuple): numerator coefficents.

    Returns
    -------
        inst (myhdl.Block, list):
    """
    assert isinstance(sigin, Samples)
    assert isinstance(sigout, Samples)
    assert isinstance(b, tuple)
    # All the coefficients need to be an `int`
    rb = [isinstance(bb, int) for bb in b]
    assert all(rb)

    w_in = sigin.word_format
    w_out = sigout.word_format
    ntaps = len(b)-1
    xmax = 2 ** (w_in[0]-1)
    ymax = 2 ** (w_out[0]-1)
    sum_abs_b = (sum([abs(x) for x in b]))/2.**(coef_w[0]-1) # coefficient area
    # S + w_in-1 + w_c-1 + coeff. area
    acc_wl = w_in[0] + coef_w[0] -1 + math.ceil(math.log(sum_abs_b, 2))
    amax = 2**(acc_wl-1)
    q = acc_wl-w_out[0]

    if q < 0:
        q = 0

    clock, reset = glbl.clock, glbl.reset
    xdv = sigin.valid
    y, ydv = sigout.data, sigout.valid
    x = Signal(intbv(0, min=-xmax, max=xmax))
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
        y.next = yacc[acc_wl:q].signed()
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