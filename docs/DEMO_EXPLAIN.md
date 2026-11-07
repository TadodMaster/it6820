# DEMO_EXPLAIN - everything that happens in the demo

This file explains, instruction by instruction and signal by signal, **what the circuits do while you run the demo**.  `docs/PRESENTATION.md` says *when* to press what; this file says *why* the screen changes.  All values were measured on the project (probe traces of `RiscVComputer.circ`) and checked against the reference simulator.

Contents: 1 The programs - 2 How to read a tick - 3 One instruction through the single-cycle CPU - 4 All 40 ticks of `demo.s` - 5 The pipeline - 6 `hazards_demo.s` cycle by cycle - 7 What the proof and the tests do - 8 Cheat sheet

---

## 1. The programs

### 1.1 `programs/demo.s` (in the ROM of both CPUs at the start)

| Address | Machine code | Instruction | What it is for |
|---|---|---|---|
| 0x00 | `00000513` | `li x10, 0` | x10 = running sum = 0 |
| 0x04 | `00a00593` | `li x11, 10` | x11 = counter = 10 |
| 0x08 | `00b50533` | `loop: add x10, x10, x11` | sum = sum + counter |
| 0x0c | `fff58593` | `addi x11, x11, -1` | counter = counter - 1 |
| 0x10 | `fe059ce3` | `bnez x11, loop` | repeat while the counter is not 0 (branch back by 8 bytes) |
| 0x14 | `00a02023` | `sw x10, 0(x0)` | store the sum (55) in data memory word 0 |
| 0x18 | `00002603` | `lw x12, 0(x0)` | load it back into x12 |
| 0x1c | `010000ef` | `jal x1, double` | call the function at 0x2c, return address 0x20 goes to x1 |
| 0x20 | `40a606b3` | `sub x13, x12, x10` | 110 - 55 = 55 |
| 0x24 | `0646a713` | `slti x14, x13, 100` | 55 < 100, so x14 = 1 |
| 0x28 | `0000006f` | `halt: j halt` | endless loop: the program is finished |
| 0x2c | `00c60633` | `double: add x12, x12, x12` | x12 = 55 + 55 = 110 |
| 0x30 | `00008067` | `ret` (= `jalr x0, 0(x1)`) | jump back to the address in x1 (0x20) |

(`li x10,0` is the pseudo instruction `addi x10,x0,0`, `li x11,10` is `addi x11,x0,10`, `ret` is `jalr x0,0(x1)`.)

Result: sum 10 + 9 + ... + 1 = **55 = 0x37**; after the call **x12 = 110 = 0x6e**; `x13 = 0x37`, `x14 = 1`; data word 0 = 0x37; final PC = 0x28; `x1 = 0x20`.

### 1.2 `programs/hazards_demo.s` (for the pipeline)

| Address | Machine code | Instruction | Purpose |
|---|---|---|---|
| 0x00 | `06400093` | `li x1, 100` | x1 = 100 |
| 0x04 | `00102023` | `sw x1, 0(x0)` | needs x1 right after it was computed: **forwarding** |
| 0x08 | `00002103` | `lw x2, 0(x0)` | load |
| 0x0c | `00110193` | `addi x3, x2, 1` | uses x2 right after the load: **load-use stall** |
| 0x10 | `00218233` | `add x4, x3, x2` | x3 is forwarded again |
| 0x14 | `00420663` | `beq x4, x4, skip` | always taken: **flush** of the next two instructions |
| 0x18 | `00100293` | `addi x5, x0, 1` | must NOT take effect |
| 0x1c | `00200313` | `addi x6, x0, 2` | must NOT take effect |
| 0x20 | `00700393` | `skip: addi x7, x0, 7` | first instruction at the branch target |
| 0x24 | `0000006f` | `halt: j halt` | end |

Result: `x1 = 0x64`, `x2 = 0x64`, `x3 = 0x65`, `x4 = 0xc9`, `x7 = 7`, and **`x5 = x6 = 0`**.

---

## 2. How to read a tick

* One **Ctrl+F9** = one full clock cycle (clock 0 > 1 > 0).  On the single-cycle CPU this executes exactly one instruction.
* The PC register and the data RAM update on the **rising** edge; on the pipeline the register file updates on the **falling** edge (`CLK_n`).
* After a tick the PC already points to the **next** instruction.  The monitor row (probes) shows that next instruction (`instr`) and what it will compute; the State tab shows the registers that the **previous** instruction has just written.  So every instruction is seen twice: first as "about to run" (probe), then as "done" (State tab) one tick later.
* Wire colours: bright green = 1, dark green = 0 (single bits); buses show their value in hex.

