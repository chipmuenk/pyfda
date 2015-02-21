pyFDA
======
# Python Filter Design Analysis Tool

![Screenshot](https://github.com/chipmuenk/pyFDA/raw/master/images/pyFDA_screenshot.png)

The goal of this project is to create a GUI based tool to analyse and design discrete time filters implemented in Python and Qt. The following goals of this FOSS project have been reached or will be in the near future:

* Easy to use, clearly structured GUI
* Accessing Scipy filter design methods with a common interface (frequency and amplitude specifications)
* Easy switching between manual and minimum filter order without losing all the settings
* Modular structure, facilitating the implementation of new filter design and analysis methods
* Filter design files can simply be added to the filter_design subdirectory without changes to the program and without restarting
* Comfortable saving and loading of filter designs
* Export of filter coefficients and poles / zeros as CSV and in Matlab (R) workspace format

Plans for the not-so near future include:
* Quantization of filter coefficients
* Multiplier-free filter designs (CIC, GCIC, SigmaDelta-Filters, ...)
* Export of Python filter objects
* Analysis of different fixpoint filter topologies (direct form, cascaded form, parallel form, ...) concerning overflow and quantization noise
* Fixpoint filter sythesis and export using the myHDL module (<myhdl.org>)

And maybe the future will bring
* Wave-Digital Filters
* ...

