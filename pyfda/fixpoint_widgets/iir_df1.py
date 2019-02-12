# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for specifying the parameters of a direct-form 1 (DF1) IIR filter
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
# if cmp_version("myhdl", "0.10") >= 0:
#     import myhdl
#     HAS_MYHDL = True
# 
#     fil_blocks_path = os.path.abspath(os.path.join(dirs.INSTALL_DIR, '../../filter-blocks'))
#     if not os.path.exists(fil_blocks_path):
#         logger.error("Invalid path {0}".format(fil_blocks_path))
#     else:
#         if fil_blocks_path not in sys.path:
#             sys.path.append(fil_blocks_path)
#         from pyfda.filter_blocks.fda.fir import FilterFIR
#         from pyfda.filter_blocks.fda.iir import FilterIIR    
# else:
#     HAS_MYHDL = False
# =============================================================================

class IIR_DF1(QWidget):
    """
    Widget for entering word formats & quantization
    """
    def __init__(self, parent):
        super(IIR_DF1, self).__init__(parent)

        self.title = ("<b>Direct-Form 1 (DF1) IIR Filter</b><br />"
                 "Simple topology, not suitable for higher orders.")
        self.img_name = "iir_df1.png"

        self._construct_UI()
        self.construct_hdl_filter()

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
    def construct_hdl_filter(self):
        """
        Construct an instance of the HDL filter object
        """
        self.hdlfilter = FilterIIR()     # Standard DF1 filter

#------------------------------------------------------------------------------
    def update_hdl_filter(self):
        """
        Update the HDL filter object with new coefficients, quantization settings etc. when
        
        - it is constructed
        
        - filter design and hence coefficients change
        
        - quantization settings are updated in this widget
        """
        # setup input and output quantizers
        self.q_i = fx.Fixed(self.hdl_dict['QI']) # setup quantizer for input quantization
        self.q_i.setQobj({'frmt':'dec'})#, 'scale':'int'}) # use integer decimal format
        self.q_o = fx.Fixed(self.hdl_dict['QO']) # setup quantizer for output quantization

        b = [ int(x) for x in self.hdl_dict['QC']['b']] # convert np.int64 to python int
        a = [ int(x) for x in self.hdl_dict['QC']['a']] # convert np.int64 to python int

        # call setup method of filter widget - this is not implemented (yet)
        # self.fx_wdg_inst.setup_HDL(self.hdl_dict)
        
        self.hdlfilter.set_coefficients(coeff_b = b, coeff_a = a)  # Coefficients for the filter

        # pass wordlength for coeffs, input, output
        # TODO: directly pass the hdl_dict here:
        self.hdlfilter.set_word_format(
                (self.hdl_dict['QC']['W'], self.hdl_dict['QC']['WI'], self.hdl_dict['QC']['WF']),
                (self.hdl_dict['QI']['W'], self.hdl_dict['QI']['WI'], self.hdl_dict['QI']['WF']),
                (self.hdl_dict['QO']['W'], self.hdl_dict['QO']['WI'], self.hdl_dict['QO']['WF'])
                )

#------------------------------------------------------------------------------
    def dict2ui(self, fxqc_dict):
        """
        Update all parts of the UI that need to be updated when specs have been
        changed outside this class, e.g. coefficients and coefficient wordlength.

        This is called from one level above by 
        :class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs`.
        """
        if not 'QA' in fxqc_dict:
            fxqc_dict.update({'QA':{}}) # no accumulator settings in dict yet 
            
        if not 'QC' in fxqc_dict:
            fxqc_dict.update({'QC':{}}) # no coefficient settings in dict yet 

        self.wdg_w_coeffs.dict2ui(fxqc_dict['QC']) # update coefficient wordlength in ui
        self.wdg_q_coeffs.dict2ui(fxqc_dict['QC']) # update coefficient quantization settings
        
        self.wdg_w_accu.dict2ui(fxqc_dict['QA']) # update accumulator wordlength in ui
        self.wdg_q_accu.dict2ui(fxqc_dict['QA']) # update accumulator quantization settings


#==============================================================================
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
        # quantized coefficients in decimal format
        fxqc_dict = {'QC':self.wdg_w_coeffs.c_dict}
    
        return fxqc_dict

