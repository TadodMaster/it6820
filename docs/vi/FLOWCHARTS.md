# Sơ đồ luồng (flowchart) của từng circuit

> Bản tiếng Việt của docs/FLOWCHARTS.md.

Tài liệu này vẽ **sơ đồ luồng cho cả 14 circuit** của dự án, kèm giải thích chi tiết từng bước, ví dụ với giá trị thật và các trường hợp đặc biệt.  Sơ đồ viết bằng **Mermaid**, nên tự hiện thành hình khi mở trên GitHub, trong VS Code (có phần mở rộng Markdown Mermaid) hoặc trong Overleaf/Obsidian.  Nếu chỗ bạn xem không hiện hình, dán đoạn mã vào https://mermaid.live.

**Cách đọc ký hiệu**

| Ký hiệu | Ý nghĩa |
|---|---|
| hình chữ nhật | một bước xử lý hoặc một khối mạch |
| hình thoi | một phép **chọn** (multiplexer) hoặc một điều kiện |
| hình bầu dục | đầu vào hoặc đầu ra của circuit |
| mũi tên có chữ | điều kiện hoặc giá trị tín hiệu chọn nhánh đó |

Mục lục: 0 Tổng quan - 1 InstructionDecode - 2 MainControl - 3 ImmGen - 4 RegisterFile - 5 ALUControl - 6 ALU - 7 BranchUnit - 8 LoadExtract - 9 StoreMerge - 10 Memory - 11 `main` (single-cycle) - 12 ForwardingUnit - 13 HazardUnit - 14 `Pipeline` - 15 Bảng so sánh nhanh

---

## 0. Tổng quan: cả máy tính nhìn từ xa

```mermaid
flowchart LR
    PC(["PC<br/>địa chỉ lệnh"]) --> ROM["ROM lệnh<br/>256 x 32"]
    ROM -->|"lệnh 32 bit"| ID["InstructionDecode<br/>cắt thành các trường"]
    ID --> CTL["MainControl<br/>sinh tín hiệu điều khiển"]
    ID --> RF["RegisterFile<br/>đọc rs1, rs2"]
    ID --> IMM["ImmGen<br/>dựng hằng số imm"]
    CTL -. "ALUOp" .-> ALUC["ALUControl"]
    ALUC -. "ALUCtrl" .-> ALU["ALU<br/>tính kết quả"]
    RF --> ALU
    IMM --> ALU
    RF --> BR["BranchUnit<br/>có rẽ nhánh không?"]
    ALU --> MEM["Memory<br/>RAM + LoadExtract + StoreMerge"]
    ALU --> WB{"chọn giá trị<br/>ghi lại (WBSel)"}
    MEM --> WB
    WB --> RF
    BR --> NPC{"chọn PC kế tiếp"}
    ALU --> NPC
    NPC --> PC
```

**Cách đọc.**  Mỗi chu kỳ CPU làm đúng một vòng: lấy lệnh từ ROM tại PC, cắt lệnh, đọc thanh ghi và dựng hằng số, ALU tính, (nếu cần) đụng RAM, chọn giá trị ghi lại vào thanh ghi `rd`, và chọn PC kế tiếp.  Nét đứt là tín hiệu điều khiển, nét liền là dữ liệu.  CPU `main` làm hết vòng này trong **một** chu kỳ xung nhịp; CPU `Pipeline` chia vòng thành 5 tầng để năm lệnh chạy chồng nhau.

---

## 1. InstructionDecode - cắt lệnh thành các trường

```mermaid
flowchart TD
    I(["Instruction<br/>32 bit"]) --> S["Splitter 32 thành 6 phần<br/>chỉ là đi dây, không có cổng"]
    S --> O["opcode = bit 6..0"]
    S --> RD["rd = bit 11..7"]
    S --> F3["funct3 = bit 14..12"]
    S --> R1["rs1 = bit 19..15"]
    S --> R2["rs2 = bit 24..20"]
    S --> F7["funct7 = bit 31..25"]
```

**Giải thích từng bước.**
1. Lệnh 32 bit đi vào một splitter duy nhất.
2. Splitter chia bus thành sáu dây theo vị trí bit **cố định**: `opcode` (7 bit), `rd` (5), `funct3` (3), `rs1` (5), `rs2` (5), `funct7` (7).
3. Không có phép tính nào: đây chỉ là đi dây, nên không tốn thời gian và không có gì để sai.

**Ví dụ:** lệnh `00b50533` -> `opcode = 0x33` (kiểu R), `rd = 10`, `funct3 = 0`, `rs1 = 10`, `rs2 = 11`, `funct7 = 0` -> đây là `add x10, x10, x11`.

**Trường hợp đặc biệt:** lệnh kiểu U/J không có `rs1`/`rs2`/`funct3` thật; các bit đó vẫn được cắt ra nhưng các khối sau bỏ qua.  Vì RISC-V đặt `rs1`, `rs2` luôn ở cùng chỗ, thanh ghi có thể được đọc **trong khi** opcode còn đang được giải mã.

