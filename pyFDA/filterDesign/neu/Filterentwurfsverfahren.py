# -*- coding: utf-8 -*-
"""
Created on Sun Jan 05 12:47:40 2014

@author: Acer
"""

class Filterentwurfsverfahren():
    def __init__(self):
        self.initUI()
        
    def initUI(self): 
        print ""
        
    def needHP(self):
        print ""
    
    
class cheby1(Filterentwurfsverfahren):
    def __init__(self):
        self.initUI()
        
    def initUI(self): 
        print ""
        
    def needHP(self):
        return {"Order":{"man":True,"spez":False},"Frequenz":{"Fs":48000,"Fpass":14400},"Betrag":{"typ":"ub","Astop":20,"Apass":1}}

class cheby2(Filterentwurfsverfahren):
    def __init__(self):
        self.initUI()
        
    def initUI(self): 
        print ""
        
    def needHP(self):
        return {"Order":{"man":False,"spez":False},"Frequenz":{"Fs":48000,"Fpass":14400},"Betrag":{"typ":"ub","Astop":20,"Apass":1}}
