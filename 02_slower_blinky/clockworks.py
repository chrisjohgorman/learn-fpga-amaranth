

""" This module handles clock division and provides a new 'slow' clock
    domain """

from amaranth import Signal, Module, ClockDomain, ClockSignal
from amaranth.lib import wiring
from amaranth.lib.wiring import Out


class Clockworks(wiring.Component):

    """ This class provides a clock domain which must be initialized as a
        submodule in the top level module """

    o_slow: Out(1)

    def __init__(self, slow=0, sim_slow=None):

        # Since the module provides a new clock domain, which is accessible
        # via the top level module, we don't need to explicitly provide the
        # slow clock signal as an output.

        self.slow = slow
        if sim_slow is None:
            self.sim_slow = slow
        else:
            self.sim_slow = sim_slow

        super().__init__()

    def elaborate(self, platform):

        """ Assign either a slow clock signal or the clock signal of the
            default sync domain """

        clk = Signal()
        m = Module()

        if self.slow != 0:
            # When the design is simulated, platform is None
            if platform is None:
                slow_bit = self.sim_slow
            else:
                slow_bit = self.slow

            slow_clk = Signal(slow_bit + 1)
            m.d.sync += slow_clk.eq(slow_clk + 1)
            m.d.comb += clk.eq(slow_clk[slow_bit])

        else:
            # When no division is requested, just use the clock signal of
            # the default 'sync' domain.
            m.d.comb += clk.eq(ClockSignal("sync"))

        # Create the new clock domain
        m.domains += ClockDomain("slow")

        # Assign the slow clock to the clock signal of the new domain
        m.d.comb += ClockSignal("slow").eq(clk)

        return m