---

## 2. MainControl - từ opcode sinh mọi tín hiệu điều khiển

```mermaid
flowchart TD
    OP(["opcode 7 bit"]) --> C{"so opcode với 9 hằng số<br/>mỗi nhóm một bộ so sánh"}
    C -->|"0x33"| R["IsR<br/>add, sub, and, or, sll..."]
    C -->|"0x13"| I["IsI<br/>addi, andi, slli..."]
    C -->|"0x03"| L["IsLoad<br/>lb, lh, lw, lbu, lhu"]
    C -->|"0x23"| S["IsStore<br/>sb, sh, sw"]
    C -->|"0x63"| B["IsBranch<br/>beq, bne, blt..."]
    C -->|"0x37"| LUI["IsLui"]
    C -->|"0x17"| AU["IsAuipc"]
    C -->|"0x6F"| J["IsJAL"]
    C -->|"0x67"| JR["IsJALR"]
    C -->|"khác"| N["mọi cờ = 0<br/>lệnh rỗng (NOP) an toàn"]
    R --> OR1["cổng OR gộp cờ"]
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
    OR1 --> AO(["ALUOp 2 bit<br/>bit1 = R hoặc I, bit0 = I hoặc branch"])
    OR1 --> IM(["ImmSel 3 bit<br/>I 000, S 001, B 010, U 011, J 100"])
    OR1 --> ASEL(["ASel 2 bit<br/>00 rs1, 01 PC, 10 số 0"])
    OR1 --> WBS(["WBSel 2 bit<br/>00 ALU, 01 RAM, 10 PC+4"])
    OR1 --> OTH(["MemWrite = IsStore<br/>MemRead = IsLoad<br/>IsBranch, IsJAL, IsJALR"])
```

**Giải thích từng bước.**
1. Chín bộ so sánh 7 bit so `opcode` với chín hằng số; chỉ một bộ báo "bằng", cho ra cờ của nhóm lệnh đó (`IsR`, `IsI`...).
2. Cổng OR (tối đa 3 ngõ vào, nên chia hai nửa) gộp các cờ thành từng tín hiệu: ví dụ `RegWrite` bật cho mọi nhóm **có ghi `rd`**; store và branch không có mặt nên không ghi thanh ghi.
3. Các tín hiệu nhiều bit (`ALUOp`, `ImmSel`, `ASel`, `WBSel`) được ghép từ bit đơn bằng splitter.
4. Opcode lạ làm mọi cờ bằng 0, nên lệnh không làm gì (NOP) mà không phá trạng thái.

**Bảng kết quả cho vài lệnh** (đã kiểm bằng `tests/maincontrol.vec`):

| Lệnh | RegWrite | ALUSrc | MemWrite | MemRead | ALUOp | ImmSel | ASel | WBSel |
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

## 3. ImmGen - dựng hằng số tức thời

```mermaid
flowchart TD
    IN(["Instruction + ImmSel"]) --> SEL{"ImmSel"}
    SEL -->|"000 kiểu I"| TI["lấy instr 31..20 (12 bit)<br/>mở rộng dấu lên 32 bit"]
    SEL -->|"001 kiểu S"| TS["ghép instr 31..25 và 11..7 (12 bit)<br/>mở rộng dấu"]
    SEL -->|"010 kiểu B"| TB["ghép bit 31, 7, 30..25, 11..8, rồi bit 0 = 0 (13 bit)<br/>mở rộng dấu"]
    SEL -->|"011 kiểu U"| TU["lấy instr 31..12<br/>nối 12 bit 0 phía sau (imm dịch trái 12)"]
    SEL -->|"100 kiểu J"| TJ["ghép bit 31, 19..12, 20, 30..21, rồi bit 0 = 0 (21 bit)<br/>mở rộng dấu"]
    TI --> MUX{"multiplexer 8 ngả<br/>chọn theo ImmSel"}
    TS --> MUX
    TB --> MUX
    TU --> MUX
    TJ --> MUX
    MUX --> OUT(["Imm 32 bit"])
```

**Giải thích từng bước.**
1. Cả năm cách dựng hằng số chạy **song song** từ cùng một lệnh (mỗi cách là vài splitter + một bộ mở rộng bit).
2. Multiplexer chọn kết quả của đúng một cách theo `ImmSel` (do `MainControl` sinh).
3. **Mở rộng dấu** chép bit cao nhất của hằng số vào các bit phía trên, nên số âm vẫn âm.  Kiểu U thì không mở rộng mà chèn 12 bit 0 (lệnh `lui`/`auipc` đặt hằng số vào 20 bit cao).
4. Bit 0 của kiểu B và J luôn bằng 0 vì địa chỉ lệnh là bội của 2 (thực tế là 4); lệnh vì thế không cất bit này.

