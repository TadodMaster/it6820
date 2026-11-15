# Kịch bản quay video demo (khoảng 13 phút)

Mỗi cảnh gồm: **Màn hình** (đang mở gì), **Chuột** (chỉ đâu, bấm gì, di chuột thế nào), **Lời nói** (đọc nguyên văn hoặc nói lại bằng lời của em), **Phải thấy** (để biết đang đúng; nếu khác, quay lại cảnh đó).

Bố cục video:
- **Mạch `main` (single-cycle): chỉ demo một lần**, với chương trình `demo.s` đã có sẵn trong ROM. Không nạp chương trình thứ hai.
- **Mạch `Pipeline`: chỉ trỏ và mô tả nhiều hơn**, nạp `hazards_demo.hex` **một lần duy nhất** ở mạch này để thấy forwarding, stall, flush.

Vị trí chân `RESET`, `PAUSE`, `DONE` và hàng probe có thể hơi khác trên máy em: lần quay thử đầu tiên hãy nhìn và chỉnh lại câu "chỉ vào".

---

## 0. Chuẩn bị trước khi bấm quay

1. Bật chế độ **Không làm phiền** (Win+N), đóng Teams / Zalo / mail. Video không được lộ thông báo.
2. Chạy kiểm tra: `powershell -ExecutionPolicy Bypass -File tools\presentation_check.ps1 -Quick`, phải thấy `READY`.
3. Độ phân giải màn hình 1920x1080, thu phóng (scale) 100%. Phóng to chữ của Logisim nếu chữ nhỏ.
4. Mở sẵn 3 thứ, xếp theo thứ tự:
   - Logisim: `java -jar .\logisim-evolution-4.1.0-all.jar .\RiscVComputer.circ` (mạch `main`, ROM đang chứa `demo.s`).
   - Terminal ở `D:\hust\logisim` (chữ to).
   - Trình duyệt: `D:\hust\logisim\docs\web\index.html`.
5. Phần mềm quay: **OBS Studio** (nguồn "Window Capture" cho Logisim và trình duyệt, tránh quay cả màn hình) hoặc **Win+Alt+R** của Xbox Game Bar. Bật micro, nói thử 10 giây rồi nghe lại.
6. Mẹo chuột: di **chậm**, dừng 1 giây trên chỗ cần chỉ rồi mới nói; vẽ một vòng tròn nhỏ quanh vùng muốn nhấn mạnh; với một đường dây, **rê chuột dọc theo đường đó** từ nơi bắt đầu đến nơi kết thúc khi nói "dữ liệu đi từ... đến...". Không rê chuột lung tung khi đang nói.
7. Trong Logisim: bấm vào vùng trống của mạch (để Logisim nhận phím), nhấn **Ctrl+R**, mở tab **State** ở góc dưới bên trái của cột trái để thấy `PC` và `x0..x31`.
8. Quay thử cả phần Pipeline một lần trước, vì phần này cần nhiều thao tác chỉ chuột nhất.

Nếu nói vấp: cứ im một nhịp rồi nói lại câu đó; sau cắt bỏ đoạn vấp khi dựng. Nên quay từng cảnh một file riêng.

---

## PHẦN A - MẠCH `main` (SINGLE-CYCLE), DEMO MỘT LẦN

## Cảnh 1 - Giới thiệu (30 giây)

- **Màn hình:** Logisim, mạch `main`, cột trái đang ở tab **Design** (cây các mạch).
- **Chuột:** rê từ trên xuống dưới cây mạch, dừng ở `main`, rồi dừng ở `Pipeline`, rồi quét chậm qua các mạch con (`ALU`, `RegisterFile`, `MainControl`...).
- **Lời nói:** "Chào thầy, nhóm em làm một máy tính RISC-V 32-bit trên Logisim Evolution. Có hai CPU: `main` là bản single-cycle, `Pipeline` là bản pipeline 5 tầng. Hai CPU dùng chung các khối con như ALU, thanh ghi, bộ điều khiển."
- **Phải thấy:** 14 mạch trong cây.

