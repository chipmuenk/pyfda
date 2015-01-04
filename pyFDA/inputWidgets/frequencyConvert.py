# -*- coding: utf-8 -*-
"""
Created on Wed Dec 04 08:04:59 2013

Conversion of frequency units between Hz, kHz, normalized frequencies ...

@author: Christian Muenker
"""
from __future__ import division, print_function, unicode_literals

class Freq(object):
    """
    See Mark Summerfield, "Rapid GUI Programming with Python and Qt", pp. 86 ff
    """
    units={"Hz":1.0, "kHz":1e3, "MHz":1e6, "GHz":1e9}#, "norm":(fs/2)}  
    numbers = frozenset("0123456789.eE")

    def __init__(self, f = None):
        if f is None:
            self.__frequency = 0.0
        else:
            digits = ""
            for i, char in enumerate(f):
                if char in Freq.numbers:
                    digits += char
                else:
                    self.__frequency = float(digits)
                    unit = f[i:].strip()
                    break
            else:
                raise ValueError, "need an amount and a unit"
            self.__frequency *= Freq.units[unit]
            
    def set(self, f):
        """Sets the frequency to the new given frequency

        >>> x = Freq("3MHz")
        >>> round(x.to("kHz"))
        3000.0
        >>> x.set("5 Hz")
        >>> round(x.to("kHz"))
        0.005
        """
        self.__init__(f)
        
    def to(self, unit):
        return self.__frequency / Freq.units[unit]
        
    def copy(self):
        """Returns a unique copy of the length
        """

        return eval(repr(self))
        
    @staticmethod
    def myUnits():
        return Freq.units.keys()
        
    # Special methods to 
        
    def __repr__(self):
        """
        >>> repr(Freq("2.5kHz"))
        "Freq('2500.000000 Hz')"
        """
        return "Length('{0:.6f}m')".format(self.__frequency)


    def __str__(self):
        """
        >>> str(Freq("2 GHz"))
        '200000000 Hz'
        """
        return "%.3f Hz" % self.__frequency
#        return "{0:.3f}m".format(self.__frequency)
        
    def __add__(self, other):
        """
        >>> x = Freq("10Hz")
        >>> y = Freq("10kHz")
        >>> x = x + y
        >>> x, str(x), round(float(x), 3)
        (Freq('26093.444979m'), '26093.445m', 26093.445)
        """
#        >>> x + 5
#        Traceback (most recent call last):
#        ...
#        AttributeError: 'int' object has no attribute '_Length__amount'

        return Freq("{0:f}Hz".format((self.__frequency + other.__frequency)))
        

#    a = units[frm] / units[to] * arr
#    return a
# 
#    def conversion(frm, to, arr, fs=1): 
#
#        units={"Hz":1.0, "kHz":1e3, "MHz":1e6, "GHz":1e9, "norm":(fs/2)}  
#        numbers = frozenset("0123456789.eE")
#        a = units[frm] / units[to] * arr
#        return a
    
#print "a = " + str(units[frm])+"/"+str(units[to])+"*"+str(arr)
#print a
    #------------------------------------------------------------------------------ 
   
if __name__ == '__main__':
    a = Freq("1 Hz")
    b = Freq("1 kHz")
#    print(a + b)
    a.set("5MHz")
    print(a.to("kHz"))
    x = Freq("10Hz")
    y = Freq("10kHz")
    x = x + y
    print(x, str(x))#, round(float(x), 3))
#print (conversion("3 kHz", "Hz" , 5))
#conversion("Hz", "norm", 50, 200)
#conversion("Hz", "norm", 5, 100)
#conversion("norm", "kHz", 0.1, 10000000)