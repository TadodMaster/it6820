# The complete guide: how this computer works

This guide explains **everything** in the project, starting from "what is a CPU" and ending with how the tests and the generator work.
All signal values shown are real: they were read from the running circuits with `tools/probe.py`.
Read it top to bottom once; later use the table of contents as a reference.

| Part | Content |
|---|---|
| [1](#1-what-a-computer-does) | what a CPU does, RISC-V in five minutes |
| [2](#2-the-project-at-a-glance) | the two CPUs, the files, how a Logisim project is organised |
| [3](#3-using-the-circuits-in-logisim) | step-by-step: load a program, run it, look inside |
| [4](#4-the-building-blocks-one-by-one) | every block: what it does, how it is built, why, how it is tested |
| [5](#5-following-instructions-through-the-single-cycle-cpu) | real signal values for `add`, `addi`, a taken branch, `lw`, `jal`, `ret` |
| [6](#6-the-memory-system) | RAM, byte / halfword access, `StoreMerge` explained with an example |
| [7](#7-the-pipelined-cpu) | why a pipeline, hazards, forwarding, stall, flush |
| [8](#8-watching-the-pipeline-a-real-trace) | a cycle-by-cycle trace of the pipeline |
| [9](#9-performance) | CPI, cycle counts, why the pipeline is not faster in cycles |
| [10](#10-writing-and-running-programs) | assembly language, the assembler, memory map |
| [11](#11-how-everything-is-tested) | the test strategy |
| [12](#12-how-to-extend-the-design) | adding instructions and features |
| [13](#13-troubleshooting) | problems and fixes |
| [14](#14-glossary) | words used in this project |

More detail: [REPORT.md](REPORT.md) (formal report), [TOOLS.md](TOOLS.md) (how the tools work inside), [DESIGN_LOG.md](DESIGN_LOG.md) (history and pitfalls).

---

## 1. What a computer does

A processor repeats one loop forever, the **fetch - decode - execute** cycle:

1. **Fetch**: read the next instruction (a 32-bit number) from the instruction memory at the address in the **program counter (PC)**.
2. **Decode**: look at the bit fields of the instruction: what operation, which registers, which constant.
3. **Execute**: do the operation (arithmetic, compare, address calculation).
4. **Memory**: for loads / stores, read or write the data memory.
5. **Write back**: store the result in a register.
6. Update the PC: normally `PC + 4` (instructions are 4 bytes), or a new address for a jump or taken branch.

Those five steps are the five stages IF, ID, EX, MEM, WB.  A *single-cycle* CPU does all of them in one clock cycle; a *pipelined* CPU
works on five different instructions at the same time, one per stage.

### RISC-V in five minutes
RISC-V is an open instruction set.  The base 32-bit integer set is called **RV32I**.  It has:

* **32 registers** `x0..x31`, each 32 bits.  `x0` always reads 0 and ignores writes.  The assembler also knows ABI names:

| Register | ABI name | Usual use |
|---|---|---|
| x0 | zero | constant 0 |
| x1 | ra | return address |
| x2 | sp | stack pointer |
| x3, x4 | gp, tp | global / thread pointer |
| x5-x7 | t0-t2 | temporaries |
| x8, x9 | s0 (fp), s1 | saved |
| x10-x17 | a0-a7 | arguments / results |
| x18-x27 | s2-s11 | saved |
| x28-x31 | t3-t6 | temporaries |

* **Instructions all have 32 bits** and six shapes (R, I, S, B, U, J).  The lowest 7 bits (`opcode`) say which shape.
  Register numbers are always in the same bit positions, which makes decoding cheap:

```
 31        25 24    20 19    15 14  12 11     7 6      0
 +-----------+--------+--------+------+--------+--------+
 |  funct7   |  rs2   |  rs1   |funct3|   rd   | opcode |   R-type   add rd, rs1, rs2
 +-----------+--------+--------+------+--------+--------+
 |      imm[11:0]     |  rs1   |funct3|   rd   | opcode |   I-type   addi rd, rs1, imm   lw rd, imm(rs1)
 +-----------+--------+--------+------+--------+--------+
 | imm[11:5] |  rs2   |  rs1   |funct3|imm[4:0]| opcode |   S-type   sw rs2, imm(rs1)
 +-----------+--------+--------+------+--------+--------+
 | imm[12|10:5] rs2   |  rs1   |funct3|imm[4:1|11]| opcode|  B-type   beq rs1, rs2, offset
 +--------------------+--------+------+--------+--------+
 |            imm[31:12]                |   rd   | opcode |   U-type   lui rd, imm20
 +--------------------------------------+--------+--------+
 |   imm[20|10:1|11|19:12]               |   rd   | opcode |   J-type   jal rd, offset
 +--------------------------------------+--------+--------+
```

* **Load / store architecture**: only `lw`, `sw` (and the byte / halfword versions) touch memory; arithmetic works on registers only.
* **Immediates** (constants inside the instruction) are sign-extended to 32 bits.  Branch and jump offsets are in bytes and always even.

Example: `addi x1, x0, 5` is `0x00500093`: `imm = 000000000101`, `rs1 = 0`, `funct3 = 000`, `rd = 1`, `opcode = 0010011`.

---

## 2. The project at a glance

```
RiscVComputer.circ
 |- main            single-cycle CPU   (the circuit that opens first)
 |- Pipeline        5-stage pipeline CPU
 |- InstructionDecode  MainControl  ImmGen  RegisterFile  ALUControl  ALU  BranchUnit
 |- Memory  (= RAM + LoadExtract + StoreMerge)
 |- ForwardingUnit  HazardUnit        (pipeline only)
```

Both CPUs are built from the **same blocks**; only the top-level wiring differs.  Both run the same machine code.
Memory is organised as a **Harvard** machine: a 256-word instruction ROM and a separate 256-word data RAM (1 KiB each).
Instructions cannot be fetched from the data RAM and a program cannot overwrite itself.

### How a Logisim project is organised
* Every box with a black title bar (`ALU`, `MainControl`, ...) is a **sub-circuit**: a circuit that is used like a chip.  Double-click it
  (Poke tool: click the magnifier) to look inside.
* A **tunnel** is a labelled stub (`rs1_data`, `alu_result`, ...).  **All tunnels with the same name in one circuit are connected**,
  without drawing a wire between them.  In this project every long connection is a tunnel; wires only appear between a pin and its tunnel.
* A **splitter** cuts a multi-bit wire into parts or merges parts into one wire (e.g. cutting `instr` into fields).
* A **register** stores a value on the rising clock edge when its enable is 1.
* Wire thickness and colour: thick = multi-bit bus, thin = 1 bit; green-ish = 1, dark = 0, blue = floating, red = conflict, orange = width mismatch.

### What each folder is for
| Folder | Purpose |
|---|---|
| `programs/` | assembly programs: `demo.s` (preloaded), `hazards_demo.s` |
| `tests/` | everything that checks the design |
| `tools/` | assembler / simulator, Java helpers, circuit generator |
| `docs/` | documentation (you are here) and pictures of every circuit (`docs/img`) |
| `backup/` | earlier versions of the `.circ` file |

---

## 3. Using the circuits in Logisim

1. Start: `java -jar logisim-evolution-4.1.0-all.jar RiscVComputer.circ` (Java **21** or newer).
2. Double-click `main` in the left tree.  The toolbar's hand icon is the **Poke tool** (click values to change them), the arrow is the Edit tool.
3. **Load a program.**  The instruction ROM already holds `programs/demo.s`.  To load another: `python tools\rv.py asm myprog.s -o myprog.hex`, then
   right-click the ROM, *Edit Contents...*, *Open...*, choose the `.hex` file.  (File format: first line `v2.0 raw`, then hex words.)
4. **Reset.**  Poke the `RESET` pin to 1 and back to 0.  RESET clears the PC register (it is the register's asynchronous clear input).  A freshly
   loaded project already starts with PC = 0 and all registers = 0.
5. **Step.**  `Simulate > Tick Full Cycle` = one complete clock cycle (rising edge + falling edge) = one instruction in the single-cycle CPU.
   `Ticks Enabled` free-runs the clock; `Simulate > Reset Simulation` (Ctrl+R) clears all registers and memories.
6. **Look at values.**  The PC register shows its value in its box.  Yellow ovals are probes (`instr`, `wb_data`).  To see the register file, use
   the Poke tool and click the **magnifier** on the `RegisterFile` box: registers are labelled `x0`..`x31` and show their value.  The same works for
   `Memory` (the RAM shows its contents when you click it, then *Edit contents* shows the table).
7. **Important:** inspect registers through the magnifier on the box *inside* `main` (or `Pipeline`).  If you open `RegisterFile` from the project tree
   you look at a separate, unused copy.

---

## 4. The building blocks one by one

For each block: **what it does**, **how it is built**, **why**, **how it is tested**.  Pictures are in `docs/img/<Block>.png`; open the circuit in
Logisim to see the same thing live.

### 4.1 InstructionDecode
*What:* splits the instruction into fields.  *How:* a single splitter.  Nothing is "decided" here: for an I-type instruction `rs2` is really part of
the immediate, but the splitter still outputs bits [24:20] as `rs2`; the control unit decides which fields matter.
`opcode = instr[6:0]`, `rd = [11:7]`, `funct3 = [14:12]`, `rs1 = [19:15]`, `rs2 = [24:20]`, `funct7 = [31:25]`.

### 4.2 MainControl
*What:* turns the `opcode` into the control signals.  *How:* nine comparators, each comparing the 7-bit opcode with one constant, give nine one-bit flags
(`IsR IsI IsLoad IsStore IsBranch IsLui IsAuipc IsJAL IsJALR`).  OR gates combine flags into the signals:

| Signal | Equation | Meaning |
|---|---|---|
| `RegWrite` | R + I + Load + LUI + AUIPC + JAL + JALR | the instruction writes `rd` |
| `ALUSrc` | I + Load + Store + LUI + AUIPC + JALR | ALU input B is the immediate |
| `MemWrite` | Store | |
| `MemRead` | Load | |
| `IsBranch`, `IsJAL`, `IsJALR` | the flags themselves | |
| `ALUOp` (2 bits) | `{R+I, I+Branch}` | 00 add, 01 subtract, 10 R-type, 11 I-type |
| `ImmSel` (3 bits) | `{JAL, Branch+LUI+AUIPC, Store+LUI+AUIPC}` | 000 I, 001 S, 010 B, 011 U, 100 J |
| `ASel` (2 bits) | `{LUI, AUIPC}` | 00 `rs1`, 01 PC, 10 zero |
| `WBSel` (2 bits) | `{JAL+JALR, Load}` | 00 ALU, 01 memory, 10 PC+4 |

*Why `ASel` / `WBSel`?*  `auipc` needs the PC as ALU input, `lui` needs 0 (so `0 + imm` gives the immediate), and `jal` / `jalr` must write `PC+4` to `rd`.
Adding two small selectors lets all of these reuse the normal ALU path.
*Test:* `tests/maincontrol.vec` checks the complete table for all nine opcodes and one unknown opcode.

### 4.3 ImmGen
*What:* builds the 32-bit immediate.  The immediate bits are **scrambled** in the instruction (so that `rs1`, `rs2`, `rd` stay in fixed places); ImmGen
unscrambles them:

| Type | Immediate | Built from |
|---|---|---|
| I | 12 bit | `instr[31:20]` |
| S | 12 bit | `instr[31:25]`, `instr[11:7]` |
| B | 13 bit (bit 0 = 0) | `instr[31]`, `[7]`, `[30:25]`, `[11:8]`, 0 |
| U | 32 bit | `instr[31:12]` followed by 12 zeros |
| J | 21 bit (bit 0 = 0) | `instr[31]`, `[19:12]`, `[20]`, `[30:21]`, 0 |

Then a bit extender copies the top bit to fill 32 bits (**sign extension**), so that `addi x1,x1,-1` adds `0xFFFFFFFF`.
An 8-input multiplexer (5 inputs used) picks the format by `ImmSel`.  *Test:* `immgen.vec`.

### 4.4 RegisterFile
*What:* 32 registers, two read ports (`rs1_data`, `rs2_data`) and one write port.  *How:* 32 register components; the **write** side is a 1-to-32
demultiplexer whose data input is `RegWrite` and whose select is `rd`, so only the register `rd` receives a write-enable (and only if `RegWrite = 1`).
All registers share `wb_data` and the clock.  The **read** side is two 32-to-1 multiplexers selected by `rs1` / `rs2`; they are *asynchronous*: change `rs1`
and `rs1_data` changes immediately.  Register `x0` has the constant 0 as its data input, so it always holds 0.
*Why asynchronous reads?* In the single-cycle CPU the value must reach the ALU in the same cycle.

### 4.5 ALU and ALUControl
*ALU:* computes all ten operations at the same time (adder, subtractor, AND, OR, XOR, three shifters, two comparators); a 16-to-1 multiplexer picks one
by `ALUCtrl`.  Shift amount = low 5 bits of B.  `SLT` / `SLTU` produce 0 or 1 (zero-extended).

| ALUCtrl | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| Operation | ADD | SUB | AND | OR | XOR | SLL | SRL | SRA | SLT | SLTU |

*ALUControl:* converts `(ALUOp, funct3, funct7)` to `ALUCtrl`.  Two-level decoding keeps the main control small:
`ALUOp = 00` forces ADD (loads, stores, address and jump calculations), `01` forces SUB, `10` decodes funct3 (and funct7 bit 5 for ADD/SUB and SRL/SRA),
`11` decodes funct3 for immediates (funct7 bit 5 only for SRLI / SRAI, because `addi` has no "sub" form).
*Tests:* `alu.vec`, `alucontrol.vec` (every operation, R and I form).

### 4.6 BranchUnit
*What:* decides if a conditional branch is taken.  *How:* an unsigned and a signed comparator give `a==b`, `a<u b`, `a<s b`; NOT gates give `!=`,
`>=u`, `>=s`; a multiplexer selected by `funct3` picks the condition; `branch_taken = IsBranch AND condition`.

| funct3 | 000 | 001 | 100 | 101 | 110 | 111 |
|---|---|---|---|---|---|---|
| instruction | beq | bne | blt | bge | bltu | bgeu |

*Test:* `branchunit.vec` (both directions of each condition, plus signed-vs-unsigned corner cases like `-1` versus `1`).

### 4.7 The next-PC logic (inside `main` / `Pipeline`)
```
pc_target   = PC + imm                          (branch and JAL target)
jalr_target = (rs1 + imm) with bit 0 cleared     (the ALU result, masked)
take_target = branch_taken OR IsJAL
next_pc     = IsJALR ? jalr_target : take_target ? pc_target : PC + 4
```
`jalr` clears bit 0 because the RISC-V specification says so (it lets software store flags in the low bit of a function pointer).

---

## 5. Following instructions through the single-cycle CPU

These are real values from `main` running `programs/demo.s` (read with `python tools/probe.py RiscVComputer.circ main programs/demo.s N <signals>`).

### 5.1 `add x10, x10, x11`  (R-type; `instr = 00b50533`, first loop iteration)
| Stage | Signals |
|---|---|
| Fetch | `pc = 8`, `instr = 00b50533`, `pc_plus4 = 0c` |
| Decode | `opcode = 33`, `rs1 = 0a (x10)`, `rs2 = 0b (x11)`, `rd = 0a`, `funct3 = 0`, `funct7 = 0` |
| Control | `RegWrite = 1`, `ALUSrc = 0`, `ALUOp = 10`, `ASel = 00`, `WBSel = 00`, `MemRead = MemWrite = 0` |
| Register read | `rs1_data = 0` (x10), `rs2_data = 0x0a` (x11 = 10) |
| Execute | `ALUCtrl = 0 (ADD)`, `alu_a = 0`, `alu_b = 0x0a`, `alu_result = 0x0a` |
| Write back | `wb_data = 0x0a` goes to x10 on the clock edge; `next_pc = 0c` |

### 5.2 `bnez x11, loop`  (= `bne x11, x0, loop`; `instr = fe059ce3`, taken)
`opcode = 63`, `imm = 0xfffffff8` (-8, the B-immediate), `IsBranch = 1`, `ALUOp = 01`, `rs1_data = 8` (x11), `rs2_data = 0`.  `BranchUnit`: `8 != 0` so
`branch_taken = 1`.  `pc_target = 0x10 + (-8) = 0x08` and `next_pc = 0x08`: the loop goes back to the `add`.  `RegWrite = 0`: nothing is written.

### 5.3 `lw x12, 0(x0)`  (`instr = 00002603`)
`imm = 0` (I-type), `alu_a = x0 = 0`, `alu_b = imm = 0`, `alu_result = 0` is the **address**.  `MemRead = 1`.  `Memory` returns `mem_rdata = 0x37` (55, stored earlier by
`sw`).  `WBSel = 01` selects the memory value: `wb_data = 0x37`, written to x12.

### 5.4 `jal x1, double`  (`instr = 010000ef`, at `pc = 0x1c`)
`imm = 0x10` (J-immediate).  `IsJAL = 1`, `take_target = 1`, `pc_target = 0x1c + 0x10 = 0x2c`, so `next_pc = 0x2c`.  `WBSel = 10`: `wb_data = pc_plus4 = 0x20` is written to `x1`
(`ra`), the return address.  The ALU is not needed.

### 5.5 `ret`  (= `jalr x0, 0(x1)`; `instr = 00008067`)
`rs1_data = 0x20` (ra), `imm = 0`, `alu_result = 0x20`, `jalr_target = 0x20`; `IsJALR = 1` makes `next_pc = jalr_target = 0x20`: execution continues after the call.
`rd = x0`, so the link value `wb_data = 0x34` is discarded (writes to x0 are ignored).

---

## 6. The memory system

### 6.1 Instruction ROM
256 words.  The PC counts bytes, so the ROM address is the **word index** `PC[9:2]` (the low two bits are always 0 because instructions are 4-byte aligned).

### 6.2 Data RAM
A Logisim RAM of 256 words x 32 bits, configured with **asynchronous read** (the data output follows the address immediately; required because a load must
deliver its value in the same cycle) and **one write enable** (the word is written on the rising clock edge).  The data address is split:

* `Address[9:2]` - word index into the RAM,
* `Address[1:0]` - byte position inside the word (little endian: byte 0 is bits 7:0).

Addresses above 1023 wrap around (only 10 address bits are used).

### 6.3 Loads: `LoadExtract`
The RAM always outputs the whole word.  `LoadExtract` takes the part the instruction wants:

| funct3 | instruction | result |
|---|---|---|
| 000 | `lb` | byte selected by `Address[1:0]`, sign-extended |
| 100 | `lbu` | the same byte, zero-extended |
| 001 | `lh` | halfword selected by `Address[1]`, sign-extended |
| 101 | `lhu` | halfword, zero-extended |
| 010 | `lw` | the whole word |

Example: word `0x8899AABB`, `lb` at byte 1 gives `0xFFFFFFAA`, `lbu` gives `0x000000AA`, `lh` at the upper half gives `0xFFFF8899`.

### 6.4 Stores: `StoreMerge`
The RAM can only write a whole word.  For `sb` / `sh` the circuit therefore reads the old word, replaces the written bytes and writes the whole word back
(a **read-modify-write**, all within one cycle).  Because the RAM read is asynchronous this needs no extra cycle.

A small 16-row ROM turns `{size, Address[1:0]}` into four **byte enables**:

| size / address | byte enables (lane 3..0) |
|---|---|
| byte, offset 0 / 1 / 2 / 3 | 0001 / 0010 / 0100 / 1000 |
| halfword, offset 0-1 / 2-3 | 0011 / 1100 |
| word | 1111 |

Four 8-bit multiplexers choose per byte lane: enabled -> the new byte, otherwise the old byte.  Which byte of `write_data` lands in a lane depends on the size
(for `sb` always `write_data[7:0]`; for `sh` the low half; for `sw` the matching byte).  Example: old word `0x11223344`, `write_data = 0xAABBCCDD`:
`sb` at offset 1 gives `0x1122DD44`; `sh` at offset 2 gives `0xCCDD3344`; `sw` gives `0xAABBCCDD`.  (These are rows of `tests/storemerge.vec`.)

Misaligned accesses (e.g. `lw` at address 2) are not supported: the hardware silently uses the aligned word.

---

## 7. The pipelined CPU

### 7.1 Why
In the single-cycle CPU the clock period must cover the *whole* path (fetch + decode + ALU + memory + write back).  In a pipeline each stage is separated by registers, so the clock
only has to cover the *slowest stage*; at best one instruction finishes every cycle.  (Logisim does not model gate delays, so you see the same number of cycles but not the faster clock.)

```
cycle:        1    2    3    4    5    6    7    8
instr 1       IF   ID   EX   MEM  WB
instr 2            IF   ID   EX   MEM  WB
instr 3                 IF   ID   EX   MEM  WB
instr 4                      IF   ID   EX   MEM  WB
```

### 7.2 The pipeline registers
Every value that is still needed in a later stage must travel with the instruction through registers between the stages:

| Between | Registers |
|---|---|
| IF / ID | `pc_id`, `instr_id` |
| ID / EX | `pc_ex`, `rs1_data_ex`, `rs2_data_ex`, `imm_ex`, `rs1_ex`, `rs2_ex`, `rd_ex`, `funct3_ex`, `funct7_ex`, `ctrl_ex` |
| EX / MEM | `alu_result_mem`, `store_data_mem`, `pc_plus4_mem`, `rd_mem`, `funct3_mem`, `ctrl_mem` |
| MEM / WB | `alu_result_wb`, `mem_rdata_wb`, `pc_plus4_wb`, `rd_wb`, `ctrl_wb` |

The control signals are decoded **once**, in ID.  They travel with the instruction as a **control word**: 13 bits in ID/EX (`RegWrite ALUSrc MemWrite MemRead IsBranch ALUOp[2] ASel[2] WBSel[2] IsJAL IsJALR`), 5 bits in EX/MEM,
3 bits in MEM/WB (each stage drops the bits it no longer needs).  A splitter packs the bits before a register and another unpacks them after it.
An all-zero control word is a **NOP / bubble**: it writes nothing.

### 7.3 A trick: the register file writes on the falling edge
WB and ID both use the register file in the same cycle.  If an instruction in WB writes `x5` while the instruction 3 behind it reads `x5` in ID, the reader must see the **new** value.  The register file's clock is `CLK_n` (the inverted clock):
it writes in the first half of the cycle and ID reads in the second half.

### 7.4 Hazards
A *hazard* is a situation where simply flowing instructions through the stages would give a wrong result.

**Data hazard (read after write).**  `add x1,x2,x3` followed by `sub x4,x1,x5`: `sub` reads `x1` in ID while `add` has not written it yet.  Solution: **forwarding**.  The value exists after the EX stage of the `add`; it is
sent straight back to the input of the ALU of the following instruction.  `ForwardingUnit` compares the source registers of the instruction in EX with the destination registers of the two instructions ahead:

| Condition (for operand A with `rs1_ex`) | `ForwardA` | Source |
|---|---|---|
| `RegWrite_mem` and `rd_mem != 0` and `rd_mem == rs1_ex` | 10 | EX/MEM (`fwd_mem_val`) |
| else `RegWrite_wb` and `rd_wb != 0` and `rd_wb == rs1_ex` | 01 | MEM/WB (`wb_data`) |
| otherwise | 00 | value read from the register file |

The younger result (EX/MEM) wins when both match.  The register `x0` is never forwarded (`rd != 0`).  Details that matter:
* `fwd_mem_val` is the ALU result, **except** for `jal` / `jalr`, where the result is `PC+4`.
* The same forwarded value is the data of a store and the input of the branch comparison.
* `ForwardA/B` can show 1 or 2 for instructions that do not use `rs1`/`rs2` (the fields are just immediate bits); this is harmless because the mux output is not used.

**Load-use hazard.**  `lw x2,0(x0)` followed by `addi x3,x2,1`: the data of a load exists only at the end of MEM, one stage too late for forwarding.  `HazardUnit` detects
`MemRead_ex and rd_ex != 0 and (rd_ex == rs1_id or rd_ex == rs2_id)` and raises `stall`.  Then PC and IF/ID keep their value for one cycle (`run = not stall` drives their enables) and the control word entering ID/EX
is replaced by zeros (a bubble).  One cycle later the data can be forwarded from MEM/WB.

**Control hazard.**  A branch is decided in EX, but two more instructions have already been fetched.  If the branch is taken (`pc_src_ex = branch_taken or IsJAL or IsJALR`), `Pipeline`
* loads the target into the PC,
* replaces the instruction being fetched by 0 (`instr_in = 0`),
* zeros the control word entering ID/EX (the `bubble` signal is `stall or pc_src_ex`).

So a taken branch / jump costs **2 cycles**; a not-taken branch costs nothing (the pipeline "predicts not taken").  An all-zero instruction word is a safe NOP because opcode 0 matches no instruction class.

**No structural hazards**, because instructions and data use separate memories and the register file has separate read and write ports.

---

## 8. Watching the pipeline: a real trace

`programs/hazards_demo.s`:

```
0000  li   x1, 100
0004  sw   x1, 0(x0)
0008  lw   x2, 0(x0)          # load ...
000c  addi x3, x2, 1          # ... used by the next instruction: load-use stall
0010  add  x4, x3, x2         # forwarding
0014  beq  x4, x4, skip       # taken: flush
0018  addi x5, x0, 1
001c  addi x6, x0, 2
0020  skip: addi x7, x0, 7
0024  halt: j halt
```

Command: `python tools\probe.py --trace RiscVComputer.circ Pipeline programs\hazards_demo.s 12 pc_if pc_id pc_ex stall pc_src_ex ForwardA ForwardB`
Row *n* = the state after clock cycle *n* (`pc_if`, `pc_id`, `pc_ex` = the instruction in IF, ID, EX).  Real output:

```
cycle  pc_if  pc_id  pc_ex  stall pc_src_ex ForwardA ForwardB
    3   000c   0008   0004      0         0        0        2
    4   0010   000c   0008      1         0        0        0     <- lw in EX, addi in ID: stall
    5   0010   000c   000c      0         0        2        0     <- PC and IF/ID held; EX holds the bubble (pc_ex is stale, control = 0)
    6   0014   0010   000c      0         0        1        0     <- addi now in EX: x2 forwarded from MEM/WB (lw is in WB): ForwardA = 1
    7   0018   0014   0010      0         0        2        0     <- add in EX: x3 from EX/MEM (ForwardA = 2); x2 is already in the register file
    8   001c   0018   0014      0         1        2        2     <- beq in EX: x4 forwarded for both operands; taken -> pc_src_ex = 1
    9   0020   001c   0018      0         0        0        0     <- 0018 and 001c are bubbles; fetch continues at skip
```

How to read it:
* **Cycle 4**: the `lw` (`pc_ex = 8`) has `MemRead` and the `addi` in ID (`pc_id = c`) needs `x2` -> `stall = 1`.
* **Cycle 5**: `pc_if` and `pc_id` did not move (held for one cycle).  The stage EX now holds the **bubble**: only its control word is zero, so `pc_ex` still shows the stale value `c`.
* **Cycle 6**: the `addi` is really in EX; the `lw` is in WB, so `x2` comes from MEM/WB (`ForwardA = 1`).  Without the stall it would have been needed one cycle earlier, when the value did not exist yet.
* **Cycle 7**: the `add` needs `x3` (result of the `addi`, now in MEM): `ForwardA = 2` (EX/MEM).  `x2` was already written to the register file, so `ForwardB = 0`.
* **Cycle 8**: `beq` in EX decides *taken*: `pc_src_ex = 1`.  The next cycle the fetch is at `0x20` (`skip`); `0x18` and `0x1c` were fetched but never take effect: `x5` and `x6` stay 0, and the result is `x7 = 7`.

---

## 9. Performance

* **CPI** (cycles per instruction) = cycles / instructions.  Single-cycle: exactly 1.  Pipeline: 1 + the average stalls and flushes.
* **Execution time** = instructions x CPI x clock period.  The pipeline has a higher CPI but a shorter clock period, so in a real implementation it is faster.  Logisim simulates in "ticks", not nanoseconds, so only the CPI is visible here.

Measured (cycles until the PC reaches the final `halt: j halt`):

| program | instructions | single-cycle | pipeline | pipeline CPI |
|---|---|---|---|---|
| alu | 92 | 91 | 91 | 0.99 |
| mem | 70 | 69 | 70 | 1.00 |
| hazard | 68 | 67 | 79 | 1.16 |
| jump | 28 | 27 | 35 | 1.25 |
| branch | 70 | 69 | 101 | 1.44 |
| fib | 124 | 123 | 178 | 1.44 |
| demo | 40 | 39 | 61 | 1.52 |

(The numbers count to the point where the halt instruction is *fetched*, so they are 1 below the instruction count for straight-line code.)
Measured penalties: forwarding 0, load-use 1, taken branch / jal / jalr 2, not-taken branch 0.
Why loops are expensive: `demo` has a 3-instruction loop with one taken branch per iteration: 3 instructions cost 5 cycles.
How to improve: resolve `jal` in ID (penalty 1), add a branch predictor / branch target buffer, or compute branches in ID with extra forwarding.

---

## 10. Writing and running programs

### 10.1 Assembly syntax (`tools/rv.py`)
```
        li   x10, 0            # comments start with # or ;
loop:   add  x10, x10, x11     # labels end with a colon
        addi x11, x11, -1
        bnez x11, loop
        sw   x10, 0(x0)        # offset(register)
halt:   j    halt              # end of program: jump to itself
        .word 0x12345678       # raw data word in the instruction stream
```
* Registers: `x0..x31` or ABI names (`zero ra sp t0 a0 s1 ...`).  Numbers: decimal, `-5`, or hex `0x1F`.
* **Pseudo instructions** (expanded by the assembler): `nop`, `li rd,imm` (1 or 2 instructions), `mv`, `not`, `neg`, `seqz`, `snez`, `j`, `jr`, `ret`, `call`, `beqz`, `bnez`, `bltz`, `bgez`, `blez`, `bgtz`, `bgt`, `ble`, `bgtu`, `bleu`.
* `chk rd, value` (used by the tests): `li x30, value` then `bne rd, x30, fail`; it needs a label `fail:` and uses register `x30`.
* The program ends with an endless loop; the test tools detect "jump to itself" as the end.

### 10.2 Commands
```powershell
python tools\rv.py asm prog.s -o prog.hex -l     # assemble, print a listing (address, machine code, source)
python tools\rv.py sim prog.s                    # run on the reference simulator and print the registers
```
`-l` prints lines like `0008: 00b50533  loop:   add  x10, x10, x11`.

### 10.3 Memory map
| Region | Addresses | Notes |
|---|---|---|
| instruction ROM | 0x000 - 0x3FF | 256 words, read only, addressed by `PC[9:2]` |
| data RAM | 0x000 - 0x3FF | 256 words, a *different* memory with the same addresses; wraps after 1 KiB |
| no I/O | - | no memory-mapped devices (an optional extension) |

Registers start at 0.  There is no stack pointer initialisation: set `sp` yourself if you need one (`li sp, 0x3F0`).

---

## 11. How everything is tested

The design principle: **an independent oracle**.  The reference simulator in `tools/rv.py` was written separately from the circuits, so a bug has to be made twice to go unnoticed.

| Level | Command | What it proves |
|---|---|---|
| Module | `powershell -File tests\run_tests.ps1` | each block gives the right output for chosen inputs (Logisim "test vectors": a text table of inputs and expected outputs) |
| Program | `python tests\run_cpu_tests.py --circuit all` | complete programs give the same registers and memory as the simulator, on both CPUs |
| Random | `python tests\fuzz.py --count 20` | the same for random programs that stress hazards |

Details:
* **Test vector files** (`tests/*.vec`): first line = pin names with widths (`rs1_data[32] ALU_Ctrl[4] result[32]`), then one row per test: `0x00000005 0x7 0x0 0x0000000C`.  Values with `0x` are hex, without are binary.
* **Self-checking programs** (`tests/programs/*.s`): each result is compared with a hand-computed constant by `chk`; at the end `x31 = 0x600D` ("good") or `0xDEAD`.  They do not depend on the simulator.
* **Full-state comparison**: after the run the test reads all 32 registers and every non-zero RAM word from the circuit (via the Java runner) and compares with the simulator.
* **Fuzzer**: generates programs of ~70 instructions with only registers `x1..x7`, so almost every instruction depends on a recent one.  It mixes ALU ops, all load / store sizes, forward branches, `jal`, `jalr`, `lui`, `auipc`.
  Failing programs are saved in the temp folder for debugging.

What the tests do **not** cover: timing (Logisim has no gate delays), misaligned accesses, `fence` / `ecall` / `ebreak`, programs longer than 256 instructions.

---

## 12. How to extend the design

**Add an R-type instruction** (e.g. a new ALU op): (1) add the operation to `ALU` and give it an `ALUCtrl` number (the multiplexer has 16 inputs, 6 free); (2) teach `ALUControl` the funct3 / funct7 combination;
(3) add the instruction to `tools/rv.py` (`R_OPS`) and to the simulator `alu()`; (4) add rows to `alu.vec`, `alucontrol.vec` and a test program; (5) rebuild.

**Add a new instruction class** (new opcode): add a comparator and flag in `MainControl` (`tools/build/blocks.py`), decide the signals, and extend `tests/maincontrol.vec`.

**Change a generated circuit**: edit the Python description in `tools/build/` (`blocks.py` for blocks, `cpus.py` / `pipeline.py` for the two CPUs) and run
`python tools\build\build_all.py tools\build\base.circ RiscVComputer.circ`.  The generator verifies the result.  The hand-drawn blocks (`ALU`, `InstructionDecode`, `RegisterFile`,
`ImmGen`, `ALUControl`) live in `tools/build/base.circ`: edit them in Logisim, save, copy the file there.

**Ideas, cheapest first**: resolve `jal` in ID; a branch predictor; a memory-mapped UART for `printf`-style output; an `M` extension (a multiplier is one combinational block, a divider needs a multi-cycle unit and a stall signal like the load-use stall).

---

## 13. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Logisim does not start; `UnsupportedClassVersionError ... 65.0` | Java older than 21.  Install JDK 21 and use its `java.exe`. |
| PC or registers show `xxxxxxxx` / red `E` after loading | a value is undefined: press Ctrl+R (reset simulation); make sure `RESET` is 0 while running |
| nothing happens when ticking | `Simulate > Ticks Enabled` is off and you did not use *Tick Full Cycle*; or the clock tool is not the poke tool |
| registers do not change | you opened `RegisterFile` from the project tree; use the magnifier inside `main` / `Pipeline` |
| program runs but results are wrong | assemble with `-l` and compare with `python tools\rv.py sim`; check that the ROM really holds your program (*Edit Contents*) |
| ROM is empty after *Open* | the file must start with the line `v2.0 raw`; `rv.py asm` writes it |
| `could not find or load main class Run` | run `powershell -File tools\compile.ps1` (needs the JDK, not only the JRE) |
| `no register labelled PC` | the circuit name is wrong (use `main` or `Pipeline`) |
| test runner prints `circuit run failed` | the java used is not 21: set `$env:JAVA = "C:\Program Files\Java\jdk-21.0.12.1\bin\java.exe"` |
| `tests\run_tests.ps1` says `no result` | same cause, or the circuit file has an error: open it in Logisim to read the message |
| regenerated file differs in layout | the generator searches for the tightest layout; sizes may change slightly when fonts or sizes change |

---

## 14. Glossary

| Word | Meaning |
|---|---|
| ALU | arithmetic logic unit, the block that computes |
| Bubble | a NOP travelling through the pipeline |
| Control word | the packed control signals that travel with an instruction in the pipeline |
| CPI | cycles per instruction |
| Datapath | the wires and blocks that carry the data |
| Flush | cancel the instructions behind a taken branch |
| Forwarding | sending a result directly to the unit that needs it, before it is written to a register |
| funct3 / funct7 | extra opcode bits that select the operation inside one opcode |
| Harvard | separate instruction and data memories |
| Hazard | a situation in which the pipeline would give a wrong result |
| Immediate | a constant stored inside the instruction |
| NOP | an instruction that does nothing (`addi x0,x0,0`, or an all-zero control word) |
| PC | program counter, the address of the instruction being fetched |
| Probe | a Logisim component that shows a value (the yellow oval) |
| Reference simulator | the Python simulator `tools/rv.py sim`, used as the oracle for the tests |
| Sign extension | widening a number by copying its top bit |
| Splitter | Logisim component that cuts / merges buses |
| Stall | holding the front of the pipeline for a cycle |
| Test vector | a table of inputs and expected outputs for one circuit |
| Tunnel | a named wire end; same name = connected |
