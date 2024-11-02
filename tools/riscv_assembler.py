#!/usr/bin/env python3

""" module docstring """

import re
import sys

# instructions

RInstructions = [
    ("ADD",  0b000, 0b0000000),
    ("SUB",  0b000, 0b0100000),
    ("SLL",  0b001, 0b0000000),
    ("SLT",  0b010, 0b0000000),
    ("SLTU", 0b011, 0b0000000),
    ("XOR",  0b100, 0b0000000),
    ("SRL",  0b101, 0b0000000),
    ("SRA",  0b101, 0b0100000),
    ("OR",   0b110, 0b0000000),
    ("AND",  0b111, 0b0000000)
]
ROps = [x[0] for x in RInstructions]

IInstructions = [
    ("ADDI",  0b000),
    ("SLTI",  0b010),
    ("SLTIU", 0b011),
    ("XORI",  0b100),
    ("ORI",   0b110),
    ("ANDI",  0b111)
]
IOps = [x[0] for x in IInstructions]

IRInstructions = [
    ("SLLI", 0b001, 0b0000000),
    ("SRLI", 0b101, 0b0000000),
    ("SRAI", 0b101, 0b0100000)
]
IROps = [x[0] for x in IRInstructions]

JInstructions = [
    ("JAL",  0b1101111),
    ("JALR", 0b1100111, 0b000)
]
JOps = [x[0] for x in JInstructions]

BInstructions = [
    ("BEQ",  0b000),
    ("BNE",  0b001),
    ("BLT",  0b100),
    ("BGE",  0b101),
    ("BLTU", 0b110),
    ("BGEU", 0b111)
]
BOps = [x[0] for x in BInstructions]

UInstructions = [
    ("LUI",   0b0110111),
    ("AUIPC", 0b0010111)
]
UOps = [x[0] for x in UInstructions]

LInstructions = [
    ("LB",  0b000),
    ("LH",  0b001),
    ("LW",  0b010),
    ("LBU", 0b100),
    ("LHU", 0b101)
]
LOps = [x[0] for x in LInstructions]

SInstructions = [
    ("SB",  0b000),
    ("SH",  0b001),
    ("SW",  0b010)
]
SOps = [x[0] for x in SInstructions]

SysInstructions = [
    ("FENCE",),
    ("FENCE_I",),
    ("ECALL",),
    ("EBREAK",),
    ("CSRRW",),
    ("CSRRS",),
    ("CSRRWI",),
    ("CSRRSI",),
    ("CSRRCI",)
]
SysOps = [x[0] for x in SysInstructions]

PseudoInstructions = [
    ("LI",),
    ("CALL",),
    ("RET",),
    ("MV",),
    ("NOP",),
    ("J",),
    ("BEQZ",),
    ("BNEZ",),
    ("BGT",),
]
PseudoOps = [x[0] for x in PseudoInstructions]

MemInstructions = [
    ("DATAW",),
    ("DATAB",),
]
MemOps = [x[0] for x in MemInstructions]

DebugInstructions = [
    ("TRACE",),
]
DebugOps = [x[0] for x in DebugInstructions]


class LabelRef():

    """ LabelRef class docstring """

    def __init__(self, op, name, arg):
        self.op = op
        self.name = name
        self.arg = arg

    def __repr__(self):
        text = f"LABELREF({self.op:4} {self.name} {self.arg})"
        return text

    @classmethod
    def from_string(cls, string):

        """ from_string function docstring """

        r = re.compile('[ ()]+')
        args = r.split(string)
        op = args[1]
        name = args[2]
        arg = args[3]
        # print(args)
        return cls(op, name, arg)


class Instruction():

    """ Instruction class docstring """

    def __init__(self, op, *args):
        self.op = op
        self.args = args

    def __repr__(self):
        text = "("
        for arg in self.args:
            text += f"{arg:2}"
            if arg is not self.args[-1]:
                text += ", "
        text += ")"
        return f"({self.op:4} {text})"


