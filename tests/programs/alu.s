# R-type and I-type ALU instructions.  chk rd, value -> branch to `fail` if rd != value
        li   x1, 5
        li   x2, 7
        add  x3, x1, x2
        chk  x3, 12
        sub  x3, x1, x2
        chk  x3, -2
        and  x3, x1, x2
        chk  x3, 5
        or   x3, x1, x2
        chk  x3, 7
        xor  x3, x1, x2
        chk  x3, 2
        li   x4, 0x80000000
        li   x5, 1
        sll  x3, x5, x2          # 1 << 7
        chk  x3, 128
        srl  x3, x4, x5          # 0x80000000 >> 1 logical
        chk  x3, 0x40000000
        sra  x3, x4, x5          # arithmetic
        chk  x3, 0xC0000000
        li   x6, -1
        slt  x3, x6, x5          # -1 < 1 signed
        chk  x3, 1
        sltu x3, x6, x5          # 0xFFFFFFFF < 1 unsigned
        chk  x3, 0
        slt  x3, x5, x6
        chk  x3, 0
        sltu x3, x5, x6
        chk  x3, 1
        addi x3, x1, 10
        chk  x3, 15
        addi x3, x1, -10
        chk  x3, -5
        andi x3, x2, 3
        chk  x3, 3
        ori  x3, x1, 8
        chk  x3, 13
        xori x3, x1, 0xFF
        chk  x3, 0xFA
        slli x3, x1, 4
        chk  x3, 80
        srli x3, x4, 31
        chk  x3, 1
        srai x3, x4, 31
        chk  x3, -1
        slti x3, x6, 0
        chk  x3, 1
        sltiu x3, x6, 0
        chk  x3, 0
        sltiu x3, x5, -1         # 1 < 0xFFFFFFFF unsigned
        chk  x3, 1
        addi x0, x0, 5           # writes to x0 are ignored
        chk  x0, 0
        li   x7, 0x12345678
        chk  x7, 0x12345678
        lui  x8, 0xABCDE
        chk  x8, 0xABCDE000
        auipc x9, 1              # pc + 0x1000
        li   x10, 0
        chk  x10, 0
        li   x31, 0x600D
halt:   j    halt
fail:   li   x31, 0xDEAD
        j    fail
