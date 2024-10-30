#!/usr/bin/env python3

""" This module blinks the leds on a Cmod A7 FPGA """

from soc import SOC
from amaranth_boards.cmod_a7 import CmodA7_35Platform
from amaranth import Module, Elaboratable


class Top(Elaboratable):

    """ This class sets pin assignments for the board leds.  """

    def __init__(self, leds):

        self.soc = SOC()
        self.leds = leds

    def elaborate(self, platform):

        """ This function sets up the board and connects the led signals
            from the SOC to the led signals on the board. """

        # We need a top level module
        m = Module()

        # This is the instance of our SOC
        soc = self.soc

        # The SOC is turned into a submodule (fragment) of our top level
        # module.
        m.submodules.soc = soc

        # We connect the SOC leds signal to the various LEDs on the board.
        m.d.comb += [
            self.leds[0].o.eq(soc.leds[0]),
            self.leds[1].o.eq(soc.leds[1]),
            self.leds[2].o.eq(soc.leds[2]),
            self.leds[3].o.eq(soc.leds[3]),
            self.leds[4].o.eq(soc.leds[4]),
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

    board_leds = [led0, led1, rgb.r, rgb.g, rgb.b]

    platform.build(Top(board_leds), do_program=True)
