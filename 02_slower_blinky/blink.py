from soc import SOC
from clockworks import Clockworks
from amaranth_boards.cmod_a7 import CmodA7_35Platform
from amaranth import Module, ClockDomain


# A platform contains board specific information about FPGA pin assignments,
# toolchain and specific information for uploading the bitfile.
platform = CmodA7_35Platform(toolchain="Xray")

# We need a top level module
m = Module()

# This is the instance of our SOC
soc = SOC()

# The SOC is turned into a submodule (fragment) of our top level module.
m.submodules.soc = soc

m.submodules.slclk = slclk = Clockworks(slow=21)

# The platform allows access to the various resources defined by the board
# definition from amaranth-boards.
led0 = platform.request('led', 0)
led1 = platform.request('led', 1)
rgb = platform.request('rgb_led')

# We connect the SOC leds signal to the various LEDs on the board.
m.d.comb += [
    led0.o.eq(soc.leds[0]),
    led1.o.eq(soc.leds[1]),
    rgb.r.o.eq(soc.leds[2]),
    rgb.g.o.eq(soc.leds[3]),
    rgb.b.o.eq(soc.leds[4]),
]

# To generate the bitstream, we build() the platform using our top level
# module m.
platform.build(m, do_program=True)
