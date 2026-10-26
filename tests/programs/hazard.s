# Data and control hazards of a pipeline (also valid on the single-cycle CPU).
# back-to-back dependencies (EX/MEM forwarding)
        li   x1, 1
        addi x2, x1, 1          # x1 from the previous instruction
        addi x3, x2, 1          # x2 from the previous instruction
        add  x4, x3, x2         # x3 one back, x2 two back (MEM/WB forwarding)
        chk  x4, 5
        sub  x5, x4, x1         # x4 just produced, x1 older
        chk  x5, 4
        # three instructions apart (register file write-then-read in the same cycle)
        addi x6, x0, 9
        nop
        nop
        add  x7, x6, x6
        chk  x7, 18
        # load-use: the loaded value is needed by the very next instruction
        li   x8, 77
        sw   x8, 16(x0)
        lw   x9, 16(x0)
        addi x10, x9, 1
        chk  x10, 78
        # load followed by a store of the loaded value
        lw   x11, 16(x0)
        sw   x11, 20(x0)
        lw   x12, 20(x0)
        chk  x12, 77
        # load, then use as the address of the next load
        li   x13, 24
        sw   x13, 24(x0)
        lw   x14, 24(x0)
        lw   x15, 0(x14)
        chk  x15, 24
        # branch that depends on a load (taken)
        li   x16, 5
        sw   x16, 28(x0)
        lw   x17, 28(x0)
        beq  x17, x16, taken1
        j    fail
taken1: li   x18, 1             # branch target
        # branch taken: the two instructions after it must not execute
        li   x19, 0
        beq  x0, x0, taken2
        addi x19, x19, 1        # must be skipped
        addi x19, x19, 1        # must be skipped
taken2: chk  x19, 0
        # not-taken branch must not disturb the next instructions
        li   x20, 3
        bne  x0, x0, fail
        addi x20, x20, 1
        chk  x20, 4
        # jump and link, link value used right away
        jal  x21, over
        j    fail               # skipped
over:   addi x22, x21, 4
        chk  x22, 204
        # jalr using a freshly computed register
        auipc x23, 0
        addi x23, x23, 16
        jalr x24, 0(x23)
        j    fail               # skipped
        li   x25, 5
        chk  x25, 5
        # x0 as a destination must never be forwarded
        addi x0, x0, 7
        add  x26, x0, x0
        chk  x26, 0
        # same register written twice in a row
        li   x27, 1
        li   x27, 2
        add  x28, x27, x27
        chk  x28, 4
        li   x31, 0x600D
halt:   j    halt
fail:   li   x31, 0xDEAD
        j    fail
