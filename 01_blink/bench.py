#!/usr/bin/env python3

""" This module emulates the values of leds in binary """

from soc import SOC
from amaranth.sim import Simulator, Tick


soc = SOC()

sim = Simulator(soc)


class Global:

    """ Class with member to get rid of use of global keyword. """

    prev_leds = 0


def proc():

    """ Process to simulate the setting of values of leds """

    while True:
        leds = yield soc.leds
        if leds != Global.prev_leds:
            print(f"LEDS = {leds:>05b}")
            Global.prev_leds = leds
        yield Tick()


sim.add_clock(Period(MHz=1))
sim.add_process(proc)

with sim.write_vcd('bench.vcd'):
    sim.run_until(Period(MHz=1) * 100)
