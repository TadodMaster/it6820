# Demo script

The assignment asks for a demo (video or live) in which a program runs on the CPU and the registers, memory and pipeline are
observed.  This is a script for a 5-8 minute demo of both CPUs.  Prepare: Java 21, open `RiscVComputer.circ`.

## 0. Setup (30 s)
* Open the project, show the project tree: `main` (single-cycle), `Pipeline`, and the blocks.
* Show `programs/demo.s` in an editor and the listing: `python tools\rv.py asm programs\demo.s -l -o programs\demo.hex`.

## 1. Single-cycle CPU (2 min)
1. Open `main`. Point out the stage headings IF, ID, EX, MEM, WB and the named signals (tunnels).
2. Right-click the ROM > *Edit Contents* to show the program (it is already loaded; or load `programs/demo.hex`).
3. Poke `RESET` 1 then 0. Use *Simulate > Tick Full Cycle* repeatedly:
   * watch `PC` count up and `instr` change (the probe next to the ROM shows the machine code);
   * open `RegisterFile` with the Poke tool (magnifier icon on the block): `x10` grows 10, 19, 27, ... up to 55;
   * after the `sw` / `lw` open `Memory` the same way: RAM word 0 holds 0x37.
4. Result after about 40 cycles: `x10 = 55 (0x37)`, `x12 = 110 (0x6E)`, `x13 = 55`, `x14 = 1`, `x1 = 0x20` (return address of the call).

## 2. Instruction by instruction (1 min)
Pick one instruction, e.g. `add x10,x10,x11`, and follow it: `instr` > `InstructionDecode` fields > `RegisterFile` read ports > ALU A/B
(`alu_a`, `alu_b`) > `alu_result` > `wb_data` > `RegisterFile` write.  Show `MainControl` outputs for a load (`MemRead`, `WBSel = 01`)
and for `jal` (`WBSel = 10`, `IsJAL`).

## 3. Pipeline (2-3 min)
1. Open `Pipeline`. Explain the five stages and the four register banks (IF/ID, ID/EX, EX/MEM, MEM/WB, labelled).
2. Reset, then tick: after each tick show which instruction is in which stage (`instr_id`, `pc_ex`, `alu_result_ex`, ...).
3. **Forwarding**: run to the `add x10,x10,x11` / `addi x11,x11,-1` pair - the `ForwardingUnit` outputs `ForwardA / ForwardB` change from 00 to 01 / 10.
4. **Branch flush**: the `bnez x11, loop` loop - when the branch is taken `pc_src_ex = 1`, the two following instructions become bubbles.
5. **Load-use stall**: load a value and use it immediately (e.g. paste `tests/programs/hazard.s` into the ROM) and show `stall = 1`, PC held for one cycle.
6. After about 65 cycles the result is identical to the single-cycle CPU (same registers).

## 4. Tests (1 min)
```powershell
powershell -File tests\run_tests.ps1                  # 9 module test files
python tests\run_cpu_tests.py --circuit all            # programs on both CPUs vs the reference simulator
python tests\fuzz.py --count 10                        # random programs
```
Show the `ALL PASSED` lines and the cycle / CPI table.

## Checklist for the submission
* source: `RiscVComputer.circ`, `programs/`, `tools/`, `tests/` (everything in this folder)
* technical report: `docs/REPORT.md` (export to PDF / Word, 10-20 pages with the figures from `docs/img`)
* module tests and CPU tests: `tests/`
* this demo
* README: `README.md`