## Cảnh 2 - Luồng dữ liệu của single-cycle (1,5 phút)

- **Màn hình:** mạch `main`, thấy cả mạch (nếu chưa vừa màn hình thì cuộn cho thấy từ trái sang phải).
- **Chuột:** đi theo luồng dữ liệu từ trái sang phải, dừng 1 giây ở mỗi khối:
  1. Thanh ghi **PC** (góc trái trên), rồi rê sang khối **ROM** bên cạnh.
  2. Khối **InstructionDecode** rồi **MainControl** (cột giữa, phía trên), rồi **ImmGen** và **RegisterFile**.
  3. Hai bộ chọn toán hạng, **ALUControl**, **ALU** và **BranchUnit** (cột giữa bên phải).
  4. Khối **Memory** (phía trên bên phải) và bộ chọn **WBSel** (cuối cùng bên phải).
  5. Cuối cùng quay lại **PC**, chỉ vào bộ chọn **next_pc** (phía dưới) để nói về vòng lặp.
- **Lời nói:** "Thanh ghi PC cho biết địa chỉ lệnh, đưa vào ROM để lấy câu lệnh 32 bit. Câu lệnh đi vào InstructionDecode để tách các trường, opcode đưa vào MainControl để tạo tín hiệu điều khiển. Hai thanh ghi nguồn đọc từ RegisterFile, ImmGen tạo số tức thời. ALU tính toán, BranchUnit quyết định rẽ nhánh. Lệnh load và store đi qua Memory. Cuối cùng một bộ chọn quyết định ghi kết quả ALU, dữ liệu từ bộ nhớ hay PC cộng 4 vào thanh ghi đích, và PC nhận giá trị mới. Tất cả diễn ra trong một chu kỳ xung nhịp."

## Cảnh 3 - Chương trình mẫu (40 giây)

- **Màn hình:** mạch `main`; sau đó mở `programs\demo.s` trong trình soạn thảo (hoặc terminal `type programs\demo.s`).
- **Chuột:** trong mạch `main`, chỉ vào khối **ROM** rồi sang **PC**. Sau đó chuyển sang cửa sổ `demo.s`, rê chuột theo từng dòng lệnh từ trên xuống dưới.
- **Lời nói:** "Chương trình mẫu cộng 10 cộng 9 xuống tới 1, lưu kết quả vào bộ nhớ, đọc lại, và gọi một hàm nhân đôi. Kết quả mong đợi là 55."

## Cảnh 4 - Chạy từng bước, giải thích từng lệnh và giá trị thay đổi (5 phút)

**Chuẩn bị:** Logisim, mạch `main`, tab **State** mở (thấy `PC`, `x1`, `x10`, `x11`, `x12`, `x13`, `x14`). Bấm vào vùng trống của mạch, nhấn **Ctrl+R** (hoặc menu **Simulate > Reset Simulation**). Mọi thanh ghi bằng 0, PC = 0.

**Cách bấm:** mỗi lần nhấn **Ctrl+F9** (hoặc menu **Simulate > Manual Tick Full Cycle**) là **một chu kỳ = một lệnh**. Với mỗi lệnh: **nói trước lệnh sắp chạy, bấm, rồi chỉ vào giá trị vừa đổi**. Cột "PC" dưới đây ghi PC **trước** khi bấm và PC **sau** khi bấm.

**Chương trình (để đối chiếu):**

