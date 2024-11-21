#!/usr/bin/env python3

""" This module uses the riscv-assembly module to improve the readability
    of the code used in the arithmetic logic unit (ALU). """

from soc import SOC
from amaranth.sim import Simulator, Period

soc = SOC()


async def testbench(ctx):

    """ Testbench function to test values from the central processing unit
        using the riscv-assembly file. """

    cpu = soc.cpu
    while True:
        state = ctx.get(soc.cpu.fsm.state)
        if state == 2:
            print("-- NEW CYCLE -----------------------")
            print(f"  F: LEDS = {ctx.get(soc.leds):>05b}")
            print(f"  F: pc={ctx.get(cpu.pc)}")
            print(f"  F: instr={ctx.get(cpu.instr):>032b}")
            if ctx.get(cpu.is_alu_reg):
                print(f"     alu_reg rd={ctx.get(cpu.rd_id)} "
                      f"rs1={ctx.get(cpu.rs1_id)} "
                      f"rs2={ctx.get(cpu.rs2_id)} "
                      f"funct3={ctx.get(cpu.funct3)}")
            if ctx.get(cpu.is_alu_imm):
                print(f"     alu_imm rd={ctx.get(cpu.rd_id)} "
                      f"rs1={ctx.get(cpu.rs1_id)} "
                      f"imm={ctx.get(cpu.i_imm)} "
                      f"funct3={ctx.get(cpu.funct3)}")
            if ctx.get(cpu.is_branch):
                print(f"    BRANCH rs1={ctx.get(cpu.rs1_id)} "
                      f"rs2={ctx.get(cpu.rs2_id)}")
            if ctx.get(cpu.is_load):
                print("    LOAD")
            if ctx.get(cpu.is_store):
                print("    STORE")
            if ctx.get(cpu.is_system):
                print("    SYSTEM")
        if state == 4:
            print(f"  R: LEDS = {ctx.get(soc.leds):>05b}")
            print(f"  R: rs1={ctx.get(cpu.rs1)}")
            print(f"  R: rs2={ctx.get(cpu.rs2)}")
        if state == 1:
            print(f"  E: LEDS = {ctx.get(soc.leds):>05b}")
            print(f"  E: Writeback x{ctx.get(cpu.rd_id)} = "
                  f"{ctx.get(cpu.write_back_data):>032b}")
        if state == 8:
            print("  NEW")
        await ctx.tick()

sim = Simulator(soc)
sim.add_clock(Period(MHz=1))
sim.add_testbench(testbench)

with sim.write_vcd('bench.vcd', 'bench.gtkw'):
    sim.run_until(Period(MHz=1) * 280)
