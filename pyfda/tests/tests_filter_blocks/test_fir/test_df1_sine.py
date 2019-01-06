
import math

import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

from filter_blocks.fda import FilterFIR


def fixp_sine(bsc_int, B1, L1):
    N=20
    sig = [np.sin(0.1*np.pi*i) for i in np.arange(0,N,1)]

    B2 = 12 # Number of bits
    L2 = math.floor(math.log((2**(B2-1)-1)/max(sig), 2))  # Round towards zero to avoid overflow

    sig = np.multiply(sig, 2**L2)
    sig = sig.round()
    sig = sig.astype(int)

    hdlfilter = FilterFIR()
    hdlfilter.set_coefficients(coeff_b = bsc_int)
    hdlfilter.set_word_format((B1, B1-1, 0),(B2, B2-1 ,0),(17 , 30, 0))
    hdlfilter.set_stimulus(sig)
    hdlfilter.run_sim()
    y = hdlfilter.get_response()

    yout = np.divide(y,2**L1)
    # hdlfilter.convert(hdl = 'VHDL')
    # TODO: plotting should not be included in the tests,
    #       create simple scripts in filter-blocks/scripts
    #       for plotting ...
    # plt.plot(yout, 'b')
    # plt.show()

    return yout


def edge(B1, L1):
    B2 = 12
    N = 10 # number of coefficients

    max_coef = 2**(B1-1)-1 
    min_coef = -2**(B1-1)

    b_max = [max_coef] * N

    max_in = 2**(B2-1)-1
    min_in = -2**(B2-1)

    coef = np.empty(100)
    coef.fill(max_in)

    hdlfilter = FilterFIR()
    hdlfilter.set_coefficients(coeff_b = b_max)
    hdlfilter.set_word_format((B1, B1-1, 0),(B2, B2-1, 0),(40, 39, 0))
    hdlfilter.set_stimulus(coef)
    hdlfilter.run_sim()
    y = hdlfilter.get_response()

    # yout = np.divide(y,2**L1)
    hdlfilter.convert(hdl = 'verilog')
    # plt.plot(yout, 'b')
    # plt.show()

    return y


def floatp_sine(b, L1):

    x=20
    sig = [np.sin(0.1*np.pi*i) for i in np.arange(0,x,1)]
    #print(sig)


    B2 = 12 # Number of bits
    L2 = math.floor(math.log((2**(B2-1)-1)/max(sig), 2))  # Round towards zero to avoid overflow
    #print(L)
    sig = np.multiply(sig, 2**L2)
    sig = sig.round()
    sig = sig.astype(int)

    y = []
    N = len(b)

    for n in range(N,len(sig)):
        sop = 0
        for i in range(N):
            sop += sig[n-i]*b[i]

        y.append(sop)

    return y


def test_df1_sine():
    """Meant to emulate how pyfda will pass parameters to filters"""
    fs = 1000.
    f1 = 45.
    f2 = 95.
    b = signal.firwin(3,[f1/fs*2,f2/fs*2])    #3 taps

    #convert floating point to fixed point 

    B1 = 18 # Number of bits
    L1 = math.floor(math.log((2**(B1-1)-1)/max(b), 2))  # Round towards zero to avoid overflow
    bsc = b*(2**L1)
    bsc_int = [int(x) for x in bsc]

    y1 = fixp_sine(bsc_int, B1, L1)
    y2 = floatp_sine(b, L1)
    # y = edge(B1, L1)

    y1 = y1[6:19] #hardcoded presently. Needs to be 
    y2 = y2[:13]

    print(y1)
    print(y2)
    print(((y1 - y2) ** 2).mean(axis=None))


if __name__ == '__main__':
    test_df1_sine()
