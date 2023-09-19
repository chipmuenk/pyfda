Package input_widgets
==================================
This package contains the widgets for entering / selecting parameters
for the filter design.

.. currentmodule:: pyfda.input_widgets

.. _dev_input_tab_widgets:

input_tab_widgets
--------------------------------

.. automodule:: pyfda.input_widgets.input_tab_widgets
	:members:


.. _dev_input_specs:

input_specs
--------------

.. automodule:: pyfda.input_widgets.input_specs
	:members:


.. _dev_select_filter:

select_filter
----------------

.. automodule:: pyfda.input_widgets.select_filter
	:members:


.. _dev_input_coeffs:

input_coeffs
--------------------

.. automodule:: pyfda.input_widgets.input_coeffs
	:members:


.. _dev_input_pz:

input_pz
------------------------------------

.. automodule:: pyfda.input_widgets.input_pz
	:members:


.. _dev_input_info:

input_info
--------------

.. automodule:: pyfda.input_widgets.input_info
	:members:



input_fixpoint_specs
---------------------

The configuration file `libs.pyfda_template.conf` lists which fixpoint classes (e.g. ``FIR_DF`` 
and ``IIR_DF1``) can be used with which filter design algorithm.
`libs.tree_builder` parses this file and writes all fixpoint modules
into the list `fb.fixpoint_widgets_list`. The input widget 
:mod:`pyfda.input_widgets.input_fixpoint_specs` constructs a combo box from this list 
with references to all successfully imported fixpoint modules. The currently 
selected fixpoint widget (e.g. `FIR_DF`) is imported from :ref:`dev_mod_fixpoint_widgets` 
together with the referenced picture.

Each fixpoint module / class contains a widget that is constructed using helper
classes from `fixpoint_widgets.fixpoint_helpers.py`. The widgets allow entering
fixpoint specifications like word lengths and formats for input, output and 
internal structures (like an accumulator) for each class. It also contains a 
reference to a picture showing the filter topology.

Details of the mechanism and the module are described in :ref:`dev_input_fixpoint_specs`.

