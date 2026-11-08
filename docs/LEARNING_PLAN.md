# Learning plan: the architecture of the RV32I computer, part by part

Goal: after this plan you can explain **every circuit of the project, what is inside it and why**, from one gate up to the whole 5-stage pipeline, and you can prove with tests that it works.
The plan is for one person; with three people use `docs/TEAM_SPLIT.md` for the split and still do Phases 0, 1 and 6 together.

How to use it: do the sessions in order (each is about 90 minutes).  In every session you **read** (a few pages), **look** (open the circuit in Logisim), **do** (one small experiment) and **check** (answer the questions without looking).  If you cannot answer a check question, repeat the session before moving on.

Time: 12 sessions (about 18 hours), or 6 days with two sessions a day.

| Phase | Sessions | Topic | Circuits |
|---|---|---|---|
| 0 | 1 | Tools and the big picture | (all, from outside) |
| 1 | 2 | Basics: how a CPU runs a program, RISC-V instruction formats | - |
| 2 | 3 | Decode and control | InstructionDecode, MainControl, ImmGen |
| 3 | 4 | Registers and arithmetic | RegisterFile, ALUControl, ALU, BranchUnit |
| 4 | 5-6 | Memory and the single-cycle CPU | Memory (LoadExtract, StoreMerge), `main` |
| 5 | 7-9 | The pipeline | `Pipeline`, ForwardingUnit, HazardUnit |
| 6 | 10-12 | Programs, tests, the tools, and the demo | assembler, simulator, test suite |

---

## Phase 0 - Tools and the big picture (session 1)

**Read:** `README.md`, `docs/GUIDE.md` section 2 ("The project at a glance"), `docs/REPORT.md` sections 1-2.
**Do:**
1. Open the project: `java -jar .\logisim-evolution-4.1.0-all.jar .\RiscVComputer.circ` (needs Java 21; see `commands.txt`).
2. In the left tree list the 14 circuits and sort them into three groups: the two CPUs (`main`, `Pipeline`), the datapath blocks (`InstructionDecode`, `MainControl`, `ImmGen`, `RegisterFile`, `ALUControl`, `ALU`, `BranchUnit`, `Memory`, `LoadExtract`, `StoreMerge`), the pipeline-only blocks (`ForwardingUnit`, `HazardUnit`).
3. Learn the Logisim controls: Ctrl+R (reset), Ctrl+F9 (one full clock cycle), the State tab (PC and x0..x31), tunnels (same name = same wire), zoom.
4. Run `python tools\live_proof.py` once and read the output: this is the "does it work" proof you will understand fully at the end.

**Key ideas:** two CPUs built from the same blocks; Harvard memory (ROM for instructions, RAM for data); names are the wires.
**Check:** What is the difference between `main` and `Pipeline`?  Why are there two memories?  What does a tunnel do?

---

## Phase 1 - Basics (sessions 2-3)

### Session 2: how a CPU runs a program
**Read:** `docs/GUIDE.md` section 1 ("What a computer does"), section 14 (glossary).
**Ideas:** fetch / decode / execute; PC; registers vs memory; clock; "state changes only on the clock edge"; combinational vs sequential logic; two's complement (negative numbers), hexadecimal.
**Do:** by hand, run `programs/demo.s` for 3 iterations on paper (PC, x10, x11) and compare with the table in `docs/DEMO_EXPLAIN.md` section 4.
**Check:** What does the PC contain?  Why is a register faster than memory?  What is -1 in 32 bits?

### Session 3: RISC-V instruction formats
**Read:** `docs/REPORT.md` section 2.2-2.3 and appendix A, `docs/GUIDE.md` section 4 (the start).
**Ideas:** six formats R, I, S, B, U, J; fixed field positions (`opcode[6:0] rd[11:7] funct3[14:12] rs1[19:15] rs2[24:20] funct7[31:25]`); immediates are scattered in B and J; the nine opcodes in use.
**Do:** assemble a program with `python tools\rv.py asm programs\demo.s -l` and decode **three** machine words by hand (for example `00b50533`, `fff58593`, `fe059ce3`): write the fields in binary, name the format, name the instruction.
**Check:** Which format has no `rd`?  Why do B and J immediates have bit 0 missing?  What does `funct7[5]` change?

