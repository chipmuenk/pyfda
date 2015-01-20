# -*- coding: utf-8 -*-
"""
filterbroker.py

Created on Wed Dec 03 06:13:50 2014

http://stackoverflow.com/questions/13034496/using-global-variables-between-files-in-python
oder
http://pymotw.com/2/articles/data_persistence.html

@author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals
# importing filterbroker runs the module once, defining all globals and variables
global gD
gD = {}
gD['rc'] = {'lw':1.5, 'font.size':12} # rc Params for matplotlib
gD['N_FFT'] = 2048 # number of FFT points for plot commands (freqz etc.)

# Dictionaries for translating short (internal) names to full (displayed) names
gD['rtNames'] = {"LP":"Lowpass", "HP":"Highpass", "BP":"Bandpass",
                 "BS":"Bandstop","AP":"Allpass", 
                 "HIL":"Hilbert","DIFF":"Differentiator"}
gD['dmNames'] = {#IIR
                  "butter":"Butterworth", "cheby1":"Chebychev 1", 
                  "cheby2":"Chebychev 2",  "ellip":"Elliptic",
                  # FIR:                  
                  "equiripple":"Equiripple", "firls":"Least-Square",
                  "window":"Windowed"}

#==============================================================================
# The following entries are created and updated dynamically during program 
# execution. The entries only demonstrate the structure of the dicts and lists
# or are used as initial / default entries.
# -----------------------------------------------------------------------------
# -----FilterFileReader.__init__() ------

# Lists for dynamic imports from filter design subdirectory
gD['initFileNames'] = [] # Python file names found in initFile (without .py)
gD['imports'] = {} # dict with filter files / classes

# Dictionary describing the available combinations of response types (rt), 
# filter types (ft), design methods (dm) and filter order (fo). 
# This dict is built + overwritten by FilterFileReader.buildFilterTree() !
         
gD['filterTree'] = {
    'HP': 
        {'FIR': 
            {'equiripple': 
                {'man': {"par":['N', 'A_pb', 'F_pb']}, 
                 'min': {"par":['A_pb', 'A_sb', 'F_pb', 'F_sb']}}}, 
         'IIR':
             {'cheby1': 
                 {'man': {"par":['N', 'A_pb', 'F_pb']}, 
                  'min': {"par":['A_pb', 'A_sb', 'F_pb', 'F_sb']}}, 
              'cheby2': 
                  {'man': {"par":['N', 'A_sb', 'F_sb']},
                   'min': {"par":['A_pb', 'A_sb', 'F_pb', 'F_sb']}}}}, 
    'BP': 
        {'FIR': 
            {'equiripple': 
                {'man': {"par":['N', 'F_pb', 'F_pb2', 'F_sb', 'F_sb2', 'W_pb', 'W_sb', 'W_sb2']}}}, 
         'IIR': 
             {'cheby1': {'man': {"par":['N', 'A_pb', 'F_pb', 'F_pb2']}, 
                         'min': {"par":['A_pb', 'A_sb', 'F_pb', 'F_pb2', 'F_sb', 'F_sb2']}}, 
              'cheby2': {'man': {"par":['N', 'A_sb', 'F_sb', 'F_sb2']}, 
                         'min': {"par":['A_pb', 'A_sb', 'F_pb', 'F_pb2', 'F_sb', 'F_sb2']}}}}, 
    'LP': 
        {'FIR': 
            {'equiripple': 
                {'man': {"par":['N', 'A_pb', 'F_pb']}, 
                 'min': {"par":['A_pb', 'A_sb', 'F_pb', 'F_sb']}}}, 
         'IIR': 
             {'cheby1': 
                 {'man': {"par":['N', 'A_pb', 'F_pb']}, 
                  'min': {"par":['A_pb', 'A_sb', 'F_pb', 'F_sb']}}, 
             'cheby2': {'man': {"par":['N', 'A_sb', 'F_sb']}, 
                        'min': {"par":['A_pb', 'A_sb', 'F_pb', 'F_sb']}}}},
    }


# -----------------------------------------------------------------------------
# Dictionaries containing current filter selections specifications, they are
# automatically overwritten 
#-------------------------------------- 
# Current filter selection, parameters and specifications              
gD['selFilter'] = {"rt":"LP", "ft":"FIR", "dm":"equiripple", "fo":"man",
                'N':10, 'fS': 48000,
                'A_pb':1., 'A_pb2': 1, 'F_pb':0.1, 'F_pb2':0.4,
                'A_sb':60., 'A_sb2': 60, 'F_sb':0.2, 'F_sb2':0.3,
                'W_pb':1, 'W_pb2':1, 'W_sb':1, 'W_sb2':1}

gD['coeffs'] = ([1,1,1],[3,0,2])
gD['zpk'] = ([-0.5 + 3**0.5/2.j, -0.5 - 3**0.5/2.j],
            [(2./3)**0.5 * 1j, -(2./3)**0.5 * 1j], 1)
            


    



"""
Alternative: Use the shelve module


import shelve

### write to database:
s = shelve.open('test_shelf.fb')
try:
    s['key1'] = { 'int': 10, 'float':9.5, 'string':'Sample data' }
finally:
    s.close()

### read from database:   
s = shelve.open('test_shelf.fb')
# s = shelve.open('test_shelf.fb', flag='r') # read-only
try:
    existing = s['key1']
finally:
    s.close()

print(existing)

### catch changes to objects, store in in-memory cache and write-back upon close
s = shelve.open('test_shelf.fb', writeback=True)
try:
    print s['key1']
    s['key1']['new_value'] = 'this was not here before'
    print s['key1']
finally:
    s.close()
    
"""