# Changelog

## [v0.3.2](https://github.com/chipmuenk/pyfda/tree/v0.3.1) (2020-09-xx)

**Enhancements:**
- Make compatible to matplotlib 3.3 and clean up hiarchy between NavigationToolbar
  an MPL_widget [\#333](https://github.com/chipmuenk/pull/333) ([chipmuenk](https://github.com/chipmuenk))

  get rid of deprecation warnings

- Pan and zoom now is safely disabled when zoom is locked (no issue or PR) 

- Tracking cursor / annotations in plots [\#112](https://github.com/chipmuenk/issues/112) ([chipmuenk](https://github.com/chipmuenk))

  When available, use mplcursors module (only for matplotlib >= 3.1)
