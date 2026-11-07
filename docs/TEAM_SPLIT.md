# Team split: three people, three parts

Everyone learns one part in depth, and everyone knows the overview (section 5), so any of you can answer a teacher's question.

## 1. The split

| Person | Topic | Circuits | Module tests (`tests/`) | Programs |
|---|---|---|---|---|
| **A** | Front end, decode and the single-cycle top level | `main`, InstructionDecode, MainControl, ImmGen, RegisterFile | `maincontrol.vec`, `immgen.vec` | `programs/demo.s`, `tests/programs/alu.s` |
| **B** | Execute and memory | ALU, ALUControl, BranchUnit, Memory, LoadExtract, StoreMerge | `alu.vec`, `alucontrol.vec`, `branchunit.vec`, `loadextract.vec`, `storemerge.vec` | `alu.s`, `mem.s`, `branch.s` |
| **C** | Pipeline and hazards | `Pipeline`, ForwardingUnit, HazardUnit | `forwardingunit.vec`, `hazardunit.vec` | `hazard.s`, `jump.s`, `fib.s`, `programs/hazards_demo.s` |

All 14 circuits are covered: A has 5, B has 6, C has 3 (but `Pipeline` is the biggest one).

## 2. What each person must be able to explain

### A - front end, decode, single-cycle datapath
* How a 32-bit instruction is cut into `opcode rd funct3 rs1 rs2 funct7`, and the six formats R I S B U J.
* How `MainControl` turns the opcode into the control signals (`RegWrite ALUSrc ASel ALUOp ImmSel WBSel ...`).
* How `ImmGen` rebuilds the immediate for each format (sign extension; U-type = `imm << 12`).
* The register file: 32 registers, `x0` always 0, two asynchronous read ports, one write port.
* The whole path IF > ID > EX > MEM > WB of `main`, and the next-PC logic (PC+4, branch / JAL target, JALR target).
* Run: **presentation steps 1-5** (single-cycle demo, State tab, tick by tick).
* Read: `docs/GUIDE.md` sections 1-5, `docs/COMPONENTS.md` entries of these circuits.

### B - execute and memory, tests
* The ALU: ten operations computed in parallel and selected by `ALUCtrl`; why `SLT` / `SLTU` differ; shifts use `B[4:0]`.
* `ALUControl`: how `ALUOp / funct3 / funct7` become `ALUCtrl` (`funct7[5]` separates ADD/SUB and SRL/SRA).
* `BranchUnit`: the six conditions and how `branch_taken` is formed.
* Memory: asynchronous-read RAM; `LoadExtract` (lb lh lw lbu lhu); why `sb` / `sh` need `StoreMerge`, a read-modify-write of one word with byte enables.
* How everything is tested: module test vectors, programs against the reference simulator, the fuzzer.
* Run: **presentation steps 6, 9, 11, 12** (load a program, the proof, writing a program, "give us any program").
* Read: `docs/GUIDE.md` sections 4, 6, 10, 11; `docs/TOOLS.md`.

### C - pipeline and hazards
* Why a pipeline: five stages, four pipeline registers (IF/ID, ID/EX, EX/MEM, MEM/WB), the packed control word.
* Why the register file writes on the falling edge (`CLK_n`).
* Forwarding: `ForwardingUnit`, `ForwardA / ForwardB` = `00 register, 01 MEM/WB, 10 EX/MEM`, and the JAL/JALR detail (forward PC+4).
* Load-use stall: `HazardUnit`, why one bubble is needed, why the PC and IF/ID hold.
* Control hazard: branch / JAL / JALR resolved in EX, `pc_src_ex`, the two flushed instructions, 2-cycle penalty.
* The results table and why cycles do not drop (the gain is a shorter clock period).
* Run: **presentation steps 7, 8, 10** (open `Pipeline`, hazards demo with the `stall`, `pc_src_ex`, `ForwardA/B` probes, results).
* Read: `docs/GUIDE.md` sections 7-9, `docs/REPORT.md` sections 5 and 8.

## 3. Questions a teacher may ask

**A**
1. How does the CPU know which instruction format it has?  (the opcode decides; `MainControl`, `ImmSel`)
2. Why is `x0` always zero?  (the register file loads the constant 0 for `x0`; writes to it are ignored)
3. What does `lui` do in this datapath?  (`ASel = 10` selects zero, B = immediate, ALU adds)
4. How is the JALR target computed?  (`(rs1 + imm)` with bit 0 cleared)

**B**
1. How does the ALU choose its result?  (all results computed, a multiplexer picks by `ALUCtrl`)
2. How do you store one byte in a word-based RAM?  (read the word, replace one byte lane, write the word back)
3. How are `blt` and `bltu` different?  (signed vs unsigned comparator in `BranchUnit`)
4. How do you know the CPU is correct?  (106 module test rows, 7 programs compared with the reference simulator, random programs)

**C**
1. What is a hazard and which ones are handled?  (data: forwarding + load-use stall; control: flush)
2. Why can a load not be forwarded like an ALU result?  (the data exists only at the end of MEM)
3. What does a taken branch cost?  (2 cycles; not taken costs nothing)
4. Why is the pipeline not faster in your table?  (the simulation has no gate delays; the benefit is a shorter clock period)

## 4. Shared by all three (30 minutes together)

* Architecture overview: `docs/REPORT.md` section 2 and the two top-level pictures `docs/img/main.png`, `docs/img/Pipeline.png`.
* The commands in `commands.txt` and the pre-flight check `tools\presentation_check.ps1`.
* One full rehearsal of `docs/PRESENTATION.md`, each person presenting their own steps (A: 1-5, B: 6, 9, 11, 12, C: 7, 8, 10).
