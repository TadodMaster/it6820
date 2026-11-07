# Hướng dẫn đầy đủ: máy tính này hoạt động như thế nào

> Bản tiếng Việt của docs/GUIDE.md.

Tài liệu này giải thích **mọi thứ** trong dự án, bắt đầu từ "CPU là gì" và kết thúc ở cách các bài kiểm thử và bộ sinh mạch (generator) hoạt động.
Mọi giá trị tín hiệu được nêu đều là thật: chúng được đọc từ các mạch đang chạy bằng `tools/probe.py`.
Hãy đọc từ đầu đến cuối một lần; về sau dùng mục lục như tài liệu tra cứu.

| Phần | Nội dung |
|---|---|
| [1](#1-what-a-computer-does) | CPU làm gì, RISC-V trong năm phút |
| [2](#2-the-project-at-a-glance) | hai CPU, các tệp, cách tổ chức một dự án Logisim |
| [3](#3-using-the-circuits-in-logisim) | từng bước: nạp chương trình, chạy, xem bên trong |
| [4](#4-the-building-blocks-one-by-one) | từng khối: làm gì, được xây dựng ra sao, vì sao, kiểm thử thế nào |
| [5](#5-following-instructions-through-the-single-cycle-cpu) | giá trị tín hiệu thật cho `add`, `addi`, nhánh được thực hiện, `lw`, `jal`, `ret` |
| [6](#6-the-memory-system) | RAM, truy cập byte / halfword, giải thích `StoreMerge` qua ví dụ |
| [7](#7-the-pipelined-cpu) | vì sao dùng pipeline, hazard, forwarding, stall, flush |
| [8](#8-watching-the-pipeline-a-real-trace) | vết (trace) từng chu kỳ của pipeline |
| [9](#9-performance) | CPI, số chu kỳ, vì sao pipeline không nhanh hơn về số chu kỳ |
| [10](#10-writing-and-running-programs) | hợp ngữ, trình hợp dịch, bản đồ bộ nhớ |
| [11](#11-how-everything-is-tested) | chiến lược kiểm thử |
| [12](#12-how-to-extend-the-design) | thêm lệnh và tính năng |
| [13](#13-troubleshooting) | sự cố và cách khắc phục |
| [14](#14-glossary) | các thuật ngữ dùng trong dự án |

Chi tiết hơn: [REPORT.md](REPORT.md) (báo cáo chính thức), [TOOLS.md](TOOLS.md) (cách các công cụ hoạt động bên trong), [DESIGN_LOG.md](DESIGN_LOG.md) (lịch sử và các bẫy thường gặp).

---

## 1. What a computer does

Bộ xử lý lặp lại mãi một vòng, chu trình **fetch - decode - execute** (nạp - giải mã - thực thi):

1. **Fetch**: đọc lệnh kế tiếp (một số 32 bit) từ bộ nhớ lệnh tại địa chỉ nằm trong **program counter (PC)**.
2. **Decode**: xem các trường bit của lệnh: phép toán nào, thanh ghi nào, hằng số nào.
3. **Execute**: thực hiện phép toán (số học, so sánh, tính địa chỉ).
4. **Memory**: với lệnh load / store, đọc hoặc ghi bộ nhớ dữ liệu.
5. **Write back**: lưu kết quả vào một thanh ghi.
6. Cập nhật PC: thông thường là `PC + 4` (lệnh dài 4 byte), hoặc một địa chỉ mới nếu là lệnh nhảy hoặc nhánh được thực hiện.

Năm bước đó chính là năm stage IF, ID, EX, MEM, WB.  CPU *single-cycle* thực hiện tất cả trong một chu kỳ xung nhịp; CPU *pipelined*
xử lý năm lệnh khác nhau cùng lúc, mỗi lệnh ở một stage.

### RISC-V in five minutes
RISC-V là một tập lệnh mở.  Tập số nguyên 32 bit cơ sở được gọi là **RV32I**.  Nó có:

* **32 thanh ghi (register)** `x0..x31`, mỗi thanh ghi 32 bit.  `x0` luôn đọc ra 0 và bỏ qua mọi thao tác ghi.  Trình hợp dịch cũng hiểu các tên ABI:

| Register | Tên ABI | Công dụng thường gặp |
|---|---|---|
| x0 | zero | hằng số 0 |
| x1 | ra | địa chỉ trả về |
| x2 | sp | con trỏ stack |
| x3, x4 | gp, tp | con trỏ toàn cục / con trỏ luồng |
| x5-x7 | t0-t2 | biến tạm |
| x8, x9 | s0 (fp), s1 | được lưu |
| x10-x17 | a0-a7 | đối số / kết quả |
| x18-x27 | s2-s11 | được lưu |
| x28-x31 | t3-t6 | biến tạm |

* **Mọi lệnh đều dài 32 bit** và có sáu dạng (R, I, S, B, U, J).  7 bit thấp nhất (`opcode`) cho biết dạng nào.
  Số hiệu thanh ghi luôn nằm ở cùng các vị trí bit, nhờ đó giải mã rất rẻ:

```
 31        25 24    20 19    15 14  12 11     7 6      0
 +-----------+--------+--------+------+--------+--------+
 |  funct7   |  rs2   |  rs1   |funct3|   rd   | opcode |   R-type   add rd, rs1, rs2
 +-----------+--------+--------+------+--------+--------+
 |      imm[11:0]     |  rs1   |funct3|   rd   | opcode |   I-type   addi rd, rs1, imm   lw rd, imm(rs1)
 +-----------+--------+--------+------+--------+--------+
 | imm[11:5] |  rs2   |  rs1   |funct3|imm[4:0]| opcode |   S-type   sw rs2, imm(rs1)
 +-----------+--------+--------+------+--------+--------+
 | imm[12|10:5] rs2   |  rs1   |funct3|imm[4:1|11]| opcode|  B-type   beq rs1, rs2, offset
 +--------------------+--------+------+--------+--------+
 |            imm[31:12]                |   rd   | opcode |   U-type   lui rd, imm20
 +--------------------------------------+--------+--------+
 |   imm[20|10:1|11|19:12]               |   rd   | opcode |   J-type   jal rd, offset
 +--------------------------------------+--------+--------+
```

* **Kiến trúc load / store**: chỉ `lw`, `sw` (và các phiên bản byte / halfword) mới truy cập bộ nhớ; các phép số học chỉ làm việc trên thanh ghi.
* **Immediate** (hằng số nằm trong lệnh) được mở rộng dấu lên 32 bit.  Offset của lệnh nhánh và lệnh nhảy tính bằng byte và luôn chẵn.

Ví dụ: `addi x1, x0, 5` là `0x00500093`: `imm = 000000000101`, `rs1 = 0`, `funct3 = 000`, `rd = 1`, `opcode = 0010011`.

---

## 2. The project at a glance

```
RiscVComputer.circ
 |- main            CPU single-cycle   (mạch được mở đầu tiên)
 |- Pipeline        CPU pipeline 5 stage
 |- InstructionDecode  MainControl  ImmGen  RegisterFile  ALUControl  ALU  BranchUnit
 |- Memory  (= RAM + LoadExtract + StoreMerge)
 |- ForwardingUnit  HazardUnit        (chỉ dùng cho pipeline)
```

Cả hai CPU được xây từ **cùng các khối**; chỉ khác nhau ở cách nối dây cấp cao nhất.  Cả hai chạy cùng một mã máy.
Bộ nhớ được tổ chức theo kiểu máy **Harvard**: một ROM lệnh 256 từ và một RAM dữ liệu 256 từ riêng biệt (mỗi bộ 1 KiB).
Không thể nạp lệnh từ RAM dữ liệu và chương trình không thể tự ghi đè lên chính nó.

### How a Logisim project is organised
* Mỗi hộp có thanh tiêu đề đen (`ALU`, `MainControl`, ...) là một **sub-circuit** (mạch con): một mạch được dùng như một con chip.  Nhấp đúp vào nó
  (công cụ Poke: nhấp vào kính lúp) để xem bên trong.
* **Tunnel** là một đầu dây có gắn nhãn (`rs1_data`, `alu_result`, ...).  **Mọi tunnel cùng tên trong một mạch đều được nối với nhau**,
  mà không cần vẽ dây giữa chúng.  Trong dự án này, mọi kết nối dài đều là tunnel; dây chỉ xuất hiện giữa một chân (pin) và tunnel của nó.
* **Splitter** cắt một dây nhiều bit thành các phần hoặc gộp các phần thành một dây (ví dụ cắt `instr` thành các trường).
* **Register** lưu một giá trị tại sườn lên của xung nhịp khi tín hiệu enable của nó bằng 1.
* Độ dày và màu của dây: dày = bus nhiều bit, mỏng = 1 bit; xanh lục nhạt = 1, tối = 0, xanh dương = thả nổi (floating), đỏ = xung đột, cam = lệch độ rộng.

### What each folder is for
| Thư mục | Mục đích |
|---|---|
| `programs/` | các chương trình hợp ngữ: `demo.s` (nạp sẵn), `hazards_demo.s` |
| `tests/` | mọi thứ dùng để kiểm tra thiết kế |
| `tools/` | trình hợp dịch / trình mô phỏng, các tiện ích Java, bộ sinh mạch |
| `docs/` | tài liệu (bạn đang ở đây) và hình ảnh của mọi mạch (`docs/img`) |
| `backup/` | các phiên bản trước của tệp `.circ` |

---

## 3. Using the circuits in Logisim

1. Khởi động: `java -jar logisim-evolution-4.1.0-all.jar RiscVComputer.circ` (Java **21** trở lên).
2. Nhấp đúp `main` trong cây bên trái.  Biểu tượng bàn tay trên thanh công cụ là **Poke tool** (nhấp vào giá trị để thay đổi), mũi tên là công cụ Edit.
3. **Nạp chương trình.**  ROM lệnh đã chứa sẵn `programs/demo.s`.  Để nạp chương trình khác: `python tools\rv.py asm myprog.s -o myprog.hex`, sau đó
   nhấp phải vào ROM, chọn **Load Image...**, gõ đường dẫn của tệp `.hex` và nhấn Enter.  (Định dạng tệp: dòng đầu là `v2.0 raw`, sau đó là các từ hex.)
4. **Reset.**  Poke chân `RESET` lên 1 rồi về 0.  RESET xóa thanh ghi PC (đó là đầu vào xóa bất đồng bộ của thanh ghi).  Một dự án vừa
   được nạp đã sẵn sàng bắt đầu với PC = 0 và mọi thanh ghi = 0.
5. **Chạy từng bước.**  `Simulate > Manual Tick Full Cycle` (**Ctrl+F9**) = một chu kỳ xung nhịp hoàn chỉnh (sườn lên + sườn xuống) = một lệnh trong CPU single-cycle.
   `Auto-Tick Enabled` (Ctrl+K) cho xung nhịp chạy tự do; `Manual Tick Half Cycle` là Ctrl+T; `Simulate > Reset Simulation` (Ctrl+R) xóa mọi thanh ghi và bộ nhớ.
6. **Xem giá trị.**  Thanh ghi PC hiển thị giá trị trong hộp của nó.  Các hình oval màu vàng là probe (`instr`, `wb_data`).  Để xem register file, dùng
   công cụ Poke và nhấp vào **kính lúp** trên hộp `RegisterFile`: các thanh ghi được gắn nhãn `x0`..`x31` và hiển thị giá trị của chúng.  Cách này cũng áp dụng cho
   `Memory` (RAM hiển thị nội dung khi bạn nhấp vào nó, sau đó *Edit contents* hiển thị bảng).
7. **Quan trọng:** hãy xem các thanh ghi qua kính lúp trên hộp nằm *bên trong* `main` (hoặc `Pipeline`).  Nếu bạn mở `RegisterFile` từ cây dự án
   thì bạn đang nhìn vào một bản sao riêng, không được sử dụng.

---

## 4. The building blocks one by one

Với mỗi khối: **làm gì**, **được xây dựng ra sao**, **vì sao**, **kiểm thử thế nào**.  Hình ảnh nằm ở `docs/img/<Block>.png`; hãy mở mạch trong
Logisim để xem cùng nội dung đó trực tiếp.

### 4.1 InstructionDecode
*Làm gì:* tách lệnh thành các trường.  *Cách xây dựng:* một splitter duy nhất.  Ở đây không có gì được "quyết định": với lệnh I-type thì `rs2` thực chất là một phần của
immediate, nhưng splitter vẫn xuất các bit [24:20] thành `rs2`; đơn vị điều khiển quyết định trường nào có ý nghĩa.
`opcode = instr[6:0]`, `rd = [11:7]`, `funct3 = [14:12]`, `rs1 = [19:15]`, `rs2 = [24:20]`, `funct7 = [31:25]`.

### 4.2 MainControl
*Làm gì:* biến `opcode` thành các tín hiệu điều khiển.  *Cách xây dựng:* chín bộ so sánh, mỗi bộ so sánh opcode 7 bit với một hằng số, cho ra chín cờ một bit
(`IsR IsI IsLoad IsStore IsBranch IsLui IsAuipc IsJAL IsJALR`).  Các cổng OR kết hợp các cờ thành các tín hiệu:

| Tín hiệu | Phương trình | Ý nghĩa |
|---|---|---|
| `RegWrite` | R + I + Load + LUI + AUIPC + JAL + JALR | lệnh ghi vào `rd` |
| `ALUSrc` | I + Load + Store + LUI + AUIPC + JALR | đầu vào B của ALU là immediate |
| `MemWrite` | Store | |
| `MemRead` | Load | |
| `IsBranch`, `IsJAL`, `IsJALR` | chính các cờ | |
| `ALUOp` (2 bit) | `{R+I, I+Branch}` | 00 cộng, 01 trừ, 10 R-type, 11 I-type |
| `ImmSel` (3 bit) | `{JAL, Branch+LUI+AUIPC, Store+LUI+AUIPC}` | 000 I, 001 S, 010 B, 011 U, 100 J |
| `ASel` (2 bit) | `{LUI, AUIPC}` | 00 `rs1`, 01 PC, 10 zero |
| `WBSel` (2 bit) | `{JAL+JALR, Load}` | 00 ALU, 01 bộ nhớ, 10 PC+4 |

*Vì sao có `ASel` / `WBSel`?*  `auipc` cần PC làm đầu vào ALU, `lui` cần 0 (để `0 + imm` cho ra immediate), và `jal` / `jalr` phải ghi `PC+4` vào `rd`.
Thêm hai bộ chọn nhỏ cho phép tất cả các lệnh này dùng lại đường đi ALU thông thường.
*Kiểm thử:* `tests/maincontrol.vec` kiểm tra toàn bộ bảng cho cả chín opcode và một opcode không xác định.

### 4.3 ImmGen
*Làm gì:* tạo immediate 32 bit.  Các bit immediate bị **xáo trộn** trong lệnh (để `rs1`, `rs2`, `rd` luôn nằm ở vị trí cố định); ImmGen
sắp xếp chúng lại:

| Dạng | Immediate | Ghép từ |
|---|---|---|
| I | 12 bit | `instr[31:20]` |
| S | 12 bit | `instr[31:25]`, `instr[11:7]` |
| B | 13 bit (bit 0 = 0) | `instr[31]`, `[7]`, `[30:25]`, `[11:8]`, 0 |
| U | 32 bit | `instr[31:12]` theo sau là 12 số 0 |
| J | 21 bit (bit 0 = 0) | `instr[31]`, `[19:12]`, `[20]`, `[30:21]`, 0 |

Sau đó một bộ mở rộng bit sao chép bit cao nhất để lấp đầy 32 bit (**sign extension** - mở rộng dấu), nhờ vậy `addi x1,x1,-1` cộng thêm `0xFFFFFFFF`.
Một bộ ghép kênh (multiplexer) 8 đầu vào (dùng 5 đầu vào) chọn định dạng theo `ImmSel`.  *Kiểm thử:* `immgen.vec`.

### 4.4 RegisterFile
*Làm gì:* 32 thanh ghi, hai cổng đọc (`rs1_data`, `rs2_data`) và một cổng ghi.  *Cách xây dựng:* 32 component register; phía **ghi** là một bộ phân kênh (demultiplexer) 1 sang 32
có đầu vào dữ liệu là `RegWrite` và đầu chọn là `rd`, nên chỉ thanh ghi `rd` nhận write-enable (và chỉ khi `RegWrite = 1`).
Mọi thanh ghi dùng chung `wb_data` và xung nhịp.  Phía **đọc** là hai bộ ghép kênh 32 sang 1 được chọn bởi `rs1` / `rs2`; chúng *bất đồng bộ*: đổi `rs1`
thì `rs1_data` đổi ngay lập tức.  Thanh ghi `x0` có hằng số 0 làm đầu vào dữ liệu, nên nó luôn giữ giá trị 0.
*Vì sao đọc bất đồng bộ?* Trong CPU single-cycle, giá trị phải tới ALU ngay trong cùng chu kỳ.

### 4.5 ALU and ALUControl
*ALU:* tính đồng thời cả mười phép toán (bộ cộng, bộ trừ, AND, OR, XOR, ba bộ dịch, hai bộ so sánh); một bộ ghép kênh 16 sang 1 chọn một kết quả
theo `ALUCtrl`.  Lượng dịch = 5 bit thấp của B.  `SLT` / `SLTU` cho ra 0 hoặc 1 (mở rộng bằng số 0).

| ALUCtrl | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| Phép toán | ADD | SUB | AND | OR | XOR | SLL | SRL | SRA | SLT | SLTU |

*ALUControl:* chuyển `(ALUOp, funct3, funct7)` thành `ALUCtrl`.  Giải mã hai tầng giúp khối điều khiển chính nhỏ gọn:
`ALUOp = 00` ép thành ADD (load, store, tính địa chỉ và địa chỉ nhảy), `01` ép thành SUB, `10` giải mã funct3 (và bit 5 của funct7 cho ADD/SUB và SRL/SRA),
`11` giải mã funct3 cho các lệnh immediate (bit 5 của funct7 chỉ dùng cho SRLI / SRAI, vì `addi` không có dạng "sub").
*Kiểm thử:* `alu.vec`, `alucontrol.vec` (mọi phép toán, dạng R và I).

### 4.6 BranchUnit
*Làm gì:* quyết định một nhánh có điều kiện có được thực hiện hay không.  *Cách xây dựng:* một bộ so sánh không dấu và một bộ so sánh có dấu cho ra `a==b`, `a<u b`, `a<s b`; các cổng NOT cho ra `!=`,
`>=u`, `>=s`; một bộ ghép kênh được chọn bởi `funct3` chọn điều kiện; `branch_taken = IsBranch AND condition`.

| funct3 | 000 | 001 | 100 | 101 | 110 | 111 |
|---|---|---|---|---|---|---|
| lệnh | beq | bne | blt | bge | bltu | bgeu |

*Kiểm thử:* `branchunit.vec` (cả hai chiều của mỗi điều kiện, cộng các trường hợp biên có dấu so với không dấu như `-1` so với `1`).

### 4.7 The next-PC logic (inside `main` / `Pipeline`)
```
pc_target   = PC + imm                          (đích của nhánh và JAL)
jalr_target = (rs1 + imm) với bit 0 bị xóa       (kết quả ALU, đã che bit)
take_target = branch_taken OR IsJAL
next_pc     = IsJALR ? jalr_target : take_target ? pc_target : PC + 4
```
`jalr` xóa bit 0 vì đặc tả RISC-V quy định như vậy (cho phép phần mềm lưu cờ trong bit thấp của một con trỏ hàm).

---

## 5. Following instructions through the single-cycle CPU

Đây là các giá trị thật từ `main` đang chạy `programs/demo.s` (đọc bằng `python tools/probe.py RiscVComputer.circ main programs/demo.s N <signals>`).

### 5.1 `add x10, x10, x11`  (R-type; `instr = 00b50533`, vòng lặp đầu tiên)
| Stage | Tín hiệu |
|---|---|
| Fetch | `pc = 8`, `instr = 00b50533`, `pc_plus4 = 0c` |
| Decode | `opcode = 33`, `rs1 = 0a (x10)`, `rs2 = 0b (x11)`, `rd = 0a`, `funct3 = 0`, `funct7 = 0` |
| Control | `RegWrite = 1`, `ALUSrc = 0`, `ALUOp = 10`, `ASel = 00`, `WBSel = 00`, `MemRead = MemWrite = 0` |
| Đọc thanh ghi | `rs1_data = 0` (x10), `rs2_data = 0x0a` (x11 = 10) |
| Execute | `ALUCtrl = 0 (ADD)`, `alu_a = 0`, `alu_b = 0x0a`, `alu_result = 0x0a` |
| Write back | `wb_data = 0x0a` được ghi vào x10 ở sườn xung nhịp; `next_pc = 0c` |

### 5.2 `bnez x11, loop`  (= `bne x11, x0, loop`; `instr = fe059ce3`, được thực hiện)
`opcode = 63`, `imm = 0xfffffff8` (-8, B-immediate), `IsBranch = 1`, `ALUOp = 01`, `rs1_data = 8` (x11), `rs2_data = 0`.  `BranchUnit`: `8 != 0` nên
`branch_taken = 1`.  `pc_target = 0x10 + (-8) = 0x08` và `next_pc = 0x08`: vòng lặp quay lại lệnh `add`.  `RegWrite = 0`: không có gì được ghi.

### 5.3 `lw x12, 0(x0)`  (`instr = 00002603`)
`imm = 0` (I-type), `alu_a = x0 = 0`, `alu_b = imm = 0`, `alu_result = 0` chính là **địa chỉ**.  `MemRead = 1`.  `Memory` trả về `mem_rdata = 0x37` (55, được lưu trước đó bởi
`sw`).  `WBSel = 01` chọn giá trị từ bộ nhớ: `wb_data = 0x37`, được ghi vào x12.

### 5.4 `jal x1, double`  (`instr = 010000ef`, tại `pc = 0x1c`)
`imm = 0x10` (J-immediate).  `IsJAL = 1`, `take_target = 1`, `pc_target = 0x1c + 0x10 = 0x2c`, nên `next_pc = 0x2c`.  `WBSel = 10`: `wb_data = pc_plus4 = 0x20` được ghi vào `x1`
(`ra`), tức địa chỉ trả về.  Không cần dùng đến ALU.

### 5.5 `ret`  (= `jalr x0, 0(x1)`; `instr = 00008067`)
`rs1_data = 0x20` (ra), `imm = 0`, `alu_result = 0x20`, `jalr_target = 0x20`; `IsJALR = 1` khiến `next_pc = jalr_target = 0x20`: việc thực thi tiếp tục sau lệnh gọi.
`rd = x0`, nên giá trị liên kết `wb_data = 0x34` bị bỏ đi (thao tác ghi vào x0 bị bỏ qua).

---

## 6. The memory system

### 6.1 Instruction ROM
256 từ.  PC đếm theo byte, nên địa chỉ ROM là **chỉ số từ** `PC[9:2]` (hai bit thấp luôn bằng 0 vì lệnh căn hàng theo 4 byte).

### 6.2 Data RAM
Một RAM Logisim gồm 256 từ x 32 bit, được cấu hình với **đọc bất đồng bộ** (đầu ra dữ liệu theo địa chỉ ngay lập tức; cần thiết vì lệnh load phải
trả giá trị ngay trong cùng chu kỳ) và **một tín hiệu write enable** (từ được ghi tại sườn lên của xung nhịp).  Địa chỉ dữ liệu được tách ra:

* `Address[9:2]` - chỉ số từ trong RAM,
* `Address[1:0]` - vị trí byte bên trong từ (little endian: byte 0 là bit 7:0).

Các địa chỉ lớn hơn 1023 sẽ quay vòng (chỉ dùng 10 bit địa chỉ).

### 6.3 Loads: `LoadExtract`
RAM luôn xuất cả từ.  `LoadExtract` lấy phần mà lệnh cần:

| funct3 | lệnh | kết quả |
|---|---|---|
| 000 | `lb` | byte được chọn bởi `Address[1:0]`, mở rộng dấu |
| 100 | `lbu` | cùng byte đó, mở rộng bằng số 0 |
| 001 | `lh` | halfword được chọn bởi `Address[1]`, mở rộng dấu |
| 101 | `lhu` | halfword, mở rộng bằng số 0 |
| 010 | `lw` | cả từ |

Ví dụ: từ `0x8899AABB`, `lb` tại byte 1 cho `0xFFFFFFAA`, `lbu` cho `0x000000AA`, `lh` ở nửa trên cho `0xFFFF8899`.

### 6.4 Stores: `StoreMerge`
RAM chỉ có thể ghi cả từ.  Vì vậy với `sb` / `sh`, mạch đọc từ cũ, thay các byte được ghi rồi ghi lại cả từ
(một thao tác **read-modify-write**, tất cả trong một chu kỳ).  Vì RAM đọc bất đồng bộ nên việc này không cần thêm chu kỳ nào.

Một ROM nhỏ 16 hàng biến `{size, Address[1:0]}` thành bốn **byte enable**:

| size / địa chỉ | byte enable (lane 3..0) |
|---|---|
| byte, offset 0 / 1 / 2 / 3 | 0001 / 0010 / 0100 / 1000 |
| halfword, offset 0-1 / 2-3 | 0011 / 1100 |
| word | 1111 |

Bốn bộ ghép kênh 8 bit chọn theo từng byte lane: được enable -> byte mới, ngược lại giữ byte cũ.  Byte nào của `write_data` rơi vào một lane tùy thuộc kích thước
(với `sb` luôn là `write_data[7:0]`; với `sh` là nửa thấp; với `sw` là byte tương ứng).  Ví dụ: từ cũ `0x11223344`, `write_data = 0xAABBCCDD`:
`sb` tại offset 1 cho `0x1122DD44`; `sh` tại offset 2 cho `0xCCDD3344`; `sw` cho `0xAABBCCDD`.  (Đây là các hàng của `tests/storemerge.vec`.)

Truy cập không căn hàng (ví dụ `lw` tại địa chỉ 2) không được hỗ trợ: phần cứng âm thầm dùng từ đã căn hàng.

---

## 7. The pipelined CPU

### 7.1 Why
Trong CPU single-cycle, chu kỳ xung nhịp phải bao trùm *toàn bộ* đường đi (fetch + decode + ALU + bộ nhớ + write back).  Trong pipeline, các stage được ngăn cách bằng thanh ghi, nên xung nhịp
chỉ cần bao trùm *stage chậm nhất*; tốt nhất là mỗi chu kỳ hoàn thành một lệnh.  (Logisim không mô hình hóa độ trễ cổng, nên bạn thấy cùng số chu kỳ nhưng không thấy xung nhịp nhanh hơn.)

```
cycle:        1    2    3    4    5    6    7    8
instr 1       IF   ID   EX   MEM  WB
instr 2            IF   ID   EX   MEM  WB
instr 3                 IF   ID   EX   MEM  WB
instr 4                      IF   ID   EX   MEM  WB
```

### 7.2 The pipeline registers
Mọi giá trị vẫn còn cần ở một stage sau phải đi cùng lệnh qua các thanh ghi giữa các stage:

| Giữa | Các thanh ghi |
|---|---|
| IF / ID | `pc_id`, `instr_id` |
| ID / EX | `pc_ex`, `rs1_data_ex`, `rs2_data_ex`, `imm_ex`, `rs1_ex`, `rs2_ex`, `rd_ex`, `funct3_ex`, `funct7_ex`, `ctrl_ex` |
| EX / MEM | `alu_result_mem`, `store_data_mem`, `pc_plus4_mem`, `rd_mem`, `funct3_mem`, `ctrl_mem` |
| MEM / WB | `alu_result_wb`, `mem_rdata_wb`, `pc_plus4_wb`, `rd_wb`, `ctrl_wb` |

Các tín hiệu điều khiển được giải mã **một lần**, ở ID.  Chúng đi cùng lệnh dưới dạng một **control word**: 13 bit ở ID/EX (`RegWrite ALUSrc MemWrite MemRead IsBranch ALUOp[2] ASel[2] WBSel[2] IsJAL IsJALR`), 5 bit ở EX/MEM,
3 bit ở MEM/WB (mỗi stage bỏ đi những bit nó không còn cần).  Một splitter đóng gói các bit trước một thanh ghi và một splitter khác tháo ra sau thanh ghi đó.
Một control word toàn số 0 là một **NOP / bubble**: nó không ghi gì cả.

### 7.3 A trick: the register file writes on the falling edge
WB và ID cùng dùng register file trong một chu kỳ.  Nếu một lệnh ở WB ghi `x5` trong khi lệnh đứng sau nó 3 vị trí đọc `x5` ở ID, thì bên đọc phải thấy giá trị **mới**.  Xung nhịp của register file là `CLK_n` (xung nhịp đảo):
nó ghi ở nửa đầu của chu kỳ còn ID đọc ở nửa sau.

### 7.4 Hazards
*Hazard* là tình huống mà việc cứ cho các lệnh chạy xuôi qua các stage sẽ cho kết quả sai.

**Data hazard (đọc sau ghi).**  `add x1,x2,x3` theo sau là `sub x4,x1,x5`: `sub` đọc `x1` ở ID trong khi `add` chưa ghi nó.  Giải pháp: **forwarding**.  Giá trị tồn tại sau stage EX của `add`; nó được
gửi thẳng ngược về đầu vào ALU của lệnh kế tiếp.  `ForwardingUnit` so sánh các thanh ghi nguồn của lệnh ở EX với các thanh ghi đích của hai lệnh phía trước:

| Điều kiện (cho toán hạng A với `rs1_ex`) | `ForwardA` | Nguồn |
|---|---|---|
| `RegWrite_mem` và `rd_mem != 0` và `rd_mem == rs1_ex` | 10 | EX/MEM (`fwd_mem_val`) |
| nếu không, `RegWrite_wb` và `rd_wb != 0` và `rd_wb == rs1_ex` | 01 | MEM/WB (`wb_data`) |
| ngược lại | 00 | giá trị đọc từ register file |

Kết quả trẻ hơn (EX/MEM) được ưu tiên khi cả hai cùng khớp.  Thanh ghi `x0` không bao giờ được forward (`rd != 0`).  Các chi tiết quan trọng:
* `fwd_mem_val` là kết quả ALU, **trừ** `jal` / `jalr`, khi đó kết quả là `PC+4`.
* Cùng giá trị được forward đó là dữ liệu của lệnh store và là đầu vào của phép so sánh nhánh.
* `ForwardA/B` có thể hiện 1 hoặc 2 với những lệnh không dùng `rs1`/`rs2` (các trường đó chỉ là bit immediate); điều này vô hại vì đầu ra của mux không được dùng.

**Load-use hazard.**  `lw x2,0(x0)` theo sau là `addi x3,x2,1`: dữ liệu của lệnh load chỉ có ở cuối MEM, chậm hơn một stage so với yêu cầu của forwarding.  `HazardUnit` phát hiện
`MemRead_ex and rd_ex != 0 and (rd_ex == rs1_id or rd_ex == rs2_id)` và đưa `stall` lên.  Khi đó PC và IF/ID giữ nguyên giá trị trong một chu kỳ (`run = not stall` điều khiển các tín hiệu enable của chúng) và control word đi vào ID/EX
bị thay bằng số 0 (một bubble).  Một chu kỳ sau, dữ liệu có thể được forward từ MEM/WB.

**Control hazard.**  Một nhánh được quyết định ở EX, nhưng hai lệnh nữa đã được nạp.  Nếu nhánh được thực hiện (`pc_src_ex = branch_taken or IsJAL or IsJALR`), `Pipeline`
* nạp địa chỉ đích vào PC,
* thay lệnh đang được nạp bằng 0 (`instr_in = 0`),
* đưa control word đi vào ID/EX về 0 (tín hiệu `bubble` là `stall or pc_src_ex`).

Vì vậy một nhánh / lệnh nhảy được thực hiện tốn **2 chu kỳ**; nhánh không được thực hiện không tốn gì (pipeline "dự đoán không thực hiện").  Một từ lệnh toàn số 0 là NOP an toàn vì opcode 0 không khớp với lớp lệnh nào.

**Không có structural hazard**, vì lệnh và dữ liệu dùng các bộ nhớ riêng và register file có cổng đọc và cổng ghi riêng biệt.

---

## 8. Watching the pipeline: a real trace

`programs/hazards_demo.s`:

```
0000  li   x1, 100
0004  sw   x1, 0(x0)
0008  lw   x2, 0(x0)          # load ...
000c  addi x3, x2, 1          # ... used by the next instruction: load-use stall
0010  add  x4, x3, x2         # forwarding
0014  beq  x4, x4, skip       # taken: flush
0018  addi x5, x0, 1
001c  addi x6, x0, 2
0020  skip: addi x7, x0, 7
0024  halt: j halt
```

Lệnh chạy: `python tools\probe.py --trace RiscVComputer.circ Pipeline programs\hazards_demo.s 12 pc_if pc_id pc_ex stall pc_src_ex ForwardA ForwardB`
Hàng *n* = trạng thái sau chu kỳ xung nhịp *n* (`pc_if`, `pc_id`, `pc_ex` = lệnh ở IF, ID, EX).  Kết quả thật:

```
cycle  pc_if  pc_id  pc_ex  stall pc_src_ex ForwardA ForwardB
    3   000c   0008   0004      0         0        0        2
    4   0010   000c   0008      1         0        0        0     <- lw in EX, addi in ID: stall
    5   0010   000c   000c      0         0        2        0     <- PC and IF/ID held; EX holds the bubble (pc_ex is stale, control = 0)
    6   0014   0010   000c      0         0        1        0     <- addi now in EX: x2 forwarded from MEM/WB (lw is in WB): ForwardA = 1
    7   0018   0014   0010      0         0        2        0     <- add in EX: x3 from EX/MEM (ForwardA = 2); x2 is already in the register file
    8   001c   0018   0014      0         1        2        2     <- beq in EX: x4 forwarded for both operands; taken -> pc_src_ex = 1
    9   0020   001c   0018      0         0        0        0     <- 0018 and 001c are bubbles; fetch continues at skip
```

Cách đọc:
* **Chu kỳ 4**: lệnh `lw` (`pc_ex = 8`) có `MemRead` và lệnh `addi` ở ID (`pc_id = c`) cần `x2` -> `stall = 1`.
* **Chu kỳ 5**: `pc_if` và `pc_id` không di chuyển (được giữ trong một chu kỳ).  Stage EX lúc này chứa **bubble**: chỉ control word của nó bằng 0, nên `pc_ex` vẫn hiện giá trị cũ `c`.
* **Chu kỳ 6**: lệnh `addi` thực sự ở EX; `lw` ở WB, nên `x2` đến từ MEM/WB (`ForwardA = 1`).  Nếu không có stall thì giá trị đã bị cần sớm hơn một chu kỳ, khi nó chưa tồn tại.
* **Chu kỳ 7**: lệnh `add` cần `x3` (kết quả của `addi`, lúc này ở MEM): `ForwardA = 2` (EX/MEM).  `x2` đã được ghi vào register file, nên `ForwardB = 0`.
* **Chu kỳ 8**: `beq` ở EX quyết định *được thực hiện*: `pc_src_ex = 1`.  Chu kỳ kế tiếp việc nạp lệnh ở `0x20` (`skip`); `0x18` và `0x1c` đã được nạp nhưng không bao giờ có hiệu lực: `x5` và `x6` vẫn bằng 0, và kết quả là `x7 = 7`.

---

## 9. Performance

* **CPI** (cycles per instruction - số chu kỳ trên mỗi lệnh) = số chu kỳ / số lệnh.  Single-cycle: đúng bằng 1.  Pipeline: 1 + trung bình số stall và flush.
* **Thời gian thực thi** = số lệnh x CPI x chu kỳ xung nhịp.  Pipeline có CPI cao hơn nhưng chu kỳ xung nhịp ngắn hơn, nên trong một hiện thực thực tế nó nhanh hơn.  Logisim mô phỏng theo "tick", không phải nano giây, nên ở đây chỉ thấy được CPI.

Số chu kỳ đo được (số chu kỳ xung nhịp cho đến khi lần ghi thanh ghi cuối cùng hoàn tất; số lệnh = các lệnh đã thực thi đến lần ghi đó):

| chương trình | số lệnh | single-cycle | pipeline | CPI của pipeline |
|---|---|---|---|---|
| alu | 91 | 91 | 94 | 1.03 |
| mem | 69 | 69 | 73 | 1.06 |
| hazard | 67 | 67 | 82 | 1.22 |
| jump | 27 | 27 | 38 | 1.41 |
| branch | 69 | 69 | 104 | 1.51 |
| fib | 123 | 123 | 181 | 1.47 |
| demo | 39 | 39 | 64 | 1.64 |

(CPU single-cycle cần đúng một chu kỳ cho mỗi lệnh.  Pipeline cần thêm 4 chu kỳ để làm đầy và xả cạn, cộng với các khoản phạt bên dưới; các số liệu được đo bởi `tests/run_cpu_tests.py`, công cụ này chụp lại các thanh ghi sau mỗi chu kỳ.)
Các khoản phạt đo được: forwarding 0, load-use 1, nhánh được thực hiện / jal / jalr 2, nhánh không được thực hiện 0.
Vì sao vòng lặp tốn kém: `demo` có một vòng lặp 3 lệnh với một nhánh được thực hiện mỗi lần lặp: 3 lệnh tốn 5 chu kỳ.
Cách cải thiện: xử lý `jal` ở ID (phạt 1), thêm bộ dự đoán nhánh / branch target buffer, hoặc tính nhánh ở ID kèm forwarding bổ sung.

---

## 10. Writing and running programs

### 10.1 Assembly syntax (`tools/rv.py`)
```
        li   x10, 0            # comments start with # or ;
loop:   add  x10, x10, x11     # labels end with a colon
        addi x11, x11, -1
        bnez x11, loop
        sw   x10, 0(x0)        # offset(register)
halt:   j    halt              # end of program: jump to itself
        .word 0x12345678       # raw data word in the instruction stream
```
* Thanh ghi: `x0..x31` hoặc tên ABI (`zero ra sp t0 a0 s1 ...`).  Số: thập phân, `-5`, hoặc hex `0x1F`.
* **Pseudo instruction** (giả lệnh, được trình hợp dịch khai triển): `nop`, `li rd,imm` (1 hoặc 2 lệnh), `mv`, `not`, `neg`, `seqz`, `snez`, `j`, `jr`, `ret`, `call`, `beqz`, `bnez`, `bltz`, `bgez`, `blez`, `bgtz`, `bgt`, `ble`, `bgtu`, `bleu`.
* `chk rd, value` (dùng trong các bài kiểm thử): `li x30, value` rồi `bne rd, x30, fail`; nó cần nhãn `fail:` và dùng thanh ghi `x30`.
* Chương trình kết thúc bằng một vòng lặp vô tận; các công cụ kiểm thử nhận biết "nhảy về chính nó" là điểm kết thúc.

### 10.2 Commands
```powershell
python tools\rv.py asm prog.s -o prog.hex -l     # assemble, print a listing (address, machine code, source)
python tools\rv.py sim prog.s                    # run on the reference simulator and print the registers
```
`-l` in ra các dòng như `0008: 00b50533  loop:   add  x10, x10, x11`.

### 10.3 Memory map
| Vùng | Địa chỉ | Ghi chú |
|---|---|---|
| ROM lệnh | 0x000 - 0x3FF | 256 từ, chỉ đọc, được địa chỉ hóa bởi `PC[9:2]` |
| RAM dữ liệu | 0x000 - 0x3FF | 256 từ, một bộ nhớ *khác* có cùng địa chỉ; quay vòng sau 1 KiB |
| không có I/O | - | không có thiết bị ánh xạ bộ nhớ (một phần mở rộng tùy chọn) |

Các thanh ghi bắt đầu bằng 0.  Không có khởi tạo con trỏ stack: hãy tự đặt `sp` nếu bạn cần (`li sp, 0x3F0`).

---

## 11. How everything is tested

Nguyên tắc thiết kế: **một oracle độc lập**.  Trình mô phỏng tham chiếu trong `tools/rv.py` được viết tách biệt với các mạch, nên một lỗi phải được mắc hai lần mới có thể lọt qua mà không bị phát hiện.

| Mức | Lệnh | Chứng minh điều gì |
|---|---|---|
| Module | `powershell -File tests\run_tests.ps1` | mỗi khối cho đầu ra đúng với các đầu vào được chọn (Logisim "test vector": một bảng văn bản gồm đầu vào và đầu ra mong đợi) |
| Chương trình | `python tests\run_cpu_tests.py --circuit all` | các chương trình hoàn chỉnh cho cùng thanh ghi và bộ nhớ như trình mô phỏng, trên cả hai CPU |
| Ngẫu nhiên | `python tests\fuzz.py --count 20` | tương tự cho các chương trình ngẫu nhiên gây áp lực lên hazard |

Chi tiết:
* **Tệp test vector** (`tests/*.vec`): dòng đầu = tên chân kèm độ rộng (`rs1_data[32] ALU_Ctrl[4] result[32]`), sau đó mỗi hàng là một bài kiểm thử: `0x00000005 0x7 0x0 0x0000000C`.  Giá trị có `0x` là hex, không có là nhị phân.
* **Chương trình tự kiểm tra** (`tests/programs/*.s`): mỗi kết quả được so với một hằng số tính tay bằng `chk`; cuối chương trình `x31 = 0x600D` ("good") hoặc `0xDEAD`.  Chúng không phụ thuộc vào trình mô phỏng.
* **So sánh toàn bộ trạng thái**: sau khi chạy, bài kiểm thử đọc cả 32 thanh ghi và mọi từ RAM khác 0 từ mạch (qua Java runner) rồi so sánh với trình mô phỏng.
* **Fuzzer**: sinh các chương trình khoảng 70 lệnh chỉ dùng các thanh ghi `x1..x7`, nên gần như mọi lệnh đều phụ thuộc vào một lệnh gần đó.  Nó trộn các phép ALU, mọi kích thước load / store, nhánh tiến, `jal`, `jalr`, `lui`, `auipc`.
  Các chương trình thất bại được lưu trong thư mục tạm để gỡ lỗi.

Những gì các bài kiểm thử **không** bao phủ: thời gian (timing, Logisim không có độ trễ cổng), truy cập không căn hàng, `fence` / `ecall` / `ebreak`, chương trình dài hơn 256 lệnh.

---

## 12. How to extend the design

**Thêm một lệnh R-type** (ví dụ một phép ALU mới): (1) thêm phép toán vào `ALU` và gán cho nó một số `ALUCtrl` (bộ ghép kênh có 16 đầu vào, còn trống 6); (2) dạy `ALUControl` tổ hợp funct3 / funct7;
(3) thêm lệnh vào `tools/rv.py` (`R_OPS`) và vào trình mô phỏng `alu()`; (4) thêm các hàng vào `alu.vec`, `alucontrol.vec` và một chương trình kiểm thử; (5) build lại.

**Thêm một lớp lệnh mới** (opcode mới): thêm một bộ so sánh và cờ trong `MainControl` (`tools/build/blocks.py`), quyết định các tín hiệu, và mở rộng `tests/maincontrol.vec`.

**Thay đổi một mạch được sinh ra**: sửa phần mô tả Python trong `tools/build/` (`blocks.py` cho các khối, `cpus.py` / `pipeline.py` cho hai CPU) và chạy
`python tools\build\build_all.py tools\build\base.circ RiscVComputer.circ`.  Bộ sinh sẽ xác minh kết quả.  Các khối vẽ tay (`ALU`, `InstructionDecode`, `RegisterFile`,
`ImmGen`, `ALUControl`) nằm trong `tools/build/base.circ`: sửa chúng trong Logisim, lưu lại, rồi sao chép tệp vào đó.

**Các ý tưởng, rẻ nhất trước**: xử lý `jal` ở ID; bộ dự đoán nhánh; một UART ánh xạ bộ nhớ để xuất kiểu `printf`; phần mở rộng `M` (bộ nhân là một khối tổ hợp, bộ chia cần một đơn vị nhiều chu kỳ và một tín hiệu stall giống như stall của load-use).

---

## 13. Troubleshooting

| Triệu chứng | Nguyên nhân / cách khắc phục |
|---|---|
| Logisim không khởi động; `UnsupportedClassVersionError ... 65.0` | Java cũ hơn 21.  Cài JDK 21 và dùng `java.exe` của nó. |
| PC hoặc các thanh ghi hiện `xxxxxxxx` / chữ `E` đỏ sau khi nạp | có giá trị chưa xác định: nhấn Ctrl+R (reset simulation); đảm bảo `RESET` bằng 0 khi đang chạy |
| không có gì xảy ra khi tick | bạn chưa dùng *Manual Tick Full Cycle* (Ctrl+F9) và `Auto-Tick Enabled` đang tắt; hoặc công cụ clock không phải là poke tool |
| các thanh ghi không thay đổi | bạn đã mở `RegisterFile` từ cây dự án; hãy dùng kính lúp bên trong `main` / `Pipeline` |
| chương trình chạy nhưng kết quả sai | hợp dịch với `-l` và so sánh với `python tools\rv.py sim`; kiểm tra ROM thật sự chứa chương trình của bạn (*Edit Contents*) |
| ROM trống sau khi *Open* | tệp phải bắt đầu bằng dòng `v2.0 raw`; `rv.py asm` sẽ ghi dòng này |
| `could not find or load main class Run` | chạy `powershell -File tools\compile.ps1` (cần JDK, không chỉ JRE) |
| `no register labelled PC` | tên mạch sai (dùng `main` hoặc `Pipeline`) |
| trình chạy kiểm thử in `circuit run failed` | java đang dùng không phải bản 21: đặt `$env:JAVA = "C:\Program Files\Java\jdk-21.0.12.1\bin\java.exe"` |
| `tests\run_tests.ps1` báo `no result` | cùng nguyên nhân, hoặc tệp mạch có lỗi: mở nó trong Logisim để đọc thông báo |
| tệp được sinh lại có bố cục khác | bộ sinh tìm bố cục chặt nhất; kích thước có thể thay đổi đôi chút khi phông chữ hoặc kích thước thay đổi |

---

## 14. Glossary

| Từ | Ý nghĩa |
|---|---|
| ALU | arithmetic logic unit (đơn vị số học và logic), khối thực hiện tính toán |
| Bubble | một NOP chạy xuyên qua pipeline |
| Control word | các tín hiệu điều khiển được đóng gói đi cùng một lệnh trong pipeline |
| CPI | số chu kỳ trên mỗi lệnh |
| Datapath | các dây và khối mang dữ liệu |
| Flush | hủy các lệnh nằm sau một nhánh được thực hiện |
| Forwarding | gửi kết quả trực tiếp đến đơn vị cần nó, trước khi nó được ghi vào thanh ghi |
| funct3 / funct7 | các bit opcode bổ sung dùng để chọn phép toán bên trong một opcode |
| Harvard | bộ nhớ lệnh và bộ nhớ dữ liệu tách biệt |
| Hazard | tình huống trong đó pipeline sẽ cho kết quả sai |
| Immediate | một hằng số được lưu bên trong lệnh |
| NOP | một lệnh không làm gì cả (`addi x0,x0,0`, hoặc một control word toàn số 0) |
| PC | program counter, địa chỉ của lệnh đang được nạp |
| Probe | một component của Logisim hiển thị một giá trị (hình oval màu vàng) |
| Reference simulator | trình mô phỏng Python `tools/rv.py sim`, dùng làm oracle cho các bài kiểm thử |
| Sign extension | mở rộng một số bằng cách sao chép bit cao nhất của nó |
| Splitter | component của Logisim cắt / gộp các bus |
| Stall | giữ phần đầu của pipeline lại trong một chu kỳ |
| Test vector | một bảng đầu vào và đầu ra mong đợi cho một mạch |
| Tunnel | một đầu dây có tên; cùng tên = được nối với nhau |
