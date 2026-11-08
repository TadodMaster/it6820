# DEMO_EXPLAIN - mọi thứ xảy ra trong buổi demo

> Bản tiếng Việt của docs/DEMO_EXPLAIN.md.

Tài liệu này giải thích, từng lệnh và từng tín hiệu, **mạch làm gì khi bạn chạy demo**.  `docs/vi/PRESENTATION.md` cho biết *khi nào* bấm gì; tài liệu này cho biết *vì sao* màn hình thay đổi.  Mọi giá trị đều được đo trên project (vết probe của `RiscVComputer.circ`) và đối chiếu với bộ mô phỏng tham chiếu.

Nội dung: 1 Các chương trình - 2 Cách đọc một tick - 3 Một lệnh đi qua CPU single-cycle - 4 Cả 40 tick của `demo.s` - 5 Pipeline - 6 `hazards_demo.s` từng chu kỳ - 7 Phần chứng minh và các bài test làm gì - 8 Bảng tra nhanh

---

## 1. Các chương trình

### 1.1 `programs/demo.s` (nằm sẵn trong ROM của cả hai CPU)

| Địa chỉ | Mã máy | Lệnh | Dùng để làm gì |
|---|---|---|---|
| 0x00 | `00000513` | `li x10, 0` | x10 = tổng đang cộng dồn = 0 |
| 0x04 | `00a00593` | `li x11, 10` | x11 = biến đếm = 10 |
| 0x08 | `00b50533` | `loop: add x10, x10, x11` | tổng = tổng + biến đếm |
| 0x0c | `fff58593` | `addi x11, x11, -1` | biến đếm = biến đếm - 1 |
| 0x10 | `fe059ce3` | `bnez x11, loop` | lặp lại khi biến đếm khác 0 (nhảy lùi 8 byte) |
| 0x14 | `00a02023` | `sw x10, 0(x0)` | lưu tổng (55) vào từ 0 của bộ nhớ dữ liệu |
| 0x18 | `00002603` | `lw x12, 0(x0)` | nạp lại vào x12 |
| 0x1c | `010000ef` | `jal x1, double` | gọi hàm ở 0x2c, địa chỉ trả về 0x20 lưu vào x1 |
| 0x20 | `40a606b3` | `sub x13, x12, x10` | 110 - 55 = 55 |
| 0x24 | `0646a713` | `slti x14, x13, 100` | 55 < 100 nên x14 = 1 |
| 0x28 | `0000006f` | `halt: j halt` | vòng lặp vô hạn: chương trình đã xong |
| 0x2c | `00c60633` | `double: add x12, x12, x12` | x12 = 55 + 55 = 110 |
| 0x30 | `00008067` | `ret` (= `jalr x0, 0(x1)`) | nhảy về địa chỉ trong x1 (0x20) |

(`li x10,0` là lệnh giả `addi x10,x0,0`, `li x11,10` là `addi x11,x0,10`, `ret` là `jalr x0,0(x1)`.)

Kết quả: tổng 10 + 9 + ... + 1 = **55 = 0x37**; sau lời gọi hàm **x12 = 110 = 0x6e**; `x13 = 0x37`, `x14 = 1`; từ dữ liệu 0 = 0x37; PC cuối = 0x28; `x1 = 0x20`.

### 1.2 `programs/hazards_demo.s` (cho pipeline)

| Địa chỉ | Mã máy | Lệnh | Mục đích |
|---|---|---|---|
| 0x00 | `06400093` | `li x1, 100` | x1 = 100 |
| 0x04 | `00102023` | `sw x1, 0(x0)` | cần x1 ngay sau khi vừa tính xong: **forwarding** |
| 0x08 | `00002103` | `lw x2, 0(x0)` | load |
| 0x0c | `00110193` | `addi x3, x2, 1` | dùng x2 ngay sau lệnh load: **stall load-use** |
| 0x10 | `00218233` | `add x4, x3, x2` | x3 lại được forward |
| 0x14 | `00420663` | `beq x4, x4, skip` | luôn rẽ: **flush** hai lệnh kế tiếp |
| 0x18 | `00100293` | `addi x5, x0, 1` | KHÔNG được có hiệu lực |
| 0x1c | `00200313` | `addi x6, x0, 2` | KHÔNG được có hiệu lực |
| 0x20 | `00700393` | `skip: addi x7, x0, 7` | lệnh đầu tiên ở đích rẽ nhánh |
| 0x24 | `0000006f` | `halt: j halt` | kết thúc |

