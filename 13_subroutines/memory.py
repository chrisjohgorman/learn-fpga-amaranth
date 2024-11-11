from riscv_assembler import RiscvAssembler
from amaranth import Elaboratable, Module, Array, Signal


class Memory(Elaboratable):

    def __init__(self):
        a = RiscvAssembler()

        a.read("""begin:
        ADD x10, x0, x0

        l0:
        ADDI x10, x10, 1
        JAL x1, wait
        JAL zero, l0
        EBREAK

        wait:
        ADDI x11, x0, 1
        SLLI x11, x11, 20

        l1:
        ADDI x11, x11, -1
        BNE x11, x0, l1
        JALR x0, x1, 0
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
        m = Module()

        if platform is None:
            with m.If(self.mem_rstrb):
                m.d.sync += self.mem_rdata.eq(self.mem[self.mem_addr[2:32]])
        else:
            with m.If(self.mem_rstrb):
                m.d.slow += self.mem_rdata.eq(self.mem[self.mem_addr[2:32]])

        return m
