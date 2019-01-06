
import numpy as np
import scipy.signal as signal
import math
import matplotlib.pyplot as plt

from filter_blocks.fda import FilterIIR


def fixp_sine(sos_asc_int, B1, L1):

    sig = signal.unit_impulse(10)

    B2 = 12  # Number of bits
    L2 = math.floor(math.log((2 ** (B2 - 1) - 1) / max(sig), 2))  # Round towards zero to avoid overflow

    sig = np.multiply(sig, 2 ** L2)
    sig = sig.round()
    sig = sig.astype(int)
    print(sig)

    hdlfilter = FilterIIR()
    hdlfilter.set_coefficients(sos = sos_asc_int)
    hdlfilter.set_cascade(3)
    hdlfilter.set_word_format((B1, B1 - 1, 0), (B2, B2 - 1, 0), (1000, 39, 0))
    hdlfilter.set_stimulus(sig)
    hdlfilter.run_sim()
    y = hdlfilter.get_response()

    #yout = np.divide(y, 2 ** B1)
    print(y)

    return y


def floatp_sine(sos, B1, L1):

    # sig = [np.sin(0.1*np.pi*i) for i in np.arange(0,x,1)]
    sig = signal.unit_impulse(10)
    # print(sig)

    B2 = 12  # Number of bits
    L2 = math.floor(math.log((2 ** (B2 - 1) - 1) / max(sig), 2))  # Round towards zero to avoid overflow
    # print(L)
    sig = np.multiply(sig, 2 ** L2)
    sig = sig.round()
    sig = sig.astype(int)

    y_sos = signal.sosfilt(sos, sig)

    print(y_sos)
    
    return y_sos




def main():
    """Meant to emulate how pyfda will pass parameters to filters"""
    
    # fs = 1000.
    # f1 = 45.
    # f2 = 95.
    # b = signal.firwin(3,[f1/fs*2,f2/fs*2])    #3 taps
    #b, a = signal.iirfilter(3, [0.4, 0.7], rs=60, btype='band', ftype='cheby2')
    # print(len(b))
    # print(len(a))
    # print(b)
    # print(a)

    #print(max([max(b),max(a)]))
    #convert floating point to fixed point 


    sos = signal.ellip(3, 0.009, 80, 0.05, output='sos')
    x = signal.unit_impulse(10)
    y_sos = signal.sosfilt(sos, x)
    print(sos)
    
    #print(y_sos)


    B1 = 12 # Number of bits
    L1 = 2**(B1-1) # Round towards zero to avoid overflow

    sos_sc = sos*(2**(B1-1))
    sos_sc_int = sos_sc.astype(int)

    print(sos_sc_int)

    y1 = fixp_sine(sos_sc_int, B1, L1)
    # #print(y1/2**B1)
    y2 = floatp_sine(sos, B1, L1)

    # #print(y1)
    # #print(y2)
    # y1 = y1[6:19] #hardcoded presently. Needs to be 
    # y2 = y2[:13]

    # #print(y1)
    # #print(y2)
    # #print( ((y1 - y2) ** 2).mean(axis=None))


   
if __name__ == '__main__':
    main()