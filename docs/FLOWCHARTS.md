# Flowcharts of each circuit

> English version of docs/vi/FLOWCHARTS.md (the Vietnamese file is the original).

This document draws a **flowchart for all 14 circuits** of the project, with a detailed step-by-step explanation, examples with real values, and special cases.  The diagrams are written in **Mermaid**, so they render automatically on GitHub, in VS Code (with a Markdown Mermaid extension), or in Obsidian.  If your viewer does not render them, paste the code into https://mermaid.live.

**How to read the notation**

| Symbol | Meaning |
|---|---|
| rectangle | a processing step or a circuit block |
| diamond | a **selection** (multiplexer) or a condition |
| rounded shape | an input or output of the circuit |
| labeled arrow | the condition or signal value that selects that branch |

Contents: 0 Overview - 1 InstructionDecode - 2 MainControl - 3 ImmGen - 4 RegisterFile - 5 ALUControl - 6 ALU - 7 BranchUnit - 8 LoadExtract - 9 StoreMerge - 10 Memory - 11 `main` (single-cycle) - 12 ForwardingUnit - 13 HazardUnit - 14 `Pipeline` - 15 Quick comparison table

---

## 0. Overview: the whole computer from a distance

```mermaid
flowchart LR
    PC(["PC<br/>instruction address"]) --> ROM["Instruction ROM<br/>256 x 32"]
    ROM -->|"32-bit instruction"| ID["InstructionDecode<br/>cuts into fields"]
    ID --> CTL["MainControl<br/>generates control signals"]
    ID --> RF["RegisterFile<br/>reads rs1, rs2"]
    ID --> IMM["ImmGen<br/>builds the imm constant"]
    CTL -. "ALUOp" .-> ALUC["ALUControl"]
    ALUC -. "ALUCtrl" .-> ALU["ALU<br/>computes the result"]
    RF --> ALU
    IMM --> ALU
    RF --> BR["BranchUnit<br/>is the branch taken?"]
    ALU --> MEM["Memory<br/>RAM + LoadExtract + StoreMerge"]
    ALU --> WB{"select the value<br/>to write back (WBSel)"}
    MEM --> WB
    WB --> RF
    BR --> NPC{"select next PC"}
    ALU --> NPC
    NPC --> PC
```

**How to read it.**  In each cycle the CPU does exactly one loop: fetch the instruction from ROM at PC, cut the instruction, read registers and build the constant, the ALU computes, (if needed) access RAM, select the value to write back into register `rd`, and select the next PC.  Dashed lines are control signals, solid lines are data.  The `main` CPU does this whole loop in **one** clock cycle; the `Pipeline` CPU splits the loop into 5 stages so that five instructions run overlapped.

---

## 1. InstructionDecode - cutting the instruction into fields

```mermaid
flowchart TD
    I(["Instruction<br/>32 bit"]) --> S["Splitter 32 into 6 parts<br/>just wiring, no gates"]
    S --> O["opcode = bit 6..0"]
    S --> RD["rd = bit 11..7"]
    S --> F3["funct3 = bit 14..12"]
    S --> R1["rs1 = bit 19..15"]
    S --> R2["rs2 = bit 24..20"]
    S --> F7["funct7 = bit 31..25"]
```

**Step-by-step explanation.**
1. The 32-bit instruction goes into a single splitter.
2. The splitter divides the bus into six wires at **fixed** bit positions: `opcode` (7 bits), `rd` (5), `funct3` (3), `rs1` (5), `rs2` (5), `funct7` (7).
3. There is no computation: this is just wiring, so it costs no time and there is nothing that can go wrong.

**Example:** instruction `00b50533` -> `opcode = 0x33` (R-type), `rd = 10`, `funct3 = 0`, `rs1 = 10`, `rs2 = 11`, `funct7 = 0` -> this is `add x10, x10, x11`.

**Special case:** U/J-type instructions have no real `rs1`/`rs2`/`funct3`; those bits are still cut out but the later blocks ignore them.  Because RISC-V always places `rs1` and `rs2` in the same spot, the registers can be read **while** the opcode is still being decoded.

---

## 2. MainControl - generating every control signal from the opcode

