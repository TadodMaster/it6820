# Presentation guide: setup and show, step by step

Goal: show the teacher that this is a **real RV32I computer**, that it **runs programs loaded into its instruction memory**, that it exists in **two versions
(single-cycle and 5-stage pipeline)**, that the pipeline **handles hazards**, and that it is **tested so well that you can prove it works**.

Everything in this guide was tried on this project: the menu names, the keyboard shortcuts, the file dialog and the expected values are the real ones
(Logisim Evolution 4.1.0, Java 21).

| Part | Content | Time |
|---|---|---|
| [1](#1-what-you-prove-and-the-plan) | what you prove and the 12-minute plan | |
| [2](#2-preparation) | one day before / 15 minutes before / 2 minutes before | |
| [3](#3-the-live-demo-step-by-step) | the demo, click by click, with the values to expect | 12 min |
| [4](#4-slides-outline) | 8 slides and what to say | |
| [5](#5-questions-the-teacher-may-ask) | questions and short answers | |
| [6](#6-if-something-goes-wrong) | problems, fixes, backup plan | |
| [7](#7-reference-tables) | expected values, shortcuts, commands | |

---

## 1. What you prove and the plan

**Five claims, and the evidence for each**

| Claim | Evidence you show |
|---|---|
| It is a complete RV32I computer | the ROM runs a real program: loop, memory, function call (`demo.s`); the instruction list in the report |
| Programs are loaded into the instruction memory, registers are never edited by hand | *Load Image...* of a `.hex` file made by our assembler; registers only change by executing |
| Two CPUs: single-cycle and 5-stage pipeline | circuits `main` and `Pipeline`, same blocks, same programs, same results |
| The pipeline solves data and control hazards | `hazards_demo.s`: load-use stall (PC stays on the same address for two ticks), forwarding, and **x5 = x6 = 0** after a taken branch (the flushed instructions had no effect) |
| It is correct | `tools\live_proof.py`: both CPUs equal an *independent* reference simulator on all 32 registers and memory; plus 106 module tests, 7 programs, random programs |

**Plan (12 minutes, two presenters: one talks, one drives the computer)**

| Minute | What | Where |
|---|---|---|
| 0-1 | goal and result in one sentence, show the architecture picture | slides 1-2 |
| 1-4 | single-cycle CPU running `demo.s`: tick by tick, registers change live | Logisim, circuit `main` |
| 4-5 | load a second program from a file | Logisim, *Load Image* |
| 5-8 | the pipeline: stages, a stall and a flush with `hazards_demo` | Logisim, circuit `Pipeline` |
| 8-10 | **proof**: the terminal shows both CPUs equal the reference; the tests | terminal |
| 10-11 | results, what we did not do | slides 7-8 |
| 11-12 | questions (also: "give us any program" - section 3, step 12) | |

---

## 2. Preparation

### 2.1 One day before
- [ ] The presentation computer has **Java 21 or newer** (`java -version` shows 21.x) and **Python 3.10+**.  Logisim 4.1.0 does not start on Java 17.
- [ ] Copy the whole `D:\hust\logisim` folder to the presentation computer *and* to a USB stick (the folder contains the jar, the circuits, the tools and the tests).
- [ ] On that computer run once: `powershell -File tools\compile.ps1` (compiles the Java helpers; needs the JDK).
- [ ] Run the pre-flight check (below).  Everything must say PASS.
- [ ] Rehearse the whole demo once, with a timer.  Decide who talks and who drives.
- [ ] Save backups on the desktop: the folder `docs\img` (pictures of every circuit), the output of `python tools\live_proof.py > proof.txt`, and a screen recording of your rehearsal.
- [ ] Print or open `docs\REPORT.md` (exported to PDF) in case the teacher asks for details.

### 2.2 Fifteen minutes before
1. Open **PowerShell** and go to the project:
   ```powershell
   cd D:\hust\logisim
   ```
2. Run the pre-flight check (about 1.5 minutes; `-Quick` = 30 seconds):
   ```powershell
   powershell -ExecutionPolicy Bypass -File tools\presentation_check.ps1
   ```
   You want: `READY: everything passed.`  Every line is PASS (Java, files, ROM contents, module tests, programs on both CPUs, random programs, live proof).
3. **Turn off notifications**: Windows `Win+N` > *Do not disturb* (or Focus assist), close Teams / Zalo / mail / Telegram.  A chat pop-up over the screen during the demo is embarrassing
   and may show private messages.
4. Close all Logisim windows.  Set the display so that everyone can read: Windows scaling 125-150 %, the terminal font large (`Ctrl + mouse wheel` in Windows Terminal).
5. Open these (side by side, or on two screens):
   - Logisim: `java -jar .\logisim-evolution-4.1.0-all.jar .\RiscVComputer.circ`  (opens `main`)
   - a terminal in `D:\hust\logisim`
   - an editor showing `programs\demo.s` (comments explain the program)

### 2.3 Two minutes before: the starting state
- Logisim shows circuit `main`.  Press **Ctrl+R** (Simulate > Reset Simulation): PC and all registers are 0.
- Click the **State** tab (bottom-left, next to *Properties*).  It lists `PC` and `RegisterFile/x0 ... x31` and shows their values live.  Make the panel taller if you can
  (drag the divider above *Properties | State* upward); otherwise scroll it.
- The `RESET` pin shows 0 (it must stay 0 while the program runs).
- The terminal is clear (`cls`), in `D:\hust\logisim`.

---

## 3. The live demo, step by step

The program `programs\demo.s` is already in the ROM of both CPUs.  What it does (say this before you start):

> It adds 10 + 9 + ... + 1 in a loop (result 55), stores the result in memory, loads it back, calls a small function that doubles it (110), and computes a few more values.

> For a complete explanation of **everything that happens in the demo** (every instruction, every signal, all 40 ticks, the pipeline cycle by cycle) see [DEMO_EXPLAIN.md](DEMO_EXPLAIN.md).

### 3.0 How to read the screen (read this once)

Three places show what the CPU is doing.  Always look at them in this order:

| Where | What it shows | When it changes |
|---|---|---|
| **State tab** (bottom-left) | `PC` and `x0..x31`: the *committed* state | after a tick, when the instruction has finished |
| **Monitor row** (bottom of the circuit, yellow probes with a Vietnamese description above each) | the signals of the instruction that is **about to execute** (single-cycle) or is in each stage (pipeline) | immediately, before the next tick |
| **Wires and register boxes** in the circuit | the values flowing through the datapath (a wire turns bright green = 1, dark green = 0; buses show their hex value) | after each tick |

**Probe rows.** `main` has three rows under the circuit (monitor, control, data); `Pipeline` has three rows too (monitor, ID/EX inputs, EX/MEM/WB data), each probe with a Vietnamese description above it.  Below the rows every circuit carries a Vietnamese explanation block (what the abbreviations mean, what the signals mean, the cases that can happen, why).  Scroll down once to show it.  In addition every component (splitter, register, multiplexer, adder, gate, constant, ROM/RAM, sub-circuit) has a small Vietnamese caption right next to it that says what it does at that place and why (2-3 lines, font 10).

**Important timing rule for the single-cycle CPU:** after a tick the PC already points to the *next* instruction, and the monitor row shows that instruction (`instr`) and what it *will* compute (`alu_result`, `branch_taken`, `wb_data`).  The register changes only at the **next** tick.  So the sequence for every instruction is:
1. before the tick: monitor row = `instr` and its result in `wb_data`; State tab still shows the old register value,
2. press **Ctrl+F9**: the State tab shows the new register value and the PC moves on.

**Rhythm of the demo:** say one sentence, press one tick, point at one thing, wait two seconds.  Never press two ticks while talking about the previous one.  Stop and explain at the ticks marked **STOP** in the tables below; between those, go quickly.

**If a value does not match the table**: do not click around.  Press **Ctrl+R**, start the step again, and tick slowly (see section 5, "If something goes wrong").

### Step 1 - Show the project (30 s)
In the left tree: `main` (single-cycle), `Pipeline`, and the blocks (`ALU`, `RegisterFile`, `MainControl`, ...).  "The two CPUs use exactly the same blocks."
Point at `main`: the headings **IF, ID, EX, MEM, WB**, the clock, the PC register, the ROM with the program.  "Each wire that leaves a block is a named tunnel; the same name means the same wire."

### Step 2 - Show the program in the ROM (30 s)
The ROM box in `main` shows the machine code (`00000513 00a00593 00b50533 ...`).  Switch to the editor with `demo.s`: "this is the assembly we wrote; our assembler turned it into these numbers".

### Step 3 - Reset (10 s)
**Ctrl+R**.  State tab: `PC = 00000000`, all registers 0.

### Step 4 - Execute tick by tick (2 min)
Press **Simulate > Manual Tick Full Cycle** (shortcut **Ctrl+F9**) once = one clock cycle = one instruction on the single-cycle CPU.  The State tab updates.  Expected values:

| After tick | PC | x10 | x11 | What happened |
|---:|---|---|---|---|
| 1 | 0x04 | 0 | 0 | `li x10,0` |
| 2 | 0x08 | 0 | 0x0a | `li x11,10` |
| 3 | 0x0c | **0x0a** | 0x0a | first `add x10,x10,x11`: 0 + 10 |
| 4 | 0x10 | 0x0a | 0x09 | `addi x11,x11,-1` |
| 5 | 0x08 | 0x0a | 0x09 | `bnez`: taken, PC goes back to the loop |
| 6 | 0x0c | **0x13** | 0x09 | second add: 10 + 9 = 19 |
| 9 | 0x0c | **0x1b** | 0x08 | 19 + 8 = 27 |
| 12 | 0x0c | **0x22** | 0x07 | 27 + 7 = 34 |

Say while ticking: "x10 is the running sum, x11 the counter. Each tick executes exactly one instruction."  Point at the **monitor row** at the bottom of the circuit (yellow probes, each with a Vietnamese description above it): `PC`, `instr` = the instruction being executed (for example `00b50533` = `add x10,x10,x11`), `alu_result`, `branch_taken`, `wb_data` = the value written to the register (`0000000a`).

**What to watch at each tick (single-cycle, program `demo.s`, values measured on the project).**  "Monitor row" = the value you see *after* the tick, i.e. for the instruction at the new PC:

| After tick | PC (State) | monitor `instr` | `alu_result` | `branch_taken` | `wb_data` | Look at / say |
|---:|---|---|---|---|---|---|
| 0 (reset) | 00 | `00000513` | 0 | 0 | 0 | everything is 0 |
| 1 | 04 | `00a00593` | 0a | 0 | 0a | `li x11,10` is next: its result `0a` is already on `wb_data`, x11 is still 0 in the State tab |
| 2 | 08 | `00b50533` | 0a | 0 | 0a | `add x10,x10,x11` is next; **x11 = 0a** now in the State tab |
| 3 | 0c | `fff58593` | 09 | 0 | 09 | **STOP**: x10 became **0a** (first sum); next is `addi x11,x11,-1` (result 09) |
| 4 | 10 | `fe059ce3` | 09 | **1** | 09 | **STOP**: `branch_taken` = 1 on the probe, the loop branch will be taken |
| 5 | **08** | `00b50533` | 13 | 0 | 13 | the PC went **back** to 08: the loop; `alu_result` 13 = 10 + 9 |
| 6 | 0c | `fff58593` | 08 | 0 | 08 | x10 = **13**, x11 = 09 |
| 7 | 10 | `fe059ce3` | 08 | 1 | 08 | taken again |
| 8 | 08 | `00b50533` | 1b | 0 | 1b | next sum 27 |
| 11 | 08 | `00b50533` | 22 | 0 | 22 | next sum 34 |

How to say it: "The probe `branch_taken` turns to 1 exactly when the loop jumps back; the PC then goes from 10 back to 08."  Three ticks make one loop iteration (add, addi, bnez), and it runs 10 times.
After tick 31 the probe already shows `branch_taken` = 0 (x11 = 0): the last `bnez` will not be taken; tick 32 moves the PC on to 14.  The loop is over, the milestones in step 5 take over.

### Step 5 - Run to the end (1 min)
Press **Ctrl+F9** until about tick 40 (or hold it; or `Simulate > Auto-Tick Enabled`, **Ctrl+K**, then switch it off).  Final state:

| PC | x1 | x10 | x12 | x13 | x14 | memory word 0 |
|---|---|---|---|---|---|---|
| 0x28 (the final `halt: j halt` loop) | 0x20 (return address) | 0x37 = 55 | 0x6e = 110 | 0x37 = 55 | 1 | 0x37 |

Milestones: tick 34 `lw` puts 0x37 in x12; tick 35 `jal` sets x1 = 0x20 and jumps to the function; tick 36 `double` makes x12 = 0x6e; tick 38 `sub` gives x13 = 0x37; tick 39 `slti` gives x14 = 1.
"55 and 110 are the right answers, and the program never touched a register directly: only the CPU wrote them."

### Step 6 - Load a different program from a file (1 min)
This shows that programs really come through the instruction memory.
1. In `main`, right-click the ROM box > **Load Image...**
2. In the file dialog type the path and press Enter:
   `D:\hust\logisim\programs\hazards_demo.hex`
3. The ROM now shows `06400093 00102023 00002103 ...`.  Press **Ctrl+R** (Reset Simulation), then **Ctrl+F9** eight times.

Expected on the single-cycle CPU after 8 ticks: PC = **0x24**, `x1 = 0x64` (100), `x2 = 0x64`, `x3 = 0x65` (101), `x4 = 0xc9` (201), `x7 = 7`, and **`x5 = x6 = 0`** (these two instructions are skipped by the taken branch: say "remember that").

### Step 7 - Open the pipeline (30 s)
Click the **Design** tab, double-click `Pipeline`.  The circuit is wide (five stages and four register banks).  "Fit to window" (**Auto** button, bottom-left) shows everything but too small to read: use
the **×½** or **×1** button and the scrollbars, stage by stage, left to right: IF, IF/ID, ID, ID/EX, EX, EX/MEM, MEM, MEM/WB, WB (the stage headings are in the picture).
The blue labels above the registers name them (`pc_id`, `instr_id`, `alu_result_mem`, ...) and each register box shows its value.  The State tab lists `PC` and the same registers `x0..x31`.
Tip: the report picture `docs\img\Pipeline.png` is a good overview slide.

### Step 8 - Run the pipeline and show hazards (2 min)
`Pipeline` has its own ROM, with `demo.s`.  Load the hazard program the same way (right-click its ROM, near the left of the circuit, **Load Image...** > `D:\hust\logisim\programs\hazards_demo.hex`), then **Ctrl+R**.
Tick with **Ctrl+F9** and watch the **PC** value in the State tab (this is the fetch address).  The monitor row at the bottom of the `Pipeline` circuit shows the same thing live: `PC`, `instr_id`, `stall` (1 at tick 5), `pc_src_ex` (1 when the branch is taken), `ForwardA` / `ForwardB` (`10` = taken from EX/MEM), `alu_result_ex`, `wb_data`:

| Tick | 1 | 2 | 3 | 4 | **5** | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| PC | 04 | 08 | 0c | 10 | **10** | 14 | 18 | 1c | 20 | 24 |

- **Tick 5: the PC did not move.** That is the **load-use stall**: `lw x2,0(x0)` is followed immediately by `addi x3,x2,1` which needs the loaded value; the pipeline holds the front for one cycle.
- **Ticks 6-8**: the PC goes on to `0x14`, `0x18`, `0x1c`: the `beq` at `0x14` is taken, but the two instructions behind it were already fetched.  At tick 9 the PC is `0x20` (the branch target; it equals the next sequential address here, so the PC alone does not prove the flush).  The proof of the flush is **`x5 = x6 = 0`** at the end: the two instructions behind the `beq` were turned into bubbles.
- Final values after about 13 ticks: `x1 = 0x64`, `x2 = 0x64`, `x3 = 0x65`, `x4 = 0xc9`, `x7 = 7`, and again **`x5 = x6 = 0`**: the flushed instructions did not change anything.
- Forwarding: `x3` and `x4` are correct although each depends on the instruction right before it (the value is taken from the EX/MEM or MEM/WB register, not from the register file).
- Afterwards the PC keeps cycling `0x24, 0x28, 0x2c` in the pipeline: normal, the `halt` jump flushes the instructions after it every time.

"Same program, same results as the single-cycle CPU - but five instructions are in flight at once."

**What to watch at each tick (pipeline, program `hazards_demo.hex`, values measured on the project).**  Values are those shown by the monitor row *after* the tick:

| After tick | `PC` | `instr_id` (instruction in ID) | `stall` | `pc_src_ex` | `ForwardA` | `ForwardB` | `alu_result_ex` | Look at / say |
|---:|---|---|:-:|:-:|:-:|:-:|---|---|
| 1 | 04 | `06400093` | 0 | 0 | 00 | 00 | 00 | `li x1,100` enters ID |
| 2 | 08 | `00102023` | 0 | 0 | 00 | 00 | 64 | `li` is in EX, result 64 |
| 3 | 0c | `00002103` | 0 | 0 | 00 | **10** | 00 | **STOP** (forwarding): `sw x1` needs x1 which `li` just computed: ForwardB = 10 = taken from EX/MEM |
| 4 | 10 | `00110193` | **1** | 0 | 00 | 00 | 00 | **STOP** (stall): `lw x2` is in EX, `addi x3,x2,1` in ID needs it: `stall` = 1 |
| 5 | **10** | `00110193` | 0 | 0 | 10 | 00 | 64 | the **PC did not move** (it held at 10): one bubble went into EX, `instr_id` is still the same `addi` |
| 6 | 14 | `00218233` | 0 | 0 | **01** | 00 | 65 | **STOP**: ForwardA = 01 = loaded x2 comes from MEM/WB, `alu_result_ex` 65 = 64 + 1 |
| 7 | 18 | `00420663` | 0 | 0 | **10** | 00 | c9 | `add x4,x3,x2` uses x3 from EX/MEM (ForwardA = 10), result c9 = 65 + 64 |
| 8 | 1c | `00100293` | 0 | **1** | 10 | 10 | 00 | **STOP** (flush): `beq` is in EX and is taken: `pc_src_ex` = 1 |
| 9 | 20 | `00000000` | 0 | 0 | 00 | 00 | 64 | `instr_id` = 00000000: the instruction behind the branch was **turned into a bubble** |
| 10 | 24 | `00700393` | 0 | 0 | 00 | 00 | 00 | `addi x7,x0,7` (the instruction after the skipped ones) |
| 12 | 2c | `00000000` | 0 | **1** | 00 | 00 | 00 | the final `halt: j halt` is in EX: it flushes again, this is normal forever after |

How to say it: "Three signals tell the whole story: `ForwardA/B` different from 00 means a value was taken from a pipeline register; `stall` = 1 means one bubble for a load; `pc_src_ex` = 1 means a jump and two flushed instructions."  Afterwards check the State tab: `x5 = x6 = 0` proves that the flushed instructions changed nothing.
Note: the tick numbers above are exact only if you pressed **Ctrl+R** after loading the program and then pressed **Ctrl+F9** once per tick without skipping.

### Step 9 - The proof (2 min, terminal)
```powershell
python tools\live_proof.py
```
(about 10 seconds).  It prints the program, then **a table with the reference simulator, the single-cycle CPU and the pipeline side by side** for every register and memory word, the cycle counts, and the verdict:

```
REGISTERS  (only registers that are not 0)
  reg         reference  single-cycle    pipeline   result
  x1  ra            20            20          20   OK
  x10 a0            37            37          37   OK
  ...
SPEED  (clock cycles until the last register write is done; 39 instructions up to that write)
  single-cycle      39 cycles  (CPI 1.00)
  5-stage pipeline  64 cycles  (CPI 1.64)
VERDICT: both CPUs produce exactly the reference result: all 32 registers and the data memory match.
```
Explain: "The reference simulator is a separate Python program, written independently of the circuits.  If the circuits agree with it on all 32 registers, they compute what a RISC-V machine must compute."
Then show the test suite (pick the ones you have time for; each prints `ALL PASSED`):
```powershell
powershell -File tests\run_tests.ps1                  # 9 module tests, 106 checks (~15 s)
python tests\run_cpu_tests.py --circuit all            # 7 programs on both CPUs (~20 s)
python tests\fuzz.py --count 5                         # 5 random programs on both CPUs (~15 s)
```

### Step 10 - Results (30 s)
- Instruction set: the whole RV32I base set (R, I, load / store of all sizes, all 6 branches, `jal`, `jalr`, `lui`, `auipc`).
- Single-cycle CPI = 1; pipeline CPI = 1.0 on straight code, +2 cycles per taken branch, +1 per load-use.
- 9 module test files (106 checks), 7 test programs, random-program fuzzing, an assembler, a reference simulator.
- Not done (optional in the assignment): branch prediction, cache, M extension, interrupts, UART, floating point.

### Step 11 - Show how a program is written (optional, 1 min)
```powershell
python tools\rv.py asm programs\demo.s -l -o programs\demo.hex
```
Shows the listing: address, machine code, source.  "This is the file that *Load Image* reads."

### Step 12 - "Give us any program" (if the teacher asks)
Create `D:\hust\logisim\test1.s`, for example computing 5! :
```
        li   x10, 1
        li   x11, 5
outer:  li   x12, 0
        mv   x13, x10
        mv   x14, x11
inner:  add  x12, x12, x13
        addi x14, x14, -1
        bnez x14, inner
        mv   x10, x12
        addi x11, x11, -1
        bnez x11, outer
halt:   j    halt
```
Then run **one command**: `python tools\live_proof.py test1.s` - it assembles the program, runs it on both CPUs and on the reference, and prints the verdict (here `x10 = 0x78` = 120, 76 cycles single-cycle, 107 pipeline).
Or load `test1.hex` into the ROM live: `python tools\rv.py asm test1.s -o test1.hex` and *Load Image...*.  (Do not offer this unless you rehearsed it; if the teacher's idea does not fit, say "we can try it right after".)

---

## 4. Slides outline

Use the pictures in `docs\img\` (`main.png`, `Pipeline.png`, `ALU.png`, `RegisterFile.png`, `MainControl.png`, `Memory.png`, ...).

| # | Title | Content | Say |
|---|---|---|---|
| 1 | Goal | assignment in one line: RV32I computer in Logisim, single-cycle + 5-stage pipeline | "We built and verified both." |
| 2 | Architecture | `main.png`; Harvard memories; blocks list | "Same blocks for both CPUs; named signals." |
| 3 | Instruction set | table of instruction groups (README), instruction formats | "All of RV32I except system instructions." |
| 4 | Single-cycle datapath | the five stages, control table (`MainControl`) | "One instruction per cycle." |
| 5 | Pipeline | `Pipeline.png`; 4 register banks; forwarding, stall, flush in 3 bullets | "Five instructions at once; hazards solved in hardware." |
| 6 | Verification | the 3 levels: module tests, programs, random; independent reference simulator | "How we know it works." |
| 7 | Results | CPI table (README); the demo values | "55 and 110, equal to the reference." |
| 8 | Limits and future work | not done: prediction, cache, M extension, UART | "Next: resolve jal in ID, a predictor." |

Order of the day: slides 1-3 (2 min) -> live demo steps 1-8 -> slide 6 + step 9 (proof) -> slides 7-8.

---

## 5. Questions the teacher may ask

| Question | Short answer |
|---|---|
| How do you know it is correct? | Three levels: 106 module checks run by Logisim itself, 7 programs and random programs compared register-by-register with a reference simulator that was written separately, and self-checking programs whose expected values were computed by hand (they end with `x31 = 0x600D`). |
| Is the reference simulator itself right? | It reproduces the encodings of the design notes (`addi x1,x0,5 = 0x00500093`, ...) and the self-checking programs do not depend on it. If both the circuit and the simulator were wrong in the same way, the hand-computed checks would still fail. |
| What bugs did you find? | In the first blocks: `SLTU` returned `0xFFFFFFFF` instead of 1; `SLL` selected the wrong ALU code; JALR / LUI had wrong decoding; the U-immediate lacked the shift; the memory never returned data (RAM was synchronous). All fixed and covered by tests. |
| Why is the pipeline not faster here? | Logisim counts cycles, not nanoseconds.  Pipelining shortens the *clock period* (only one stage in each cycle), which is not simulated.  The cycle count is higher because of the 2-cycle penalty for taken branches and the 1-cycle load-use stall. |
| How does forwarding work? | `ForwardingUnit` compares the source registers of the instruction in EX with the destination registers of the instructions in MEM and WB and selects the newer value for the ALU input. |
| Why a stall for load-use? | The loaded data exists only at the end of MEM, one stage too late for forwarding into the next instruction's EX. |
| What is `x0`? | A register that always reads 0; the register file keeps loading the constant 0 into it. |
| Why separate instruction and data memory? | Harvard organisation: no structural hazard in the pipeline, simpler. |
| Why is the RAM read asynchronous? | A load must deliver its data in the same cycle; Logisim's default RAM answers one cycle later. |
| What happens on a misaligned access? | Not supported: the hardware uses the aligned word / halfword. |
| Which instructions are missing? | `fence`, `ecall`, `ebreak`, CSR instructions (treated as no-ops), and everything outside the base RV32I set. |
| Why do you generate circuits with a program? | The hand-drawn first version had long crossing wires and open connections; generated circuits are repeatable and are verified automatically (every net is checked after saving). |
| What would you improve next? | Resolve `jal` in ID (penalty 1 instead of 2), a branch predictor, a UART, the M extension. |
| Can we run another program? | Yes: step 12; `python tools\live_proof.py yourprogram.s`. |

---

## 6. If something goes wrong

| Problem | Fix |
|---|---|
| Logisim does not start / error about class version | Java is older than 21: install JDK 21 or run with the full path `"C:\Program Files\Java\jdk-21.0.12.1\bin\java.exe" -jar ...` |
| Values show `x` or `E`, or nothing changes | **Ctrl+R** (Reset Simulation), make sure `RESET` shows 0, then tick again |
| Nothing happens when you tick | Use the menu *Simulate > Manual Tick Full Cycle* once (if *Auto-Tick Enabled* is on, switch it off with Ctrl+K) |
| The State tab shows only a few rows | scroll it, or drag the divider above *Properties \| State* upward |
| The ROM is empty or shows the wrong program | right-click the ROM > *Load Image...* > `D:\hust\logisim\programs\demo.hex` > Enter, then Ctrl+R |
| The file dialog does not accept the path | the Filename field is focused: type the full path with backslashes and press Enter; or navigate: `programs` folder > the `.hex` file |
| Different registers than expected after you loaded another program | Ctrl+R before running; the table values in this guide are for `demo.s` and `hazards_demo.s` only |
| Logisim freezes | wait 10 s; otherwise close it (choose *Don't save*) and reopen; show the terminal proof instead |
| `live_proof.py` fails | run `powershell -File tools\presentation_check.ps1` to see which step fails; check `$env:JAVA` |
| Windows notification pops up | dismiss it; next time enable Do not disturb |
| Teacher asks for something you cannot do live | say "we can show that after"; show the report (`docs\REPORT.md`) |

**Backup plan** if the computer or Logisim fails completely: the pictures in `docs\img\` (every circuit), the saved `proof.txt` (output of `live_proof.py`), and your rehearsal recording.
When closing Logisim at the end choose **Don't Save** if it asks (you loaded other programs into the ROM during the demo).

---

## 7. Reference tables

### Keyboard shortcuts and menu names (verified)
| Action | Menu | Shortcut |
|---|---|---|
| One full clock cycle | Simulate > Manual Tick Full Cycle | **Ctrl+F9** |
| Half a clock cycle | Simulate > Manual Tick Half Cycle | Ctrl+T |
| Free-running clock on / off | Simulate > Auto-Tick Enabled | Ctrl+K |
| Reset the simulation | Simulate > Reset Simulation | **Ctrl+R** |
| Live registers | the **State** tab, bottom-left | - |
| Load a program | right-click the ROM > **Load Image...** | - |
| Show the ROM as a hex editor | right-click the ROM > Edit Contents... | - |
| Zoom to fit / ×½ / ×1 / ×2 | buttons at the bottom-left | - |

Also in the Simulate menu: *Timing diagram* (waveforms of selected signals; not used in this guide, try it in a rehearsal if you want waveforms) and *Test Vector...* (runs a test-vector file).

### Expected values: `demo.s`
Single-cycle, after N ticks (PC points to the instruction about to execute): see the table in step 4; final: PC 0x28, x1 0x20, x10 0x37, x12 0x6e, x13 0x37, x14 1, memory[0] 0x37 (reached after 39 ticks).
Pipeline: the same final values after 64 ticks.  After exactly 20 ticks on the pipeline: PC 0x14, x10 0x1b, x11 0x07.

### Expected values: `hazards_demo.s`
Final (both CPUs): `x1 = 0x64, x2 = 0x64, x3 = 0x65, x4 = 0xc9, x7 = 7`, all other registers 0 (in particular `x5 = x6 = 0`).  Single-cycle: after 8 ticks (PC 0x24).  Pipeline: after 13 ticks; the PC sequence is 04 08 0c 10 **10** 14 18 1c 20 24.

### Commands (copy-paste)
```powershell
cd D:\hust\logisim
java -jar .\logisim-evolution-4.1.0-all.jar .\RiscVComputer.circ        # open the project
powershell -ExecutionPolicy Bypass -File tools\presentation_check.ps1   # pre-flight (add -Quick for 30 s)
python tools\live_proof.py                                              # the proof screen (demo program)
python tools\live_proof.py programs\hazards_demo.s                      # the proof for the hazard program
python tools\rv.py asm programs\demo.s -l -o programs\demo.hex          # assemble + listing
powershell -File tests\run_tests.ps1                                    # 9 module tests
python tests\run_cpu_tests.py --circuit all                             # programs on both CPUs
python tests\fuzz.py --count 5                                          # random programs
python tools\probe.py --trace RiscVComputer.circ Pipeline programs\hazards_demo.s 12 pc_if pc_id pc_ex stall pc_src_ex ForwardA ForwardB
```
The last command prints the cycle-by-cycle pipeline trace (which instruction is in IF / ID / EX, `stall`, `pc_src_ex` = flush, forwarding selects) as a table: a good backup if you cannot show the circuit.
