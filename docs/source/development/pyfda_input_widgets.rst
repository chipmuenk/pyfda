Package :mod:`pyfda.input_widgets`
==================================
This package contains the widgets for entering / selecting parameters
for the filter design.

.. currentmodule:: pyfda.input_widgets

.. _dev_input_tab_widgets:

:mod:`input_tab_widgets`
--------------------------------------------------------------

.. automodule:: pyfda.input_widgets.input_tab_widgets
	:members:


.. _dev_input_specs:

:mod:`pyfda.input_widgets.input_specs`
---------------------------------------

.. automodule:: pyfda.input_widgets.input_specs
    :show-inheritance:
	:members:


.. _dev_select_filter:

:mod:`pyfda.input_widgets.select_filter`
-----------------------------------------

.. automodule:: pyfda.input_widgets.select_filter
    :show-inheritance:
	:members:


.. _dev_input_coeffs:

:mod:`pyfda.input_widgets.input_coeffs`
----------------------------------------

.. automodule:: pyfda.input_widgets.input_coeffs
    :show-inheritance:
	:members:


.. _dev_input_pz:

:mod:`pyfda.input_widgets.input_pz`
------------------------------------

.. automodule:: pyfda.input_widgets.input_pz
    :show-inheritance:
	:members:


.. _dev_input_info:

:mod:`pyfda.input_widgets.input_info`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pyfda.input_widgets.input_info
    :show-inheritance:
	:members:


.. _dev_input_files:

pyfda.input_widgets.input_files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pyfda.input_widgets.input_files
    :show-inheritance:
	:members:
	
	
.. _dev_input_fixpoint_specs:

:mod:`pyfda.input_widgets.input_fixpoint_specs`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This package contains all fixpoint classes, i.e. classes which define filter 
topologies that can be implemented in hardware. The filter topologies use the 
order and the coefficients that have been determined by a filter design algorithm
from the `pyfda.filter_designs` package. The coefficients have been calculated 
for a desired filter specification (usually in the frequency domain).

Hardware implementations for discrete-time filters usually imply fixpoint 
arithmetics but this could change in the future as floating point arithmetics 
can be implemented on FPGAs using dedicated floating point units (FPUs).

Each fixpoint module / class contains a widget that is constructed using helper
classes from `fixpoint_widgets.fixpoint_helpers.py`. The widgets allow entering
fixpoint specifications like word lengths and formats for input, output and 
internal structures (like an accumulator) for each class. It also contains a 
reference to a picture showing the filter topology.

The configuration file `pyfda.conf` lists the fixpoint classes to be used, e.g. 
`DF1` and `DF2`. `tree_builder` parses this file and writes all fixpoint modules
into the list `fb.fixpoint_widgets_list`. The input widget 
`pyfda.input_widgets.input_fixpoint_specs` constructs a combo box from this list 
with references to all successfully imported fixpoint modules. The currently 
selected fixpoint widget (e.g. `DF1`) is imported from `pyfda.fixpoint_widgets` 
together with the referenced picture.

A myhdl filter instance `self.hdlfilter` of :ref:`dev_filter_blocks_filter_fir`
:ref:`dev_filter_blocks_filter_iir` is instantiated as ``hdlfilter``.  Its methods 

* ``hdlfilter.set_stimulus(self.stim)``
* ``hdlfilter.run_sim()``
* ``self.fx_results = hdlfilter.get_response()``
* ``hdlfilter.convert(hdl=hdl, name=hdl_file_name, path=hdl_dir_name)``

are used for bit-true simulations and for generating VHDL or Verilog code for the filter. 


.. automodule:: pyfda.input_widgets.input_fixpoint_specs
	:members:

