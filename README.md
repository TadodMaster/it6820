# RV32I computer in Logisim Evolution

A 32-bit RISC-V (RV32I) computer built in **Logisim Evolution 4.1.0** for the course project
(assignment: [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md)).  The project contains **two CPUs** that share the same
building blocks and run the same programs:

| Circuit | What it is |
|---|---|
| `main` | **single-cycle CPU** (one instruction per clock cycle) |
| `Pipeline` | **5-stage pipeline** IF > ID > EX > MEM > WB with forwarding, load-use stall and branch / jump flush |

Both implement the whole RV32I base integer ISA except `fence`, `ecall`, `ebreak` (they execute as no-ops).
Everything is tested: 9 module test files, 7 whole-CPU test programs and a random-program fuzzer, all compared with an
independent reference simulator.  Technical report: [docs/REPORT.md](docs/REPORT.md).

![single-cycle CPU](docs/img/main.png)

## Quick start

Requirements: Java 21 or newer (Logisim Evolution 4.1.0 does not start on Java 17), Python 3.10+.

```powershell
cd D:\hust\logisim
java -jar .\logisim-evolution-4.1.0-all.jar .\RiscVComputer.circ
```

1. In the project tree open `main` (single-cycle) or `Pipeline`.
2. **Load a program** into the instruction ROM: right-click the ROM > *Edit Contents...* > *Open...* and choose a
   `.hex` file (Logisim "v2.0 raw" format), or type the words in. Make one from assembly:
   ```powershell
   python tools\rv.py asm programs\demo.s -o programs\demo.hex -l
   ```
   The ROM already contains `programs/demo.s` (sum 1..10, store/load, a function call).
3. Poke `RESET` to 1 and back to 0 (puts PC at 0).
4. Step: `Simulate > Tick Full Cycle` once per clock cycle (or *Ticks Enabled* to free-run).
5. Watch `PC`, `instr`, `wb_data` and the registers: open `RegisterFile` with the Poke tool (magnifier on the block);
   registers are labelled `x0`..`x31`. Do not poke registers by opening the sub-circuit from the project tree - that is a
   different state.

Demo program expected result: `x10 = 55`, `x12 = 110`, `x13 = 55`, `x14 = 1`; the single-cycle CPU is done after about 40 cycles, the pipeline after about 65.
See [docs/DEMO.md](docs/DEMO.md) for a demo script.

## Files

| Path | Content |
|---|---|
| `RiscVComputer.circ` | the project (both CPUs and all blocks) |
| `programs/` | `demo.s` (preloaded in the ROM), `hazards_demo.s` (shows stall / forwarding / flush), with `.hex` images |
| `tools/rv.py` | assembler (`asm`) and reference simulator (`sim`) |
| `tools/java/`, `tools/bin/` | Java helpers: headless runner `Run`, renderer `Render`, pin dump `Ends` (`tools\compile.ps1` builds them) |
| `tools/build/` | generators for the circuits (`build_all.py`), see [Rebuilding](#rebuilding-the-circuits) |
| `tests/` | module test vectors, test programs, test runners |
| `docs/` | documentation, see the index below |
| `backup/` | earlier versions of the `.circ` |
| `logisim-mcp/` | MCP server so Claude Code can read / test circuits (see `commands.txt`) |

## Documentation

| Document | Read it to ... |
|---|---|
| [docs/GUIDE.md](docs/GUIDE.md) | **understand everything**: what a CPU does, every block, real signal values, the pipeline, tests, troubleshooting, glossary |
| [docs/REPORT.md](docs/REPORT.md) | the formal technical report (architecture, modules, pipeline, hazards, tests, results) |
| [docs/COMPONENTS.md](docs/COMPONENTS.md), [docs/BOM.md](docs/BOM.md) | the **configuration of every component and why** (settings, GUI names, traps, design decisions), and the generated bill of materials |
| [docs/TOOLS.md](docs/TOOLS.md) | how the assembler, simulator, runner, generator and tests work inside |
| [docs/DESIGN_LOG.md](docs/DESIGN_LOG.md) | history, design decisions, pitfalls found |
| [docs/DEMO.md](docs/DEMO.md) | script for the demo video |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | the assignment (Vietnamese) with the status of each item |
| [docs/INDEX.md](docs/INDEX.md) | map of all documents and a suggested reading order |

## Instruction set

All of RV32I: `add sub sll slt sltu xor srl sra or and`, `addi slti sltiu xori ori andi slli srli srai`,
`lb lh lw lbu lhu sb sh sw`, `beq bne blt bge bltu bgeu`, `jal jalr`, `lui auipc`.
Pseudo instructions in the assembler: `nop li mv not neg j jr ret call beqz bnez bltz bgez blez bgtz bgt ble bgtu bleu seqz snez`.
Memory: instruction ROM 256 words, data RAM 256 words (address wraps modulo 1 KiB), Harvard organisation.
Loads / stores need natural alignment (a misaligned access uses the aligned word / halfword).

## Architecture in one page

Blocks (each is a circuit in the project, with a picture in `docs/img`):

| Block | Role |
|---|---|
| `InstructionDecode` | splits `instr` into `opcode rd funct3 rs1 rs2 funct7` |
| `MainControl` | opcode > `RegWrite ALUSrc MemWrite MemRead IsBranch ALUOp ImmSel ASel WBSel IsJAL IsJALR` |
| `ImmGen` | I / S / B / U / J immediates |
| `RegisterFile` | x0..x31, 2 read ports, 1 write port |
| `ALUControl`, `ALU` | 10 operations, `ALUCtrl` 0..9 |
| `BranchUnit` | `beq bne blt bge bltu bgeu` |
| `Memory` = `LoadExtract` + `StoreMerge` + RAM | `lb lh lw lbu lhu sb sh sw` |
| `ForwardingUnit`, `HazardUnit` | pipeline only |

Control signals (checked by `tests/maincontrol.vec`):

| opcode | class | RegWrite | ALUSrc | MemW | MemR | Branch | ALUOp | ImmSel | ASel | WBSel |
|---|---|---|---|---|---|---|---|---|---|---|
| `0x33` | R-type | 1 | 0 | 0 | 0 | 0 | 10 | - | rs1 | ALU |
| `0x13` | I-type ALU | 1 | 1 | 0 | 0 | 0 | 11 | I | rs1 | ALU |
| `0x03` | load | 1 | 1 | 0 | 1 | 0 | 00 | I | rs1 | MEM |
| `0x23` | store | 0 | 1 | 1 | 0 | 0 | 00 | S | rs1 | - |
| `0x63` | branch | 0 | 0 | 0 | 0 | 1 | 01 | B | rs1 | - |
| `0x37` | lui | 1 | 1 | 0 | 0 | 0 | 00 | U | zero | ALU |
| `0x17` | auipc | 1 | 1 | 0 | 0 | 0 | 00 | U | PC | ALU |
| `0x6F` | jal | 1 | 0 | 0 | 0 | 0 | 00 | J | - | PC+4 |
| `0x67` | jalr | 1 | 1 | 0 | 0 | 0 | 00 | I | rs1 | PC+4 |

`ALUCtrl`: 0 ADD, 1 SUB, 2 AND, 3 OR, 4 XOR, 5 SLL, 6 SRL, 7 SRA, 8 SLT, 9 SLTU.
`ImmSel`: 0 I, 1 S, 2 B, 3 U, 4 J.  `ASel`: 00 rs1, 01 PC, 10 zero.  `WBSel`: 00 ALU, 01 memory, 10 PC+4.

**Pipeline hazards** (details in the report):

* *Data hazard, ALU result needed soon*: `ForwardingUnit` selects the operand of EX from EX/MEM or MEM/WB (`wb_data`).
  The register file writes on the falling clock edge, so WB and ID can use it in the same cycle.
* *Load-use*: `HazardUnit` stalls PC and IF/ID for one cycle and inserts a bubble in ID/EX.
* *Control hazard*: branch / JAL / JALR are resolved in EX; when taken, PC is redirected and the two instructions behind
  are flushed (2-cycle penalty). There is no branch prediction (always "not taken").

## Tests

```powershell
powershell -File tests\run_tests.ps1                  # 9 module test files (Logisim test vectors), ~35 s
python tests\run_cpu_tests.py --circuit all            # test programs on both CPUs, compared with the reference simulator
python tests\fuzz.py --count 20 --seed 1               # random programs on both CPUs
```

| Test | What it checks |
|---|---|
| `tests/*.vec` | every module in isolation: `ALU` 15 rows, `ALUControl` 23, `MainControl` 10, `ImmGen` 6, `BranchUnit` 16, `LoadExtract` 15, `StoreMerge` 7, `ForwardingUnit` 9, `HazardUnit` 5 |
| `tests/programs/*.s` | `alu` (all R/I ops), `mem` (all loads / stores), `branch` (6 conditions, taken and not), `jump` (jal jalr lui auipc, call / ret), `fib`, `hazard` (dependent instructions, load-use, branch after load, ...). They check themselves: `x31 = 0x600D` when everything was right |
| `tests/fuzz.py` | random programs (loads, stores, branches, jumps, dense register reuse) compared register-by-register and word-by-word with the reference simulator |

Measured cycles (cycles until the PC reaches the final `halt: j halt`):

| program | instructions | single-cycle | pipeline | pipeline CPI |
|---|---|---|---|---|
| alu | 92 | 91 | 91 | 0.99 |
| mem | 70 | 69 | 70 | 1.00 |
| hazard | 68 | 67 | 79 | 1.16 |
| jump | 28 | 27 | 35 | 1.25 |
| branch | 70 | 69 | 101 | 1.44 |
| fib | 124 | 123 | 178 | 1.44 |
| demo | 40 | 39 | 61 | 1.52 |

The pipeline reaches CPI 1.0 on straight-line code; loops with taken branches cost 2 extra cycles each.

## Rebuilding the circuits

`RiscVComputer.circ` is generated from netlists by `tools/build/build_all.py` (no hand wiring for the new blocks); the hand-drawn
blocks `ALU`, `InstructionDecode`, `RegisterFile`, `ImmGen`, `ALUControl` come from `tools/build/base.circ`.

```powershell
powershell -File tools\compile.ps1                                           # once: compile the Java helpers
python tools\build\build_all.py tools\build\base.circ RiscVComputer.circ     # regenerate everything
```

The generator asks Logisim for the exact pin positions, draws stubs and named tunnels, avoids collisions, and then **verifies** the
saved file: every net must be connected as intended, nothing may be shorted.  Rules learned the hard way: Logisim connects wires
only at their end points (no T-junctions in files), everything must lie on the 10-pixel grid, and `Constant` defaults to the value 1.

## Known limits

* No branch prediction, cache, multiplier / divider, interrupts, GPIO / UART or floating point (the optional extensions).
* `fence`, `ecall`, `ebreak`, CSR instructions are not implemented (treated as `nop`).
* The instruction ROM and data RAM are 256 words; the data RAM is separate from the ROM (a program cannot modify itself).
* The report is drafted in [docs/REPORT.md](docs/REPORT.md) (to be proof-read and exported by the group); the demo video still has to be recorded ([docs/DEMO.md](docs/DEMO.md) is a script).

## Tools

Java 21 (JDK 21.0.12 at `C:\Program Files\Java\jdk-21.0.12.1`), Python 3.10, `logisim-mcp` MCP server (venv needs `mcp<2`).
`commands.txt` lists the commands.
