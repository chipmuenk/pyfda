pyFDA
======
## Python Filter Design Analysis Tool

The goal of this project is to create a GUI based tool in Python / Qt to analyse, design and synthesize discrete time filters. 

![Screenshot](images/pyFDA_screenshot_3.PNG)

### Why yet another filter design tool?
* **Education:** There is a very limited choice of user-friendly, license-free tools available to teach the influence of different filter design methods and specifications on time and frequency behaviour. It should be possible to run the tool without severe limitations also with the limited resolution of a beamer.
* **Show-off:** Demonstrate that Python is a potent tool for digital signal processing applications as well. The interfaces for textual filter design routines are a nightmare: linear vs. logarithmic specs, frequencies normalized w.r.t. to sampling or Nyquist frequency, -3 dB vs. -6 dB vs. band-edge frequencies ... (This is due to the different backgrounds and the history of filter design algorithms and not Python-specific.)
* **Fixpoint filter design for uCs:** Recursive filters have become a niche for experts. Convenient design and simulation support (round-off noise, stability under different quantization options and topologies) could attract more designers to these filters that are easier on hardware resources and much more suitable e.g. for uCs.
* **Fixpoint filter design for FPGAs**: Especially on low-budget FPGAs, multipliers are rare. However, there are no good tools for designing and analyzing filters requiring a limited number of multipliers (or none at all) like CIC-, LDI- or Sigma-Delta based designs.
* **HDL filter implementation:** Implementing a fixpoint filter in VHDL / Verilog without errors requires some experience, verifying the correct performance in a digital design environment with very limited frequency domain simulation options is even harder. The Python module [myHDL](http://myhdl.org) can automate both design and verification.


### The following features are currently implemented:

* **Design methods** (from scipy.signal): Equiripple, Firwin, Butterworth, Elliptic, Chebychev 1 and Chebychev 2 
* **Switch between design methods**, keeping all other settings:
 * Filter order and corner frequencies calculated by minimum order algorithms can be fine-tuned by hand
 * Directly compare how a set of specifications influences the resulting filter for different design methods
* **Clearly structured GUI**
 * only widgets needed for the currently selected design method are visible
 * enhanced matplotlib NavigationToolbar (nicer icons, additional functions 'grid' and 'zoom full extent')
* **Common interface for all filter design methods:**
 * specify frequencies as absolute values or normalized to sampling or Nyquist frequency
 * specify ripple and attenuations in dB, as voltage or as power ratios
 * enter expressions like exp(-pi/4 * 1j) with the help of the library [simpleeval](https://pypi.python.org/pypi/simpleeval) (included in source files)
* **Graphical Analyses**
 * Magnitude response (lin / power / log) with optional display of the specification bands and inset plot
 * Phase response (wrapped / unwrapped)
 * Group delay
 * Pole / Zero plot
 * Impulse response
 * 3D-Plots (|H(f)|, mesh, surface, contour) with optional pole / zero display
* **Modular architecture**, facilitating the implementation of new filter design and analysis methods
 * Filter design files can be added and edited *without* changing or even restarting the program
 * Special widgets needed by design methods (e.g. for choosing the window in Firwin) are included in the filter design file, not in the main program
* **Filter coefficients and poles / zeros**
 * Display, edit and quantize 
 * Save as Comma-separated values (CSV) or Matlab (R) workspace format
* **Display help files** (own / Python docstrings) as rich text
* **Runs under Python 2.7 and Python 3.4** 

### Release 0.1 (target: end of May 2015)

The following features are still missing for the first release. Help is very welcome!
* Save and load filter designs (pickle? shelve?)
* **Filter coefficients and poles / zeros**
  * Display coefficients / poles and zeros with fewer digits while keeping full precision
  * Group multiple poles / zeros
  * Load coefficients / poles and zeros, 
* Smooth some rough edges:
  * not all text fields are supported by simpleeval yet
  * better debugging options
  * reflect in the GUI whether a filter design was successful, is out-of-date (specs have been changed) or whether an error occurred

### Following releases
* Better help files and messages
* Add a tracking cursor
* Graphical modification of poles / zeros
* Export of filter properties as PDF / HTML files
* Show error messages and warnings in the GUI
* Design, analysis and export of filters as second-order sections
* Multiplier-free filter designs (CIC, GCIC, LDI, SigmaDelta-Filters, ...)
* Export of Python filter objects
* Analysis of different fixpoint filter topologies (direct form, cascaded form, parallel form, ...) concerning overflow and quantization noise
* Fixpoint filter sythesis and export using the myHDL module (<http://myhdl.org>)

### Further ideas are
* Wave-Digital Filters
* ...

