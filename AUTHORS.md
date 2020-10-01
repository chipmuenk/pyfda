Authors
=======

[pyFDA][home] is written and maintained by Christian Muenker,
along with the contributors on [github](https://github.com/chipmuenk/pyfda) .

Special thanks:
~~~~~~~~~~~~~~~

- [@endolith](https://github.com/endolith) for his [bandlimited periodic functions](https://gist.github.com/endolith/407991)
- [sbourdeauducq](https://github.com/sbourdeauducq) for discussions and support on [migen](https://github.com/m-labs/migen)
- [@cfelton](https://github.com/cfelton) for a lot of discussions on fixpoint simulations and [myhdl](http://myhdl.org/)
- [@sriyash25](https://github.com/sriyash25) for his contributions on fixpoint filters during the GSoC 2018


[home]: README_PYPI.md


External modules and libraries
==============================

pyFDA itself is licensed under the permissive MIT license. The source code is
released at the Github repository [chipmuenk/pyfda](https://github.com/chipmuenk/pyfda).

The binary distribution comes bundled with several external libraries and icons.

Most included software has BSD-style licenses, i.e. MIT or PSF (Python Software Foundation)
with the notable exception of the Qt5 and PyQt libraries and the pyInstaller itself.
The (L)GPL licenses of these components require that the pyFDA binary is released under
GPL license.


| Module | Version | Licence | Purpose |
========================================
| Python | PSF     |
| [numpy](https://numpy.org/) | BSD | Base package for fast array numerics|
| [scipy](https://scipy.org/)  | BSD | | Library for scientific computing |
| [numexpr](https://github.com/pydata/numexpr) | MIT | Fast numerical array expression|
| [matplotlib](https://matplotlib.org/) | PSF-based | Plotting library |
| [Qt5](https://qt.io/)  | LPGLv3 | Widget library (UI etc.) |
| [PyQt](https://www.riverbankcomputing.com/software/pyqt/) | GPLv3 | Python bindings for Qt5 |
| [Markdown](https://github.com/Python-Markdown/markdown)| | BSD | Python implementation of Markdown|
| docutils | |
| migen |  | Fixpoint simulation and synthesis |
| nMigen |  | Fixpoint simulation and synthesis |
| mplcursors | | Interactive cursors |
| pyInstaller | GPL 2.0  |Packager for distributing the binary |

https://stackoverflow.com/questions/59914573/how-to-pass-on-python-variables-to-markdown-table

https://velovix.github.io/post/lgpl-gpl-license-compliance-with-pyinstaller/

Icons (except the pyFDA icon) are taken from the "Open Iconic" Icons collection 
at  [https://useiconic.com/open/](https://useiconic.com/open/) under MIT license.