Kết quả: `x1 = 0x64`, `x2 = 0x64`, `x3 = 0x65`, `x4 = 0xc9`, `x7 = 7`, và **`x5 = x6 = 0`**.

---

## 2. Cách đọc một tick

* Một lần **Ctrl+F9** = một chu kỳ xung nhịp đầy đủ (clock 0 > 1 > 0).  Trên CPU single-cycle, việc này thực thi đúng một lệnh.
* Thanh ghi PC và RAM dữ liệu cập nhật ở sườn **lên**; trên pipeline, register file cập nhật ở sườn **xuống** (`CLK_n`).
* Sau một tick, PC đã trỏ tới lệnh **kế tiếp**.  Hàng theo dõi (probe) hiện lệnh kế tiếp đó (`instr`) và nó sẽ tính ra gì; tab State hiện các thanh ghi mà lệnh **trước** vừa ghi.  Vì vậy mỗi lệnh được thấy hai lần: trước hết là "sắp chạy" (probe), rồi "đã xong" (tab State) sau một tick.
* Probe: `main` có hàng theo dõi (`PC`, `instr`, `alu_result`, `branch_taken`, `wb_data`), hàng điều khiển (`RegWrite`, `MemWrite`, `ALUSrc`, `ALUCtrl`, `WBSel`) và hàng dữ liệu (`rs1_data`, `rs2_data`, `imm`, `mem_rdata`, `next_pc`).  `Pipeline` có hàng theo dõi (`PC`, `instr_id`, `stall`, `pc_src_ex`, `ForwardA`, `ForwardB`, `alu_result_ex`, `wb_data`), hàng ID/EX (`pc_id`, `rs1_data_id`, `rs2_data_id`, `imm_id`, `pc_ex`, `rd_ex`, `MemRead_ex`, `run`, `bubble`) và hàng EX/MEM/WB (`opA`, `opB`, `alu_a`, `alu_b`, `target_ex`, `alu_result_mem`, `rd_mem`, `mem_rdata_wb`, `rd_wb`, `RegWrite_wb`).  Số thanh ghi hiện dạng hex (`0a` = x10).
* Màu dây: xanh sáng = 1, xanh tối = 0 (tín hiệu 1 bit); các bus hiện giá trị dạng hex.

---

## 3. Một lệnh đi qua CPU single-cycle

Mọi lệnh đều đi qua cùng năm tầng trong một chu kỳ: **IF** (nạp từ ROM tại PC) > **ID** (giải mã, đọc thanh ghi, tạo hằng số) > **EX** (ALU, quyết định rẽ nhánh, PC kế tiếp) > **MEM** (RAM dữ liệu) > **WB** (ghi kết quả vào `rd`).  Dưới đây là giá trị trên các dây chính cho từng nhóm lệnh của `demo.s`.

### 3.1 Kiểu R: `add x10, x10, x11` (0x08, `00b50533`), lần đầu (tick 3)
* **IF**: ROM tại PC = 0x08 xuất `00b50533`; `pc_plus4` = 0x0c.
* **ID**: `InstructionDecode` cắt ra `opcode = 0x33`, `rd = 10`, `funct3 = 0`, `rs1 = 10`, `rs2 = 11`, `funct7 = 0`.  `MainControl`: `RegWrite = 1`, `ALUSrc = 0` (B là thanh ghi), `ALUOp = 10` (kiểu R), `MemWrite = MemRead = 0`, `WBSel = 00`.  Register file xuất `rs1_data = x10 = 0` và `rs2_data = x11 = 0x0a`.
* **EX**: `ALUControl` biến `ALUOp = 10, funct3 = 0, funct7 = 0` thành `ALUCtrl = 0` (ADD).  ALU tính 0 + 0x0a = **0x0a** (`alu_result`).  `IsBranch = 0` nên `branch_taken = 0`.
* **MEM**: không có gì (RAM không bị ghi).
* **WB**: `wb_data = alu_result = 0x0a`; ở sườn xung nhịp nó được ghi vào `x10`.  PC kế tiếp = PC + 4 = 0x0c.
* **Cách thấy**: probe `instr = 00b50533` và `alu_result = wb_data = 0000000a` *trước* tick; x10 đổi từ 0 sang 0x0a *sau* tick.

