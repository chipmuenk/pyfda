pyFDA
======
## Python Filter Design Analysis Tool

pyFDA is a GUI based tool in Python / Qt for analysing and designing discrete time filters. When the migen module ist installed, fixpoint implementations (for some filter types) can be simulated and exported as synthesizable Verilog netlists. 

For more info see the [`Github Repo`](https://github.com/chipmuenk/pyFDA).

![Screenshot](https://github.com/chipmuenk/pyFDA/raw/develop/img/pyFDA_screenshot_3.png)

## Prerequisites

* Python versions: **3.3 ... 3.7**
* All operating systems - there should be no OS specific requirements.
* Libraries:
  * **(Py)Qt5**
  * **numpy**
  * **scipy**
  * **matplotlib**: **2.0** or higher

### Optional libraries:
* **migen** for fixpoint simulation and Verilog export. When missing, the "Fixpoint" tab is hidden.
* **docutils** for rich text in documentation
* **xlwt** and / or **XlsxWriter** for exporting filter coefficients as *.xls(x) files

## Installing and Starting pyFDA
There is only one version of pyfda for all supported operating systems, Python and Qt versions. As there are no binaries included, you can simply install from the source.

### conda
If you use the Anaconda distribution, you can install / update pyfda from my Anaconda channel [`Chipmuenk`](https://anaconda.org/Chipmuenk/pyfda) using

    > conda install -c Chipmuenk pyfda

resp.

    > conda update  -c Chipmuenk pyfda

### pip
Otherwise, you can install from PyPI using

    > pip install pyfda

or upgrade using

    > pip install pyfda -U
	
or install locally using

    > pip install -e <YOUR_PATH_TO_PYFDA>
	
where the specified path points to `pyfda.setup.py` but without including `setup.py`. In this case, you need to have a local copy of the pyfda project, preferrably using git.

### setup.py   
You could also download the zip file from Github and extract it to a directory of your choice. Install it either to your `<python>/Lib/site-packages` subdirectory using

    > python setup.py install

or just create a link to where you have copied the python source files (for testing / development) using

    > python setup.py develop

### Starting pyFDA
In any case, the start script `pyfdax` has been created in `<python>/Scripts` which should be in your path. So, simply start pyfda using

    > pyfdax

For development and debugging, you can also run pyFDA using

    In [1]: %run -m pyfda.pyfdax # IPython or
    > python -m pyfda.pyfdax    # plain python interpreter
    
All individual files from pyFDA can be run using e.g.

    In [2]: %run -m pyfda.input_widgets.input_pz    # IPython or 
    > python -m pyfda.input_widgets.input_pz       # plain python interpreter
   
### Customization

The location of the following two configuration files (copied to user space) can be checked via the tab `Files -> About`:

- Logging verbosity can be controlled via the file `pyfda_log.conf` 
- Widgets and filters can be enabled / disabled via the file `pyfda.conf`. You can also define one or more user directories containing your own widgets and / or filters.

Layout and some default paths can be customized using the file `pyfda/pyfda_rc.py`, right now you have to edit that file at its original location.

