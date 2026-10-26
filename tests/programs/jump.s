# jal, jalr, lui, auipc, call / return.
        li   x12, 0
        jal  x5, target         # x5 = address of the next instruction
        li   x12, 99             # skipped
target: chk  x12, 0
        chk  x5, 8
        auipc x6, 0             # x6 = address of this instruction (0x1c = 28)
        chk  x6, 28
        lui  x7, 0x12345
        chk  x7, 0x12345000
        # function call: x10 = add3(4)
        li   x10, 4
        call add3
        chk  x10, 7
        # jalr with offset and bit-0 clearing
        auipc x8, 0
        addi x8, x8, 21         # odd target: bit 0 must be cleared -> lands on the chk below
        jalr x9, 0(x8)
        li   x12, 99             # skipped
        li   x12, 98             # skipped
        # jalr target lands here
        chk  x12, 0
        chk  x9, 80              # jalr wrote its return address
        li   x31, 0x600D
halt:   j    halt
fail:   li   x31, 0xDEAD
        j    fail
add3:   addi x10, x10, 3
        ret
