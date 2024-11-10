#!/usr/bin/env python3

""" This module emulates the register bank """

from soc import SOC
from amaranth import Signal
from amaranth.sim import Simulator, Period

en = Signal(init=1)
count = Signal(4)
soc = SOC()


async def process(ctx):

    """ Process function to test values from the register bank.
        Create a counter to increment and wait for during the
        testbench function. """

    count_value = 0  # initialize counter to 0
    async for clk_edge, rst_value, en_value in ctx.tick().sample(en):
        if rst_value:  # can be asserted with or without clk_edge
            count_value = 0  # re-initialize counter
        elif clk_edge and en_value:
            count_value += 1  # advance the counter
            ctx.set(count, count_value)  # publish its value to the simulation


async def testbench(ctx):

    """ Testbench function to test values from the register bank """

    while True:
        print(f"pc={ctx.get(soc.pc)}")
        print(f"instr={ctx.get(soc.instr):>032b}")
        print(f"LEDS = {ctx.get(soc.leds):>05b}")
        if ctx.get(soc.is_alu_reg):
            print(f"alu_reg rd={ctx.get(soc.rd_id)} "
                  f"rs1={ctx.get(soc.rs1_id)} "
                  f"rs2={ctx.get(soc.rs2_id)} "
                  f"funct3={ctx.get(soc.funct3)}")
        if ctx.get(soc.is_alu_imm):
            print(f"alu_imm rd={ctx.get(soc.rd_id)} "
                  f"rs1={ctx.get(soc.rs1_id)} "
                  f"i_imm={ctx.get(soc.i_imm)} "
                  f"funct3={ctx.get(soc.funct3)}")
        if ctx.get(soc.is_load):
            print("LOAD")
        if ctx.get(soc.is_store):
            print("STORE")
        if ctx.get(soc.is_system):
            print("SYSTEM")
        # each instruction requires three clock ticks to execute
        await ctx.tick()


sim = Simulator(soc)
sim.add_clock(Period(MHz=1))
sim.add_process(process)
sim.add_testbench(testbench)

with sim.write_vcd('bench.vcd', 'bench.gtkw', traces=soc.ports):
    sim.run_until(Period(MHz=1) * 30)
