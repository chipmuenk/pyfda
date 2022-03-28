# Installing and packaging pyFDA

There are several options to install pyfda either from source or from a binary / 
bundle. The ">" signs below only indicate the command lines, don't enter them.

## Installation
### pip and PyPI
Installing pyfda from the Python Package Inventory <https://pypi.org> is most 
straightforward (if you have Python installed on your computer), required libraries 
are installed automatically if missing. Just run (you might need `pip3` instead
of `pip`)

    > pip install pyfda
    
A **specific version** instead of the latest stable version can be selected with e.g.

    > pip install pyfda==0.2b3

**Upgrade** pyfda using

    > pip install pyfda -U
	
**Install locally** (development mode) using

    > pip install -e <YOUR_PATH_TO_PYFDA>
	
where the specified path points to `pyfda/setup.py` (without including `setup.py`).
In this case, you need to have a local copy of the pyfda project, preferrably 
synchronized to the GitHub repo using git.

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
I'm not providing conda builds for the Anaconda distribution anymore (too messy) 
but so far I've had no major problems installing pyfda with pip under Anaconda.

You need to be careful with `PyQt5` as conda installs it under the name
`pyqt` and pip under the name `pyqt5`:

- `pip install` **`pyqt5`** installs system wide

- `conda install` **`pyqt`** installs sytem wide or in an environment.

`pip install pyfda` checks whether PyQt5 is installed already (but conda doesn't) 
so you **need** to do `conda install pyqt` before pip.


If you end up having *both* installed, you're in 
[trouble](https://github.com/ContinuumIO/anaconda-issues/issues/1554): If you do

    > conda list qt

    pyqt                      5.6.0                    py36_2
    PyQt5                     5.8.2                     <pip>
    
and get a similar result as above, you probably have a corrupted system. 

Don't use the `base` environment  for installing pyfda (you shouldn't do this 
for *any* software) but rather switch to another environment (`conda activate my_fancy_environment`) 
or create a new one (`conda create --name my_new_environment`). 

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
into a local directory and deleted when terminating pyfda. The executable is
operating system specific, I can only provide exectuables for Windows 10 and for 
the version of my currently installed Linux distro. This may or may not work on 
your Linux distro, please try. 

If you can provide a MacOS executable, please help, for building instructions see below. 

Under Linux, flatpak installation should be preferred (currently working on that).

### Flatpak
"[Flatpak](https://flatpak.org/) is a framework for distributing desktop applications across various Linux distributions." 
Flatpak provides containers which also contain runtime libraries to be independent of individual Linux distributions. 

In contrast to snap, Flatpak is a community based project encouraging multiple servers
for distributing the Flatpaks. The most popular is <https://flathub.org/>, a situation
similar to git and GitHub.

Some Linux distributions (like Mint) include Flatpak, otherwise you need to install flatpak (see
<https://flatpak.org/setup/>), e.g. for Ubuntu

    > sudo apt install flatpak
    
Once Flatpak is installed, you should add the Flathub repo with

    > flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    
You can install pyfda system wide with

    > sudo flatpak install --from FLATPAKREF
    
where FLATPAKREF is the path to `pyfda.flatpakref` which can be either a local file
or a URL.

Local installation:

    > flatpak install --user --from FLATPAKREF 

## Building / packaging

### pip and PyPI
Pip packages (source only) are created using the `setuptools` flow:

    > python setup.py clean
    > python setup.py bdist_wheel sdist
    
which creates a `dist` directory containing a python wheel `pyfda-<VERSION>.whl` and the source archive `pyfda-<VERSION>.tar.gz`. 
Creating a source archive (and hence the `sdist` option) is optional, wheels are the standard format for distributing python modules.

Non-python files to be included in the package have to be declared in 
`MANIFEST.in`, see 
<https://packaging.python.org/guides/using-manifest-in/>.

Beware of an [old bug](https://github.com/pypa/setuptools/issues/436) where updates
to the `MANIFEST.in` file are ignored.

As a workaround, delete the directory `pyfda.egg-info` containing `SOURCES.txt` after each change to the file structure or `MANIFEST.in`. It seems
that an existing file `SOURCES.txt` is not updated.

Check the integrity of this package and upload it to <https://pypi.org/project/pyfda/> using twine by

	> twine check dist/*
    > twine upload dist/pyfda-<VERSION>-py3-none-any.whl


### pyInstaller
pyInstaller can build executables with the help of a `*.spec`  file that is provided 
in the directory `ressource`. Hopefully, this works out of the box across operating
systems with

    > pyinstaller pyfdax.spec

### Flatpak
It is only possible to build flatpaks under Linux. In addition to Flatpak itself, you need to install `flatpak-builder` to build your own flatpaks:

    > sudo apt install flatpak-builder

The first steps are described in ["Building your first Flatpak"](https://docs.flatpak.org/en/latest/first-build.html) and
<https://docs.flatpak.org/en/latest/python.html> w.r.t. python.
    
Next, you need a manifest file `org.flatpak.pyfda.json` or `...yaml` with information 
and build instructions for the app. 

This file also contains the dependencies which 
can be collected for pip / PyPI projects with the python helper file
`flatpak-pip-generator` from <https://github.com/flatpak/flatpak-builder-tools/tree/master/pip> 
by running

    > python flatpak-pip-generator pyfda 
	
generating the file `python3-pyfda.json`
    
You can also get the dependencies from pip's `requirements.txt`:

    > python flatpak-pip-generator --requirements-file=requirements.txt
    
The created file `python3-pyfda.json` or `python3-requirements.json` has to 
be included in the manifest (JSON or YaML) file as

    "modules": [
      "python3-requirements.json",
      {
        "name": "other-modules"
      }
    ]
    
resp. for a YaML manifest

    modules:
      - python3-requirements.json
      # (other modules go here)

The manifest also specifies which of the 
[three available runtimes](https://docs.flatpak.org/en/latest/available-runtimes.html)
(Freedesktop, Gnome or KDE) will be used. As pyfda builds upon (py)Qt, the KDE runtime
is selected.

Runtime and SDK need to be installed first to your local computer using 
(omit the version number for a command line selection)

    > flatpak install flathub org.kde.Platform//5.15
    > flatpak install flathub org.kde.Sdk//5.15
    
which adds another 1.5 GB to your hard disk ...

This information is compiled in `org.flatpak.pyfda.json`:

    {
      "app-id": "org.flatpak.pyfda",
      "runtime": "org.kde.Platform",
      "runtime-version": "5.15",
      "sdk": "org.kde.Sdk",
      "command": "pyfdax",
      "finish-args": [
        "--socket=wayland",
    	"--socket=x11",
        "--device=dri",
        "--filesystem=xdg-run/dconf", "--filesystem=~/.config/dconf:ro",
        "--talk-name=ca.desrt.dconf", "--env=DCONF_USER_CONFIG_DIR=.config/dconf",
        "--own-name=org.flatpak.pyfda",
        "--filesystem=home"
    	],
        "rename-icon":"pyfda_icon", /*Image will renamed to match the app-id konvention*/
        "rename-appdata-file": "pyfda.appdata.xml",
    	"rename-desktop-file":"pyfda.desktop",
        "modules": [
          "python3-requests.json",
          {
            "name": "other-modules"
          }
        ]
    }
    
resp. in `org.flatpak.pyfda.yaml`:

    app-id: org.flatpak.pyfda
    runtime: org.kde.Platform
    runtime-version: '5.15'
    sdk: org.kde.Sdk
    command: pyfdax
    finish-args:
      - --share=ipc
      - --socket=x11
      - --socket=wayland
      - --filesystem=host
      - --device=dri
      - --own-name=org.flatpak.pyfda
      - --filesystem=home # which part of the file system can be accessed by the app
      # I don't know what the following arguments do
      - --filesystem=xdg-run/dconf
      - --filesystem=~/.config/dconf:ro
      - --talk-name=ca.desrt.dconf
      - --env=DCONF_USER_CONFIG_DIR=.config/dconf
    modules:
      - python3-requests.json
      
    rename-icon:pyfda_icon # Image will renamed to match the app-id konvention
    rename-appdata-file: pyfda.appdata.xml
    rename-desktop-file: pyfda.desktop # launcher for the desktop


Finally, the build process is started with

    > flatpak-builder build-dir org.flatpak.pyfda.json
    
resp.

    > flatpak-builder build-dir org.flatpak.pyfda.yaml
    
Currently, this process fails, probably due to 
<https://github.com/flatpak/flatpak-builder-tools/issues/47>
<https://stackoverflow.com/questions/64189236/using-flatpak-pip-generator-resulting-in-error-could-not-find-a-version-when>