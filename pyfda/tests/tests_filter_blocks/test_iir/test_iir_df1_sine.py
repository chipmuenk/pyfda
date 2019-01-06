

import math
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

from filter_blocks.fda import FilterIIR


def fixp_sine(bsc_int, asc_int, B1, L1):
    # N=20
    # sig = [np.sin(0.1*np.pi*i) for i in np.arange(0,N,1)]

    sig = signal.unit_impulse(10)

    B2 = 17  # Number of bits
    L2 = math.floor(math.log((2 ** (B2 - 1) - 1) / max(sig), 2))  # Round towards zero to avoid overflow

    sig = np.multiply(sig, 2 ** L2)
    sig = sig.round()
    sig = sig.astype(int)
    #print(sig)

    hdlfilter = FilterIIR()
    hdlfilter.set_coefficients(coeff_b=bsc_int, coeff_a=asc_int)
    hdlfilter.set_word_format(coeff_w = (B1, B1 - 1, 0), input_w = (B2, B2 - 1, 0), output_w = (35, 25, 0))
    hdlfilter.set_stimulus(sig)
    hdlfilter.run_sim()
    y = hdlfilter.get_response()

    yout = np.divide(y, 2 ** B1)
    print(yout)
    # hdlfilter.convert(hdl = 'verilog')
    # TODO: plotting should not be included in the tests,
    #       create simple scripts in filter-blocks/scripts
    #       for plotting ...
    # plt.plot(yout, 'b')
    # plt.show()

    return yout


def floatp_sine(b, a, B1, L1):
    # sig = [np.sin(0.1*np.pi*i) for i in np.arange(0,x,1)]
    sig = signal.unit_impulse(10)
    # print(sig)

    B2 = 17  # Number of bits
    L2 = math.floor(math.log((2 ** (B2 - 1) - 1) / max(sig), 2))  # Round towards zero to avoid overflow
    # print(L)
    sig = np.multiply(sig, 2 ** L2)
    sig = sig.round()
    sig = sig.astype(int)

    y_tf = signal.lfilter(b, a, sig)

    print(y_tf)

    return y_tf


def test_iir_df1_sine():
    """Meant to emulate how pyfda will pass parameters to filters"""


    #b, a = signal.ellip(3, 5, 40, 0.6, output='ba')
    b, a = signal.bessel(4, 0.09, 'low')

    print(b)
    print(a)

    B1 = 17  # Number of bits
    L1 = math.floor(math.log((2 ** (B1 - 1) - 1) / max([max(b), max(a)]), 2))  # Round towards zero to avoid overflow

    bsc = b * (2 ** B1)
    asc = a * (2 ** B1)
    bsc_int = [int(x) for x in bsc]
    asc_int = [int(x) for x in asc]
    #print(bsc_int)
    #print(asc_int)

    y1 = fixp_sine(bsc_int, asc_int, B1, L1)
    # print(y1/2**B1)
    y2 = floatp_sine(b, a, B1, L1)


    # print(y1)
    # print(y2)
    # y1 = y1[6:19] #hardcoded presently. Needs to be
    # y2 = y2[:13]

    # print(y1)
    # print(y2)
    # print( ((y1 - y2) ** 2).mean(axis=None))


if __name__ == '__main__':
    test_iir_df1_sine()
