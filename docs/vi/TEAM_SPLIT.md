# Chia việc cho nhóm: ba người, ba phần

> Bản tiếng Việt của docs/TEAM_SPLIT.md.

Mỗi người học sâu một phần, và cả ba cùng nắm phần tổng quan (mục 4), để ai cũng trả lời được khi giáo viên hỏi.

## 1. Cách chia

| Người | Chủ đề | Circuit | Test module (`tests/`) | Chương trình |
|---|---|---|---|---|
| **A** | Front end, giải mã và CPU single-cycle (mức trên cùng) | `main`, InstructionDecode, MainControl, ImmGen, RegisterFile | `maincontrol.vec`, `immgen.vec` | `programs/demo.s`, `tests/programs/alu.s` |
| **B** | Thực thi và bộ nhớ | ALU, ALUControl, BranchUnit, Memory, LoadExtract, StoreMerge | `alu.vec`, `alucontrol.vec`, `branchunit.vec`, `loadextract.vec`, `storemerge.vec` | `alu.s`, `mem.s`, `branch.s` |
| **C** | Pipeline và hazard | `Pipeline`, ForwardingUnit, HazardUnit | `forwardingunit.vec`, `hazardunit.vec` | `hazard.s`, `jump.s`, `fib.s`, `programs/hazards_demo.s` |

Cả 14 circuit đều có người phụ trách: A có 5, B có 6, C có 3 (nhưng `Pipeline` là circuit lớn nhất).

## 2. Mỗi người phải giải thích được gì

### A - front end, giải mã, datapath single-cycle
* Cách cắt lệnh 32-bit thành `opcode rd funct3 rs1 rs2 funct7`, và sáu định dạng R I S B U J.
* Cách `MainControl` biến opcode thành các tín hiệu điều khiển (`RegWrite ALUSrc ASel ALUOp ImmSel WBSel ...`).
* Cách `ImmGen` dựng lại hằng số cho từng định dạng (mở rộng dấu; kiểu U = `imm << 12`).
* Register file: 32 thanh ghi, `x0` luôn bằng 0, hai cổng đọc bất đồng bộ, một cổng ghi.
* Toàn bộ đường đi IF > ID > EX > MEM > WB của `main`, và logic PC kế tiếp (PC+4, đích của branch / JAL, đích của JALR).
* Trình bày: **các bước 1-5 của buổi thuyết trình** (demo single-cycle, tab State, từng tick).
* Đọc: `docs/vi/GUIDE.md` mục 1-5, `docs/vi/COMPONENTS.md` phần của các circuit này.

### B - thực thi và bộ nhớ, kiểm thử
* ALU: mười phép tính chạy song song và được chọn bằng `ALUCtrl`; vì sao `SLT` / `SLTU` khác nhau; lệnh dịch dùng `B[4:0]`.
* `ALUControl`: cách `ALUOp / funct3 / funct7` thành `ALUCtrl` (`funct7[5]` phân biệt ADD/SUB và SRL/SRA).
* `BranchUnit`: sáu điều kiện và cách tạo `branch_taken`.
* Bộ nhớ: RAM đọc bất đồng bộ; `LoadExtract` (lb lh lw lbu lhu); vì sao `sb` / `sh` cần `StoreMerge`, tức đọc-sửa-ghi một từ với tín hiệu cho phép từng byte.
* Cách kiểm thử mọi thứ: test vector của module, chương trình so với bộ mô phỏng tham chiếu, bộ fuzz.
* Trình bày: **các bước 6, 9, 11, 12 của buổi thuyết trình** (nạp chương trình, phần chứng minh, cách viết chương trình, "cho chúng em chương trình bất kỳ").
* Đọc: `docs/vi/GUIDE.md` mục 4, 6, 10, 11; `docs/vi/TOOLS.md`.

### C - pipeline và hazard
* Vì sao dùng pipeline: năm tầng, bốn thanh ghi pipeline (IF/ID, ID/EX, EX/MEM, MEM/WB), từ điều khiển đóng gói.
* Vì sao register file ghi ở sườn xuống (`CLK_n`).
* Forwarding: `ForwardingUnit`, `ForwardA / ForwardB` = `00 register, 01 MEM/WB, 10 EX/MEM`, và chi tiết về JAL/JALR (forward PC+4).
* Stall load-use: `HazardUnit`, vì sao cần một bubble, vì sao PC và IF/ID đứng yên.
* Hazard điều khiển: branch / JAL / JALR được quyết định ở EX, `pc_src_ex`, hai lệnh bị flush, mức phạt 2 chu kỳ.
* Bảng kết quả và vì sao số chu kỳ không giảm (lợi ích là chu kỳ xung nhịp ngắn hơn).
* Trình bày: **các bước 7, 8, 10 của buổi thuyết trình** (mở `Pipeline`, demo hazard với các probe `stall`, `pc_src_ex`, `ForwardA/B`, kết quả).
* Đọc: `docs/vi/GUIDE.md` mục 7-9, `docs/vi/REPORT.md` mục 5 và 8.

## 3. Câu hỏi giáo viên có thể hỏi

**A**
1. CPU biết lệnh thuộc định dạng nào bằng cách nào?  (opcode quyết định; `MainControl`, `ImmSel`)
2. Vì sao `x0` luôn bằng 0?  (register file nạp hằng số 0 cho `x0`; ghi vào nó bị bỏ qua)
3. `lui` làm gì trong datapath này?  (`ASel = 10` chọn số 0, B = hằng số, ALU cộng)
4. Đích của JALR được tính thế nào?  (`(rs1 + imm)` với bit 0 bị xóa)

**B**
1. ALU chọn kết quả như thế nào?  (tính mọi kết quả, một multiplexer chọn theo `ALUCtrl`)
2. Lưu một byte vào RAM theo từ như thế nào?  (đọc cả từ, thay một làn byte, ghi lại cả từ)
3. `blt` và `bltu` khác nhau ra sao?  (bộ so sánh có dấu và không dấu trong `BranchUnit`)
4. Làm sao biết CPU đúng?  (106 hàng test module, 7 chương trình so với bộ mô phỏng tham chiếu, chương trình ngẫu nhiên)

**C**
1. Hazard là gì và xử lý những loại nào?  (dữ liệu: forwarding + stall load-use; điều khiển: flush)
2. Vì sao load không forward được như kết quả ALU?  (dữ liệu chỉ có ở cuối tầng MEM)
3. Branch được rẽ tốn bao nhiêu?  (2 chu kỳ; không rẽ thì không tốn gì)
4. Vì sao bảng của các bạn cho thấy pipeline không nhanh hơn?  (mô phỏng không có độ trễ cổng; lợi ích là chu kỳ xung nhịp ngắn hơn)

## 4. Cả ba cùng nắm (họp chung 30 phút)

* Tổng quan kiến trúc: `docs/vi/REPORT.md` mục 2 và hai hình mức trên cùng `docs/img/main.png`, `docs/img/Pipeline.png`.
* Các lệnh trong `commands.txt` và bước kiểm tra trước buổi trình bày `tools\presentation_check.ps1`.
* Một buổi tập đầy đủ theo `docs/vi/PRESENTATION.md`, mỗi người trình bày các bước của mình (A: 1-5, B: 6, 9, 11, 12, C: 7, 8, 10).
