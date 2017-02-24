# -*- coding: utf-8 -*-
"""
Created on Fri Feb 24 15:53:42 2017

@author: Christian Muenker
"""
import sys
from distutils.version import LooseVersion
from numpy import __version__ as VERSION_NP
from scipy import __version__ as VERSION_SCI
from matplotlib import __version__ as VERSION_MPL
from .compat import QT_VERSION_STR

import logging
logger = logging.getLogger(__name__)


VERSION = {}
VERSION.update({'python_long': sys.version})
VERSION.update({'python': ".".join(map(str, sys.version_info[:3]))})
VERSION.update({'matplotlib': VERSION_MPL})
VERSION.update({'pyqt': QT_VERSION_STR})
VERSION.update({'numpy': VERSION_NP})
VERSION.update({'scipy': VERSION_SCI})


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
    if mod:
        return LooseVersion(VERSION[mod])
    else:
        v = ""
        keys = sorted(list(VERSION.keys()))
        for k in keys:
            v += "{0: <11} : {1}\n".format(k, LooseVersion(VERSION[k]))
        return v   
        
logger.info(mod_version())
print(mod_version())