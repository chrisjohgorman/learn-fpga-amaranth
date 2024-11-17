""" This module is the memory module for our SOC. """

from riscv_assembler import RiscvAssembler
from amaranth import Elaboratable, Module, Array, Signal


class Memory(Elaboratable):

    """ This class describe the memory of our system on chip. """

    def __init__(self):
        a = RiscvAssembler()

        a.read("""begin:
        LI  a0, 0
        LI  s1, 16
        LI  s0, 0

        l0:
        LB  a1, s0, 400
        SB  a1, s0, 800
        CALL wait
        ADDI s0, s0, 1
        BNE s0, s1, l0

        LI s0, 0

        l1:
        LB a0, s0, 800
        CALL wait
        ADDI s0, s0, 1
        BNE s0, s1, l1
        EBREAK

        wait:
        LI t0, 1
        SLLI t0, t0, 3

        l2:
        ADDI t0, t0, -1
        BNEZ t0, l2
        RET
        """)

        a.assemble()
        self.instructions = a.mem

        # Add some data at offset 400 / word 100
        while len(self.instructions) < 100:
            self.instructions.append(0)
        self.instructions.append(0x04030201)
        self.instructions.append(0x08070605)
        self.instructions.append(0x0c0b0a09)
        self.instructions.append(0xff0f0e0d)
        # Add 0 memory up to offset 1024 / word 256
        while len(self.instructions) < 256:
            self.instructions.append(0)

        print(f"memory = {self.instructions}")

        # Instruction memory initialised with above instructions
        self.mem = Array([Signal(32, init=x, name=f"mem{i}")
                          for i, x in enumerate(self.instructions)])

        self.mem_addr = Signal(32)
        self.mem_rdata = Signal(32)
        self.mem_rstrb = Signal()
        self.mem_wdata = Signal(32)
        self.mem_wmask = Signal(4)

    def elaborate(self, platform):

        """ The memory module sets either the sync domain or slow domain
            depending on whether or not we are being simulated.  If we are
            simulated it is sync, otherwise it is slow. """

        m = Module()

        word_addr = self.mem_addr[2:32]

        # Differentiate between domains depending on whether or not we
        # are simulating.
        if platform is None:
            with m.If(self.mem_rstrb):
                m.d.sync += self.mem_rdata.eq(self.mem[word_addr])
            with m.If(self.mem_wmask[0]):
                m.d.sync += self.mem[word_addr][0:8].eq(self.mem_wdata[0:8])
            with m.If(self.mem_wmask[1]):
                m.d.sync += self.mem[word_addr][8:16].eq(self.mem_wdata[8:16])
            with m.If(self.mem_wmask[2]):
                m.d.sync += [
                    self.mem[word_addr][16:24].eq(self.mem_wdata[16:24])
                ]
            with m.If(self.mem_wmask[3]):
                m.d.sync += [
                    self.mem[word_addr][24:32].eq(self.mem_wdata[24:32])
                ]
        else:
            with m.If(self.mem_rstrb):
                m.d.slow += self.mem_rdata.eq(self.mem[word_addr])
            with m.If(self.mem_wmask[0]):
                m.d.slow += self.mem[word_addr][0:8].eq(self.mem_wdata[0:8])
            with m.If(self.mem_wmask[1]):
                m.d.slow += self.mem[word_addr][8:16].eq(self.mem_wdata[8:16])
            with m.If(self.mem_wmask[2]):
                m.d.slow += [
                    self.mem[word_addr][16:24].eq(self.mem_wdata[16:24])
                ]
            with m.If(self.mem_wmask[3]):
                m.d.slow += [
                    self.mem[word_addr][24:32].eq(self.mem_wdata[24:32])
                ]

        return m
