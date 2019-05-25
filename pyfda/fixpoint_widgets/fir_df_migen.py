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

import math
import pyfda.filterbroker as fb

from ..compat import QWidget, QLabel, QVBoxLayout, QHBoxLayout

import pyfda.pyfda_fix_lib as fx
from .fixpoint_helpers import UI_W, UI_W_coeffs, UI_Q, UI_Q_coeffs

#####################
from functools import reduce
from operator import add

from math import cos, pi
#from scipy import signal
#import matplotlib.pyplot as plt

from migen import *
from migen.fhdl import verilog
################################

classes = {'FIR_DF':'DF'} #: Dict containing class name : display name

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
    def construct_hdl_filter(self):
        """
        Construct an instance of the HDL filter object
        """
        #b = self.hdl_dict['QC']['b']
        self.hdlfilter = FIR()     # Standard DF1 filter - hdl_dict should be passed here


###############################################################################
# A synthesizable FIR filter.
class FIR(Module):
    def __init__(self, coef=[12,14,16], wsize=16):
        self.coef = coef
        self.wsize = wsize
        self.i = Signal((self.wsize, True))
        self.o = Signal((self.wsize, True))
        self.response = []

        ###
        muls = []
        src = self.i
        for c in self.coef:
            sreg = Signal((self.wsize, True))
            self.sync += sreg.eq(src)
            src = sreg
            #c_fp = int(c*2**(self.wsize - 1))
            c_fp = c
            muls.append(c_fp*sreg)
        sum_full = Signal((2*self.wsize-1, True))
        self.sync += sum_full.eq(reduce(add, muls))
        self.comb += self.o.eq(sum_full >> self.wsize-1)
        
    def setup(self, fx_dict):
        logger.warning("fx_dict = {0}".format(fx_dict))


    def get_response(self):
        """
        Return filter output.

        Returns
        -------
        response(numpy int array) : returns filter output as numpy array
        """
        return self.response
            
    def set_stimulus(self, stimulus, outputs):
        """
        Run filter simulation
        """
        self.response = []
        for x in stimulus:
            #v = 0.1*cos(2*pi*frequency*cycle)
            yield FIR_DF.hdlfilter.i.eq(x)
            self.response.append((yield FIR_DF.hdlfilter.o))
            yield
            
    def convert(self, **kwargs):
        """
        Convert the HDL description to Verilog or VHDL.
        """
        fir = FIR()
        if True:
            logger.info(verilog.convert(fir, ios={fir.i, fir.o}))       
        else:
            raise ValueError('incorrect target HDL {}'.format(self.hdl_target))


# A test bench for our FIR filter.
# Generates a sine wave at the input and records the output.
def fir_tb(dut, frequency, inputs, outputs):
    f = 2**(dut.wsize - 1)
    for cycle in range(200):
        v = 0.1*cos(2*pi*frequency*cycle)
        yield dut.i.eq(int(f*v))
        inputs.append(v)
        outputs.append((yield dut.o)/f)
        yield

def convert(self, **kwargs):
    """
    Convert the HDL description to Verilog and VHDL.
    """
    fir = FIR(self.b)
    print(verilog.convert(fir, ios={fir.i, fir.o}))       
    if self.hdl_target.lower() == 'verilog':
        filter_fir_top(hdl, clock, reset, x, xdv, y, ydv)
 
    elif self.hdl_target.lower() == 'vhdl':
        filter_fir_top(hdl, clock, reset, x, xdv, y, ydv)
    else:
        raise ValueError('incorrect target HDL {}'.format(self.hdl_target))

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = FIR_DF(None)
    mainw.show()

    app.exec_()
    
    # test using "python -m pyfda.fixpoint_widgets.fir_df1"