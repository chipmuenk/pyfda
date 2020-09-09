# Changelog

## [v0.3.2](https://github.com/chipmuenk/pyfda/tree/v0.3.1) (2020-09-xx)

**Bug Fixes**
- [PR \#333:](https://github.com/chipmuenk/pull/333) Make compatible to matplotlib 3.3 by cleaning up hierarchy for NavigationToolbar
 [(Issue \179)](https://github.com/chipmuenk/pyfda/issues/179) get rid of mpl 3.3 related deprecation warnings, disable zoom rectangle and pan when zoom is locked
([chipmuenk](https://github.com/chipmuenk))

**Enhancements**

- [PR \#333:](https://github.com/chipmuenk/pull/333) Add cursor / annotations in plots [Issue \#112](https://github.com/chipmuenk/issues/112) ([chipmuenk](https://github.com/chipmuenk))

  When available, use mplcursors module (only for matplotlib >= 3.1)