```mermaid
flowchart TD
    OP(["opcode 7 bit"]) --> C{"compare opcode with 9 constants<br/>one comparator per group"}
    C -->|"0x33"| R["IsR<br/>add, sub, and, or, sll..."]
    C -->|"0x13"| I["IsI<br/>addi, andi, slli..."]
    C -->|"0x03"| L["IsLoad<br/>lb, lh, lw, lbu, lhu"]
    C -->|"0x23"| S["IsStore<br/>sb, sh, sw"]
    C -->|"0x63"| B["IsBranch<br/>beq, bne, blt..."]
    C -->|"0x37"| LUI["IsLui"]
    C -->|"0x17"| AU["IsAuipc"]
    C -->|"0x6F"| J["IsJAL"]
    C -->|"0x67"| JR["IsJALR"]
    C -->|"other"| N["all flags = 0<br/>safe empty instruction (NOP)"]
    R --> OR1["OR gates combine flags"]
    I --> OR1
    L --> OR1
    S --> OR1
    B --> OR1
    LUI --> OR1
    AU --> OR1
    J --> OR1
    JR --> OR1
    OR1 --> RW(["RegWrite = R, I, load, lui, auipc, jal, jalr"])
    OR1 --> AS(["ALUSrc = I, load, store, lui, auipc, jalr"])
    OR1 --> AO(["ALUOp 2 bit<br/>bit1 = R or I, bit0 = I or branch"])
    OR1 --> IM(["ImmSel 3 bit<br/>I 000, S 001, B 010, U 011, J 100"])
    OR1 --> ASEL(["ASel 2 bit<br/>00 rs1, 01 PC, 10 zero"])
    OR1 --> WBS(["WBSel 2 bit<br/>00 ALU, 01 RAM, 10 PC+4"])
    OR1 --> OTH(["MemWrite = IsStore<br/>MemRead = IsLoad<br/>IsBranch, IsJAL, IsJALR"])
```

**Step-by-step explanation.**
1. Nine 7-bit comparators compare `opcode` with nine constants; only one reports "equal", producing the flag of that instruction group (`IsR`, `IsI`...).
2. OR gates (at most 3 inputs, so split into two halves) combine the flags into each signal: for example `RegWrite` is on for every group that **writes `rd`**; store and branch are not included, so they do not write registers.
3. Multi-bit signals (`ALUOp`, `ImmSel`, `ASel`, `WBSel`) are assembled from single bits with a splitter.
4. An unknown opcode makes every flag 0, so the instruction does nothing (NOP) without corrupting the state.

**Result table for some instructions** (checked with `tests/maincontrol.vec`):

| Instruction | RegWrite | ALUSrc | MemWrite | MemRead | ALUOp | ImmSel | ASel | WBSel |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `add` (R) | 1 | 0 | 0 | 0 | 10 | - | 00 | 00 |
| `addi` (I) | 1 | 1 | 0 | 0 | 11 | 000 | 00 | 00 |
| `lw` | 1 | 1 | 0 | 1 | 00 | 000 | 00 | 01 |
| `sw` | 0 | 1 | 1 | 0 | 00 | 001 | 00 | - |
| `beq` | 0 | 0 | 0 | 0 | 01 | 010 | 00 | - |
| `lui` | 1 | 1 | 0 | 0 | 00 | 011 | 10 | 00 |
| `auipc` | 1 | 1 | 0 | 0 | 00 | 011 | 01 | 00 |
| `jal` | 1 | - | 0 | 0 | - | 100 | - | 10 |
| `jalr` | 1 | 1 | 0 | 0 | 00 | 000 | 00 | 10 |

---

## 3. ImmGen - building the immediate constant

```mermaid
flowchart TD
    IN(["Instruction + ImmSel"]) --> SEL{"ImmSel"}
    SEL -->|"000 I-type"| TI["take instr 31..20 (12 bit)<br/>sign-extend to 32 bit"]
    SEL -->|"001 S-type"| TS["join instr 31..25 and 11..7 (12 bit)<br/>sign-extend"]
    SEL -->|"010 B-type"| TB["join bit 31, 7, 30..25, 11..8, then bit 0 = 0 (13 bit)<br/>sign-extend"]
    SEL -->|"011 U-type"| TU["take instr 31..12<br/>append 12 zero bits (imm shifted left 12)"]
    SEL -->|"100 J-type"| TJ["join bit 31, 19..12, 20, 30..21, then bit 0 = 0 (21 bit)<br/>sign-extend"]
    TI --> MUX{"8-way multiplexer<br/>selected by ImmSel"}
    TS --> MUX
    TB --> MUX
    TU --> MUX
    TJ --> MUX
    MUX --> OUT(["Imm 32 bit"])
```

**Step-by-step explanation.**
1. All five ways of building the constant run **in parallel** from the same instruction (each is a few splitters plus a bit extender).
2. The multiplexer selects the result of exactly one way according to `ImmSel` (generated by `MainControl`).
3. **Sign extension** copies the highest bit of the constant into the upper bits, so negative numbers stay negative.  The U-type does not extend but inserts 12 zero bits (`lui`/`auipc` put the constant into the upper 20 bits).
4. Bit 0 of the B and J types is always 0 because instruction addresses are multiples of 2 (in practice 4); the instruction therefore does not store this bit.

