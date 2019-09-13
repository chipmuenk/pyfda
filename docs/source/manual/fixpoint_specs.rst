Fixpoint Specs
===============

Overview
--------

This tab provides options for generating and simulating discrete-time filters that 
can be implemented in hardware. Hardware implementations for discrete-time filters 
usually imply fixpoint arithmetics but this could change over time as floating point
arithmetics can be implemented on FPGAs using dedicated floating point units (FPUs).

Order and the coefficients have been
calculated by a filter design algorithm from the `pyfda.filter_designs` package to meet
target filter specifications (usually in the frequency domain).

Word length and saturation / quantization behaviour can be selected in the widget and
simulated:

.. figure:: ../img/pyfda_screenshot_hn_fix_t.png
   :alt: Screenshot of fixpoint simulation results (time domain)
   :width: 100%
   :align: center

Fixpoint filters are inherently non-linear due to quantization and saturation effects,
that's why frequency characteristics can only be derived by running a transient
simulation and calculating the Fourier response afterwards:
   
.. figure:: ../img/pyfda_screenshot_hn_fix_f.png
   :alt: Screenshot of fixpoint simulation results (time domain)
   :width: 100%
   :align: center


Configuration
-------------

The configuration file ``pyfda.conf`` lists the fixpoint classes to be used, 
e.g. ``DF1`` and ``DF2``. :class:`pyfda.tree_builder.Tree_Builder` parses this file 
and writes all fixpoint modules 
into the list ``fb.fixpoint_widgets_list``. The input widget 
:class:`pyfda.input_widgets.input_fixpoint_specs.Input_Fixpoint_Specs` constructs a combo box from this list 
with references to all successfully imported fixpoint modules. 
The currently selected fixpoint widget (e.g. ``DF1``) is imported from 
:mod:`pyfda.fixpoint_widgets` together with the referenced image.

Development
------------

More info on this widget can be found under :ref:`dev_input_fixpoint_specs`.

