# All six conditional branches, taken and not taken.  x10 counts the branches that behaved correctly.
        li   x1, 5
        li   x2, 5
        li   x3, -1             # 0xFFFFFFFF
        li   x4, 1
        li   x10, 0
        beq  x1, x2, b1         # taken
        j    fail
b1:     addi x10, x10, 1
        beq  x1, x4, fail       # not taken
        addi x10, x10, 1
        bne  x1, x4, b2         # taken
        j    fail
b2:     addi x10, x10, 1
        bne  x1, x2, fail
        addi x10, x10, 1
        blt  x3, x4, b3         # -1 < 1 signed: taken
        j    fail
b3:     addi x10, x10, 1
        blt  x4, x3, fail       # 1 < -1 signed: not taken
        addi x10, x10, 1
        bge  x4, x3, b4         # 1 >= -1 signed: taken
        j    fail
b4:     addi x10, x10, 1
        bge  x3, x4, fail
        addi x10, x10, 1
        bltu x4, x3, b5         # 1 < 0xFFFFFFFF unsigned: taken
        j    fail
b5:     addi x10, x10, 1
        bltu x3, x4, fail
        addi x10, x10, 1
        bgeu x3, x4, b6         # taken
        j    fail
b6:     addi x10, x10, 1
        bgeu x4, x3, fail
        addi x10, x10, 1
        bge  x1, x2, b7         # equal: taken
        j    fail
b7:     addi x10, x10, 1
        chk  x10, 13
        # backward branch: count down from 10
        li   x5, 10
        li   x6, 0
loop:   add  x6, x6, x5
        addi x5, x5, -1
        bnez x5, loop
        chk  x6, 55
        li   x31, 0x600D
halt:   j    halt
fail:   li   x31, 0xDEAD
        j    fail
