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

import os
import sys
from subprocess import check_output, CalledProcessError, STDOUT
import shutil
import platform
import tempfile
import datetime

# ANSI color codes
CSEL = '\033[96;1m'  # highlight select key (CYAN bold and bright)
CEND = '\033[0m'     # end coloring


# ------------------------------------------------------------------------------
def valid(path):
    """ Check whether path exists and is valid"""
    if path and os.path.isdir(path):
        return True
    return False


# ------------------------------------------------------------------------------
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
    return os.environ.get(name, '')


# ------------------------------------------------------------------------------
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
            user_name = os.getlogin()  # alternative
        # home_dir = os.path.expanduser(os.getenv('USERPROFILE'))
        home_dir = env('USERPROFILE')
        if not valid(home_dir):
            home_dir = env('HOME')
            if not valid(home_dir):
                home_dir = '%s%s' % (env('HOMEDRIVE'), env('HOMEPATH'))
                if not valid(home_dir):
                    home_dir = env('SYSTEMDRIVE')
                    if home_dir and (not home_dir.endswith('\\')):
                        home_dir += '\\'
                    if not valid(home_dir):
                        home_dir = 'C:\\'
    return home_dir, user_name


# ------------------------------------------------------------------------------
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
        # check whether directory /..../.pyfda exists and is writeable
        if valid(log_dir_pyfda) and os.access(log_dir_pyfda, os.W_OK):  # R_OK = readable
            return log_dir_pyfda
        # check whether directory .../.pyfda can be created:
        elif valid(d) and os.access(d, os.W_OK):
            try:
                os.mkdir(log_dir_pyfda)
                print("Created logging directory {0}".format(log_dir_pyfda))
                return log_dir_pyfda
            except (IOError, OSError) as e:
                print("ERROR creating {0}:\n{1}\nUsing '{2}'".format(log_dir_pyfda, e, d))
                return d  # use base directory instead if it is writable
    print("ERROR: No suitable directory found for logging.")
    return None


# ------------------------------------------------------------------------------
def get_yosys_dir():
    """
    Try to find YOSYS path and version from environment variable or path:
    """
    yosys_exe = env("YOSYS")
    yosys_ver = "not found"

    if yosys_exe:  # something is stored in the environment variable
        # redirect `yosys -V` output to string
        command = [yosys_exe, "-V"]
    elif "yosys" in env("PATH"):
        command = ["yosys", "-V"]
        try:
            output = check_output(command, stderr=STDOUT).decode().split(' ', 2)
            if len(output) > 1:
                yosys_ver = output[1]

        except CalledProcessError as e:
            print(e.output.decode())

    # print("YOSYS: {0}, ver. {1}".format(yosys_exe, yosys_ver))
    return yosys_exe, yosys_ver


# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
def copy_conf_files(force_copy=False, logger=None):
    """
    If they don't exist, create `pyfda.conf` und `pyfda_log.conf` from template files.
    in the user directory where they can be edited by the user without admin rights.
    If they exist and `force_copy=True`, make a backup of the old files and then
    overwrite them.

    Parameters
    ----------
    force_copy : bool
       When True, make a backup and overwrite existing config files.

    logger : logger instance
        Write info and error messages to `logger` when it exists, otherwise use
        `print()`. When called during the initial phase, loggers have not been
        created yet and `print()` has to be used.

    Returns
    -------
    None.

    """
    if logger:
        log_info = logger.info
        log_err  = logger.error
    else:
        log_info = print
        log_err  = print
    # pyfda config file
    try:
        # Create Backup
        if os.path.isfile(USER_CONF_DIR_FILE) and force_copy:
            shutil.move(USER_CONF_DIR_FILE, USER_CONF_DIR_FILE + "_bak_" + TODAY)
            log_info('Created backup "{0}"\n\tof user config file.'
                     .format(USER_CONF_DIR_FILE + "_bak_" + TODAY))
        # Create config file
        if not os.path.isfile(USER_CONF_DIR_FILE) or force_copy:
            shutil.copyfile(TMPL_CONF_DIR_FILE, USER_CONF_DIR_FILE)
            log_info('Created user config file "{0}" from template.'
                     .format(USER_CONF_DIR_FILE))
    except (IOError, FileNotFoundError, FileExistsError) as e:
        log_err("File error: {0}".format(e))

    # Logging config file
    try:
        # Create Backup
        if os.path.isfile(USER_LOG_CONF_DIR_FILE) and force_copy:
            shutil.move(USER_LOG_CONF_DIR_FILE, USER_LOG_CONF_DIR_FILE + "_bak_" + TODAY)
            log_info('Created backup "{0}"\n\tof user logging config file'
                     .format(USER_LOG_CONF_DIR_FILE + "_bak_" + TODAY))
        # Create log config file
        if not os.path.isfile(USER_LOG_CONF_DIR_FILE) or force_copy:
            shutil.copyfile(TMPL_LOG_CONF_DIR_FILE, USER_LOG_CONF_DIR_FILE)
            log_info('Created user logging config file "{0}" from template.'
                     .format(USER_LOG_CONF_DIR_FILE))
    except (IOError, FileNotFoundError, FileExistsError) as e:
        log_err("File error: {0}".format(e))