**Ví dụ:** `fe059ce3` (`bnez x11, loop`, kiểu B): imm[12] = 1, imm[11] = 1, imm[10:5] = 111111, imm[4:1] = 1100, bit 0 = 0 -> 13 bit `1111111111000` -> mở rộng dấu thành **`0xFFFFFFF8` = -8**: nhảy lùi 8 byte về đầu vòng lặp.

---

## 4. RegisterFile - đọc hai thanh ghi, ghi một thanh ghi

```mermaid
flowchart TD
    subgraph READ["Đọc (bất đồng bộ, không chờ xung)"]
        RS1(["rs1"]) --> M1["Mux 32:1<br/>chọn thanh ghi số rs1"]
        RS2(["rs2"]) --> M2["Mux 32:1<br/>chọn thanh ghi số rs2"]
        M1 --> D1(["rs1_data"])
        M2 --> D2(["rs2_data"])
    end
    subgraph WRITE["Ghi (ở cạnh xung nhịp)"]
        RW(["RegWrite"]) --> DM["Demux 1:32<br/>chọn theo rd"]
        RD(["rd"]) --> DM
        DM -->|"chỉ thanh ghi số rd có WE = 1"| REG["32 thanh ghi x0..x31<br/>x0 luôn nạp số 0"]
        WD(["write_data"]) --> REG
        CLK(["CLK"]) --> REG
    end
    REG --> M1
    REG --> M2
```

**Giải thích từng bước.**
1. **Đọc:** hai multiplexer 32 ngả chọn thanh ghi theo `rs1` và `rs2`; vì không có xung nhịp ở đây nên đổi `rs1` là `rs1_data` đổi ngay (CPU single-cycle cần toán hạng ngay trong chu kỳ).
2. **Ghi:** demultiplexer đưa `RegWrite` tới **đúng một** thanh ghi (số `rd`); thanh ghi đó nạp `write_data` ở cạnh xung nhịp, các thanh ghi khác giữ nguyên.
3. `x0` có đầu vào cố định bằng 0 nên mãi bằng 0, bất kể ghi gì.

**Các trường hợp:** `RegWrite = 0` (store, branch) -> không thanh ghi nào đổi; `rd = 0` -> ghi vào x0 vô hiệu; đọc và ghi cùng thanh ghi trong một chu kỳ -> đọc giá trị cũ (trên pipeline, khối này ghi ở cạnh **xuống** nên lệnh ở ID thấy giá trị mới).

---

## 5. ALUControl - chọn phép tính của ALU

```mermaid
flowchart TD
    IN(["ALUOp, funct3, funct7"]) --> Q{"ALUOp"}
    Q -->|"00"| ADD0["ALUCtrl = 0 (ADD)<br/>load, store, lui, auipc, jalr"]
    Q -->|"01"| SUB0["ALUCtrl = 1 (SUB)<br/>branch: so sánh bằng phép trừ"]
    Q -->|"10 kiểu R"| TR{"funct3"}
    Q -->|"11 kiểu I"| TI{"funct3"}
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

**Giải thích từng bước.**
1. `ALUOp` do `MainControl` đưa vào chia thành bốn nhánh: 00 cộng, 01 trừ (không cần xem `funct`), 10 tra bảng kiểu R, 11 tra bảng kiểu I.
2. Với R và I, `funct3` chọn phép tính (hai multiplexer 8 ngả, mỗi bảng một cái; mỗi dòng bảng là một hằng số 4 bit).
3. `funct7[5]` (bit 30 của lệnh) làm hai việc: ở kiểu R biến ADD thành SUB và SRL thành SRA; ở kiểu I chỉ có ý nghĩa với lệnh dịch (`srai` khác `srli`).  `addi` bỏ qua bit này vì bit đó là một phần của hằng số.

**Mã đầu ra:** 0 ADD, 1 SUB, 2 AND, 3 OR, 4 XOR, 5 SLL, 6 SRL, 7 SRA, 8 SLT, 9 SLTU.

---

## 6. ALU - tính song song rồi chọn

```mermaid
flowchart TD
    A(["rs1_data (A)"]) --> P["tính SONG SONG mọi phép"]
    B(["rs2_data (B)"]) --> P
    P --> R0["A + B (ADD)"]
    P --> R1["A - B (SUB)"]
    P --> R2["A and B"]
    P --> R3["A or B"]
    P --> R4["A xor B"]
    P --> R5["A dịch trái B[4:0] (SLL)"]
    P --> R6["A dịch phải logic B[4:0] (SRL)"]
    P --> R7["A dịch phải số học B[4:0] (SRA)"]
    P --> R8["A nhỏ hơn B, có dấu<br/>mở rộng 0 thành 0 hoặc 1"]
    P --> R9["A nhỏ hơn B, không dấu<br/>mở rộng 0 thành 0 hoặc 1"]
    R0 --> MX{"Mux 16 ngả<br/>chọn theo ALU_Ctrl"}
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