### 3.2 ALU kiểu I: `addi x11, x11, -1` (0x0c, `fff58593`)
* **ID**: `imm = 0xffffffff` (giá trị 12-bit `fff` được mở rộng dấu); `ALUSrc = 1` (B là hằng số); `ALUOp = 11` (kiểu I).
* **EX**: ngõ vào B của ALU = imm; `ALUCtrl = ADD`; 0x0a + (-1) = **0x09**.
* **WB**: x11 = 9.  Lần đầu (tick 4) probe hiện `alu_result = 9`.

### 3.3 Branch được rẽ: `bnez x11, loop` (0x10, `fe059ce3` = `bne x11, x0, -8`)
* **ID**: hằng số kiểu B là **-8** (`ImmGen` dựng lại từ các bit rải rác của lệnh); `IsBranch = 1`; `RegWrite = 0`.
* **EX**: `BranchUnit` so `rs1_data` (x11 = 9) với `rs2_data` (x0 = 0) bằng `funct3 = 001` (BNE): khác nhau, nên **`branch_taken = 1`** (probe hiện 1).  Logic PC kế tiếp: `pc_target = PC + imm = 0x10 - 8 = 0x08`; `take_target = 1`, nên `next_pc = 0x08`.
* **WB**: không ghi gì.  Sau tick, **PC lại là 0x08** (vòng lặp).
* Lần lặp cuối (x11 = 0): probe hiện `branch_taken = 0` sau tick 31, và `next_pc = PC + 4 = 0x14` ở tick 32: vòng lặp kết thúc.

### 3.4 Store: `sw x10, 0(x0)` (0x14, `00a02023`), tick 33
* **ID**: hằng số kiểu S = 0; `MemWrite = 1`, `RegWrite = 0`, `ALUSrc = 1`.
* **EX**: địa chỉ = `rs1 + imm` = x0 + 0 = **0** (`alu_result`).
* **MEM**: `Memory` nhận `Address = 0`, `write_data = rs2_data = x10 = 0x37`, `MemWrite = 1`, `funct3 = 010` (word); `StoreMerge` bật cả bốn tín hiệu cho phép byte, và ở sườn xung nhịp từ 0 của RAM thành **0x37**.
* **Cách thấy**: tick 33 không thanh ghi nào đổi; chỉ RAM đổi (phần chứng minh in ra là `0x0000  37`).

### 3.5 Load: `lw x12, 0(x0)` (0x18, `00002603`), tick 34
* **EX**: địa chỉ 0.  **MEM**: từ 0 của RAM = 0x37 xuất hiện trên `read_data`; `LoadExtract` với `funct3 = 010` (word) cho qua nguyên vẹn: `mem_rdata = 0x37`.
* **WB**: `WBSel = 01` chọn bộ nhớ thay cho ALU: `wb_data = 0x37` được ghi vào x12.

### 3.6 Nhảy và liên kết: `jal x1, double` (0x1c, `010000ef`), tick 35
* **ID**: hằng số kiểu J = 0x10; `IsJAL = 1`, `RegWrite = 1`, `WBSel = 10` (PC + 4).
* **EX**: `pc_target = PC + imm = 0x1c + 0x10 = 0x2c`; `take_target = IsJAL = 1`, nên `next_pc = 0x2c`.
* **WB**: `wb_data = pc_plus4 = 0x20` đi vào x1 (địa chỉ trả về).
* **Cách thấy**: PC nhảy từ 0x1c sang **0x2c** và x1 = 0x20.

### 3.7 Hàm: `add x12, x12, x12` (tick 36) và `ret` (tick 37, `00008067` = `jalr x0, 0(x1)`)
* `add x12,x12,x12`: 0x37 + 0x37 = **0x6e** đi vào x12.
* `ret`: `IsJALR = 1`; ALU tính `rs1 + imm = x1 + 0 = 0x20`; logic PC kế tiếp xóa bit 0 (`& 0xFFFFFFFE`) rồi chọn nó: `next_pc = 0x20`.  `rd = x0` nên giá trị liên kết bị bỏ đi (x0 không đổi được).
* PC đi từ 0x30 > **0x20**.

### 3.8 Sau lời gọi: `sub x13, x12, x10` (tick 38, `40a606b3`) và `slti x14, x13, 100` (tick 39, `0646a713`)
* `sub`: `funct7 = 0100000` làm `ALUControl` chọn SUB: 0x6e - 0x37 = **0x37** đi vào x13.
* `slti`: kiểu I, `funct3 = 010`: ALU so sánh có dấu 0x37 < 100, kết quả 1, nên **x14 = 1**.

