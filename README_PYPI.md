pyfda
======
## Python Filter Design Analysis Tool

pyfda is a GUI based tool in Python / Qt for analysing and designing discrete time filters. Fixpoint implementations (for some filter types) can be simulated. 

For more info see the [`Github Repo`](https://github.com/chipmuenk/pyfda) and the documentation at [readthedocs.org](https://pyfda.readthedocs.io/en/latest/).

![Screenshot](https://github.com/chipmuenk/pyfda/raw/develop/img/pyFDA_screenshot_3.png)

## Prerequisites

* Python versions: **3.6 ... 3.10**
* All operating systems - there should be no OS specific requirements.
* Libraries:
  * **(Py)Qt5**
  * **numpy**
  * **scipy**
  * **matplotlib**: **2.1** or higher

### Optional libraries:
* **docutils** for rich text in documentation
* **xlwt** and / or **XlsxWriter** for exporting filter coefficients as *.xls(x) files

## Installing pyfda
Self-executing archives are available for Windows and OS X at https://github.com/chipmuenk/pyfda/releases which do not require a Python installation.

Otherwise, installation is straight forward: There is only one version of pyfda for all supported operating systems, no compilation is required:

### pip
You can install from PyPI using

    > pip install pyfda

or upgrade using

    > pip install pyfda -U
	
or install locally using

    > pip install -e <YOUR_PATH_TO_PYFDA>
	
where `<YOUR_PATH_TO_PYFDA>` specifies the path of `setup.py` without including `setup.py`. 
In this case, you need to have a local copy of the pyfda project, preferrably obtained using git and `pip install` only creates the start script.

### setup.py   
You could also download the zip file from Github and extract it to a directory of your choice. Install it either to your `<python>/Lib/site-packages` subdirectory using

    > python setup.py install

or just create a link to where you have copied the python source files (for testing / development) using

    > python setup.py develop

## Starting pyfda
In any case, the start script `pyfdax` has been created in `<python>/Scripts` which should be in your path. So, simply start pyfda using

    > pyfdax

For development and debugging, you can also run pyfda using

    In [1]: %run -m pyfda.pyfdax # IPython or
    > python -m pyfda.pyfdax    # plain python interpreter
    
All individual files from pyfda can be run using e.g.

    In [2]: %run -m pyfda.input_widgets.input_pz    # IPython or 
    > python -m pyfda.input_widgets.input_pz       # plain python interpreter
   
## Customization

The location of the following two configuration files (copied to user space) can be checked via the tab `Files -> About`:

- Logging verbosity can be controlled via the file `pyfda_log.conf` 
- Widgets and filters can be enabled / disabled via the file `pyfda.conf`. You can also define one or more user directories containing your own widgets and / or filters.

Layout and some default paths can be customized using the file `pyfda/pyfda_rc.py`, right now you have to edit that file at its original location.

