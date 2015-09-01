# -*- coding: utf-8 -*-
from os import path
from setuptools import setup, find_packages

# @todo: WIP see https://packaging.python.org/en/latest/index.html

setup(
    name='pyfda',

    # see PEP440 for versioning information
    version='0.1a1',
    description='pyfda description',
    #long_description
    url='https://github.com/chipmuenk/pyFDA',
    author='Christian Munker',
    author_email='',
    license='Apache',
    packages=find_packages(exclude=('contrib', 'docs', 'test')),
    entry_points={
        'console_scripts':[
            'pyfda=pyfda:main',
        ],
    },
)