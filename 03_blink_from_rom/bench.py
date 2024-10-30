#!/usr/bin/env python3

""" This module emulates the leads in binary """

from soc import SOC
from amaranth.sim import Simulator, Period

soc = SOC()


class Global:

    """ Class with member to get rid of use of the global keyword. """

    prev_leds = 0


async def testbench(ctx):

    """ Testbench to simulate the setting of values of leds """

    while True:
        leds = ctx.get(soc.leds)
        if leds != Global.prev_leds:
            print(f"LEDS = {leds:>05b}")
            Global.prev_leds = leds
        await ctx.tick()

sim = Simulator(soc)
sim.add_clock(Period(MHz=1))
sim.add_testbench(testbench)

with sim.write_vcd('bench.vcd'):
    # Let's run for a quite long time
    sim.run_until(Period(MHz=1) * 50)
