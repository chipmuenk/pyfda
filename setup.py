# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages
from pyfdax import __version__

# @todo: WIP see https://packaging.python.org/en/latest/index.html

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'pyfda',
    # see PEP440 for versioning information
    version = __version__,
    description = ('pyFDA is a tool for designing and analysing discrete time '
                 'filters written in python with a graphical user interface.'),
    long_description = read('README.txt'),
    keywords = ["digital", "discrete time", "filter design", "IIR", "FIR", "GUI"],
    url = 'https://github.com/chipmuenk/pyFDA',
    author = 'Christian Muenker',
    author_email = '',
    license = 'Apache',
    packages = find_packages(exclude=('contrib', 'docs', 'test')),
    package_data = {'pyfda': ['images/icons/*']},
    data_files = [('pyfda/filter_design', ['pyfda/filter_design/filter_list.txt'])],
    entry_points = {
        'console_scripts': [
            'pyfdax = pyfdax:main',
        ],
        'gui_scripts': [
            'pyfda_gui = pyfdax:main',
        ]
    }
)

"""
On non-Windows platforms (using "setup.py install", "setup.py develop", 
or by using EasyInstall), a "pyfdax" script will be installed that imports 
"main" from pyfdax.py. main() is called with no arguments, and the
return value is passed to sys.exit(), so an errorlevel or message to print 
to stderr could be provided (not implemented yet).

On Windows, a set of pyfdax.exe and pyfda_gui.exe launchers are created, 
alongside a set of pyfdax.py and pyfda_gui.pyw files. The .exe wrappers find 
and execute the right version of Python to run the .py or .pyw file.
"""
