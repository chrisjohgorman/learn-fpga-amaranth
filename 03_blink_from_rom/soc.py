
""" This module provides the system on chip (SOC) implementation """

from amaranth import Module, Signal, Array, Mux
from amaranth.lib import wiring
from amaranth.lib.wiring import Out


class SOC(wiring.Component):

    """ This class describes the SOC """

    leds: Out(5)

    def __init__(self):

        super().__init__()

    def elaborate(self, platform):

        """ The clockwork provides a new clock domain called 'slow'.
            We replace the default sync domain with the new one to have the
            counter run slower. """

        m = Module()

        sequence = [
                0b00000,
                0b00001,
                0b00010,
                0b00011,
                0b00100,
                0b00101,
                0b00110,
                0b00111,
                0b01000,
                0b01001,
                0b01010,
                0b01011,
                0b01100,
                0b01101,
                0b01110,
                0b01111,
                0b10000,
                0b10001,
                0b10010,
                0b10011,
                0b10100,
                0b10101,
                0b10110,
                0b10111,
                0b11000,
                0b11001,
                0b11010,
                0b11011,
                0b11100,
                0b11101,
                0b11110,
                0b11111,
        ]

        pc = Signal(5)
        mem = Array([Signal(5, init=x) for x in sequence])

        if platform is None:
            m.d.sync += pc.eq(Mux(pc == len(sequence), 0, pc + 1))
        else:
            m.d.slow += pc.eq(Mux(pc == len(sequence), 0, pc + 1))

        m.d.comb += self.leds.eq(mem[pc])

        return m
