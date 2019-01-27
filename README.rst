Python Filter Design Analysis Tool
==================================

pyFDA is a GUI tool in Python / Qt for analysing and designing
discrete time filters.

.. figure:: img/pyFDA_screenshot_3.png
   :alt: Screenshot

   Screenshot

Prerequisites
-------------

-  Python versions: **2.7** or **3.3 ... 3.6**
-  All operating systems - there should be no OS specific requirements.
-  Libraries:
-  **(Py)Qt4** or **(Py)Qt5**. When both libraries are installed, PyQt5
   is used.
-  **numpy**, **scipy**, **matplotlib**

Optional libraries: \* **docutils** for rich text in documentation \*
**xlwt** and / or **XlsxWriter** for exporting filter coefficients as
\*.xls(x) files

Features
--------

-  **Filter design**

   -  **Design methods**: Equiripple, Firwin, Moving Average, Bessel,
      Butterworth, Elliptic, Chebychev 1 and 2 (from scipy.signal and
      custom methods)
   -  **Second-Order Sections** are used in the filter design when
      available for more robust filter design and analysis
   -  **Remember all specifications** when changing between filter design
      methods
   -  **Fine-tune** manually the filter order and corner frequencies
      calculated by minimum order algorithms
   -  **Filter coefficients and poles / zeroes** can be displayed,
      edited and quantized in various formats

-  **Clearly structured User Interface**

   -  only widgets needed for the currently selected design method are
      visible
   -  enter specifications as absolute or normalized frequencies resp. in
      dB or voltage / power ratios using expressions like exp(-pi/4 \* 1j)
      (integrated library `simpleeval <https://pypi.python.org/pypi/simpleeval>`)
   -  enhanced matplotlib NavigationToolbar (nicer icons, additional
      functions)
   -  display help files (own / Python docstrings) as rich text
   -  tooltips for all control and entry widgets

-  **Graphical Analyses**

   -  Magnitude response (lin / power / log) with optional display of
      specification bands, phase and an inset plot
   -  Phase response (wrapped / unwrapped)
   -  Group delay
   -  Pole / Zero plot
   -  Impulse response and step response (lin / log)
   -  3D-Plots (\|H(f)\|, mesh, surface, contour) with optional pole /
      zero display

-  **Modular architecture**, facilitating the implementation of new
   filter design and analysis methods

   -  Filter design files not only contain the actual algorithm but also
      dictionaries specifying which parameters and standard widgets have
      to be displayed in the GUI.
   -  Special widgets needed by design methods (e.g. for choosing the
      window type in Firwin) are included in the filter design file, not
      in the main program

-  **Saving and loading**

   -  Save and load filter designs in pickled and in numpy's NPZ-format
   -  Export and import coefficients and poles/zeros as comma-separated
      values (CSV), in numpy's NPY- and NPZ-formats, in Excel (R) or in
      Matlab (R) workspace format
   -  Export coefficients in FPGA vendor specific formats like Xilinx
      (R) COE-format

Installing pyFDA
----------------

There is only one version of pyfda for all supported operating systems,
Python and Qt versions. As there are no binaries included, you can
simply install from the source.

conda
~~~~~

If you use the Anaconda distribution, you can install / update pyfda
from my Anaconda channel
`Chipmuenk <https://anaconda.org/Chipmuenk/pyfda>`_ using

::

    conda install -c Chipmuenk pyfda

resp.

::

    conda update  -c Chipmuenk pyfda

pip
~~~

Otherwise, you can install from PyPI using

::

    pip install pyfda

or upgrade using

::

    pip install pyfda -U
	
or install locally using

::

	pip install -e <YOUR_PATH_TO_PYFDA>
	
where the specified path is the one your `setup.py` sits in. In this case, you need to have a local copy of the pyfda project, preferrably using git. Now you can edit your local copy, test it and e.g. push it to your own git fork.

Starting pyFDA
--------------

In any case, the start script ``pyfdax`` has been created in
``<python>/Scripts`` which should be in your path. So, simply start
pyfda using

::

    >> pyfdax

For development and debugging, you can also run pyFDA using

::

    In [1]: %run -m pyfda.pyfdax # IPython or
    >> python -m pyfda.pyfdax    # plain python interpreter

All individual files from pyFDA can be run using e.g.

::

    In [2]: %run -m pyfda.input_widgets.input_pz    # IPython or
    >> python -m pyfda.input_widgets.input_pz       # plain python interpreter

Customization
~~~~~~~~~~~~~

- Layout and some parameters can be customized with the file
  ``pyfda/pyfda_rc.py`` (within the install directory right now). 
- Select which widgets and filters will be included, define a user
  directory for integration of your own widgets in ``<USER_HOME>/.pyfda/pyfda.conf``
- Control logging behaviour with ``<USER_HOME>/.pyfda/pyfda_log.conf``
