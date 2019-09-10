User Manual
===========

This part of the documentation is intended to describe the features of pyFDA that are relevant to a user (i.e. non-developer).

Once you have started up pyFDA, you'll see a screen similar to the following figure:

.. figure:: ../img/pyfda_specs_Hf.png
   :alt: pyfda screenshot

   Screenshot of pyfda

*	**Inputs widgets:** On the left-hand side you see tabs for different input widgets, i.e. where you can enter and modify parameters for the filter to be designed

*	**Plotting widgets** can be selected on the right hand side of the application.

The two parts can be resized using the handles (red dots).


.. toctree::
   :maxdepth: 1
   :caption: Contents

   input_specs
   fixpoint_specs


Customization
~~~~~~~~~~~~~

- Layout and some parameters can be customized with the file
  ``pyfda/pyfda_rc.py`` (within the install directory right now). 
- Select which widgets and filters will be included, define a user
  directory for integration of your own widgets in ``<USER_HOME>/.pyfda/pyfda.conf``
- Control logging behaviour with ``<USER_HOME>/.pyfda/pyfda_log.conf``

.. include:: pyfda_conf
   :literal:
