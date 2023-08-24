# Building and packaging pyfda

## pip and PyPI
Pip packages (source only) are created using the `setuptools` flow:

    > python setup.py clean
    > python setup.py bdist_wheel sdist
    
which creates a `dist` directory containing a python wheel `pyfda-<VERSION>.whl` and the source archive `pyfda-<VERSION>.tar.gz`. 
Creating a source archive (and hence the `sdist` option) is optional, wheels are the standard format for distributing python modules.

Non-python files to be included in the package have to be declared in 
`MANIFEST.in`, see 
<https://packaging.python.org/guides/using-manifest-in/>.
