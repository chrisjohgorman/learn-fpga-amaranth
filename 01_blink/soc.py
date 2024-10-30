
""" This module provides a system on chip (SOC) implementation of
    blinking the leds on the FPGA. """

from amaranth import Elaboratable, Module, Signal


# Any Elaboratable class is used to generate HDL output
class SOC(Elaboratable):

    """ This class blinks the leds on the FPGA """

    def __init__(self):

        # A Signal is usually created with its number of bits (default = 1).
        # Signals declared as instance variables (self.*) are accessible
        # from outside the class (either as input or output).
        # These signals define the external interface of the module.
        self.leds = Signal(5)

    def elaborate(self, platform):

        """ We create a new module and signal.  Then we sync to the
            positive edge of the implicit clock signal and output
            a different led output value each clock tick.  Unfortunatley
            we cannot see the difference between the led blinks as the
            clock is ticking too fast. """

        # Create a new Amaranth module
        m = Module()

        # This is a local signal, which will not be accessible from outside.
        count = Signal(5)

        # In the sync domain all logic is clocked at the positive edge of
        # the implicit clk signal.
        m.d.sync += count.eq(count + 1)

        # The comb domain contains logic that is unclocked and purely
        # combinatorial.
        m.d.comb += self.leds.eq(count)

        return m