# -----------------------------------------------------------------------------
def update_conf_files(logger):
    """
    Copy templates to user config and logging config files, making backups
    of the old versions.
    """
    if OS.lower() == "windows":
        os.system('color')  # activate colored terminal under windows

    logger.error("Please either\n"
                 "\t- {R_str}eplace the existing user and log config files \n"
                 "\t     by copies of the templates (backups will be created).\n"
                 "\t\t{tmpl_conf} and \n\t\t{tmpl_log}\n"
                 "\t- {Q_str}uit and edit or delete the user config files yourself.\n\t"
                 "     When deleted, new config files will be created at the next start."
                 "\n\n"
                 "\tEnter 'q' to quit or 'r' to replace existing user config file:"
                 .format(tmpl_conf=TMPL_CONF_DIR_FILE,
                         tmpl_log=TMPL_LOG_CONF_DIR_FILE,
                         R_str=CSEL+"[R]"+CEND,
                         Q_str=CSEL+"[Q]"+CEND))
    val = input(
        "Enter 'q' to quit or 'r' to replace the existing user config file:").lower()
    if val == 'r':
        # - create backups of old user and logging config files
        # - copy templates to user directory.
        copy_conf_files(force_copy=True, logger=logger)
    elif val == 'q':
        sys.exit()
    else:
        sys.exit("Unknown option '{0}', quitting.".format(val))


# ==============================================================================
# is the software running in a bundled PyInstaller environment?
PYINSTALLER = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

OS     = platform.system()
OS_VER = platform.release()

CONF_FILE = 'pyfda.conf'            #: name for general configuration file
LOG_CONF_FILE = 'pyfda_log.conf'    #: name for logging configuration file

THIS_DIR = os.path.dirname(os.path.abspath(__file__))  # dir of this file
INSTALL_DIR = os.path.normpath(os.path.join(THIS_DIR, '..'))

TEMP_DIR = tempfile.gettempdir()  #: Temp directory for constructing logging dir
USER_DIRS = []  #: Placeholder for user widgets directory list, set by treebuilder

HOME_DIR, USER_NAME = get_home_dir()  #: Home dir and user name

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
# full path to YOSYS exe (if found) and version
YOSYS_EXE, YOSYS_VER = get_yosys_dir()

# store command line options as a list in ARGV, stripping '-' or '--'
ARGV = []
for a in sys.argv:
    ARGV.append(a.strip('-'))

# print information about pyfda paths and quit
if 'i' in ARGV:
    print("\n----- pyfda environment variables ------------")
    print("INSTALL_DIR:            {0}".format(INSTALL_DIR))
    print("USER_CONF_DIR_FILE:     {0}".format(USER_CONF_DIR_FILE))
    print("USER_LOG_CONF_DIR_FILE: {0}".format(USER_LOG_CONF_DIR_FILE))
    print("LOG_DIR_FILE:           {0}".format(LOG_DIR_FILE))
    sys.exit()

# print help infos and quit
if 'h' in ARGV:
    print("Start pyfdax with the following options:\n")
    print("\tpyfdax -h : Show this help message")
    print("\tpyfdax -i : Print information on user directories")
    print("\tpyfdax -r : Replace the config files")
    sys.exit()

# force replacement of config files when 'r' is specified
copy_conf_files(force_copy=('r' in ARGV))

# ------------------------------------------------------------------------------
""" Place holder for storing the name of the last file"""
last_file_name = ""
""" Place holder for storing the directory location of the last file"""
last_file_dir = HOME_DIR
""" Place holder for file type selected (e.g. "csv") in last file dialog"""
last_file_type = ''
""" Global handle to pop-up window for CSV options """
csv_options_handle = None
