#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#===========================================================================
# pyfda_lib_fix.py
#
# Fixpoint library for converting numpy scalars and arrays to quantized
# numpy values
#
# (c) 2014-Feb-04 Christian Münker 
#===========================================================================
from __future__ import division, print_function, unicode_literals # v3line15

import numpy as np
#from numpy import (pi, log10, exp, sqrt, sin, cos, tan, angle, arange,
#                   linspace, array, zeros, ones)

#------------------------------------------------------------------------
class Fixed(object):    
    """
    Implement binary quantization of signed scalar or array-like objects 
    in the form yq = IW.FW where IW and FW are the wordlength of integer resp. 
    fractional part; total wordlength is W = IW + FW + 1 due to the sign bit.
    
    q_obj = {'QI':1, 'QF':14, 'ovfl':'sat', 'quant':'round'} or
    q_obj = {'Q':'1.14', 'ovfl':'sat', 'quant':'round'}
    myQ = Fixed(q_obj) # instantiate fixed-point object
    
        
    Parameters
    ----------
    q_obj : dict 
        with 2 ... 4 elements defining quantization operation with
            
      q_obj['QI']: IW; integer word length, default: 0
      
      q_obj['QW']: FW; fractional word length; default: 15; IW + FW + 1 = W (1 sign bit)
      
      q_obj['quant']: Quantization method, optional
      
      - 'floor': (default) largest integer i such that i <= x (= binary truncation)
      - 'round': (binary) rounding
      - 'fix': round to nearest integer towards zero ('Betragsschneiden')
      - 'ceil': smallest integer i, such that i >= x
      - 'rint': round towards nearest int 
      - 'none': no quantization (for debugging purposes)
      
      q_obj['ovfl']: Overflow method, optional; default = 'wrap'
      
      - 'wrap': do a two's complement wrap-around
      - 'sat' : saturate at minimum / maximum value
      - 'none': no overflow; the integer word length is ignored (for debugging)
    
    y : scalar or array-like object
        to be quantized
    
    Returns
    -------
    yq : ndarray
        The quantized input value(s) as an ndarray with np.float64. If this is
        not what you want, see examples:
        
    Attention: 
    - For integer quantization, select 
    - The returned value usually is 
    
    Notes
    -----
    class Fixed() can be used like Matlabs quantizer object / function from the
    fixpoint toolbox, see (Matlab) 'help round' and 'help quantizer/round' e.g. 
    
    q_dsp = quantizer('fixed', 'round', [16 15], 'wrap'); % Matlab
    
    q_dsp = (0, 15, 'round', 'wrap') # Python
    
    
    Example:
    --------
        Example:
    

    yq = myQ.fix(y)    # calculate fixed-point representation of y
    print(myQ.N_over, "overflows!")
    myQ.resetN()       # reset overflow counter
    >>> q_obj_a = (1,2,'round','wrap')
    >>> myQ = Fixed(q_obj) # instantiate fixed-point object
    >>> a = np.arange(0,5,0.05)

    >>> aq, N_over = fixed(q_obj_a, a)
    >>> plt.plot(a,aq)
    >>> print(N_over) # print number of overflows
    Convert output to same format as input:
    >>> b = np.arange(200, dtype = np.int16)
    >>> btype = np.result_type(b)
    >>> q_obj_b = (7,-2,'round','wrap') # MSB = 2**7, LSB = 2**2
    >>> bq, N_over = fixed(q_obj_b, b)
    >>> bq = bq.astype(btype) # restore original variable type
    >>> 
    """
    def __init__(self, q_obj):
        """
        Initialize fixed object with q_obj
        """
        # test if all passed keys of quantizer object are known
        self.setQobj(q_obj)
        self.resetN() # initialize overflow-counter
               
    def setQobj(self, q_obj):
        """
        Analyze quantization dict, complete and transform it if needed and
        store it as instance attribute
        """
        for key in q_obj.keys():
            if key not in ['Q','QF','QI','quant','ovfl']:
                raise Exception(u'Unknown Key "%s"!'%(key))

        # set default values for parameters if undefined:
        if 'Q' in q_obj:
            Q_str = str(q_obj['Q']).split('.',1)  # split 'Q':'1.4'         
            q_obj['QI'] = int(Q_str[0])
            q_obj['QF'] = int(Q_str[1])
        else:
            if 'QI' not in q_obj: q_obj['QI'] = 0
            else: q_obj['QI'] = int(q_obj['QI'])
            if 'QF' not in q_obj: q_obj['QF'] = 15
            else: q_obj['QF'] = int(q_obj['QF'])
        if 'quant' not in q_obj: q_obj['quant'] = 'floor'
        if 'ovfl' not in q_obj: q_obj['ovfl'] = 'wrap'
        
        self.q_obj    = q_obj # store quant. dict in instance      
        self.requant  = q_obj['quant']
        self.overflow = q_obj['ovfl']
        
        self.LSB  = 2. ** (-q_obj['QF']) # value of LSB = 2 ^ (-WF)
        self.MSB  = 2. ** q_obj['QI']    # value of MSB = 2 ^ WI        
        

    def fix( self, y):
        """
        Return fixed-point representation yq of y (scalar or array-like), 
        yq.shape = y.shape
        """
        try:
            _ = len(y)
        except TypeError: # exception -> y is scalar:   
            over_pos = over_neg = yq = 0
        else: # no exception -> y is array:
            # create empty arrays for result and overflows with same shape as y
            y = np.asarray(y)
            yq = np.zeros(y.shape)
            over_pos = over_neg = np.zeros(y.shape, dtype = bool)          
        # Quantize inputs
        if   self.requant == 'floor':  yq = self.LSB * np.floor(y / self.LSB)
             # largest integer i, such that i <= x (= binary truncation)
        elif self.requant == 'round':  yq = self.LSB * np.round(y / self.LSB)
             # rounding, also = binary rounding
        elif self.requant == 'fix':    yq = self.LSB * np.fix(y / self.LSB)
             # round to nearest integer towards zero ("Betragsschneiden")
        elif self.requant == 'ceil':   yq = self.LSB * np.ceil(y / self.LSB)
             # smallest integer i, such that i >= x
        elif self.requant == 'rint':   yq = self.LSB * np.rint(y / self.LSB)
             # round towards nearest int 
        elif self.requant == 'none':   yq = y
        else: raise Exception('Unknown Requantization type "%s"!'%(self.requant))
        
        # Handle Overflow / saturation        
        if   self.overflow == 'none': pass
        else:
            # Bool. vectors with '1' for every neg./pos overflow:
            over_neg = (yq < -self.MSB)
            over_pos = (yq >= self.MSB)
            # No. of pos. / neg. / all overflows occured since last reset:
            self.N_over_neg += np.sum(over_neg)
            self.N_over_pos += np.sum(over_pos)
            self.N_over = self.N_over_neg + self.N_over_pos 

            # Replace overflows with Min/Max-Values (saturation):           
            if self.overflow == 'sat':
                yq = yq * (~over_pos) * (~over_neg) - over_neg * self.MSB\
                                            + over_pos * (self.MSB - self.LSB)
            # Replace overflows by two's complement wraparound (wrap)
            elif self.overflow == 'wrap':
                yq = yq - 2. * self.MSB*np.fix((np.sign(yq)* self.MSB+ yq)/(2*self.MSB))
            else: raise Exception('Unknown overflow type "%s"!'%(self.overflow))
        return yq
        
    def resetN(self):
        """ Reset overflow-counters of Fixed object"""
        self.N_over = 0
        self.N_over_neg = 0
        self.N_over_pos = 0
            

