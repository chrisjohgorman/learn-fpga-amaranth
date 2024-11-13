""" First iteration of separation of the system on chip into three modules.
    This module is the CPU. """

from amaranth import Module, Signal, Array, Mux, Cat, Const, Elaboratable


class CPU(Elaboratable):

    """ This class describes the central processing unit (CPU) of our
        system on chip (SOC). """

    def __init__(self):
        self.mem_addr = Signal(32)
        self.mem_rstrb = Signal()
        self.mem_rdata = Signal(32)
        self.x1 = Signal(32)

        # Signals in this list can easily be plotted as vcd traces
        self.ports = []

        # Initialize instance variables being used by this module
        self.fsm = None
        self.pc = None
        self.instr = None
        self.rd_id = None
        self.rs1_id = None
        self.rs2_id = None
        self.funct3 = None
        self.i_imm = None
        self.write_back_data = None
        self.is_alu_reg = None
        self.is_alu_imm = None
        self.is_branch = None
        self.is_load = None
        self.is_store = None
        self.is_system = None

    def elaborate(self, platform):

        """ The CPU module has a mem_addr signal as output, a mem_rdata
            signal as input and a mem_rstrb signal as output.  There is a x1
            signal that contains the contents of register x1 that will be
            plugged into the LEDs for visual debugging.  Also we have added an
            extra state to the finite state machine. As with the memory
            we have a conditional execution of the finite state machine and
            the write_back_data.  If we are simulating, we use the sync domain
            and if we're writing to the FPGA we use the slow domain. """

        m = Module()

        # Program counter
        pc = Signal(32)
        self.pc = pc

        # Current instruction
        instr = Signal(32, init=0b0110011)
        self.instr = instr

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
        self.is_alu_reg = is_alu_reg
        self.is_alu_imm = is_alu_imm
        self.is_branch = is_branch
        self.is_load = is_load
        self.is_store = is_store
        self.is_system = is_system

        # Immediate format decoder
        u_imm = Cat(Const(0).replicate(12), instr[12:32])
        i_imm = Cat(instr[20:31], instr[31].replicate(21))
        s_imm = Cat(instr[7:12], instr[25:31], instr[31].replicate(21))
        b_imm = Cat(0, instr[8:12], instr[25:31], instr[7],
                    instr[31].replicate(20))
        j_imm = Cat(0, instr[21:31], instr[20], instr[12:20],
                    instr[31].replicate(12))
        self.i_imm = i_imm

        # Register addresses decoder
        rs1_id = instr[15:20]
        rs2_id = instr[20:25]
        rd_id = instr[7:12]

        self.rd_id = rd_id
        self.rs1_id = rs1_id
        self.rs2_id = rs2_id

        # Function code decoder
        funct3 = instr[12:15]
        funct7 = instr[25:32]
        self.funct3 = funct3

        # ALU
        alu_in1 = rs1
        alu_in2 = Mux(is_alu_reg, rs2, i_imm)
        shamt = Mux(is_alu_reg, rs2[0:5], instr[20:25])

        # Wire memory address to pc
        m.d.comb += self.mem_addr.eq(pc)

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

        # Next program counter is either next instruction or depends on
        # jump target
        next_pc = Mux((is_branch & take_branch), pc + b_imm,
                      Mux(is_jal, pc + j_imm,
                      Mux(is_jalr, rs1 + i_imm, pc + 4)))

        # Main state machine
        if platform is None:
            with m.FSM(reset="FETCH_INSTR") as fsm:
                self.fsm = fsm
                m.d.comb += self.mem_rstrb.eq(fsm.ongoing("FETCH_INSTR"))
                with m.State("FETCH_INSTR"):
                    m.next = "WAIT_INSTR"
                with m.State("WAIT_INSTR"):
                    m.d.sync += instr.eq(self.mem_rdata)
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
            with m.FSM(reset="FETCH_INSTR") as fsm:
                self.fsm = fsm
                m.d.comb += self.mem_rstrb.eq(fsm.ongoing("FETCH_INSTR"))
                with m.State("FETCH_INSTR"):
                    m.next = "WAIT_INSTR"
                with m.State("WAIT_INSTR"):
                    m.d.slow += instr.eq(self.mem_rdata)
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

        self.write_back_data = write_back_data

        if platform is None:
            with m.If(write_back_en & (rd_id != 0)):
                m.d.sync += regs[rd_id].eq(write_back_data)
                # Also assign to debug output to see what is happening
                m.d.sync += self.x1.eq(write_back_data)
        else:
            with m.If(write_back_en & (rd_id != 0)):
                m.d.slow += regs[rd_id].eq(write_back_data)
                # Also assign to debug output to see what is happening
                m.d.slow += self.x1.eq(write_back_data)

        return m