**Giải thích từng bước.**
1. Mười phép tính chạy cùng lúc từ cùng hai toán hạng; không phép nào "biết" phép nào được chọn.
2. Multiplexer 16 ngả (dùng 10 ngõ) lấy đúng một kết quả theo `ALU_Ctrl` (từ `ALUControl`).
3. Lệnh dịch chỉ dùng 5 bit thấp của B (dịch tối đa 31).  SRL chèn bit 0 phía trên, SRA chép bit dấu.
4. SLT/SLTU cho kết quả 1 bit; **mở rộng 0** thành 32 bit để ra đúng 0 hoặc 1.  (Lỗi từng gặp: mở rộng dấu làm SLTU trả `0xFFFFFFFF`.)

**Ví dụ:** A = -1 (`0xFFFFFFFF`), B = 1: SLT cho 1 (vì -1 < 1 có dấu), SLTU cho 0 (vì 4294967295 không nhỏ hơn 1).  Tràn số khi cộng/trừ bị bỏ qua: kết quả quấn vòng 32 bit đúng như RISC-V.

---

## 7. BranchUnit - branch có được rẽ không

```mermaid
flowchart TD
    IN(["rs1_data, rs2_data, funct3, IsBranch"]) --> CMP["so sánh rs1 với rs2<br/>bằng, nhỏ hơn có dấu, nhỏ hơn không dấu<br/>cùng các phủ định"]
    CMP --> F{"funct3"}
    F -->|"000 beq"| C0["bằng"]
    F -->|"001 bne"| C1["khác"]
    F -->|"100 blt"| C4["nhỏ hơn, có dấu"]
    F -->|"101 bge"| C5["lớn hơn hoặc bằng, có dấu"]
    F -->|"110 bltu"| C6["nhỏ hơn, không dấu"]
    F -->|"111 bgeu"| C7["lớn hơn hoặc bằng, không dấu"]
    F -->|"010, 011"| C2["không phải lệnh branch<br/>điều kiện = 0"]
    C0 --> AND
    C1 --> AND
    C4 --> AND
    C5 --> AND
    C6 --> AND
    C7 --> AND
    C2 --> AND
    AND{"IsBranch = 1<br/>VÀ điều kiện đúng?"} -->|"có"| T(["branch_taken = 1<br/>PC = PC + imm"])
    AND -->|"không"| N(["branch_taken = 0<br/>PC = PC + 4"])
```

**Giải thích từng bước.**
1. Một bộ so sánh không dấu và một bộ có dấu cho ra các quan hệ "bằng" và "nhỏ hơn"; ba cổng NOT cho ra các phủ định ("khác", "lớn hơn hoặc bằng").
2. Một multiplexer 8 ngả theo `funct3` chọn điều kiện của đúng lệnh branch đang chạy.
3. Cổng AND với `IsBranch` bảo đảm các lệnh khác (cũng có `funct3`) **không bao giờ** bị coi là rẽ nhánh.

**Ví dụ:** `bnez x11, loop` là `bne x11, x0`: khi x11 = 9 thì 9 khác 0 -> `branch_taken = 1`, PC quay về đầu vòng lặp; khi x11 = 0 thì bằng nhau -> `branch_taken = 0`, vòng lặp kết thúc.  `blt` và `bltu` chỉ khác ở bộ so sánh dùng (có dấu hay không dấu): với -1 và 1, `blt` rẽ, `bltu` không rẽ.

---

## 8. LoadExtract - lấy dữ liệu của lệnh load

```mermaid
flowchart TD
    W(["word 32 bit từ RAM<br/>Address[1:0], funct3"]) --> SPLB["tách 4 byte"]
    W --> SPLH["tách 2 nửa từ"]
    SPLB --> MB{"chọn byte<br/>theo Address[1:0]"}
    SPLH --> MH{"chọn nửa từ<br/>theo Address[1]"}
    MB --> EB1["mở rộng DẤU 8 thành 32 bit (lb)"]
    MB --> EB2["mở rộng 0 8 thành 32 bit (lbu)"]
    MH --> EH1["mở rộng DẤU 16 thành 32 bit (lh)"]
    MH --> EH2["mở rộng 0 16 thành 32 bit (lhu)"]
    EB1 --> F{"funct3"}
    EB2 --> F
    EH1 --> F
    EH2 --> F
    W --> F
    F -->|"000"| OB["lb"]
    F -->|"001"| OH["lh"]
    F -->|"010"| OW["lw: cả từ, không đổi"]
    F -->|"100"| OBU["lbu"]
    F -->|"101"| OHU["lhu"]
    OB --> OUT(["read_data 32 bit"])
    OH --> OUT
    OW --> OUT
    OBU --> OUT
    OHU --> OUT
```