###############################################################################
        
# was: from pyfda.filter_blocks.fda.iir
class FilterIIR(FilterHardware):
    def __init__(self, b = None, a = None):
        """
        Contains IIR filter parameters. Parent Class : FilterHardware
        
        Arguments
        ---------
        b (list of int): list of numerator coefficients.
        a (list of int): list of denominator coefficients.
        word format (tuple of int): (W, WI, WF)
        filter_type:
        filter_form_type:
        response(list): list of filter output in int format.
            """
        super(FilterIIR, self).__init__(b, a)
        #self.filter_type = 'direct_form'
        #self.direct_form_type = 1
        self.response = []

    def get_response(self):
        """Return filter output.

        Returns:
            response(numpy int array) : returns filter output as
            numpy array
        """
        return self.response

    def run_sim(self):
        """Run filter simulation"""

        testfil = self.filter_block()
        #testfil.config_sim(trace=True)
        testfil.run_sim()

    def convert(self, **kwargs):
        """Convert the HDL description to Verilog and VHDL.
        """
        w = self.input_word_format
        w_out = self.output_word_format
        omax = 2**(w_out[0]-1)
        imax = 2**(w[0]-1)

        # small top-level wrapper
        def filter_iir_top(hdl , clock, reset, x, xdv, y, ydv):
            sigin = Samples(x.min, x.max, self.input_word_format)
            sigin.data, sigin.data_valid = x, xdv
            sigout = Samples(y.min, y.max, self.output_word_format)
            sigout.data, sigout.data_valid = y, ydv
            clk = clock
            rst = reset
            glbl = Global(clk, rst)
            
            # choose appropriate filter
            iir_hdl = filter_iir

            iir = iir_hdl(
                glbl, sigin, sigout, self.b, self.a, self.coef_word_format,
                shared_multiplier=self._shared_multiplier
            )
            iir.convert(**kwargs)

        clock = Clock(0, frequency=50e6)
        reset = Reset(1, active=0, async=True)
        x = Signal(intbv(0, min=-imax, max=imax))
        y = Signal(intbv(0, min=-omax, max=omax))
        xdv, ydv = Signal(bool(0)), Signal(bool(0))
        

        if self.hdl_target.lower() == 'verilog':
            filter_iir_top(hdl, clock, reset, x, xdv, y, ydv)
 
        elif self.hdl_target.lower() == 'vhdl':
            filter_iir_top(hdl, clock, reset, x, xdv, y, ydv)
        else:
            raise ValueError('incorrect target HDL {}'.format(self.hdl_target))

    @hdl.block
    def filter_block(self):
        """
        This elaboration code was supposed to select the different structure 
        and implementations. This will be handled by individual classes / blocks now.
        
        Check myhdl._block for how to use attributes etc
        """
        w = self.input_word_format
        w_out = self.output_word_format
        
        ymax = 2**(2*w[0]-1)
        vmax = 2**(2*w[0])
        omax = 2**(w_out[0]-1)
        xt = Samples(min=-ymax, max=ymax, word_format=self.input_word_format)
        yt = Samples(min=-omax, max=omax, word_format=self.output_word_format)
        xt.valid = bool(1)
        clock = Clock(0, frequency=50e6)
        reset = Reset(1, active=0, async=True)
        glbl = Global(clock, reset)
        tbclk = clock.process()
        
        _t = yt.process_record(clock, num_samples=len(self.sigin)) # was: rec_insts = ...

        _ = filter_iir(glbl, xt, yt, self.b, self.a, self.coef_word_format)


        @hdl.instance
        def stimulus():
            """record output in numpy array yt.sample_buffer"""
            for k in self.sigin:
                xt.data.next = int(k)
                xt.valid = bool(1)

                yt.record = True
                yt.valid = True
                yield clock.posedge
                # Collect a sample from each filter
                yt.record = False
                yt.valid = False

            self.response = yt.sample_buffer

            raise StopSimulation()

        return hdl.instances()

