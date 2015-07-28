# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Christopher Felton
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
==================
Simple IIR Filter
==================
The following is a straight forward HDL description of a Direct Form I IIR
filter and an object that encapsulates the design and configuration of the
IIR filter.  This module can be used to generate synthesizable Verilog/VHDL
for an FPGA.
How to use this module
-----------------------
  1.  Instantiate an instance of the SIIR object.  Pass the desired low-pass
      frequency cutoff (Fc) and the sample rate (Fs).
   >>> flt = SIIR(Fc=1333, Fs=48000)
  2.  Test the frequency response by running a simulation that inputs random
      samples and then computes the FFT of the input and output, compute
      Y(x)/X(w) = H(w) and plot.
   >>> flt.TestFreqResponse()
  3.  If all looks good create the Verilog and VHDL
   >>> flt.Convert()
This code is discussed in the following
http://www.fpgarelated.com/showarticle/7.php
http://dsp.stackexchange.com/questions/1605/designing-butterworth-filter-in-matlab-and-obtaining-filter-a-b-coefficients-a
:Author: Christopher Felton <cfelton@ieee.org>
"""

from myhdl import (toVerilog, toVHDL, Signal, always, always_comb, delay,
                   instance, instances, intbv, traceSignals, 
                   Simulation, StopSimulation)
#import myhdl

import numpy as np
from numpy import pi, log10
from numpy.fft import fft, fftshift
from numpy.random import uniform, normal

from scipy.signal import freqz
import pylab


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# RTL description of the IIR type I filter
def siir_hdl(
    # ~~ Ports ~~
    clk,           # Synchronous clock
    x,             # Input word, fixed-point format described by "W"
    y,             # Output word, fixed-point format described by "W"
    ts,            # Sample rate strobe (sample rate < system clock rate)

    # ~~ Parameters ~~
    B=None,        # Numerator coefficients, in fixed-point specified
    A=None,        # Denominator coefficients, in fixed-point specified
    W=(24,0)       # Fixed-point description, tuple,
                   #  W[0] = word length (wl)
                   #  W[1] = integer word length (iwl)
                   #  fraction word length (fwl) = wl-iwl-1
    ):
    """
    This is a simple MyHDL IIR Direct Form I Filter example.  This is intended
    to only be used with the SIIR object.
    """

    assert isinstance(A, tuple), "Tuple of denominator coefficents length 3"
    assert len(A) == 3, "Tuple of denominator coefficients length 3"

    assert isinstance(B, tuple), "Tuple of numerator coefficients length 3"
    assert len(B) == 3, "Tuple of numerator coefficients length 3"

    assert isinstance(W, tuple), "Fixed-Point format (W) should be a 2-element tuple"
    assert len(W) == 2, "Fixed-Point format (W) should be a 2-element tuple"

    # Make sure all coefficients are int, the class wrapper handles all float to
    # fixed-point conversion.

    rA = [isinstance(A[ii], int) for ii in range(len(A))]
    rB = [isinstance(B[ii], int) for ii in range(len(B))]

    assert False not in rA, "All A coefficients must be type int (fixed-point)"
    assert False not in rB, "All B coefficients must be type int (fixed-point)"

    Max  = 2**(W[0]-1)
    # double width max and min
    _max = 2**(2*W[0])
    _min = -1*_max

    # Quantize IIR Coefficients
    b0 = B[0]
    b1 = B[1]
    b2 = B[2]

    a1 = A[1]
    a2 = A[2]

    Q  = W[0]-1
    Qd = 2*W[0]

    # Delay elements, list of signals (double length for all)
    ffd = [Signal(intbv(0, min=_min, max=_max)) for ii in range(2)]
    fbd = [Signal(intbv(0, min=_min, max=_max)) for ii in range(2)]
    #ib  = [Signal(intbv(0, min=_min, max=_max)) for ii in range(3)]
    #ia  = [Signal(intbv(0, min=_min, max=_max)) for ii in range(2)]

    yacc = Signal(intbv(0, min=_min, max=_max))
    ys   = Signal(intbv(0, min=-1*Max, max=Max))

    @always(clk.posedge)
    def rtl_iir():
        if ts:
            ffd[1].next = ffd[0]
            ffd[0].next = x

            fbd[1].next = fbd[0]
            fbd[0].next = yacc[Qd:Q].signed()

        # Double precision accumulator
        y.next = yacc[Qd:Q].signed()

    @always_comb
    def rtl_acc():
        # Double precision accumulator
        yacc.next = (b0*x) + (b1*ffd[0]) + (b2*ffd[1]) - (a1*fbd[0]) - (a2*fbd[1])


    return instances()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def siir_sos_hdl(
    # ~~ Ports ~~
    clk,           # Synchronous clock
    x,             # Input word, fixed-point format described by "W"
    y,             # Output word, fixed-point format described by "W"
    ts,            # Sample rate strobe (sample rate < system clock rate)

    # ~~ Parameters ~~
    B=None,        # Numerator coefficients, in fixed-point specified
    A=None,        # Denominator coefficients, in fixed-point specified
    W=(24,0)       # Fixed-point description, tuple,
                   #  W[0] = word length (wl)
                   #  W[1] = integer word length (iwl)
                   #  fraction word length (fwl) = wl-iwl-1
    ):

    assert len(B) == len(A)
    NumberOfSections = len(B)
    ListOfIir = [None for ii in range(NumberOfSections)]
    _x = [Signal(intbv(0, max=y.max, min=y.min))
          for ii in range(NumberOfSections+1)]
    _x[0] = x
    _x[NumberOfSections] = y

    for ii in range(len(B)):
        ListOfIir[ii] = siir_hdl(clk, _x[ii], _x[ii+1], ts,
                                 B=tuple(map(int, B[ii])),
                                 A=tuple(map(int, A[ii])),
                                 W=W)

    return ListOfIir


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class _iir_typeI_section(object):
    def __init__(self, b, a):
        self.b = b
        self.a = a

        self._fbd = [0. for ii in range(2)]
        self._ffd = [0. for ii in range(2)]

    def process(self, x):

        y = x*self.b[0] + \
            self._ffd[0]*self.b[1] + \
            self._ffd[1]*self.b[2] - \
            self._fbd[0]*self.a[1] - \
            self._fbd[1]*self.a[2]

        self._ffd[1] = self._ffd[0]
        self._ffd[0] = x

        self._fbd[1] = self._fbd[0]
        self._fbd[0] = y

        return y


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class _iir_typeII_section(object):
    def __init__(self, b, a):
        self.b = b
        self.a = a


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class SIIR():
    """
    This is a simple example that illustrates how to create
    an object for designing an simple (fixed structure) IIR
    filter and the RTL implementation.
    """
    def __init__(self,
                 Fc=9200,     # cutoff frequency
                 Fs=96000,    # sample rate
                 b = None,    # or pass b,a coefficients
                 a = None,    # or pass b,a coefficients
                 sos = None,  # WIP sos of section matrix
                 W=(24,0)     # Fixed-point to use
                 ):
        """
        In general this object generates
        the HDL based on a set of coefficients or a sum of
        sections matrix.  This object can only be used for 2nd
        order type=I IIR filters or cascaded 2nd orders.
        -------
        """
        print("init_SIIR")
        print("b",b)
        print(type(b), b)
        print("a", a)
        # The W format, intended to be (total bits, integer bits,
        # fraction bits) is not fully supported.
        # Determine the max and min for the word-widths specified
        self.W = W
        self.max = int(2**(W[0]-1))
        self.min = int(-1*self.max)

        # Filter Design
        N  = 2
        Wn = 0
        self.isSos = False
        if sos is not None:
            self.isSos = True
            (self.nSection, o) = sos.shape
            print(sos)
            self.b = sos[:, 0:3]
            self.a = sos[:, 3:6]
            #for ii in range(self.nSection):
                #self.a[ii,1] = -1*self.a[ii,1]
                #self.a[ii,2] = -1*self.a[ii,2]
            print(self.b)
            print(self.a)
        else:
            self.b = b
            self.a = a
            self.nSection = 1


        # fixed-point Coefficients for the IIR filter
        self.fxb = np.round(self.b * self.max)/self.max
        self.fxa = np.floor(self.a * self.max)/self.max
        
        print("fxa", len(self.fxa), self.fxa)
        print("fxb", len(self.fxb), self.fxb)

        # Save off the frequency response for the fixed-point
        # coefficients.
        if not self.isSos:
            self.w, self.h = freqz(self.fxb, self.fxa)
            self.hz = (self.w/(2*pi) * Fs)
        else:
            self.w = [None for ii in range(self.nSection)]
            self.h = [None for ii in range(self.nSection)]
            for ii in range(self.nSection):
                self.w[ii], self.h[ii] = freqz(self.fxb[ii], self.fxa[ii])
            self.w = np.array(self.w); self.h = np.array(self.h)
            self.hz = (self.w/(2*pi) * Fs)

        # Create the integer version
        if self.isSos:
            self.fxb = self.fxb*self.max
            self.fxa = self.fxa*self.max
        else:
            self.fxb = tuple(map(int, self.fxb*self.max))
            self.fxa = tuple(map(int, self.fxa*self.max))

        print ("IIR w,b,a", Wn, self.b, self.a)
        print ("IIR fixed-point b,a", self.fxb, self.fxa)

        # used by the RTL simulation to generate freq response
        self.yfavg = None
        self.xfavg = None
        self.pfavg = None

        # golden model
        self.iirSections = [None for ii in range(self.nSection)]
        if self.nSection > 1:
            for ii in range(self.nSection):
                self.iirSections[ii] = _iir_typeI_section(self.b[ii], self.a[ii])
        else:
            self.iirSections[0] = _iir_typeI_section(self.b, self.a)

        #self._d = [0. for ii in range(2)]
        #self._fbd = [0. for ii in range(2)]
        #self._ffd = [0. for ii in range(2)]

        self.firstPass = True

    def filter_directI(self, x):

        """Floating-point IIR filter direct-form I
        """
        #print(" Input x %d" % (x))
        for ii in range(self.nSection):
            x = self.iirSections[ii].process(x)
        y = x
        #print(" Output y %d" % (y))
        #if self.isSos:
        #    if self.firstPass:
        #        print('WARNING: SOS WIP')
        #        self.firstPass = False
        #    return 0
        #
        #y = x*self.b[0] + \
        #    self._ffd[0]*self.b[1] + \
        #    self._ffd[1]*self.b[2] - \
        #    self._fbd[0]*self.a[1] - \
        #    self._fbd[1]*self.a[2]
        #
        #self._ffd[1] = self._ffd[0]
        #self._ffd[0] = x
        #
        #self._fbd[1] = self._fbd[0]
        #self._fbd[0] = y

        return y


    def filter_directII(self, x):
        """Floating-point IIR filter direct-form II
        """
        if self.isSos:
            raise (StandardError, "WIP SOS")

        w = x - self._d[0]*self.a[1] - self._d[1]*self.a[2]
        y = self.b[0]*w + self._d[0]*self.b[1] + self._d[1]*self.b[2]

        self._d[1] = self._d[0]
        self._d[0] = w

        return y


    def RTL(self, clk, x, y, ts):
        if self.isSos:
            hdl = siir_sos_hdl(clk, x, y, ts, A=self.fxa, B=self.fxb, W=self.W)
        else:
            hdl = siir_hdl(clk, x, y, ts, A=self.fxa, B=self.fxb, W=self.W)

        return hdl


    def Convert(self, W=None):
        """Convert the HDL description to Verilog and VHDL.
        """
        clk = Signal(False)
        ts  = Signal(False)
        x   = Signal(intbv(0,min=-2**(self.W[0]-1), max=2**(self.W[0]-1)))
        y   = Signal(intbv(0,min=-2**(self.W[0]-1), max=2**(self.W[0]-1)))

        if self.isSos:
            print("Convert IIR SOS to Verilog and VHDL")
            toVerilog(siir_sos_hdl, clk, x, y, ts, A=self.fxa, B=self.fxb, W=self.W)
            toVHDL(siir_sos_hdl, clk, x, y, ts, A=self.fxa, B=self.fxb, W=self.W)
        else:
            # Convert to Verilog and VHDL
            print("Convert IIR to Verilog and VHDL")
            toVerilog(siir_hdl, clk, x, y, ts,  A=self.fxa, B=self.fxb, W=self.W)
            toVHDL(siir_hdl, clk, x, y, ts,  A=self.fxa, B=self.fxb, W=self.W) 

    def TestFreqResponse(self, Nloops=3, Nfft=1024):
        """
        """
        self.Nfft = Nfft
        Q = self.W[0]-1
        clk = Signal(False)
        ts  = Signal(False)
        x   = Signal(intbv(0,min=-2**Q,max=2**Q))
        y   = Signal(intbv(0,min=-2**Q,max=2**Q))
        xf  = Signal(0.0)

        NC=32
        cnt = Signal(NC)

        dut = traceSignals(self.RTL, clk, x, y, ts)
        #dut = self.RTL(clk, x, y, ts)

        @always(delay(10))
        def clkgen():
            clk.next = not clk

        @always(clk.posedge)
        def tsgen():
            if cnt == 0:
                cnt.next = NC
                ts.next = True
            else:
                cnt.next -= 1
                ts.next = False

        @always(clk.posedge)
        def ist():
            if ts:
                xi      = uniform(-1,1)
                x.next  = 0 #int(self.max*xi)
                xf.next = xi

        @instance
        def stimulus():
            ysave      = np.zeros(Nfft)
            xsave      = np.zeros(Nfft)
            psave      = np.zeros(Nfft)

            self.yfavg = np.zeros(Nfft)
            self.xfavg = np.zeros(Nfft)
            self.pfavg = np.zeros(Nfft)

            for ii in range(Nloops):
                for jj in range(Nfft):
                    yield ts.posedge
                    xsave[jj] = float(xf)
                    ysave[jj] = float(y)/self.max

                    psave[jj] = self.filter_directI(float(xf))
                    #psave[jj] = self.filter_directII(float(xf))

                self.yfavg = self.yfavg + (abs(fft(ysave, Nfft)) / Nfft)
                self.xfavg = self.xfavg + (abs(fft(xsave, Nfft)) / Nfft)
                self.pfavg = self.pfavg + (abs(fft(psave, Nfft)) / Nfft)

            raise StopSimulation

        return instances()


    def PlotResponse(self, fn="siir"):
        # Plot the designed filter response
        pylab.ioff()
        if self.nSection == 1:
            pylab.plot(self.w, 20*log10(np.abs(self.h)), 'm')
            fxw,fxh = freqz(self.fxb, self.fxa)
            pylab.plot(fxw, 20*log10(np.abs(fxh)), 'y:')

        # plot the simulated response
        #  -- Fixed Point Sim --
        xa = 2*pi * np.arange(self.Nfft)/self.Nfft
        H = self.yfavg / self.xfavg
        pylab.plot(xa, 20*log10(H), 'b' )
        #  -- Floating Point Sim --
        Hp = self.pfavg / self.xfavg
        pylab.plot(xa, 20*log10(Hp), 'g' )

        #pylab.axis((0, pi, -40, 3))
        pylab.ylabel('Magnitude dB');
        pylab.xlabel('Frequency Normalized Radians')
        pylab.legend(('Ideal', 'Quant. Coeff.',
                      'Fixed-P. Sim', 'Floating-P. Sim'))
        pylab.savefig(fn+".png")
        pylab.savefig(fn+".eps")


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == '__main__':
    # Instantiate the filter and define the Signal
    W = (8,0)
    b = np.asarray([1,1,1])
#    b = [1,1,1]
    a = np.asarray([3, 0, 2])
    # need to be ndarrays, with type list / tuple the filter "explodes" 
    flt = SIIR(W = W, b = b, a = a)

#    clk = Signal(False)
#    ts  = Signal(False)
#    x   = Signal(intbv(0,min=-2**(W[0]-1), max=2**(W[0]-1)))
#    y   = Signal(intbv(0,min=-2**(W[0]-1), max=2**(W[0]-1)))
#
    # Setup the Testbench and run
    print ("Simulation")
    tb = flt.TestFreqResponse(Nloops=3, Nfft=1024)
    sim = Simulation(tb)
    print ("Run Simulation")
    sim.run()
    print ("Plot Response")
    flt.PlotResponse()

    flt.Convert()
    print("Finished!")