---

## 3. One instruction through the single-cycle CPU

Every instruction goes through the same five stages in one cycle: **IF** (fetch from the ROM at PC) > **ID** (decode, read registers, build the immediate) > **EX** (ALU, branch decision, next PC) > **MEM** (data RAM) > **WB** (write the result into `rd`).  Below is what is on the key wires for each class of instruction of `demo.s`.

### 3.1 R-type: `add x10, x10, x11` (0x08, `00b50533`), first time (tick 3)
* **IF**: the ROM at PC = 0x08 outputs `00b50533`; `pc_plus4` = 0x0c.
* **ID**: `InstructionDecode` cuts `opcode = 0x33`, `rd = 10`, `funct3 = 0`, `rs1 = 10`, `rs2 = 11`, `funct7 = 0`.  `MainControl`: `RegWrite = 1`, `ALUSrc = 0` (B is a register), `ALUOp = 10` (R-type), `MemWrite = MemRead = 0`, `WBSel = 00`.  The register file outputs `rs1_data = x10 = 0` and `rs2_data = x11 = 0x0a`.
* **EX**: `ALUControl` turns `ALUOp = 10, funct3 = 0, funct7 = 0` into `ALUCtrl = 0` (ADD).  The ALU computes 0 + 0x0a = **0x0a** (`alu_result`).  `IsBranch = 0`, so `branch_taken = 0`.
* **MEM**: nothing (the RAM is not written).
* **WB**: `wb_data = alu_result = 0x0a`; at the clock edge it is written into `x10`.  Next PC = PC + 4 = 0x0c.
* **See it**: probes `instr = 00b50533` and `alu_result = wb_data = 0000000a` *before* the tick; x10 changes from 0 to 0x0a *after* the tick.

### 3.2 I-type ALU: `addi x11, x11, -1` (0x0c, `fff58593`)
* **ID**: `imm = 0xffffffff` (the 12-bit value `fff` sign-extended); `ALUSrc = 1` (B is the immediate); `ALUOp = 11` (I-type).
* **EX**: ALU input B = imm; `ALUCtrl = ADD`; 0x0a + (-1) = **0x09**.
* **WB**: x11 = 9.  The first time (tick 4) the probe shows `alu_result = 9`.

### 3.3 Branch taken: `bnez x11, loop` (0x10, `fe059ce3` = `bne x11, x0, -8`)
* **ID**: the B-type immediate is **-8** (`ImmGen` rebuilds it from scattered instruction bits); `IsBranch = 1`; `RegWrite = 0`.
* **EX**: `BranchUnit` compares `rs1_data` (x11 = 9) with `rs2_data` (x0 = 0) using `funct3 = 001` (BNE): they differ, so **`branch_taken = 1`** (the probe shows 1).  Next-PC logic: `pc_target = PC + imm = 0x10 - 8 = 0x08`; `take_target = 1`, so `next_pc = 0x08`.
* **WB**: nothing is written.  After the tick the **PC is 0x08 again** (the loop).
* Last iteration (x11 = 0): the probe shows `branch_taken = 0` after tick 31, and `next_pc = PC + 4 = 0x14` at tick 32: the loop ends.

### 3.4 Store: `sw x10, 0(x0)` (0x14, `00a02023`), tick 33
* **ID**: S-type immediate = 0; `MemWrite = 1`, `RegWrite = 0`, `ALUSrc = 1`.
* **EX**: address = `rs1 + imm` = x0 + 0 = **0** (`alu_result`).
* **MEM**: `Memory` gets `Address = 0`, `write_data = rs2_data = x10 = 0x37`, `MemWrite = 1`, `funct3 = 010` (word); `StoreMerge` sets all four byte enables, and at the clock edge RAM word 0 becomes **0x37**.
* **See it**: no register changes at tick 33; only the RAM changes (the proof prints it as `0x0000  37`).

### 3.5 Load: `lw x12, 0(x0)` (0x18, `00002603`), tick 34
* **EX**: address 0.  **MEM**: RAM word 0 = 0x37 appears on `read_data`; `LoadExtract` with `funct3 = 010` (word) passes it unchanged: `mem_rdata = 0x37`.
* **WB**: `WBSel = 01` selects memory instead of the ALU: `wb_data = 0x37` is written into x12.

