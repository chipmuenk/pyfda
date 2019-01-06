
from math import sin, pi, fmod, cos
import myhdl as hdl
from myhdl import intbv, always_seq
from filter_blocks.support import Samples


class DDSine(object):
    """ Direct Digital Sine (Synthesis) """

    def __init__(self, frequency, sample_rate, amp, phi, dtype):
        """

        Args:
            frequency:
            sample_rate:
            amp: amplitude
            phi: initial phase
            dtype: data type
        """
        self.f = frequency
        self.fs = sample_rate
        self._amp = amp
        self._phi = phi
        self._max = dtype.max
        self._min = dtype.min
        self._dtype = dtype
        self.zero = False
        self.phi = 0
        self.pinc = 0

    def set_frequency(self, f):
        self.f = f
        self.pinc = fmod(2 * pi * self.f / self.fs, 2 * pi)

    def set_zero(self, z=True):
        self.zero = z

    @hdl.block
    def process(self, clock, reset, xi, xf):
        # determine the number of clocks per sample rate
        # TODO: warning and/or dual-modulus for non-int
        # if  is None:
        #     = Sample(min=self._min, max=self._max)
        assert isinstance(xi, Samples)
        assert isinstance(xf, Samples)

        if hasattr(clock, 'frequency'):
            tpfs = int(round((clock.frequency / self.fs)))
        else:
            tpfs = 1

        cnt = intbv(0, min=0, max=tpfs)
        self.phi = self._phi
        self.pinc = fmod(2 * pi * self.f / self.fs, 2 * pi)

        @always_seq(clock.posedge, reset=reset)
        def tproc():
            xi.valid.next = False
            xf.valid.next = False
            if cnt < tpfs - 1:
                cnt[:] = cnt + 1
            else:
                cnt[:] = 0
                if self.zero:
                    xi.data.next = 0
                    xf.data.next = 0.
                else:
                    self.phi = fmod(self.phi + self.pinc, 2 * pi)
                    x = sin(self.phi) * self._amp
                    _xi = int(round(x * self._max))
                    xi.data.next = _xi
                    xf.data.next = x
                xi.valid.next = True
                xf.valid.next = True

        return tproc
