# -*- coding: utf-8 -*-
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see LICENSE in root directory for details)

"""

"""
from __future__ import print_function
import os
import shutil
import platform
import tempfile
import time

OS     = platform.system()
OS_VER = platform.release()

log_conf_file = 'pyfda_log.conf'

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # dir of this file (dirs_finder.py)

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

HOME_DIR = get_home_dir()        
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
            return log_dir

LOG_DIR  = get_log_dir()

#------------------------------------------------------------------------------
def get_conf_dir():
    """Return the user's configuration directory"""
    return get_home_dir()
    conf_dir = os.path.join(HOME_DIR, 'pyfda')

    if valid(conf_dir) and os.access(conf_dir, os.W_OK):
        return conf_dir
    else:
        try:
            os.mkdir(conf_dir)
            print("Creating config directory \n{0}".format(conf_dir))
            return conf_dir
        except (IOError, OSError) as e:
            print("Error creating {0}:\n{1}".format(conf_dir, e))
            return home_dir

CONF_DIR = get_conf_dir()
#------------------------------------------------------------------------------

USER_LOG_CONF_FILE = os.path.join(CONF_DIR, log_conf_file)

if not os.path.isfile(USER_LOG_CONF_FILE):
    try:
        shutil.copyfile(os.path.join(BASE_DIR, log_conf_file), USER_LOG_CONF_FILE)
    except IOError as e:
        print(e)
        
    

print("Operating System: {0} {1}".format(OS, OS_VER)) # logger.info?