### 3.6 Jump and link: `jal x1, double` (0x1c, `010000ef`), tick 35
* **ID**: J-type immediate = 0x10; `IsJAL = 1`, `RegWrite = 1`, `WBSel = 10` (PC + 4).
* **EX**: `pc_target = PC + imm = 0x1c + 0x10 = 0x2c`; `take_target = IsJAL = 1`, so `next_pc = 0x2c`.
* **WB**: `wb_data = pc_plus4 = 0x20` goes to x1 (the return address).
* **See it**: the PC jumps from 0x1c to **0x2c** and x1 = 0x20.

### 3.7 The function: `add x12, x12, x12` (tick 36) and `ret` (tick 37, `00008067` = `jalr x0, 0(x1)`)
* `add x12,x12,x12`: 0x37 + 0x37 = **0x6e** goes into x12.
* `ret`: `IsJALR = 1`; the ALU computes `rs1 + imm = x1 + 0 = 0x20`; the next-PC logic clears bit 0 (`& 0xFFFFFFFE`) and selects it: `next_pc = 0x20`.  `rd = x0`, so the link value is thrown away (x0 cannot change).
* The PC goes 0x30 > **0x20**.

### 3.8 After the call: `sub x13, x12, x10` (tick 38, `40a606b3`) and `slti x14, x13, 100` (tick 39, `0646a713`)
* `sub`: `funct7 = 0100000` makes `ALUControl` select SUB: 0x6e - 0x37 = **0x37** goes into x13.
* `slti`: I-type, `funct3 = 010`: the ALU does a signed compare 0x37 < 100, result 1, so **x14 = 1**.

### 3.9 The end: `halt: j halt` (0x28, `0000006f` = `jal x0, 0`)
A jump to itself: `pc_target = PC + 0 = 0x28`.  The PC stays at 0x28 forever; `rd = x0`, so no register changes.  This means "the program has ended"; more ticks change nothing.

---

## 4. All 40 ticks of `demo.s` (single-cycle)

Tick n executes the instruction at the PC *before* the tick; the last two columns are the state *after* the tick.

| Tick | Executed (PC) | Instruction | Register / memory change | PC after |
|---:|---|---|---|---|
| 1 | 0x00 | `li x10, 0` | (x10 stays 0) | 0x04 |
| 2 | 0x04 | `li x11, 10` | x11 = 0x0a | 0x08 |
| 3 | 0x08 | `add x10,x10,x11` | x10 = 0x0a | 0x0c |
| 4 | 0x0c | `addi x11,x11,-1` | x11 = 0x09 | 0x10 |
| 5 | 0x10 | `bnez` (taken) | - | 0x08 |
| 6 | 0x08 | `add` | x10 = 0x13 | 0x0c |
| 7 | 0x0c | `addi` | x11 = 0x08 | 0x10 |
| 8 | 0x10 | `bnez` (taken) | - | 0x08 |
| 9 | 0x08 | `add` | x10 = 0x1b | 0x0c |
| 10 | 0x0c | `addi` | x11 = 0x07 | 0x10 |
| 11 | 0x10 | `bnez` (taken) | - | 0x08 |
| 12 | 0x08 | `add` | x10 = 0x22 | 0x0c |
| 13 | 0x0c | `addi` | x11 = 0x06 | 0x10 |
| 14 | 0x10 | `bnez` (taken) | - | 0x08 |
| 15 | 0x08 | `add` | x10 = 0x28 | 0x0c |
| 16 | 0x0c | `addi` | x11 = 0x05 | 0x10 |
| 17 | 0x10 | `bnez` (taken) | - | 0x08 |
| 18 | 0x08 | `add` | x10 = 0x2d | 0x0c |
| 19 | 0x0c | `addi` | x11 = 0x04 | 0x10 |
| 20 | 0x10 | `bnez` (taken) | - | 0x08 |
| 21 | 0x08 | `add` | x10 = 0x31 | 0x0c |
| 22 | 0x0c | `addi` | x11 = 0x03 | 0x10 |
| 23 | 0x10 | `bnez` (taken) | - | 0x08 |
| 24 | 0x08 | `add` | x10 = 0x34 | 0x0c |
| 25 | 0x0c | `addi` | x11 = 0x02 | 0x10 |
| 26 | 0x10 | `bnez` (taken) | - | 0x08 |
| 27 | 0x08 | `add` | x10 = 0x36 | 0x0c |
| 28 | 0x0c | `addi` | x11 = 0x01 | 0x10 |
| 29 | 0x10 | `bnez` (taken) | - | 0x08 |
| 30 | 0x08 | `add` | x10 = 0x37 (= 55) | 0x0c |
| 31 | 0x0c | `addi` | x11 = 0x00 | 0x10 |
| 32 | 0x10 | `bnez` (**not** taken) | - | 0x14 |
| 33 | 0x14 | `sw x10,0(x0)` | memory word 0 = 0x37 | 0x18 |
| 34 | 0x18 | `lw x12,0(x0)` | x12 = 0x37 | 0x1c |
| 35 | 0x1c | `jal x1,double` | x1 = 0x20 | **0x2c** |
| 36 | 0x2c | `add x12,x12,x12` | x12 = 0x6e (= 110) | 0x30 |
| 37 | 0x30 | `ret` | - | **0x20** |
| 38 | 0x20 | `sub x13,x12,x10` | x13 = 0x37 | 0x24 |
| 39 | 0x24 | `slti x14,x13,100` | x14 = 0x01 | 0x28 |
| 40 | 0x28 | `halt` | - | 0x28 (stays) |

