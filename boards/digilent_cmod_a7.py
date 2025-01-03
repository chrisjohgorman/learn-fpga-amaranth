from amaranth.build import *
from amaranth_boards.cmod_a7 import *

from top import Top

if __name__ == "__main__":
    platform = CmodA7_35Platform(toolchain="Vivado")
    gpio = ("gpio", 0)
    platform.add_resources([
        Resource("uart", 1,
             Subsignal("tx", Pins("1", conn=gpio, dir='o')),
             Subsignal("rx", Pins("2", conn=gpio, dir='i')),
             Attrs(IOSTANDARD="LVCMOS33")
        )
    ])

    # The platform allows access to the various resources defined
    # by the board definition from amaranth-boards.
    led0 = platform.request('led', 0)
    led1 = platform.request('led', 1)
    rgb = platform.request('rgb_led')
    leds = [led0, led1, rgb.r, rgb.g, rgb.b]
    uart = platform.request('uart')

    platform.build(Top(leds, uart), do_program=True)
