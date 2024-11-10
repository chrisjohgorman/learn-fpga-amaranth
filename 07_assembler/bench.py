#!/usr/bin/env python3

""" This module uses the riscv-assembly module to improve the readability
    of the code used in the arithmetic logic unit (ALU). """

from soc import SOC
from amaranth import Signal
from amaranth.sim import Simulator, Period

en = Signal(init=1)
count = Signal(4)
soc = SOC()


async def process(ctx):

    """ Process function to test values from the arithmetic logic unit
        using the riscv-assembler.  Create a counter to increment and
        wait for during the testbench function. """

    count_value = 0  # initialize counter to 0
    async for clk_edge, rst_value, en_value in ctx.tick().sample(en):
        if rst_value:  # can be asserted with or without clk_edge
            count_value = 0  # re-initialize counter
        elif clk_edge and en_value:
            count_value += 1  # advance the counter
            ctx.set(count, count_value)  # publish its value to the simulation


async def testbench(ctx):

    """ Testbench function to test values from the arithmetic logic unit
        using the riscv-assembly file. """

    while True:
        state = ctx.get(soc.state)
        print(f"state is {state}")
        if state == 2:
            print("-- NEW CYCLE -----------------------")
            print(f"  Fetch: LEDS = {ctx.get(soc.leds):>05b}")
            print(f"  Fetch: pc={ctx.get(soc.pc)}")
            print(f"  Fetch: instr={ctx.get(soc.instr):>032b}")
            if ctx.get(soc.is_alu_reg):
                print(f"     alu_reg rd={ctx.get(soc.rd_id)} "
                      f"rs1={ctx.get(soc.rs1_id)} "
                      f"rs2={ctx.get(soc.rs2_id)} "
                      f"funct3={ctx.get(soc.funct3)}")
            if ctx.get(soc.is_alu_imm):
                print(f"     alu_imm rd={ctx.get(soc.rd_id)} "
                      f"rs1={ctx.get(soc.rs1_id)} "
                      f"imm={ctx.get(soc.i_imm)} "
                      f"funct3={ctx.get(soc.funct3)}")
            if ctx.get(soc.is_load):
                print("    LOAD")
            if ctx.get(soc.is_store):
                print("    STORE")
            if ctx.get(soc.is_system):
                print("    SYSTEM")
        if state == 4:
            print(f"  Register: LEDS = {ctx.get(soc.leds):>05b}")
            print(f"  Register: rs1={ctx.get(soc.rs1)}")
            print(f"  Register: rs2={ctx.get(soc.rs1)}")
        if state == 1:
            print(f"  Execute: LEDS = {ctx.get(soc.leds):>05b}")
            print(f"  Execute: Writeback x{ctx.get(soc.rd_id)} "
                  f"= {ctx.get(soc.write_back_data):>032b}")
        await ctx.tick()


sim = Simulator(soc)
sim.add_clock(Period(MHz=1))
sim.add_process(process)
sim.add_testbench(testbench)

with sim.write_vcd('bench.vcd', 'bench.gtkw', traces=soc.ports):
    sim.run_until(Period(MHz=1) * 45)
