# -*- coding: utf-8 -*-
"""
Created on Fri Feb 24 15:53:42 2017

@author: Christian Muenker
"""
import sys
from distutils.version import LooseVersion

import logging
logger = logging.getLogger(__name__)

# ================ Required Modules ============================
from numpy import __version__ as VERSION_NP
from scipy import __version__ as VERSION_SCI
from matplotlib import __version__ as VERSION_MPL
from .compat import QT_VERSION_STR # imports pyQt

VERSION = {}
VERSION.update({'python_long': sys.version})
VERSION.update({'python': ".".join(map(str, sys.version_info[:3]))})
VERSION.update({'matplotlib': VERSION_MPL})
VERSION.update({'pyqt': QT_VERSION_STR})
VERSION.update({'numpy': VERSION_NP})
VERSION.update({'scipy': VERSION_SCI})

# ================ Optional Modules ============================
try:
    from mayavi import __version__ as VERSION_MAYAVI
    VERSION.update({'mayavi': VERSION_MAYAVI})
except ImportError:
    logger.info("Module mayavi not found.")
    
try:
    from myhdl import __version__ as VERSION_HDL
    VERSION.update({'myhdl': VERSION_HDL})
except ImportError:
    logger.info("Module myhdl not found.")



def cmp_version(mod, version):
    """
    Compare version number of installed module `mod` against string `version` and 
    return 1, 0 or -1 if the installed version is greater, equal or less than 
    the number in `version`.
    """
    if LooseVersion(VERSION[mod]) > LooseVersion(version):
        return 1
    elif  LooseVersion(VERSION[mod]) == LooseVersion(version):
        return 0
    else:
        return -1

def mod_version(mod = None):
    """
    Return the version of the module 'mod'. If the module is not found, return
    None. When no module is specified, return a string with all modules and 
    their versions sorted alphabetically.
    """
    if mod:
        if mod in VERSION:
            return LooseVersion(VERSION[mod])
        else:
            return None
    else:
        v = ""
        keys = sorted(list(VERSION.keys()))
        for k in keys:
            v += "{0: <11} : {1}\n".format(k, LooseVersion(VERSION[k]))
        return v   
        
logger.info(mod_version())
print(mod_version())