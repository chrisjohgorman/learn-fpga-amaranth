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
            # export(pc, "pc")
            # export(instr, "instr")
            # export(isALUreg, "isALUreg")
            # export(isALUimm, "isALUimm")
            # export(isBranch, "isBranch")
            # export(isJAL, "isJAL")
            # export(isJALR, "isJALR")
            # export(isLoad, "isLoad")
            # export(isStore, "isStore")
            # export(isSystem, "isSystem")
            # export(rdId, "rdId")
            # export(rs1Id, "rs1Id")
            # export(rs2Id, "rs2Id")
            # export(Iimm, "Iimm")
            # export(Bimm, "Bimm")
            # export(Jimm, "Jimm")
            # export(funct3, "funct3")
            # export(rdId, "rdId")
            # export(rs1, "rs1")
            # export(rs2, "rs2")
            # export(writeBackData, "writeBackData")
            # export(writeBackEn, "writeBackEn")
            # export(aluOut, "aluOut")
            # export((1 << cpu.fsm.state), "state")

        return m
