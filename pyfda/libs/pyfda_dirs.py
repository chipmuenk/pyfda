# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Handle directories in an OS-independent way, create logging directory etc.
Upon import, all the variables are set.
This is imported first by pyfdax.
"""

import os, sys
import shutil
import platform
import tempfile
import datetime

# ANSI color codes
CSEL = '\033[96;1m'# highlight select key (CYAN bold and bright)
CEND = '\033[0m'   # end coloring

def valid(path):
    """ Check whether path exists and is valid"""
    if path and os.path.isdir(path):
        return True
    return False

def env(name):
    """
    Get value for environment variable ``name`` from the OS.

    Parameters
    ----------
    name : str
       environment variable

    Returns
    -------
    str
      value of environment variable
    """
    return os.environ.get( name, '' )

def get_home_dir():
    """
    Return the user's home directory and name
    """
    if OS != "Windows":
    # set home directory from user name for Mac and Linux when started as user or
    # sudo user
        user_name = os.getenv('SUDO_USER') or os.getenv('USER')
        if user_name is None:
            user_name = ""
        home_dir = os.path.expanduser('~'+user_name)
    else:
        # same for windows
        user_name = os.getenv('USER')
        if not user_name:
            user_name = os.getlogin() # alternative
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
    return home_dir, user_name

#------------------------------------------------------------------------------
def get_log_dir():
    """
    Try different OS-dependent locations for creating log files and return
    the first suitable directory name. Only called once at startup.

    see https://stackoverflow.com/questions/847850/cross-platform-way-of-getting-temp-directory-in-python
    """

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
            print("Error creating config directory {0}:\n{1}".format(conf_dir, e))
            return HOME_DIR

#------------------------------------------------------------------------------
def create_conf_files():
    if not os.path.isfile(USER_CONF_DIR_FILE):
        # Copy default configuration file to user directory if it doesn't exist
        # This file can be easily edited by the user without admin access rights
        try:
            shutil.copyfile(TMPL_CONF_DIR_FILE, USER_CONF_DIR_FILE)
            print('Config file "{0}" doesn\'t exist yet, creating it.'.format(USER_CONF_DIR_FILE))
        except IOError as e:
            print(e)

    if not os.path.isfile(USER_LOG_CONF_DIR_FILE):
        # Copy default logging configuration file to user directory if it doesn't exist
        # This file can be easily edited by the user without admin access rights
        try:
            shutil.copyfile(TMPL_LOG_CONF_DIR_FILE, USER_LOG_CONF_DIR_FILE)
            print("Logging config file {0} doesn't exist yet, creating it.".format(USER_LOG_CONF_DIR_FILE))
        except IOError as e:
            print(e)
#-----------------------------------------------------------------------------
def update_conf_files(logger):
    """
    Copy templates to user config and logging config files, making backups
    of the old versions.
    """
    if OS.lower() == "windows":
        os.system('color') # activate colored terminal under windows

    logger.error("Please either\n"
                 "\t- {R_str}eplace the existing user and log config files \n"
                 "\t     by copies of the templates (backups will be created).\n"
                 "\t\t{tmpl_conf} and \n\t\t{tmpl_log}\n"
                 "\t- {Q_str}uit and edit or delete the user config files yourself.\n\t"
                 "     When deleted, new config files will be created at the next start.\n\n"
                 "\tEnter 'q' to quit or 'r' to replace existing user config file:"
                 .format(tmpl_conf=TMPL_CONF_DIR_FILE,
                        tmpl_log=TMPL_LOG_CONF_DIR_FILE,
                        R_str=CSEL+"[R]"+CEND,
                        Q_str=CSEL+"[Q]"+CEND))
    val = input("Enter 'q' to quit or 'r' to replace the existing user config file:").lower()
    if val == 'r':
        # Create backups of old user and logging config files, copy templates to user directory.
        try:
            shutil.move(USER_CONF_DIR_FILE, USER_CONF_DIR_FILE + "_bak_" + TODAY)
            shutil.copyfile(TMPL_CONF_DIR_FILE, USER_CONF_DIR_FILE)
            logger.info('Created new user config file "{0}".'.format(USER_CONF_DIR_FILE))

            shutil.move(USER_LOG_CONF_DIR_FILE, USER_LOG_CONF_DIR_FILE + "_bak_" + TODAY)
            shutil.copyfile(TMPL_LOG_CONF_DIR_FILE, USER_LOG_CONF_DIR_FILE)
            logger.info('Created new user logging config file "{0}".'.format(USER_LOG_CONF_DIR_FILE))
        except IOError as e:
            logger.error("IOError: {0}".format(e))

    elif val == 'q':
        sys.exit()
    else:
        sys.exit("Unknown option '{0}', quitting.".format(val))

#==============================================================================
# is the software running in a bundled PyInstaller environment?
PYINSTALLER = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

OS     = platform.system()
OS_VER = platform.release()

CONF_FILE = 'pyfda.conf'            #: name for general configuration file
LOG_CONF_FILE = 'pyfda_log.conf'    #: name for logging configuration file

THIS_DIR = os.path.dirname(os.path.abspath(__file__)) # dir of this file
INSTALL_DIR = os.path.normpath(os.path.join(THIS_DIR, '..'))

TEMP_DIR = tempfile.gettempdir() #: Temp directory for constructing logging dir
USER_DIRS = [] #: Placeholder for user widgets directory list, set by treebuilder

HOME_DIR, USER_NAME = get_home_dir() #: Home dir and user name

TODAY = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

LOG_DIR  = get_log_dir()
if LOG_DIR:
    LOG_FILE = 'pyfda_{0}.log'.format(TODAY)
    #: Name of the log file, can be changed in ``pyfdax.py``
    LOG_DIR_FILE = os.path.join(LOG_DIR, LOG_FILE)
else:
    LOG_FILE = None
    LOG_DIR_FILE = None


CONF_DIR = get_conf_dir()
# full path name of user configuration file:
USER_CONF_DIR_FILE     = os.path.join(CONF_DIR, CONF_FILE)
# full path name of logging configuration file:
USER_LOG_CONF_DIR_FILE = os.path.join(CONF_DIR, LOG_CONF_FILE)
# full path name of configuration template:
TMPL_CONF_DIR_FILE = os.path.join(THIS_DIR, 'pyfda_template.conf')
# full path name of logging configuration template:
TMPL_LOG_CONF_DIR_FILE = os.path.join(THIS_DIR, 'pyfda_log_template.conf')

create_conf_files()

#------------------------------------------------------------------------------
""" Place holder for storing the directory location where the last file was saved"""
save_dir = HOME_DIR
""" Place holder for default file filter in file dialog"""
save_filt = ''
""" Global handle to pop-up window for CSV options """
csv_options_handle = None
