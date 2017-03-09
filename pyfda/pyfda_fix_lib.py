#!/usr/bin/env python
# -*- coding: utf-8 -*-
#===========================================================================
# dsp_fpga_fix_lib.py
#
# Fixpoint library for converting numpy scalars and arrays to quantized
# numpy values
#
# (c) 2015 Christian Münker 
#===========================================================================
from __future__ import division, print_function, unicode_literals

import logging
logger = logging.getLogger(__name__)


import numpy as np
#from numpy import (pi, log10, exp, sqrt, sin, cos, tan, angle, arange,
#                   linspace, array, zeros, ones)
from numpy import binary_repr
__version__ = 0.4

def hex2(val, nbits):
    """
    Return `val` in hex format with a wordlength of `nbits`. In contrast to hex(),   
    negative values are returned in two's complement format 
    """
    return "{0:x}".format((val + (1 << nbits)) % (1 << nbits))

vbin  = np.vectorize(np.binary_repr)
vhex2 = np.vectorize(hex2)

#------------------------------------------------------------------------
class Fixed(object):    
    """
    Implement binary quantization of signed scalar or array-like objects 
    in the form yq = QI.QF where QI and QF are the wordlength of integer resp. 
    fractional part; total wordlength is W = QI + QF + 1 due to the sign bit.
    
    q_obj = {'QI':1, 'QF':14, 'ovfl':'sat', 'quant':'round'} or
    
    q_obj = {'Q':'1.14', 'ovfl':'sat', 'quant':'round'}

    myQ = Fixed(q_obj) # instantiate fixed-point object
    
        
    Parameters
    ----------
    q_obj : dict 
        with 2 ... 4 elements defining quantization operation with the keys
            
    * **'QI'** : integer word length, default: 0
      
    * **'QF'** : fractional word length; default: 15; QI + QF + 1 = W (1 sign bit)
      
    * **'quant'** : Quantization method, optional; default = 'floor'
      
      - 'floor': (default) largest integer `I` such that :math:`I \\le x` (= binary truncation)
      - 'round': (binary) rounding
      - 'fix': round to nearest integer towards zero ('Betragsschneiden')
      - 'ceil': smallest integer `I`, such that :math:`I \\ge x`
      - 'rint': round towards nearest int 
      - 'none': no quantization
      
    * **'ovfl'** : Overflow method, optional; default = 'wrap'
      
      - 'wrap': do a two's complement wrap-around
      - 'sat' : saturate at minimum / maximum value
      - 'none': no overflow; the integer word length is ignored

    * **'frmt'** : Output format, optional; default = 'frac'

      - 'frac' : (default) return result as a fraction
      - 'int'  : return result in integer form, scaled by :math:`2^{WF}`
      - 'bin'  : return result as binary string, scaled by :math:`2^{WF}`
      - 'hex'  : return result as hex string, scaled by :math:`2^{WF}`
        

    Instance Attributes
    -------------------
    q_obj : dict
        A copy of the quantization dictionary (see above)

    quant : string
        Quantization behaviour ('floor', 'round', ...)

    ovfl  : string
        Overflow behaviour ('wrap', 'sat', ...)
        
    frmt : string
        target output format ('frac', 'int', 'bin', 'hex')

    N_over : integer
        total number of overflows

    N_over_neg : integer
        number of negative overflows
        
    N_over_pos : integer
        number of positive overflows    

    LSB : float
        value of LSB (smallest quantization step)
        
    MSB : float
        value of most significant bit (MSB)
        
    Notes
    -----
    class Fixed() can be used like Matlabs quantizer object / function from the
    fixpoint toolbox, see (Matlab) 'help round' and 'help quantizer/round' e.g. 
    
    q_dsp = quantizer('fixed', 'round', [16 15], 'wrap'); % Matlab
    
    q_dsp = {'Q':'0.15', 'quant':'round', 'ovfl':'wrap'} # Python
    
    
    """
    def __init__(self, q_obj):
        """
        Initialize fixed object with dict q_obj
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
            if key not in ['Q','QF','QI','quant','ovfl','frmt']:
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
        if 'frmt' not in q_obj: q_obj['frmt'] = 'frac'
        
        self.q_obj = q_obj # store quant. dict in instance      
        self.quant = str(q_obj['quant']).lower()
        self.ovfl  = str(q_obj['ovfl']).lower()
        self.frmt = str(q_obj['frmt']).lower()
        self.QF = q_obj['QF']
        self.QI = q_obj['QI']
        self.W = self.QF + self.QI + 1
        
        self.LSB  = 2. ** (-q_obj['QF']) # value of LSB = 2 ^ (-WF)
        self.MSB  = 2. ** q_obj['QI']    # value of MSB = 2 ^ WI

        if self.frmt == 'int':
            self.digits = int(np.ceil(np.log10(self.W) * np.log10(2.))) # required number of digits for dec. repr.
        elif self.frmt == 'bin':
            self.digits = self.W # required number of digits for bin. repr.
        elif self.frmt == 'hex':
            self.digits = int(np.ceil(self.W / 4.)) # required number of digits for hex. repr.
        elif self.frmt == 'frac':
            self.digits = 4
        else:
            raise Exception(u'Unknown format "%s"!'%(self.frmt))


    def fix(self, y):
        """
        Return fixed-point representation yq of y (scalar or array-like), 
        yq.shape = y.shape

        Parameters
        ----------        
        y : scalar or array-like object
            to be quantized
    
        
        Returns
        -------
        yq : float or ndarray with the same shape as y
            The quantized input value(s) as a np.float64 or an ndarray with np.float64
            If this is not what you want, see examples.

        Example:
        --------
          
        >>> q_obj_a = {'QI':1, 'QF':6, 'ovfl':'sat', 'quant':'round'}
        >>> myQa = Fixed(q_obj_a) # instantiate fixed-point object myQa
        >>> myQa.resetN()  # reset overflow counter
        >>> a = np.arange(0,5, 0.05) # create input signal
    
        >>> aq = myQa.fixed(a) # quantize input signal
        >>> plt.plot(a, aq) # plot quantized vs. original signal
        >>> print(myQa.N_over, "overflows!") # print number of overflows
    
        >>> # Convert output to same format as input:
        >>> b = np.arange(200, dtype = np.int16)
        >>> btype = np.result_type(b)
        >>> # MSB = 2**7, LSB = 2**2:
        >>> q_obj_b = {'QI':7, 'QF':-2, 'ovfl':'wrap', 'quant':'round'} 
        >>> myQb = Fixed(q_obj_b) # instantiate fixed-point object myQb
        >>> bq = myQb.fixed(b)
        >>> bq = bq.astype(btype) # restore original variable type
        >>> 
    
        """
        y = np.real_if_close(y)
        if np.iscomplexobj(y):
            logger.warn("Casting complex values to real before quantization!")
            print("complex!")
            y = y.real()

        try:
            _ = len(y)
        except TypeError: # exception -> y is scalar:   
            SCALAR = True
            over_pos = over_neg = yq = 0
        else: # no exception -> y is array:
            # create empty arrays for result and overflows with same shape as y
            SCALAR = False
            y = np.asarray(y)
            yq = np.zeros(y.shape)
            over_pos = over_neg = np.zeros(y.shape, dtype = bool)
        # Quantize inputs
        if   self.quant == 'floor':  yq = self.LSB * np.floor(y / self.LSB)
             # largest integer i, such that i <= x (= binary truncation)
        elif self.quant == 'round':  yq = self.LSB * np.round(y / self.LSB)
             # rounding, also = binary rounding
        elif self.quant == 'fix':    yq = self.LSB * np.fix(y / self.LSB)
             # round to nearest integer towards zero ("Betragsschneiden")
        elif self.quant == 'ceil':   yq = self.LSB * np.ceil(y / self.LSB)
             # smallest integer i, such that i >= x
        elif self.quant == 'rint':   yq = self.LSB * np.rint(y / self.LSB)
             # round towards nearest int 
        elif self.quant == 'none':   yq = y
        else: 
            raise Exception('Unknown Requantization type "%s"!'%(self.quant))
        
        # Handle Overflow / saturation        
        if   self.ovfl == 'none': 
            pass
        else:
            # Bool. vectors with '1' for every neg./pos overflow:
            over_neg = (yq < -self.MSB)
            over_pos = (yq >= self.MSB)
            # No. of pos. / neg. / all overflows occured since last reset:
            self.N_over_neg += np.sum(over_neg)
            self.N_over_pos += np.sum(over_pos)
            self.N_over = self.N_over_neg + self.N_over_pos

            # Replace overflows with Min/Max-Values (saturation):           
            if self.ovfl == 'sat':
                yq = np.where(over_pos, self.MSB-self.LSB, yq) # (cond, true, false)
                yq = np.where(over_neg, -self.MSB, yq)
            # Replace overflows by two's complement wraparound (wrap)
            elif self.ovfl == 'wrap':
                yq = np.where(over_pos | over_neg,
                    yq - 2. * self.MSB*np.fix((np.sign(yq)* self.MSB+yq)/(2*self.MSB)),
                    yq)
            else:
                raise Exception('Unknown overflow type "%s"!'%(self.overfl))
                return None
        if self.frmt == 'frac':
                return yq
        if self.frmt in {'hex', 'bin', 'int'}:
            yq = (np.round(yq * 2. ** self.QF)).astype(int) # shift left by QF bits
        if self.frmt == 'hex':
            if SCALAR:
                return hex2(yq, nbits=self.W)
            else:
                return vhex2(yq, nbits=self.W)
        elif self.frmt == 'bin':
            if SCALAR:
                 return np.binary_repr(yq, width=self.W)
            else:
                return vbin(yq, width=self.W)
        elif self.frmt == 'int':
            return yq
        else:
            raise Exception('Unknown output format "%s"!'%(self.format))
            return None
         
#==============================================================================            
            
    def resetN(self):
        """ Reset overflow-counters of Fixed object"""
        self.N_over = 0
        self.N_over_neg = 0
        self.N_over_pos = 0
            
class FIX_filt_MA(Fixed):
    """
    Usage:
    Q = FIX_filt_MA(q_mul, q_acc) # Instantiate fixpoint filter object 
    x_bq = self.Q_mul.fxp_filt(x[k:k + len(bq)] * bq) 
    
    The fixpoint object has two different quantizers:
    - q_mul describes requanitization after coefficient multiplication
    - q_acc describes requanitization after each summation in the accumulator
            (resp. in the common summation point)
            
    """
    def __init__(self, q_mul, q_acc):
        """
        Initialize fixed object with q_obj
        """
        # test if all passed keys of quantizer object are known
        self.Q_mul = Fixed(q_mul)
        self.Q_mul.resetN() # reset overflow counter of Q_mul
        self.Q_acc = Fixed(q_acc)
        self.Q_acc.resetN() # reset overflow counter of Q_acc
        self.resetN() # reset filter overflow-counter	
	

    def fxp_filt_df(self, x, bq, verbose = True):
        """
        Calculate filter (direct form) response via difference equation with 
        quantization
        
        Parameters
        ----------
        x : scalar or array-like
            input value(s)
        
        bq : array-like
            filter coefficients
            
        Returns
        -------
        yq : ndarray
            The quantized input value(s) as an ndarray with np.float64. If this is
            not what you want, see examples.
     
        
        """

        # Initialize vectors (also speeds up calculation)
        yq = accu_q = np.zeros(len(x))
        x_bq = np.zeros(len(bq))
        
        for k in range(len(x) - len(bq)):
            # weighted state-vector x at time k:
            x_bq = self.Q_mul.fix(x[k:k + len(bq)] * bq) 
            # sum up x_bq to get accu[k]
            accu_q[k] = self.Q_acc.fix(sum(x_bq)) 
        yq = accu_q # scaling at the output of the accumulator

        if (self.Q_mul.N_over and verbose): print('Overflows in Multiplier:  ',
                Fixed.Q_mul.N_over)
        if (self.Q_acc.N_over and verbose): print('Overflows in Accumulator: ',
                self.Q_acc.N_over)
        self.N_over = self.Q_mul.N_over + self.Q_acc.N_over
             
        return yq
    
# nested loop would be much slower!
#  for k in range(Nx - len(bq)):
#	for i in len(bq):
#	  accu_q[k] = fixed(q_acc, (accu_q[k] + fixed(q_mul, x[k+i]*bq[i+1])))

#----------------------------------------------------------------------
#============ not working yet =================================================
# class FIX_filt_MA(Fixed):
#     """
#     yq = FIX_filt_MA.fixFilt(x,aq,bq,gq)
# 	FIR-Filter mit verschiedenen internen Quantisierungen: 
# 	q_mul beschreibt Requantisierung nach Koeffizientenmultiplikation
# 	q_acc beschreibt Requantisierung bei jeder Summation im Akkumulator 
# 	(bzw. gemeinsamen Summenpunkt)
#     """
#     def __init__(self, q_mul, q_acc):
#         """
#         Initialize fixed object with q_obj
#         """
#         # test if all passed keys of quantizer object are known
#         self.setQobj(q_mul)
#         self.resetN() # initialize overflow-counter	
# 
# 	
# # Calculate filter response via difference equation with quantization:
# 
#     def fixFilt(x, bq, aq, gq, q_mul, q_acc, verbose = True):
#         
#         # Initialize vectors (also speeds up calculation)
#     #    Nx = len(x)
#     #    s = zeros(Nx) # not needed in this filter
#         yq = accu_q = np.zeros(len(x))
#     #    bq_len = len(bq)
#         x_bq = np.zeros(len(bq))
#         
#         for k in range(len(x) - len(bq)):
#             # weighted state-vector x at time k:
#             x_bq, N_over_m = Fixed.fix(q_mul, x[k:k + len(bq)] * bq)
#             # sum up x_bq to get accu[k]
#             accu_q[k], N_over_a = Fixed.fix(q_acc, sum(x_bq))
#         yq = accu_q * gq # scaling at the output of the accumulator
#         s = x # copy state-vector
#         if (N_over_m and verbose): print('Overflows in Multiplier:  ', N_over_m)
#         if (N_over_a and verbose): print('Overflows in Accumulator: ', N_over_a)
#
#       return yq
#
#==============================================================================
             
    
# nested loop would be much slower!
#  for k in range(Nx - len(bq)):
#	for i in len(bq):
#	  accu_q[k] = fixed(q_acc, (accu_q[k] + fixed(q_mul, x[k+i]*bq[i+1])))

