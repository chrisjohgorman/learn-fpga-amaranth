from memory import Memory
from cpu import CPU
from amaranth import Elaboratable, Signal, Module, DomainRenamer, ClockSignal


class SOC(Elaboratable):

    def __init__(self):

        self.leds = Signal(5)

        # Signals in this list can easily be plotted as vcd traces
        self.ports = []

        # Initialize instance variables being used by this module
        self.cpu = None
        self.memory = None

    def elaborate(self, platform):

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

        # Export signals for simulation
        def export(signal, name):
            if not isinstance(signal, Signal):
                newsig = Signal(signal.shape(), name=name)
                m.d.comb += newsig.eq(signal)
            else:
                newsig = signal
            self.ports.append(newsig)
            setattr(self, name, newsig)

        if platform is None:
            export(ClockSignal("sync"), "sync_clk")

        return m
