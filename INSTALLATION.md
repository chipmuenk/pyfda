# Installing pyfda

There are several options to install pyfda either from source or from a binary / 
bundle. The ">" signs below only indicate the command lines, don't enter them.

## Installation
### pip and PyPI
If there is a working Python interpreter on your computer, installing pyfda with `pip` (or `pip3`) from the Python Package Inventory [PyPI](https://pypi.org) is most straightforward, required libraries are installed automatically if missing. 

You should create a separate environment for pyfda to avoid e.g. unwanted updating of installed python modules:

    > python -m venv <PATH_TO_ENVIRONMENT>

This creates the subdirectory if it doesn't exist. Activation of the environment depends on your OS, see https://docs.python.org/3/library/venv.html for details.

Installation pyfda with

    > pip install pyfda

and start it with

    > pyfdax
    
A **specific version** instead of the latest stable version can be selected with e.g.

    > pip install pyfda==0.8.0b1

**Upgrade** pyfda using

    > pip install pyfda -U
	
**Install from local files** (development mode) using

    > pip install -e <YOUR_PATH_TO_PYFDA>
	
where the specified path points to `pyfda/setup.py` (without including `setup.py`).
In this case, you need to have a local copy of the pyfda project, preferrably 
synchronized to the GitHub repo using git (see below).

Install the latest development version from **GitHub** using

    > pip install https://github.com/chipmuenk/pyfda/archive/develop.tar.gz
    
**Uninstall** pyfda with

    > pip uninstall pyfda

### Running from source
You can simply download and unpack the zip file from GitHub and start the program 
from the `pyfda` top project directory with

    > python -m pyfda.pyfdax     # Plain Python interpreter 

or
    
    In [1]: %run -m pyfda.pyfdax # IPython
    
For testing purposes, most individual files from pyFDA can be run using e.g.

    > python -m pyfda.input_widgets.input_pz       # Plain python interpreter

or
    
    In [2]: %run -m pyfda.input_widgets.input_pz   # IPython 
    
However, installing pyfda makes life easier as it creates a run script `pyfdax`
in your path.

### conda
If you're working with Anaconda's packet manager conda, there is a recipe for pyfda on `conda-forge` since July 2023:

    > conda install --channel=conda-forge pyfda

It is recommended to install pyfda in a seperate environment instead of the `base` environment, e.g. called `pyfda-env`:

    > conda install --name pyfda-env --channel=conda-forge pyfda

In that case, you need to activate the environment each time you want to use pyfda with:

    > conda activate pyfda-env

In any case, start pyfda with

    > pyfdax

It is *not* recommended to install pyfda with pip under Anaconda. One potential 
problem is that conda installs `PyQt5` under the name `pyqt` and pip under the name `pyqt5`:

- `pip install` **`pyqt5`** installs system wide

- `conda install` **`pyqt`** installs sytem wide or in an environment.

`pip install pyfda` checks whether PyQt5 is installed already (but conda doesn't) 
so you **need** to do `conda install pyqt` before running `pip install pyfda` .

If you end up having *both* installed, you're in 
[trouble](https://github.com/ContinuumIO/anaconda-issues/issues/1554): If

    > conda list qt

    pyqt                      5.6.0                    py36_2
    PyQt5                     5.8.2                     <pip>
    
gives you a similar result as above, you probably have a corrupted system. 

### setuptools   
You can also download the project as a zip file from GitHub and extract it to 
a directory of your choice. Either install a copy to your `<python>/Lib/site-packages` 
subdirectory using

    > python setup.py install

or just create a link to where you have copied the python source files (for testing
 / development) using

    > python setup.py develop
    
Attention: There is no automatic uninstall option when installing pyfda this way!
    
### pyInstaller
pyInstaller bundles all required Python and data files together with a bootloader
into a self-expanding executable. When executing this file, the content is expanded
into a temporary directory and deleted when terminating pyfda. Thanks to Github Actions, you can download bundles for Windows 10 and for OS X.

There is no need for an uninstall, simply delete the downloaded executable if you don't need it anymore or replace it by a newer version.

### Flatpak
"[Flatpak](https://flatpak.org/) is a framework for distributing desktop applications across various Linux distributions." 
Flatpak provides containers which also contain runtime libraries to be independent of individual Linux distributions. 

In contrast to snap, Flatpak is a community based project encouraging multiple servers
for distributing the Flatpaks. The most popular is <https://flathub.org/>, a situation
similar to git and GitHub.

Many Linux distributions include Flatpak, otherwise you need to install flatpak (see
<https://flatpak.org/setup/>), e.g. for Ubuntu

    > sudo apt install flatpak
    
Once Flatpak is installed, you should add the Flathub repo with

    > flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    
You can install pyfda system wide with

    > sudo flatpak install --from FLATPAKREF
    
where FLATPAKREF is the path to `pyfda.flatpakref` which can be either a local file
or a URL.

Installation only for current user:

    > flatpak install --user --from FLATPAKREF 
