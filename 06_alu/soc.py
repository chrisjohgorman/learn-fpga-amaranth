
""" This module provides the system on chip (SOC) implementation
    for the ALU """

from amaranth import Module, Signal, Array, Mux, Cat, Const, ClockSignal
from amaranth.lib import wiring
from amaranth.lib.wiring import Out


class SOC(wiring.Component):

    """ This class describes the SOC arithmetic logic unit (ALU) """

    leds: Out(5)

    def __init__(self):

        # Signals in this list can easily be plotted as vcd traces
        self.ports = []

        super().__init__()

    def elaborate(self, platform):

        """ The arithmetic logic unit performs arithmetical and logic
            operations.  It receives binary input from registers,
            performs arithmetical and logic operations and creates,
            stores and distributes binary output back into registers
            for further processing. """

        m = Module()

        # Instruction sequence to be executed
        sequence = [
            #       24      16       8       0
            # .......|.......|.......|.......|
            #R         rs2  rs1 f3   rd     op
            #I         imm  rs1 f3   rd     op
            #S    imm  rs2  rs1 f3  imm     op
            # ......|....|....|..|....|......|
            # add x1, x0, x0
            #                    rs2   rs1  add  rd   ALUREG
            # -> x1 = 0
            0b00000000000000000000000010110011,
            # addi x1, x1, 1
            #             imm         rs1  add  rd   ALUIMM
            # -> x1 = 1
            0b00000000000100001000000010010011,
            # addi x1, x1, 1
            #             imm         rs1  add  rd   ALUIMM
            # -> x1 = 2
            0b00000000000100001000000010010011,
            # addi x1, x1, 1
            #             imm         rs1  add  rd   ALUIMM
            # -> x1 = 3
            0b00000000000100001000000010010011,
            # addi x1, x1, 1
            #             imm         rs1  add  rd   ALUIMM
            # -> x1 = 4
            0b00000000000100001000000010010011,
            # add x2, x1, x0
            #                    rs2   rs1  add  rd   ALUREG
            # -> x2 = 4
            0b00000000000000001000000100110011,
            # add x3, x1, x2
            #                    rs2   rs1  add  rd   ALUREG
            # -> x3 = 8
            0b00000000001000001000000110110011,
            # srli x3, x3, 3
            #                   shamt   rs1  sr  rd   ALUIMM
            # -> x3 = 1
            0b00000000001100011101000110010011,
            # slli x3, x3, 31
            #                   shamt   rs1  sl  rd   ALUIMM
            # -> x3 = 0x80000000
            0b00000001111100011001000110010011,
            # srai x3, x3, 5
            #                   shamt   rs1  sr  rd   ALUIMM
            # -> x3 = 0xfc000000
            0b01000000010100011101000110010011,
            # srli x1, x3, 26
            #                   shamt   rs1  sr  rd   ALUIMM
            # -> x1 = 0x3f
            0b00000001101000011101000010010011,

            0b00000000000100000000000001110011  # S ebreak
        ]

        # Program counter
        pc = Signal(32)

        # Current instruction
        instr = Signal(32, init=0b0110011)

        # Instruction memory initialised with above 'sequence'
        mem = Array([Signal(32, init=x, name="mem") for x in sequence])

        # Register bank
        regs = Array([Signal(32, name="x"+str(x)) for x in range(32)])
        rs1 = Signal(32)
        rs2 = Signal(32)

        # ALU registers
        alu_out = Signal(32)

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
        u_imm = (Cat(Const(0).replicate(12), instr[12:32]))
        i_imm = (Cat(instr[20:31], instr[31].replicate(21)))
        s_imm = (Cat(instr[7:12], instr[25:31], instr[31].replicate(21)))
        b_imm = (Cat(0, instr[8:12], instr[25:31],
                 instr[7], instr[31].replicate(20)))
        j_imm = (Cat(0, instr[21:31], instr[20],
                 instr[12:20], instr[31].replicate(12)))

        # Register addresses decoder
        rs1_id = instr[15:20]
        rs2_id = instr[20:25]
        rd_id = instr[7:12]

        # Function code decoder
        funct3 = instr[12:15]
        funct7 = instr[25:32]

        # ALU
        alu_in1 = rs1
        alu_in2 = Mux(is_alu_reg, rs2, i_imm)
        shamt = Mux(is_alu_reg, rs2[0:5], instr[20:25])

        # FIXME - replaced alu with _, if this is broken examine this change
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

        if platform is None:
            # Main state machine for simulator
            with m.FSM(reset="FETCH_INSTR", domain="sync") as fsm:
                with m.State("FETCH_INSTR"):
                    m.d.sync += instr.eq(mem[pc])
                    m.next = "FETCH_REGS"
                with m.State("FETCH_REGS"):
                    m.d.sync += [
                        rs1.eq(regs[rs1_id]),
                        rs2.eq(regs[rs2_id])
                    ]
                    m.next = "EXECUTE"
                with m.State("EXECUTE"):
                    m.d.sync += pc.eq(pc + 1)
                    m.next = "FETCH_INSTR"
        else:
            # Main state machine for FPGA
            with m.FSM(reset="FETCH_INSTR", domain="slow") as fsm:
                with m.State("FETCH_INSTR"):
                    m.d.slow += instr.eq(mem[pc])
                    m.next = "FETCH_REGS"
                with m.State("FETCH_REGS"):
                    m.d.slow += [
                        rs1.eq(regs[rs1_id]),
                        rs2.eq(regs[rs2_id])
                    ]
                    m.next = "EXECUTE"
                with m.State("EXECUTE"):
                    m.d.slow += pc.eq(pc + 1)
                    m.next = "FETCH_INSTR"

        # Assign important signals to LEDS
        # Note: fsm.state is only accessible outside of the FSM context
        m.d.comb += self.leds.eq(Mux(is_system, 31, (1 << fsm.state)))

        # Register write back
        write_back_data = alu_out
        write_back_en = fsm.ongoing("EXECUTE") & (is_alu_reg | is_alu_imm)

        if platform is None:
            with m.If(write_back_en & (rd_id != 0)):
                m.d.sync += regs[rd_id].eq(write_back_data)
        else:
            with m.If(write_back_en & (rd_id != 0)):
                m.d.slow += regs[rd_id].eq(write_back_data)

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
            export(is_load, "is_load")
            export(is_store, "is_store")
            export(is_system, "is_system")
            export(rd_id, "rd_id")
            export(rs1_id, "rs1_id")
            export(rs2_id, "rs2_id")
            export(i_imm, "i_imm")
            export(funct3, "funct3")
            export(rd_id, "rd_id")
            export(rs1, "rs1")
            export(rs2, "rs2")
            export(write_back_data, "write_back_data")
            export(write_back_en, "write_back_en")
            export(alu_out, "alu_out")
            export((1 << fsm.state), "state")

        return m