### 3.9 Kết thúc: `halt: j halt` (0x28, `0000006f` = `jal x0, 0`)
Nhảy về chính nó: `pc_target = PC + 0 = 0x28`.  PC đứng ở 0x28 mãi mãi; `rd = x0` nên không thanh ghi nào đổi.  Nghĩa là "chương trình đã kết thúc"; bấm thêm tick cũng không có gì thay đổi.

---

## 4. Cả 40 tick của `demo.s` (single-cycle)

Tick n thực thi lệnh ở PC *trước* tick; hai cột cuối là trạng thái *sau* tick.

| Tick | Thực thi (PC) | Lệnh | Thay đổi thanh ghi / bộ nhớ | PC sau |
|---:|---|---|---|---|
| 1 | 0x00 | `li x10, 0` | (x10 vẫn là 0) | 0x04 |
| 2 | 0x04 | `li x11, 10` | x11 = 0x0a | 0x08 |
| 3 | 0x08 | `add x10,x10,x11` | x10 = 0x0a | 0x0c |
| 4 | 0x0c | `addi x11,x11,-1` | x11 = 0x09 | 0x10 |
| 5 | 0x10 | `bnez` (rẽ) | - | 0x08 |
| 6 | 0x08 | `add` | x10 = 0x13 | 0x0c |
| 7 | 0x0c | `addi` | x11 = 0x08 | 0x10 |
| 8 | 0x10 | `bnez` (rẽ) | - | 0x08 |
| 9 | 0x08 | `add` | x10 = 0x1b | 0x0c |
| 10 | 0x0c | `addi` | x11 = 0x07 | 0x10 |
| 11 | 0x10 | `bnez` (rẽ) | - | 0x08 |
| 12 | 0x08 | `add` | x10 = 0x22 | 0x0c |
| 13 | 0x0c | `addi` | x11 = 0x06 | 0x10 |
| 14 | 0x10 | `bnez` (rẽ) | - | 0x08 |
| 15 | 0x08 | `add` | x10 = 0x28 | 0x0c |
| 16 | 0x0c | `addi` | x11 = 0x05 | 0x10 |
| 17 | 0x10 | `bnez` (rẽ) | - | 0x08 |
| 18 | 0x08 | `add` | x10 = 0x2d | 0x0c |
| 19 | 0x0c | `addi` | x11 = 0x04 | 0x10 |
| 20 | 0x10 | `bnez` (rẽ) | - | 0x08 |
| 21 | 0x08 | `add` | x10 = 0x31 | 0x0c |
| 22 | 0x0c | `addi` | x11 = 0x03 | 0x10 |
| 23 | 0x10 | `bnez` (rẽ) | - | 0x08 |
| 24 | 0x08 | `add` | x10 = 0x34 | 0x0c |
| 25 | 0x0c | `addi` | x11 = 0x02 | 0x10 |
| 26 | 0x10 | `bnez` (rẽ) | - | 0x08 |
| 27 | 0x08 | `add` | x10 = 0x36 | 0x0c |
| 28 | 0x0c | `addi` | x11 = 0x01 | 0x10 |
| 29 | 0x10 | `bnez` (rẽ) | - | 0x08 |
| 30 | 0x08 | `add` | x10 = 0x37 (= 55) | 0x0c |
| 31 | 0x0c | `addi` | x11 = 0x00 | 0x10 |
| 32 | 0x10 | `bnez` (**không** rẽ) | - | 0x14 |
| 33 | 0x14 | `sw x10,0(x0)` | từ bộ nhớ 0 = 0x37 | 0x18 |
| 34 | 0x18 | `lw x12,0(x0)` | x12 = 0x37 | 0x1c |
| 35 | 0x1c | `jal x1,double` | x1 = 0x20 | **0x2c** |
| 36 | 0x2c | `add x12,x12,x12` | x12 = 0x6e (= 110) | 0x30 |
| 37 | 0x30 | `ret` | - | **0x20** |
| 38 | 0x20 | `sub x13,x12,x10` | x13 = 0x37 | 0x24 |
| 39 | 0x24 | `slti x14,x13,100` | x14 = 0x01 | 0x28 |
| 40 | 0x28 | `halt` | - | 0x28 (đứng yên) |

Vì sao kết quả ghi 39 chu kỳ chứ không phải 40: tick thứ 40 chỉ lặp lại lệnh nhảy cuối; lần ghi thanh ghi cuối cùng xảy ra ở tick 39 (`live_proof.py` báo 39 chu kỳ, CPI 1.00).

Những điểm nên chỉ: PC **quay lùi** ở các tick 5, 8, 11, ... (vòng lặp); ở tick 32 nó cuối cùng **đi tiếp**; ở tick 35 nó **nhảy tới** 0x2c và x1 được gán; ở tick 37 nó **trở về** 0x20.

