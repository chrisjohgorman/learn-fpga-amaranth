#!/usr/bin/env python3

""" This module emulates the values of leds in binary """

from soc import SOC
from amaranth.sim import Simulator, Tick


soc = SOC()

sim = Simulator(soc)


class Global:

    """ Class with member to get rid of use of global keyword. """

    PREV_LEDS = 0


def proc():

    """ Process to simulate the setting of values of leds """

    while True:
        leds = yield soc.leds
        if leds != Global.PREV_LEDS:
            print(f"LEDS = {leds:>05b}")
            Global.PREV_LEDS = leds
        yield Tick()


sim.add_clock(1e-6)
sim.add_process(proc)

with sim.write_vcd('bench.vcd'):
    sim.run_until(2e-5)