| Địa chỉ | Lệnh | Ý nghĩa |
|---|---|---|
| 0x00 | `li x10, 0` | x10 = 0 (tổng) |
| 0x04 | `li x11, 10` | x11 = 10 (biến đếm) |
| 0x08 | `add x10, x10, x11` | x10 = x10 + x11 |
| 0x0c | `addi x11, x11, -1` | x11 = x11 - 1 |
| 0x10 | `bnez x11, loop` | nếu x11 khác 0 thì nhảy về 0x08 |
| 0x14 | `sw x10, 0(x0)` | ghi x10 vào bộ nhớ địa chỉ 0 |
| 0x18 | `lw x12, 0(x0)` | đọc lại vào x12 |
| 0x1c | `jal x1, double` | gọi hàm, x1 = địa chỉ trả về |
| 0x20 | `sub x13, x12, x10` | x13 = x12 - x10 |
| 0x24 | `slti x14, x13, 100` | x14 = 1 nếu x13 < 100 |
| 0x28 | `j halt` | lặp mãi (dừng) |
| 0x2c | `add x12, x12, x12` | hàm `double`: nhân đôi x12 |
| 0x30 | `ret` | quay về địa chỉ trong x1 |

### 4a. Ba lệnh đầu: khởi tạo (tick 1 đến 3)

| Tick | PC | Lệnh | Giá trị thay đổi | Chuột chỉ vào | Lời nói |
|---|---|---|---|---|---|
| **1** | 0x00 -> 0x04 | `li x10, 0` | **Không đổi giá trị nào** (x10 vốn bằng 0). Chỉ PC tăng 0x00 -> 0x04 | ô **PC** trong State; probe `instr` (= `0x00000513`) | "Lệnh đầu tiên gán x10 bằng 0. Giá trị đã bằng 0 sẵn nên không thấy gì đổi, chỉ có PC tăng thêm 4." |
| **2** | 0x04 -> 0x08 | `li x11, 10` | **x11: 0x00 -> 0x0a** | ô **x11**; probe `imm` (= `0x0000000a`), `wb_data` (= `0x0000000a`) | "Lệnh này gán x11 bằng 10. Số 10 là hằng số tức thời từ ImmGen đi qua ALU rồi ghi vào x11. x11 sẽ là biến đếm của vòng lặp." |
| **3** | 0x08 -> 0x0c | `add x10, x10, x11` | **x10: 0x00 -> 0x0a** | ô **x10**; probe `rs1_data` (= 0), `rs2_data` (= 0x0a), `alu_result` (= 0x0a) | "Vòng lặp bắt đầu. ALU cộng x10 (0) với x11 (10) ra 10 và ghi lại vào x10. Tổng mới là 10." |

### 4b. Một vòng lặp đầy đủ (tick 4 đến 6) - giải thích kỹ vì nó lặp 10 lần

| Tick | PC | Lệnh | Giá trị thay đổi | Chuột chỉ vào | Lời nói |
|---|---|---|---|---|---|
| **4** | 0x0c -> 0x10 | `addi x11, x11, -1` | **x11: 0x0a -> 0x09** | ô **x11**; probe `ALUSrc` (= 1: toán hạng B là hằng số), `imm` (= `0xffffffff`, tức -1) | "Giảm biến đếm đi 1. Lần này ALU cộng x11 với hằng số -1, nên ALUSrc bằng 1." |
| **5** | 0x10 -> **0x08** | `bnez x11, loop` | **Không có thanh ghi nào đổi.** **PC nhảy lùi về 0x08** | ô **PC** (từ 0x10 về 0x08); probe `branch_taken` (= **1**), `next_pc` (= `0x00000008`) | "Lệnh rẽ nhánh: x11 đang bằng 9, khác 0, nên điều kiện đúng. branch_taken bằng 1, PC không cộng 4 mà nhảy về đầu vòng lặp, địa chỉ 0x08." |
| **6** | 0x08 -> 0x0c | `add x10, x10, x11` | **x10: 0x0a -> 0x13** (10 + 9 = 19) | ô **x10**; probe `alu_result` (= `0x13`) | "Vòng lặp thứ hai: 10 cộng 9 bằng 19, tức 0x13." |

Mỗi vòng lặp luôn là **3 lệnh** theo đúng thứ tự: `add` (x10 tăng), `addi` (x11 giảm 1), `bnez` (PC nhảy về 0x08). Sau tick 6, cứ bấm thêm 3 tick là sang một vòng mới.

### 4c. Các vòng lặp còn lại (bấm nhanh, chỉ đọc giá trị)

