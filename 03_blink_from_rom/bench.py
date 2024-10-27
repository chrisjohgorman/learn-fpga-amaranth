from soc import SOC
from amaranth.sim import Simulator, Period

soc = SOC()

prev_leds = 0

async def testbench(ctx):
    global prev_leds
    while True:
        leds = ctx.get(soc.leds)
        if leds != prev_leds:
            print("LEDS = {:05b}".format(leds))
            prev_leds = leds
        await ctx.tick()

sim = Simulator(soc)
sim.add_clock(Period(MHz=1))
sim.add_testbench(testbench)

with sim.write_vcd('bench.vcd'):
    # Let's run for a quite long time
    sim.run_until(Period(MHz=1) * 100)
