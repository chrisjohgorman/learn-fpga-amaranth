""" This is the system on chip module. """

from memory import Mem
from cpu import CPU
from uart_tx import UartTx
from amaranth import Elaboratable, Signal, Module, DomainRenamer, Cat, C, Mux


class SOC(Elaboratable):

    """ This class describes the SOC. """

    def __init__(self):

        self.leds = Signal(5)
        self.tx = Signal()

        self.cpu = None
        self.memory = None
        self.mem_wdata = None
        self.uart_valid = None

    def elaborate(self, platform):

        """ Here we connect the CPU and peripherals.  The memory module
            mem_addr, mem_rstrb and mem_rdata get connected to their
            respective CPU counterparts.  Then we connect the x10 register
            to the LEDs.  And finally we connect the UART module. """

        clk_frequency = int(platform.default_clk_constraint.frequency)
        print(f"clock frequency = {clk_frequency}")

        m = Module()
        memory = DomainRenamer("slow")(Mem())
        cpu = DomainRenamer("slow")(CPU())
        uart_tx = DomainRenamer("slow")(
                UartTx(freq_hz=clk_frequency, baud_rate=345600))

        m.submodules.cpu = cpu
        m.submodules.memory = memory
        m.submodules.uart_tx = uart_tx

        self.cpu = cpu
        self.memory = memory

        ram_rdata = Signal(32)
        mem_wordaddr = Signal(30)
        is_io = Signal()
        is_ram = Signal()
        mem_wstrb = Signal()
        io_rdata = Signal(32)

        # Memory map bits
        io_leds_bit = 0
        io_uart_dat_bit = 1
        io_uart_cntl_bit = 2

        m.d.comb += [
            mem_wordaddr.eq(cpu.mem_addr[2:32]),
            is_io.eq(cpu.mem_addr[22]),
            is_ram.eq(~is_io),
            mem_wstrb.eq(cpu.mem_wmask.any())
        ]

        self.mem_wdata = cpu.mem_wdata

        # Connect memory to CPU
        m.d.comb += [
            memory.mem_addr.eq(cpu.mem_addr),
            memory.mem_rstrb.eq(is_ram & cpu.mem_rstrb),
            memory.mem_wdata.eq(cpu.mem_wdata),
            memory.mem_wmask.eq(is_ram.replicate(4) & cpu.mem_wmask),
            ram_rdata.eq(memory.mem_rdata),
            cpu.mem_rdata.eq(Mux(is_ram, ram_rdata, io_rdata))
        ]

        if platform is not None:
            # LEDs
            with m.If(is_io & mem_wstrb & mem_wordaddr[io_leds_bit]):
                m.d.slow += self.leds.eq(cpu.mem_wdata)

        # UART
        uart_valid = Signal()
        self.uart_valid = uart_valid
        uart_ready = Signal()

        m.d.comb += [
            uart_valid.eq(is_io & mem_wstrb & mem_wordaddr[io_uart_dat_bit])
        ]

        # Hook up UART
        m.d.comb += [
            uart_tx.valid.eq(uart_valid),
            uart_tx.data.eq(cpu.mem_wdata[0:8]),
            uart_ready.eq(uart_tx.ready),
            self.tx.eq(uart_tx.tx)
        ]

        # Data from UART
        m.d.comb += [
            io_rdata.eq(Mux(mem_wordaddr[io_uart_cntl_bit],
                            Cat(C(0, 9), ~uart_ready, C(0, 22)), C(0, 32)))
        ]

        return m