Giá trị phải thấy ngay sau tick `add` của vòng đó và sau tick `addi` kế tiếp:

| Vòng | Tick `add` | x10 sau `add` | Tick `addi` | x11 sau `addi` |
|---|---|---|---|---|
| 1 | 3 | 0x0a (10) | 4 | 0x09 (9) |
| 2 | 6 | 0x13 (19) | 7 | 0x08 (8) |
| 3 | 9 | 0x1b (27) | 10 | 0x07 (7) |
| 4 | 12 | **0x22 (34)** | 13 | 0x06 (6) |
| 5 | 15 | 0x28 (40) | 16 | 0x05 (5) |
| 6 | 18 | 0x2d (45) | 19 | 0x04 (4) |
| 7 | 21 | 0x31 (49) | 22 | 0x03 (3) |
| 8 | 24 | 0x34 (52) | 25 | 0x02 (2) |
| 9 | 27 | 0x36 (54) | 28 | 0x01 (1) |
| 10 | 30 | **0x37 (55)** | 31 | **0x00 (0)** |

- **Gợi ý khi quay:** bấm chậm đúng 3 vòng đầu (tick 3 đến 12) và dừng ở tick 12 để chỉ **x10 = 0x22**. Sau đó có thể bấm nhanh qua các vòng 5 đến 9, nói: "Vòng lặp cứ thế, x10 cộng dồn, x11 giảm dần."
- **Tick 31:** `addi` làm **x11 = 0x00**. Chỉ vào x11: "Biến đếm về 0."
- **Tick 32:** `bnez` lần cuối: x11 bằng 0 nên **không nhảy**. Chỉ vào probe `branch_taken` (= **0**) và PC: **0x10 -> 0x14** (đi tiếp xuống, không quay lại 0x08). Nói: "Lần này điều kiện sai, branch_taken bằng 0, PC chỉ cộng 4 và thoát khỏi vòng lặp. x10 đã là 55, tức 0x37."

### 4d. Ghi và đọc bộ nhớ (tick 33 đến 34)

| Tick | PC | Lệnh | Giá trị thay đổi | Chuột chỉ vào | Lời nói |
|---|---|---|---|---|---|
| **33** | 0x14 -> 0x18 | `sw x10, 0(x0)` | **Không thanh ghi nào đổi.** **Bộ nhớ RAM tại địa chỉ 0 chứa 0x37** | probe `MemWrite` (= **1**), `RegWrite` (= **0**); khối **Memory** | "Lệnh store ghi x10 (55) vào bộ nhớ địa chỉ 0. MemWrite bằng 1, RegWrite bằng 0 vì lệnh này không ghi thanh ghi nào." |
| **34** | 0x18 -> 0x1c | `lw x12, 0(x0)` | **x12: 0x00 -> 0x37** | ô **x12**; probe `mem_rdata` (= `0x37`), `WBSel` (= **01**: lấy từ bộ nhớ), `wb_data` (= `0x37`) | "Lệnh load đọc lại giá trị vừa ghi. WBSel bằng 01 nên dữ liệu ghi vào x12 lấy từ bộ nhớ chứ không phải từ ALU. x12 bằng 55." |

### 4e. Gọi hàm và quay về (tick 35 đến 37)

| Tick | PC | Lệnh | Giá trị thay đổi | Chuột chỉ vào | Lời nói |
|---|---|---|---|---|---|
| **35** | 0x1c -> **0x2c** | `jal x1, double` | **x1: 0x00 -> 0x20** (địa chỉ trả về); **PC nhảy tới 0x2c** | ô **x1** và **PC**; probe `WBSel` (= **10**: PC+4), `next_pc` (= `0x2c`) | "Lệnh jal gọi hàm: PC nhảy tới hàm double ở 0x2c, đồng thời lưu địa chỉ lệnh kế tiếp, 0x20, vào x1 để biết đường quay về. WBSel bằng 10 nghĩa là giá trị ghi vào x1 là PC cộng 4." |
| **36** | 0x2c -> 0x30 | `add x12, x12, x12` | **x12: 0x37 -> 0x6e** (55 + 55 = 110) | ô **x12**; probe `rs1_data` = `rs2_data` = `0x37`, `alu_result` = `0x6e` | "Trong hàm double, x12 cộng với chính nó: 55 nhân đôi bằng 110, tức 0x6e." |
| **37** | 0x30 -> **0x20** | `ret` | **Không thanh ghi nào đổi giá trị thật** (ret ghi vào x0 nên bị bỏ qua). **PC nhảy về 0x20** | ô **PC** (0x30 về 0x20); probe `next_pc` (= `0x20`) | "ret là jalr: PC lấy giá trị đã lưu trong x1, là 0x20, nên quay về ngay sau lệnh gọi." |

