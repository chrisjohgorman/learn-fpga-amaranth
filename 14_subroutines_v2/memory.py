""" This module is the memory module for our SOC. """

from riscv_assembler import RiscvAssembler
from amaranth import Elaboratable, Module, Array, Signal


class Memory(Elaboratable):

    """ This class describe the memory of our system on chip. """

    def __init__(self):
        a = RiscvAssembler()

        a.read("""begin:
        LI  a0, 0

        l0:
        ADDI a0, a0, 1
        CALL wait
        J    l0
        EBREAK

        wait:
        LI   a1, 1
        SLLI a1, a1, 20

        l1:
        ADDI a1, a1, -1
        BNEZ a1, l1
        RET
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
