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
   pyfda_fixpoint_widgets
   pyfda_filter_blocks

Software Organization
----------------------

The software is organized as shown in the following figure

.. figure:: ../img/pyfda_dev_classes_overview.png
   :alt: pyfda class structure
   :width: 100%
   :align: center

   pyfda organization

**Communication:** 
    The modules communicate via Qt's signal-slot mechanism (see: :ref:`dev_signalling`).

**Data Persistence:** 
    Common data is stored in dicts that can be accessed globally (see: :ref:`dev_persistence`).

**Customization:** 
    The software can be customized via the file ``conf.py`` (see: :ref:`dev_customization`).

.. _dev_signalling:

Signalling: What's up?
----------------------

The figure above shows the general pyfda hierarchy. When parameters or settings are
changed in a widget, a Qt signal is emitted that can be processed by other widgets
with a ``sig_rx`` slot for receiving information. The dict ``dict_sig`` is attached
to the signal as a "payload", providing information about the sender and the type
of event . ``sig_rx`` is connected to the 
``process_sig_rx()`` method that processes the dict.

Many Qt signals can be connected to one Qt slot and one signal to many slots, 
so signals of input and plot widgets are collected in 
:mod:`pyfda.input_widgets.input_tab_widgets`
and :mod:`pyfda.plot_widgets.plot_tab_widgets` respectively and connected collectively.

When a redraw / calculations can take a long time, it makes sense to perform these
operations only when the widget is visible and store the need for a redraw in a flag.    

.. code::

    class MyWidget(QWidget):       
        sig_resize = pyqtSignal()   # emit a local signal upon resize
        sig_rx = pyqtSignal(object) # incoming signal 
        sig_tx = pyqtSignal(object) # outgoing signal
        
        def __init__(self, parent):
            super(MyWidget, self).__init__(parent)
            self.data_changed = True # initialize flags
            self.view_changed = True
            self.filt_changed = True
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
                self.recalculate_some_data() # this may take time ...
                self.data_changed = False
            if 'view_changed' in dict_sig and dict_sig['view_changed'] == 'new_limits'\
                or self.view_changed:
                self._update_my_plot()       # ... while this just updates the display
                self.view_changed = False
            if 'filt_changed' in dict_sig or self.filt_changed:
                self.update_wdg_UI()         # new filter needs new UI options
                self.filt_changed = False
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

The following dictionary keys are generally used, individual ones can be created
as needed.

:'sender': Fully qualified name of the sending widget, usually given as ``__name__``.
       The sender name is needed a.o. to prevent infinite loops which may occur
       when the rx event is connected to the tx signal.

:filt_changed': A different filter type (response type, algorithm, ...) has been
    selected or loaded, requiring an update of the UI in some widgets.

:'data_changed': A filter has been designed and the actual data (e.g. coefficients) 
    has changed, you can add the (short) name or a data description as the dict value.
    When this key is sent, most widgets have to be updated.

:'specs_changed': Filter specifications have changed - this will influence only
    a few widgets like the :ref:`dev_plot_hf` widget that plots the filter specifications
    as an overlay or the :ref:`dev_input_info` widget that compares filter performance
    to filter specifications.

:'view_changed': When e.g. the range of the frequency axis is changed from 
    :math:`0 \ldots f_S/2` to :math:`-f_S/2 \ldots f_S/2`, this information can 
    be propagated with the ``'view_changed'`` key.

:'ui_changed': Propagate a change of the UI to other widgets, examples are:

     - ``'ui_changed':'csv'`` for a change of CSV import / export options
     
     - ``'ui_changed':'resize'`` when the parent window has been resized
    
     - ``'ui_changed':'tab'`` when a different tab has been selected



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

