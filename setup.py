# -*- coding: utf-8 -*-
from setuptools import setup, find_packages, find_namespace_packages
from os import path

here = path.abspath(path.dirname(__file__))
# Get the long description from the README file
# see e.g. https://github.com/alttch/finac/blob/master/setup.py
with open(path.join(here, 'README_PYPI.md'), encoding='utf-8') as f:
    long_description = f.read()

# version_nr contains ... well ... the version in the form  __version__ = '0.1b10'
version_nr = {}
with open(path.join(here, 'pyfda/version.py'), encoding='utf-8') as f_v:
    exec(f_v.read(), version_nr)

# --- read requirements.txt, remove comments and unneeded modules
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f_r:
    requirements_list = f_r.read().strip().split("\n")

for p in requirements_list[:]:
    if p.startswith('#'):
        requirements_list.remove(p)
if 'nose' in requirements_list:
    requirements_list.remove('nose')
try:
    from PyQt5.QtCore import QT_VERSION_STR
    requirements_list.remove('pyqt5')
    print("PyQt5 {0} is already installed, skipping it.".format(QT_VERSION_STR))
    # try to prevent installing library twice under conda where lib is listed
    # as "pyqt" for backward compatibility with PyQt4
except ImportError:
    pass

print("Installing packages\n{0}\n".format(requirements_list))

setup(
    name='pyfda',
    version=version_nr['__version__'],
    description=("Design and analyse discrete time DSP filters with a user-friendly GUI "
                 "tool. Fixpoint filters in time and frequency domain, too."),
    long_description_content_type='text/markdown',
    # long_description_content_type='text/x-rst',
    long_description=long_description,
    keywords=["digital", "discrete time", "filter design", "IIR", "FIR", "GUI"],
    url='https://github.com/chipmuenk/pyFDA',
    author='Christian Muenker',
    author_email='mail07@chipmuenk.de',
    license='MIT',
    platforms=['any'],
    install_requires=requirements_list,

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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    # automatically find top-level package and sub-packages input_widgets,
    # plot_widgets etc.:
    packages=find_namespace_packages(),  # exclude=('contrib', 'docs', 'tests', 'bak',
                                        #      'recipe')),
    # Install data files (specified in MANIFEST.in)
    include_package_data=True,
    # add additional data files (= non *.py) for package / subpackages relative
    # to package directory, include 'qrc_resources.py' instead of 'images/icons/*',
    # ('qrc_resources.py','version.py' are automatically installed).
    ## package_data={'pyfda': ['pyfda_log.conf', 'pyfda.conf']},
    # https://stackoverflow.com/questions/2026876/packaging-python-applications-with-configuration-files
    # include files that get installed OUTSIDE the package
    ## data_files = [('', ['README.rst']), ('', ['LICENSE'])],
    # Required modules
    #    install_requires = [
    #        'numpy',
    #        'scipy',
    #        'matplotlib',
    #        'pyqt5',
    #        'docutils',
    #        ],

    # link the executable pyfdax to running the python function main() in the
    # pyfdax module, with and without an attached terminal:
    entry_points={
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
main() is called with no arguments, and the return value is passed to sys.exit(),
so an errorlevel or message to print
to stderr could be provided (not implemented yet).

pyfdax_no_term does essentially the same but it starts no terminal.

On Windows, a set of pyfdax.exe and pyfdax_no_term.exe launchers are created,
alongside a set of pyfdax.py and pyfdax_no_term.pyw files. The .exe wrappers find
and execute the right version of Python to run the .py or .pyw file.
"""
# http://locallyoptimal.com/blog/2014/03/14/executable-python-scripts-via-entry-points/
