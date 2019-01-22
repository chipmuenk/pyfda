Fixpoint Specs
===============

This tab provides options for generating and simulating discrete-time filters that 
can be implemented in hardware. Hardware implementations for discrete-time filters 
usually imply fixpoint arithmetics but this could change over time as floating point
arithmetics can be implemented on FPGAs using dedicated floating point units (FPUs).

Currently, pyfda supports only fixpoint filters. Order and the coefficients have been
calculated by a filter design algorithm from the `pyfda.filter_designs` package to meet
target filter specifications (usually in the frequency domain).

The configuration file ``pyfda.conf`` lists the fixpoint classes to be used, 
e.g.`DF1` and `DF2`. :class:`pyfda.tree_builder.Tree_Builder` parses this file and writes all fixpoint modules 
into the list `fb.fixpoint_widgets_list`. The input widget 
`pyfda.input_widgets.input_fixpoint_specs` constructs a combo box from this list 
with references to all successfully imported fixpoint modules. 
The currently selected fixpoint widget (e.g.`DF1`) is imported from 
`pyfda.fixpoint_widgets` together with the referenced image.

Development
------------

More info on this widget can be found under :ref:`dev_input_fixpoint_specs`.