---

## Phase 2 - Decode and control (session 4... three circuits)

### 2.1 InstructionDecode
* **Purpose:** cut a 32-bit instruction into its fields.
* **Inputs / outputs:** `Instruction` in; `opcode` (7), `rd` (5), `funct3` (3), `rs1` (5), `rs2` (5), `funct7` (7) out.
* **Inside:** a single **splitter** (32 -> 6 parts).  No logic: the fields sit at fixed positions, so decoding is just wiring.
* **Why:** RISC-V was designed so that the register numbers are always in the same place: the register file can be read *while* the opcode is still being decoded.
* **Experiment:** in the circuit, poke `Instruction` with `00b50533` and read the six outputs.  Then run `tests\run_tests.ps1` (it has no vector file for this block: why not?  because it is only wires).
* **Check:** Which bits form `rs2`?  Why does the block contain no gate?

### 2.2 MainControl
* **Purpose:** from the `opcode` produce all control signals of the datapath.
* **Inputs / outputs:** `opcode` (7) in; `RegWrite`, `ALUSrc`, `MemWrite`, `MemRead`, `IsBranch`, `IsJAL`, `IsJALR`, `ALUOp` (2), `ImmSel` (3), `ASel` (2), `WBSel` (2) out.
* **Inside:** nine **comparators** (7 bit, unsigned), one per opcode (R `0x33`, I-ALU `0x13`, load `0x03`, store `0x23`, branch `0x63`, LUI `0x37`, AUIPC `0x17`, JAL `0x6F`, JALR `0x67`), each with a 7-bit **constant**; **OR gates** (at most 3 inputs) that say "which instruction classes set this signal"; **splitters** that join single bits into the 2- and 3-bit buses.
* **How it works:** `ALUOp = {IsR|IsI, IsI|IsBranch}` (00 add, 01 subtract, 10 R-type, 11 I-type); `ImmSel = {IsJAL, IsBranch|IsLui|IsAuipc, IsStore|IsLui|IsAuipc}`; `ASel = {IsLui, IsAuipc}`; `WBSel = {IsJAL|IsJALR, IsLoad}`.  An unknown opcode makes every signal 0 (a harmless NOP).
* **Why:** one comparator per opcode is the most readable form of the opcode table; the ORs are the "control table" columns.
* **Experiment:** fill the control table of the report (section 2.3) on paper for `lw`, `sw`, `beq`, `lui`, `jal`, then compare with `tests\maincontrol.vec`.
* **Check:** Which signals are 1 for `sw`?  What does `ASel = 10` mean and for which instruction?  What happens with opcode 0?

### 2.3 ImmGen
* **Purpose:** rebuild the 32-bit immediate for the format chosen by `ImmSel`.
* **Inputs / outputs:** `Instruction`, `ImmSel` (3) in; `Imm` (32) out.
* **Inside:** 8 **splitters** (cut the scattered fields out and merge them in the right order), 4 **bit extenders** (sign extension for I, S, B, J: 12, 12, 13, 21 bits -> 32), for U-type a 12-bit zero **constant** and a merging splitter (`imm << 12`), two 1-bit zero **constants** for the always-zero bit 0 of B and J, one **8-to-1 multiplexer** (5 inputs used) selected by `ImmSel` (0 I, 1 S, 2 B, 3 U, 4 J).
* **Why:** the immediate bits are scrambled in the instruction on purpose (so that most bits stay at the same place across formats); the splitters un-scramble them; sign extension keeps negative numbers negative.
* **Experiment:** decode `fe059ce3` (B-type): the immediate must be `0xfffffff8` = -8.  Check it in `tests\immgen.vec`.
* **Check:** Why is a B-type offset always even?  Where does the sign bit come from in each format?

**Session end test:** from a machine word, name the format and write `rd`, `rs1`, `rs2`, the immediate and the control signals, without looking.

---

## Phase 3 - Registers and arithmetic (session 5... four circuits)

