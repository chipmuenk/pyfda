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
import datetime

OS     = platform.system()
OS_VER = platform.release()

INSTALL_DIR = os.path.dirname(os.path.abspath(__file__)) # dir of this file
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
    # set home directory from user name for Mac and Linux when started as user or
    # sudo user
        USERNAME = os.getenv('SUDO_USER') or os.getenv('USER') 
        home_dir = os.path.expanduser('~'+USERNAME)
    else:
        # same for windows
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

     # list of base directories for constructing the logging directory
    log_dirs = ['/var/log/', TEMP_DIR]
    for d in log_dirs:
        log_dir_pyfda = os.path.join(d, '.pyfda')
        # check whether directory /..../.pyfda exists and is writable
        if valid(log_dir_pyfda) and os.access(log_dir_pyfda, os.W_OK): # R_OK for readable
            return log_dir_pyfda
        # check whether directory .../.pyfda can be created:
        elif valid(d) and os.access(d, os.W_OK):
            try:
                os.mkdir(log_dir_pyfda)
                print("Created logging directory {0}".format(log_dir_pyfda))
                return log_dir_pyfda
            except (IOError, OSError) as e:
                print("ERROR creating {0}:\n{1}\nUsing '{2}'".format(log_dir_pyfda, e, d))
                return d # use base directory instead if it is writable
    print("ERROR: No suitable directory found for logging.")
    return None

LOG_DIR  = get_log_dir()
if LOG_DIR:
    LOG_FILE = 'pyfda_{0}.log'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    # the name of the file can be changed in pyfdax.py
    LOG_DIR_FILE = os.path.join(LOG_DIR, LOG_FILE) 
else:
    LOG_FILE = None
    LOG_DIR_FILE = None
#------------------------------------------------------------------------------
def get_conf_dir():
    """Return the user's configuration directory"""
    conf_dir = os.path.join(HOME_DIR, '.pyfda')

    if valid(conf_dir) and os.access(conf_dir, os.W_OK):
        return conf_dir
    else:
        try:
            os.mkdir(conf_dir)
            print("Creating config directory \n'{0}'".format(conf_dir))
            return conf_dir
        except (IOError, OSError) as e:
            print("Error creating {0}:\n{1}".format(conf_dir, e))
            return HOME_DIR

CONF_DIR = get_conf_dir()
LOG_CONF_FILE = 'pyfda_log.conf'
#------------------------------------------------------------------------------

USER_LOG_CONF_FILE = os.path.join(CONF_DIR, LOG_CONF_FILE)

if not os.path.isfile(USER_LOG_CONF_FILE):
    # copy default logging configuration file to user directory if it doesn't exist
    # This file can be easily edited by the user without admin access rights
    try:
        shutil.copyfile(os.path.join(INSTALL_DIR, LOG_CONF_FILE), USER_LOG_CONF_FILE)
    except IOError as e:
        print(e)
#------------------------------------------------------------------------------
# This is the place holder for storing where the last file was saved
save_dir = HOME_DIR

print("Operating System: {0} {1}".format(OS, OS_VER)) # logger.info?
