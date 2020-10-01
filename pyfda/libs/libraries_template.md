###Authors

[pyFDA][home] is written and maintained by Christian Muenker, 
along with the contributors on [github](https://github.com/chipmuenk/pyfda) .

####Special thanks:

- [@endolith](https://github.com/endolith) for his [bandlimited periodic functions](https://gist.github.com/endolith/407991)
- [sbourdeauducq](https://github.com/sbourdeauducq) for discussions and support on [migen](https://github.com/m-labs/migen)
- [@cfelton](https://github.com/cfelton) for a lot of discussions on fixpoint simulations and [myhdl](http://myhdl.org/)
- [@sriyash25](https://github.com/sriyash25) for his contributions on fixpoint filters during the GSoC 2018


[home]: README_PYPI.md


###External modules and libraries

pyFDA itself is licensed under the permissive MIT license. The source code is 
released at the Github repository [chipmuenk/pyfda](https://github.com/chipmuenk/pyfda).

However, the binary distribution of pyFDA bundles several external libraries and icons. 
Most of them have permissive BSDD-style licenses, i.e. MIT or PSF (Python Software Foundation)
with the notable exception of the Qt5 and PyQt libraries and the pyInstaller itself. 
The (L)GPL licenses of these components require an 
[(L)GPL compliant license](https://velovix.github.io/post/lgpl-gpl-license-compliance-with-pyinstaller/), 
hence, the pyFDA binary is distributed with a GPL license.


| Module | Version | Licence | Purpose |
| :------ | :------- | :------- | :------- |
| [Python](https://www.python.org/) | {V_PY}   | PSF | | 
| [numpy](https://numpy.org/) | {V_NP} | BSD | Base package for fast array numerics |
| [scipy](https://scipy.org/) | {V_SCI} | BSD | Library for scientific computing |
| [numexpr](https://github.com/pydata/numexpr) | {V_NUM} | MIT | Fast numerical array expression|
| [matplotlib](https://matplotlib.org/) | {V_MPL} | PSF-based&emsp; | Plotting library |
| [Qt5](https://qt.io/) | {V_QT} | LPGLv3 | Widget library (UI etc.) |
| [PyQt](https://www.riverbankcomputing.com/software/pyqt/) | {V_PYQT} | GPLv3 | Python bindings for Qt5 |
| [Markdown](https://github.com/Python-Markdown/markdown) |  {V_MD} | BSD | Python implementation of Markdown|
| [docutils](https://docutils.sourceforge.io) | {V_DOC} | GPLv3 a.o. | Convert plain text to markup formats |
| migen | | | Fixpoint simulation and synthesis |
| nMigen | {V_NMG} | | Fixpoint simulation and synthesis |
| [mplcursors](https://github.com/anntzer/mplcursors)&emsp: | {V_CUR} | MIT | Interactive cursors (needs Matplotlib >= 3.1) |
| pyInstaller | | GPL 2.0  |Packager for distributing the binary |


Icons (except the pyFDA icon) are taken from the ["Open Iconic"](https://useiconic.com/open/)Icons collection 
under MIT license.

