# Changelog

## [v0.9.4](https://github.com/chipmuenk/pyfda/tree/v0.9.4) (2024-xxx)

### Bugfixes

### Updates

- Change some UI default settings for better usability
- Add some tool tips
- Normalize data to given maximum value also before saving in y[n] file tab.

## [v0.9.3](https://github.com/chipmuenk/pyfda/tree/v0.9.3) (2024-11-04)

### Bugfixes

- Fix too narrow pull-down list in combo boxes under Linux and MacOS
- Fix crash when disabling plot in y[n] tab
- Make rectangular window the default window for spectral analysis
- Re-enable display of frequency index k in y[n] frequency tab
- Comment out ultraspherical window as it crashes pyfda
- Rename pyInstaller archive pyfda_linux to pyfda_ubuntu to make it clear that this file can
only be used under Ubuntu (or probably other Debian related distros)
- Fix several small issues in dark UI

## [v0.9.2](https://github.com/chipmuenk/pyfda/tree/v0.9.2) (2024-10-20)

### Bugfixes

- Fix "IndexError: list assignment index out of range"
    File "/home/cmuenker/Daten/design/python/git/pyfda/pyfda/filterbroker.py", line 486, in store_fil
        fil_undo[undo_ptr] = copy.deepcopy(fil[0])
    IndexError: list assignment index out of range
- Fix broken badges on README.md
- Fix broken build process for ReadTheDocs

## [v0.9.1](https://github.com/chipmuenk/pyfda/tree/v0.9.1) (2024-10-03)

### Bugfixes

- Fix Python 3.12 related syntax warnings about invalid escape sequences by using raw strings
- remove distutils.LooseVersion imports as this is no longer supported by Python 3.12

## [v0.9.0](https://github.com/chipmuenk/pyfda/tree/v0.9.0) (2024-09-30)

### Bugfixes