Why the results say 39 cycles and not 40: the 40th tick only repeats the final jump; the last register write happens at tick 39 (`live_proof.py` reports 39 cycles, CPI 1.00).

Things to point at: the PC goes **back** at ticks 5, 8, 11, ... (the loop); at tick 32 it finally **falls through**; at tick 35 it **jumps forward** to 0x2c and x1 is set; at tick 37 it **returns** to 0x20.

---

## 5. The pipeline: the same instructions in five stages

On the pipeline CPU the five stages work on five different instructions at the same time.  One instruction needs 5 cycles from fetch to write-back, but when nothing goes wrong a new one finishes every cycle.

```
              1   2   3   4   5   6   7   8
instruction A IF  ID  EX  ME  WB
instruction B     IF  ID  EX  ME  WB
instruction C         IF  ID  EX  ME  WB
instruction D             IF  ID  EX  ME  WB
```

* **IF/ID, ID/EX, EX/MEM, MEM/WB** are the pipeline registers (the labelled boxes between the stages): they hold everything an instruction needs in the next stage (PC, register values, immediate, destination `rd`, control word).
* The control signals are produced once, in ID, packed into a "control word" and travel with the instruction; each stage uses its part.
* The register file writes on the **falling** edge, so an instruction in WB writes in the first half of a cycle and an instruction in ID reads the new value in the second half.
* The cost: every taken branch or jump costs 2 cycles (the two instructions fetched behind it are cancelled).  This explains the 64 cycles of `demo.s` on the pipeline: 39 instructions, plus 11 taken redirects x 2 = 22 lost cycles (9 taken `bnez`, the `jal` and the `ret`), gives 61; the remaining 3 cycles are the pipeline filling (the write-back comes 4 stages after the fetch, and the single-cycle count already includes one).
* The real gain of a pipeline is a shorter clock period (one stage instead of five in the longest path); Logisim's zero-delay simulation does not show this, so in cycles the pipeline looks slower.

---

## 6. `hazards_demo.s` on the pipeline, cycle by cycle

Occupancy of the stages **after** each tick (what you see in the circuit and in the monitor row).  "bubble" = a NOP inserted by the hazard logic.

