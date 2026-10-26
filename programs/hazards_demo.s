# Small program for watching pipeline hazards (see docs/GUIDE.md section 8).
        li   x1, 100
        sw   x1, 0(x0)
        lw   x2, 0(x0)          # load ...
        addi x3, x2, 1          # ... used by the very next instruction: load-use stall
        add  x4, x3, x2         # x3 forwarded from EX/MEM; x2 is already in the register file
        beq  x4, x4, skip       # taken branch: the next two instructions are flushed
        addi x5, x0, 1
        addi x6, x0, 2
skip:   addi x7, x0, 7
halt:   j    halt
