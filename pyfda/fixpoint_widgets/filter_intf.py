
from myhdl import Signal, intbv

class FilterInterface(object):
    def __init__(self, word_format=(24, 0, 0,), sample_rate=1, clock_frequency=1):
        """ Interface to the various filters

        :param word_format:
        :return:
        """
        self.word_format = word_format
        # @todo: use myhld.fixbv
        # @todo: use myhdl.fixbv, currently the fixed-point coefficient
        # @todo: the current implementation only uses an "all fractional"
        # @todo: format.
        if len(self.word_format) == 2 and self.word_format[1] != 0:
            raise NotImplementedError
        elif (len(self.word_format) == 3 and
              self.word_format[1] != 0 and
              self.word_format[2] != self.word_format[1]-1):
            raise NotImplementedError

        imax = 2**(word_format[0]-1)
        self.data = Signal(intbv(0, min=-imax, max=imax))
        self.data_valid = Signal(bool(0))

        self.sample_rate = sample_rate
        self.clock_frequency = clock_frequency
