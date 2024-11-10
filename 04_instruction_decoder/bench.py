#!/usr/bin/env python3

""" This module emulates the instruction decoder """

from soc import SOC
from amaranth.sim import Simulator, Period

soc = SOC()


class Global:

    """ Class with member to get rid of use of global keyword. """

    prev_pc = 0


async def testbench(ctx):

    """ Proc function to test values from the instruction decoder. """

    while True:
        pc = ctx.get(soc.pc)
        if Global.prev_pc != pc:
            print(f"pc={pc}")
            print(f"instr={ctx.get(soc.instr):>032b}")
            print(f"LEDS = {ctx.get(soc.leds):>05b}")
            if ctx.get(soc.is_alu_reg):
                print(f"alu_reg rd={ctx.get(soc.rd_id)} "
                      f"rs1={ctx.get(soc.rs1_id)} "
                      f"rs2={ctx.get(soc.rs2_id)} "
                      f"i_imm={ctx.get(soc.i_imm)} "
                      f"funct3={ctx.get(soc.funct3)}")
            if ctx.get(soc.is_alu_imm):
                print(f"alu_imm rd={ctx.get(soc.rd_id)} "
                      f"rs1={ctx.get(soc.rs1_id)} "
                      f"imm={ctx.get(soc.i_imm)} "
                      f"funct3={ctx.get(soc.funct3)}")
            if ctx.get(soc.is_load):
                print("LOAD")
            if ctx.get(soc.is_store):
                print("STORE")
            if ctx.get(soc.is_system):
                print("SYSTEM")
        await ctx.tick()
        Global.prev_pc = pc


sim = Simulator(soc)
sim.add_clock(Period(MHz=1))
sim.add_testbench(testbench)

with sim.write_vcd('bench.vcd', 'bench.gtkw', traces=soc.ports):
    sim.run_until(Period(MHz=1) * 10)