- The number of data points for the impulse response of FIR filters is no longer limited to 100 and the
  automatic calculation for the number of data points now is enabled by a push button instead of setting
  'N = 0' [issue \#246](https://github.com/chipmuenk/pyfda/issues/246)
- Fixed warnings about unknown entries 'value' and 'matplotlib'
- Fixed a lot of errors in docstrings and documentation causing errors and warnings
  during the Sphinx ReadTheDocs document generation
- When saving filters, use only keys from the reference filter (and warn about unsupported
  keys).
- Fixed more problems when loading / saving fixpoint filters
  [issue \#239](https://github.com/chipmuenk/pyfda/issues/239)
- Fixed problems when loading / saving windowed and equiripple filters.
- Fixed problems when loading csv audio files
- Lots of code clean-up

### New features

- Provide a simple example of an Amaranth fixpoint filter (needs to be enabled in pyfda.conf) with fixpoint
  simulation and Verilog export (still buggy)
- Provide an estimation for the length of the impulse response of IIR filters until -40 dB are
  reached (currently hardcoded)
- For complex-valued time signals, display single-sided spectra as magnitude
  [issue \#242](https://github.com/chipmuenk/pyfda/issues/242)
- Dark mode (needs to be set in `pyfda.conf` with `THEME = 'dark'`. When updating an existing installation,
  recreate the config file first with `pyfdax -r`
- New second-order sections export formats 'CMSIS DSP coefficients' and 'Scipy/Matlab SOS coefficients'
- Add more infos in FFT Window viewer


## [v0.9.0b1](https://github.com/chipmuenk/pyfda/tree/v0.9.0b1) (2024-04-02)

### Changed settings and behaviour

- Minimum initial number of data points in the y[n] tab now is 25
- Initial width of rect pulse now is T_1 = 10

### New features

- load / save filters to 9 different memory locations [issue \#220](https://github.com/chipmuenk/pyfda/issues/220)
- coefficients can be saved in CMSIS format directly via 'save coefficients', this
  is no longer hidden in the CSV options [issue \#213](https://github.com/chipmuenk/pyfda/issues/213)
- in 'float' mode, fixpoint widget is now invisible and fixpoint simulations are no longer run
- filters can be saved and loaded in JSON format
- show fixpoint ranges for input and output separately
- filter coefficients can also be complex as float2frmt() now handles complex numbers
- accept complex number of the kind +.234j (pos. sign, no leading zero)
- add separate quantizers for partial products x*b and y*a in iir_df1_pyfixp
- new fixpoint number format 'octal'
- numexpr >= 2.8.8 is now required as '1j' is parsed by numexpr again

### Bugfixes

- fixed bugs w.r.t. behaviour of locking absolute frequencies in filter design widget
- highlighting frequencies outside the first Nyquist zone 0 ... f_S resp. -f_S/2 ... f_S/2 didn't work
  reliably
- [issue \#243](https://github.com/chipmuenk/pyfda/issues/243) where deleting all cells results in an index error
- [issue \#239](https://github.com/chipmuenk/pyfda/issues/239): lots of bugs fixed w.r.t. fixpoint and especially integer fixpoint behaviour
- fix behaviour when no fixpoint filter exists for a filter class
- lots of bugs fixed for loading / saving filters
- fixed several bugs w.r.t. signalling, causing multiple executions of code and erroneous ui updates

## [v0.8.4](https://github.com/chipmuenk/pyfda/tree/v0.8.4) (2023-10-10)

### Bugfixes

- Require numexpr <= 2.8.4 to avoid limitations / bugs of newer versions (https://github.com/pydata/numexpr/issues/442) which prevents parsing of complex arguments ["numexpr: Value error: Expression 1.0j has forbidden control characters."]
- Fix deprecation of plt.stem(... 'use_line_collection' ...)  introduced in matplotlib 3.8.0.
- Fix several crashes when loading / saving coefficients or poles / zeros
- Fix loading complex coefficients
- Fix loading fixpoint resp. formatted coefficients and poles/zeros, using a new "format" button
- Fix wrong default orientation when exporting tables
- Fix importing csv-files in row format with headers
- Disable Flatpak generation, doesn't work any more

### New features

- Self-extracting Linux archives in pyInstaller format are generated and released per Github action
- Start adding amaranth to the tool flow

## [v0.8.3](https://github.com/chipmuenk/pyfda/tree/v0.8.3) (2023-09-14)

### Bugfixes

- Fix crashes when saving coefficients in fixpoint format ( [issue \#230](https://github.com/chipmuenk/pyfda/issues/230) and [\#238](https://github.com/chipmuenk/pyfda/issues/238))
- Update images for README.md and readthedocs documentation
- Rename square to rect stimulus in y[n] stimuli
- Allow for zero or negative delays in y[n] stimuli
- Correct wrong CSV defaults for header and row/column mode while saving
- Fix improper alignment of matplotlib navigation bar
- Minor UI improvements

## [v0.8.2](https://github.com/chipmuenk/pyfda/tree/v0.8.2) (2023-09-08)

### Bugfixes

- Fine-tuning of Matplotlib font size for different screens, scalings and resolutions

## [v0.8.1](https://github.com/chipmuenk/pyfda/tree/v0.8.1) (2023-09-08)

### Bugfixes

- Correct scaling of 'UI detail' icon for high resolution screens
- Increase Matplotlib font size for high resolution screens

### Improvements

- Nicer icons for 'UI detail' and 'Grid'

## [v0.8.0](https://github.com/chipmuenk/pyfda/tree/v0.8.0) (2023-08-09)

### Bugfixes

- Several tabs: Various crashes related to file imports
- 'H(f'): Fix deprecation error w.r.t. matplotlib, causing a crash when using
  inset plot in the H(f) tab (#234)
- 'Specs': Fix wrong / erroneous behaviour of 'Lock frequencies' button
- 'Specs': Sampling frequency, unit and display mode are now exported and
  imported to /from filters.
- 'FFT': Replace deprecated Slepian window by DPSS
- Several tabs: Fixed some strange behaviours and crashes with complex data / plots
- Several tabs: Fix deprecation error w.r.t. to 'ragged arrays' in numpy which made
  filter import / export unusable. The format of the npz file had to be
  changed, so old filter designs can no longer be read with this version.

### New features

- Github action workflows for creating Flatpak installation files, as Github
  release and on Flathub (thanks to @Martin Marmsoler). This now works for
  tagged (pre)releases and 'latest' releases from the main branch.
- 'y[n]': Stimulus can be loaded from wav and csv files,
  additionally  response / quantized response can be saved in those formats.
- 'y[n]': Plotting can be disabled, as plotting of large data sets takes the
   most time by far compared to calculating the response.
- 'y[n]': Frequency input fields are highlighted in red when the value is
   outside the first Nyquist zone. The value is used anyway but will be
   aliased.
- 'y[n]': Improve overall UI
- 'y[n]': Show interpolated waveform x(t) for discrete time stimuli (mainly
   for didactic purposes)
- 'y[n]: Periodic sinc is now correctly called 'diric' and properly defined.

- 'H(f)': Allow plotting magnitude, real and imaginary part of H(F) at the same time
- 'H(f)': Add legend

- Make the display of polar coordinates in the P/Z input tab more compact

- 'Specs': Frequency input fields are highlighted in red when the value is
   outside the first Nyquist zone. The value is passed to filter design routines
   anyway where it usually raises an error.

- All tabs: Allow hiding the control options for maximum plotting area via a new
   button in the toolbar

- All tabs: Lots of little UI and tooltip improvements

## [v0.7.1](https://github.com/chipmuenk/pyfda/tree/v0.7.1) (2022-10-05)

### Bugfixes

- Fix crash in 'y[n]' tab when no file is loaded
- Remove some superfluous files in pip package

## [v0.7](https://github.com/chipmuenk/pyfda/tree/v0.7.0) (2022-10-04)

### Bugfixes

- Fix lot of bugs and redundancies in the fixpoint simulation routines
- When the filter is complex-valued, set data type to 'complex' for the response
  signal in y[n] (was 'float' so only the real part was displayed)
- Fix crash when entering a complex coefficient in a previously real-valued filter
- Default file filters for QFileDialog objects could not be set in some cases,
  producing warning messages in the console
- Remove module import and version display for module nmigen to avoid message
  "KeyError: 'V_NMG'"

### New features

- Show number of pos. and neg. overflows in quantizers
- Implement IIR DF1 fixpoint filter
- Export SOS filter coefficients in CMSIS DSP format (via the CSV export options in the coefficient tab)
- New stimulus Randint process
- Add sequence length parameter to MLS process, remove PRBS (which was a Randint
  process with values 0 and 1)

### Maintenance

- move CSV_option_box to separate module 'csv_option_box.py'

## [v0.6.1](https://github.com/chipmuenk/pyfda/tree/v0.6.1) (2022-03-28)

### Bugfixes

- Fix crash with matplotlib 3.1 due to missing Axes3D import
- Fix crash with scipy 1.8.0 by providing local copy of `validate_sos()` (#214)

### New features

- Keyboard modifier `<ALT>` hides the plot title when saving a
  figure or copying it to the clipboard
- Add new stimulus "PWM"
- Verified functionality with Python 3.10

## [v0.6.0](https://github.com/chipmuenk/pyfda/tree/v0.6.0) (2021-12-23)

### Bugfixes

- Recalculate frequency specs in 'k' in the y[n] widget when `self.N` has been changed
- Renamed file `iir_df1.py` to `iir_df1.py_bak` to prevent it from being analyzed
  by `python setup.py install`. The myhdl keyword `async` creates an error with
  python 3.7 and up.
- Update frequency specs when the frequency unit has been changed (regression)
- Angles now can be entered in the Input P/Z tab by preceding "<" instead of the
  angle character
- It is now possible to set the filter type ('FIR' or 'IIR') in the Coeffs tab.
  Changing the filter type now highlights the save button.
- Complex flag is reset in fixpoint simulation when switching back from complex
  to real stimuli
- Improved legend in the y[n] / Y(f) tab (markers were missing, tab alignment didn't
  work)
- Improve group delay algorithms for IIR, allow selection between algorithms.
  Equalize length of f and tau_g in differentiation algorithm (selecting 'Diff'
  crashed pyfda for dual sided spectra)

### New features accessible from the UI

- Improved FFT window widget for displaying the window in time and frequency domain, it
  can be invoked from the `y[n]` tab and the Firwin filter design subwidget with
  much improved selection of window function for spectral analysis (`y[n]` tab)
  and Firwin filter design

  - Window function can be changed from combo boxes in the main widget and in
    the FFT widget
  - improved tooltipps
  - optional combobox for window parameters (used e.g. for Blackmanharris window)

- Lots of improvements in `y[n]` tab:

  - UI overhaul
  - Simulation is now frame based simulation to interrupt simulation of long
    sequences and audio I/O in the future. Progress bar works, though.
  - Add widgets T1 and T2 for time and TW1 and TW2 for delays in y[n] and use them
      for impulse shaped stimuli
  - New stimuli 'Gauss' and 'Rect impulse'
  - New stimulus 'Exp' (complex exponentials)
  - New noise types "Maximum Length Sequence" and "Brownian"
  - Tooltips for combo box items
  - Replace check boxes by checkable push bottons for a cleaner UI
  - Group stimuli for a better overview
  - Display magnitude and phase in frequency tab

- Allow turning off automatic grid alignment between mag. and phase in the
  `H(f)` tab
- Allow changing the number of FFT data points via `Info -> Settings`
- Plots can be copied to the clipboard in base64 encoded PNG format for easier
  embedding in e.g. HTML pages or Jupyter Noteboks.
  The \<img\> tag can be included as well. This is controlled with the modifiers
  \<SHIFT\> or \<CTRL\>.
- New overlays 'Contours' and 'Filled Contours' for P/Z Plots

### Code maintenance

- Complete make-over of signalling for DRY using new method
  'pyfda_qt_lib.emit()' to generate default dict keys 'id' and 'class' and
     providing an time-to-live mechanisms for signals

- Fixpoint and floating point simulation is now frame based; in a future version
  this will allow to stop long running simulation and / or update the plot during
  simulation. Restructured and simplified fixpoint simulation flow.

- Started using pyfixp for fixpoint simulations. nMigen / Amaranth interfaces are
  still implemented but filter is not enabled by default as frame based simulations
  are not implemented.
- Fixpoint filters now live in their own subdirectories together with graphics and
  other related files.
- Try to detect YOSYS executable and store path and version in `dirs.YOSYS_EXE`
  and `dirs.YOSYS_VER`
- Started preparation of code for i18n
- Renamed subdirectory "filter_designs" to "filter_widgets" for consistency with
  other widgets and updated required config file version from 3 to 4
- Provide a simple IIR allpass design as an template for a simple filter
  widget
- New command options when starting pyfda: -h for help, -i for infos on
  paths and files and -r for replacing the config files with copies of
  the templates

## [v0.5.3](https://github.com/chipmuenk/pyfda/tree/v0.5.3) (2020-12-08)

(There is no release v0.5.2)

### Bugfixes

- Use f_C widgets in elliptic manual filter design (entered values had not been
  used for the filter design)

### New features

- Added widget duty cycle for the rect pulse, enabling and disabling of widgets
  is now structured much cleaner
- Absolute frequencies can be locked now, i.e. normalized frequencies change
  with the sampling frequency, absolute frequencies remain unchanged

## [v0.5.1](https://github.com/chipmuenk/pyfda/tree/v0.5.1) (2020-12-01)

### Bugfixes

- Stimulus FM modulation had a false definition. For sinusoidal modulation, it
  is identical to PM modulation. FM modulation is deleted, PM modulation is renamed
  to "PM / FM".
- Various scaling errors for new frequency unit "k" have been fixed
- Wrong time scaling for frequency unit "f_Ny"
- Corrected calculation and display of single-sided spectra and H_id

### New features

- Added stimulus "sinc"
- Added warning indicator for complex valued time signals where display of single-sided
  and H_id spectra may be wrong

## [v0.5.0](https://github.com/chipmuenk/pyfda/tree/v0.5.0) (2020-11-17)

### New features

- Added spectrogram view in the time tab of the transient response widget
- Minor grid lines have been added, grid mode can be cycled through off / coarse (former grid mode) / fine (with minor grid)
- Added links to corresponding documentation page on ReadTheDocs for plot widgets. Doc pages need
  to be updated though ...
- Overhauled plotting of spectra in the y[n] tab
- Cleaned up the UI of the y[n] tab
- Real and imaginary parts of spectra in the y[n] tab now can be plotted

### Bug fixes

- Add fallback mode (cm fonts) again for matplotlib that had been removed due to matplotlib 3.3
  incompatibilities. Fallback mode now supports both mechanisms of mpl 3.3 and older versions.
- Fix error with complex-valued entries in newly created row in `input_coeffs` widget
  (ID: 26ba25f4f947)
- Complex stimuli are now plotted as real and imaginary parts just like the response
  (a.o. ID: 5b20228c93a98a8c601b8ef172f0162dc97d52c1)
- Fix scaling for spectra of complex-valued time signals (ID:8664401933c7b8e5e3137a1d255d0b6f2494450f)
- Allow for complex amplitudes in the impz UI (ID 8664401933c7b8e5e3137a1d255d0b6f2494450f)
- Fix missing taskbar icon under Windows (ID: fe60993a1c1e6ae9c2b6f2b9433ee8e94e55c7d5)
- Lots of small fixes

## [v0.4.0](https://github.com/chipmuenk/pyfda/tree/v0.4.0) (2020-10-19)

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
- Comment out filter `ellip_zero` in configuration template as it is too special for
general usage. If needed, it can be commented back in the user config file.
- Eliminate tab *Files*, its three buttons have been moved to the *Specs* and the *Info* tab

### Bug fixes

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

## [v0.3](https://github.com/chipmuenk/pyfda/tree/v0.3.1) (2020-05)

### New Features

- display pop-up window for showing time and frequency properties of FFT windows for filter design and spectral analysis of transient signals.
- overlay ideal frequency response in impulse response window and scale it with the number of FFT points for impulse responses. This allows a direct comparison of the fixpoint frequency response (calculated from the transient response) and the ideal response (calculated from the filter coefficients).
- improve parameter entry and tooltipps for windowed FIR filter design
- add more windows and use same widget for filter design and spectral analysis
- new AM, FM, PM stimuli for transient response
- first successful generation of a binary for Windows using pyinstall. "spec" - files are included for own experiments

### Bug Fixes

- only install PyQt5 when it cannot be imported to prevent double installation under conda.
- don't try to import PyQt4 (pyfda isn't compatible anymore) as this gives strange error messages on some systems
- stop installation when matplotlib version 3.1.0 is detected as it isn't compatible
- fix crash with matplotlib version 3.2.1 due resulting from changed colormap list
- fix crash when selecting Fixponpoint Tab for a filter design without fixpoint widget
- fix error when trying to load `*.npz` files: `numpy.load()` requires `allow_pickle = True`  since version 1.16.3 for security reasons
- fix error when trying to load pickled files
`[  ERROR] [pyfda.input_widgets.input_files:187] Unexpected error:
The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()`
- fixed buggy export of coefficients in Xilinx and Microsemi format
- Changing the CSV option box parameters from 'file' to 'clipboard' or the other way round in input_coeffs or input_pz would not update the other tab
- improve robustness when importing csv Files (still room for improvements)
- suppress "divide by zero in log10" warnings
- reduce number of debug logging messages, especially from matplotlib
- eliminate false logging warnings and errors
- refactor common libraries, all libraries now are within the folder "libs"
- simplify clipboard instantiation
- improve robustness by enforcing inputs <> 0 ('poszero', 'negzero') in input fields
- rename pole/residue export format suffix to *.txt_rpk

## Release 0.2 (2019-05)

### New features

- **Rework of signal-slot connections**
  - Clearer structure: only one RX / TX signal connection per widget
  - More flexibility: transport dicts or lists via the signals
  - Much improved modularity - new functionality can be easily added

- **Reorganization of configuration files**
  - Specify module names instead of class names for widgets, class names are defined in the modules
  - More flexibility in defining user directories
  - List suitable fixpoint implementations for each filter design as well as the other way around

- **HDL synthesis (beta status, expect bugs)**
  - Use migen to generate synthesizable Verilog netlists for basic filter topologies and do fixpoint simulation
  - When migen is missing on your system, pyFDA will start without the fixpoint tab but otherwise fully functional

- **Didactic improvements**
  - Improved display of transient response and FFT of transient response
  - Display magnitude frequency response in the PZ plot to ease understanding the relationship
- **Documentation using Sphinx / ReadTheDocs**

    Could be more and better ... but hey, it's a start!

## Release 0.1 (2018-02-04)

Initial release