**Giải thích từng bước.**
1. RAM luôn đọc **nguyên từ 32 bit**; việc cắt byte hay nửa từ là của khối này.
2. Hai multiplexer chọn byte (theo `Address[1:0]`) và nửa từ (theo `Address[1]`).
3. Bốn bộ mở rộng bit chuẩn bị cả bốn kết quả (có dấu và không dấu); multiplexer cuối chọn theo `funct3` (000 lb, 001 lh, 010 lw, 100 lbu, 101 lhu).

**Ví dụ:** từ `0x000000F0`, địa chỉ byte 0: `lb` cho `0xFFFFFFF0` (0xF0 có bit dấu = 1 nên mở rộng toàn 1), `lbu` cho `0x000000F0`, `lw` cho nguyên `0x000000F0`.

---

## 9. StoreMerge - ghi một phần của từ (đọc - sửa - ghi)

```mermaid
flowchart TD
    IN(["old_word (từ cũ đang trong RAM)<br/>write_data, funct3, Address[1:0]"]) --> SZ["size = funct3[1:0]<br/>00 byte, 01 nửa từ, 10 từ"]
    SZ --> ROM["ROM 16 hàng x 4 bit<br/>địa chỉ = size và Address[1:0]"]
    ROM --> EN["4 bit cho phép: mỗi bit ứng với một làn byte<br/>byte: 0001 0010 0100 1000<br/>nửa từ: 0011, 1100<br/>cả từ: 1111"]
    IN --> SRC["chọn byte nguồn cho từng làn<br/>sb: luôn lấy byte thấp của write_data<br/>sh: hai byte thấp<br/>sw: cả 4 byte"]
    EN --> L{"với mỗi làn i từ 0 đến 3:<br/>cho phép = 1?"}
    SRC --> L
    IN --> OLD["tách old_word thành 4 byte"]
    OLD --> L
    L -->|"1"| NEWB["làn i lấy byte MỚI"]
    L -->|"0"| OLDB["làn i giữ byte CŨ"]
    NEWB --> JOIN["ghép 4 làn thành từ mới 32 bit"]
    OLDB --> JOIN
    JOIN --> OUT(["new_word -> RAM ghi nguyên từ"])
```

**Giải thích từng bước.**
1. RAM chỉ ghi **nguyên từ**, nên khi chỉ ghi một byte phải giữ nguyên ba byte kia.
2. Từ cũ được đọc ra (RAM đọc bất đồng bộ nên có sẵn trong cùng chu kỳ).
3. ROM nhỏ 16 hàng đổi `{size, Address[1:0]}` thành 4 bit cho phép, mỗi bit là một "làn" byte.
4. Với mỗi làn: nếu được phép thì lấy byte mới (từ `write_data`), không thì giữ byte cũ.  Ghép bốn làn thành từ mới để RAM ghi.

**Ví dụ:** từ cũ `0x11223344`, `sb x1, 1(x0)` với x1 = `0xAA`: `size = 00` (byte), `Address[1:0] = 01` -> cho phép = `0010` (chỉ làn 1) -> từ mới = `0x1122AA44`.

---

## 10. Memory - bộ nhớ dữ liệu

```mermaid
flowchart TD
    IN(["Address, write_data, MemWrite, CLK, funct3"]) --> SPL["tách Address<br/>Address[9:2] = chỉ số từ<br/>Address[1:0] = byte trong từ"]
    SPL --> RAM["RAM 256 x 32<br/>ĐỌC bất đồng bộ"]
    RAM -->|"từ cũ"| LE["LoadExtract<br/>cắt byte, nửa từ + mở rộng"]
    RAM -->|"từ cũ"| SM["StoreMerge<br/>ghép byte mới vào từ cũ"]
    IN --> SM
    SM -->|"từ mới"| W{"MemWrite = 1?"}
    W -->|"có, ở cạnh lên xung nhịp"| WR["RAM ghi từ mới vào địa chỉ"]
    W -->|"không"| NOW["RAM không đổi"]
    LE --> OUT(["read_data"])
```

**Giải thích từng bước.**
1. Địa chỉ được tách: chỉ số từ (0..255) đi vào RAM, hai bit thấp chỉ byte trong từ.
2. RAM trả ngay từ ở địa chỉ đó (đọc bất đồng bộ).  `LoadExtract` biến từ này thành giá trị của lệnh load.
3. Khi là lệnh store, `StoreMerge` dựng từ mới; chỉ khi `MemWrite = 1` thì RAM mới ghi, ở cạnh lên của xung nhịp.
4. Lệnh không phải load/store có `MemWrite = 0` nên RAM không đổi; `read_data` vẫn có giá trị nhưng bị bỏ qua ở bước write-back.

**Vì sao đọc bất đồng bộ:** nếu đọc đồng bộ thì dữ liệu chỉ xuất hiện sau cạnh xung kế tiếp, lệnh load trả dữ liệu không xác định (lỗi đã gặp và sửa).  Địa chỉ từ 1 KiB trở lên quấn vòng vì chỉ dùng `Address[9:2]`.

---

