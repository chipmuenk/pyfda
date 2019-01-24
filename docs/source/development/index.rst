Development
===========

This part of the documentation describes the features of pyFDA that are relevant for developers.

.. toctree::
   :maxdepth: 1
   :caption: Contents:
   
   pyfda_main_routines
   pyfda_libs
   pyfda_input_widgets
   pyfda_plot_widgets
   pyfda_filter_blocks

Software Hierarchy
-------------------

The software is structured as shown in the following figure

.. figure:: ../img/pyfda_dev_classes_overview.png
   :alt: pyfda class structure
   :align: center

   pyfda hierarchy

Common data is stored in a large dict, the modules communicate via Qt's signal-slot mechanism.

Signalling: What's up?
----------------------

The figure above shows the general pyfda hierarchy. When parameters or settings are
changed in a widget, a Qt signal is emitted to all other widgets via the class level signals
``sig_rx`` and ``sig_tx`` for receiving resp. transmitting information, attached
via a dict (``dict_sig``) as a "payload". ``sig_rx`` is connected to a method 
that processes the dict:    

.. code::

    class MyWidget(QWidget):       
        sig_resize = pyqtSignal()   # emit a local signal upon resize
        sig_rx = pyqtSignal(object) # incoming signal 
        sig_tx = pyqtSignal(object) # outgoing signal
        
        def __init__(self, parent):
            super(Input_Fixpoint_Specs, self).__init__(parent)
            self.sig_rx.connect(self.process_sig_rx) # or in method ``_construct_UI()``
            
        def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming in via subwidgets and sig_rx
        """
        if dict_sig['sender'] == __name__:
            logger.debug("Infinite loop detected")
            return
        if 'data_changed' in dict_sig:
            self.recalculate_some_data() # this might be computationally intensive ...
        if 'view_changed' in dict_sig and dict_sig['view_changed'] == 'new_limits':
            self._update_my_plot()       # ... while this just updates the display
        if 'filt_changed' in dict_sig:
            self.update_wdg_UI()         # new filter needs new UI options

Information is transmitted via the ``sig_tx`` signal:

.. code::

        dict_sig = {'sender':__name__, 'fx_sim':'set_results', 'fx_results':self.fx_results}            
        self.sig_tx.emit(dict_sig)

 The following keys are used for all widgets: 

* 'sender': Fully qualified name of the sending widget, usually given as ``__name__``.
       The sender name is needed a.o. to prevent infinite loops which may occur
       when the rx event is connected to the tx signal.

* 'data_changed'

* 'view_changed'

Persistence: Where's the data?
------------------------------

At startup, a dictionary is constructed with information about the filter 
classes and their methods. The central dictionary ``fb.dict`` is initialized.


Customization
-------------

- Layout and some parameters can be customized with the file
  ``pyfda/pyfda_rc.py`` (within the install directory right now). 
- Select which widgets and filters will be included, define a user
  directory for integration of your own widgets in ``<USER_HOME>/pyfda/pyfda.conf``
- Control logging behaviour with ``<USER_HOME>/pyfda/pyfda_log.conf``

