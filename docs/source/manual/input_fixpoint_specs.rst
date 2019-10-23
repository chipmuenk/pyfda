Fixpoint Specs
===============

Overview
--------

The **Fixpoint** tab (:numref:`fig_input_fixpoint`) provides options for 
generating and simulating discrete-time filters that 
can be implemented in hardware. Hardware implementations for discrete-time filters 
usually imply fixpoint arithmetics but this could change in the future as floating point
arithmetics can be implemented on FPGAs using dedicated floating point units (FPUs).

Order and the coefficients have been
calculated by a filter design algorithm from the `pyfda.filter_designs` package to meet
target filter specifications (usually in the frequency domain).

In this tab, a fixpoint implementation can be selected in the upper left corner
(fixpoint filter implementations
are available only for a few filter design algorithms at the moment, most notably
IIR filters are missing). 

The fixpoint format of input word $Q_X$ and output word
::math`Q_Y` can be adjusted for all fixpoint filters, pressing the "lock" button
makes the format of input and output word identical. Depending on the fixpoint
filter, other formats (coefficients, accumulator) can be set as well.

In general, **Ovfl.** combo boxes determine overflow behaviour (Two's complement
wrap around or saturation), **Quant.** combo boxes select quantization behaviour
between rounding, truncation ("floor") or round-towards-zero ("fix"). These methods
may not all be implemented for each fixpoint filter. Truncation is easiest to
implement but has an average bias of -1/2 LSB, in contrast, rounding has no bias
but requires an additional adder. Only rounding-towards-zero guarantees that the
magnitude of the rounded number is not larger than the input, thus preventing
limit cycles in recursive filters.

.. _fig_input_fixpoint:

.. figure:: ../img/manual/pyfda_input_fixpoint.png
   :alt: Fixpoint parameter entry widget
   :width: 50%
   :align: center
   
   Fixpoint parameter entry widget

Typical simulation results are shown in :numref:`fig_pyfda_screenshot_hn_fix_t`
(time domain) and :numref:`fig_pyfda_screenshot_hn_fix_f` (frequency domain).

.. _fig_pyfda_screenshot_hn_fix_t:

.. figure:: ../img/pyfda_screenshot_hn_fix_t.png
   :alt: Screenshot of fixpoint simulation results (time domain)
   :width: 100%
   :align: center
   
   Fixpoint simulation results (time domain)

Fixpoint filters are inherently non-linear due to quantization and saturation effects,
that's why frequency characteristics can only be derived by running a transient
simulation and calculating the Fourier response afterwards:
   
.. _fig_pyfda_screenshot_hn_fix_f:

.. figure:: ../img/pyfda_screenshot_hn_fix_f.png
   :alt: Screenshot of fixpoint simulation results (frequency domain)
   :width: 100%
   :align: center

   Fixpoint simulation results (frequency domain)

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