**Example:** `fe059ce3` (`bnez x11, loop`, B-type): imm[12] = 1, imm[11] = 1, imm[10:5] = 111111, imm[4:1] = 1100, bit 0 = 0 -> 13 bits `1111111111000` -> sign-extended to **`0xFFFFFFF8` = -8**: jump back 8 bytes to the start of the loop.

---

## 4. RegisterFile - read two registers, write one register

```mermaid
flowchart TD
    subgraph READ["Read (asynchronous, no clock wait)"]
        RS1(["rs1"]) --> M1["Mux 32:1<br/>selects register number rs1"]
        RS2(["rs2"]) --> M2["Mux 32:1<br/>selects register number rs2"]
        M1 --> D1(["rs1_data"])
        M2 --> D2(["rs2_data"])
    end
    subgraph WRITE["Write (at the clock edge)"]
        RW(["RegWrite"]) --> DM["Demux 1:32<br/>selected by rd"]
        RD(["rd"]) --> DM
        DM -->|"only register number rd has WE = 1"| REG["32 registers x0..x31<br/>x0 always loads zero"]
        WD(["write_data"]) --> REG
        CLK(["CLK"]) --> REG
    end
    REG --> M1
    REG --> M2
```

**Step-by-step explanation.**
1. **Read:** two 32-way multiplexers select the register by `rs1` and `rs2`; since there is no clock here, changing `rs1` changes `rs1_data` immediately (the single-cycle CPU needs the operands within the cycle).
2. **Write:** the demultiplexer sends `RegWrite` to **exactly one** register (number `rd`); that register loads `write_data` at the clock edge, the other registers keep their values.
3. `x0` has its input tied to 0 so it stays 0 forever, no matter what is written.

**Cases:** `RegWrite = 0` (store, branch) -> no register changes; `rd = 0` -> the write to x0 has no effect; reading and writing the same register in one cycle -> reads the old value (on the pipeline, this block writes at the **falling** edge so the instruction in ID sees the new value).

---

## 5. ALUControl - choosing the ALU operation

```mermaid
flowchart TD
    IN(["ALUOp, funct3, funct7"]) --> Q{"ALUOp"}
    Q -->|"00"| ADD0["ALUCtrl = 0 (ADD)<br/>load, store, lui, auipc, jalr"]
    Q -->|"01"| SUB0["ALUCtrl = 1 (SUB)<br/>branch: compare by subtraction"]
    Q -->|"10 R-type"| TR{"funct3"}
    Q -->|"11 I-type"| TI{"funct3"}
    TR -->|"000"| RAS{"funct7 bit 5"}
    RAS -->|"0"| RADD["ADD (0)"]
    RAS -->|"1"| RSUB["SUB (1)"]
    TR -->|"001"| RSLL["SLL (5)"]
    TR -->|"010"| RSLT["SLT (8)"]
    TR -->|"011"| RSLTU["SLTU (9)"]
    TR -->|"100"| RXOR["XOR (4)"]
    TR -->|"101"| RSR{"funct7 bit 5"}
    RSR -->|"0"| RSRL["SRL (6)"]
    RSR -->|"1"| RSRA["SRA (7)"]
    TR -->|"110"| ROR["OR (3)"]
    TR -->|"111"| RAND["AND (2)"]
    TI -->|"000"| IADD["ADD (0): addi"]
    TI -->|"001"| ISLL["SLL (5): slli"]
    TI -->|"010"| ISLT["SLT (8): slti"]
    TI -->|"011"| ISLTU["SLTU (9): sltiu"]
    TI -->|"100"| IXOR["XOR (4): xori"]
    TI -->|"101"| ISR{"funct7 bit 5"}
    ISR -->|"0"| ISRL["SRL (6): srli"]
    ISR -->|"1"| ISRA["SRA (7): srai"]
    TI -->|"110"| IOR["OR (3): ori"]
    TI -->|"111"| IAND["AND (2): andi"]
```

**Step-by-step explanation.**
1. `ALUOp`, supplied by `MainControl`, splits into four branches: 00 add, 01 subtract (no need to look at `funct`), 10 look up the R-type table, 11 look up the I-type table.
2. For R and I, `funct3` selects the operation (two 8-way multiplexers, one per table; each table row is a 4-bit constant).
3. `funct7[5]` (bit 30 of the instruction) does two things: in R-type it turns ADD into SUB and SRL into SRA; in I-type it only matters for shift instructions (`srai` differs from `srli`).  `addi` ignores this bit because it is part of the constant.

