# biquad.py : digital IIR filters using cascaded biquad sections generated using filter_gen.py.
# https://projects-raspberry.com/raspberry-pi-pico-signal-processing-examples-circuitpython/

#--------------------------------------------------------------------------------
# Coefficients for a low-pass Butterworth IIR digital filter with sampling rate
# 10 Hz and corner frequency 1.0 Hz.  Filter is order 4, implemented as
# second-order sections (biquads).
# Reference: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.butter.html

low_pass_10_1 = [[[1.0,       -1.04859958, 0.29614036],   # A coefficients, first section
                  [0.00482434, 0.00964869, 0.00482434]],  # B coefficients, first section
                 [[1.0,       -1.32091343, 0.63273879],   # A coefficients, second section
                  [1.0,        2.0,        1.0]]]         # B coefficients, second section

#--------------------------------------------------------------------------------
# Coefficients for a high-pass Butterworth IIR digital filter with 
# sampling rate: 10 Hz and corner frequency 1.0 Hz.
# Filter is order 4, implemented as second-order sections (biquads).

high_pass_10_1 = [[[1.0,        -1.04859958, 0.29614036],
                   [0.43284664, -0.86569329, 0.43284664]],
                  [[1.0,        -1.32091343, 0.63273879],
                   [1.0,        -2.0,        1.0]]]

#--------------------------------------------------------------------------------
# Coefficients for a band-pass Butterworth IIR digital filter with sampling rate
# 10 Hz and pass frequency range [0.5, 1.5] Hz.  Filter is order 4, implemented
# as second-order sections (biquads).
band_pass_10_1 = [[[1.0,        -1.10547167, 0.46872661],
                   [0.00482434,  0.00964869, 0.00482434]],
                  [[1.0,        -1.48782202, 0.63179763],
                   [1.0,        2.0,         1.0]],
                  [[1.0,        -1.04431445, 0.72062964],
                   [1.0,        -2.0,        1.0]],
                  [[1.0,        -1.78062325, 0.87803603],
                   [1,          -2.0,        1.0]]]

#--------------------------------------------------------------------------------
# Coefficients for a band-stop Butterworth IIR digital filter with
# sampling rate: 10 Hz and exclusion frequency range [0.5, 1.5] Hz.
# Filter is order 4, implemented as second-order sections (biquads).

band_stop_10_1 = [[[1.0,        -1.10547167, 0.46872661],
                   [0.43284664, -0.73640270, 0.43284664]],
                  [[1.0,        -1.48782202, 0.63179763],
                   [1.0,        -1.70130162, 1.0]],
                  [[1.0,        -1.04431445, 0.72062964],
                   [1.0,        -1.70130162, 1.0]],
                  [[1.0,        -1.78062325, 0.87803603],
                   [1.0,        -1.70130162, 1.0]]]

#--------------------------------------------------------------------------------
class BiquadFilter:
    def __init__(self, coeff=low_pass_10_1):
        """General IIR digital filter using cascaded biquad sections.  The specific
        filter type is configured using a coefficient matrix.  These matrices can be
        generated for low-pass, high-pass, and band-pass configurations.
        """
        self.coeff = coeff                                 # coefficient matricies
        self.sections = len(self.coeff)                    # number of biquad sections in chain
        self.state = [[0,0] for i in range(self.sections)] # biquad state vectors
        
    def update(self, input):
        # Iterate over the biquads in sequence.  The accum variable transfers
        # the input into the chain, the output of each section into the input of
        # the next, and final output value.
        accum = input        
        for s in range(self.sections):
            A = self.coeff[s][0]
            B = self.coeff[s][1]
            Z = self.state[s]
            x     = accum   - A[1]*Z[0] - A[2]*Z[1]
            accum = B[0]*x  + B[1]*Z[0] + B[2]*Z[1]
            Z[1] = Z[0]
            Z[0] = x

        return accum