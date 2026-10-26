# Loops with arithmetic: fib(10) = 55 and the sum 1..20 = 210; results also stored in memory.
        li   x1, 0              # fib(n-1)
        li   x2, 1              # fib(n)
        li   x3, 9              # 9 more steps -> fib(10)
fibl:   add  x4, x1, x2
        mv   x1, x2
        mv   x2, x4
        addi x3, x3, -1
        bnez x3, fibl
        chk  x2, 55
        sw   x2, 0(x0)
        li   x5, 20
        li   x6, 0
suml:   add  x6, x6, x5
        addi x5, x5, -1
        bgtz x5, suml
        chk  x6, 210
        sw   x6, 4(x0)
        lw   x7, 0(x0)
        lw   x8, 4(x0)
        add  x9, x7, x8
        chk  x9, 265
        li   x31, 0x600D
halt:   j    halt
fail:   li   x31, 0xDEAD
        j    fail
