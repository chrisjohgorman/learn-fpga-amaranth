#!/usr/bin/env python3

""" This module emulates the instruction decoder """

from soc import SOC
from amaranth.sim import Simulator, Period, Tick

soc = SOC()

sim = Simulator(soc)


class Global:

    """ Class with member to get rid of use of global keyword. """

    prev_pc = 0


def proc():

    """ Proc function to test values from the instruction decoder. """

    while True:
        pc = yield soc.pc
        if Global.prev_pc != pc:
            print(f"pc={pc}")
            print(f"instr={(yield soc.instr):>032b}")
            print(f"LEDS = {(yield soc.leds):>05b}")
            if (yield soc.is_alu_reg):
                print(f"ALUreg rd={(yield soc.rd_id)} rs1={(yield soc.rs1_id)}"
                      f" rs2={(yield soc.rs2_id)} i_imm={(yield soc.i_imm)} "
                      f"funct3={(yield soc.funct3)}")
            if (yield soc.is_system):
                print("SYSTEM")
                break
        yield Tick()
        Global.prev_pc = pc


sim.add_clock(Period(MHz=1))
sim.add_process(proc)

with sim.write_vcd('bench.vcd'):
    # Let's run for a quite long time
    sim.run_until(Period(MHz=1) * 100)
