
""" This module provides the system on chip (SOC) implementation
    for the register bank """

from clockworks import Clockworks
from amaranth import Module, Signal, Array, Mux, Cat, Const, C, ClockSignal
from amaranth.lib import wiring
from amaranth.lib.wiring import Out


class SOC(wiring.Component):

    """ this class describes the SOC registger bank """

    leds: Out(5)

    def __init__(self):

        # Signals in this list can easily be plotted as vcd traces
        self.ports = []

        self.cw = []

        super().__init__()

    def elaborate(self, platform):

        """ The clockwork provides a new clock domain called 'slow'.
            we replace the default sync domain with the new one to have the
            counter run slower unless we are simulating.  This is required
            as the leds blink too quickly to tell if they are working
            otherwise. """

        m = Module()

        if platform is None:
            self.cw = Clockworks()
            m.submodules.cw = self.cw

        # Instruction sequence to be executed
        sequence = [
                #       24      16       8       0
                # .......|.......|.......|.......|
                #R         rs2  rs1 f3   rd     op
                #I         imm  rs1 f3   rd     op
                #S    imm  rs2  rs1 f3  imm     op
                # ......|....|....|..|....|......|
                0b00000000000000000000000000110011,  # R add  x0, x0, x0
                0b00000000000000000000000010110011,  # R add  x1, x0, x0
                0b00000000000100001000000010010011,  # I addi x1, x1,  1
                0b00000000000100001000000010010011,  # I addi x1, x1,  1
                0b00000000000100001000000010010011,  # I addi x1, x1,  1
                0b00000000000100001000000010010011,  # I addi x1, x1,  1
                0b00000000000000001010000100000011,  # I lw   x2, 0(x1)
                0b00000000000100010010000000100011,  # S sw   x2, 0(x1)
                0b00000000000100000000000001110011   # S ebreak
        ]

        # Program counter
        pc = Signal(32)

        # Current instruction
        instr = Signal(32, init=0b0110011)

        # Instruction memory initialised with above 'sequence'
        mem = Array([Signal(32, init=x) for x in sequence])

        # Register bank
        regs = Array([Signal(32) for x in range(32)])
        rs1 = Signal(32)
        rs2 = Signal(32)

        write_back_data = C(0)
        write_back_en = C(0)

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

        # Data write back
        with m.If(write_back_en & (rd_id != 0)):
            if platform is None:
                m.d.sync += regs[rd_id].eq(write_back_data)
            else:
                m.d.slow += regs[rd_id].eq(write_back_data)

        # Main finite state machine (FSM)
        with m.FSM(reset="FETCH_INSTR", domain="slow") as fsm:
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

        # Assign important signals to LEDS
        # Note: fsm.state is only accessible outside of the FSM context
        m.d.comb += self.leds.eq(Mux(is_system, 31, (1 << fsm.state)))

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
            export(ClockSignal("slow"), "slow_clk")
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

        return m
