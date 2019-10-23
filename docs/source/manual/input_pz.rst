Input P/Z
==========

:numref:`fig_input_pz_cartesian` shows a typical view of the **P/Z** tab where 
you can view and edit the filter poles and zeros. Pole / zero values are updated 
every time you design a new filter or update the coefficients.

In the top row, the display of poles and zeros can be disabled as an
update can be time consuming for high order filters (:math:`N > 100`).

Cartesian format
-----------------

.. _fig_input_pz_cartesian:

.. figure:: ../img/manual/pyfda_input_pz_cartesian.png
   :alt: Screenshot of the pole/zero tab for cartesian format
   :align: center
   :width: 50%

   Screenshot of the pole/zero tab for cartesian format

Poles and zeros are displayed in cartesian format (x and y) by default as shown
in :numref:`fig_input_pz_cartesian`.

Polar format
--------------

.. _fig_input_pz_polar:

.. figure:: ../img/manual/pyfda_input_pz_polar.png
   :alt: Screenshot of the pole/zero tab for polar format
   :align: center
   :width: 50%

   Screenshot of the pole/zero tab for polar format
   
Alternatively, poles and zeros can be displayed and edited in polar format
(radius and angle) as shown in :numref:`fig_input_pz_polar`. Especially for zeros
which typically sit on the unit circle (:math:`r = 1`) this format may be more
suitable.
   
Development
-----------

More info on this widget can be found under :ref:`dev_input_pz`.