**Output codes:** 0 ADD, 1 SUB, 2 AND, 3 OR, 4 XOR, 5 SLL, 6 SRL, 7 SRA, 8 SLT, 9 SLTU.

---

## 6. ALU - compute in parallel, then select

```mermaid
flowchart TD
    A(["rs1_data (A)"]) --> P["compute ALL operations IN PARALLEL"]
    B(["rs2_data (B)"]) --> P
    P --> R0["A + B (ADD)"]
    P --> R1["A - B (SUB)"]
    P --> R2["A and B"]
    P --> R3["A or B"]
    P --> R4["A xor B"]
    P --> R5["A shifted left by B[4:0] (SLL)"]
    P --> R6["A logical shift right by B[4:0] (SRL)"]
    P --> R7["A arithmetic shift right by B[4:0] (SRA)"]
    P --> R8["A less than B, signed<br/>zero-extend to 0 or 1"]
    P --> R9["A less than B, unsigned<br/>zero-extend to 0 or 1"]
    R0 --> MX{"16-way Mux<br/>selected by ALU_Ctrl"}
    R1 --> MX
    R2 --> MX
    R3 --> MX
    R4 --> MX
    R5 --> MX
    R6 --> MX
    R7 --> MX
    R8 --> MX
    R9 --> MX
    CT(["ALU_Ctrl 0..9"]) --> MX
    MX --> OUT(["result 32 bit"])
```

**Step-by-step explanation.**
1. Ten operations run at the same time from the same two operands; no operation "knows" which one is selected.
2. The 16-way multiplexer (using 10 inputs) takes exactly one result according to `ALU_Ctrl` (from `ALUControl`).
3. Shift instructions use only the low 5 bits of B (shift at most 31).  SRL inserts 0 bits at the top, SRA copies the sign bit.
4. SLT/SLTU produce a 1-bit result; **zero-extend** it to 32 bits to get exactly 0 or 1.  (A bug we hit: sign extension made SLTU return `0xFFFFFFFF`.)

**Example:** A = -1 (`0xFFFFFFFF`), B = 1: SLT gives 1 (since -1 < 1 signed), SLTU gives 0 (since 4294967295 is not less than 1).  Overflow in add/subtract is ignored: the result wraps around at 32 bits exactly as in RISC-V.

---

## 7. BranchUnit - is the branch taken

```mermaid
flowchart TD
    IN(["rs1_data, rs2_data, funct3, IsBranch"]) --> CMP["compare rs1 with rs2<br/>equal, less than signed, less than unsigned<br/>and their negations"]
    CMP --> F{"funct3"}
    F -->|"000 beq"| C0["equal"]
    F -->|"001 bne"| C1["not equal"]
    F -->|"100 blt"| C4["less than, signed"]
    F -->|"101 bge"| C5["greater than or equal, signed"]
    F -->|"110 bltu"| C6["less than, unsigned"]
    F -->|"111 bgeu"| C7["greater than or equal, unsigned"]
    F -->|"010, 011"| C2["not a branch instruction<br/>condition = 0"]
    C0 --> AND
    C1 --> AND
    C4 --> AND
    C5 --> AND
    C6 --> AND
    C7 --> AND
    C2 --> AND
    AND{"IsBranch = 1<br/>AND condition true?"} -->|"yes"| T(["branch_taken = 1<br/>PC = PC + imm"])
    AND -->|"no"| N(["branch_taken = 0<br/>PC = PC + 4"])
```

**Step-by-step explanation.**
1. One unsigned comparator and one signed comparator produce the "equal" and "less than" relations; three NOT gates produce the negations ("not equal", "greater than or equal").
2. An 8-way multiplexer driven by `funct3` selects the condition of exactly the branch instruction being executed.
3. The AND gate with `IsBranch` guarantees that other instructions (which also have a `funct3`) are **never** treated as taken branches.

**Example:** `bnez x11, loop` is `bne x11, x0`: when x11 = 9, 9 is not equal to 0 -> `branch_taken = 1`, PC returns to the start of the loop; when x11 = 0 they are equal -> `branch_taken = 0`, the loop ends.  `blt` and `bltu` differ only in which comparator is used (signed or unsigned): with -1 and 1, `blt` is taken, `bltu` is not.

---

## 8. LoadExtract - extracting the data of a load instruction

