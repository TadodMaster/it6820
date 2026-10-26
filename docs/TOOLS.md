# Tools reference: how the toolchain works inside

Everything that is not a circuit lives in `tools/` and `tests/`.  This page explains each tool: purpose, usage, how it works, and its limits.
For the CPU itself read [GUIDE.md](GUIDE.md).

```
programs/*.s --rv.py asm--> *.hex --(ROM contents)--> circuit
                  |                                      |
                  +--rv.py sim (reference)               +--Run.java (headless run) --> registers / memory
                            \                                         /
                             +------------- compare ------------------+   tests/run_cpu_tests.py, tests/fuzz.py

tools/build/*.py --(netlists)--> RiscVComputer.circ --Ends.java--> pin positions   (used while generating)
                                        |
                                        +--Render.java--> docs/img/*.png
                                        +--verify.py  (checks the saved nets)
```

| Tool | File | Needs |
|---|---|---|
| Assembler + reference simulator | `tools/rv.py` | Python 3.10 |
| Headless runner | `tools/java/Run.java` | JDK 21 + the Logisim jar |
| Net probe / trace | `tools/probe.py` | the above |
| Renderer (PNG of a circuit) | `tools/java/Render.java` | the above |
| Pin position dump | `tools/java/Ends.java` | the above |
| Circuit generator | `tools/build/` | the above |
| Test runners | `tests/run_tests.ps1`, `tests/run_cpu_tests.py`, `tests/fuzz.py` | the above |

Set the environment variable `JAVA` to a JDK 21 `java.exe` if `java` on the PATH is older (`$env:JAVA = "C:\Program Files\Java\jdk-21.0.12.1\bin\java.exe"`).
`powershell -File tools\compile.ps1` compiles the Java files into `tools/bin` (needs `javac`).

---

## 1. `tools/rv.py` - assembler and reference simulator

`python tools/rv.py asm prog.s [-o prog.hex] [-l]` and `python tools/rv.py sim prog.s [-n max_steps]`.  It can also be imported (`import rv`):
`rv.assemble(text) -> (words, listing, labels)`, `rv.Sim(words)`, `rv.to_hex(words)`.

### Assembler
Two passes:
1. **Pass 1** reads the lines, strips comments (`#` or `;`), collects labels (`name:` gives the address of the next *machine* instruction), and **expands pseudo instructions** into
   real ones.  Because the expansion of `li` can be one or two instructions, the addresses are only known after expansion.
2. **Pass 2** encodes every instruction with the bit layouts of RV32I (`enc_r`, `enc_i`, `enc_s`, `enc_b`, `enc_u`, `enc_j`); label operands become `label - current address`
   for branches and jumps.  Range errors (immediate too big, branch too far, odd offsets) raise `AsmError` with the line number.

`li rd, v` becomes `addi rd, x0, v` if `v` fits in 12 bits, else `lui rd, hi` + `addi rd, rd, lo` where `lo` is the sign-extended low 12 bits and `hi` is corrected by +1 when `lo` is negative.
`chk rd, v` is a self-check macro for the tests (`li x30, v` + `bne rd, x30, fail`).

Output format (Logisim "raw" memory image): first line `v2.0 raw`, then one 32-bit hex word per line (Logisim also accepts several per line).

### Reference simulator (`rv.Sim`)
A plain Python model of the architecture, deliberately independent of the circuits:
* 32 registers (x0 forced to 0), PC, 256-word ROM, 256-word data memory (`(addr >> 2) & 0xFF`, so addresses wrap like the hardware);
* `step()` decodes the opcode and executes (R, I, load, store, branch, LUI, AUIPC, JAL, JALR); unknown opcodes (fence, ecall) act as NOPs;
* sub-word loads and stores use the same byte / halfword selection as the hardware (`lh` at an odd address uses the aligned halfword, like `LoadExtract`);
* `run()` stops when an instruction jumps to itself (the `halt: j halt` convention) or after `max_steps`.

Limits: no CSRs, no traps, no misaligned-access exceptions.

---

## 2. `tools/java/Run.java` - run a program on a circuit without the GUI

