# -*- coding: utf-8 -*-
"""
databroker.py

Created on Wed Dec 03 06:13:50 2014

http://stackoverflow.com/questions/13034496/using-global-variables-between-files-in-python
oder
http://pymotw.com/2/articles/data_persistence.html

@author: Christian Muenker
"""

# importing databroker runs the module once, defining all globals and variables
global gD
gD = {}
gD['rc'] = {'lw':1.5}
gD['N_FFT'] = 2048
gD['coeffs'] = ([1,1,1],[3,0,2])
gD['zpk'] = ([-0.5 + 3**0.5/2.j, -0.5 - 3**0.5/2.j],
            [(2./3)**0.5 * 1j, -(2./3)**0.5 * 1j], 1)
gD['specs'] = {'Order':10, 
            'A_pass1':1., 'A_pass2': 1, 'F_pass1':0.1, 'F_pass2':0.4,
            'A_stop1':60., 'A_stop2': 60, 'F_stop1':0.2, 'F_stop2':0.3}

#def init():
#    """
#    Initialize global dictionary gD for data exchange between modules
#    The module is executed upon import anyway, but providing a dedicated
#    init() functions prevents other modules from accidentally modifying 
#    the dictionary (?)
#    """
#    global gD
#    gD = {}
#    gD['N_FFT'] = 2048
#    gD['coeffs'] = ([1,1,1],[3,0,2]) # notch @ F = 1/3
    



"""
Alternative: Use the shelve module


import shelve

### write to database:
s = shelve.open('test_shelf.db')
try:
    s['key1'] = { 'int': 10, 'float':9.5, 'string':'Sample data' }
finally:
    s.close()

### read from database:   
s = shelve.open('test_shelf.db')
# s = shelve.open('test_shelf.db', flag='r') # read-only
try:
    existing = s['key1']
finally:
    s.close()

print(existing)

### catch changes to objects, store in in-memory cache and write-back upon close
s = shelve.open('test_shelf.db', writeback=True)
try:
    print s['key1']
    s['key1']['new_value'] = 'this was not here before'
    print s['key1']
finally:
    s.close()
    
"""