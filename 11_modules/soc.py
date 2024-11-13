""" First iteration of separation of the system on chip into three modules.
    This is the main module, the SOC. """

from memory import Memory
from cpu import CPU
from amaranth import Elaboratable, Signal, Module, DomainRenamer


class SOC(Elaboratable):

    """ This class describe the SOC itself. """

    def __init__(self):

        self.leds = Signal(5)

        # Initialize instance variables being used by this module
        self.cpu = None
        self.memory = None

    def elaborate(self, platform):

        """ Here we connect the CPU and memory modules.  The memory module
            mem_addr, mem_rstrb and mem_rdata get connected to their
            respective CPU counterparts.  Then we connect the x1 register
            to the LEDs. """

        m = Module()

        # TODO - establish if this conditional is needed
        if platform is None:
            memory = Memory()
            cpu = CPU()
        else:
            memory = DomainRenamer("slow")(Memory())
            cpu = DomainRenamer("slow")(CPU())
        m.submodules.cpu = cpu
        m.submodules.memory = memory

        self.cpu = cpu
        self.memory = memory

        x1 = Signal(32)

        # Connect memory to CPU
        m.d.comb += [
            memory.mem_addr.eq(cpu.mem_addr),
            memory.mem_rstrb.eq(cpu.mem_rstrb),
            cpu.mem_rdata.eq(memory.mem_rdata)
        ]

        # CPU debug output
        m.d.comb += [
            x1.eq(cpu.x1),
            self.leds.eq(x1[0:5])
        ]

        return m