### 3.1 RegisterFile
* **Purpose:** 32 registers x 32 bits; two reads and one write per cycle.
* **Inputs / outputs:** `write_data`, `CLK`, `write` (`RegWrite`), `rd`, `rs1`, `rs2` in; `rs1_data`, `rs2_data` out.
* **Inside:** 32 **registers** (labelled `x0..x31`, rising edge), one **demultiplexer** (select 5, data bit = `RegWrite`) that routes the write enable to register `rd`, two **multiplexers** 32-to-1 (select 5, 32 bit) as read ports (asynchronous), a 32-bit zero constant that feeds `x0`.
* **How it works:** write: only the register whose number is `rd` gets WE = 1; read: the multiplexers always show the registers selected by `rs1` / `rs2`.  `x0` can only load 0, so it is always 0.
* **Why:** asynchronous reads are needed so that the single-cycle CPU gets its operands in the same cycle; separate register boxes are readable (and you can see them in the State tab).  In the pipeline this block is clocked by the **inverted clock** (writes on the falling edge).
* **Experiment:** in `main`, tick the demo 3 times and open `RegisterFile`: find which register changed and which demux output was 1.
* **Check:** What happens if `rd = 0` and `RegWrite = 1`?  Why are reads asynchronous but writes clocked?

### 3.2 ALUControl
* **Purpose:** turn `ALUOp`, `funct3`, `funct7` into the 4-bit `ALUCtrl` code of the ALU.
* **Inputs / outputs:** `funct7` (7), `ALUOp` (2), `funct3` (3) in; `ALUCtrl` (4) out.
* **Inside:** 19 4-bit **constants** (the codes: 0 ADD, 1 SUB, 2 AND, 3 OR, 4 XOR, 5 SLL, 6 SRL, 7 SRA, 8 SLT, 9 SLTU), 5 **multiplexers**: two 8-to-1 (the R-type and the I-type tables, selected by `funct3`), two 2-to-1 (ADD/SUB and SRL/SRA, selected by `funct7[5]`), one 4-to-1 (selected by `ALUOp`: force ADD, force SUB, R table, I table).
* **Why:** a table of codes = one constant per row selected by a multiplexer: each row of the textbook table is one visible constant.  Two-level control (`MainControl` > `ALUOp` > `ALUControl`) keeps both tables small.
* **Experiment:** write the code for `sub`, `sra`, `srai`, `slti`, `lw`, `beq` on paper, then check `tests\alucontrol.vec`.
* **Check:** Why does `addi` ignore `funct7` but `srai` does not?  Which `ALUOp` do loads and branches use and why?

### 3.3 ALU
* **Purpose:** compute the result for the code in `ALUCtrl`.
* **Inputs / outputs:** `rs1_data`, `rs2_data`, `ALU_Ctrl` in; `result` out.
* **Inside:** an **adder**, a **subtractor**, 32-bit **AND / OR / XOR** gates, three **shifters** (logical left, logical right, arithmetic right; shift amount `B[4:0]`), a **signed** and an **unsigned comparator** each followed by a 1 -> 32 **zero extender** (so SLT/SLTU return 0 or 1), one **16-to-1 multiplexer** (10 inputs used).
* **How it works:** every operation is computed in parallel; the multiplexer picks one result by `ALUCtrl`.  (Simple, and speed does not matter in Logisim.)
* **Experiment:** poke `-1` and `1` for A, B with `ALUCtrl = 8` then `9`: SLT gives 1, SLTU gives 0.  Compare with `tests\alu.vec`.
* **Check:** Why must the SLT result be zero-extended?  Which part makes `sra` keep the sign?

### 3.4 BranchUnit
* **Purpose:** decide whether a branch is taken.
* **Inputs / outputs:** `rs1_data`, `rs2_data`, `IsBranch`, `funct3` in; `branch_taken` out.
* **Inside:** an unsigned and a signed 32-bit **comparator** (give `==`, `<u`, `<s`), 3 **NOT** gates (`!=`, `>=u`, `>=s`), an **8-to-1 one-bit multiplexer** selected by `funct3` (000 beq, 001 bne, 100 blt, 101 bge, 110 bltu, 111 bgeu; 010 and 011 give 0), an **AND** gate with `IsBranch`.
* **Why:** the six conditions are three comparisons and their negations; AND with `IsBranch` means other instructions can never "branch".
* **Experiment:** `tests\branchunit.vec`: find the rows for `blt` vs `bltu` with -1 and 1.
* **Check:** What is the difference between `blt` and `bltu` in the circuit?

