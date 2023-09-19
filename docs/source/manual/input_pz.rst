Input P/Z
==========

:numref:`fig_input_pz_cartesian` shows a typical view of the **P/Z** tab where
you can view and edit the filter poles and zeros. Pole / zero values are updated
every time you design a new filter or update the coefficients.

You can select the number of displayed digits, poles and zeros are always stored with
full accuracy.

Cartesian format
-----------------

.. _fig_input_pz_cartesian:

.. figure:: ../img/manual/pyfda_input_pz_cartesian.png
   :alt: Screenshot of the pole/zero tab in cartesian format
   :align: center
   :width: 30%

   Screenshot of the pole/zero tab in cartesian format

Poles and zeros are displayed and can be edited in cartesian format (:math:`x` and `y`) by default as shown
in :numref:`fig_input_pz_cartesian`.

Polar format
--------------

.. _fig_input_pz_polar:

.. figure:: ../img/manual/pyfda_input_pz_polar.png
   :alt: Screenshot of the pole/zero tab in polar format
   :align: center
   :width: 30%

   Screenshot of the pole/zero tab in polar format

Alternatively, poles and zeros can be displayed and edited in polar format
(radius and angle) as shown in :numref:`fig_input_pz_polar`. Especially for zeros
which typically sit on the unit circle (:math:`r = 1`) this format may be more
suitable.

During editing, use the '>' character to separate radius and phase. The phase can
be displayed and entered in the following formats:

* **Degrees** with a range of :math:`\pm -180° \ldots +180°`, terminate the phase
  with an 'o' or '°' to indicate degrees.
* **Rad** with a range of :math:`\pm -\pi \ldots +\pi`, simply enter the value or terminate
  the phase with an 'r' or with 'rad' to indicate rads.
* Multiples of **pi** with a range of :math:`\pm -1 \ldots +1`, terminate the phase with
  a 'p' or 'pi' to specifiy multiples of pi.

For real-valued systems, poles and zeros need to be either real-valued or come in
conjugate complex pairs, e.g. :math:`p_1 = 0.5 + 0.5j` and :math:`p_2 = 0.5 - 0.5j` or
:math:`z_1 = 1\angle +0.25 \pi` and :math:`z_2 = 1\angle - 0.25 \pi`. Otherwise, you
end up with a complex-valued system with complex-valued coefficients which is not what
you want in most cases.

Use the corresponding icons to enter a new row or delete one. The trash can deletes the whole
table.

When poles or zeros have been modified, the "upload values" icon becomes highlighted. Changes
are only applied when stored in the internal dict.

Development
-----------

More info on this widget can be found under :ref:`dev_input_pz`.

