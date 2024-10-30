#!/usr/bin/env python3

""" This module blinks the leds on a Cmod A7 FPGA slowly enough to see """

from soc import SOC
from clockworks import Clockworks, CLOCKWORKS_DOMAIN_NAME
from amaranth_boards.cmod_a7 import CmodA7_35Platform
from amaranth import Module, ClockDomain, Elaboratable


class Top(Elaboratable):

    def __init__(self, leds):

        self.leds = leds
        self.soc = SOC()

    def elaborate(self, platform):
        # We need a top level module
        m = Module()

        soc = self.soc
        leds = self.leds

        # This is the instance of our SOC

        # The SOC is turned into a submodule (fragment) of our top level
        # module.
        m.submodules.soc = soc

        # for amaranth version 0.6 define slow domain in top module
        # Instantiate the clockwork with a divider of 2^21
        m.domains += ClockDomain(CLOCKWORKS_DOMAIN_NAME)
        slclk = Clockworks(slow=21)
        # Turn the clockwork into a submodule of the top level module
        m.submodules.slclk = slclk

        # We connect the SOC leds signal to the various LEDs on the board.
        m.d.comb += [
            leds[0].o.eq(soc.leds[0]),
            leds[1].o.eq(soc.leds[1]),
            leds[2].o.eq(soc.leds[2]),
            leds[3].o.eq(soc.leds[3]),
            leds[4].o.eq(soc.leds[4]),
        ]

        return m


if __name__ in "__main__":

    # A platform contains board specific information about FPGA pin
    # assignments, toolchain and specific information for uploading the
    # bitfile.
    platform = CmodA7_35Platform(toolchain="Xray")
    # To generate the bitstream, we build() the platform using our top level
    # module m.
    # The platform allows access to the various resources defined by the board
    # definition from amaranth-boards.
    led0 = platform.request('led', 0)
    led1 = platform.request('led', 1)
    rgb = platform.request('rgb_led')

    leds = [led0, led1, rgb.r, rgb.g, rgb.b]

    platform.build(Top(leds), do_program=True)