**Phase test:** compute by hand `sub x13,x12,x10` through RegisterFile > ALUControl > ALU, then verify with the demo (tick 38 in `docs/DEMO_EXPLAIN.md`).

---

## Phase 4 - Memory and the single-cycle CPU (sessions 6-7)

### Session 6: Memory (with LoadExtract and StoreMerge)
**Read:** `docs/GUIDE.md` section 6, `docs/COMPONENTS.md` section 1 (RAM).
* **Memory purpose:** the data memory with byte, halfword and word access (`lb lh lw lbu lhu sb sh sw`).
* **Inputs / outputs:** `Address`, `write_data`, `MemWrite`, `CLK`, `funct3` in; `read_data` out.
* **Inside:** one **RAM** 256 x 32 with **asynchronous read** and a single write enable (line enables), an address **splitter** (byte offset `Address[1:0]`, word index `Address[9:2]`), `LoadExtract`, `StoreMerge`.
* **Why asynchronous read:** a load must deliver data in the same cycle (with the default synchronous read, loads returned undefined data: one of the bugs we found).
* **LoadExtract:** splitters (4 bytes, 2 halves), a 4-to-1 x 8 and a 2-to-1 x 16 multiplexer pick the byte / halfword, 4 bit extenders (sign / zero, 8 and 16 -> 32), a final 8-to-1 x 32 multiplexer selected by `funct3`.  `lbu`/`lhu` zero-extend, `lb`/`lh` sign-extend.
* **StoreMerge:** the RAM writes only whole words, so a byte store is **read-modify-write**: read the old word, replace one lane, write the word back.  A **16 x 4 ROM** turns `{size, address[1:0]}` into four byte enables (`1 2 4 8` bytes, `3 3 c c` halfwords, `f` word); four 8-bit 2-to-1 multiplexers choose, per lane, the new or the old byte; 3 more byte multiplexers choose the source byte per lane.
* **Experiment:** in the tests `tests\loadextract.vec` and `tests\storemerge.vec` find the rows for `sb` at offset 2, and `lb` of a byte with the top bit set.
* **Check:** Why can `StoreMerge` read the old word?  What is stored to word 0 by `sb x1, 1(x0)` if the old word is `0x11223344` and x1 = `0xAA`?  (Answer: `0x1122AA44`.)

### Session 7: the single-cycle CPU (`main`)
**Read:** `docs/GUIDE.md` section 5, `docs/REPORT.md` section 4, `docs/DEMO_EXPLAIN.md` section 3.
* **Inside `main`:** PC **register** (clear = `RESET`), instruction **ROM** (256 x 32, addressed by `PC[9:2]`), 2 **adders** (`PC+4`, `PC+imm`), a 32-bit **AND** with the `0xFFFFFFFE` mask (JALR), an **OR** gate (`branch_taken OR IsJAL`), 5 **multiplexers** (ALU operand A `ASel`, operand B `ALUSrc`, write-back `WBSel`, two for the next PC), the 8 sub-circuits.
* **Next PC:** `next_pc = IsJALR ? jalr_target : (branch_taken OR IsJAL) ? PC+imm : PC+4`.
* **Why this shape:** `lui`, `auipc`, `jal`, `jalr` reuse the same ALU and write-back path through `ASel` and `WBSel` instead of new hardware.
* **Experiment:** follow **one instruction of each class** through the five stages with the real values from `docs/DEMO_EXPLAIN.md` section 3 (add, addi, bnez, sw, lw, jal, ret).  Use the probes at the bottom of the circuit.
* **Check:** Draw `main` from memory as boxes IF, ID, EX, MEM, WB and mark where the three mux selects come from.  Which instructions use the separate adder `PC+imm`?  How is the JALR target computed?

**Phase test:** run the demo to tick 40 and explain every register change in `docs/DEMO_EXPLAIN.md` section 4 without looking at the explanation column.

---

## Phase 5 - The pipeline (sessions 8-10)