#----------------------------------------------------------------------
class FIX_filt_MA(Fixed):
    """
    yq = FIX_filt_MA.fixFilt(x,aq,bq,gq)
	FIR-Filter mit verschiedenen internen Quantisierungen: 
	q_mul beschreibt Requantisierung nach Koeffizientenmultiplikation
	q_acc beschreibt Requantisierung bei jeder Summation im Akkumulator 
	(bzw. gemeinsamen Summenpunkt)
    """
    def __init__(self, q_mul, q_acc):
        """
        Initialize fixed object with q_obj
        """
        # test if all passed keys of quantizer object are known
        self.setQobj(q_mul)
        self.resetN() # initialize overflow-counter	

	
# Calculate filter response via difference equation with quantization:

    def fixFilt(x, bq, aq, gq, q_mul, q_acc, verbose = True):
        
        # Initialize vectors (also speeds up calculation)
    #    Nx = len(x)
    #    s = zeros(Nx) # not needed in this filter
        yq = accu_q = np.zeros(len(x))
    #    bq_len = len(bq)
        x_bq = np.zeros(len(bq))
        
        for k in range(len(x) - len(bq)):
            # weighted state-vector x at time k:
            x_bq, N_over_m = Fixed.fix(q_mul, x[k:k + len(bq)] * bq)
            # sum up x_bq to get accu[k]
            accu_q[k], N_over_a = Fixed.fix(q_acc, sum(x_bq))
        yq = accu_q * gq # scaling at the output of the accumulator
        s = x # copy state-vector
        if (N_over_m and verbose): print('Overflows in Multiplier:  ', N_over_m)
        if (N_over_a and verbose): print('Overflows in Accumulator: ', N_over_a)
             
        return yq
    
# nested loop would be much slower!
#  for k in range(Nx - len(bq)):
#	for i in len(bq):
#	  accu_q[k] = fixed(q_acc, (accu_q[k] + fixed(q_mul, x[k+i]*bq[i+1])))

#######################################
# If called directly, do some example #
#######################################
if __name__=='__main__':
    pass
