#!/usr/bin/env python3

""" This module blinks the leds on a Cmod A7 FPGA slowly enough to see """

from soc import SOC
from clockworks import Clockworks, CLOCKWORKS_DOMAIN_NAME
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

if CLOCKWORKS_DOMAIN_NAME == "slow":
    # for amaranth version 0.6 define slow domain in top module
    # Instantiate the clockwork with a divider of 2^21
    m.domains += ClockDomain(CLOCKWORKS_DOMAIN_NAME)
    slclk = Clockworks(slow=21)
else:
    slclk = Clockworks()

# Turn the clockwork into a submodule of the top level module
m.submodules.slclk = slclk

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
