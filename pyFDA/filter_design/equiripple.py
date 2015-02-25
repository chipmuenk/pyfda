# -*- coding: utf-8 -*-
"""
Design equiripple-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zeros, poles, gain (zpk) format
Created on Tue Nov 26 12:13:41 2013

@author: Christian Muenker

Expected changes in scipy 0.16:
https://github.com/scipy/scipy/pull/3717
https://github.com/scipy/scipy/issues/2444
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import scipy.signal as sig
import numpy as np
from numpy import log10, pi, arctan
from PyQt4 import QtGui

#import filterbroker as fb

# TODO: Order of A_XX is incorrect e.g. for BP
# TODO: Try HP with even order & type = Hilbert
# TODO: Hilbert not working correctly yet

output = 'ba' # set output format of filter design routines to 'zpk' or 'ba'
             # currently, only 'ba' is supported for equiripple routines

class equiripple(object):

    info =\
    """
    Equiripple filter have a constant ripple in pass- and 
    stop band, the tolerance bands are fully used. 
        
    The minimum order to fulfill the target specifications is estimated 
    using one of three algorithms.
    """
    
    def __init__(self):
        self.name = {'equiripple':'Equiripple'}

        # common messages for all man. / min. filter order response types:            
        msg_man = ("Enter desired order, corner frequencies and a weight "
            "value for each band.")
        msg_min = ("Enter the maximum pass band ripple, minimum stop band "
                    "attenuation and the corresponding corner frequencies.")

        # VISIBLE widgets for all man. / min. filter order response types:     
        vis_man = ['fo','fspec','aspec'] # manual filter order
        vis_min = ['fo','fspec','aspec'] # minimum filter order

        # ENABLED widgets for all man. / min. filter order response types:     
        enb_man = ['fo','fspec','wspec'] # manual filter order
        enb_min = ['fo','fspec','aspec'] # minimum filter order

        # common parameters for all man. / min. filter order response types:    
        par_man = ['N', 'f_S'] # enabled widget for man. filt. order
        par_min = ['f_S', 'A_PB', 'A_SB'] # enabled widget for min. filt. order

        # Common data for all man. / min. filter order response types:
        # This data is merged with the entries for individual response types 
        # (common data comes first):
        self.com = {"man":{"enb":enb_man, "msg":msg_man, "par": par_man},
                    "min":{"enb":enb_min, "msg":msg_min, "par": par_min}}
        self.ft = 'FIR'
        self.rt = {
            "LP": {"man":{"par":['W_PB','W_SB','F_PB','F_SB','A_PB','A_SB']},
                   "min":{"par":['F_PB','F_SB','W_PB','W_SB']}},
            "HP": {"man":{"par":['W_SB','W_PB','F_SB','F_PB','A_SB','A_PB'],
                          "msg":r"<br /><b>Note:</b> Order needs to be even (type I FIR filters)!"},
                   "min":{"par":['F_SB','F_PB','W_SB','W_PB']}},
            "BP": {"man":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'W_SB','W_PB','W_SB2','A_SB','A_PB','A_SB2']},
                   "min":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2', 
                                 'W_SB', 'W_PB','W_SB2','A_SB2']}},                                 
            "BS": {"man":{"par":['F_PB', 'F_SB', 'F_SB2', 'F_PB2',
                                 'W_PB', 'W_SB', 'W_PB2','A_PB','A_SB','A_PB2'],
                      "msg":r"<br /><b>Note:</b> Order needs to be even (type I FIR filters)!"},
                   "min":{"par":['A_PB2','W_PB','W_SB','W_PB2', 
                                 'F_PB','F_SB','F_SB2','F_PB2']}},
            "HIL": {"man":{"par":['F_SB', 'F_PB', 'F_PB2', 'F_SB2',
                                 'W_SB', 'W_PB', 'W_SB2','A_SB','A_PB','A_SB2']
                                 }}
          #"DIFF":
                   }
#        self.info = 
#        """
#        Equiripple filter have a constant ripple in pass- and 
#        stop band, the tolerance bands are fully used. 
#        
#        The minimum order to fulfill the target specifications is estimated 
#        using one of three algorithms."""
#        self.info_doc = '<b>From the "Remez" module docstring:</b>\n' + sig.remez.__doc__
        self.info_doc = '    remez()\n    =======\n'+sig.remez.__doc__

        #----------------------------------------------------------------------
        # Additional subwidgets
        self.wdg = {'fo':'combo_equirip_alg'} 
        #----------------------------------------------------------------------
        # Combobox for selecting the algorithm to estimate minimum filter order
        self.combo_equirip_alg = QtGui.QComboBox()
        self.combo_equirip_alg.setObjectName('combo_firwin_alg')
        self.combo_equirip_alg.addItems(['ichige','kaiser','herrmann'])

    def get_params(self, specs):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N     = specs['N'] + 1 # remez algorithms expects number of taps
                                # which is larger by one than the order!!
        self.F_PB  = specs['F_PB'] 
        self.F_SB  = specs['F_SB'] 
        self.F_PB2 = specs['F_PB2']
        self.F_SB2 = specs['F_SB2']
        # remez amplitude specs are linear (not in dBs) and need to be 
        # multiplied by a factor of two to obtain a "tight fit" (why??)
        self.A_PB  = (10.**(specs['A_PB']/20.)-1) / (10**(specs['A_PB']/20.)+1)*2
        self.A_PB2 = (10.**(specs['A_PB2']/20.)-1)/(10**(specs['A_PB2']/20.)+1)*2
        self.A_SB  = 10.**(-specs['A_SB']/20.)
        self.A_SB2 = 10.**(-specs['A_SB2']/20.)

        self.alg = str(self.combo_equirip_alg.currentText())

    def save(self, specs, arg):
        """ 
        Convert between poles / zeros / gain, filter coefficients (polynomes) 
        and second-order sections and store all available formats in the passed
        dictionary 'specs'.
        """
        
        if output == 'zpk': # arg = [z,p,k]
            self.coeffs = sig.zpk2tf(arg[0], arg[1], arg[2])        
            self.zpk = arg
        else: # arg = [b,a]
            self.zpk = sig.tf2zpk(arg[0], arg[1])#[np.roots(arg), [1, np.zeros(len(arg)-1)],1]
            self.coeffs = arg  
        specs["coeffs"] = self.coeffs
        specs["zpk"] = self.zpk
        try: # has the order been calculated by a "min" filter design?
            specs['N'] = self.N-1 # yes, update filterbroker
        except AttributeError:
            pass


    def LPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.remez(self.N,[0, self.F_PB, self.F_SB, 0.5],
               [1, 0], weight = [specs['W_PB'],specs['W_SB']],Hz = 1))

    def LPmin(self, specs):
        self.get_params(specs)
        (self.N, F, A, W) = self.remezord([self.F_PB, self.F_SB], [1, 0], 
            [self.A_PB, self.A_SB], Hz = 1, alg = self.alg)     
        specs['W_PB'] = W[0]
        specs['W_SB'] = W[1]
        self.save(specs, sig.remez(self.N, F, [1, 0], weight = W, Hz = 1))
                
    def HPman(self, specs):
        self.get_params(specs)
