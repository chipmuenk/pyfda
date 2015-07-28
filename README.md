pyFDA
======
## Python Filter Design Analysis Tool

[![Join the chat at https://gitter.im/chipmuenk/pyFDA](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/chipmuenk/pyFDA?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

The goal of this project is to create a GUI based tool in Python / Qt to analyse, design and synthesize discrete time filters. 

**Screenshot from the current version:**
![Screenshot](images/pyFDA_screenshot_3.PNG)

### Prerequisites
The project builds only on standard python libraries, libraries from the scipy stack (numpy, scipy, matplotlib) and the pyQt4 widget library. When the modules xlwt and / or XlsxWriter are installed, coefficients can be exported as *.xls(x) files.

### Getting started
Just download the zip file and extract it to a directory of your choice. The application is started with the file pyfda from the main directory.

### Why yet another filter design tool?
* **Education:** There is a very limited choice of user-friendly, license-free tools available to teach the influence of different filter design methods and specifications on time and frequency behaviour. It should be possible to run the tool without severe limitations also with the limited resolution of a beamer.
* **Show-off:** Demonstrate that Python is a potent tool for digital signal processing applications as well. The interfaces for textual filter design routines are a nightmare: linear vs. logarithmic specs, frequencies normalized w.r.t. to sampling or Nyquist frequency, -3 dB vs. -6 dB vs. band-edge frequencies ... (This is due to the different backgrounds and the history of filter design algorithms and not Python-specific.)
* **Fixpoint filter design for uCs:** Recursive filters have become a niche for experts. Convenient design and simulation support (round-off noise, stability under different quantization options and topologies) could attract more designers to these filters that are easier on hardware resources and much more suitable e.g. for uCs.
* **Fixpoint filter design for FPGAs**: Especially on low-budget FPGAs, multipliers are expensive. However, there are no good tools for designing and analyzing filters requiring a limited number of multipliers (or none at all) like CIC-, LDI- or Sigma-Delta based designs.
* **HDL filter implementation:** Implementing a fixpoint filter in VHDL / Verilog without errors requires some experience, verifying the correct performance in a digital design environment with very limited frequency domain simulation options is even harder. The Python module [myHDL](http://myhdl.org) can automate both design and verification.

### The following features are currently implemented:

* **Filter design**
    * **Design methods** from scipy.signal: Equiripple, Firwin, Butterworth, Elliptic, Chebychev 1 and Chebychev 2 
    * **Remember all specifications** when changing filter design methods
    * **Fine-tune** manually the filter order and corner frequencies calculated by minimum order algorithms
    * **Compare filter designs** for a given set of specifications and different design methods
    * **Filter coefficients and poles / zeroes** can be displayed, edited and quantized
* **Clearly structured GUI**
 * only widgets needed for the currently selected design method are visible
 * enhanced matplotlib NavigationToolbar (nicer icons, additional functions)
* **Common interface for all filter design methods:**
 * specify frequencies as absolute values or normalized to sampling or Nyquist frequency
 * specify ripple and attenuations in dB, as voltage or as power ratios
 * enter expressions like exp(-pi/4 * 1j) with the help of the library [simpleeval](https://pypi.python.org/pypi/simpleeval) (included in source files)
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
 * Filter design files can be added and edited *without* changing or even restarting the program
* **Saving and loading**
 * Save and load filter designs in pickled and in numpy's NPZ-format
 * Export coefficients and poles/zeros as comma-separated values (CSV), in numpy's NPZ-format, in Excel (R) or in Matlab (R) workspace format
* **Display help files** (own / Python docstrings) as rich text
* **Runs under Python 2.7 and Python 3.4** 

**More screenshots from the current version:**
<table>
    <tr>
        <td><img src = "images/pyFDA_screenshot_3d_2.PNG" alt="Screenshot" width=300px></td>
        <td><img src = "images/pyFDA_screenshot_hn.PNG" alt="Screenshot" width=300px></td>        
   </tr>
    <tr>
        <td><img src = "images/pyFDA_screenshot_3d_3.PNG" alt="Screenshot" width=300px></td>
        <td><img src = "images/pyFDA_screenshot_PZ.PNG" alt="Screenshot" width=300px></td>
    </tr>
</table>

### Release 0.1 (target: end of <s>May</s> July 2015)

The following features are still missing for the first release. 
* Documentation

### Release 0.2 (target: end of 2015) - Help is very welcome!
* **scipy 0.16 SOS features**
* **myHDL support**
    * Export of VHDL / Verilog netlists for basic filter topologies
    * Fixpoint simulation
* **Filter coefficients and poles / zeros**<br />
Implement model-view controller architecture for the following features:
  * Display coefficients / poles and zeros with fewer digits while keeping full precision internally
  * Group multiple poles / zeros
  * Load coefficients / poles and zeros in various formats 
* **Filter Manager**
  * Store multiple designs in one filter dict
  * Compare multiple designs in plots
* **Documentation using Sphinx**

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

### Further ideas are
* Wave-Digital Filters
* test filters in real-time with a audio stream
* ...

