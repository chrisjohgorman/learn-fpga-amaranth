""" First iteration of separation of the system on chip into three modules.
    This module is for the memory. """

from riscv_assembler import RiscvAssembler
from amaranth import Elaboratable, Module, Array, Signal


class Memory(Elaboratable):

    """ This class describes the memory of our system on chip. """

    def __init__(self):
        a = RiscvAssembler()

        a.read("""begin:
        ADD x1, x0, x0
        ADDI x2, x0, 31
        l0:
        ADDI x1, x1, 1
        BNE x1, x2, l0
        EBREAK
        """)

        a.assemble()
        self.instructions = a.mem
        print(f"memory = {self.instructions}")

        # Instruction memory initialised with above instructions
        self.mem = Array([Signal(32, init=x, name="mem")
                          for x in self.instructions])

        self.mem_addr = Signal(32)
        self.mem_rdata = Signal(32)
        self.mem_rstrb = Signal()

    def elaborate(self, platform):

        """ The memory module sets either the sync domain or slow domain
            depending on whether or not we are being simulated.  If we are
            simulated it is sync, otherwise it is slow. """

        m = Module()

        if platform is None:
            with m.If(self.mem_rstrb):
                m.d.sync += self.mem_rdata.eq(self.mem[self.mem_addr[2:32]])
        else:
            with m.If(self.mem_rstrb):
                m.d.slow += self.mem_rdata.eq(self.mem[self.mem_addr[2:32]])

        return m