| After tick | IF (PC) | ID | EX | MEM | WB | `stall` | `pc_src_ex` | `ForwardA` | `ForwardB` | What happens |
|---:|---|---|---|---|---|:-:|:-:|:-:|:-:|---|
| 1 | sw (04) | li x1 | - | - | - | 0 | 0 | 00 | 00 | the pipeline fills |
| 2 | lw (08) | sw | li | - | - | 0 | 0 | 00 | 00 | `li` computes 0x64 in EX |
| 3 | addi x3 (0c) | lw | sw | li | - | 0 | 0 | 00 | **10** | **forwarding**: `sw` needs x1; `li` is in MEM, so its ALU result 0x64 is taken from EX/MEM (ForwardB = 10) instead of waiting for the register file |
| 4 | add x4 (10) | addi x3 | lw | sw | li | **1** | 0 | 00 | 00 | **load-use hazard** found: `addi x3,x2,1` (in ID) needs x2, which `lw` (in EX) has only at the end of MEM: `stall` = 1 |
| 5 | add x4 (**10**, held) | addi x3 | **bubble** | lw | sw | 0 | 0 | 10 | 00 | PC and IF/ID **hold**; the bubble in EX is the one lost cycle |
| 6 | beq (14) | add x4 | addi x3 | bubble | lw | 0 | 0 | **01** | 00 | `lw` is in WB: its data reaches `addi` through MEM/WB (ForwardA = 01); `addi` computes 0x65 |
| 7 | addi x5 (18) | beq | add x4 | addi x3 | bubble | 0 | 0 | **10** | 00 | `add x4,x3,x2`: x3 comes from EX/MEM (ForwardA = 10), x2 is already in the register file; result 0xc9 |
| 8 | addi x6 (1c) | addi x5 | **beq** | add x4 | addi x3 | 0 | **1** | 10 | 10 | `beq x4,x4` compares the two forwarded copies of x4: **taken**, `pc_src_ex` = 1 |
| 9 | skip (**20**) | **bubble** | **bubble** | beq | add x4 | 0 | 0 | 00 | 00 | **flush**: the two instructions fetched behind the `beq` (`addi x5`, `addi x6`) became bubbles; the PC is now the target 0x20 |
| 10 | halt (24) | addi x7 | bubble | bubble | beq | 0 | 0 | 00 | 00 | the program continues at the target |
| 11 | (28) | halt | addi x7 | bubble | bubble | 0 | 0 | 00 | 00 | `addi x7,x0,7` computes 7 |
| 12 | (2c) | bubble | halt | addi x7 | bubble | 0 | **1** | 00 | 00 | the final `j halt` redirects (and flushes) again; this repeats forever and is normal |

(The `ForwardA = 10` at tick 5 belongs to the bubble in EX: a bubble keeps the register numbers of the stalled instruction but its control word is zero, so it does nothing.)

At the end (after about 13 ticks) the State tab must show `x1 = 0x64`, `x2 = 0x64`, `x3 = 0x65`, `x4 = 0xc9`, `x7 = 0x07`, and `x5 = x6 = 0`: the flushed instructions left no trace.  Three kinds of hazard, three solutions:

| Hazard | Where you see it | Solution | Cost |
|---|---|---|---|
| use of a value just computed by the ALU | `ForwardA/B` = 10 or 01 | forwarding from EX/MEM or MEM/WB | 0 cycles |
| use of a value just loaded | `stall` = 1, the PC holds at 10 for one tick | one bubble, then forwarding | 1 cycle |
| taken branch / jump | `pc_src_ex` = 1, `instr_id` = 0 afterwards | flush the two fetched instructions | 2 cycles |

---

## 7. What the proof and the tests do

* `python tools\live_proof.py` assembles the program and runs it on the **reference simulator** (independent Python code), on the **single-cycle circuit** and on the **pipeline circuit** (both through Logisim itself, without the GUI).  It then compares all 32 registers and every non-zero data word (`OK` for each) and prints `VERDICT: both CPUs produce exactly the reference result`, with the cycle counts (39 and 64).
* `tests\run_tests.ps1`: Logisim test vectors for 9 blocks (106 rows: every opcode in `MainControl`, every operation of the ALU, ...).
* `tests\run_cpu_tests.py --circuit all`: 7 programs on both CPUs against the reference simulator.
* `tests\fuzz.py`: random programs with many dependencies, same comparison.
* `tools\presentation_check.ps1`: runs all of these in short form and ends with `READY` or `NOT READY`.

---

## 8. Cheat sheet

| I see ... | It means ... |
|---|---|
| the PC goes back to 0x08 | the loop branch was taken (`branch_taken` = 1 just before) |
| the PC jumps to 0x2c and x1 = 0x20 | `jal`: call, return address saved |
| the PC goes from 0x30 to 0x20 | `ret`: return through x1 |
| pipeline: the PC stays for one tick | load-use stall (`stall` = 1 just before) |
| pipeline: `ForwardA/B` is not 00 | an operand was taken from a pipeline register |
| pipeline: `pc_src_ex` = 1, then `instr_id` = 0 | taken branch / jump: wrong-path instructions flushed |
| `x5 = x6 = 0` at the end of the hazard demo | the flush really cancelled them |
| `VERDICT ... exactly the reference result` in the proof | the circuits agree with the independent reference |
