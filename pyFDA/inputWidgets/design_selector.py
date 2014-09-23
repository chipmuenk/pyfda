# -*- coding: utf-8 -*-
"""
Created on Wed Dec 04 08:04:59 2013

@author: Christian Muenker
"""

from filterDesign import iir_basic #, fir_basic

def select(params):
    status = iir_basic.iir_basic(params)
    return status
   
 
def conversion(frm, to, arr, fs=1): 
    units={"Hz":1.0, "kHz":1000.0, "MHz":1000000.0, "GHz":1000000000.0, 
    "norm":(fs/2)}  
  
    a = units[frm] / units[to] * arr
    print "a = " + str(units[frm])+"/"+str(units[to])+"*"+str(arr)
    print a
    
conversion("kHz", "Hz" , 5)
conversion("Hz", "norm", 50, 200)
conversion("Hz", "norm", 5, 100)
conversion("norm", "kHz", 0.1, 10000000)