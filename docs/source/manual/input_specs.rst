Input Specs
===========

The figure below shows a typical view of the **Specs** tab where you can specify
the kind of filter to be designed and its specifications in the frequency domain:

- **Response type** (low pass, band pass, ...)

- **Filter type** (IIR for a recursive filter with infinite impulse response or 
    FIR for a non-recursive filter with finite impulse response)
    
- **Filter class** (elliptic, ...) allowing you to select the filter design algorithm


.. figure:: ../img/manual/pyfda_specs_FIR_MHz.png
   :alt: Screenshot of specs input window
   :align: center

   Screenshot of specs input window


Not all combinations of design algorithms and response types are available - you
won't be offered unavailable combinations and some fields may be greyed out.


Order
-------
The **order** of the filter, i.e. the number of poles / zeros / delays is
either specified manually or the minimum order can be estimated for many filter
algorithms to fulfill a set of given specifications.


Frequencies
------------  
In DSP, specifications and frequencies are expressed in different ways:

.. math::

    F = \frac{f}{f_S}  \textrm{ or }\Omega = \frac{2\pi f}{f_S} = 2\pi F

In pyfda, you can enter parameters as absolute frequency :math:`{{f}}`, as
normalized frequency :math:`{{F}}` w.r.t. to  the :ref:`sampling_frequency` 
:math:`{f_S}` or to the :ref:`nyquist_frequency` :math:`f_{Ny} = f_S / 2`:

.. figure:: ../img/manual/pyfda_specs_fs.png
   :alt: pyfda displaying normalized frequencies
   :align: center
   
   Displaying normalized frequencies

Background Info
---------------

.. _sampling_frequency:

Sampling Frequency
~~~~~~~~~~~~~~~~~~~
One of the most important parameters in a digital signal processing system is 
the **sampling frequency** :math:`{\pmb{f_S}}`, defining the clock frequency with which 
the registers (flip-flops) in the system are updated. In a simple DSP system,
the clock frequency of ADC, digital filter and DAC might be identical:

.. figure:: ../img/manual/ADC_DAC_single_fs.png
   :alt: A simple signal processing system
   :align: center
   
   A simple signal processing system

Sometimes it makes sense to change the sampling frequency in the processing system
e.g. to reduce the sampling rate of an oversampling ADC or to increase the 
clocking frequency of an DAC to ease and improve reconstruction of the analog
signal.

.. figure:: ../img/manual/ADC_DAC_multi_fs.png
   :alt: A signal processing system with muliple sampling frequencies
   :align: center

   A signal processing system with multiple sampling frequencies
   
.. _nyquist_frequency:

Nyquist Frequency
~~~~~~~~~~~~~~~~~~

Aliasing
~~~~~~~~~~~~~~~~~~
   
Development
-----------

More info on this widget can be found under :ref:`dev_input_specs`.

