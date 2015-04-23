# -*- coding: utf-8 -*-
"""
filterbroker.py

Created on Wed Dec 03 06:13:50 2014

http://stackoverflow.com/questions/13034496/using-global-variables-between-files-in-python
oder
http://pymotw.com/2/articles/data_persistence.html

@author: Christian Muenker
"""

# TODO: dmNames need to be built automatically!

from __future__ import print_function, division, unicode_literals
# importing filterbroker runs the module once, defining all globals and variables
#global gD # dicts are global by default?



gD = {}
gD['rc'] = {'lw':1.5, 'font.size':14} # rc Params for matplotlib
gD['N_FFT'] = 2048 # number of FFT points for plot commands (freqz etc.)

# Dictionaries for translating short (internal) names to full (displayed) names
gD['rtNames'] = {"LP":"Lowpass", "HP":"Highpass", "BP":"Bandpass",
                 "BS":"Bandstop", "AP":"Allpass", "MB":"Multiband",
                 "HIL":"Hilbert", "DIFF":"Differentiator"}
gD['dmNames'] = {#IIR
                  "butter":"Butterworth", "cheby1":"Chebychev 1",
                  "cheby2":"Chebychev 2", "ellip":"Elliptic",
                  # FIR:
                  "equiripple":"Equiripple", "firls":"Least-Square",
                  "firwin":"Windowed"}

#==============================================================================
# The following entries are created and updated dynamically during program
# execution. The entries only demonstrate the structure of the dicts and lists
# or are used as initial / default entries.
# -----------------------------------------------------------------------------
# -----FilterFileReader.__init__() ------

# Lists for dynamic imports from filter design subdirectory
gD['filtFileNames'] = [] # Python file names found in filtFile (without .py)
gD['imports'] = {} # dict with filter files / classes
    
# Dictionary describing the available combinations of response types (rt),
# filter types (ft), design methods (dm) and filter order (fo).
# This dict is built + overwritten by FilterFileReader.buildFilterTree() !
filTree = {
    'HP':
        {'FIR':
            {'equiripple':
                {'man': {"par":['N', 'A_PB', 'F_PB']},
                 'min': {"par":['A_PB', 'A_SB', 'F_PB', 'F_SB']}}},
         'IIR':
             {'cheby1':
                 {'man': {"par":['N', 'A_PB', 'F_PB']},
                  'min': {"par":['A_PB', 'A_SB', 'F_PB', 'F_SB']}},
              'cheby2':
                  {'man': {"par":['N', 'A_SB', 'F_SB']},
                   'min': {"par":['A_PB', 'A_SB', 'F_PB', 'F_SB']}}}},
    'BP':
        {'FIR':
            {'equiripple':
                {'man': {"par":['N', 'F_PB', 'F_PB2', 'F_SB', 'F_SB2', 'W_PB', 'W_SB', 'W_SB2']}}},
         'IIR':
             {'cheby1': {'man': {"par":['N', 'A_PB', 'F_PB', 'F_PB2']},
                         'min': {"par":['A_PB', 'A_SB', 'F_PB', 'F_PB2', 'F_SB', 'F_SB2']}},
              'cheby2': {'man': {"par":['N', 'A_SB', 'F_SB', 'F_SB2']},
                         'min': {"par":['A_PB', 'A_SB', 'F_PB', 'F_PB2', 'F_SB', 'F_SB2']}}}},
    'LP':
        {'FIR':
            {'equiripple':
                {'man': {"par":['N', 'A_PB', 'F_PB']},
                 'min': {"par":['A_PB', 'A_SB', 'F_PB', 'F_SB']}}},
         'IIR':
             {'cheby1':
                 {'man': {"par":['N', 'A_PB', 'F_PB']},
                  'min': {"par":['A_PB', 'A_SB', 'F_PB', 'F_SB']}},
             'cheby2': {'man': {"par":['N', 'A_SB', 'F_SB']},
                        'min': {"par":['A_PB', 'A_SB', 'F_PB', 'F_SB']}}}},
    }


# -----------------------------------------------------------------------------
# Dictionaries containing current filter specifications, they are
# automatically overwritten
#--------------------------------------
# Handle to current filter object
filObj = ""
# Current filter selection, parameters and specifications
fil = [None] * 10 # create empty list with length 10 for filter designs

fil[0] = {'rt':'LP', 'ft':'FIR', 'dm':'equiripple', 'fo':'man',
            'N':10, 'f_S':1,
            'A_PB':0.1, 'A_PB2': 1., 'F_PB':0.1, 'F_PB2':0.4,
            'A_SB':60., 'A_SB2': 60., 'F_SB':0.2, 'F_SB2':0.3,
            'W_PB':1., 'W_PB2':1., 'W_SB':1., 'W_SB2':1.,
            #
            'coeffs':([1, 1, 1], [3, 0, 2]), # tuple of bb, aa
            'zpk':([-0.5 + 3**0.5/2.j, -0.5 - 3**0.5/2.j],
                   [(2./3)**0.5 * 1j, -(2./3)**0.5 * 1j], 1),
            'creator':('ba','filterbroker'), #(format ['ba', 'zpk', 'sos'], routine)
            'freqSpecsRangeType':'Half',
            'freqSpecsRange': [0,0.5],
            'plt_fLabel':r'$f$ in Hz $\rightarrow$',
            'plt_fUnit':'Hz',
            'plt_tLabel':r'$n \; \rightarrow$',
            'plt_tUnit':'s',
            'plt_phiUnit': 'rad',
            'plt_phiLabel': r'$\angle H(\mathrm{e}^{\mathrm{j} \Omega})$  in rad ' + r'$\rightarrow $'
            }

