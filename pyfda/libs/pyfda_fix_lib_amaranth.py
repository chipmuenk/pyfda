# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Helper classes and functions for amaranth fixpoint filters
"""
from pyfda.libs.pyfda_lib import cmp_version
import logging
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
if cmp_version("amaranth", "0.3") >= 0:
    from amaranth import Signal, signed, Cat, Module, Repl

    def requant(mod: Module, sig_i: Signal, QI: dict, QO: dict) -> Signal:
        """
        Change word length of input signal `sig_i` to the wordlength of the output
        signal, using the quantization and saturation methods specified by
        ``QO['quant']`` and ``QO['ovfl']``.

        Parameters
        ----------

        mod: Module
            instance of amaranth module

        sig_i: Signal (nmigen)
            Signal to be requantized

        QI: dict
            Quantization dict for input word, only the keys 'WI' and 'WF' for integer
            and fractional wordlength are evaluated. QI['WI'] = 2 and QI['WF'] = 13
            e.g. define Q-Format '2.13'  with 2 integer, 13 fractional bits and 1 implied
            sign bit = 16 bits total.

        QO: dict
            Quantization dict for output word format; the keys 'WI' and 'WF' for
            integer and fractional wordlength are evaluated as well as the keys 'quant'
            and 'ovfl' describing requantization and overflow behaviour.

        Returns
        -------

        sig_o: Signal
            Requantized Amaranth signal

        Documentation
        -------------

        **Input and output word are aligned at their binary points.**

        The following shows an example of rescaling an input word from Q2.4 to Q0.3
        using wrap-around and truncation. It's easy to see that for simple wrap-around
        logic, the sign of the result may change.

        ::

        S | WI1 | WI0 * WF0 | WF1 | WF2 | WF3  :  WI = 2, WF = 4, W = 7
        0 |  1  |  0  *  1  |  0  |  1  |  1   =  43 (dec) or 43/16 = 2 + 11/16 (float)
                      *
                |  S  * WF0 | WF1 | WF2        :  WI = 0, WF = 3, W = 4
                   0  *  1  |  0  |  1         =  7 (dec) or 7/8 (float)


        The float or "real (world) value" is calculated by multiplying the integer
        value by 2 ** (-WF).

        For requantizing two numbers to the same WI and WF, imagine both binary numbers
        to be right-aligned. Changes in the number of integer bits `dWI` and fractional
        bits `dWF` are handled separately.

        Fractional Bits
        ---------------

        - For reducing the number of fractional bits by `dWF`, simply right-shift the
          integer number by `dWF`. For rounding, add '1' to the bit below the truncation
          point before right-shifting.

        - Extend the number of fractional bits by left-shifting the integer by `dWF`,
          LSB's are filled with zeros.

        Integer Bits
        ------------

        - For reducing the number of integer bits by `dWI`, simply right-shift the
          integer by `dWI`.

        - The number of fractional bits is SIGN-EXTENDED by filling up the left-most
          bits with the sign bit.

        """
        WI_I = QI['WI']         # number of integer bits (input signal)
        WI_F = QI['WF']         # number of fractional bits (input signal)
        WI   = WI_I + WI_F + 1  # total word length (input signal)

        WO_I = QO['WI']         # number of integer bits (output signal)
        WO_F = QO['WF']         # number of fractional bits (output signal)
        WO   = WO_I + WO_F + 1  # total word length (output signal)
        N_over = QO['N_over']  # number of overflows

        dWF = WI_F - WO_F       # difference of fractional lengths
        dWI = WI_I - WO_I       # difference of integer lengths

        # max. resp. min, output values
        MIN_o = - 1 << (WO - 1)
        MAX_o = -MIN_o - 1

        # intermediate signal with requantized fractional part
        sig_i_q = Signal(signed(max(WI, WO)))
        sig_o = Signal(signed(WO))

        # logger.debug(f"rescale: dWI={dWI}, dWF={dWF}, Qu:{QO['quant']}, Ov:{QO['ovfl']}")

        # -----------------------------------------------------------------------
        # Requantize fractional part
        # -----------------------------------------------------------------------
        if dWF <= 0:    # Extend fractional word length of output word by
                        # multiplying with 2^dWF
            mod.d.comb += sig_i_q.eq(sig_i << -dWF)  # shift input left by -dWF
        else:   # dWF > 0, reduce fract. word length by dividing by 2^dWF
                # (shift right by dWF)
            if QO['quant'] == 'round':
                # add half an LSB (1 << (dWF - 1)) before right shift
                mod.d.comb += sig_i_q.eq((sig_i + (1 << (dWF - 1))) >> dWF)
            elif QO['quant'] == 'floor':  # just shift right
                mod.d.comb += sig_i_q.eq(sig_i >> dWF)
            elif QO['quant'] == 'fix':
                # add sign bit (sig_i[-1]) as LSB (1 << dWF) before right shift
                mod.d.comb += sig_i_q.eq((sig_i + (sig_i[-1] << dWF)) >> dWF)
            else:
                logger.error(f"Unknown output quantization method <{QO['quant']}>,\n"
                             "\tusing <floor> instead.")
                mod.d.comb += sig_i_q.eq(sig_i >> dWF)

        # -----------------------------------------------------------------------
        # Requantize integer part
        # -----------------------------------------------------------------------
        if dWI < 0:  # WI_I < WO_I, sign extend integer part (prepend copies of sign bit)
            mod.d.comb += sig_o.eq(Cat(sig_i_q, Repl(sig_i_q[-1], -dWI)))
        elif dWI == 0:  # WI = WO, don't change integer part
            mod.d.comb += sig_o.eq(sig_i_q)
        elif QO['ovfl'] == 'sat':
            with mod.If(sig_i_q[-1] == 1):
                with mod.If(sig_i_q < MIN_o):
                    mod.d.comb += sig_o.eq(MIN_o)
                with mod.Else():
                    mod.d.comb += sig_o.eq(sig_i_q)
            with mod.Elif(sig_i_q > MAX_o):  # sig_i_q[-1] == 0
                mod.d.comb += sig_o.eq(MAX_o)
            with mod.Else():
                mod.d.comb += sig_o.eq(sig_i_q)

        else:  # wrap around (shift left)
            mod.d.comb += sig_o.eq(sig_i_q)

            if QO['ovfl'] != 'wrap':
                logger.error(f"Unknown output overflow method <{QO['ovfl']}>,\n"
                            "\tusing <wrap> instead.")
        QO['N_over'] = 15  # TODO: dummy
        return sig_o
else:
    logger.error('Module "amaranth" not found!')

# ==============================================================================
if __name__ == '__main__':
    pass
