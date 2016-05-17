# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

# @todo: WIP see https://packaging.python.org/en/latest/index.html


here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# VERSION contains ... well ... the version in the form  __version__ = '0.1b10'
version_nr = {}
with open("pyfda/version.py") as fp:
    exec(fp.read(), version_nr)

setup(
    name = 'pyfda',
    # see PEP440 for versioning information
    version = version_nr['__version__'],   
    description = ('pyFDA is a python tool with a user-friendly GUI for designing and analysing discrete time '
                 'filters.'),
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
    # directory, include 'qrc_resources.py' instead of 'images/icons/*',
    # 'qrc_resources.py','version.py' are automatically installed
    package_data={'pyfda': ['pyfda_log.conf', 'pyfda_log_debug.conf',
                            'filter_design/filter_list.txt'],
                  },

    # include files that get installed OUTSIDE the package
    data_files = [
#        ('', ['README.rst']),
#        ('', ['LICENSE'])
        ],
    install_requires = [
        'numpy >= 1.9', 'scipy >= 0.15', 'matplotlib >= 1.1', 'docutils'
        ],
    # link the executable pyfdax to running the python function main() in the
    # pyfdax module, with and without an attached terminal:
    entry_points = {
        'console_scripts': [
            'pyfdax = pyfda.pyfdax:main',
        ],
        'gui_scripts': [
            'pyfdax_no_term = pyfda.pyfdax:main',
        ]
    }
)


"""
On non-Windows platforms (using "setup.py install", "setup.py develop",
or by using EasyInstall), a "pyfdax" script will be installed that opens up
a terminal and imports "main" from pyfdax.py. 
main() is called with no arguments, and the return value is passed to sys.exit(), so an errorlevel or message to print
to stderr could be provided (not implemented yet).

pyfdax_no_term does essentially the same but it starts no terminal.

On Windows, a set of pyfdax.exe and pyfdax_no_term.exe launchers are created,
alongside a set of pyfdax.py and pyfdax_no_term.pyw files. The .exe wrappers find
and execute the right version of Python to run the .py or .pyw file.
"""
# http://locallyoptimal.com/blog/2014/03/14/executable-python-scripts-via-entry-points/

