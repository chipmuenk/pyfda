.. _dev_mod_fixpoint_widgets:

Package pyfda.fixpoint_widgets
======================================
This package contains widgets and fixpoint descriptions for simulating filter 
designs with fixpoint arithmetics and for converting filter designs to Verilog 
using the migen library. These Verilog netlists can be synthesized e.g. on an FPGA.

Hardware implementations for discrete-time filters usually imply fixpoint 
arithmetics but this could change in the future as floating point arithmetics 
can be implemented on FPGAs using dedicated floating point units (FPUs).

Filter topologies are defined in the corresponding classes and can be implemented
in hardware. The filter topologies use the order and the coefficients that have 
been determined by a filter design algorithm from the `pyfda.filter_designs` 
package for a target filter specification (usually in the frequency domain). Filter
coefficients are quantized according to the settings in the fixpoint widget.

Each fixpoint module / class contains a widget that is constructed using helper
classes from :mod:`fixpoint_widgets.fixpoint_helpers`. The widgets allow entering
fixpoint specifications like word lengths and formats for input, output and 
internal structures (like an accumulator) for each class. It also contains a 
reference to a picture showing the filter topology.

The configuration file `pyfda.conf` lists which fixpoint classes (e.g. ``FIR_DF`` 
and ``IIR_DF1``) can be used with which filter design algorithm.
`tree_builder` parses this file and writes all fixpoint modules
into the list `fb.fixpoint_widgets_list`. 

The widgets are selected and instantiated in the widget :ref:`dev_input_fixpoint_specs`.

The input widget 
:mod:`pyfda.input_widgets.input_fixpoint_specs` constructs a combo box from this list 
with references to all successfully imported fixpoint modules. The currently 
selected fixpoint widget (e.g. `FIR_DF`) is imported from :ref:`dev_mod_fixpoint_widgets` 
together with the referenced picture.

First, a filter widget is instantiated as ``self.fx_wdg_inst`` (after the previous
one has been destroyed).

Next, ``fx_wdg_inst.construct_fixp_filter()`` constructs an instance ``fixp_filter``
of a migen filter class (of e.g. :ref:`dev_fixpoint_widgets_fir_df`).

The widget's methods 

* ``response = fx_wdg_inst.run_sim(stimulus)``
* ``fx_wdg_inst.to_verilog()``

are used for bit-true simulations and for generating Verilog code for the filter. 


.. automodule:: pyfda.input_widgets.input_fixpoint_specs
	:members:


are used for bit-true simulations and for generating Verilog code for the filter. 


A fixpoint filter for a given filter design is selected in the widget 
:mod:`pyfda.input_widgets.input_fixpoint_specs` resp.  :ref:`dev_input_fixpoint_specs`


.. _dev_fixpoint_widgets_fir_df:

:mod:`pyfda.fixpoint_widgets.fir_df`
--------------------------------------
.. automodule:: pyfda.fixpoint_widgets.fir_df
	:members:
 