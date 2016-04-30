# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path
#from pyfdax import __version__

# @todo: WIP see https://packaging.python.org/en/latest/index.html


here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

version_nr = {}
with open("version.py") as fp:
    exec(fp.read(), version_nr)

setup(
    name = 'pyfda',
    # see PEP440 for versioning information
    version = version_nr['__version__'],   
    description = ('pyFDA is a tool for designing and analysing discrete time '
                 'filters written in python with a graphical user interface.'),
    long_description = long_description,
    keywords = ["digital", "discrete time", "filter design", "IIR", "FIR", "GUI"],
    url = 'https://github.com/chipmuenk/pyFDA',
    author = 'Christian Muenker',
    author_email = 'mail07@chipmuenk.de',
    license = 'MIT',
    platforms = ['any'],

     # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Topic :: Scientific/Engineering',
        'Topic :: Education',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    # automatically find top-level package and sub-packages input_widgets,
    # plot_widgets etc.:
    packages = find_packages(exclude=('contrib', 'docs', 'test')),

    # add additional data files for package / subpackages relative to package
    # directory
    package_data={'pyfda': ['images/icons/*', 'pyfda_log.conf',
                            'filter_design/filter_list.txt'],
                  },

    # include general data files
    data_files = [
        ('', ['README.rst']),
        ('', ['LICENSE'])
        ],
    # link the executable pyfdax to running the python function main() in the
    # pyfdax module, with and without an attached console:
    entry_points = {
        'console_scripts': [
            'pyfdax = pyfda.pyfdax:main',
        ],
        'gui_scripts': [
            'pyfdax_gui = pyfda.pyfdax:main',
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
# http://locallyoptimal.com/blog/2014/03/14/executable-python-scripts-via-entry-points/

