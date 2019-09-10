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

:mod:`input_specs`
-------------------

.. automodule:: pyfda.input_widgets.input_specs
	:members:


.. _dev_select_filter:

:mod:`select_filter`
~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pyfda.input_widgets.select_filter
    :show-inheritance:
	:members:


.. _dev_input_coeffs:

:mod:`input_coeffs`
~~~~~~~~~~~~~~~~~~~~~

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

The configuration file `pyfda.conf` lists which fixpoint classes (e.g. ``FIR_DF`` 
and ``IIR_DF1``) can be used with which filter design algorithm.
`tree_builder` parses this file and writes all fixpoint modules
into the list `fb.fixpoint_widgets_list`. The input widget 
`pyfda.input_widgets.input_fixpoint_specs` constructs a combo box from this list 
with references to all successfully imported fixpoint modules. The currently 
selected fixpoint widget (e.g. `FIR_DF`) is imported from :ref:`dev_mod_fixpoint_widgets` 
together with the referenced picture.

Each fixpoint module / class contains a widget that is constructed using helper
classes from `fixpoint_widgets.fixpoint_helpers.py`. The widgets allow entering
fixpoint specifications like word lengths and formats for input, output and 
internal structures (like an accumulator) for each class. It also contains a 
reference to a picture showing the filter topology.


A migen filter instance `self.hdlfilter` of e.g. :ref:`dev_fixpoint_widgets_fir_df`
is instantiated as ``hdlfilter``. Its methods 

* ``hdlfilter.set_stimulus(self.stim)``
* ``hdlfilter.run_sim()``
* ``self.fx_results = hdlfilter.get_response()``
* ``hdlfilter.convert(hdl=hdl, name=hdl_file_name, path=hdl_dir_name)``

are used for bit-true simulations and for generating Verilog code for the filter. 


.. automodule:: pyfda.input_widgets.input_fixpoint_specs
	:members:

