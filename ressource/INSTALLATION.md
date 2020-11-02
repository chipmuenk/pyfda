# Distributing and installing pyFDA

There are several options to install pyfda either from source or from a binary / 
bundle. The ">" signs below only indicates a command line, don't enter them.

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
obtained using git (see below).

Install the latest development version from **GitHub** using

    > pip install https://github.com/chipmuenk/pyfda/archive/develop.tar.gz
    
**Uninstall** pyfda with

    > pip uninstall pyfda

### conda
I'm not providing conda builds anymore (too messy) but so far I've had no major
problems installing pyfda with pip under Anaconda 

### setup.py   
You can also download the project as a zip file from GitHub and extract it to 
a directory of your choice. Either install a copy to your `<python>/Lib/site-packages` 
subdirectory using

    > python setup.py install

or just create a link to where you have copied the python source files (for testing
 / development) using

    > python setup.py develop
    
Attention: There is no automatic uninstall option in this case!
    
### pyInstaller
pyInstaller bundles all required Python and data files together with a bootloader
into a self-expanding executable. When executing this file, the content is expanded
into a local directory and deleted when terminating pyfda. The executable is
operating system specific, I can only provide exectuables for Windows 10 and for 
the version of my currently installed Linux distro. This may or may not work on 
your Linux distro, please try. 

If you can provide a MacOS executable, please help, for building instructions see below. 

Under Linux, flatpak installation should be preferred (currently working on that).

### flatpak
[flatpak](https://www.flatpak.org/) was developed to build and distribute apps for
all Linux desktop distributions. flatpak provides containers which also contain 
runtime libraries to be independent of individual Linux distributions. 

In contrast to snap, flatpak is a community based project encouraging multiple servers
for distributing the flatpaks. The most popular is <https://flathub.org/>, a situation
similar to git and GitHub.

Some Linux distributions (like Mint) include flatpak, otherwise you need to install flatpak (see
<https://flatpak.org/setup/>), e.g. for Ubuntu

    > sudo apt install flatpak
    
Once flatpak is installed, you should add the Flathub repo with

    > flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    
You can install pyfda system wide with

    > sudo flatpak install --from FLATPAKREF
    
where FLATPAKREF is the path to `pyfda.flatpakref` which can be either a local file
or a URL.

Local installation:

    > flatpak install --user --from FLATPAKREF 

## Building

### pip and PyPI

### pyInstaller

pyInstaller can build executables with the help of a `*.spec`  file that is provided 
in the directory `ressource`. Hopefully, this works out of the box across operating
systems with

    > pyinstaller pyfdax.spec
    
Pyinstaller 4.0 does not support matplotlib 3.3 yet, the generated binaries fail 
with "RuntimeError: Could not find the matplotlib data files" when executed.

### flatpak
The basic build process is described in 
["Building your first Flatpak"](https://docs.flatpak.org/en/latest/first-build.html) and
<https://docs.flatpak.org/en/latest/python.html> w.r.t. python.

In addition to flatpak itself, you need to install `flatpak-builder` with

    > sudo apt install flatpak-builder
    
Next, you need a manifest file `org.flatpak.pyfda.json` or `...yaml` with information 
and build instructions for the app. This file also contains the dependencies which 
can be collected for pip / PyPI projects with the python helper file
`flatpak-pip-generator` from <https://github.com/flatpak/flatpak-builder-tools/tree/master/pip> 
by running

    > python flatpak-pip-generator pyfda 
    
You can also read the dependencies from pip's `requirements.txt`:

    > python flatpak-pip-generator --requirements-file=requirements.txt
    
The created file `python3-pyfda.json` resp. `python3-requirements.json` has to 
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
(Freedesktop, Gnome or KDE) shall be used. As pyfda uses a lot of Qt, the KDE runtime
is selected.

Runtime and SDK need to be installed first to your local computer using 
(omit the version number to get a selection)

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
      # I don't know what the following arguments do
      - --filesystem=xdg-run/dconf
      - --filesystem=~/.config/dconf:ro
      - --talk-name=ca.desrt.dconf
      - --env=DCONF_USER_CONFIG_DIR=.config/dconf
      - --own-name=org.flatpak.pyfda
      - --filesystem=home # where can files be stored
    
    modules:
      - python3-requests.json
      
    rename-icon:pyfda_icon # Image will renamed to match the app-id konvention
    rename-appdata-file: pyfda.appdata.xml
    rename-desktop-file: pyfda.desktop


Finally, the build process is started with

    > flatpak-builder build-dir org.flatpak.pyfda.json
    
resp.

    > flatpak-builder build-dir org.flatpak.pyfda.yaml