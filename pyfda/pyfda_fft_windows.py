# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Store the available fft windows and their properties
"""
import logging
logger = logging.getLogger(__name__)

import numpy as np
from numpy import pi, sqrt
import scipy.signal as sig


windows =\
    {'Boxcar':
        {'fn_name':'boxcar', 
         'tooltip':
             ("<span>Rectangular window, well suited for coherent signals, i.e. "
              " where the window length is an integer number of the signal's period.</span>"),
        'props':{
            'enbw':1,
            'cgain':1,
            'bw':1
            }
         },
    'Barthann':
        {'fn_name':'barthann',
         'tooltip':
             ("<span>A modified Bartlett-Hann Window."
              "</span>")},
    'Bartlett':
        {'fn_name':'bartlett'},
    'Blackman':
        {'fn_name':'blackman'},
    'Blackmanharris':
        {'fn_name':'blackmanharris',
         'tooltip':
             ("<span>The minimum 4-term Blackman-Harris window with excellent side-"
              "lobe suppression.</span>")
             },
    'Bohman':
        {'fn_name':'bohman'},
    'Chebwin':
        {'fn_name':'chebwin',
         'par':[['Attn.'],[80], ["<span>Side lobe attenuation in dB (typ. 80 dB).</span>"]],
         'tooltip':
             ("<span>This window optimizes for the narrowest main lobe width for "
              "a given order <i>M</i> and sidelobe equiripple attenuation <i>Attn.</i>, "
              "using Chebyshev polynomials.</span>"),
        },
    'Cosine':{},
    'Flattop':
         {'win_fn_name':'flattop'},
    'General_Gaussian':{},
    'Gaussian':{},
    'Hamming':
        {'fn_name':'hamming',
         'tooltip':
         ("<span>This window is smooth at the edges and has a fall-off rate of "
          "18 dB/oct.</span>")
         },
    'Hann':{},
    'Kaiser':
        {'fn_name':'kaiser',
         'par':[['beta'],[10],
                ["<span>Shape parameter; lower values reduce  main lobe width, "
                 "higher values reduce side lobe level, typ. in the range 5 ... 20.</span>"]],
         'tooltip':
             ("<span>The Kaiser window is a very good approximation to the "
              "Digital Prolate Spheroidal Sequence, or Slepian window, which is "
              "which maximizes the energy in the main lobe of the window relative "
              "to the total energy.</span>")
        },
    'Nuttall':{},
    'Parzen':{},
    'Slepian':{},
    'Triang':{}
    }

def calc_window_function(win_dict, win_name):
    
    N_par = 0
    txt_par = ""

    if win_name in {"Bartlett", "Triangular"}:
        win_fnct_name = "bartlett"
    elif win_name == "Flattop":
        win_fnct_name = "flattop"
    elif win_name == "Hamming":
        win_fnct_name = "hamming"
    elif win_name == "Hann":
        win_fnct_name = "hann"
    elif win_name == "Rect":
        win_fnct_name = "boxcar"
    #--------------------------------------
    elif win_name == "Kaiser":
        win_fnct_name = "kaiser"
        N_par = 1
        txt_par = '&beta; ='
        tooltip = ("<span>Shape parameter; lower values reduce  main lobe width, "
                   "higher values reduce side lobe level, typ. in the range 5 ... 20.</span>")
        _get_param()
        #if not self.param:
         #   _set_param(5)
    #--------------------------------------
    elif win_name == "Chebwin":
        win_fnct_name = "chebwin"
        N_par = 1
        txt_par = 'Attn ='
        tooltip = ("<span>Side lobe attenuation in dB (typ. 80 dB).</span>")
        _get_param()
        if not self.param:
            self.param = 80
        if self.param < 45:
            _set_param(45)
            logger.warning("Attenuation needs to be larger than 45 dB!")
    else:
        logger.error("Unknown window type {0}".format(win_name))

    # get attribute win_fnct_name from submodule sig.windows and
    # return the desired window function:
    win_fnct = getattr(sig.windows, win_fnct_name, None)
    
    if not win_fnct:
        logger.error("No window function {0} in scipy.signal.windows, using rectangular window instead!"\
                     .format(win_fnct_name))
        win_fnct = sig.windows.boxcar
        self.param = None
        
    win_dict['win_name'] = win_name
    win_dict['win_fnct'] = win_fnct_name
    if N_par == 1:
        win_dict['win_params'] = self.param
    else:
        win_dict['win_params'] = ''
    win_dict['win_len']  = self.N
    
return win_fnct