### 4f. Hai lệnh cuối và dừng (tick 38 đến 39)

| Tick | PC | Lệnh | Giá trị thay đổi | Chuột chỉ vào | Lời nói |
|---|---|---|---|---|---|
| **38** | 0x20 -> 0x24 | `sub x13, x12, x10` | **x13: 0x00 -> 0x37** (110 - 55 = 55) | ô **x13**; probe `alu_result` (= `0x37`) | "Trừ x12 cho x10: 110 trừ 55 bằng 55, tức 0x37." |
| **39** | 0x24 -> **0x28** | `slti x14, x13, 100` | **x14: 0x00 -> 0x01** (55 nhỏ hơn 100 nên bằng 1) | ô **x14**; probe `alu_result` (= `0x1`) | "So sánh: x13 bằng 55 nhỏ hơn 100 nên x14 bằng 1." |

Sau tick 39, PC dừng ở 0x28 là lệnh `j halt` (nhảy về chính nó). Nếu bấm tiếp thì PC vẫn là 0x28, không có gì đổi nữa.

**Bảng kết quả cuối để chỉ vào (sau 39 tick):**

| Thanh ghi / ô nhớ | Giá trị | Ý nghĩa |
|---|---|---|
| PC | 0x28 | đứng ở lệnh `halt` |
| x10 | 0x37 (55) | tổng 1 + 2 + ... + 10 |
| x11 | 0x00 | biến đếm đã về 0 |
| x12 | 0x6e (110) | 55 nhân đôi bởi hàm `double` |
| x13 | 0x37 (55) | x12 - x10 |
| x14 | 0x01 | 55 < 100 |
| x1 | 0x20 | địa chỉ trả về của `jal` |
| RAM[0] | 0x37 | giá trị `sw` đã ghi |

### 4g. Chạy một lần bấm (tổng kết, 1 phút)

- **Chuột:** bấm vùng trống, nhấn **Ctrl+R** để đưa mọi thứ về 0. Chỉ vào chân **DONE** (đang là 0). Mở menu **Simulate** ở thanh trên cùng, bấm **Auto-Tick Enabled** (hoặc **Ctrl+K**). Giữ chuột yên trên tab State, rồi chuyển sang chân **DONE** khi nó lên 1.
- **Lời nói:** "Em chỉ bật một lần, chương trình tự chạy lại toàn bộ 39 lệnh vừa rồi. Mạch có cổng chặn xung nhịp: khi gặp lệnh dừng, nó tự tắt clock và chân DONE lên 1. Chân PAUSE dùng để tạm dừng giữa chừng."
- **Phải thấy:** đúng bảng kết quả cuối ở trên, `DONE = 1`.
- Sau khi xong, vào lại **Simulate > Auto-Tick Enabled** để **tắt** (bỏ dấu tích).
- Chốt: "Vậy CPU single-cycle chạy đúng chương trình mẫu." **Không nạp thêm chương trình nào ở mạch `main`.**

---

## PHẦN B - MẠCH `Pipeline`, CHỈ TRỎ VÀ MÔ TẢ NHIỀU

## Cảnh 5 - Chuẩn bị mạch Pipeline và nạp chương trình (1 phút)