### Session 8: stages, pipeline registers, timing
**Read:** `docs/GUIDE.md` section 7 (start), `docs/REPORT.md` sections 5.1-5.2, `docs/DEMO_EXPLAIN.md` section 5.
* **Idea:** five stages work on five instructions at once; **four pipeline registers** (IF/ID, ID/EX, EX/MEM, MEM/WB) carry what the next stage needs.
* **Inside `Pipeline`:** 24 **registers** (PC + 23 pipeline registers, labelled `pc_id`, `instr_id`, `alu_result_mem`, ...), 8 **splitters** (PC bits, packing / unpacking the control word), 10 **sub-circuits**, forwarding and flush **multiplexers**, a **NOT** gate for `CLK_n`.
* **Control word:** the control signals are produced once, in ID, and packed (13 bits in ID/EX: `RegWrite ALUSrc MemWrite MemRead IsBranch ALUOp ASel WBSel IsJAL IsJALR`; 5 in EX/MEM; 3 in MEM/WB): each stage unpacks only what it needs.
* **Timing detail:** the register file writes on the **falling** edge: WB writes in the first half of a cycle, ID reads the new value in the second half, so no forwarding is needed for a distance of 3.
* **Experiment:** open `Pipeline`, find the four register banks from the labels and write down for `add x2,x1,x1` what is in each bank after 1, 2, 3, 4 ticks.
* **Check:** Why does the PC and IF/ID have a write enable `run` while the others do not?  Why are the pipeline registers 0 at start and why is that harmless?

### Session 9: ForwardingUnit and HazardUnit
**Read:** `docs/GUIDE.md` sections 7-8, `docs/REPORT.md` sections 5.3-5.6, `docs/DEMO_EXPLAIN.md` section 6.

**ForwardingUnit**
* **Purpose:** give EX the newest value of `rs1` / `rs2` when an older instruction has not written it yet.
* **Inputs / outputs:** `rs1_ex`, `rs2_ex`, `rd_mem`, `RegWrite_mem`, `rd_wb`, `RegWrite_wb` in; `ForwardA`, `ForwardB` (2 bits) out.
* **Inside:** 6 **comparators** (5 bit), **AND / NOT** gates, 2 **splitters** that build the 2-bit selects.
* **Rule:** `ForwardA = 10` if `RegWrite_mem` and `rd_mem != 0` and `rd_mem == rs1_ex` (value from EX/MEM); else `01` if the same holds for WB (value from MEM/WB); else `00` (register file).  EX/MEM wins because it is newer.  `rd != 0` stops x0 from being forwarded.
* **Two details:** the value taken from EX/MEM is the ALU result **except for JAL/JALR, where it is PC+4**; the forwarded B operand is also the store data.

**HazardUnit**
* **Purpose:** detect a load followed immediately by an instruction that uses its result.
* **Inputs / outputs:** `MemRead_ex`, `rd_ex`, `rs1_id`, `rs2_id` in; `stall` out.
* **Inside:** 3 **comparators** (5 bit), **OR**, **NOT**, a 3-input **AND**.
* **Rule:** `stall = MemRead_ex AND rd_ex != 0 AND (rd_ex == rs1_id OR rd_ex == rs2_id)`.  Effect: `run = not stall` freezes the PC and IF/ID, and the control word entering ID/EX is replaced by 0 (a bubble).
* **Experiment:** load `programs\hazards_demo.hex` into `Pipeline`, tick 12 times and fill the table of `docs/DEMO_EXPLAIN.md` section 6 yourself with the probes `stall`, `pc_src_ex`, `ForwardA`, `ForwardB` before reading it.
* **Check:** Why can a load not be forwarded like an ALU result?  Why one stall and not two?  Which comparator catches `rd_ex == rs2_id`?