---

## 5. Pipeline: cùng các lệnh đó trong năm tầng

Trên CPU pipeline, năm tầng làm việc trên năm lệnh khác nhau cùng một lúc.  Một lệnh cần 5 chu kỳ từ lúc nạp đến lúc write-back, nhưng khi mọi thứ suôn sẻ thì mỗi chu kỳ có một lệnh hoàn thành.

```
              1   2   3   4   5   6   7   8
lệnh A        IF  ID  EX  ME  WB
lệnh B            IF  ID  EX  ME  WB
lệnh C                IF  ID  EX  ME  WB
lệnh D                    IF  ID  EX  ME  WB
```

* **IF/ID, ID/EX, EX/MEM, MEM/WB** là các thanh ghi pipeline (các hộp có nhãn giữa các tầng): chúng giữ mọi thứ mà một lệnh cần ở tầng kế tiếp (PC, giá trị thanh ghi, hằng số, thanh ghi đích `rd`, từ điều khiển).
* Các tín hiệu điều khiển chỉ được tạo một lần, ở tầng ID, đóng gói thành "từ điều khiển" và đi cùng lệnh; mỗi tầng dùng phần của mình.
* Register file ghi ở sườn **xuống**, nên lệnh ở tầng WB ghi trong nửa đầu chu kỳ và lệnh ở tầng ID đọc giá trị mới trong nửa sau.
* Cái giá: mỗi branch hoặc lệnh nhảy được rẽ tốn 2 chu kỳ (hai lệnh đã nạp phía sau bị hủy).  Điều này giải thích 64 chu kỳ của `demo.s` trên pipeline: 39 lệnh, cộng 11 lần chuyển hướng x 2 = 22 chu kỳ mất đi (9 lần `bnez` được rẽ, một `jal` và một `ret`), thành 61; 3 chu kỳ còn lại là thời gian làm đầy pipeline (write-back đến sau fetch 4 tầng, và số chu kỳ của single-cycle đã tính sẵn một).
* Lợi ích thật của pipeline là chu kỳ xung nhịp ngắn hơn (đường dài nhất chỉ còn một tầng thay vì năm); mô phỏng không độ trễ của Logisim không cho thấy điều này, nên tính theo chu kỳ thì pipeline trông chậm hơn.

---

## 6. `hazards_demo.s` trên pipeline, từng chu kỳ

Tình trạng các tầng **sau** mỗi tick (cái bạn thấy trong mạch và ở hàng theo dõi).  "bubble" = một NOP do logic hazard chèn vào.

| Sau tick | IF (PC) | ID | EX | MEM | WB | `stall` | `pc_src_ex` | `ForwardA` | `ForwardB` | Chuyện gì xảy ra |
|---:|---|---|---|---|---|:-:|:-:|:-:|:-:|---|
| 1 | sw (04) | li x1 | - | - | - | 0 | 0 | 00 | 00 | pipeline đang được làm đầy |
| 2 | lw (08) | sw | li | - | - | 0 | 0 | 00 | 00 | `li` tính 0x64 ở EX |
| 3 | addi x3 (0c) | lw | sw | li | - | 0 | 0 | 00 | **10** | **forwarding**: `sw` cần x1; `li` đang ở MEM, nên kết quả ALU 0x64 của nó được lấy từ EX/MEM (ForwardB = 10) thay vì chờ register file |
| 4 | add x4 (10) | addi x3 | lw | sw | li | **1** | 0 | 00 | 00 | phát hiện **hazard load-use**: `addi x3,x2,1` (ở ID) cần x2, mà `lw` (ở EX) chỉ có dữ liệu ở cuối MEM: `stall` = 1 |
| 5 | add x4 (**10**, giữ nguyên) | addi x3 | **bubble** | lw | sw | 0 | 0 | 10 | 00 | PC và IF/ID **đứng yên**; bubble ở EX là một chu kỳ bị mất |
| 6 | beq (14) | add x4 | addi x3 | bubble | lw | 0 | 0 | **01** | 00 | `lw` ở WB: dữ liệu của nó đến `addi` qua MEM/WB (ForwardA = 01); `addi` tính 0x65 |
| 7 | addi x5 (18) | beq | add x4 | addi x3 | bubble | 0 | 0 | **10** | 00 | `add x4,x3,x2`: x3 lấy từ EX/MEM (ForwardA = 10), x2 đã nằm trong register file; kết quả 0xc9 |
| 8 | addi x6 (1c) | addi x5 | **beq** | add x4 | addi x3 | 0 | **1** | 10 | 10 | `beq x4,x4` so hai bản x4 đã forward: **được rẽ**, `pc_src_ex` = 1 |
| 9 | skip (**20**) | **bubble** | **bubble** | beq | add x4 | 0 | 0 | 00 | 00 | **flush**: hai lệnh nạp sau `beq` (`addi x5`, `addi x6`) đã thành bubble; PC giờ là đích 0x20 |
| 10 | halt (24) | addi x7 | bubble | bubble | beq | 0 | 0 | 00 | 00 | chương trình tiếp tục ở đích |
| 11 | (28) | halt | addi x7 | bubble | bubble | 0 | 0 | 00 | 00 | `addi x7,x0,7` tính 7 |
| 12 | (2c) | bubble | halt | addi x7 | bubble | 0 | **1** | 00 | 00 | lệnh `j halt` cuối lại chuyển hướng (và flush); điều này lặp mãi và là bình thường |