- **Màn hình:** bấm mạch **`Pipeline`** trong cây bên trái.
- **Chuột:** chuột phải vào khối **ROM** của Pipeline > **Load Image...** > gõ `D:\hust\logisim\programs\hazards_demo.hex` > Enter. Bấm vùng trống, nhấn **Ctrl+R**.
- **Lời nói:** "Bây giờ em sang CPU pipeline. Em nạp chương trình `hazards_demo` qua ROM: chương trình này cố ý có các tình huống làm pipeline phải xử lý đặc biệt."
- Chuột chỉ nhanh vào ROM, rồi mở `programs\hazards_demo.s` cho thầy thấy vài dòng đầu (một lệnh load rồi dùng ngay thanh ghi đó, và một lệnh rẽ nhánh). Nói: "Lệnh `lw` rồi lệnh dùng kết quả của nó ngay là tình huống stall, còn lệnh rẽ nhánh là tình huống flush."

## Cảnh 6 - Chỉ cấu trúc pipeline trước khi chạy (2 phút)

- **Màn hình:** mạch `Pipeline`, thấy cả mạch.
- **Chuột:** đi từ trái sang phải, mỗi mục dừng 1-2 giây, **vẽ một vòng quanh vùng** rồi nói:

| Chỉ vào | Cách chỉ | Lời nói |
|---|---|---|
| Năm tiêu đề tầng **IF, ID, EX, MEM, WB** phía trên | rê chuột dọc theo hàng tiêu đề từ trái sang phải | "Mạch chia thành năm tầng. Mỗi lệnh đi qua cả năm tầng, mỗi tầng một chu kỳ, nên năm lệnh chạy chồng nhau." |
| **PC**, bộ cộng **PC+4** và **ROM** trong vùng IF | khoanh nhóm này | "Tầng IF nạp lệnh từ ROM tại PC." |
| Thanh ghi **IF/ID** (giữa IF và ID) | chỉ vào hộp, rồi đưa chuột về hai phía của nó | "Giữa các tầng là thanh ghi pipeline. IF/ID giữ lệnh vừa nạp để chuyển sang tầng giải mã ở chu kỳ sau." |
| **InstructionDecode, MainControl, ImmGen, RegisterFile** (vùng ID) | quét theo cột từ trên xuống | "Tầng ID giải mã lệnh, tạo tín hiệu điều khiển, sinh số tức thời và đọc hai thanh ghi nguồn." |
| Thanh ghi **ID/EX**, **EX/MEM**, **MEM/WB** | chỉ lần lượt từng hộp | "Cả ba thanh ghi này mang theo dữ liệu và tín hiệu điều khiển của từng lệnh, để mỗi lệnh luôn đi cùng dữ liệu của nó." |
| **ALU**, **BranchUnit** (vùng EX) | khoanh ALU rồi BranchUnit | "Tầng EX tính toán và quyết định có rẽ nhánh không." |
| **Memory** (vùng MEM) và bộ chọn ghi lại (WB) | rê từ Memory sang bộ chọn WBSel | "MEM đọc ghi bộ nhớ, WB chọn kết quả ghi vào thanh ghi." |
| **ForwardingUnit** và hai bộ chọn trước ALU | khoanh khối rồi rê chuột theo đường từ EX/MEM và MEM/WB quay về đầu vào ALU | "Đây là bộ chuyển tắt: khi lệnh sau cần kết quả mà lệnh trước chưa kịp ghi, nó lấy thẳng từ EX/MEM hoặc MEM/WB đưa vào ALU." |
| **HazardUnit** | khoanh khối, rồi rê chuột tới PC và IF/ID | "HazardUnit phát hiện xung đột phải dừng. Nó điều khiển PC và IF/ID đứng yên, và chèn bubble vào EX." |
| Chân **DONE** và **PAUSE** | chỉ vào từng chân | "Giống single-cycle, mạch tự dừng khi gặp lệnh dừng." |

- Rê chuột xuống **hàng probe** ở cuối mạch và nói: "Các ô này hiện tín hiệu thật: ForwardA, ForwardB, stall, pc_src_ex... để thầy thấy khi nào có sự kiện."

