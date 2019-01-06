Development
===========

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   pyfda_main_routines
   pyfda_libs
   pyfda_input_widgets
   pyfda_plot_widgets
   pyfda_fixpoint_widgets
   pyfda_filter_blocks


This part of the documentation describes the features of pyFDA that are relevant for developers.

The software is structured as shown in the following figure

.. figure:: ../img/pyfda_dev_classes_overview.png
   :alt: pyfda class structure

   pyfda class structure

Common data is stored in a large dict, the modules communicate via Qt's signal-slot mechanism.

Signalling: What's up?
----------------------

The figure above features the **Specs** widget where you can select:
- *response type* (low pass, band pass, ...)
- *filter type* (IIR for a recursive filter with infinite impulse response or FIR for a transversal filter with finite impulse response)
- *filter class* (elliptic, ...) allowing you to select 

Persistence: Where's the data?
------------------------------

At startup, a dictionary is constructed with information about the filter classes and their methods. The central dictionary `fb.dict` is initialized.


Customization
~~~~~~~~~~~~~

- Layout and some parameters can be customized with the file
  ``pyfda/pyfda_rc.py`` (within the install directory right now). 
- Select which widgets and filters will be included, define a user
  directory for integration of your own widgets in ``<USER_HOME>/.pyfda/pyfda.conf``
- Control logging behaviour with ``<USER_HOME>/.pyfda/pyfda_log.conf``

