
[![Documentation Status](https://readthedocs.org/projects/filter-blocks/badge/?version=latest)](https://filter-blocks.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/cfelton/filter-blocks.svg?branch=master)](https://travis-ci.org/cfelton/filter-blocks)
[![Coverage Status](https://coveralls.io/repos/github/cfelton/filter-blocks/badge.svg?branch=master)](https://coveralls.io/github/cfelton/filter-blocks?branch=master)
[![Join the chat at https://gitter.im/chipmuenk/pyFDA](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/chipmuenk/pyFDA?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![MIT licensed](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![codebeat badge](https://codebeat.co/badges/fd78906c-9f59-44e5-8c9a-d31d2439fa46)](https://codebeat.co/projects/github-com-cfelton-filter-blocks-master)
[![Code Health](https://landscape.io/github/cfelton/filter-blocks/master/landscape.svg?style=flat)](https://landscape.io/github/cfelton/filter-blocks/master)


This repository contains a collection of hardware
digital filter implementations coded with [myhdl](http://myhdl.org).


In addition to the digital filters, this repository also contains
a class based API that is integrated with the
[pyfda](https://github.com/chipmuenk/pyFDA)
project.  A subset of the digital filters can be configured
and analyzed from the
[pyfda](https://github.com/chipmuenk/pyFDA) GUI.  
The filter-blocks and pyfda integration is
a work in progress and currently exists in beta form.  The
beginning of the documentation for the pyfda class based
API can be found [here]().

<!--
If any of the filter blocks and/or code from this repository are
used in any publication this repository can be cited with the
following:
-->

The paper "A comparison of efficient first decimation filters
for continuous time delta sigma modulators", presented at the
2017 IEEE Asilomar Signals, Systems, and Computers conference
used the blocks in the
[edf](https://github.com/cfelton/filter-blocks/filter_blocks/edf)
(efficient decimation filter) directory.

<!--
Many of the filter blocks in this repository can be configured
and anaylyzed with the [pyfda]() tool.
-->