## Cảnh 7 - Chạy từng tick, chỉ trỏ từng sự kiện (4 phút, cảnh quan trọng nhất)

Mỗi lần bấm **Ctrl+F9** là một tick. Với từng tick, **nói trước một câu rồi mới bấm**, sau đó chỉ vào đúng chỗ.

**Tick 1 đến 2: các lệnh đi vào pipeline**
- **Chuột:** bấm Ctrl+F9; chỉ vào **PC** (giá trị tăng 4), rồi vào **IF/ID** (giá trị lệnh vừa nạp, hiện trong hộp). Bấm tiếp.
- **Lời nói:** "Mỗi tick, PC tăng 4 và lệnh mới đi vào tầng IF. Lệnh cũ đã tiến sang tầng ID, thấy ở thanh ghi IF/ID. Cứ mỗi tick, mỗi lệnh tiến một tầng."

**Tick 3: forwarding**
- **Chuột:** bấm tới tick 3. Chỉ vào probe **`ForwardB`** (phải thấy `10` nhị phân), rồi vào khối **ForwardingUnit**, rồi rê chuột theo đường dữ liệu từ thanh ghi **EX/MEM** quay về bộ chọn trước ALU.
- **Lời nói:** "Tick này lệnh ở EX cần kết quả của lệnh ngay trước nó. Kết quả đó mới tính xong, đang nằm ở EX/MEM, chưa ghi vào thanh ghi. ForwardB bằng 10 nghĩa là toán hạng B lấy thẳng từ EX/MEM thay vì từ RegisterFile. Nhờ vậy không mất chu kỳ nào."

**Tick 4: stall**
- **Chuột:** bấm tới tick 4. Chỉ vào probe **`stall`** (phải thấy `1`), rồi vào khối **HazardUnit**, rồi lần lượt vào **PC** và **IF/ID**. Bấm thêm **một tick (tick 5)** và chỉ vào **PC**: giá trị **giữ nguyên 0x10**.
- **Lời nói:** "Tick 4 là trường hợp load rồi dùng ngay. Dữ liệu của lệnh load chỉ có sau tầng MEM, nên lệnh phía sau không thể lấy tắt kịp. HazardUnit đặt stall bằng 1: giữ PC và IF/ID đứng yên một chu kỳ, và chèn một bubble, tức là lệnh rỗng, vào tầng EX. Thầy thấy PC giữ nguyên 0x10 ở tick sau. Mất đúng một chu kỳ, sau đó forwarding chạy được."

**Tick 6 đến 7: chờ đến nhánh**
- **Chuột:** bấm tiếp, chỉ vào **PC** và hộp **ID/EX** để thầy thấy lệnh rẽ nhánh đang tiến dần tới tầng EX.
- **Lời nói:** "Lệnh rẽ nhánh đang tiến tới tầng EX. Phía sau nó, CPU vẫn nạp tiếp các lệnh theo thói quen PC cộng 4."

**Tick 8: flush**
- **Chuột:** bấm tới tick 8. Chỉ vào probe **`pc_src_ex`** (phải thấy `1`), rồi **BranchUnit**, rồi rê chuột theo đường từ khối rẽ nhánh về **PC** ở tầng IF, cuối cùng chỉ vào **IF/ID** và **ID/EX**.
- **Lời nói:** "Tick 8, lệnh rẽ nhánh ở tầng EX quyết định nhảy, pc_src_ex bằng 1. PC nhận địa chỉ đích. Hai lệnh phía sau vừa được nạp nhầm, nên mạch hủy chúng, gọi là flush: chúng biến thành lệnh rỗng và không ghi gì. Mất hai chu kỳ cho mỗi lần rẽ nhánh."