def csdigit(num, WI=0, WF=15):
    """
     Returns the canonical signed digit representation of the input number.
     Useful for simple DSP implementations of multipliers.
        [digits,pos,neg,err]=csdigit(num,WI,WF)
    
     example csdigit(23) returns +0-00-.
             Where +0-00-. is a representation of +1 in 2**5, -1 in 2**3 and -1 in 2**0 positions.
             i.e. 23 = 32 - 8 -1
    
     example [a,p,n]=csdigit(23.5,6,2) returns
                a = +0-000.-0
                p=32
                n=8.5
                23.5 = 32 - 8 -.5
    
     num   : input number (decimal)
     WI    : maximum digits to the left of the decimal point
     WF    : digits to the right of decimal point
     for example
        csdigit(.25,2,2) represents xx.xx binary
        csdigit(.25,0,4) represents .xxxx binary
     Note: An error is generated if num does not fit inside the representation.
           It is truncated to the specified resolution WF.
     Note: A warning message is generated if num doesn't fit in the precision
           specified. The returned value is truncated.
     Note: The WI is not used except for a check for overflow and to add
           leading zeros.
    
     Patrick J. Moran
     AirSprite Technologies Inc.
    
     Copyright 2006, Patrick J. Moran for AirSprite Technologies Inc.
     Redistribution and use in source and binary forms, with or without modification, 
     are permitted provided that the following conditions are met:
     
        1. Redistributions of source code must retain the above copyright notice.
        2. Any derivative of this work must credit the author, and must be made available to everyone.
        3. The name of the author may not be used to endorse or promote products derived 
           from this software without specific prior written permission.
    
     THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, 
     INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
     PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, 
     INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
     LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
     OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
     CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY 
     WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
     """

    def findstr(string, char):
        """ return a list with the indices of all occurences of char in string """
        idx = []
        for i in range(len(string)):
            if string[i] == char:
                idx.append[i]
        return idx
            
    if not num:
        help(csdigit)
        return
    
    targetNum=num;
    num = abs(num)/(2**(-WF));
    if num != np.floor(num):
        if np.floor(num) == 0:
            logger.error('Insufficient precision to represent this number!')
        else:
            logger.warning('Some precision has been lost. Returned value is truncated!')
    
    num = np.floor(num);
    if num > 2**(WI+WF):
        logger.error('Input number is too large for the requested bit representation.');
    
    binNum = np.binary_repr(num, WI + WF) # +1? 
    digits=('0'+0) * np.ones(len(binNum))
    #%allZeros=allZeros;
    onesLoc = findstr(binNum, '1')
    if onesLoc:
        onesRun=find(diff(onesLoc)==1)
        while not onesRun:
            onesPointer=find(diff(onesLoc)==1)+1;
            addIn=onesLoc(onesPointer(end));
            adder=('0'+0)*np.ones(len(binNum))
            adder[addIn]=('1'+0);
            # keep track of the additional digits
            digits[addIn]=('-'+0);
            binAdder=char(adder);
            binNum=dec2bin(bin2dec(binNum)+bin2dec(binAdder),WI+WF);
            onesLoc=findstr(binNum,'1');
            onesRun=find(diff(onesLoc)==1);
            if len(binNum) > len(digits):
                digits=['0'+0,digits] # add any additional leading zero
            
    pos=bin2dec(binNum)*2**(-WF);
    negLoc=find(digits==('-'+0));
    neg=('0'+0) * np.ones(size(binNum));
    neg[negLoc]='1'+0;
    neg=bin2dec(char(neg))*2**(-WF);
    digits[onesLoc]='+'+0;
    if (len(digits)-WF)>WI:
        logger.warning('Number overflowed for this CSD representation')
    
    if len(digits)<WF:
        digits=[digits,('0'+0) * np.ones(WF-len(digits))]
    
    #digits = char([digits[0:len(digits)-WF], '.'+0, digits[len(digits)-WF+1:-1])
#    digits = char()
    if targetNum < 0: # flip representation if negative
        ntemp=neg
        neg=pos
        pos=ntemp
        digits = strrep(digits,'+','p')
        digits = strrep(digits,'-','+')
        digits = strrep(digits,'p','-')
    
    # %digits=char(digits);
    err = targetNum - (pos-neg)
    
    return (digits, pos, neg, err)

#######################################
# If called directly, do some example #
#######################################
if __name__=='__main__':
    pass
