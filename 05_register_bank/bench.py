#!/usr/bin/env python3

""" This module emulates the register bank """

from soc import SOC
from amaranth.sim import Simulator, Period


soc = SOC()

class Global:

    """ Class with member to get rid of the use if the global keyword """

    prev_clk = 0


async def testbench(ctx):

    """ Testbench function to test values from the register bank """

    while True:
        clk = ctx.get(soc.cw.o_slow)
        if Global.prev_clk == 0 and Global.prev_clk != clk:
            print(f"pc={soc.pc}")
            print(f"instr={ctx.get(soc.instr):>032b}")
            print(f"LEDS = {ctx.get(soc.leds):>05b}")
            if ctx.get(soc.is_alu_reg):
                print(f"ALUreg rd={ctx.get(soc.rd_id)} "
                      f"rs1={ctx.get(soc.rs1_id)} "
                      f"rs2={ctx.get(soc.rs2_id)} "
                      f"funct3={ctx.get(soc.funct3)}")
            if ctx.get(soc.is_alu_imm):
                print(f"ALUimm rd={ctx.get(soc.rd_id)} "
                      f"rs1={ctx.get(soc.rs1_id)} "
                      f"i_imm={ctx.get(soc.i_imm)} "
                      f"funct3={ctx.get(soc.funct3)}")
            if ctx.get(soc.is_load):
                print("LOAD")
            if ctx.get(soc.is_store):
                print("STORE")
            if ctx.get(soc.is_system):
                print("SYSTEM")
                break
        await ctx.tick()
        Global.prev_clk = clk

sim = Simulator(soc)
sim.add_clock(Period(MHz=1))
sim.add_testbench(testbench)

with sim.write_vcd('bench.vcd', 'bench.gtkw', traces=soc.ports):
    # Let's run for a quite long time
    sim.run_until(Period(MHz=1) * 10000)