###############################################################################
# was: from filter_blocks.iir.iir_df1.py
@hdl.block
def filter_iir(glbl, sigin, sigout, b, a, coef_w, shared_multiplier=False):
    """
    Basic IIR direct-form I filter.
    
    Ports:
        glbl (Global): global signals.
        sigin (SignalBus): input digital signal.
        sigout (SignalBus): output digital signal.

    Arguments
    ---------
        b (tuple): numerator coefficents of type ``int`` (not numpy.int32 etc).
        a (tuple): denominator coefficents of type ``int`` (not numpy.int32 etc).
    Returns
    -------
        inst (myhdl.Block, list):
    """
    assert isinstance(sigin, Samples)
    assert isinstance(sigout, Samples)
    assert isinstance(b, tuple)
    assert isinstance(a, tuple)

    # All the coefficients need to be an `int`

    rb = [isinstance(bb, int) for bb in b]
    ra = [isinstance(aa, int) for aa in a]
    assert all(rb)
    assert all(ra)

    w = sigin.word_format
    w_out = sigout.word_format

    ymax = 2 ** (w[0] - 1)
    vmax = 2 ** (2 * w[0])  # top bit is guard bit
    # max without guard bit. Value at which output will saturate

    N = len(b) - 1
    clock, reset = glbl.clock, glbl.reset
    xdv = sigin.valid
    y, ydv = sigout.data, sigout.valid
    x, xdv = sigin.data, sigin.valid



    ######### method 1 for calculating accumulator

    # amax = 2 ** (2 * w[0] - 1)

    # q, qd = w[0], 2 * w[0]  # guard bit not fed back
    # q = 0 if q < 0 else q

    # # guard bit not passed to output
    # o, od = 2 * w[0] - w_out[0], 2 * w[0]
    # o = 0 if o < 0 else o
    # yacc = Signal(intbv(0, min=-vmax, max=vmax))  # verify the length of this

    #########


    ########## method 2 of calculating accumulator size based on fir filter implementation

    acc_bits = w[0] + coef_w[0] + math.floor(math.log(N, 2))

    amax = 2**(acc_bits-1)
    od = acc_bits - 1
    o = acc_bits-w_out[0] - 1
    o = 0 if o < 0 else o
    q, qd = acc_bits - w[0] -1 , acc_bits -1
    q = 0 if q < 0 else q

    yacc = Signal(intbv(0, min=-amax, max=amax))

    ##########

    # Delay elements, list-of-signals
    ffd = Signals(intbv(0, min=-ymax, max=ymax), N)
    fbd = Signals(intbv(0, min=-ymax, max=ymax), N)
    

    dvd = Signal(bool(0))
    overflow = Signal(bool(0)) 
    underflow = Signal(bool(0))

    @hdl.always(clock.posedge)
    def beh_direct_form_one():
        if sigin.valid:

            for i in range(N - 1):
                ffd[i + 1].next = ffd[i]
                fbd[i + 1].next = fbd[i]

            ffd[0].next = x
            fbd[0].next = yacc[qd:q].signed()

    @hdl.always_comb
    def beh_acc():
        c = b[0]
        sop = x * c


        for ii in range(N):
            c = b[ii + 1]  # first element in list in b0
            d = a[ii + 1]  # first element in list is a0 =1
            sop = sop + (c * ffd[ii]) - (d * fbd[ii])

        if overflow:
            yacc.next = amax-1

        if underflow:
            yacc.next = -amax

        else:
            yacc.next = sop


    @always_seq(clock.posedge, reset=reset)
    def beh_output():
        dvd.next = xdv
        # y.next = yacc[od:o].signed()

        if (yacc[qd] == 1 and yacc[qd - 1] == 1) or (yacc[qd] == 0 and yacc[qd - 1] == 0):
            ydv.next = dvd
            y.next = yacc[od:o].signed()
            overflow = 0
            underflow = 0

        elif yacc[qd] == 1 and yacc[qd-1] == 0:
            y.next = -amax
            ydv.next = dvd
            underflow = 1
            print('underflow')


        elif yacc[qd] == 0 and yacc[qd - 1] == 1:
            y.next = amax - 1
            ydv.next = dvd
            overflow = 1
            print('overflow')

    return hdl.instances()
#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = IIR_DF1(None)
    mainw.show()

    app.exec_()
    
    # test using "python -m pyfda.fixpoint_widgets.iir_df1"