
import math
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

from filter_blocks.fda import FilterIIR



def test_iir_df1():
    """Meant to emulate how pyfda will pass parameters to filters"""

    sig = signal.unit_impulse(10)
    # print(sig)

    B2 = 17  # Number of bits
    L2 = math.floor(math.log((2 ** (B2 - 1) - 1) / max(sig), 2))  # Round towards zero to avoid overflow
    # print(L)
    sig = np.multiply(sig, 2 ** L2)
    sig = sig.round()
    sig = sig.astype(int)

    



    stim = np.empty(15)
    stim.fill(32767)
    hdlfilter = FilterIIR()
    #b = [1287, 5148, 7722, 5148, 1287]
    #a = [1, -22954, 14021, -3702, 459]
    b = [32767, 32767, 32767, 32767, 32767]
    a = [1, -22954, 14021, -3702, 459]

    hdlfilter.set_coefficients(coeff_b=b, coeff_a=a)
    # TODO: increase the test coverage by adding contraint random
    #
    hdlfilter.set_word_format((16,23,0), (16, 23, 0), (100, 53, 0))
    hdlfilter.set_stimulus(stim)
    hdlfilter.run_sim()
    #hdlfilter.convert(hdl = 'verilog')
    #hdlfilter.info()
    y = hdlfilter.get_response()

    y_tf = signal.lfilter(b, a, stim)

    print(y)
    #print(y_tf)
    hdlfilter.convert(hdl = 'verilog')
    # TODO: plotting should not be included in the tests,
    #       create simple scripts in filter-blocks/scripts
    #       for plotting ...
    #plt.plot(y, 'b')
    #plt.show()


if __name__ == '__main__':
    test_iir_df1()
