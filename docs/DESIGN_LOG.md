# Design log

Condensed from `RV32I_Logisim_Evolution_Full_Session.pdf` (a saved chat session, in Vietnamese) and
updated to match the current `RiscVComputer.circ`. The PDF stops at ImmGen; everything after that
(control unit, ALUControl, BranchUnit, Memory, full 32-register file) was built later and is described
in [../README.md](../README.md) and [REPORT.md](REPORT.md).

## Roadmap that was followed

`ADDI/ADD/SUB` -> full ALU -> `LW/SW` -> `BEQ/BNE` -> `JAL/JALR/LUI/AUIPC`.
All steps are done, including `JAL/JALR/LUI/AUIPC`, the optional loads / stores and `BLT/BGE/BLTU/BGEU`.
Multi-cycle was skipped; the 5-stage pipeline (forwarding, load-use stall, branch / jump flush) is done.
Optional branch prediction and cache are not done.  See [REPORT.md](REPORT.md) for the final design.

Conventions fixed at the start: datapath 32-bit, register addresses 5-bit, opcode 7-bit, funct3 3-bit,
`ALUCtrl` 4-bit. Use tunnels for long signals (`pc`, `instr`, `rs1_data`, `rs2_data`, `imm`, `wb_data`).

## Fetch

* `PC` is a 32-bit register, rising edge. `PC + 4` comes from a 32-bit adder with a constant 4.
* ROM is 256 x 32, address 8 bits. PC is a byte address, so the ROM address is `PC[9:2]`
  (splitter: fan-out 3 = `PC[1:0]`, `PC[9:2]`, `PC[31:10]`).
* Debug with *Manual Tick Full Cycle*: one rising edge per click, so PC advances once.
* Reset: the register's `R` pin. Added to `main` as the `RESET` input (it was not wired before).

## Decode

`InstructionDecode` is only a splitter:

```
opcode = instr[6:0]    rd  = instr[11:7]    funct3 = instr[14:12]
rs1    = instr[19:15]  rs2 = instr[24:20]   funct7 = instr[31:25]
```

For I-type instructions bits `[24:20]` are part of the immediate, not `rs2`. The decoder always cuts the
same fields; the control unit decides which ones matter.

## Register file

* 32 real registers (`x0` loads constant 0 so it always reads 0), two 32:1 multiplexers for the read
  ports, a 1-to-32 demultiplexer (`data = RegWrite`, `select = rd`) for the write enables.
* Tunnels `x0..x31`, `WE0..WE31`, `CLK`, `wb_data` keep it from becoming wire spaghetti.
* Demux vs decoder: a decoder gives one-hot only; the demux also forwards `RegWrite`, so with
  `RegWrite = 0` every write enable is 0.

## ALU

Ten operations computed in parallel, then a 16:1 multiplexer selected by `ALUCtrl`:

| ALUCtrl | op | | ALUCtrl | op |
|---|---|---|---|---|
| 0000 | ADD | | 0101 | SLL |
| 0001 | SUB | | 0110 | SRL |
| 0010 | AND | | 0111 | SRA |
| 0011 | OR | | 1000 | SLT (signed) |
| 0100 | XOR | | 1001 | SLTU (unsigned) |

Shifts use `B[4:0]`. Test values used: `5 + 7 = 0xC`, `5 - 7 = 0xFFFFFFFE`, `0x80000000 >>> 1 = 0xC0000000`,
`0xFFFFFFFF <s 1 = 1`, `0xFFFFFFFF <u 1 = 0`.
Covered by `tests/alu.vec` (15 rows). A bug where SLTU returned `0xFFFFFFFF` (sign-extended 1-bit result) was found and fixed with this test.

## ImmGen

`ImmSel`: 0 I, 1 S, 2 B, 3 U, 4 J. Splitters rebuild each format, a Bit Extender sign-extends it (U-type instead appends 12 zero
bits with a splitter), a 3-bit select multiplexer chooses. Covered by `tests/immgen.vec`.

| Type | imm | Example | Result |
|---|---|---|---|
| I | `instr[31:20]` | `00500093` `addi x1,x0,5` | `00000005` |
| S | `instr[31:25]`, `instr[11:7]` | `0020A623` `sw x2,12(x1)` | `0000000C` |
| B | `[31]`, `[7]`, `[30:25]`, `[11:8]`, 0 | `00208463` `beq x1,x2,8` | `00000008` |
| U | `instr[31:12] << 12` | `123452B7` `lui x5,0x12345` | `12345000` |
| J | `[31]`, `[19:12]`, `[20]`, `[30:21]`, 0 | `008000EF` `jal x1,8` | `00000008` |

