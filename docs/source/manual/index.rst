User Manual
===========

This part of the documentation is intended to describe the features of pyFDA that are relevant to a user (i.e. non-developer).

Once you have started up pyFDA, you'll see a screen similar to the following figure:

.. figure:: ../img/pyfda_specs_Hf.png
   :alt: pyfda screenshot

   Screenshot of pyfda

*	**Inputs widgets:** On the left-hand side you see tabs for different input widgets, i.e. where you can enter and modify parameters for the filter to be designed

*	**Plotting widgets** can be selected on the right hand side of the application.

*   **Logger window** is in the lower part of the plotting window, it can be resized
        or completely closed. The content of the logger window can be selected, copied
        or cleared with a right mouse button context menu.

The invidual windows can be resized using the handles (red dots).

.. toctree::
   :maxdepth: 1
   :caption: Contents

   input_specs
   input_coeffs
   input_pz
   input_info
   input_files
   input_fixpoint_specs
   
.. toctree::
   :maxdepth: 1
   :caption: Plotting Widgets

   plot_hf
   plot_phi
   plot_tau_g
   plot_pz

.. _man_customization:

Customization
--------------
You can customize pyfda behaviour in some configuration files:

pyfda.conf
~~~~~~~~~~~~~

A copy of ``pyfda/pyfda.conf`` is created in ``<USER_HOME>/.pyfda/pyfda.conf``
where it can be edited by the user to choose which widgets and filters will be included.
Fixpoint widgets can be assigned to filter designs and one or more user directories can 
be defined if you want to develop and integrate your own widgets (it's not so hard!):

.. include:: pyfda_conf.rst

pyfda_log.conf
~~~~~~~~~~~~~~~

A copy of ``pyfda/pyfda_log.conf`` is created in ``<USER_HOME>/.pyfda/pyfda_log.conf``
where it can be edited to control logging behaviour:

.. include:: pyfda_conf_log.rst

pyfda_rc.py
~~~~~~~~~~~~~~~

Layout and some parameters can be customized with the file
``pyfda/pyfda_rc.py`` (within the install directory right now, no user copy). 




