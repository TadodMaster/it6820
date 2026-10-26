# Loads and stores of every size.
        li   x1, 0x100          # base address
        li   x2, 0x8899AABB
        sw   x2, 0(x1)
        lw   x3, 0(x1)
        chk  x3, 0x8899AABB
        lb   x3, 0(x1)          # byte 0 = 0xBB, sign-extended
        chk  x3, 0xFFFFFFBB
        lbu  x3, 0(x1)
        chk  x3, 0xBB
        lb   x3, 1(x1)          # 0xAA
        chk  x3, 0xFFFFFFAA
        lbu  x3, 2(x1)          # 0x99
        chk  x3, 0x99
        lb   x3, 3(x1)          # 0x88
        chk  x3, 0xFFFFFF88
        lh   x3, 0(x1)          # 0xAABB
        chk  x3, 0xFFFFAABB
        lhu  x3, 2(x1)          # 0x8899
        chk  x3, 0x8899
        lh   x3, 2(x1)
        chk  x3, 0xFFFF8899
        li   x4, 0x11
        sb   x4, 1(x1)          # replace byte 1
        lw   x3, 0(x1)
        chk  x3, 0x889911BB
        li   x4, 0x2233
        sh   x4, 2(x1)          # replace upper half
        lw   x3, 0(x1)
        chk  x3, 0x223311BB
        sb   x4, 3(x1)          # 0x33 into byte 3
        sb   x4, 0(x1)
        lw   x3, 0(x1)
        chk  x3, 0x33331133
        sw   x0, 4(x1)
        lw   x3, 4(x1)
        chk  x3, 0
        li   x5, -2
        sw   x5, 8(x1)
        lw   x6, 8(x1)
        chk  x6, -2
        sw   x6, 12(x1)         # store a value that was just loaded
        lw   x7, 12(x1)
        chk  x7, -2
        li   x31, 0x600D
halt:   j    halt
fail:   li   x31, 0xDEAD
        j    fail