```mermaid
flowchart TD
    W(["32-bit word from RAM<br/>Address[1:0], funct3"]) --> SPLB["split into 4 bytes"]
    W --> SPLH["split into 2 halfwords"]
    SPLB --> MB{"select byte<br/>by Address[1:0]"}
    SPLH --> MH{"select halfword<br/>by Address[1]"}
    MB --> EB1["SIGN-extend 8 to 32 bit (lb)"]
    MB --> EB2["zero-extend 8 to 32 bit (lbu)"]
    MH --> EH1["SIGN-extend 16 to 32 bit (lh)"]
    MH --> EH2["zero-extend 16 to 32 bit (lhu)"]
    EB1 --> F{"funct3"}
    EB2 --> F
    EH1 --> F
    EH2 --> F
    W --> F
    F -->|"000"| OB["lb"]
    F -->|"001"| OH["lh"]
    F -->|"010"| OW["lw: whole word, unchanged"]
    F -->|"100"| OBU["lbu"]
    F -->|"101"| OHU["lhu"]
    OB --> OUT(["read_data 32 bit"])
    OH --> OUT
    OW --> OUT
    OBU --> OUT
    OHU --> OUT
```

**Step-by-step explanation.**
1. RAM always reads the **entire 32-bit word**; cutting out a byte or halfword is the job of this block.
2. Two multiplexers select the byte (by `Address[1:0]`) and the halfword (by `Address[1]`).
3. Four bit extenders prepare all four results (signed and unsigned); the final multiplexer selects by `funct3` (000 lb, 001 lh, 010 lw, 100 lbu, 101 lhu).

**Example:** word `0x000000F0`, byte address 0: `lb` gives `0xFFFFFFF0` (0xF0 has sign bit = 1 so it is extended with all 1s), `lbu` gives `0x000000F0`, `lw` gives the whole `0x000000F0`.

---

## 9. StoreMerge - writing part of a word (read - modify - write)

```mermaid
flowchart TD
    IN(["old_word (the old word currently in RAM)<br/>write_data, funct3, Address[1:0]"]) --> SZ["size = funct3[1:0]<br/>00 byte, 01 halfword, 10 word"]
    SZ --> ROM["ROM 16 rows x 4 bit<br/>address = size and Address[1:0]"]
    ROM --> EN["4 enable bits: each bit corresponds to one byte lane<br/>byte: 0001 0010 0100 1000<br/>halfword: 0011, 1100<br/>word: 1111"]
    IN --> SRC["select the source byte for each lane<br/>sb: always the low byte of write_data<br/>sh: the two low bytes<br/>sw: all 4 bytes"]
    EN --> L{"for each lane i from 0 to 3:<br/>enable = 1?"}
    SRC --> L
    IN --> OLD["split old_word into 4 bytes"]
    OLD --> L
    L -->|"1"| NEWB["lane i takes the NEW byte"]
    L -->|"0"| OLDB["lane i keeps the OLD byte"]
    NEWB --> JOIN["join 4 lanes into the new 32-bit word"]
    OLDB --> JOIN
    JOIN --> OUT(["new_word -> RAM writes the whole word"])
```

**Step-by-step explanation.**
1. RAM only writes a **whole word**, so when writing just one byte the other three bytes must be preserved.
2. The old word is read out (RAM reads asynchronously so it is available in the same cycle).
3. A small 16-row ROM converts `{size, Address[1:0]}` into 4 enable bits, each bit being one byte "lane".
4. For each lane: if enabled, take the new byte (from `write_data`), otherwise keep the old byte.  The four lanes are joined into the new word for RAM to write.

**Example:** old word `0x11223344`, `sb x1, 1(x0)` with x1 = `0xAA`: `size = 00` (byte), `Address[1:0] = 01` -> enable = `0010` (only lane 1) -> new word = `0x1122AA44`.

---

## 10. Memory - the data memory

```mermaid
flowchart TD
    IN(["Address, write_data, MemWrite, CLK, funct3"]) --> SPL["split Address<br/>Address[9:2] = word index<br/>Address[1:0] = byte within word"]
    SPL --> RAM["RAM 256 x 32<br/>asynchronous READ"]
    RAM -->|"old word"| LE["LoadExtract<br/>cuts byte, halfword + extends"]
    RAM -->|"old word"| SM["StoreMerge<br/>merges new byte into old word"]
    IN --> SM
    SM -->|"new word"| W{"MemWrite = 1?"}
    W -->|"yes, at the rising clock edge"| WR["RAM writes the new word to the address"]
    W -->|"no"| NOW["RAM unchanged"]
    LE --> OUT(["read_data"])
```

