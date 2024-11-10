""" This module provides the system on chip (SOC) implementation
    for the ALU and uses the riscv-assembly program to simplify the
    readability of the operations. """

from riscv_assembler import RiscvAssembler
from amaranth import Module, Signal, Array, Mux, Cat, Const, ClockSignal
from amaranth.lib import wiring
from amaranth.lib.wiring import Out


class SOC(wiring.Component):

    """ This class describes the SOC arithmetic logic unit (ALU) encoding
        logic instructions with riscv assembler commands """

    leds: Out(5)

    def __init__(self):

        # Signals in this list can easily be plotted as vcd traces
        self.ports = []

        a = RiscvAssembler()
        a.read("""begin:
        LUI x1, 0b11111111111111111111111111111111
        ORI x1, x1, 0b11111111111111111111111111111111
        EBREAK
        """)

        a.assemble()
        self.sequence = a.mem
        print(f"memory = {self.sequence}")

        super().__init__()

    def elaborate(self, platform):

        """ The arithmetic logic unit performs arithmetical and logic
            operations.  It receives binary input from registers,
            performs arithmetical and logic operations and creates,
            stores and distributes binary output back into registers
            for further processing.   For lui and auipc instructions
            we need only modify varialbles write_back_data and write_back_en
            to add conditions for both lui and auipc. """

        m = Module()

        # Program counter
        pc = Signal(32)

        # Current instruction
        instr = Signal(32, init=0b0110011)

        # Instruction memory initialised with above 'sequence'
        mem = Array([Signal(32, init=x, name="mem") for x in self.sequence])

        # Register bank
        regs = Array([Signal(32, name="x"+str(x)) for x in range(32)])
        rs1 = Signal(32)
        rs2 = Signal(32)

        # ALU registers
        alu_out = Signal(32)
        take_branch = Signal(32)

        # Opcode decoder
        is_alu_reg = instr[0:7] == 0b0110011
        is_alu_imm = instr[0:7] == 0b0010011
        is_branch =  instr[0:7] == 0b1100011
        is_jalr =    instr[0:7] == 0b1100111
        is_jal =     instr[0:7] == 0b1101111
        is_auipc =   instr[0:7] == 0b0010111
        is_lui =     instr[0:7] == 0b0110111
        is_load =    instr[0:7] == 0b0000011
        is_store =   instr[0:7] == 0b0100011
        is_system =  instr[0:7] == 0b1110011

        # Immediate format decoder
        u_imm = (Cat(Const(0, 12), instr[12:32]))
        i_imm = (Cat(instr[20:31], instr[31].replicate(21)))
        s_imm = (Cat(instr[7:12], instr[25:31], instr[31].replicate(21)))
        b_imm = (Cat(0, instr[8:12], instr[25:31], instr[7],
                     instr[31].replicate(20)))
        j_imm = (Cat(0, instr[21:31], instr[20], instr[12:20],
                     instr[31].replicate(12)))

        # Register addresses decoder
        rs1_id = instr[15:20]
        rs2_id = instr[20:25]
        rd_id =  instr[7:12]

        # Function code decdore
        funct3 = instr[12:15]
        funct7 = instr[25:32]

        # ALU
        alu_in1 = rs1
        alu_in2 = Mux(is_alu_reg, rs2, i_imm)
        shamt = Mux(is_alu_reg, rs2[0:5], instr[20:25])

        with m.Switch(funct3) as _:
            with m.Case(0b000):
                m.d.comb += alu_out.eq(Mux(funct7[5] & instr[5],
                                       (alu_in1 - alu_in2),
                                       (alu_in1 + alu_in2)))
            with m.Case(0b001):
                m.d.comb += alu_out.eq(alu_in1 << shamt)
            with m.Case(0b010):
                m.d.comb += alu_out.eq(alu_in1.as_signed()
                                       < alu_in2.as_signed())
            with m.Case(0b011):
                m.d.comb += alu_out.eq(alu_in1 < alu_in2)
            with m.Case(0b100):
                m.d.comb += alu_out.eq(alu_in1 ^ alu_in2)
            with m.Case(0b101):
                m.d.comb += alu_out.eq(Mux(
                    funct7[5],
                    (alu_in1.as_signed() >> shamt),  # arithmetic right shift
                    (alu_in1.as_unsigned() >> shamt)))  # logical right shift
            with m.Case(0b110):
                m.d.comb += alu_out.eq(alu_in1 | alu_in2)
            with m.Case(0b111):
                m.d.comb += alu_out.eq(alu_in1 & alu_in2)

        with m.Switch(funct3) as _:
            with m.Case(0b000):
                m.d.comb += take_branch.eq(rs1 == rs2)
            with m.Case(0b001):
                m.d.comb += take_branch.eq(rs1 != rs2)
            with m.Case(0b100):
                m.d.comb += take_branch.eq(rs1.as_signed() < rs2.as_signed())
            with m.Case(0b101):
                m.d.comb += take_branch.eq(rs1.as_signed() >= rs2.as_signed())
            with m.Case(0b110):
                m.d.comb += take_branch.eq(rs1 < rs2)
            with m.Case(0b111):
                m.d.comb += take_branch.eq(rs1 >= rs2)
            with m.Case("---"):
                m.d.comb += take_branch.eq(0)

        # Next program counter is either next intstruction or depends on
        # jump target
        next_pc = Mux((is_branch & take_branch), pc + b_imm,
                      Mux(is_jal, pc + j_imm,
                      Mux(is_jalr, rs1 + i_imm, pc + 4)))

        # Main state machine
        if platform is None:
            with m.FSM(reset="FETCH_INSTR", domain="sync") as fsm:
                with m.State("FETCH_INSTR"):
                    m.d.sync += instr.eq(mem[pc[2:32]])
                    m.next = "FETCH_REGS"
                with m.State("FETCH_REGS"):
                    m.d.sync += [
                        rs1.eq(regs[rs1_id]),
                        rs2.eq(regs[rs2_id])
                    ]
                    m.next = "EXECUTE"
                with m.State("EXECUTE"):
                    m.d.sync += pc.eq(next_pc)
                    m.next = "FETCH_INSTR"
        else:
            with m.FSM(reset="FETCH_INSTR", domain="slow") as fsm:
                with m.State("FETCH_INSTR"):
                    m.d.slow += instr.eq(mem[pc[2:32]])
                    m.next = "FETCH_REGS"
                with m.State("FETCH_REGS"):
                    m.d.slow += [
                        rs1.eq(regs[rs1_id]),
                        rs2.eq(regs[rs2_id])
                    ]
                    m.next = "EXECUTE"
                with m.State("EXECUTE"):
                    m.d.slow += pc.eq(next_pc)
                    m.next = "FETCH_INSTR"

        # Register write back
        write_back_data = Mux((is_jal | is_jalr), (pc + 4),
                              Mux(is_lui, u_imm,
                              Mux(is_auipc, (pc + u_imm), alu_out)))
        write_back_en = fsm.ongoing("EXECUTE") & (
                is_alu_reg |
                is_alu_imm |
                is_lui     |
                is_auipc   |
                is_jal     |
                is_jalr)

        if platform is None:
            with m.If(write_back_en & (rd_id != 0)):
                m.d.sync += regs[rd_id].eq(write_back_data)
                # Assign write_back_data to leds to see what is happening
                m.d.sync += self.leds.eq(write_back_data)
        else:
            with m.If(write_back_en & (rd_id != 0)):
                m.d.slow += regs[rd_id].eq(write_back_data)
                # Assign write_back_data to leds to see what is happening
                m.d.slow += self.leds.eq(write_back_data)

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
            export(pc, "pc")
            export(instr, "instr")
            export(is_alu_reg, "is_alu_reg")
            export(is_alu_imm, "is_alu_imm")
            export(is_branch, "is_branch")
            export(is_jal, "is_jal")
            export(is_jalr, "is_jalr")
            export(is_load, "is_load")
            export(is_store, "is_store")
            export(is_system, "is_system")
            export(rs1_id, "rs1_id")
            export(rs2_id, "rs2_id")
            export(i_imm, "i_imm")
            export(b_imm, "b_imm")
            export(j_imm, "j_imm")
            export(funct3, "funct3")
            export(rd_id, "rd_id")
            export(rs1, "rs1")
            export(rs2, "rs2")
            export(write_back_data, "write_back_data")
            export(write_back_en, "write_back_en")
            export(alu_out, "alu_out")
            export((1 << fsm.state), "state")

        return m