### Session 10: control hazards and performance
**Read:** `docs/REPORT.md` sections 5.5, 5.6, 8; `docs/GUIDE.md` section 9.
* **Idea:** branches, JAL and JALR are resolved in **EX**: `pc_src_ex = branch_taken OR IsJAL OR IsJALR`.  The next PC becomes the target, the instruction being fetched becomes 0 (`instr_in = 0`), and the control word entering ID/EX is zeroed: the two instructions behind the branch are cancelled.  Cost: 2 cycles per taken branch; a not-taken branch costs nothing (static "not taken").
* **Penalties (measured):** forwarding 0, load-use 1, taken branch / jump 2.
* **Why the pipeline looks slower in cycles:** Logisim has no gate delays; the gain is a shorter clock period (one stage instead of five), which this simulation cannot show.  Improvement ideas: resolve JAL in ID, branch predictor, branch-target buffer.
* **Experiment:** explain the numbers of the results table (`demo`: 39 instructions, 64 cycles: 11 taken redirects x 2 = 22, plus 3 for the fill).
* **Check:** Why is `x5 = x6 = 0` the proof that the flush works?  What would happen with no flush?

**Phase test:** draw the pipeline diagram (IF ID EX ME WB per cycle) of `hazards_demo.s` on paper, then compare with `docs/DEMO_EXPLAIN.md` section 6.

---

## Phase 6 - Programs, tests, tools, demo (sessions 11-12)

### Session 11: programs and verification
**Read:** `docs/GUIDE.md` sections 10-11, `docs/TOOLS.md`, `docs/REPORT.md` section 7.
* **Assembler** (`tools\rv.py asm`): labels, pseudo instructions (`li`, `mv`, `bnez`, `ret`, `j`), the check macro, produces the ROM image (`v2.0 raw` hex).
* **Reference simulator** (`tools\rv.py sim`): written independently of the circuits; the "oracle" of all tests.
* **Headless runner** (`tools\java\Run.java`): loads the ROM, toggles the clock, reads PC, registers and RAM from the real circuit.
* **Three test levels:** (1) module test vectors (`tests\run_tests.ps1`, 106 rows, 9 files); (2) programs on both CPUs vs the reference (`tests\run_cpu_tests.py`, 7 programs); (3) random programs (`tests\fuzz.py`).
* **Do:** write `test1.s` (the factorial of `docs/PRESENTATION.md` step 12), run `python tools\live_proof.py test1.s`; then change one instruction and predict the result before running.
* **Check:** Why must the reference simulator be independent?  What does the fuzzer find that hand-written tests do not?

### Session 12: the generator, the pitfalls, the demo
**Read:** `docs/DESIGN_LOG.md`, `docs/COMPONENTS.md` sections 0 and 7, `docs/PRESENTATION.md`, `docs/DEMO_EXPLAIN.md`.
* **Generated circuits:** `tools\build` writes the circuits from netlists and verifies every net (rebuild: `python tools\build\build_all.py tools\build\base.circ RiscVComputer.circ`).
* **Bugs found and fixed** (REPORT section 9): SLTU extended with sign; ALUControl SLL used the SRL code; JALR decoded as JAL; U-type missing `<< 12`; RAM with synchronous read.  Learn to say *how a test found each of them*.
* **Pitfalls:** Logisim connects wires only at end points; everything on the 10-px grid; `Constant` defaults to 1; RAM defaults to synchronous read.
* **Do:** one full rehearsal of the demo (`docs/PRESENTATION.md`) with a partner asking the questions of `docs/TEAM_SPLIT.md`.
* **Final exam (no notes):** (1) draw `main` and `Pipeline`; (2) trace `lw` followed by a dependent `addi` through the pipeline; (3) explain three bugs; (4) explain why the proof can be trusted.

---

## What "learned" means: self-assessment

| Level | You can ... |
|---|---|
| 1 | name every circuit and say what it does in one sentence |
| 2 | list the components inside every circuit and say why they are there |
| 3 | trace any instruction through `main` with real values |
| 4 | predict the pipeline behaviour (stall, forwarding, flush) of a short program |
| 5 | explain how the project is tested and why the result can be trusted |

Aim for level 5 on your own part (`docs/TEAM_SPLIT.md`) and level 3 on the other two parts.

## Reading order cheat sheet

`README.md` > `docs/GUIDE.md` (1, 2, 4, 5, 6, 7, 8, 9, 10, 11) > `docs/REPORT.md` > `docs/COMPONENTS.md` (details of every component) > `docs/DEMO_EXPLAIN.md` (real values) > `docs/PRESENTATION.md` (the show) > `docs/TOOLS.md`, `docs/DESIGN_LOG.md` (how it was built).