**Step-by-step explanation.**
1. The address is split: the word index (0..255) goes into RAM, the two low bits indicate the byte within the word.
2. RAM immediately returns the word at that address (asynchronous read).  `LoadExtract` turns this word into the value of the load instruction.
3. For a store instruction, `StoreMerge` builds the new word; only when `MemWrite = 1` does RAM write, at the rising clock edge.
4. Instructions that are not load/store have `MemWrite = 0` so RAM is unchanged; `read_data` still has a value but it is ignored at the write-back step.

**Why asynchronous read:** with a synchronous read the data would only appear after the next clock edge, and a load would return undefined data (a bug we hit and fixed).  Addresses of 1 KiB and above wrap around because only `Address[9:2]` is used.

---

## 11. `main` - single-cycle CPU: one instruction in one cycle

```mermaid
flowchart TD
    S(["start of cycle"]) --> IF["IF: ROM reads the instruction at PC<br/>pc_plus4 = PC + 4"]
    IF --> ID["ID: InstructionDecode cuts the instruction<br/>MainControl generates control<br/>RegisterFile reads rs1, rs2<br/>ImmGen builds imm"]
    ID --> MA{"ASel"}
    MA -->|"00"| A1["A = rs1"]
    MA -->|"01 auipc"| A2["A = PC"]
    MA -->|"10 lui"| A3["A = 0"]
    ID --> MB{"ALUSrc"}
    MB -->|"0"| B1["B = rs2"]
    MB -->|"1"| B2["B = imm"]
    A1 --> ALU
    A2 --> ALU
    A3 --> ALU
    B1 --> ALU
    B2 --> ALU
    ALU["EX: ALUControl selects the operation, ALU computes alu_result<br/>BranchUnit computes branch_taken"] --> MEMQ{"load or store instruction?"}
    MEMQ -->|"load: MemRead"| LD["MEM: RAM reads, LoadExtract gives mem_rdata"]
    MEMQ -->|"store: MemWrite"| ST["MEM: StoreMerge builds the new word, RAM writes"]
    MEMQ -->|"no"| SK["skip MEM"]
    LD --> WBQ
    ST --> WBQ
    SK --> WBQ
    WBQ{"WBSel"} -->|"00"| W1["write alu_result"]
    WBQ -->|"01"| W2["write mem_rdata"]
    WBQ -->|"10"| W3["write PC + 4"]
    W1 --> RWQ{"RegWrite = 1?"}
    W2 --> RWQ
    W3 --> RWQ
    RWQ -->|"yes"| WR["write the value into rd at the clock edge"]
    RWQ -->|"no"| NW["no register write"]
    WR --> NP
    NW --> NP
    NP{"select next PC"} -->|"IsJALR"| P3["(rs1 + imm) with bit 0 = 0"]
    NP -->|"branch_taken or IsJAL"| P2["PC + imm"]
    NP -->|"otherwise"| P1["PC + 4"]
    P1 --> E(["new PC, end of cycle"])
    P2 --> E
    P3 --> E
```

**Step-by-step explanation.**
1. **IF:** ROM receives `PC[9:2]` and returns the instruction; a separate adder computes `PC + 4`.
2. **ID:** the instruction is cut, control is generated, two registers are read, the constant is built; all four things happen in parallel.
3. **EX:** two multiplexers select operand A (`rs1`, `PC` or `0`) and B (`rs2` or `imm`); the ALU computes; `BranchUnit` decides the branch.
4. **MEM:** there is work only for load/store.
5. **WB:** the `WBSel` multiplexer selects the value to write (ALU, RAM or PC+4); if `RegWrite = 1` it is written into `rd`.
6. **Next PC:** `jalr` (target computed by the ALU, bit 0 cleared) has the highest priority; then a taken branch or `jal` (PC + imm); otherwise PC + 4.

**Why it is designed this way:** `lui`, `auipc`, `jal`, `jalr` reuse the same ALU and write-back path thanks to `ASel` and `WBSel`, with no extra dedicated hardware.

**Examples of each instruction group in `demo.s`:** see `DEMO_EXPLAIN.md` section 3 (add, addi, bnez, sw, lw, jal, ret, sub, slti) with the real values on each wire.

---

## 12. ForwardingUnit - choosing the newest source for the operand at EX

```mermaid
flowchart TD
    IN(["rs1_ex (or rs2_ex)<br/>rd_mem, RegWrite_mem<br/>rd_wb, RegWrite_wb"]) --> Q1{"the instruction at MEM writes a register<br/>AND rd_mem is not x0<br/>AND rd_mem = rs1_ex ?"}
    Q1 -->|"yes"| F10(["Forward = 10<br/>take from EX/MEM"])
    Q1 -->|"no"| Q2{"the instruction at WB writes a register<br/>AND rd_wb is not x0<br/>AND rd_wb = rs1_ex ?"}
    Q2 -->|"yes"| F01(["Forward = 01<br/>take from MEM/WB"])
    Q2 -->|"no"| F00(["Forward = 00<br/>take from the register file"])
```

