all: blinker.bram.elf

AS := riscv64-linux-gnu-as
LD := riscv64-linux-gnu-ld
ASFLAGS := -march=rv32i -mabi=ilp32 -mno-relax
LDFLAGS := -T bram.ld -m elf32lriscv -nostdlib -no-relax

%.o: %.S
	$(AS) $(ASFLAGS) $< -o $@

blinker.bram.elf: start.o blinker.o wait.o
	$(LD) $(LDFLAGS) $^ -o $@

clean:
	rm *.o
	rm *.bram.elf
