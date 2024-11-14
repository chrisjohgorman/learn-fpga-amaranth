""" This module is the memory module for our SOC. """

from riscv_assembler import RiscvAssembler
from amaranth import Elaboratable, Module, Array, Signal


class Memory(Elaboratable):

    """ This class describe the memory of our system on chip. """

    def __init__(self):
        a = RiscvAssembler()

        a.read("""begin:
        LI  s0, 0
        LI  s1, 16

        l0:
        LB   a0, s0, 400
        CALL wait
        ADDI s0, s0, 1
        BNE  s0, s1, l0
        EBREAK

        wait:
        LI   t0, 1
        SLLI t0, t0, 20

        l1:
        ADDI t0, t0, -1
        BNEZ t0, l1
        RET
        """)

        a.assemble()
        self.instructions = a.mem
        print(f"memory = {self.instructions}")

        # Instruction memory initialised with above instructions
        self.mem = Array([Signal(32, init=x, name=f"mem{i}")
                          for i, x in enumerate(self.instructions)])

        self.mem_addr = Signal(32)
        self.mem_rdata = Signal(32)
        self.mem_rstrb = Signal()

        while len(self.mem) < 100:
            self.mem.append(0)

        self.mem.append(0x04030201)
        self.mem.append(0x08070605)
        self.mem.append(0x0c0b0a09)
        self.mem.append(0xff0f0e0d)

        print(self.mem)

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