**Step-by-step explanation.**
1. The problem: the instruction at EX needs a register that an **earlier** instruction has not yet written into the register file (a RAW dependency: read after write).
2. Check the immediately preceding instruction (now at MEM) **first**: if it writes exactly the register needed, take its result from EX/MEM (`Forward = 10`).
3. If not, check the instruction one further back (now at WB): take from MEM/WB (`Forward = 01`).
4. If neither matches: use the value read from the register file (`00`).
5. This block runs twice: once for `rs1` (`ForwardA`), once for `rs2` (`ForwardB`).

**Why MEM has priority:** if both stages write that register, the instruction at MEM is newer so its value is the correct one.  **Why x0 is excluded:** x0 is always 0, and forwarding a "result" written to x0 would be wrong.  The value taken from EX/MEM is the ALU result, **except for `jal`/`jalr`, where it is PC + 4**.

**Example (`hazards_demo.s`):** `li x1,100` followed immediately by `sw x1,0(x0)`: when `sw` is at EX, `li` is at MEM, `rd_mem = 1 = rs2_ex` -> `ForwardB = 10`.

---

## 13. HazardUnit - detecting load-use and stalling the pipeline

```mermaid
flowchart TD
    IN(["MemRead_ex, rd_ex<br/>rs1_id, rs2_id"]) --> Q1{"the instruction at EX is a load<br/>(MemRead_ex = 1)?"}
    Q1 -->|"no"| N(["stall = 0"])
    Q1 -->|"yes"| Q2{"rd_ex is not x0?"}
    Q2 -->|"no"| N
    Q2 -->|"yes"| Q3{"rd_ex = rs1_id<br/>OR rd_ex = rs2_id?"}
    Q3 -->|"no"| N
    Q3 -->|"yes"| S(["stall = 1"])
    S --> A1["PC holds (run = 0)"]
    S --> A2["IF/ID holds"]
    S --> A3["control word into ID/EX is cleared<br/>to 0 = bubble"]
```

**Step-by-step explanation.**
1. A load instruction only has its data at the **end of the MEM stage**, too late for the next instruction to use at EX; forwarding cannot save it.
2. Stall condition: the instruction at EX is a load, its destination is not x0, and the instruction at ID uses exactly that register (`rs1` or `rs2`).
3. When `stall = 1`: PC and IF/ID hold for one cycle (the instruction at ID must wait), and ID/EX receives an empty instruction (bubble).  In the next cycle the load is at MEM/WB so forwarding can get the data.

**The cost is exactly 1 cycle.**  Load, one unrelated instruction, then the use: no stall.  **Example:** `lw x2,0(x0)` then `addi x3,x2,1`: at tick 4 `stall = 1`, at tick 5 PC stays at 0x10.

---

## 14. `Pipeline` - one cycle of the 5-stage CPU

```mermaid
flowchart TD
    S(["start of cycle: all 5 stages run in parallel"]) --> IFS
    subgraph IFS["IF - instruction fetch"]
        I1{"pc_src_ex = 1?<br/>(branch/jal/jalr just decided at EX)"}
        I1 -->|"yes"| I2["next PC = jump target target_ex<br/>the instruction just fetched is changed to 0 (flush)"]
        I1 -->|"no"| I3["next PC = PC + 4<br/>instruction = ROM at PC"]
        I4{"stall = 1?"}
        I4 -->|"yes"| I5["PC and IF/ID hold"]
        I4 -->|"no"| I6["PC and IF/ID load new values"]
    end
    subgraph IDS["ID - decode"]
        D1["InstructionDecode, MainControl, ImmGen<br/>RegisterFile reads rs1, rs2"]
        D2{"HazardUnit:<br/>load-use?"}
        D1 --> D2
        D2 -->|"yes"| D3["stall = 1<br/>control word into ID/EX = 0 (bubble)"]
        D2 -->|"no"| D4{"pc_src_ex = 1?"}
        D4 -->|"yes"| D5["control word into ID/EX = 0<br/>(flush the wrongly fetched instruction)"]
        D4 -->|"no"| D6["the real control word moves on"]
    end
    subgraph EXS["EX - execute"]
        E1["ForwardingUnit selects the source<br/>of operands A and B"]
        E1 --> E2{"ForwardA/B"}
        E2 -->|"00"| E3["take from ID/EX (register)"]
        E2 -->|"01"| E4["take wb_data (MEM/WB)"]
        E2 -->|"10"| E5["take EX/MEM<br/>(ALU, or PC+4 for jal/jalr)"]
        E3 --> E6["ALU computes, BranchUnit decides<br/>PC + imm and the jalr target"]
        E4 --> E6
        E5 --> E6
        E6 --> E7{"branch_taken or IsJAL or IsJALR?"}
        E7 -->|"yes"| E8["pc_src_ex = 1"]
        E7 -->|"no"| E9["pc_src_ex = 0"]
    end
    subgraph MS["MEM - memory"]
        M1["Memory: load reads, store writes"]
    end
    subgraph WS["WB - write back"]
        W1["WBSel selects alu_result, mem_rdata or PC+4<br/>writes into rd at the FALLING clock edge"]
    end
    IFS --> IDS
    IDS --> EXS
    EXS --> MS
    MS --> WS
```

