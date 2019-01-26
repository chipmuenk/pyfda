Development
===========

This part of the documentation describes the features of pyFDA that are relevant for developers.

.. autosummary ::
   :toctree: generated

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

The software is organized as shown in the following figure

.. figure:: ../img/pyfda_dev_classes_overview.png
   :alt: pyfda class structure
   :align: center

   pyfda hierarchy

**Communication:** The modules communicate via Qt's signal-slot mechanism (see: :ref:`dev_signalling`).

**Data Persistence:** Common data is stored in dicts that can be accessed globally (see: :ref:`dev_persistence`).

**Customization:** The software can be customized via the file ``conf.py`` (see: :ref:`dev_customization`).

.. _dev_signalling:

Signalling: What's up?
----------------------

The figure above shows the general pyfda hierarchy. When parameters or settings are
changed in a widget, a Qt signal is emitted to all other widgets that have a
``sig_rx`` slot for receiving information, attached
via a dict (``dict_sig``) as a "payload". ``sig_rx`` is connected to the 
``process_sig_rx()`` method that processes the dict.

When a redraw / calculations can take a long time, it makes sense to perform these
operations only when the widget is visible and store the need for a redraw in a flag.    

.. code::

    class MyWidget(QWidget):       
        sig_resize = pyqtSignal()   # emit a local signal upon resize
        sig_rx = pyqtSignal(object) # incoming signal 
        sig_tx = pyqtSignal(object) # outgoing signal
        
        def __init__(self, parent):
            super(MyWidget, self).__init__(parent)
            self.sig_rx.connect(self.process_sig_rx)
            # usually done in method ``_construct_UI()``
            
        def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming in via subwidgets and sig_rx
        """
        if dict_sig['sender'] == __name__:   # only needed when a ``sig_tx signal`` is fired 
            logger.debug("Infinite loop detected")
            return
            
        if self.isVisible():
            if 'data_changed' in dict_sig or self.data_changed:
                self.recalculate_some_data() # this might be computationally intensive ...
            if 'view_changed' in dict_sig and dict_sig['view_changed'] == 'new_limits'\
                or self.view_changed:
                self._update_my_plot()       # ... while this just updates the display
            if 'filt_changed' in dict_sig or self.filt_changed:
                self.update_wdg_UI()         # new filter needs new UI options
            # don't forget to reset the 'changed' flags in the corresponding routines!
        else:
            if 'data_changed' in dict_sig or 'view_changed' in dict_sig:
                self.data_changed = True
                self.view_changed = True
            if 'filt_changed' in dict_sig:
                self.filt_changed = True


Information is transmitted via the global ``sig_tx`` signal:

.. code::

        dict_sig = {'sender':__name__, 'fx_sim':'set_results', 'fx_results':self.fx_results}            
        self.sig_tx.emit(dict_sig)

The following keys are used for all widgets: 

:'sender': Fully qualified name of the sending widget, usually given as ``__name__``.
       The sender name is needed a.o. to prevent infinite loops which may occur
       when the rx event is connected to the tx signal.

:'data_changed': A filter has been designed and the actual data (e.g. coefficients) 
    has changed, you can add the (short) name or a data description as the dict value.
    When this key is sent, most widgets have to be updated.

:'specs_changed': Filter specifications have changed - this will influence only
    a few widgets like the :ref:`dev_plot_hf` widget that plots the filter specifications
    as an overlay or the :ref:`dev_input_info` widget that compares filter performance
    to filter specificatiions.

:'view_changed': When e.g. the range of the frequency axis is changed from 
    :math:'0 \ldots f_S/2' to :math:`-f_S/2 \ldots f_S/2`, this information can 
    be propagated with the 'view_changed' key.

:'ui_changed':



.. _dev_persistence:

Persistence: Where's the data?
------------------------------

At startup, a dictionary is constructed with information about the filter 
classes and their methods. The central dictionary ``fb.dict`` is initialized.

.. _dev_customization:

Customization: Any color so long as it's black
-----------------------------------------------

- Layout and some parameters can be customized with the file
  ``pyfda/pyfda_rc.py`` (within the install directory right now). 
- Select which widgets and filters will be included, define a user
  directory for integration of your own widgets in ``<USER_HOME>/pyfda/pyfda.conf``
- Control logging behaviour with ``<USER_HOME>/pyfda/pyfda_log.conf``