## Debugging notes (Logisim pitfalls hit during the build)

* **Incompatible widths:** check Data Bits on Register, Adder, Constant, Pin, Tunnel, Mux. The small number
  next to a wire is its width, not a value.
* **Red bus / `E`:** two sources drive one net (for example an Input Pin and a Constant), or a pin has the
  wrong direction. A multiplexer output that is red with correct properties is usually an Input Pin where an
  Output Pin should be.
* **Poking the right instance:** a sub-circuit opened from the project tree has its own state. To change
  registers that `main` really uses, go *Main -> magnifier on the instance*. If a popup says the pin is
  attached to the super circuit, choose *Cancel* and poke only the registers inside.
* **Probes:** a tunnel shows no value. Attach a Probe (hex for 32-bit buses, decimal for `rs1/rs2/rd`).
* Component locations must be on the 10 px grid; sub-circuit pins sit at the box edge, so choose the
  location from the pin row, not from the box corner.

## Tool notes

* Logisim Evolution 4.1.0 needs Java 21 (Java 17 fails with `UnsupportedClassVersionError`, class file 65).
* Headless test of one sub-circuit:
  `java -jar logisim-evolution-4.1.0-all.jar --test-vector <circuit> <file.vec> RiscVComputer.circ`.
  The first line of the `.vec` lists pin labels (`name[width]`), values are `0x..` hex or binary.

## Later work (after the PDF)

Chronological notes, kept because several of the lessons are not obvious.

### Layout clean-up and first tests
* `main` was re-laid out in stage order with named tunnels; sub-circuits got titles and text.
* Test vectors (`--test-vector`) for each module found bugs in the hand-built blocks: ALU `SLTU` (sign- instead of zero-extended),
  `ALUControl` `SLL` (constant 6 instead of 5), `MainControl` (JALR / LUI / JALR immediate select), `ImmGen` (U-type shift, J-type bit 0).
* A reference simulator + headless runner showed that the original `Memory` block never returned data (RAM with synchronous read).

### Full RV32I and the pipeline
* New control signals: `ASel` (A = rs1 / PC / 0) and `WBSel` (ALU / memory / PC+4); next-PC logic for JAL, JALR (bit 0 cleared) and branches.
* `BranchUnit` with signed / unsigned comparators; `Memory` rebuilt around an asynchronous-read RAM, with `LoadExtract` and `StoreMerge`
  (sub-word stores are a read-modify-write of one word, byte enables from a 16-row ROM).
* Pipeline: control signals generated in ID and carried in a packed control word; register file writes on the falling edge;
  `ForwardingUnit` (EX/MEM before MEM/WB; JAL / JALR forward PC+4), `HazardUnit` (load-use stall), flush on `pc_src_ex`.

### Generating circuits from netlists
New circuits are described as components + named nets and written by `tools/build`:
the generator gets pin positions from Logisim itself, adds stubs and tunnels, avoids collisions and verifies the result.  Pitfalls found:

| Pitfall | Effect |
|---|---|
| a wire that merely passes through another wire's end point is **not connected** (T-junctions) | nets silently open; the `instr` tap and others were open in the first generated `main` |
| a component or wire not on the 10-px grid is snapped | pins no longer touch the wires |
| two stubs ending at the same tunnel spot | two nets shorted - the generator now routes with collision checks |
| `Constant` default value is 1 | "zero" constant was 1: `lui` produced `x + 1` |
| RAM default: synchronous read, byte enables | loads return garbage; need `asyncread = true`, `enables = line` |
| splitter pins are 10 px apart | no room for tunnels: use the `spacing` attribute |
| a circuit called `__x__` is renamed on load | use plain names |
| `java *` expands `*` to file names on Windows | use a word such as `ALL` |
| test-vector rows do not keep RAM contents between rows | test memory through whole programs (`Run.java`) |

An earlier claim that the re-laid-out `main` had "30 of 30 nets identical" came from a checker that wrongly assumed T-junction connections;
the strict checker found 7 broken nets, which were fixed before anything was built on top.