(`ForwardA = 10` ở tick 5 thuộc về bubble ở EX: bubble giữ số hiệu thanh ghi của lệnh bị stall nhưng từ điều khiển của nó bằng 0, nên nó không làm gì.)

Cuối cùng (sau khoảng 13 tick) tab State phải hiện `x1 = 0x64`, `x2 = 0x64`, `x3 = 0x65`, `x4 = 0xc9`, `x7 = 0x07`, và `x5 = x6 = 0`: các lệnh bị flush không để lại dấu vết.  Ba loại hazard, ba cách giải quyết:

| Hazard | Thấy ở đâu | Cách giải quyết | Chi phí |
|---|---|---|---|
| dùng giá trị vừa do ALU tính | `ForwardA/B` = 10 hoặc 01 | forwarding từ EX/MEM hoặc MEM/WB | 0 chu kỳ |
| dùng giá trị vừa load | `stall` = 1, PC đứng ở 10 trong một tick | một bubble, rồi forwarding | 1 chu kỳ |
| branch / lệnh nhảy được rẽ | `pc_src_ex` = 1, sau đó `instr_id` = 0 | flush hai lệnh đã nạp | 2 chu kỳ |

---

## 7. Phần chứng minh và các bài test làm gì

* `python tools\live_proof.py` assemble chương trình rồi chạy trên **bộ mô phỏng tham chiếu** (mã Python độc lập), trên **mạch single-cycle** và trên **mạch pipeline** (cả hai chạy qua chính Logisim, không cần GUI).  Sau đó nó so cả 32 thanh ghi và mọi từ dữ liệu khác 0 (mỗi mục báo `OK`) và in `VERDICT: both CPUs produce exactly the reference result`, kèm số chu kỳ (39 và 64).
* `tests\run_tests.ps1`: test vector của Logisim cho 9 khối (106 hàng: mọi opcode trong `MainControl`, mọi phép của ALU, ...).
* `tests\run_cpu_tests.py --circuit all`: 7 chương trình trên cả hai CPU, so với bộ mô phỏng tham chiếu.
* `tests\fuzz.py`: chương trình ngẫu nhiên có nhiều phụ thuộc, so sánh tương tự.
* `tools\presentation_check.ps1`: chạy tất cả các bước trên ở dạng rút gọn và kết thúc bằng `READY` hoặc `NOT READY`.

---

## 8. Bảng tra nhanh

| Tôi thấy ... | Nghĩa là ... |
|---|---|
| PC quay lại 0x08 | branch của vòng lặp được rẽ (ngay trước đó `branch_taken` = 1) |
| PC nhảy tới 0x2c và x1 = 0x20 | `jal`: gọi hàm, đã lưu địa chỉ trả về |
| PC đi từ 0x30 về 0x20 | `ret`: trả về qua x1 |
| pipeline: PC đứng yên một tick | stall load-use (ngay trước đó `stall` = 1) |
| pipeline: `ForwardA/B` khác 00 | một toán hạng được lấy từ thanh ghi pipeline |
| pipeline: `pc_src_ex` = 1, sau đó `instr_id` = 0 | branch / lệnh nhảy được rẽ: các lệnh sai đường đã bị flush |
| `x5 = x6 = 0` ở cuối demo hazard | flush đã thực sự hủy chúng |
| `VERDICT ... exactly the reference result` ở phần chứng minh | các mạch khớp với chuẩn tham chiếu độc lập |