```
java -cp "logisim-evolution-4.1.0-all.jar;tools\bin" Run <file.circ> <circuit> <program.hex> <cycles> [trace|x] [@probe ...]
```

How it works (it uses Logisim's own Java classes):
1. `LogisimFile.load` loads the project; the circuit named `<circuit>` must contain exactly one ROM; its contents attribute (`Rom.CONTENTS_ATTR`) is overwritten with the words of the hex file.
2. `CircuitState.createRootState(project, circuit, Thread.currentThread())` creates a simulation state whose propagator belongs to the *main thread* (the normal
   `Project`/`Simulator` creates its own thread and refuses calls from elsewhere).
3. For each cycle: `propagator.toggleClocks(); propagator.propagate();` twice (rising and falling edge).  The `Clock` component of the circuit is what is toggled.
4. After the run it prints `CYCLES=`, `PC=` (the register labelled `PC`), `x0..x31` (the registers labelled `x0..x31` inside the sub-circuit state `RegisterFile`) and
   every non-zero word of the RAM inside the sub-circuit state `Memory`, as `MEM[addr]=value`.  State classes like `RegisterData` are package-private, so they are read by reflection.
5. **Trace mode** (`trace`) prints `T <cycle> PC=<hex> <probe values...>` after every cycle.  **Probes** are `@x,y` (a point in the top circuit) or `@Circuit:x,y` (inside a
   sub-circuit); the value of the wire at that point is printed (`U` = undefined bit, `E` = error, `-` = no wire at that point).

Why registers are labelled: the generator names the 32 registers `x0..x31` and the PC register `PC` precisely so that tools can find them.

## 3. `tools/probe.py` - look at named signals

`python tools/probe.py [--trace] file.circ circuit prog.s cycles label...` assembles the program, looks up the **tunnel names** in the circuit to find a wire location for each label,
and calls `Run` with those probes.  Without `--trace` it prints the values after `cycles` cycles; with `--trace` it prints a table with one row per cycle.  Example:

```powershell
python tools\probe.py RiscVComputer.circ main programs\demo.s 2 pc instr rs1_data rs2_data alu_result wb_data
python tools\probe.py --trace RiscVComputer.circ Pipeline programs\hazards_demo.s 12 pc_if pc_id pc_ex stall ForwardA
```
Multi-bit values are printed in hex without leading zeros for narrow buses (`0a`, `2`).  Values are the state *after* the given number of full clock cycles.

## 4. `tools/java/Render.java` and `Ends.java`

* `Render <file.circ> <outdir> <circuit|ALL> <scale>` draws a circuit into `<outdir>/<circuit>.png` with Logisim's own drawing code (`Circuit.draw`).  (Use the word `ALL`: on Windows
  `java` expands a bare `*` to file names.)
* `Ends <file.circ> [circuit]` prints for every component its location, bounding box and the **exact positions, widths and directions of all its pins**.  This is how the generator
  learns where to attach wires: no pin offsets are hard-coded.

---

## 5. `tools/build/` - the circuit generator

`python tools/build/build_all.py <base.circ> <out.circ>` reads the hand-drawn library (`base.circ`: ALU, InstructionDecode, RegisterFile, ImmGen, ALUControl), (re)generates all other
circuits and writes the project.

| File | Content |
|---|---|
| `circgen.py` | the generator engine: `Project` (the .circ text), `Circ` (a circuit being built) |
| `blocks.py` | netlists of `MainControl`, `BranchUnit`, `LoadExtract`, `StoreMerge`, `Memory`, `ForwardingUnit`, `HazardUnit` |
| `cpus.py` | the single-cycle CPU `main`, the layout search `tightest()` |
| `pipeline.py` | the 5-stage pipeline |
| `fonts.py` | final pass: every font becomes `Monospaced` |
| `verify.py` | checks every generated circuit after saving |
| `build_all.py` | the driver: patches, generates, saves, verifies |

