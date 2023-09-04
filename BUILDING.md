# Building and packaging pyfda

## pip and PyPI
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


## pyInstaller
pyInstaller can build executables with the help of a `*.spec`  file that is provided 
in the directory `ressource`. Hopefully, this works out of the box across operating
systems with

    > pyinstaller pyfdax.spec

## Flatpak
It is only possible to build flatpaks under Linux. In addition to `flatpak` itself, you need to install `flatpak-builder` to build your own flatpaks:

    > sudo apt install flatpak flatpak-builder

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