#        N = self.oddround(self.N) # enforce odd order 
        self.save(specs, sig.remez(self.N,[0, self.F_SB, self.F_PB, 0.5],
                [0, 1], weight = [specs['W_SB'],specs['W_PB']], Hz = 1))
        
    def HPmin(self, specs):
        self.get_params(specs)
        (N, F, A, W) = self.remezord([self.F_SB, self.F_PB], [0, 1], 
            [self.A_SB, self.A_PB], Hz = 1, alg = self.alg)
        self.N = self.oddround(N)  # enforce odd length = even order
        specs['W_SB'] = W[0]
        specs['W_PB'] = W[1]
        self.save(specs, sig.remez(self.N, F,[0, 1], weight = W, Hz = 1, type = 'bandpass'))

    # For BP and BS, F_PB and F_SB have two elements each
    def BPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.remez(self.N,[0, self.F_SB, self.F_PB, 
                self.F_PB2, self.F_SB2, 0.5],[0, 1, 0], 
                weight = [specs['W_SB'],specs['W_PB'], specs['W_SB2']], Hz = 1))

    def BPmin(self, specs):
        self.get_params(specs)
        (self.N, F, A, W) = self.remezord([self.F_SB, self.F_PB, 
                                self.F_PB2, self.F_SB2], [0, 1, 0], 
            [self.A_SB, self.A_PB, self.A_SB2], Hz = 1, alg = self.alg)
        specs['W_SB']  = W[0]
        specs['W_PB']  = W[1]
        specs['W_SB2'] = W[2]   
        self.save(specs, sig.remez(self.N,F,[0, 1, 0], weight = W, Hz = 1))

    def BSman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.remez(self.N,[0, self.F_PB, self.F_SB, 
                self.F_SB2, self.F_PB2, 0.5],[1, 0, 1], 
                weight = [specs['W_PB'],specs['W_SB'], specs['W_PB2']],Hz = 1))
                
    def BSmin(self, specs):
        self.get_params(specs)
        (N, F, A, W) = self.remezord([self.F_PB, self.F_SB, 
                                self.F_SB2, self.F_PB2], [1, 0, 1], 
            [self.A_PB, self.A_SB, self.A_PB2], Hz = 1, alg = self.alg)
        self.N = self.oddround(N)  # enforce odd length = even order
        specs['W_PB']  = W[0]
        specs['W_SB']  = W[1]
        specs['W_PB2'] = W[2]   
        self.save(specs, sig.remez(self.N,F,[1, 0, 1], weight = W, Hz = 1))

    def HILman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.remez(self.N,[0, self.F_SB, self.F_PB, 
                self.F_PB2, self.F_SB2, 0.5],[0, 1, 0], 
                weight = [specs['W_SB'],specs['W_PB'], specs['W_SB2']], Hz = 1,
                type = 'hilbert'))
                
    #========================================================
    """Supplies remezord method according to Scipy Ticket #475
    was: http://projects.scipy.org/scipy/ticket/475
    now: https://github.com/scipy/scipy/issues/1002
    https://github.com/thorstenkranz/eegpy/blob/master/eegpy/filter/remezord.py
    """
    
    #from numpy import mintypecode
    
     
    abs = np.absolute
     
    def oddround(self, x):
        """Return the nearest odd integer from x."""
    
        return x-np.mod(x,2)+1
    
    def oddceil(self, x):
        """Return the smallest odd integer not less than x."""
    
        return self.oddround(x+1)
        
    def remlplen_herrmann(self, fp,fs,dp,ds):
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
        Dinf = log10(ds)*(a[0]*log10(dp)**2+a[1]*log10(dp)+a[2])+ \
               a[3]*log10(dp)**2+a[4]*log10(dp)+a[5]
        f = b[0]+b[1]*(log10(dp)-log10(ds))
        N1 = Dinf/dF-f*dF+1
    