## 11. `main` - CPU single-cycle: một lệnh trong một chu kỳ

```mermaid
flowchart TD
    S(["bắt đầu chu kỳ"]) --> IF["IF: ROM đọc lệnh tại PC<br/>pc_plus4 = PC + 4"]
    IF --> ID["ID: InstructionDecode cắt lệnh<br/>MainControl sinh điều khiển<br/>RegisterFile đọc rs1, rs2<br/>ImmGen dựng imm"]
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
    ALU["EX: ALUControl chọn phép, ALU tính alu_result<br/>BranchUnit tính branch_taken"] --> MEMQ{"lệnh load hoặc store?"}
    MEMQ -->|"load: MemRead"| LD["MEM: RAM đọc, LoadExtract cho mem_rdata"]
    MEMQ -->|"store: MemWrite"| ST["MEM: StoreMerge dựng từ mới, RAM ghi"]
    MEMQ -->|"không"| SK["bỏ qua MEM"]
    LD --> WBQ
    ST --> WBQ
    SK --> WBQ
    WBQ{"WBSel"} -->|"00"| W1["ghi alu_result"]
    WBQ -->|"01"| W2["ghi mem_rdata"]
    WBQ -->|"10"| W3["ghi PC + 4"]
    W1 --> RWQ{"RegWrite = 1?"}
    W2 --> RWQ
    W3 --> RWQ
    RWQ -->|"có"| WR["ghi giá trị vào rd ở cạnh xung"]
    RWQ -->|"không"| NW["không ghi thanh ghi"]
    WR --> NP
    NW --> NP
    NP{"chọn PC kế tiếp"} -->|"IsJALR"| P3["(rs1 + imm) với bit 0 = 0"]
    NP -->|"branch_taken hoặc IsJAL"| P2["PC + imm"]
    NP -->|"còn lại"| P1["PC + 4"]
    P1 --> E(["PC mới, hết chu kỳ"])
    P2 --> E
    P3 --> E
```

**Giải thích từng bước.**
1. **IF:** ROM nhận `PC[9:2]`, trả lệnh; bộ cộng riêng tính `PC + 4`.
2. **ID:** lệnh được cắt, điều khiển được sinh, hai thanh ghi được đọc, hằng số được dựng; cả bốn việc diễn ra song song.
3. **EX:** hai multiplexer chọn toán hạng A (`rs1`, `PC` hay `0`) và B (`rs2` hay `imm`); ALU tính; `BranchUnit` quyết định branch.
4. **MEM:** chỉ có việc khi là load/store.
5. **WB:** multiplexer `WBSel` chọn giá trị ghi (ALU, RAM hay PC+4); nếu `RegWrite = 1` thì ghi vào `rd`.
6. **PC kế tiếp:** `jalr` (đích tính bằng ALU, xóa bit 0) ưu tiên cao nhất; rồi tới branch được rẽ hoặc `jal` (PC + imm); còn lại PC + 4.

**Vì sao thiết kế thế:** `lui`, `auipc`, `jal`, `jalr` dùng lại đúng ALU và đường write-back nhờ `ASel` và `WBSel`, không thêm phần cứng riêng.

**Ví dụ mỗi nhóm lệnh trong `demo.s`:** xem `docs/vi/DEMO_EXPLAIN.md` mục 3 (add, addi, bnez, sw, lw, jal, ret, sub, slti) với giá trị thật trên từng dây.

---

## 12. ForwardingUnit - chọn nguồn mới nhất cho toán hạng ở EX

```mermaid
flowchart TD
    IN(["rs1_ex (hoặc rs2_ex)<br/>rd_mem, RegWrite_mem<br/>rd_wb, RegWrite_wb"]) --> Q1{"lệnh ở MEM ghi thanh ghi<br/>VÀ rd_mem khác x0<br/>VÀ rd_mem = rs1_ex ?"}
    Q1 -->|"có"| F10(["Forward = 10<br/>lấy từ EX/MEM"])
    Q1 -->|"không"| Q2{"lệnh ở WB ghi thanh ghi<br/>VÀ rd_wb khác x0<br/>VÀ rd_wb = rs1_ex ?"}
    Q2 -->|"có"| F01(["Forward = 01<br/>lấy từ MEM/WB"])
    Q2 -->|"không"| F00(["Forward = 00<br/>lấy từ register file"])
```

**Giải thích từng bước.**
1. Vấn đề: lệnh ở EX cần thanh ghi mà một lệnh **trước đó** chưa kịp ghi vào register file (phụ thuộc RAW: đọc sau ghi).
2. Kiểm tra lệnh ngay trước (đang ở MEM) **trước**: nếu nó ghi đúng thanh ghi cần thì lấy kết quả của nó từ EX/MEM (`Forward = 10`).
3. Nếu không, kiểm tra lệnh cách một (đang ở WB): lấy từ MEM/WB (`Forward = 01`).
4. Cả hai đều không khớp: dùng giá trị đọc từ register file (`00`).
5. Khối này chạy hai lần: một cho `rs1` (`ForwardA`), một cho `rs2` (`ForwardB`).

