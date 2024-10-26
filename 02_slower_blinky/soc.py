from clockworks import Clockworks
from amaranth import Elaboratable, Module, Signal

# Import the new Clockworks class that handles creating new clock signals


class SOC(Elaboratable):

    def __init__(self):

        self.leds = Signal(5)

    def elaborate(self, platform):

        m = Module()

        count = Signal(5)

        # Instantiate the clockwork with a divider of 2^21

        # Add the clockwork to the top module. If this is not done,
        # the logic will not be instantiated.

        # The clockwork provides a new clock domain called 'slow'.
        # We replace the default sync domain with the new one to have the
        # counter run slower.
        m.d.slow += count.eq(count + 1)

        m.d.comb += self.leds.eq(count)

        return m