**Kết thúc chương trình**
- **Chuột:** bấm tiếp đến **tick 13**. Chỉ vào chân **DONE** (phải thấy `1`) và mở tab **State** chỉ vào **x5, x6** (phải thấy `0`).
- **Lời nói:** "Chương trình dừng ở tick 13, DONE bằng 1. x5 và x6 bằng 0 vì hai lệnh gán chúng đã bị hủy, đúng như kết quả của single-cycle."
- Nếu muốn thêm một lần chạy liền: **Ctrl+R**, **Ctrl+K**, mạch tự dừng ở tick 13, rồi tắt Ctrl+K.

---

## PHẦN C - CHỨNG MINH VÀ KẾT LUẬN

## Cảnh 8 - Chứng minh đúng bằng bộ tham chiếu (1,5 phút)

- **Màn hình:** terminal ở `D:\hust\logisim`.
- **Chuột:** click vào terminal, gõ `python tools\live_proof.py`, Enter. Khi bảng hiện ra, rê chuột theo 3 cột rồi dừng ở dòng cuối.
- **Lời nói:** "Em viết một bộ mô phỏng tham chiếu độc lập bằng Python. Chương trình chạy thật trên Logisim ở cả hai CPU, rồi so sánh với tham chiếu ở cả 32 thanh ghi và bộ nhớ."
- **Phải thấy:** mọi dòng `OK` và dòng cuối `VERDICT: both CPUs produce exactly the reference result`.
- Nếu còn thời gian: "Em còn kiểm thử 9 module và 7 chương trình trên cả hai CPU, cộng với kiểm thử ngẫu nhiên; tất cả đều đạt."

## Cảnh 9 - Hình ảnh trực quan trên web (1,5 phút)

- **Màn hình:** trình duyệt, `docs\web\index.html`.
- **Chuột:** bấm tab **Pipeline**; ở ô "Chương trình" chọn `hazards_demo.s`; bấm nút **▶ Chạy tự động đến hết**. Trong khi chạy, rê chuột theo thẻ lệnh đang trượt qua các cột IF > ID > EX > MEM > WB. Dừng lại ở: (a) thẻ viền đứt đứng yên (stall), (b) thẻ đỏ chữ X (bị flush), (c) mũi tên xanh cong phía trên (forwarding). Sau đó kéo xuống bảng "Đang làm gì" bên dưới băng chuyền.
- **Lời nói:** "Đây là trang web mô phỏng để dễ nhìn. Mỗi thẻ là một lệnh, mỗi tick thẻ tiến một tầng. Thẻ viền đứt đứng yên là stall, thẻ đỏ là lệnh bị hủy, mũi tên xanh là forwarding. Bảng dưới ghi từng tầng đang làm gì với giá trị thật."
- Rồi bấm tab **Biểu đồ hiệu năng**, chỉ vào cột so sánh số chu kỳ của hai CPU.

## Cảnh 10 - Kết quả và kết luận (40 giây)

- **Màn hình:** bảng kết quả ở tab **Biểu đồ hiệu năng**.
- **Chuột:** chỉ vào hàng `demo`, rồi vào cột CPI.
- **Lời nói:** "Với chương trình demo, single-cycle chạy 39 chu kỳ, pipeline 64 chu kỳ, CPI 1,64. Trong mô phỏng Logisim, cổng không có độ trễ nên pipeline không nhanh hơn; lợi ích thật là chu kỳ xung nhịp ngắn hơn vì mỗi tầng chỉ làm một việc. Cả hai CPU cho kết quả giống hệt bộ tham chiếu. Em xin cảm ơn thầy đã xem."

---

## Sau khi quay

- Nghe lại toàn bộ để chắc không lộ thông báo hay đường dẫn riêng tư.
- Cắt các đoạn chờ hoặc vấp; chèn chữ nổi tên cảnh nếu có thời gian.
- Xuất MP4 1080p. Nếu file lớn, hạ bitrate hoặc tách thành 2 video (phần single-cycle và phần pipeline).
- Chưa kiểm chứng trên màn hình thật của em: phím tắt Logisim và vị trí các khối, chân `DONE`, `PAUSE`, hàng probe, vì vậy hãy chạy thử toàn bộ một lần trước khi quay chính thức.
