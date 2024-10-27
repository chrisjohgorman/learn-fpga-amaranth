
""" This module provides the system on chip (SOC) implementation """

from amaranth import Module, Signal
from amaranth.lib import wiring
from amaranth.lib.wiring import Out


class SOC(wiring.Component):

    """ This class describes the SOC """

    leds: Out(5)

    def __init__(self):

        super().__init__()

    def elaborate(self, platform):

        """ The clockwork provides a new clock domain called 'slow'.
            We replace the default sync domain with the new one to have the
            counter run slower. """

        m = Module()
        count = Signal(5)

        # The clockwork provides a new clock domain called 'slow'.
        # We replace the default sync domain with the new one to have the
        # counter run slower.
        if platform is None:
            m.d.sync += count.eq(count + 1)
        else:
            m.d.slow += count.eq(count + 1)
        m.d.comb += self.leds.eq(count)

        return m
