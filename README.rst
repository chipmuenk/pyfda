pyFDA
*****

Python Filter Design Analysis Tool
==================================

pyFDA is a GUI based tool in Python / Qt for analysing and designing discrete time filters. The capability for generating Verilog and VHDL code for the designed and quantized filters will be added in the next release.

.. image:: https://github.com/chipmuenk/pyFDA/raw/master/images/pyFDA_screenshot_3.PNG
    :width: 300px

Prerequisites
-------------
The software runs under Python 2.7 and 3.3 ... 3.6. The following additional libraries are required:

* numpy
* scipy
* matplotlib
* pyQt4 or pyQt5

* Optional libraries:
    * docutils for rendering info text as rich text
    * xlwt and / or XlsxWriter for exporting filter coefficients as \*.xls(x) files


Installing and starting pyFDA
-----------------------------

There is only one version of pyfda for all supported operating systems, Python and Qt versions. As there are no binaries included, you can simply install from the source.

**conda**

If you use the Anaconda distribution, you can install / update pyfda from my Anaconda channel `Chipmuenk` (https://anaconda.org/Chipmuenk/pyfda) using

    ``>> conda install -c Chipmuenk pyfda``
resp.

    ``>> conda update  -c Chipmuenk pyfda``

**pip**

Otherwise, you can install from PyPI using

    ``>> pip install pyfda``

or upgrade using

    ``>> pip install pyfda -U``

**from setup.py**

Download the zip file and extract it to a directory of your choice. Install it either to your ``<python>/Lib/site-packages`` subdirectory using

    ``>> python setup.py install``

or run it where you have installed the python source files using (for testing / development)

    ``>> python setup.py develop``

In both cases, start scripts ``pyfdax`` and `pyfdax_no_term` are created (with / without terminal).

For development, you can also run pyFDA using::

    In [1]: %run -m pyfda.pyfdax # IPython or
    >> python -m pyfda.pyfdax    # plain python interpreter

    
or run individual files from pyFDA using e.g.::

    In [2]: %run -m pyfda.input_widgets.input_pz  # IPython or
    >> python -m pyfda.input_widgets.input_pz     # plain python interpreter
   
Customization
-------------

The layout and some default paths can be customized using the file ``pyfda/pyfda_rc.py``.

Features
--------

* **Filter design**
    * **Design methods**: Equiripple, Firwin, Moving Average, Bessel, Butterworth, Elliptic, Chebychev 1 and 2 (from scipy.signal and custom methods)
    * **Second-Order Sections** are used in the filter design when available for more robust filter design and analysis
    * **Remember all specifications** when changing filter design methods
    * **Fine-tune** manually the filter order and corner frequencies calculated by minimum order algorithms
    * **Compare filter designs** for a given set of specifications and different design methods
    * **Filter coefficients and poles / zeroes** can be displayed, edited and quantized in various formats
* **Clearly structured User Interface**
    * only widgets needed for the currently selected design method are visible
    * enhanced matplotlib NavigationToolbar (nicer icons, additional functions)
    * display help files (own / Python docstrings) as rich text
    * tooltips for all control and entry widgets
* **Common interface for all filter design methods:**
    * specify frequencies as absolute values or normalized to sampling or Nyquist frequency
    * specify ripple and attenuations in dB, as voltage or as power ratios
    * enter expressions like exp(-pi/4 * 1j) with the help of the library simpleeval (https://pypi.python.org/pypi/simpleeval) (included in source files)
* **Graphical Analyses**
    * Magnitude response (lin / power / log) with optional display of specification bands, phase and an inset plot
    * Phase response (wrapped / unwrapped)
    * Group delay
    * Pole / Zero plot
    * Impulse response and step response (lin / log)
    * 3D-Plots (|H(f)|, mesh, surface, contour) with optional pole / zero display
* **Modular architecture**, facilitating the implementation of new filter design and analysis methods
    * Filter design files not only contain the actual algorithm but also dictionaries specifying which parameters and standard widgets have to be displayed in the GUI. 
    * Special widgets needed by design methods (e.g. for choosing the window type in Firwin) are included in the filter design file, not in the main program
* **Saving and loading**
    * Save and load filter designs in pickled and in numpy's NPZ-format
    * Export and import coefficients and poles/zeros as comma-separated values (CSV), in numpy's NPY- and NPZ-formats, in Excel (R) or in Matlab (R) workspace format
    * Export coefficients in FPGA vendor specific formats like Xilinx (R) COE-format

