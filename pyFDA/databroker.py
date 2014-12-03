# -*- coding: utf-8 -*-
"""
databroker.py

Created on Wed Dec 03 06:13:50 2014

http://stackoverflow.com/questions/13034496/using-global-variables-between-files-in-python
oder
http://pymotw.com/2/articles/data_persistence.html

@author: Christian Muenker
"""


def init():
    """
    Initialize global dictionary gD for data exchange between modules
    The module is executed upon import anyway, but providing a dedicated
    init() functions prevents other modules from accidentally modifying 
    the dictionary (?)
    """
    global gD
    gD = {}
    gD['N_FFT'] = 2048
    



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