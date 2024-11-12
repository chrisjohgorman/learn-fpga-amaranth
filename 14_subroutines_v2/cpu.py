from amaranth import Module, Signal, Array, Mux, Cat, Const, Elaboratable, C


class CPU(Elaboratable):

    def __init__(self):
        self.mem_addr = Signal(32)
        self.mem_rstrb = Signal()
        self.mem_rdata = Signal(32)
        self.x10 = Signal(32)

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
        is_alu_reg = Signal()
        is_alu_imm = Signal()
        is_branch = Signal()
        is_jalr = Signal()
        is_jal = Signal()
        is_auipc = Signal()
        is_lui = Signal()
        is_load = Signal()
        is_store = Signal()
        is_system = Signal()
        m.d.comb += [
            is_alu_reg.eq(instr[0:7] == 0b0110011),
            is_alu_imm.eq(instr[0:7] == 0b0010011),
            is_branch.eq(instr[0:7] == 0b1100011),
            is_jalr.eq(instr[0:7] == 0b1100111),
            is_jal.eq(instr[0:7] == 0b1101111),
            is_auipc.eq(instr[0:7] == 0b0010111),
            is_lui.eq(instr[0:7] == 0b0110111),
            is_load.eq(instr[0:7] == 0b0000011),
            is_store.eq(instr[0:7] == 0b0100011),
            is_system.eq(instr[0:7] == 0b1110011)
        ]
        self.is_alu_reg = is_alu_reg
        self.is_alu_imm = is_alu_imm
        self.is_branch = is_branch
        self.is_load = is_load
        self.is_store = is_store
        self.is_system = is_system

        def extend(x, n):
            return [x for i in range(n + 1)]

        # Immediate format decoder
        u_imm = Cat(Const(0, 12), instr[12:32])
        i_imm = Cat(instr[20:31], *extend(instr[31], 21))
        s_imm = Cat(instr[7:12], instr[25:31], *extend(instr[31], 21))
        b_imm = Cat(0, instr[8:12], instr[25:31], instr[7],
                    *extend(instr[31], 20))
        j_imm = Cat(0, instr[21:31], instr[20], instr[12:20],
                    *extend(instr[31], 12))
        self.i_imm = i_imm

        # Register addresses decoder
        rs1_id = instr[15:20]
        rs2_id = instr[20:25]
        rd_id = instr[7:12]

        self.rd_id = rd_id
        self.rs1_id = rs1_id
        self.rs2_id = rs2_id

        # Function code decdore
        funct3 = instr[12:15]
        funct7 = instr[25:32]
        self.funct3 = funct3

        # ALU
        alu_in1 = Signal.like(rs1)
        alu_in2 = Signal.like(rs2)
        shamt = Signal(5)
        alu_minus = Signal(33)
        alu_plus = Signal.like(alu_in1)

        m.d.comb += [
            alu_in1.eq(rs1),
            alu_in2.eq(Mux((is_alu_reg | is_branch), rs2, i_imm)),
            shamt.eq(Mux(is_alu_reg, rs2[0:5], instr[20:25]))
        ]

        # Wire memory address to pc
        m.d.comb += self.mem_addr.eq(pc)

        m.d.comb += [
            alu_minus.eq(Cat(~alu_in1, C(0, 1)) + Cat(alu_in2, C(0, 1)) + 1),
            alu_plus.eq(alu_in1 + alu_in2)
        ]

        eq = alu_minus[0:32] == 0
        ltu = alu_minus[32]
        lt = Mux((alu_in1[31] ^ alu_in2[31]), alu_in1[31], alu_minus[32])

        def flip32(x):
            a = [x[i] for i in range(0, 32)]
            return Cat(*reversed(a))

        # TODO: check these again!
        shifter_in = Mux(funct3 == 0b001, flip32(alu_in1), alu_in1)
        shifter = Cat(shifter_in, (instr[30] & alu_in1[31])) >> alu_in2[0:5]
        leftshift = flip32(shifter)

        with m.Switch(funct3) as _:
            with m.Case(0b000):
                m.d.comb += alu_out.eq(Mux(funct7[5] & instr[5],
                                           alu_minus[0:32], alu_plus))
            with m.Case(0b001):
                m.d.comb += alu_out.eq(leftshift)
            with m.Case(0b010):
                m.d.comb += alu_out.eq(lt)
            with m.Case(0b011):
                m.d.comb += alu_out.eq(ltu)
            with m.Case(0b100):
                m.d.comb += alu_out.eq(alu_in1 ^ alu_in2)
            with m.Case(0b101):
                m.d.comb += alu_out.eq(shifter)
            with m.Case(0b110):
                m.d.comb += alu_out.eq(alu_in1 | alu_in2)
            with m.Case(0b111):
                m.d.comb += alu_out.eq(alu_in1 & alu_in2)

        with m.Switch(funct3) as _:
            with m.Case(0b000):
                m.d.comb += take_branch.eq(eq)
            with m.Case(0b001):
                m.d.comb += take_branch.eq(~eq)
            with m.Case(0b100):
                m.d.comb += take_branch.eq(lt)
            with m.Case(0b101):
                m.d.comb += take_branch.eq(~lt)
            with m.Case(0b110):
                m.d.comb += take_branch.eq(ltu)
            with m.Case(0b111):
                m.d.comb += take_branch.eq(~ltu)
            with m.Case("---"):
                m.d.comb += take_branch.eq(0)

        # Next program counter is either next instruction or depends on
        # jump target
        pc_plus_imm = pc + Mux(instr[3], j_imm[0:32],
                               Mux(instr[4], u_imm[0:32], b_imm[0:32]))
        pc_plus4 = pc + 4

        next_pc = Mux(((is_branch & take_branch) | is_jal), pc_plus_imm,
                      Mux(is_jalr, Cat(C(0, 1), alu_plus[1:32]), pc_plus4))

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
                    with m.If(~is_system):
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
                    with m.If(~is_system):
                        m.d.slow += pc.eq(next_pc)
                    m.next = "FETCH_INSTR"

        # Register write back
        write_back_data = Mux((is_jal | is_jalr), pc_plus4,
                              Mux(is_lui, u_imm,
                                  Mux(is_auipc, pc_plus_imm, alu_out)))

        write_back_en = fsm.ongoing("EXECUTE") & ~is_branch & ~is_store

        self.write_back_data = write_back_data

        if platform is None:
            with m.If(write_back_en & (rd_id != 0)):
                m.d.sync += regs[rd_id].eq(write_back_data)
                # Also assign to debug output to see what is happening
                with m.If(rd_id == 10):
                    m.d.sync += self.x10.eq(write_back_data)
        else:
            with m.If(write_back_en & (rd_id != 0)):
                m.d.slow += regs[rd_id].eq(write_back_data)
                # Also assign to debug output to see what is happening
                with m.If(rd_id == 10):
                    m.d.slow += self.x10.eq(write_back_data)

        return m
