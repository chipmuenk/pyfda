# Changelog

## [v0.4.0](https://github.com/chipmuenk/pyfda/tree/v0.3.2) (2020-09-xx)

**Bug Fixes**
- Make compatible to matplotlib 3.3 by cleaning up hierarchy for NavigationToolbar in mpl_widgets.py
 [(Issue \#179)](https://github.com/chipmuenk/pyfda/issues/179) and get rid of mpl 3.3 related deprecation warnings. Disable zoom rectangle and pan when zoom is locked. 

- [PR \#182:](https://github.com/chipmuenk/pull/182) Get rid of deprecation warnings "Creating an ndarray from ragged nested sequences"  [(Issue \#180)](https://github.com/chipmuenk/pyfda/issues/180)
  by declaring explicitly np.array(some_ragged_list , dtype=object) or by handling the elements of ragged list indidually
  ([chipmuenk](https://github.com/chipmuenk))
  
- [Issue \#184](https://github.com/chipmuenk/pyfda/issues/184) "Filter type "Delay" can crash pyfda", 
  syntax errors in the UI description have been fixed. As the filter class does not produce a proper 
  delay, it is commented out in the configuratiion file for the time being 
  (see [Issue \#184](https://github.com/chipmuenk/pyfda/issues/185))

  
- When the gain k has been changed in the P/Z input widget, highlight the save button.

- Fix several small bugs and deprecation warnings in the Coeff input widget

- Enforce correct sign for various input fields

**Enhancements**

- Add cursor / annotations in plots [(Issue \#112)](https://github.com/chipmuenk/issues/112)

  (only available when [mplcursors](https://mplcursors.readthedocs.io/) module is installed and for matplotlib >= 3.1.)
  
- [PR \#183:](https://github.com/chipmuenk/pull/183) Replace simpleeval library by numexpr. 
  This enables the creation of formula based stimuli, closing [Issue \#162](https://github.com/chipmuenk/issues/162)

- Add chirp stimulus

- The top level module name for generated Verilog netlists (Fixpoint tab) is now derived from the
  specified file name. The module name is converted to lower cased and sanitized so that is only 
  contains alpha-numeric characters and '_'.  ([(Issue \#176)](https://github.com/chipmuenk/pyfda/issues/176), 
  "allow different module names for verilog export").

- Add CHANGELOG.md (this file)

- Move attributions to AUTHORS.md

