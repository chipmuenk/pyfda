# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)
# -*- coding: utf-8 -*-

"""
Common settings and some helper functions for filter design
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import numpy as np

class Common(object):
    
    def __init__(self):
                      
        self.rt_base_iir = {
            'COM':{'man':{'fo': ('a', 'N')},
                   'min':{'fo': ('d', 'N'),
                          'msg':('a',
                   "Enter maximum pass band ripple <b><i>A<sub>PB</sub></i></b>, "
                    "minimum stop band attenuation <b><i>A<sub>SB</sub> </i></b>"
                    "&nbsp;and the corresponding corner frequencies of pass and "
                    "stop band(s), <b><i>F<sub>PB</sub></i></b>&nbsp; and "
                    "<b><i>F<sub>SB</sub></i></b> .")
                        }
                    },
            'LP': {'man':{'fspecs': ('a','F_C'),
                          'tspecs': ('u', {'frq':('u','F_PB','F_SB'), 
                                           'amp':('a','A_PB','A_SB')})
                          },
                   'min':{'fspecs': ('d','F_C'),
                          'tspecs': ('a', {'frq':('a','F_PB','F_SB'), 
                                           'amp':('a','A_PB','A_SB')})
                        }
                },
            'HP': {'man':{'fspecs': ('a','F_C'),
                          'tspecs': ('u', {'frq':('u','F_SB','F_PB'), 
                                           'amp':('a','A_SB','A_PB')})
                         },
                   'min':{'fspecs': ('d','F_C'),
                          'tspecs': ('a', {'frq':('a','F_SB','F_PB'), 
                                           'amp':('a','A_SB','A_PB')})
                         }
                    },
            'BP': {'man':{'fspecs': ('a','F_C', 'F_C2'),
                          'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2'), 
                                           'amp':('a','A_SB','A_PB')})
                         },
                   'min':{'fspecs': ('d','F_C','F_C2'),
                          'tspecs': ('a', {'frq':('a','F_SB','F_PB','F_PB2','F_SB2'), 
                                           'amp':('a','A_SB','A_PB')})
                         },
                    },
            'BS': {'man':{'fspecs': ('a','F_C','F_C2'),
                          'tspecs': ('u', {'frq':('u','F_PB','F_SB','F_SB2','F_PB2'), 
                                           'amp':('a','A_PB','A_SB')})
                          },
                   'min':{'fspecs': ('d','F_C','F_C2'),
                          'tspecs': ('a', {'frq':('a','F_PB','F_SB','F_SB2','F_PB2'), 
                                           'amp':('a','A_PB','A_SB')})
                        }
                }
            }
        
#========================================================
"""Supplies remezord method according to Scipy Ticket #475
was: http://projects.scipy.org/scipy/ticket/475
now: https://github.com/scipy/scipy/issues/1002
https://github.com/thorstenkranz/eegpy/blob/master/eegpy/filter/remezord.py
"""

def remezord(freqs,amps,rips,Hz=1,alg='ichige'):
    """
    Filter parameter selection for the Remez exchange algorithm.

    Calculate the parameters required by the Remez exchange algorithm to
    construct a finite impulse response (FIR) filter that approximately
    meets the specified design.

    Parameters
    ----------

    freqs : list
        A monotonic sequence of band edges specified in Hertz. All elements
        must be non-negative and less than 1/2 the sampling frequency as
        given by the Hz parameter. The band edges "0" and "f_S / 2" do not
        have to be specified, hence  2 * number(amps) - 2 freqs are needed.

    amps : list
        A sequence containing the amplitudes of the signal to be
        filtered over the various bands, e.g. 1 for the passband, 0 for the
        stopband and 0.42 for some intermediate band.

    rips : list
        A list with the peak ripples (linear, not in dB!) for each band. For
        the stop band this is equivalent to the minimum attenuation.

    Hz : float
        Sampling frequency

    alg : string
        Filter length approximation algorithm. May be either 'herrmann',
        'kaiser' or 'ichige'. Depending on the specifications, some of
        the algorithms may give better results than the others.

    Returns
    -------

    numtaps,bands,desired,weight -- See help for the remez function.

    Examples
    --------
        We want to design a lowpass with the band edges of 40 resp. 50 Hz and a
        sampling frequency of 200 Hz, a passband peak ripple of 10%
        and a stop band ripple of 0.01 or 40 dB.

        >>> (L, F, A, W) = remezord([40, 50], [1, 0], [0.1, 0.01], Hz = 200)

    """

    # Make sure the parameters are floating point numpy arrays:
    freqs = np.asarray(freqs,'d')
    amps = np.asarray(amps,'d')
    rips = np.asarray(rips,'d')

    # Scale ripples with respect to band amplitudes:
    rips /= (amps+(amps==0.0))

    # Normalize input frequencies with respect to sampling frequency:
    freqs /= Hz

    # Select filter length approximation algorithm:
    if alg == 'herrmann':
        remlplen = remlplen_herrmann
    elif alg == 'kaiser':
        remlplen = remlplen_kaiser
    elif alg == 'ichige':
        remlplen = remlplen_ichige
    else:
        raise ValueError('Unknown filter length approximation algorithm.')

    # Validate inputs:
    if any(freqs > 0.5):
        raise ValueError('Frequency band edges must not exceed the Nyquist frequency.')
    if any(freqs < 0.0):
        raise ValueError('Frequency band edges must be nonnegative.')
    if any(rips <= 0.0):
        raise ValueError('Ripples must be nonnegative and non-zero.')
    if len(amps) != len(rips):
        raise ValueError('Number of amplitudes must equal number of ripples.')
    if len(freqs) != 2*(len(amps)-1):
        raise ValueError('Number of band edges must equal 2*(number of amplitudes-1)')


    # Find the longest filter length needed to implement any of the
    # low-pass or high-pass filters with the specified edges:
    f1 = freqs[0:-1:2]
    f2 = freqs[1::2]
    L = 0
    for i in range(len(amps)-1):
        L = max((L,
                 remlplen(f1[i],f2[i],rips[i],rips[i+1]),
                 remlplen(0.5-f2[i],0.5-f1[i],rips[i+1],rips[i])))

    # Cap the sequence of band edges with the limits of the digital frequency
    # range:
    bands = np.hstack((0.0,freqs,0.5))

    # The filter design weights correspond to the ratios between the maximum
    # ripple and all of the other ripples:
    weight = max(rips)/rips

    return [L,bands,amps,weight]



def remlplen_herrmann(fp,fs,dp,ds):
    """
    Determine the length of the low pass filter with passband frequency
    fp, stopband frequency fs, passband ripple dp, and stopband ripple ds.
    fp and fs must be normalized with respect to the sampling frequency.
    Note that the filter order is one less than the filter length.

    Uses approximation algorithm described by Herrmann et al.:

    O. Herrmann, L.R. Raviner, and D.S.K. Chan, Practical Design Rules for
    Optimum Finite Impulse Response Low-Pass Digital Filters, Bell Syst. Tech.
    Jour., 52(6):769-799, Jul./Aug. 1973.
    """

    dF = fs-fp
    a = [5.309e-3,7.114e-2,-4.761e-1,-2.66e-3,-5.941e-1,-4.278e-1]
    b = [11.01217, 0.51244]
    Dinf = np.log10(ds)*(a[0]*np.log10(dp)**2+a[1]*np.log10(dp)+a[2])+ \
           a[3]*np.log10(dp)**2+a[4]*np.log10(dp)+a[5]
    f = b[0]+b[1]*(np.log10(dp)-np.log10(ds))
    N1 = Dinf/dF-f*dF+1

    return int(N1)
    #------------------------------------------------------------------------------

def remlplen_kaiser(fp,fs,dp,ds):
    """
    Determine the length of the low pass filter with passband frequency
    fp, stopband frequency fs, passband ripple dp, and stopband ripple ds.
    fp and fs must be normalized with respect to the sampling frequency.
    Note that the filter order is one less than the filter length.

    Uses approximation algorithm described by Kaiser:

    J.F. Kaiser, Nonrecursive Digital Filter Design Using I_0-sinh Window
    function, Proc. IEEE Int. Symp. Circuits and Systems, 20-23, April 1974.
    """

    dF = fs-fp
    N2 = (-20*np.log10(np.sqrt(dp*ds))-13.0)/(14.6*dF)+1.0

    return int(N2)
#------------------------------------------------------------------------------

def remlplen_ichige(fp,fs,dp,ds):
    """
    Determine the length of the low pass filter with passband frequency
    fp, stopband frequency fs, passband ripple dp, and stopband ripple ds.
    fp and fs must be normalized with respect to the sampling frequency.
    Note that the filter order is one less than the filter length.
    Uses approximation algorithm described by Ichige et al.:
    K. Ichige, M. Iwaki, and R. Ishii, Accurate Estimation of Minimum
    Filter Length for Optimum FIR Digital Filters, IEEE Transactions on
    Circuits and Systems, 47(10):1008-1017, October 2000.
    """
#        dp_lin = (10**(dp/20.0)-1) / (10**(dp/20.0)+1)*2
    dF = fs-fp
    v = lambda dF,dp:2.325*((-np.log10(dp))**-0.445)*dF**(-1.39)
    g = lambda fp,dF,d:(2.0/np.pi)*np.arctan(v(dF,dp)*(1.0/fp-1.0/(0.5-dF)))
    h = lambda fp,dF,c:(2.0/np.pi)*np.arctan((c/dF)*(1.0/fp-1.0/(0.5-dF)))
    Nc = np.ceil(1.0+(1.101/dF)*(-np.log10(2.0*dp))**1.1)
    Nm = (0.52/dF)*np.log10(dp/ds)*(-np.log10(dp))**0.17
    N3 = np.ceil(Nc*(g(fp,dF,dp)+g(0.5-dF-fp,dF,dp)+1.0)/3.0)
    DN = np.ceil(Nm*(h(fp,dF,1.1)-(h(0.5-dF-fp,dF,0.29)-1.0)/2.0))
    N4 = N3+DN

    return int(N4)


#------------------------------------------------------------------------------

if __name__ == '__main__':
    pass    