**Vì sao ưu tiên MEM:** nếu cả hai tầng cùng ghi thanh ghi đó thì lệnh ở MEM mới hơn nên giá trị của nó là đúng.  **Vì sao loại x0:** x0 luôn bằng 0, forward một "kết quả" ghi vào x0 sẽ sai.  Giá trị lấy từ EX/MEM là kết quả ALU, **riêng `jal`/`jalr` là PC + 4**.

**Ví dụ (`hazards_demo.s`):** `li x1,100` rồi ngay sau là `sw x1,0(x0)`: khi `sw` ở EX thì `li` ở MEM, `rd_mem = 1 = rs2_ex` -> `ForwardB = 10`.

---

## 13. HazardUnit - phát hiện load-use và dừng pipeline

```mermaid
flowchart TD
    IN(["MemRead_ex, rd_ex<br/>rs1_id, rs2_id"]) --> Q1{"lệnh ở EX là load<br/>(MemRead_ex = 1)?"}
    Q1 -->|"không"| N(["stall = 0"])
    Q1 -->|"có"| Q2{"rd_ex khác x0?"}
    Q2 -->|"không"| N
    Q2 -->|"có"| Q3{"rd_ex = rs1_id<br/>HOẶC rd_ex = rs2_id?"}
    Q3 -->|"không"| N
    Q3 -->|"có"| S(["stall = 1"])
    S --> A1["PC đứng yên (run = 0)"]
    S --> A2["IF/ID đứng yên"]
    S --> A3["từ điều khiển vào ID/EX bị xóa<br/>thành 0 = bubble"]
```

**Giải thích từng bước.**
1. Lệnh load chỉ có dữ liệu ở **cuối tầng MEM**, quá muộn để lệnh ngay sau dùng ở EX; forwarding không cứu được.
2. Điều kiện stall: lệnh ở EX là load, đích khác x0, và lệnh đang ở ID dùng đúng thanh ghi đó (`rs1` hoặc `rs2`).
3. Khi `stall = 1`: PC và IF/ID đứng yên một chu kỳ (lệnh ở ID phải chờ), còn ID/EX nhận lệnh rỗng (bubble).  Chu kỳ sau load đã ở MEM/WB nên forwarding lấy được dữ liệu.

**Chi phí đúng 1 chu kỳ.**  Load, một lệnh không liên quan rồi mới dùng: không stall.  **Ví dụ:** `lw x2,0(x0)` rồi `addi x3,x2,1`: tại tick 4 `stall = 1`, tick 5 PC đứng ở 0x10.

---

## 14. `Pipeline` - một chu kỳ của CPU 5 tầng

```mermaid
flowchart TD
    S(["bắt đầu chu kỳ: cả 5 tầng chạy song song"]) --> IFS
    subgraph IFS["IF - nạp lệnh"]
        I1{"pc_src_ex = 1?<br/>(branch/jal/jalr vừa quyết định ở EX)"}
        I1 -->|"có"| I2["PC kế = đích nhảy target_ex<br/>lệnh vừa nạp bị đổi thành 0 (flush)"]
        I1 -->|"không"| I3["PC kế = PC + 4<br/>lệnh = ROM tại PC"]
        I4{"stall = 1?"}
        I4 -->|"có"| I5["PC và IF/ID đứng yên"]
        I4 -->|"không"| I6["PC và IF/ID nạp giá trị mới"]
    end
    subgraph IDS["ID - giải mã"]
        D1["InstructionDecode, MainControl, ImmGen<br/>RegisterFile đọc rs1, rs2"]
        D2{"HazardUnit:<br/>load-use?"}
        D1 --> D2
        D2 -->|"có"| D3["stall = 1<br/>từ điều khiển vào ID/EX = 0 (bubble)"]
        D2 -->|"không"| D4{"pc_src_ex = 1?"}
        D4 -->|"có"| D5["từ điều khiển vào ID/EX = 0<br/>(flush lệnh nạp nhầm)"]
        D4 -->|"không"| D6["từ điều khiển thật đi tiếp"]
    end
    subgraph EXS["EX - thực thi"]
        E1["ForwardingUnit chọn nguồn<br/>của toán hạng A và B"]
        E1 --> E2{"ForwardA/B"}
        E2 -->|"00"| E3["lấy từ ID/EX (thanh ghi)"]
        E2 -->|"01"| E4["lấy wb_data (MEM/WB)"]
        E2 -->|"10"| E5["lấy EX/MEM<br/>(ALU, hoặc PC+4 nếu jal/jalr)"]
        E3 --> E6["ALU tính, BranchUnit quyết định<br/>PC + imm và đích jalr"]
        E4 --> E6
        E5 --> E6
        E6 --> E7{"branch_taken hoặc IsJAL hoặc IsJALR?"}
        E7 -->|"có"| E8["pc_src_ex = 1"]
        E7 -->|"không"| E9["pc_src_ex = 0"]
    end
    subgraph MS["MEM - bộ nhớ"]
        M1["Memory: load đọc, store ghi"]
    end
    subgraph WS["WB - ghi lại"]
        W1["WBSel chọn alu_result, mem_rdata hoặc PC+4<br/>ghi vào rd ở cạnh XUỐNG xung nhịp"]
    end
    IFS --> IDS
    IDS --> EXS
    EXS --> MS
    MS --> WS
```

