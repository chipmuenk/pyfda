## Changelog

### [v0.4.0](https://github.com/chipmuenk/pyfda/tree/v0.4.0) (2020-10-xx)

#### Bug Fixes
- Make compatible to matplotlib 3.3 by cleaning up hierarchy for NavigationToolbar in mpl_widgets.py
 ([Issue \#179](https://github.com/chipmuenk/pyfda/issues/179), [Issue \#44](https://github.com/chipmuenk/pyfda/issues/144)) 
  and get rid of mpl 3.3 related deprecation warnings. Disable zoom rectangle and pan when zoom is locked. 

- [PR \#182:](https://github.com/chipmuenk/pyfda/pull/182) Get rid of deprecation warnings "Creating an ndarray from ragged nested sequences"  [(Issue \#180)](https://github.com/chipmuenk/pyfda/issues/180)
  by declaring explicitly np.array(some_ragged_list , dtype=object) or by handling the elements of ragged list indidually
  ([chipmuenk](https://github.com/chipmuenk))
  
- [PR \#186](https://github.com/chipmuenk/pyfda/pull/186), fixing [Issue \#184](https://github.com/chipmuenk/pyfda/issues/184) "Filter type "Delay" can crash pyfda", 
  syntax errors in the UI description have been fixed. As the filter class does not produce a proper 
  delay, it is commented out in the configuratiion file for the time being 
  (see [Issue \#184](https://github.com/chipmuenk/pyfda/issues/185))
  
- When the gain *k* has been changed in the P/Z input widget, highlight the save button.

- Fix several small bugs and deprecation warnings in the Coeff input widget

- Enforce correct sign for various input fields

#### New features

- [PR \#183:](https://github.com/chipmuenk/pyfda/pull/187) Include license information for 
  distribution of pyFDA as source code and in bundled form, redesign the whole 
  "About" window, add CHANGELOG.md (this file) and move attributions to AUTHORS.md

- Add cursor / annotations in plots ([Issue \#112](https://github.com/chipmuenk/pyfda/issues/112)) This is only available when 
  [mplcursors](https://mplcursors.readthedocs.io/) module is installed and for matplotlib >= 3.1.
  
- [PR \#183:](https://github.com/chipmuenk/pyfda/pull/183) Replace simpleeval library by numexpr. 
  This enables the creation of formula based stimuli, closing [Issue \#162](https://github.com/chipmuenk/pyfda/issues/162) and 
  part of [Issue \#44](https://github.com/chipmuenk/pyfda/issues/144).

- Add chirp stimulus in Impulse Response tab.

- The top level module name for generated Verilog netlists (Fixpoint tab) is now derived from the
  specified file name. The module name is converted to lower cased and sanitized so that is only 
  contains alpha-numeric characters and '_'.  [(Issue \#176)](https://github.com/chipmuenk/pyfda/issues/176), 
  "allow different module names for verilog export").
  
- User and user log config files now can be replaced automatically if the config file version number is wrong 
   ([Issue \#44](https://github.com/chipmuenk/pyfda/issues/144))

### Release 0.3 (2020-03)

### Release 0.2 (2019-05)

#### New features

- **Rework of signal-slot connections**
    * Clearer structure: only one RX / TX signal connection per widget
    * More flexibility: transport dicts or lists via the signals
    * Much improved modularity - new functionality can be easily added
    
- **Reorganization of configuration files**
    * Specify module names instead of class names for widgets, class names are defined in the modules 
    * More flexibility in defining user directories
    * List suitable fixpoint implementations for each filter design as well as the other way around
    
- **HDL synthesis (beta status, expect bugs)**
    * Use migen to generate synthesizable Verilog netlists for basic filter topologies and do fixpoint simulation 
    * When migen is missing on your system, pyFDA will start without the fixpoint tab but otherwise fully functional
- **Didactic improvements**
    * Improved display of transient response and FFT of transient response
    * Display magnitude frequency response in the PZ plot to ease understanding the relationship
- **Documentation using Sphinx / ReadTheDocs**

    Could be more and better ... but hey, it's a start!
  
### Release 0.1 (2018-02-04)

Initial release 
