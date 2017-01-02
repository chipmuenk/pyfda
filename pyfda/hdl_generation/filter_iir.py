# -*- coding: utf-8 -*-
#
# Copyright (c) 2011, 2015 Christopher L. Felton
#

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

"""
IIR Hadward Filter Generation
=============================

The following is a straight forward HDL description of a Direct Form I IIR
filter and an object that encapsulates the design and configuration of the
IIR filter.  This module can be used to generate synthesizable Verilog/VHDL
for ASIC of FPGA implementations.

How to use this module
-----------------------

   >>> flt = FilterIIR()

This code is discussed in the following
http://www.fpgarelated.com/showarticle/7.php
http://dsp.stackexchange.com/questions/1605/designing-butterworth-filter-in-matlab-and-obtaining-filter-a-b-coefficients-a


:Author: Christopher Felton <cfelton@ieee.org>
"""

import os

from myhdl import (toVerilog, toVHDL, Signal, ResetSignal,
                   always, delay, instance, intbv,
                   traceSignals, Simulation, StopSimulation)

import numpy as np
from numpy import pi, log10
from numpy.fft import fft
from numpy.random import uniform
from scipy import signal

from .filter_intf import FilterInterface
from .filter_iir_hdl import filter_iir_hdl, filter_iir_sos_hdl


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class FilterIIR(object):
    def __init__(self, b=None, a=None, sos=None, word_format=(24,0), sample_rate=1):
        """
        In general this object generates the HDL based on a set of
        coefficients or a second order sections matrix.  This object can
        only be used for 2nd order type=I IIR filters or cascaded 2nd orders.
        The coefficients are passed as floating-point values are and converted
        to fixed-point using the format defined in the `W` argument.  The
        `W` argument is a tuple that defines the overall word length (`wl`),
        the interger word length (`iwl`) and the fractional word length (`fwl`):
        `W= (wl, iwl, fwl,)`.

        Arguments
        ---------
          b: the filters transfer function numerator coefficients
          a: the filters transfer function denominator coefficients
          sos: the second-order-sections array coefficients, if used `a` and `b`
            are ignored
          W: word format (fixed-point) used

        @todo: utilize the myhdl.fixbv type for fixed point format (`W`)
        """
        # The W format, intended to be (total bits, integer bits,
        # fraction bits) is not fully supported.
        # Determine the max and min for the word-widths specified
        w = word_format
        self.word_format = w
        self.max = int(2**(w[0]-1))
        self.min = int(-1*self.max)
        self._sample_rate = sample_rate
        self._clock_frequncy = 20

        # properties that are set/configured
        self._sample_rate = 1
        self._clock_frequency = 20
        self._shared_multiplier = False

        self.Nfft = 1024

        # conversion attributes
        self.hdl_name = 'name'
        self.hdl_directory = 'directory'
        self.hdl_target = 'verilog' # or 'vhdl'

        # create the fixed-point (integer) version of the coefficients
        self._convert_coefficients(a, b, sos)

        # used by the RTL simulation to generate freq response
        self.yfavg, self.xfavg, self.pfavg = None, None, None

        # golden model - direct-form I IIR filter using floating-point
        # coefficients
        self.iir_sections = [None for _ in range(self.n_section)]

        # @todo: fix this, the default format of `b` and `a` should be
        # @todo: an 2D array.
        if self.n_section == 1:
            b, a = [self.b], [self.a]
        else:
            b, a = self.b, self.a

        # @todo: determine the section used type 1, 2, 3, 4 ...
        # @todo: _iir_section = _iir_type_one_section if self.form_type == 1 else _iir_type_two_section
        for ii in range(self.n_section):
            # @todo: assign the structure type
            self.iir_sections[ii] = IIRTypeOneSection(b[ii], a[ii])

        self.first_pass = True

    def _convert_coefficients(self, a, b, sos):
        """ Extract the coefficients and convert to fixed-point (integer)

        Arguments
        ---------
        :param a:
        :param b:
        :param sos:

        """
        # @todo: use myhdl.fixbv, currently the fixed-point coefficient
        # @todo: the current implementation only uses an "all fractional"
        # @todo: format.
        if len(self.word_format) == 2 and self.word_format[1] != 0:
            raise NotImplementedError
        elif (len(self.word_format) == 3 and
              self.word_format[1] != 0 and
              self.word_format[2] != self.word_format[1]-1):
            raise NotImplementedError

        # @todo: if a sum-of-sections array is supplied only the first
        # @todo: section is currently used to compute the frequency
        # @todo: response, the full response is needed.
        N, Wn = 2, 0
        self.is_sos = False
        if sos is not None:
            self.is_sos = True
            (self.n_section, o) = sos.shape
            self.b = sos[:, 0:3]
            self.a = sos[:, 3:6]
        else:
            self.b = b
            self.a = a
            self.n_section = 1

        # fixed-point Coefficients for the IIR filter
        # @todo: use myhdl.fixbv, see the comments and checks above
        # @todo: the fixed-point conversion is currently very limited.
        self.fxb = np.round(self.b * self.max)/self.max
        self.fxa = np.floor(self.a * self.max)/self.max

        # Save off the frequency response for the fixed-point
        # coefficients.
        if not self.is_sos:
            self.w, self.h = signal.freqz(self.fxb, self.fxa)
            self.hz = (self.w/(2*pi) * self._sample_rate)
        else:
            self.w = [None for _ in range(self.n_section)]
            self.h = [None for _ in range(self.n_section)]
            for ii in range(self.n_section):
                self.w[ii], self.h[ii] = signal.freqz(self.fxb[ii], self.fxa[ii])
            self.w, self.h = np.array(self.w), np.array(self.h)
            self.hz = (self.w/(2*pi) * self._sample_rate)

        # Create the integer version
        if self.is_sos:
            self.fxb = self.fxb * self.max
            self.fxa = self.fxa * self.max
        else:
            self.fxb = tuple(map(int, self.fxb*self.max))
            self.fxa = tuple(map(int, self.fxa*self.max))

    @property
    def shared_multiplier(self):
        return self._shared_multiplier

    @shared_multiplier.setter
    def shared_multiplier(self, val):
        # @todo: check the frequencies to make sure shared is valid
        self._shared_multiplier = val

    def filter_model(self, x):
        """Floating-point IIR filter models
        The "iir_sections" are assigned based on the settings, when
        the filter is simulated an all floating-point simulation is
        compared to the HDL.
        """
        for ii in range(self.n_section):
            x = self.iir_sections[ii].process(x)
        y = x

        return y

    def get_hdl(self, clock, reset, sigin, sigout):
        if self.is_sos:
            hdl = filter_iir_sos_hdl(clock, reset, sigin, sigout,
                                     coefficients=(self.fxb, self.fxa),
                                     shared_multiplier=self._shared_multiplier)
        else:
            hdl = filter_iir_hdl(clock, reset, sigin, sigout,
                                 coefficients=(self.fxb, self.fxa),
                                 shared_multiplier=self._shared_multiplier)
        return hdl

    def convert(self):
        """Convert the HDL description to Verilog and VHDL.
        """
        w = self.word_format
        imax = 2**(w[0]-1)

        # small top-level wrapper
        def filter_iir_top(clock, reset, x, xdv, y, ydv):
            sigin = FilterInterface(word_format=(len(x), 0, len(y)-1))
            sigin.data, sigin.data_valid = x, xdv
            sigout = FilterInterface(word_format=(len(y), 0, len(y)-1))
            sigout.data, sigout.data_valid = y, ydv

            if self.is_sos:
                iir_hdl = filter_iir_sos_hdl
            else:
                iir_hdl = filter_iir_hdl

            iir = iir_hdl(clock, reset, sigin, sigout,
                          coefficients=(self.fxb, self.fxa),
                          shared_multiplier=self._shared_multiplier)
            return iir

        clock = Signal(False)
        reset = ResetSignal(0, active=1, async=False)
        x = Signal(intbv(0, min=-imax, max=imax))
        y = Signal(intbv(0, min=-imax, max=imax))
        xdv, ydv = Signal(bool(0)), Signal(bool(0))

        if self.hdl_target.lower() == 'verilog':
            tofunc = toVerilog
        elif self.hdl_target.lower() == 'vhdl':
            tofunc = toVHDL
        else:
            raise ValueError('incorrect target HDL {}'.format(self.hdl_target))

        if not os.path.isdir(self.hdl_directory):
            os.mkdir(self.hdl_directory)
        tofunc.name = self.hdl_name
        tofunc.directory = self.hdl_directory
        tofunc(filter_iir_top, clock, reset, x, xdv, y, ydv)

    def simulate_freqz(self, num_loops=3, Nfft=1024):
        """ simulate the discrete frequency response
        This function will invoke an HDL simulation and capture the
        inputs and outputs of the filter.  The response can be compared
        to the frequency response (signal.freqz) of the coefficients.
        """
        self.Nfft = Nfft
        w = self.word_format[0]
        clock = Signal(bool(0))
        reset = ResetSignal(0, active=1, async=False)
        sigin = FilterInterface(word_format=self.word_format)
        sigout = FilterInterface(word_format=self.word_format)
        xf = Signal(0.0)    # floating point version

        # determine the sample rate to clock frequency
        fs = self._sample_rate
        fc = self._clock_frequency
        fscnt_max = fc//fs
        cnt = Signal(fscnt_max)

        def _test_stim():
            # get the hardware description to simulation
            tbdut = self.get_hdl(clock, reset, sigin, sigout)

            @always(delay(10))
            def tbclk():
                clock.next = not clock

            @always(clock.posedge)
            def tbdv():
                if cnt == 0:
                    cnt.next = fscnt_max
                    sigin.data_valid.next = True
                else:
                    cnt.next -= 1
                    sigin.data_valid.next = False

            @always(clock.posedge)
            def tbrandom():
                if sigin.data_valid:
                    xi = uniform(-1, 1)
                    sigin.data.next = int(self.max*xi)
                    xf.next = xi

            @instance
            def tbstim():
                ysave = np.zeros(Nfft)
                xsave = np.zeros(Nfft)
                psave = np.zeros(Nfft)

                self.yfavg = np.zeros(Nfft)
                self.xfavg = np.zeros(Nfft)
                self.pfavg = np.zeros(Nfft)

                for ii in range(num_loops):
                    for jj in range(Nfft):
                        yield sigin.data_valid.posedge
                        xsave[jj] = float(sigin.data)/self.max
                        yield sigout.data_valid.posedge
                        ysave[jj] = float(sigout.data)/self.max
                        # grab the response from the floating-point model
                        psave[jj] = self.filter_model(float(xf))

                    # remove any zeros
                    xsave[xsave == 0] = 1e-19
                    ysave[ysave == 0] = 1e-19
                    psave[psave == 0] = 1e-19

                    # average the FFT frames (converges the noise variance)
                    self.yfavg += (np.abs(fft(ysave, Nfft)) / Nfft)
                    self.xfavg += (np.abs(fft(xsave, Nfft)) / Nfft)
                    self.pfavg += (np.abs(fft(psave, Nfft)) / Nfft)

                raise StopSimulation

            return (tbdut, tbclk, tbdv, tbrandom, tbstim,)

        traceSignals.name = 'filter_iir_sim'
        if os.path.isfile(traceSignals.name+'.vcd'):
            os.remove(traceSignals.name+'.vcd')
        gens = traceSignals(_test_stim)
        Simulation(gens).run()

        return None

    def plot_response(self, ax):
        # Plot the designed filter response
        if self.n_section == 1:
            fw, fh = signal.freqz(self.b, self.a, worN=self.Nfft)
            ax.plot(fw, 20*log10(np.abs(fh)), linewidth=2, alpha=.75)
            fxw, fxh = signal.freqz(self.fxb, self.fxa, worN=self.Nfft)
            ax.plot(fxw, 20*log10(np.abs(fxh)), linestyle='--', linewidth=3,
                    alpha=.75)

        # plot the simulated response, if simulated data exists
        if self.xfavg is None or self.yfavg is None or self.pfavg is None:
            pass
        else:
            #  -- Fixed Point Sim --
            xa = 2*pi * np.arange(self.Nfft)/self.Nfft
            h = self.yfavg / self.xfavg
            ax.plot(xa, 20*log10(h), linewidth=4, alpha=.5)
            #  -- Floating Point Sim --
            hp = self.pfavg / self.xfavg
            ax.plot(xa, 20*log10(hp), color='k', linestyle=':',
                    linewidth=2, alpha=.75)

        ax.set_ylim(-80, 10)
        ax.set_xlim(0, np.pi)

        ax.set_ylabel('Magnitude dB');
        ax.set_xlabel('Frequency Normalized Radians')
        ax.legend(('Ideal', 'Quant. Coeff.',
                      'Fixed-P. Sim', 'Floating-P. Sim'))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class IIRTypeOneSection(object):
    def __init__(self, b, a):
        self.b, self.a = b, a
        self._fbd = [0. for _ in range(2)]
        self._ffd = [0. for _ in range(2)]

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


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class IIRTypeTwoSection(object):
    def __init__(self, b, a):
        self.b = b
        self.a = a

    def process(self, x):
        # @todo: finish type two ...
        y = 0
        return y