**Giải thích từng bước.**
1. Trong mỗi chu kỳ năm tầng làm việc trên **năm lệnh khác nhau**; bốn thanh ghi pipeline (IF/ID, ID/EX, EX/MEM, MEM/WB) giữ mọi thứ mà mỗi lệnh cần ở tầng sau, gồm cả "từ điều khiển" đóng gói sinh một lần ở ID.
2. **Stall (load-use):** `HazardUnit` thấy lệnh ở ID phụ thuộc lệnh load ở EX -> giữ PC và IF/ID, chèn bubble vào ID/EX.
3. **Forwarding:** ở EX, nếu một toán hạng đã có ở lệnh phía trước chưa ghi xong, `ForwardingUnit` đưa nó thẳng vào ALU.
4. **Flush (control hazard):** branch, `jal`, `jalr` quyết định ở EX; khi `pc_src_ex = 1`, PC nhảy tới đích và **hai lệnh đã nạp phía sau bị hủy** (thành bubble): mất 2 chu kỳ.  Branch không rẽ không mất gì.
5. **Register file ghi ở cạnh xuống** (`CLK_n`): lệnh ở WB ghi nửa đầu chu kỳ, lệnh ở ID đọc nửa sau nên thấy giá trị mới (không cần forward khoảng cách 3 lệnh).

**Các trường hợp (tóm tắt):**

| Tình huống | Dấu hiệu trên probe | Cách giải quyết | Chi phí |
|---|---|---|---|
| dùng giá trị ALU vừa tính | `ForwardA/B` = 10 hoặc 01 | forwarding | 0 chu kỳ |
| dùng giá trị vừa load | `stall` = 1, PC đứng yên 1 tick | stall + forwarding | 1 chu kỳ |
| branch/jal/jalr được rẽ | `pc_src_ex` = 1, sau đó `instr_id` = 0 | flush 2 lệnh | 2 chu kỳ |
| branch không rẽ | `pc_src_ex` = 0 | không làm gì | 0 chu kỳ |

Chi tiết từng tick của `hazards_demo.s` xem `docs/vi/DEMO_EXPLAIN.md` mục 6.

---

## 15. Bảng so sánh nhanh: mỗi circuit trả lời câu hỏi gì

| Circuit | Câu hỏi nó trả lời | Đầu vào chính | Đầu ra chính |
|---|---|---|---|
| InstructionDecode | Lệnh gồm những trường nào? | `Instruction` | `opcode rd funct3 rs1 rs2 funct7` |
| MainControl | Lệnh này cần bật những tín hiệu nào? | `opcode` | `RegWrite ALUSrc MemWrite MemRead IsBranch ALUOp ImmSel ASel WBSel IsJAL IsJALR` |
| ImmGen | Hằng số trong lệnh là bao nhiêu? | `Instruction`, `ImmSel` | `Imm` |
| RegisterFile | Giá trị các thanh ghi nguồn, và ghi vào đâu? | `rs1 rs2 rd write_data RegWrite` | `rs1_data rs2_data` |
| ALUControl | ALU phải làm phép gì? | `ALUOp funct3 funct7` | `ALUCtrl` |
| ALU | Kết quả phép tính là gì? | `rs1_data rs2_data ALU_Ctrl` | `result` |
| BranchUnit | Có rẽ nhánh không? | `rs1_data rs2_data funct3 IsBranch` | `branch_taken` |
| LoadExtract | Giá trị load là gì? | từ RAM, `Address[1:0]`, `funct3` | `read_data` |
| StoreMerge | Từ mới ghi vào RAM là gì? | từ cũ, `write_data`, `funct3`, `Address[1:0]` | `new_word` |
| Memory | Đọc/ghi RAM thế nào? | `Address write_data MemWrite funct3` | `read_data` |
| `main` | Một lệnh chạy trọn vẹn thế nào? | xung nhịp | PC, thanh ghi, RAM |
| ForwardingUnit | Lấy toán hạng từ đâu cho đúng? | `rs1_ex rs2_ex rd_mem rd_wb RegWrite_*` | `ForwardA ForwardB` |
| HazardUnit | Có phải dừng pipeline không? | `MemRead_ex rd_ex rs1_id rs2_id` | `stall` |
| `Pipeline` | Năm lệnh chạy chồng thế nào? | xung nhịp | PC, thanh ghi, RAM |
