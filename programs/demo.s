# Demo program (loaded into the ROM of both CPUs).
#   1. x10 = 1 + 2 + ... + 10 = 55      (loop with a backward branch)
#   2. store x10 to memory word 0 and load it back into x12     (sw / lw)
#   3. call double(): x12 = x12 + x12 = 110                      (jal / jalr, return address in x1)
#   4. x13 = x12 - x10 = 55, x14 = x13 < 100 (slt)
# Watch the registers x10, x12, x13, x14 and PC.  The program ends in an endless loop.
        li   x10, 0
        li   x11, 10
loop:   add  x10, x10, x11
        addi x11, x11, -1
        bnez x11, loop          # until x11 == 0
        sw   x10, 0(x0)
        lw   x12, 0(x0)
        jal  x1, double
        sub  x13, x12, x10
        slti x14, x13, 100
halt:   j    halt
double: add  x12, x12, x12
        ret