#        return int(self.oddround(N1))
        return int(N1)
    
    def remlplen_kaiser(self, fp,fs,dp,ds):
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
        N2 = (-20*log10(np.sqrt(dp*ds))-13.0)/(14.6*dF)+1.0
    
#        return int(self.oddceil(N2))
        return int(N2)
    
    def remlplen_ichige(self, fp,fs,dp,ds):
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
        v = lambda dF,dp:2.325*((-log10(dp))**-0.445)*dF**(-1.39)
        g = lambda fp,dF,d:(2.0/pi)*arctan(v(dF,dp)*(1.0/fp-1.0/(0.5-dF)))
        h = lambda fp,dF,c:(2.0/pi)*arctan((c/dF)*(1.0/fp-1.0/(0.5-dF)))
        Nc = np.ceil(1.0+(1.101/dF)*(-log10(2.0*dp))**1.1)
        Nm = (0.52/dF)*log10(dp/ds)*(-log10(dp))**0.17
        N3 = np.ceil(Nc*(g(fp,dF,dp)+g(0.5-dF-fp,dF,dp)+1.0)/3.0)
        DN = np.ceil(Nm*(h(fp,dF,1.1)-(h(0.5-dF-fp,dF,0.29)-1.0)/2.0))
        N4 = N3+DN
        
#        return int(self.oddceil(N4))
        return int(N4)
    
    def remezord(self, freqs,amps,rips,Hz=1,alg='ichige'):
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
            remlplen = self.remlplen_herrmann
        elif alg == 'kaiser':
            remlplen = self.remlplen_kaiser
        elif alg == 'ichige':
            remlplen = self.remlplen_ichige
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
    
    
            