### Describing a circuit
```python
c = Circ(proj, "HazardUnit", spread=(1.5, 1.3))
c.pin_in("rd_ex", 5, (120, 180))                                   # circuit input pin
c.add("Comparator", (700, 300), {"width": 5, "mode": "unsigned"},  # component, location, attributes
      {"a": "rd_ex", "b": "rs1_id", "eq": "hit1"})                  # pin name -> net name
c.add("AND Gate", (1450, 300), {"inputs": 3}, {"in1": "MemRead_ex", "in2": "rd_ok", "in3": "uses", "out": "stall"})
c.pin_out("stall", 1, (1750, 300))
c.install()
```
A **net** is just a name; every pin with that name is connected.  `c.link(c1, "out", c2, "b")` draws a direct wire instead of tunnels.  Pin names per component are in `pin_names()`
(`a b out` for adders, `d0..dN sel out` for multiplexers, `bus b0..` for splitters, ...); for sub-circuits the names are the labels of the pins inside them.

### What `build()` does
1. **Probe**: writes a temporary project containing all components (no wires) and runs `Ends` on it to learn the real pin positions and bounding boxes.
2. **Net widths**: the width of every net is taken from its pins (probes report width 0 until connected, so the maximum is used).
3. **Stubs and tunnels**: every pin gets a short wire and a **tunnel** carrying the net name.  The router tries stub lengths in 10-px steps, sideways jogs, and (for pins on the top or
   bottom of a component) both directions, and accepts the first placement whose wire and label box do not touch any component, other stub or other label.  Pins that are only
   10 px apart (splitters, 8-input multiplexers, comparator outputs) are **fanned out**: stubs bend to rows 30 px apart with crossing-free jog columns and all labels line up.
4. **Wire splitting**: Logisim only connects wires at end points, so every wire is split at the end points of other wires.
5. **Text placement**: annotation texts are placed after routing and nudged away from anything they overlap.
6. **Lint**: width mismatches, nets with no driver, nets with several drivers, unused outputs are reported; any coordinate not on the 10-px grid is an error.
7. **Layout search** (`cpus.tightest`): the two CPUs are built with a series of layout scale factors (0.5 ... 1.15) until the router finds room for everything; the smallest wins.

### The verifier (`verify.py`)
After the file is saved it is read back **independently**: it takes the pin positions from `Ends`, joins wires at end points and tunnels by label, and checks for every generated circuit that
* all pins of one intended net really are one electrical net (otherwise "net X is split"),
* no two different intended nets are electrically joined ("SHORT"),
* every tunnel sits on a wire end.

This check exists because of real mistakes made while building the tool (open T-junctions, off-grid tunnels, two tunnels on the same point); see [DESIGN_LOG.md](DESIGN_LOG.md).
The build exits with an error code if any circuit fails.

### Editing rules
* Do **not** hand-edit the generated circuits in Logisim: the next build overwrites them.  Change the Python description.
* Hand-drawn blocks: open `tools/build/base.circ` in Logisim, edit, save, rebuild.
* New Logisim component types need an entry in `LIB` (library number) and `pin_names()` in `circgen.py`.

---

## 6. Test runners

* `tests/run_tests.ps1 [file.circ]` - for each module runs `java -jar logisim.jar --test-vector <circuit> tests/<module>.vec <file>` and prints `passed N, failed M`.
  `.vec` format: header line `pin[width] ...`; one row per test, values `0x...` hex or binary; inputs and expected outputs share the row.
  Limitation: in our experiments RAM contents did not persist from one row to the next, so the RAM is tested through whole programs.
* `tests/run_cpu_tests.py [--circuit main|Pipeline|all] [--circ file] [programs]` - assembles each program, runs the reference simulator, runs the circuit for
  `2 * steps + 24` cycles, compares all registers and every non-zero data word, checks the self-check value `x31 = 0x600D` (if the program uses it) and reports the cycle count.
* `tests/fuzz.py [--count N --seed S --length L]` - random programs: see the guide, section 11.  Failing programs are written to the temp directory as `fuzz_fail_<seed>.s`.

## 7. Known limits of the tools
* The assembler has no directives besides `.word`, no `%hi/%lo`, no sections.
* The ROM holds 256 words; larger programs are rejected.
* `Run.java` finds the ROM, registers and RAM by name / label; circuits that do not follow the naming (`PC`, `x0..x31`, sub-circuits `RegisterFile`, `Memory`) need small changes.
* The layout of generated circuits is functional rather than pretty: signals are named tunnels, not routed wires.