**Step-by-step explanation.**
1. In each cycle the five stages work on **five different instructions**; four pipeline registers (IF/ID, ID/EX, EX/MEM, MEM/WB) hold everything each instruction needs in the later stages, including the packed "control word" generated once at ID.
2. **Stall (load-use):** `HazardUnit` sees that the instruction at ID depends on the load at EX -> hold PC and IF/ID, insert a bubble into ID/EX.
3. **Forwarding:** at EX, if an operand is already available from an earlier instruction that has not finished writing, `ForwardingUnit` feeds it straight into the ALU.
4. **Flush (control hazard):** branch, `jal`, `jalr` are decided at EX; when `pc_src_ex = 1`, PC jumps to the target and the **two instructions already fetched behind are discarded** (turned into bubbles): this costs 2 cycles.  A branch not taken costs nothing.
5. **The register file writes at the falling edge** (`CLK_n`): the instruction at WB writes in the first half of the cycle, the instruction at ID reads in the second half and so sees the new value (no need to forward at a distance of 3 instructions).

**Cases (summary):**

| Situation | Sign on the probe | How it is resolved | Cost |
|---|---|---|---|
| uses an ALU value just computed | `ForwardA/B` = 10 or 01 | forwarding | 0 cycles |
| uses a value just loaded | `stall` = 1, PC holds for 1 tick | stall + forwarding | 1 cycle |
| branch/jal/jalr taken | `pc_src_ex` = 1, then `instr_id` = 0 | flush 2 instructions | 2 cycles |
| branch not taken | `pc_src_ex` = 0 | nothing | 0 cycles |

For the tick-by-tick details of `hazards_demo.s` see `DEMO_EXPLAIN.md` section 6.

---

## 15. Quick comparison table: what question each circuit answers

| Circuit | The question it answers | Main inputs | Main outputs |
|---|---|---|---|
| InstructionDecode | Which fields does the instruction consist of? | `Instruction` | `opcode rd funct3 rs1 rs2 funct7` |
| MainControl | Which signals must this instruction turn on? | `opcode` | `RegWrite ALUSrc MemWrite MemRead IsBranch ALUOp ImmSel ASel WBSel IsJAL IsJALR` |
| ImmGen | What is the constant in the instruction? | `Instruction`, `ImmSel` | `Imm` |
| RegisterFile | What are the values of the source registers, and where to write? | `rs1 rs2 rd write_data RegWrite` | `rs1_data rs2_data` |
| ALUControl | Which operation must the ALU perform? | `ALUOp funct3 funct7` | `ALUCtrl` |
| ALU | What is the result of the operation? | `rs1_data rs2_data ALU_Ctrl` | `result` |
| BranchUnit | Is the branch taken? | `rs1_data rs2_data funct3 IsBranch` | `branch_taken` |
| LoadExtract | What is the loaded value? | word from RAM, `Address[1:0]`, `funct3` | `read_data` |
| StoreMerge | What is the new word written to RAM? | old word, `write_data`, `funct3`, `Address[1:0]` | `new_word` |
| Memory | How are RAM reads/writes done? | `Address write_data MemWrite funct3` | `read_data` |
| `main` | How does one instruction run to completion? | clock | PC, registers, RAM |
| ForwardingUnit | Where to take the operand from to be correct? | `rs1_ex rs2_ex rd_mem rd_wb RegWrite_*` | `ForwardA ForwardB` |
| HazardUnit | Must the pipeline stall? | `MemRead_ex rd_ex rs1_id rs2_id` | `stall` |
| `Pipeline` | How do five instructions run overlapped? | clock | PC, registers, RAM |