abi_names = {
    'zero': 0,
    'ra'  : 1,
    'sp'  : 2,
    'gp'  : 3,
    'tp'  : 4,
    't0'  : 5,
    't1'  : 6,
    't2'  : 7,
    'fp'  : 8,
    's0'  : 8,
    's1'  : 9,
    'a0'  : 10,
    'a1'  : 11,
    'a2'  : 12,
    'a3'  : 13,
    'a4'  : 14,
    'a5'  : 15,
    'a6'  : 16,
    'a7'  : 17,
    's2'  : 18,
    's3'  : 19,
    's4'  : 20,
    's5'  : 21,
    's6'  : 22,
    's7'  : 23,
    's8'  : 24,
    's9'  : 25,
    's10' : 26,
    's11' : 27,
    't3'  : 28,
    't4'  : 29,
    't5'  : 30,
    't6'  : 31
}


def reg2int(arg):

    """ reg2int function docstring """

    if len(arg) == 0:
        return None
    if arg.lower() in abi_names:
        return abi_names[arg.lower()]
    if arg[0].upper() == "X":
        return int(arg[1:])
    print(f"Unknown register '{arg}'")
    sys.exit(-1)


class RiscvAssembler():

    """ RiscvAssembler class docstring """

    def __init__(self, simulation=False):
        self.pc = 0
        self.labels = {}
        self.constants = {}
        self.pseudos = {}
        self.instructions = []
        self.mem = []
        self.debug_args = []
        self.simulation = simulation

        print("Simulation = ", "OFF" if simulation is False else "ON")

    def assemble(self):

        """ assemble function docstring """

        for inst in self.instructions:
            self.mem.append(self.encode(inst))

    def encode_r(self, f7, rs2, rs1, f3, rd, op):

        """ encode_r function docstring """

        return ((f7 << 25) | (rs2 << 20) | (rs1 << 15)
                | (f3 << 12) | (rd << 7) | op)

    def encode_i(self, imm, rs, f3, rd, op):

        """ encode_i function docstring """

        return ((imm & 0xfff) << 20) | (rs << 15) | (f3 << 12) | (rd << 7) | op

    def encode_j(self, imm, rd, op):

        """ encode_j function docstring """

        imm31 = (imm >> 20) & 1
        imm21 = (imm >> 1) & 0x3ff
        imm20 = (imm >> 11) & 1
        imm12 = (imm >> 12) & 0xff
        return ((imm31 << 31) | (imm21 << 21) | (imm20 << 20)
                | (imm12 << 12) | (rd << 7) | op)

    def encode_b(self, imm, rs2, rs1, f3, op):

        """ encode_j function docstring """

        imm31 = (imm >> 12) & 1
        imm25 = (imm >> 5) & 0x3f
        imm8 =  (imm >> 1) & 0xf
        imm7 =  (imm >> 11) & 1
        return ((imm31 << 31) | (imm25 << 25) | (rs2 << 20) | (rs1 << 15)
                | (f3 << 12) | (imm8 << 8) | (imm7 << 7) | op)

    def encode_u(self, imm, rd, op):

        """ encode_u function docstring """

        return (imm & 0xfffff000) | (rd << 7) | op

    def encode_s(self, imm, rs2, rs1, f3, op):

        """ encode_s function docstring """

        imm25 = (imm >> 5) & 0x7f
        imm7  = imm & 0x1f
        return ((imm25 << 25) | (rs2 << 20) | (rs1 << 15)
                | (f3 << 12) | (imm7 << 7) | op)

    def encode_r_ops(self, instruction):

        """ encode_r_ops function docstring """

        rd, rs1, rs2 = [reg2int(x) for x in instruction.args]
        _, f3, f7 = [x for x in RInstructions if x[0] == instruction.op][0]
        return self.encode_r(f7, rs2, rs1, f3, rd, 0b0110011)

    def encode_i_ops(self, instruction):

        """ encode_i_ops function docstring """

        rd, rs = reg2int(instruction.args[0]), reg2int(instruction.args[1])
        imm = self.imm2int(instruction.args[2])
        _, f3 = [x for x in IInstructions if x[0] == instruction.op][0]
        return self.encode_i(imm, rs, f3, rd, 0b0010011)

    def encode_ir_ops(self, instruction):

        """ encode_ir_ops function docstring """

        rd, rs = reg2int(instruction.args[0]), reg2int(instruction.args[1])
        imm = self.imm2int(instruction.args[2])
        _, f3, f7 = [x for x in IRInstructions if x[0] == instruction.op][0]
        return self.encode_r(f7, imm, rs, f3, rd, 0b0010011)

    def encode_j_ops(self, instruction):

        """ encode_j_ops function docstring """

        if instruction.op == "JAL":
            rd = reg2int(instruction.args[0])
            imm = self.imm2int(instruction.args[1])
            _, _op = [x for x in JInstructions if x[0] == instruction.op][0]
            return self.encode_j(imm, rd, 0b1101111)
        if instruction.op == "JALR":
            rd, rs = reg2int(instruction.args[0]), reg2int(instruction.args[1])
            imm = self.imm2int(instruction.args[2])
            _, _op, f3 = [x for x in JInstructions if x[0] == instruction.op][0]
            return self.encode_i(imm, rs, f3, rd, 0b1100111)
        return None

    def encode_b_ops(self, instruction):

        """ encode_b_ops function docstring """

        rs1, rs2 = reg2int(instruction.args[0]), reg2int(instruction.args[1])
        imm = self.imm2int(instruction.args[2])
        _, f3 = [x for x in BInstructions if x[0] == instruction.op][0]
        return self.encode_b(imm, rs2, rs1, f3, 0b1100011)

    def encode_u_ops(self, instruction):

        """ encode_u_ops function docstring """

        rd = reg2int(instruction.args[0])
        imm = self.imm2int(instruction.args[1])
        _, op = [x for x in UInstructions if x[0] == instruction.op][0]
        return self.encode_u(imm, rd, op)

    def encode_lops(self, instruction):

        """ encode_lops function docstring """

        rd, rs = reg2int(instruction.args[0]), reg2int(instruction.args[1])
        imm = self.imm2int(instruction.args[2])
        _, f3 = [x for x in LInstructions if x[0] == instruction.op][0]
        return self.encode_i(imm, rs, f3, rd, 0b0000011)

    def encode_s_ops(self, instruction):

        """ encode_s_ops function docstring """

        # Swapped rs2, rs1 to match assembly code
        rs2, rs1 = reg2int(instruction.args[0]), reg2int(instruction.args[1])
        imm = self.imm2int(instruction.args[2])
        _, f3 = [x for x in SInstructions if x[0] == instruction.op][0]
        return self.encode_s(imm, rs2, rs1, f3, 0b0100011)

    def encode_sys_ops(self, instruction):

        """ encode_sys_ops function docstring """

        op = instruction.op
        if op == "FENCE":
            return 0b00000000000000000000000001110011
        if op == "FENCE_I":
            return 0b00000000000000000001000001110011
        if op == "ECALL":
            return 0b00000000000000000000000001110011
        if op == "EBREAK":
            return 0b00000000000100000000000001110011
        print(f"Unhandled system op {op}")
        return None

    def encode_mem_ops(self, instruction):

        """ encode_mem_ops function docstring """

        op = instruction.op
        if op == "DATAW":
            w = int(instruction.args[0])
            return w
        if op == "DATAB":
            b1 = int(instruction.args[0]) & 0xff
            b2 = int(instruction.args[1]) & 0xff
            b3 = int(instruction.args[2]) & 0xff
            b4 = int(instruction.args[3]) & 0xff
            return (b4 << 24) | (b3 << 16) | (b2 << 8) | b1
        return None

    def encode_debug_ops(self, instruction):

        """ encode_debug_ops function docstring """

        op = instruction.op
        self.debug_args.append(instruction.args)
        index = len(self.debug_args) - 1
        if op == "TRACE":
            return (index << 24) | 0b11110011
        return None

    def unravel_pseudo_ops(self, instruction):

        """ encode_pseudo_ops function docstring """

        op = instruction.op
        instr = []
        if op == "NOP":
            instr.append(self.i_from_line("ADD x0, x0, x0"))
        elif op == "LI":
            rd = instruction.args[0]
            imm = self.imm2int(instruction.args[1])
            if imm == 0:
                instr.append(self.i_from_line(f"ADD {rd}, zero, zero"))
            elif -2048 <= imm < 2048:
                instr.append(self.i_from_line(f"ADDI {rd}, zero, {imm}"))
            else:
                imm2 = hex(imm + ((imm & 0x800) << 1))
                imm12 = hex(imm & 0xfff)
                instr.append(self.i_from_line(f"LUI {rd}, {imm2}"))
                if imm12 != 0:
                    instr.append(self.i_from_line(f"ADDI {rd}, {rd}, {imm12}"))
        elif op == "CALL":
            ref1 = LabelRef(op, "offset", instruction.args[0])
            ref2 = LabelRef(op, "offset12", instruction.args[0])
            instr.append(self.i_from_line(f"AUIPC x6, {ref1}"))
            instr.append(self.i_from_line(f"JALR  x1, x6, {ref2}"))
        elif op == "RET":
            instr.append(self.i_from_line("JALR  x0, x1, 0"))
        elif op == "MV":
            rd = instruction.args[0]
            rs1 = instruction.args[1]
            instr.append(self.i_from_line(f"ADD   {rd}, {rs1}, zero"))
        elif op == "J":
            ref = LabelRef(op, "imm", instruction.args[0])
            instr.append(self.i_from_line(f"JAL   zero, {ref}"))
        elif op == "BEQZ":
            rs1 = instruction.args[0]
            ref = LabelRef(op, "imm", instruction.args[1])
            instr.append(self.i_from_line(f"BEQ   {rs1}, x0, {ref}"))
        elif op == "BNEZ":
            rs1 = instruction.args[0]
            ref = LabelRef(op, "imm", instruction.args[1])
            instr.append(self.i_from_line(f"BNE   {rs1}, x0, {ref}"))
        elif op == "BGT":
            rs1 = instruction.args[0]
            rs2 = instruction.args[1]
            ref = LabelRef(op, "imm", instruction.args[2])
            instr.append(self.i_from_line(f"BLT   {rs2}, {rs1}, {ref}"))
        else:
            return [instruction], False
        return instr, True

    def encode(self, instruction):

        """ encode function docstring """

        encoded = 0
        if instruction.op in ROps:
            encoded = self.encode_r_ops(instruction)
        elif instruction.op in IOps:
            encoded = self.encode_i_ops(instruction)
        elif instruction.op in IROps:
            encoded = self.encode_ir_ops(instruction)
        elif instruction.op in JOps:
            encoded = self.encode_j_ops(instruction)
        elif instruction.op in BOps:
            encoded = self.encode_b_ops(instruction)
        elif instruction.op in UOps:
            encoded = self.encode_u_ops(instruction)
        elif instruction.op in LOps:
            encoded = self.encode_lops(instruction)
        elif instruction.op in SOps:
            encoded = self.encode_s_ops(instruction)
        elif instruction.op in SysOps:
            encoded = self.encode_sys_ops(instruction)
        elif instruction.op in MemOps:
            encoded = self.encode_mem_ops(instruction)
        elif instruction.op in DebugOps:
            encoded = self.encode_debug_ops(instruction)
        else:
            print(f"Unhandled instruction / opcode {instruction}")
            sys.exit(1)
        # TODO remove once assured that I have not broken this using .items()
        # for label in self.labels:
        #     if self.labels[label] == self.pc:
        #         print(f"  lab@pc=0x{self.pc:03x}={self.pc} -> {label}")
        for label, item in self.labels.items():
            if item == self.pc:
                print(f"  lab@pc=0x{item:03x}={item} -> {label}")
        if self.pc in self.pseudos:
            print(f"  psu@pc=0x{self.pc:03x}={self.pc} -> "
                  f"{self.pseudos[self.pc]}")
        print(f"  enc@pc=0x{self.pc:03x} {instruction} -> 0b{encoded:>032b}")
        self.pc += 4
        return encoded

    def i_from_line(self, line):

        """ i_from_line function docstring """

        line = line.strip()
        if len(line) == 0:
            return None
        if ' ' not in line:
            return Instruction(line)
        op, rest = [x.strip() for x in (
            line.split(' ', maxsplit=1))]
        # print("op = {}, rest = {}".format(op, rest))
        items = [x.strip() for x in rest.split(',')]
        return Instruction(op, *items)

    def read(self, text):

        """ read function docstring """

        instructions = []
        for line in text.splitlines():
            line = line.strip()
            i = None
            # Quoted characters
            if "TRACE" in line:
                if self.simulation is False:
                    continue
            if '"' in line:
                n = line.count('"')
                if n % 2 != 0:
                    print("Not an even number of quotes. Check code.")
                    sys.exit(1)
                # Replace double-quoted characters with their ascii value
                line = re.sub('"(.)"', lambda m: str(ord(m.group(1))), line)
            # Strip comments
            if ';' in line:
                line = line.split(';', maxsplit=1)[0]
            # Constants
            if 'equ' in line:
                items = [x.strip() for x in line.split()]
                name = items[0]
                value = "".join(items[2:])
                self.constants[name.upper()] = int(value)
                print(f"found equ '{name}', value = '{value}'")
                continue
            # Labels
            if ':' in line:
                label, line = [x.strip() for x in line.split(':', maxsplit=1)]
                pc = len(instructions) * 4
                self.labels[label.upper()] = pc
                print(f"found label '{label}', pc = {pc}")
            i = self.i_from_line(line)
            if i is not None:
                unravelled, is_pseudo = self.unravel_pseudo_ops(i)
                if is_pseudo:
                    pc = len(instructions) * 4
                    self.pseudos[pc] = i.op
                    print(f"found peudo '{i.op}', pc = {pc}")
                for u in unravelled:
                    instructions.append(u)
        self.instructions += instructions

    def imm2int(self, arg):

        """ imm2int function docstring """

        upp = arg.upper()
        if len(arg) == 0:
            return None
        if upp in self.constants:
            value = self.constants[upp]
            return value
        if upp in self.labels:
            offset = self.labels[upp] - self.pc
            # print("label offset = {}".format(offset))
            return offset
        if upp.startswith("LABELREF"):
            print("  found labelref")
            label = LabelRef.from_string(upp)
            if label.op == "CALL":
                offset = self.imm2int(label.arg)
                print(f"    resolving label {label.arg} -> {offset}")
                # print("offset = {}".format(offset))
                if label.name == "OFFSET":
                    return offset
                if label.name == "OFFSET12":
                    return (offset + 4) & 0xfff
            elif (label.op in ["J", "BEQZ", "BNEZ", "BGT"]):
                if label.name == "IMM":
                    imm = self.imm2int(label.arg)
                    print(f"    resolving label {label.arg} -> {imm}")
                    return imm
        if arg.startswith('"'):
            if arg.endswith('"'):
                if len(arg) == 3:
                    try:
                        return ord(arg[1])
                    except Exception as exc:
                        raise ValueError(f"Expected char, but got "
                                         f"{arg}") from exc
                else:
                    raise ValueError(f"Expected quoted char, but got {arg}")
            else:
                raise ValueError(f"Strange argument: {arg}")
        try:
            return int(arg)
        except ValueError as e:
            if 'B' in upp[1]:
                return int(arg, 2)
            if 'X' in upp:
                if "0X" == upp[0:2] or "-0X" == upp[0:3]:
                    return int(arg, 16)
            else:
                raise ValueError(f"Can't parse arg {arg}") from e
        return None

    def test_code(self):

        """ function test_code docstring """

        return """begin:
            slow_bit equ 3

           step4:
           ADD   x0, x0, x0
           ADD   x1, x0, x0
           ADDI  x1, x1,  1
           ADDI  x1, x1,  1
           ADDI  x1, x1,  1
           ADDI  x1, x1,  1
           LW    x2, x1,  0
           SW    x2, x1,  0
           test_sub:
           LI   a0, 100
           LI   a1, 50
           SUB  a2, a0, a1  ; 50
           LI   a0, 50
           LI   a1, 100     ; -50
           SUB  a3, a0, a1
           LI   a0, -50
           LI   a1, 100
           SUB  a4, a0, a1  ; -150
           LI   a0, 50
           LI   a1, -100
           SUB  a5, a0, a1  ; 150
           LI   a0, -50
           LI   a1, -100
           SUB  a6, a0, a1
           LI   a0, -100
           LI   a1, 50
           SUB  a7, a0, a1
           LI   a0, 100
           LI   a1, -50
           SUB  s2, a0, a1
           LI   a0, -100
           LI   a1, -50
           SUB  s3, a0, a1
           ; TRACE a0, a1, s3 ; does not work yet
           CALL wait
           test_shift:
           LI   a1, 100
           SLLI a2, a1, 2
           SRLI a3, a1, 2
           SRAI a4, a1, 2
           LI   a1, -100
           SLLI a5, a1, 2
           SRLI a6, a1, 2
           SRAI a7, a1, 2
           CALL wait
           test_mul:
           LI   a0, 5120
           LI   a1, 5120
           LI   a4, 25600
           CALL mulsi3
           SRLI a2, a0, 10
           NOP
           LI   a0, -5120
           LI   a1, 5120
           LI   a4, -25600
           CALL mulsi3
           SRAI a2, a0, 10
           NOP
           CALL wait
           test_gt:
           LI   a0, 32
           LI   a1, 64
           BGT  a1, a0, gt_ok
           LI   a0, 0xdead
           LI   a1, 0xdead
           gt_ok:
           NOP
           CALL wait
           test_lt:
           LI   a0, 64
           LI   a1, 32
           BLT  a1, a0, lt_ok
           LI   a0, 0xdead
           LI   a1, 0xdead
           lt_ok:
           NOP
           CALL wait
           start:
           EBREAK
           ADD x3, x2, x1
           ADDI  x1, x0,  4
           ADDI  ra, zero,  4
           AND   x2, x1, x0
           SUB   x4, x1, x0
           SRAI  x4, x1,  3
           jumps:
           JAL   x4, 255
           JALR  x5, x7,  start
           JALR  x5, x7,  future
           branches:
           BEQ   x3, x4,  1
           BNE   x3, x4,  1
           BLT   x3, x4,  1
           BGE   x3, x4,  1
           BLTU  x3, x4,  1
           BGEU  x3, x4,  1
           future:
           luiandauipc:
           lui: LUI   x5,  0x30000
           AUIPC x5,  0x30000
           load:
           LB    x7, x10, 0xaa
           LH    x7, x10, 0xab
           LW    x7, x10, 0xac
           LBU   x7, x10, 0xad
           LHU   x7, x10, 0xae
           finish:
           store:
           SB    x7, x10, 1
           SH    x7, x10, 2
           SW    x7, x10, 3
           before_li:
           LI    x3, 400
           after_li:
           LI    a1, 0
           LI    a2, 128
           LI    a3, 4000
           LI    a4, 0x2000
           test_other_pseudos:
           CALL  load
           CALL  futurelabel
           RET
           test_mv:
           MV    x2, x3
           NOP
           J     after_li
           BEQZ  a2, store
           BNEZ  a1, store
           BGT   a3, a2, store
           futurelabel:
           NOP
           EBREAK

            mulsi3:                 ; integer multiplication
            MV      a2, a0
            LI      a0, 0
            mulsi3_l0:
            ANDI    a3, a1, 1
            BEQZ    a3, mulsi3_l1
            ADD     a0, a0, a2
            mulsi3_l1:
            SRLI    a1, a1, 1
            SLLI    a2, a2, 1
            BNEZ    a1, mulsi3_l0
            RET

            wait:
            LI      t0, 1
            SLLI    t0, t0, slow_bit
            wait_loop:
            ADDI    t0, t0, -1
            BNEZ    t0, wait_loop
            RET

    """


if __name__ == "__main__":
    a = RiscvAssembler(simulation=True)
    a.read(a.test_code())
    print(a.instructions)
    a.assemble()
