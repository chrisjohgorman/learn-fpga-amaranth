#!/usr/bin/env python3

""" This module blinks the leds on a Cmod A7 FPGA slowly enough to see """

from soc import SOC
from clockworks import Clockworks, CLOCKWORKS_DOMAIN_NAME
from amaranth_boards.cmod_a7 import CmodA7_35Platform, Resource, Subsignal, \
        Pins, Attrs
from amaranth import Module, ClockDomain, Elaboratable


class Top(Elaboratable):

    """ This class sets pin assignments for the board leds.  It initializes the
        clock domain to slow it down so we can see the leds blink on the board
        describing the states of the finite state machine of the system on
        chip. """

    def __init__(self, leds, uart):

        self.soc = SOC()
        self.leds = leds
        self.uart = uart

    def elaborate(self, platform):

        """ This function sets up the board.  A ClockDomain is initialized and
            the leds of the board are connected to the leads of the SOC. """

        # We need a top level module
        m = Module()

        # This is the instance of our SOC
        soc = self.soc
        leds = self.leds
        uart = self.uart

        # The SOC is turned into a submodule (fragment) of our top level
        # module.
        m.submodules.soc = soc

        # for amaranth version 0.6 define slow domain in top module
        m.domains += ClockDomain(CLOCKWORKS_DOMAIN_NAME)
        slow_clk = Clockworks()
        # Turn the clockwork into a submodule of the top level module
        m.submodules.slow_clk = slow_clk

        # We connect the SOC leds signal to the various LEDs on the board.
        m.d.comb += [
            leds[0].o.eq(soc.leds[0]),
            leds[1].o.eq(soc.leds[1]),
            leds[2].o.eq(soc.leds[2]),
            leds[3].o.eq(soc.leds[3]),
            leds[4].o.eq(soc.leds[4]),
        ]

        # Connect the tx port to the SOC
        if hasattr(soc, "tx"):
            m.d.comb += [
                uart.tx.o.eq(soc.tx)
            ]

        return m


if __name__ in "__main__":

    # A platform contains board specific information about FPGA pin
    # assignments, toolchain and specific information for uploading the
    # bitfile.
    platform = CmodA7_35Platform(toolchain="Vivado")
    gpio = ("gpio", 0)
    platform.add_resources([
        Resource("uart", 1,
                 Subsignal("tx", Pins("1", conn=gpio, dir='o')),
                 Subsignal("rx", Pins("2", conn=gpio, dir='i')),
                 Attrs(IOSTANDARD="LVCMOS33"))
    ])
    # To generate the bitstream, we build() the platform using our top level
    # module m.
    # The platform allows access to the various resources defined by the board
    # definition from amaranth-boards.
    led0 = platform.request('led', 0)
    led1 = platform.request('led', 1)
    rgb = platform.request('rgb_led')

    board_leds = [led0, led1, rgb.r, rgb.g, rgb.b]
    board_uart = platform.request('uart')

    platform.build(Top(board_leds, board_uart), do_program=True)
