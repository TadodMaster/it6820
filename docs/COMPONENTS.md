# Components: configuration and why we use them

This page explains every **kind of Logisim component** used in the project: what it is, **which settings we use and why**, where it appears, and the
traps we fell into.  For the exact configuration of every single component in every circuit see [BOM.md](BOM.md) (generated from the real file).
For how the blocks work together see [GUIDE.md](GUIDE.md).

In the circuit file the settings are stored as attributes (`<a name="width" val="32"/>`).  The tables below give both the **file name**
and the **name shown in Logisim's attribute panel** (select a component with the arrow tool; its settings appear at the bottom left).
All "default" values were read from Logisim 4.1.0 itself.

Contents: [0 Project-wide settings](#0-project-wide-settings) - [1 State](#1-state-register-ram-rom) - [2 Selecting](#2-selecting-and-routing-multiplexer-demultiplexer-splitter) -
[3 Arithmetic](#3-arithmetic-and-comparison-adder-subtractor-comparator-shifter-bit-extender) - [4 Logic gates](#4-logic-gates) - [5 Wiring and I/O](#5-wiring-and-io-constant-pin-tunnel-probe-clock-text) -
[6 Sub-circuits](#6-sub-circuits) - [7 Design decisions](#7-design-decisions-why-this-and-not-that) - [8 Recipes](#8-recipes-to-build-a-component-by-hand)

---

## 0. Project-wide settings

| Setting | Value | Where | Why |
|---|---|---|---|
| Logisim version | 4.1.0 (Java 21+) | file header `source="4.1.0"` | the version the group installed |
| Gate output when undefined (`gateUndefined`) | `ignore` | Project > Options > Simulation | unconnected gate inputs are ignored instead of producing an error value |
| Iteration limit (`simlimit`) | 1000 | same | steps before Logisim reports "oscillation"; the CPUs settle in far fewer, so a real loop would be caught quickly |
| Noise on component delays (`simrand`) | 0 (off) | same | the simulation must be deterministic so that tests are repeatable |
| Grid | 10 px | fixed by Logisim | all components and wires must sit on it; off-grid items are *moved* when the file is loaded and the wires then miss the pins |
| Font | `Monospaced` | every text and label | requested for the documentation / demo; applied by `tools/build/fonts.py` |
| Clock | one `Clock` per CPU, high 1 tick / low 1 tick (defaults) | `main`, `Pipeline` | a full cycle = 2 ticks (rising edge + falling edge); `Simulate > Tick Full Cycle` does both.  The clock is stepped by hand, so its frequency is irrelevant |
| Libraries in use | Wiring, Gates, Plexers, Arithmetic, Memory, Base | project tree | the other libraries in the file (I/O, TTL, FP, ...) are just Logisim's default template and are not used |
| Data width | 32 bits everywhere in the datapath; 5 bits for register numbers, 3 for `funct3`, 7 for `opcode` / `funct7` | | RV32I |
| Reset | pin `RESET` (default 0) drives the *clear* input of the PC register | `main`, `Pipeline` | puts PC at 0 without resetting the whole simulation |

---

## 1. State: Register, RAM, ROM

### Register
A register stores a value on the **rising clock edge** when its enable is 1.

| File name | GUI name | Value used | Default | Why |
|---|---|---|---|---|
| `width` | Data Bits | 32 (PC, register file); 5, 3, 7, 13 for pipeline fields | 8 | one register per field, sized to the field (5 = register number, 3 = `funct3`, 7 = `funct7`, 13 = control word) |
| `trigger` | Trigger | Rising Edge | rising | all state changes on the rising edge, so everything updates "at the same time" |
| `appearance` | Appearance | `logisim_evolution` | same | draws the pin names D, Q, WE, clk, R on the box: easier to read than the plain classic box |
| `label` | Label | `PC`, `x0`..`x31`, pipeline names | none | the test runner finds the PC and registers by label; the pipeline labels name the stage registers |
| `labelvisible` | (label shown) | true for pipeline registers | false | shows `pc_ex`, `alu_result_mem`, ... above each register in the Pipeline picture |

Pins: **D** data in, **Q** data out, **WE** enable, **clk**, **R** asynchronous clear.
* WE: tied to constant 1 when the register always loads; tied to `run` (= not stall) for the PC and IF/ID registers, which must *hold* during a load-use stall.
* R: only the PC uses it (`RESET`).  An unconnected R is treated as 0 (no clear).
* Registers power up with 0.  The pipeline registers therefore start as bubbles (instruction 0 = NOP).
* In the pipeline the register file's clock pin receives the **inverted clock** (`CLK_n`), so its registers load on the *falling* edge of `CLK`.

Used: PC (1), register file (32 x 32 bit), pipeline registers (23).

### RAM (data memory) - the most delicate setting
| File name | GUI name | Value used | Default | Why |
|---|---|---|---|---|
| `addrWidth` | Address Bit Width | 8 | 8 | 256 words |
| `dataWidth` | Data Bit Width | 32 | 8 | one RV32 word |
| `asyncread` | Asynchronous read | **true** | false | a load must deliver data in the same cycle in which the address is applied.  With the default (synchronous) read the data appears only after the next clock edge, so every load returned undefined data in the original project |
| `enables` | Enables | **line** (Use line enables) | byte | line mode has one write-enable pin and a clock; byte mode needs one enable per byte.  Sub-word stores are done in `StoreMerge` instead, which is simpler and testable |
| `databus` | Data bus implementation | separate (default, called `bibus` in the file) | separate | separate data-in / data-out pins: no bidirectional bus, so no contention |
| `type` | Ram type | volatile | volatile | contents are lost on reset (all zero at start) |
| `trigger` | Trigger | rising | rising | the write happens on the rising edge |
| `appearance` | Appearance | `classic` | `logisim_evolution` | the classic symbol is 240 x 154 px; the other one is 730 px tall (it shows the contents) |

Pins in line mode: `addr`, `dout` (always enabled: there is no OE pin in this mode), `din`, `we`, `clk`.
Because `dout` is always on, `StoreMerge` can read the old word while preparing the new one.
Used once, in `Memory`.

### ROM (instruction memory and one lookup table)
| File name | GUI name | Instruction ROM | Byte-enable table | Why |
|---|---|---|---|---|
| `addrWidth` | Address Bit Width | 8 | 4 | 256 words, 16 rows |
| `dataWidth` | Data Bit Width | 32 | 4 | instruction / four enable bits |
| `contents` | Contents | the program | `1 2 4 8 3 3 c c f f f f f f f f` | loaded by the build; changed in the GUI with *Edit Contents* |
| `appearance` | Appearance | classic | classic | compact |

Why a ROM for the byte enables: the 16 combinations of `{size, address[1:0]}` are a truth table; a 16-row ROM is the shortest correct way to write it down and the contents are readable
(`1 2 4 8` = single bytes, `3 3 c c` = halfwords, `f` = word).  Why a ROM for the program: instruction memory is read-only and read combinationally with the PC.

---

## 2. Selecting and routing: Multiplexer, Demultiplexer, Splitter

### Multiplexer
A multiplexer copies one of its `2^select` inputs to the output.

| File name | GUI name | Default | Notes |
|---|---|---|---|
| `select` | Select Bits | 1 | number of select bits: inputs = 2^select |
| `width` | Data Bits | 1 | width of every data input and of the output |
| `enable` | Include Enable? | no | never used |
| `facing`, `size`, `selloc`, `disabled` | Facing, Gate Size, Select Location, Disabled Output | east, 40, bottom-left, 0 | defaults |

The select pin is on the bottom edge, the data inputs on the left, numbered from the top (input 0 is the top one).

| Where | select / width | Selects |
|---|---|---|
| ALU result | 4 / 32 (16 inputs, 10 used) | one of the 10 operations by `ALUCtrl` |
| Register file read ports (2) | 5 / 32 | register `rs1` / `rs2` |
| ALU operand A | 2 / 32 | `rs1`, PC, 0 (by `ASel`) |
| ALU operand B | 1 / 32 | `rs2` or immediate (by `ALUSrc`) |
| Write-back | 2 / 32 | ALU, memory, PC+4 (by `WBSel`) |
| Next PC | 1 / 32 (two in series) | `PC+4` / `pc_target` / `jalr_target` |
| ImmGen | 3 / 32 (8 inputs, 5 used) | I, S, B, U, J immediate |
| ALUControl | 3 / 4 (several) | decode of `funct3` into an `ALUCtrl` code |
| BranchUnit | 3 / 1 | comparison selected by `funct3` |
| LoadExtract | 2 / 8, 1 / 16, 3 / 32 | byte, halfword, final result by `funct3` |
| StoreMerge | 2 / 8 (3), 1 / 8 (4) | byte source per lane, old / new byte per lane |
| Pipeline | 2 / 32 (forwarding A and B), 1 / 32 (forwarded memory value, flush of the fetched instruction), 1 / 13 (bubble in the control word) | |

Settings that matter: **width must equal the width of the buses** connected (a mismatch shows as an orange wire); unused data inputs may stay unconnected, because only the selected input reaches the output.
Why muxes and not tri-state buses: no contention, the data flow is visible, the simulation is deterministic.

### Demultiplexer
Sends its data input to **one** of `2^select` outputs; the others output 0 (`Disabled Output` = 0, the default).

| Setting | Value | Why |
|---|---|---|
| Select Bits | 5 | 32 outputs, one per register |
| Data Bits | 1 (default) | the data input is `RegWrite`, a single bit |
| Three-state | no | unselected outputs are driven to 0, not floating |

Used once: `RegisterFile`.  Input = `RegWrite`, select = `rd`, output *i* = write enable of register *i*.  When `RegWrite = 0` every write enable is 0.
A plain decoder would also work but would need an extra AND with `RegWrite` per output.

### Splitter
Cuts a wide bus into parts or merges parts into one bus.

| File name | GUI name | Notes |
|---|---|---|
| `incoming` | Bit Width In | width of the combined bus |
| `fanout` | Fan Out | number of parts |
| `bitN` | Bit N | which part bit N goes to (one setting per bit) |
| `facing` | Facing | **east**: bus on the left, parts on the right (splitting); **west**: bus on the right, parts on the left (merging) |
| `spacing` | Spacing | 3 in all generated circuits = 30 px between pins (default 1 = 10 px) |

Uses: cutting an instruction into fields (`fanout 6`), `PC[9:2]` (`fanout 3`: bits 1:0 / 9:2 / 31:10), address into byte offset and word index, packing and unpacking the pipeline control word
(`fanout 10`, `13` bits wide), building 2- / 3-bit buses out of single signals (`ALUOp`, `ImmSel`, `ASel`, `WBSel`), the four byte lanes of a word.
Why `spacing 3`: with 10 px between pins there is no room to attach a labelled tunnel to each one.

---

## 3. Arithmetic and comparison: Adder, Subtractor, Comparator, Shifter, Bit Extender

### Adder
`Data Bits` = 32.  Inputs A, B, carry-in; outputs sum, carry-out.  Carry-in and carry-out are **left unconnected**; an unconnected carry-in counts as 0 (the tests prove it).
Used: `PC + 4`, `PC + imm` (branch / JAL target), the ALU's ADD.

### Subtractor
`Data Bits` = 32; computes A - B (the borrow pins are left open).  Used once: the ALU's SUB.  Why a separate subtractor and not "adder with inverted B": it is clearer and costs nothing in Logisim.

### Comparator
Outputs three bits: A > B, A = B, A < B.

| File name | GUI name | Values | Notes |
|---|---|---|---|
| `width` | Data Bits | 32, 7, 5 | 32 for data, 7 for the opcode, 5 for register numbers |
| `mode` | Numeric Type | `unsigned` or two's complement (default) | **the signedness matters for 32-bit data**: SLT and `blt` / `bge` use two's complement, SLTU and `bltu` / `bgeu` use unsigned.  For opcode and register-number compares it is irrelevant; unsigned is used |

Used: 9 opcode comparators in `MainControl`; ALU (SLT signed, SLTU unsigned); `BranchUnit` (one of each); register-number compares in `ForwardingUnit` and `HazardUnit`.

### Shifter
| File name | GUI name | Values | Why |
|---|---|---|---|
| `width` | Data Bits | 32 | |
| `shift` | Shift Type | `ll` (logical left, default), `lr` (logical right), `ar` (arithmetic right) | one shifter of each type for SLL, SRL, SRA |

The shift amount input is 5 bits wide (`B[4:0]`), which is what RISC-V specifies.

### Bit Extender
Widens a bus.

| File name | GUI name | Values | Used for |
|---|---|---|---|
| `in_width` / `out_width` | Bit Width In / Out | 12, 13, 21 -> 32; 8, 16 -> 32; 1 -> 32 | immediates, loaded byte / halfword, SLT result |
| `type` | Extension Type | `sign` (default) or `zero` | **sign** for immediates and for `lb` / `lh`; **zero** for `lbu` / `lhu` and for the 1-bit SLT / SLTU result (a comparison result is 0 or 1, never -1) |

(One of the original bugs: the SLTU extender was *sign* and returned `0xFFFFFFFF` instead of 1.)

---

## 4. Logic gates

| Gate | Settings | Used |
|---|---|---|
| AND, OR, XOR | `width` (Data Bits): 32 makes a bit-wise gate for the ALU; `inputs` (Number Of Inputs): 2 default, 3 for the OR trees of `MainControl` | ALU AND / OR / XOR (32 bit); JALR address mask (32-bit AND with `0xFFFFFFFE`); control equations; hazard / forwarding conditions |
| NOT | none | inverted clock `CLK_n`; `!=`, `>=` conditions; "not stall" |

Why OR trees of at most 3 inputs: a wide OR gate has input pins only 10 px apart, which leaves no room for labels; two small gates are easier to read.  Gate size is left at the default.
The option `gateUndefined = ignore` (section 0) makes unused inputs harmless.

---

## 5. Wiring and I/O: Constant, Pin, Tunnel, Probe, Clock, Text

### Constant
| File name | GUI name | Default | Notes |
|---|---|---|---|
| `value` | Value | **1** | **trap**: the default is 1, not 0, and Logisim does not write the default into the file, so a constant without a `value` line *is* a one (in [BOM.md](BOM.md) such constants are marked).  A "zero" constant that was not given `value=0x0` made `lui` compute `x+1` once |
| `width` | Data Bits | 1 | must match the bus |

Used: opcode constants (7 bit, `MainControl`), `ALUCtrl` codes (4 bit, 19 in `ALUControl`), `0`, `4`, `0xFFFFFFFE` (32 bit), register number 0 (5 bit), the 12 zero bits of the U-immediate, the all-zero control word.

### Pin
Input and output pins define the interface of a circuit.

| File name | GUI name | Values | Why |
|---|---|---|---|
| `type` | Type | input (default) / `output` | |
| `width` | Data Bits | 1..32 | |
| `label` | Label | the name of the signal | **becomes the pin name on the sub-circuit box** |
| `radix` | Radix | 16 for 32-bit data pins (default 2) | readable values when poking |
| `facing` | Facing | east for inputs, west for outputs (hand-drawn blocks also use north / south) | |
| `appearance` | Appearance | classic | rectangular pin showing the value |
| `initial` | Reset value | 0 (default) | `RESET` therefore starts at 0 |

The **order of the pins** inside a circuit decides their order on the box: inputs on the left sorted from top to bottom, outputs on the right.  The generated circuits place their pins in a column in the desired order.

### Tunnel
A labelled wire end; all tunnels with the same label in one circuit are connected.

| File name | GUI name | Value | Why |
|---|---|---|---|
| `label` | Label | the signal name | case sensitive |
| `width` | Data Bits | = width of the net | **must equal the bus width** (default 1), otherwise the wire is orange |
| `facing` | Facing | west (box on the right of the wire end) or east (box on the left) | the label box extends away from the component |

Why tunnels instead of wires: a CPU has hundreds of connections; long wires cross and become unreadable.  A tunnel is a *name*, and names are what the report and the guide talk about.
There are about 900 tunnels in the project.  The generator puts one tunnel on every pin that needs a connection.

### Probe
`radix` = 16 and `label` = `instr`, `wb_data` (and one inside the ALU).  Shows a value without being part of the logic (yellow oval).  Not needed for function, useful for demos.

### Clock
`High Duration` = `Low Duration` = 1 tick, `Phase Offset` 0 (all defaults).  One per CPU; its output is the `CLK` tunnel that feeds PC, pipeline registers, RAM and (inverted) the register file.

### Text
Annotation only (title, explanations, tables).  Font `Monospaced`.  About 200 texts in the project; they do not affect the circuit.

---

## 6. Sub-circuits

A circuit used as a component.  Settings (on the circuit, in the file as `<a name="appearance" val="logisim_evolution"/>` etc.):

| Setting | Value | Why |
|---|---|---|
| Appearance | `logisim_evolution` (box with a black name bar) | the standard look; pins are placed automatically from the pin order |
| `circuitnamedboxfixedsize` | true | box size depends on the number of pins, not on the name |
| Pin positions | inputs left, outputs right (ordered by the pin positions inside) | |
| Location of an instance | the position of its **first output pin** | that is how Logisim anchors the box |

Instances are listed in [BOM.md](BOM.md).

---

### Block by block: what each circuit is made of

(Exact lists with counts: [BOM.md](BOM.md).)

| Circuit | Components and settings | Why |
|---|---|---|
| `InstructionDecode` | 1 splitter, 32 bits -> 6 parts (7, 5, 5, 3, 5, 7 bits) | the instruction fields sit at fixed bit positions: pure wiring, no logic |
| `MainControl` | 9 comparators (7 bit, unsigned) each with a 7-bit constant; 3-input OR gates; 2-bit and 3-bit buses made with splitters | one comparator per opcode is the most readable way to write the opcode table; ORs implement the "which classes set this signal" equations |
| `ImmGen` | 8 splitters (cut the fields out of the instruction and merge them in the right order), 4 sign bit extenders (I, S, B, J: 12, 12, 13, 21 -> 32 bits), for U-type a 12-bit zero constant and a merging splitter instead of an extender, two 1-bit zero constants for the always-zero bit 0 of B and J, one 8:1 x 32 multiplexer | the scrambled immediate bits are re-ordered by splitters; the multiplexer selects the format by `ImmSel` |
| `RegisterFile` | 32 registers (32 bit, labelled `x0..x31`), 1 demultiplexer (select 5), 2 multiplexers (select 5, 32 bit), a 32-bit zero constant for x0 | write: demux routes `RegWrite` to register `rd`; read: asynchronous multiplexers; x0 can only ever load 0 |
| `ALUControl` | 5 multiplexers of 4 bits: two 8:1 (R-type table and I-type table, selected by `funct3`), two 2:1 (ADD / SUB and SRL / SRA, selected by `funct7` bit 5), one 4:1 (selected by `ALUOp`: force add, force sub, R table, I table); 19 constants of 4 bits (the `ALUCtrl` codes) | a table of codes is a constant per entry selected by a multiplexer: each row of the control table is one visible constant |
| `ALU` | adder, subtractor, 32-bit AND / OR / XOR gates, 3 shifters (`ll`, `lr`, `ar`), signed and unsigned comparators + 1 -> 32 zero extenders, one 16:1 x 32 multiplexer | all operations computed in parallel, the multiplexer picks one by `ALUCtrl` (simple; speed does not matter in Logisim) |
| `BranchUnit` | unsigned + signed 32-bit comparators, 3 NOT gates, an 8:1 x 1 multiplexer, an AND gate | the six branch conditions are three comparisons and their negations |
| `LoadExtract` | splitters (4 bytes, 2 halves), 4:1 x 8 and 2:1 x 16 multiplexers, 4 bit extenders (sign / zero, 8 / 16 -> 32), an 8:1 x 32 multiplexer | pick the part of the word, extend as the instruction asks |
| `StoreMerge` | 6 splitters (old word, write data, size, byte-enable address, byte enables, new word), 3 byte multiplexers (source byte per lane), a 16 x 4 ROM, 4 two-way byte multiplexers | read-modify-write of one word |
| `Memory` | RAM (256 x 32, async read, line enables), `LoadExtract`, `StoreMerge`, 1 address splitter (byte offset / word index) | see section 1 |
| `ForwardingUnit` | 6 comparators (5 bit, unsigned), AND / NOT gates, 2 splitters building the 2-bit select | register-number comparisons, one rule per source |
| `HazardUnit` | 3 comparators (5 bit), OR, NOT, 3-input AND | the load-use condition |
| `main` | PC register, ROM, 2 adders (PC+4, PC+imm), a 32-bit AND with the 0xFFFFFFFE mask, an OR gate, 5 multiplexers (A, B, write-back, two for the next PC), 8 sub-circuits | the datapath of section 4 of the guide |
| `Pipeline` | 24 registers (PC + 23 pipeline registers), 8 splitters (PC bits, pack / unpack of the control words), 10 sub-circuits, forwarding and flush multiplexers, a NOT gate for `CLK_n` | the 5-stage version |

## 7. Design decisions: why this and not that

| Decision | Alternative | Why we chose this |
|---|---|---|
| Separate instruction ROM and data RAM (Harvard) | one shared memory | no structural hazard in the pipeline (fetch and data access in the same cycle); simple |
| Register file from 32 `Register`s + mux + demux | RAM as register file (dual RAM) | visible: each register is a labelled box you can read; `x0` can be hard-wired to 0; the pipeline writes on the falling edge, which is trivial with registers |
| Register file reads asynchronous | clocked reads | the single-cycle CPU needs the operands in the same cycle |
| RAM with asynchronous read, line enables | synchronous read / byte enables | load data must arrive in the same cycle; byte enables would need four write strobes |
| Sub-word stores = read-modify-write in `StoreMerge` | byte-enabled RAM, 4 RAMs of 8 bits | one RAM, easy to test with test vectors |
| Two-level control (`MainControl` -> `ALUOp` -> `ALUControl`) | one big decoder | small tables, each tested separately; the classic textbook structure |
| Control word generated once in ID and packed | decode again in every stage | one source of truth; packing makes the pipeline registers few and the diagram short |
| Register file writes on the falling edge (pipeline) | forwarding from WB to ID | no extra mux / comparators; textbook trick |
| Branches resolved in EX, always "not taken" | resolve in ID, predictors | smaller and obviously correct; costs 2 cycles per taken branch (could be improved, see report) |
| Separate adder for `PC + imm`; ALU used for `JALR` target | ALU for everything | branches and JAL need the ALU result elsewhere; this avoids a conflict |
| `ASel` and `WBSel` selectors | extra instructions-specific paths | `lui`, `auipc`, `jal`, `jalr` reuse the ALU and write-back path |
| Tunnels for every long connection | drawn wires | readability, generated automatically, easy to check by name |
| Circuits generated from netlists (`tools/build`) | drawn by hand | exact, repeatable, verified automatically; the original hand-drawn main had long crossing wires and open ends |
| 10 px pin pitch avoided (`spacing 3`, fan-out routing) | leave overlapping labels | every label stays readable |

---

## 8. Recipes: to build a component by hand

Use these if you want to change a block in Logisim instead of in the generator.

**A 32-to-1 register read port** - Plexers > Multiplexer: Select Bits 5, Data Bits 32, Include Enable no; connect the 32 register outputs to inputs 0..31 (x0 = input 0), `rs1` to the select.

**A write-enable decoder** - Plexers > Demultiplexer: Select Bits 5, Data Bits 1; data input = `RegWrite`, select = `rd`; output *i* to the WE pin of register *i*.

**The PC** - Memory > Register: Data Bits 32, Trigger Rising Edge, Label `PC`; D = `next_pc`, clk = `CLK`, WE = 1 (or `run`), R = `RESET`.

**The data RAM** - Memory > RAM: Address Bit Width 8, Data Bit Width 32, Enables = Use line enables, Asynchronous read = yes, Data bus = separate, Appearance classic.

**A sign / zero extender** - Wiring > Bit Extender: Bit Width In 8 (or 12, 16 ...), Bit Width Out 32, Extension Type sign or zero.

**A signed / unsigned comparator** - Arithmetic > Comparator: Data Bits 32, Numeric Type two's complement (signed) or unsigned.

**A 3-bit bus from three signals** - Wiring > Splitter facing west: Fan Out 3, Bit Width In 3; bit 0 -> part 0, bit 1 -> part 1, bit 2 -> part 2; connect the three signals on the left.

**A constant 0 of 32 bits** - Wiring > Constant: Data Bits 32, Value 0x0 (remember the default is 1).

**Loading a program** - right-click the ROM > Edit Contents > Open (a file starting with `v2.0 raw`).
