# -*- coding: utf-8 -*-
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE in root directory for details)

"""

"""
from __future__ import print_function
import os
import platform
import tempfile
import time
print("dirfinder is here!")
time.sleep(5)

OS     = platform.system()
OS_VER = platform.release()

#------------------------------------------------------------------------------
# taken from http://matplotlib.1069221.n5.nabble.com/Figure-with-pyQt-td19095.html
def valid(path):
    """ Check whether path exists and is valid"""
    if path and os.path.isdir(path):
        return True
    return False

def env(name):
    """Get value for environment variable"""
    return os.environ.get( name, '' )

def get_home_dir():
    """Return the user's home directory"""
    if OS != "Windows":
    # set user and logging directories for Mac and Linux when started as user or
    # sudo user
        USERNAME = os.getenv('SUDO_USER') or os.getenv('USER') 
        home_dir = os.path.expanduser('~'+USERNAME)
        # create ".pyfda" directory?
        #return os.path.expanduser( '~' )
    else:
        USERNAME = os.getenv('USER')
        # home_dir = os.path.expanduser(os.getenv('USERPROFILE'))
        home_dir = env( 'USERPROFILE' )
        if not valid(home_dir):
            home_dir = env( 'HOME' )
            if not valid(home_dir) :
                home_dir = '%s%s' % (env('HOMEDRIVE'),env('HOMEPATH'))
                if not valid(home_dir) :
                    home_dir = env( 'SYSTEMDRIVE' )
                    if home_dir and (not home_dir.endswith('\\')) :
                        home_dir += '\\'
                    if not valid(home_dir) :
                        home_dir = 'C:\\'
    return home_dir

#------------------------------------------------------------------------------ 

TEMP_DIR = tempfile.gettempdir()

def get_log_dir():
    """Return the logging directory"""
    log_dir = '/var/log/'
    if not valid(log_dir):
        if valid (TEMP_DIR):
            log_dir = TEMP_DIR
        else:
            return None
    log_dir_pyfda = os.path.join(log_dir, 'pyfda')
    if valid(log_dir_pyfda) and os.access(log_dir_pyfda, os.W_OK): # R_OK for readable
        return log_dir_pyfda
    else:
        try:
            os.mkdir(log_dir_pyfda)
            return log_dir_pyfda
        except (IOError, OSError) as e:
            print("Error creating {0}:\n{1}".format(log_dir_pyfda, e))
        else:
            return log_dir

    return 

#------------------------------------------------------------------------------
def get_conf_dir():
    """Return the user's configuration directory"""
    return get_home_dir()


HOME_DIR = get_home_dir()

LOG_DIR  = get_log_dir()
CONF_DIR = get_conf_dir()

print("Operating System: {0} {1}".format(OS, OS_VER)) # logger.info?