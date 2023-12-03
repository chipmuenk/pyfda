.. _man_fixpoint_arithmetics:

####################
Fixpoint Arithmetics
####################

Overview
---------

In contrast to floating point numbers, **fixpoint** numbers have a fixed scaling, 
requiring more care to avoid over- or underflows. 

The fixpoint format of input word :math:`Q_X` and output word
:math:`Q_Y` can be adjusted for all fixpoint filters, pressing the "lock" button
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

Typical simulation results are shown in :numref:`fig_pyfda_screenshot_yn_overflows`,
where first the input signal exceeds the numeric range and then the output signal.
The overflow behaviour is set to 'wrap', resulting in twos-complement wrap around 
with changes in the sign.

.. _fig_pyfda_screenshot_yn_overflows:

.. figure:: ../screenshots/pyfda_screenshot_fix_yn_t.png
   :alt: Screenshot of fixpoint simulation results (time domain)
   :width: 80%
   :align: center
   
   Fixpoint filter response with overflows

Truncation and wrap-around
**************************

The following shows an example of a positive number in Q2.4 that is converted to Q1.3
format using truncation. It's easy to see that for simple wrap-around
logic, the sign of the result may change.

::

  S | WI1 | WI0 . WF0 | WF1 | WF2 | WF3  :  WI = 2, WF = 4, W = 7
  0 |  1  |  0  .  1  |  0  |  1  |  1   =  43 (QINT) or 43/16 = 2 + 11/16 (QFRAC)
                |
                v
       S  | WI0 . WF0 | WF1 | WF2        :  WI = 1, WF = 3, W = 5
       1     0  .  1  |  0  |  1         = -32 + 21 = -11 (subtract -2Ŵ for sign bit)
                                         = -16 + 5  = -11 (sign bit as -2^(W -1) )
                                         or -2 + 5/8 = -11 / 8


Summation
*********

Before adding two fixpoint numbers with a different number of integer and/or
fractional bits, integer and fractional word lenghts need to equalized:

- the fractional parts are padded with zeros
- the integer parts need to be sign extended, i.e. with zeros for positive
  numbers and with ones for negative numbers
- adding numbers can require additional integer places due to word growth

For this reason, the position of the binary point needs to be respected when
summing fixpoint numbers.

::

  S | WI1 | WI0 . WF0 | WF1 | WF2 | WF3  :  WI = 2, WF = 4, W = 7
  0 |  1  |  0  .  1  |  0  |  1  |  1   =  43 (INT) or 43/16 = 2 + 11/16 (RWV)

                +

  S | WI1 | WI0 . WF0 | WF1 | WF2 | WF3  :  WI = 2, WF = 4, W = 7
  0 |  0  |  0  .  1  |  0  |  1  |  0   =  10 (INT) or 10/16 (RWV)

                =

  S | WI1 | WI0 . WF0 | WF1 | WF2 | WF3  :  WI = 2, WF = 4, W = 7
  0 |  1  |  1  .  0  |  1  |  0  |  1   =  53 (INT) or 53/16 = 3 + 5/16 (RWV)

Products
*********