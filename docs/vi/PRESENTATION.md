# Hướng dẫn thuyết trình: chuẩn bị và trình diễn, từng bước một

> Bản tiếng Việt của docs/PRESENTATION.md.

Mục tiêu: cho thầy/cô thấy đây là một **máy tính RV32I thật**, nó **chạy các chương trình được nạp vào bộ nhớ lệnh**, nó có **hai phiên bản
(single-cycle và pipeline 5 tầng)**, pipeline **xử lý được hazard**, và nó được **kiểm thử kỹ đến mức có thể chứng minh là chạy đúng**.

Mọi thứ trong hướng dẫn này đều đã được thử trên chính dự án này: tên menu, phím tắt, hộp thoại chọn file và các giá trị mong đợi đều là thật
(Logisim Evolution 4.1.0, Java 21).

| Phần | Nội dung | Thời gian |
|---|---|---|
| [1](#1-bạn-chứng-minh-điều-gì-và-kế-hoạch) | bạn chứng minh điều gì và kế hoạch 12 phút | |
| [2](#2-chuẩn-bị) | một ngày trước / 15 phút trước / 2 phút trước | |
| [3](#3-demo-trực-tiếp-từng-bước-một) | demo, từng cú nhấp chuột, kèm các giá trị cần thấy | 12 phút |
| [4](#4-dàn-ý-các-slide) | 8 slide và lời nói | |
| [5](#5-các-câu-hỏi-thầycô-có-thể-hỏi) | các câu hỏi và câu trả lời ngắn | |
| [6](#6-nếu-có-sự-cố) | sự cố, cách sửa, phương án dự phòng | |
| [7](#7-các-bảng-tham-khảo) | giá trị mong đợi, phím tắt, lệnh | |

---

## 1. Bạn chứng minh điều gì và kế hoạch

**Năm luận điểm và bằng chứng cho từng luận điểm**

| Luận điểm | Bằng chứng bạn trình bày |
|---|---|
| Đây là một máy tính RV32I hoàn chỉnh | ROM chạy một chương trình thật: vòng lặp, bộ nhớ, gọi hàm (`demo.s`); danh sách lệnh trong báo cáo |
| Chương trình được nạp vào bộ nhớ lệnh, không bao giờ sửa register bằng tay | *Load Image...* một file `.hex` do assembler của nhóm tạo ra; register chỉ thay đổi khi thực thi lệnh |
| Hai CPU: single-cycle và pipeline 5 tầng | các circuit `main` và `Pipeline`, cùng các khối, cùng chương trình, cùng kết quả |
| Pipeline giải quyết hazard dữ liệu và hazard điều khiển | `hazards_demo.s`: load-use stall (PC đứng yên ở cùng một địa chỉ trong hai tick), forwarding, và **x5 = x6 = 0** sau một lệnh rẽ nhánh được thực hiện (các lệnh bị flush không có tác dụng gì) |
| Nó chạy đúng | `tools\live_proof.py`: cả hai CPU đều trùng với một trình mô phỏng tham chiếu *độc lập* trên cả 32 register và bộ nhớ; cộng thêm 106 phép kiểm thử module, 7 chương trình, các chương trình ngẫu nhiên |

**Kế hoạch (12 phút, hai người trình bày: một người nói, một người điều khiển máy tính)**

| Phút | Nội dung | Ở đâu |
|---|---|---|
| 0-1 | mục tiêu và kết quả trong một câu, cho xem hình kiến trúc | slide 1-2 |
| 1-4 | CPU single-cycle chạy `demo.s`: từng tick một, register thay đổi trực tiếp | Logisim, circuit `main` |
| 4-5 | nạp chương trình thứ hai từ một file | Logisim, *Load Image* |
| 5-8 | pipeline: các tầng, một stall và một flush với `hazards_demo` | Logisim, circuit `Pipeline` |
| 8-10 | **chứng minh**: terminal cho thấy cả hai CPU trùng với bản tham chiếu; các bài kiểm thử | terminal |
| 10-11 | kết quả, những gì nhóm chưa làm | slide 7-8 |
| 11-12 | hỏi đáp (kể cả: "cho tụi em một chương trình bất kỳ" - phần 3, bước 12) | |

---

## 2. Chuẩn bị

### 2.1 Một ngày trước
- [ ] Máy trình bày có **Java 21 trở lên** (`java -version` hiển thị 21.x) và **Python 3.10+**.  Logisim 4.1.0 không khởi động được trên Java 17.
- [ ] Sao chép toàn bộ thư mục `D:\hust\logisim` sang máy trình bày *và* vào một USB (thư mục chứa file jar, các circuit, các công cụ và các bài kiểm thử).
- [ ] Trên máy đó chạy một lần: `powershell -File tools\compile.ps1` (biên dịch các công cụ Java phụ trợ; cần JDK).
- [ ] Chạy bước kiểm tra trước giờ trình bày (bên dưới).  Mọi dòng phải ghi PASS.
- [ ] Tập dượt toàn bộ demo một lần, có bấm giờ.  Quyết định ai nói, ai điều khiển.
- [ ] Lưu bản dự phòng ra desktop: thư mục `docs\img` (hình của mọi circuit), kết quả của `python tools\live_proof.py > proof.txt`, và một video quay màn hình buổi tập dượt.
- [ ] In hoặc mở sẵn `docs\REPORT.md` (xuất ra PDF) phòng khi thầy/cô hỏi chi tiết.

### 2.2 Mười lăm phút trước
1. Mở **PowerShell** và vào thư mục dự án:
   ```powershell
   cd D:\hust\logisim
   ```
2. Chạy bước kiểm tra trước giờ trình bày (khoảng 1,5 phút; `-Quick` = 30 giây):
   ```powershell
   powershell -ExecutionPolicy Bypass -File tools\presentation_check.ps1
   ```
   Kết quả mong muốn: `READY: everything passed.`  Mọi dòng đều là PASS (Java, các file, nội dung ROM, kiểm thử module, các chương trình trên cả hai CPU, chương trình ngẫu nhiên, live proof).
3. **Tắt thông báo**: Windows `Win+N` > *Do not disturb* (hoặc Focus assist), đóng Teams / Zalo / mail / Telegram.  Một cửa sổ chat bật lên giữa màn hình trong lúc demo rất mất mặt
   và có thể lộ tin nhắn riêng tư.
4. Đóng tất cả cửa sổ Logisim.  Chỉnh màn hình để mọi người đọc được: Windows scaling 125-150 %, cỡ chữ terminal lớn (`Ctrl + mouse wheel` trong Windows Terminal).
5. Mở các thứ sau (cạnh nhau, hoặc trên hai màn hình):
   - Logisim: `java -jar .\logisim-evolution-4.1.0-all.jar .\RiscVComputer.circ`  (mở `main`)
   - một terminal tại `D:\hust\logisim`
   - một trình soạn thảo hiển thị `programs\demo.s` (các chú thích giải thích chương trình)

### 2.3 Hai phút trước: trạng thái xuất phát
- Logisim hiển thị circuit `main`.  Nhấn **Ctrl+R** (Simulate > Reset Simulation): PC và mọi register đều bằng 0.
- Nhấp vào tab **State** (góc dưới bên trái, cạnh *Properties*).  Tab này liệt kê `PC` và `RegisterFile/x0 ... x31` và hiển thị giá trị của chúng trực tiếp.  Kéo cao khung này lên nếu được
  (kéo thanh chia phía trên *Properties | State* lên trên); nếu không thì cuộn.
- Chân `RESET` hiển thị 0 (phải giữ ở 0 trong khi chương trình chạy).
- Terminal đã được xóa sạch (`cls`), đang ở `D:\hust\logisim`.

---

## 3. Demo trực tiếp, từng bước một

Chương trình `programs\demo.s` đã nằm sẵn trong ROM của cả hai CPU.  Nó làm gì (hãy nói điều này trước khi bắt đầu):

> Nó cộng 10 + 9 + ... + 1 trong một vòng lặp (kết quả 55), lưu kết quả vào bộ nhớ, đọc lại, gọi một hàm nhỏ nhân đôi giá trị đó (110), rồi tính thêm vài giá trị nữa.

> Phần giải thích đầy đủ **mọi thứ xảy ra trong demo** (từng lệnh, từng tín hiệu, cả 40 tick, pipeline từng chu kỳ, và bảng giá trị probe sau mỗi tick) nằm trong [DEMO_EXPLAIN.md](DEMO_EXPLAIN.md), mục 2, 4 và 6.  Dưới mạch có các hàng probe (`main` ba hàng: theo dõi, điều khiển, dữ liệu; `Pipeline` ba hàng: theo dõi, đầu vào ID/EX, dữ liệu EX/MEM/WB) và một khối giải thích tiếng Việt (viết tắt, ý nghĩa tín hiệu, các trường hợp, lý do) ở cuối mỗi circuit.  Ngoài ra mỗi linh kiện (splitter, thanh ghi, multiplexer, bộ cộng, cổng, hằng số, ROM/RAM, khối con) có một chú thích tiếng Việt nhỏ ngay bên cạnh, nói nó làm gì ở đúng chỗ đó và vì sao (2-3 dòng, cỡ chữ 10).  Quy tắc đọc màn hình: tab State hiện trạng thái đã hoàn tất; hàng probe hiện lệnh **sắp chạy** (single-cycle) hoặc đang ở từng tầng (pipeline); nói một câu, bấm một tick, chỉ một thứ, chờ hai giây.

### Bước 1 - Giới thiệu dự án (30 giây)
Ở cây bên trái: `main` (single-cycle), `Pipeline`, và các khối (`ALU`, `RegisterFile`, `MainControl`, ...).  "Hai CPU dùng hoàn toàn các khối giống nhau."
Chỉ vào `main`: các tiêu đề **IF, ID, EX, MEM, WB**, xung clock, register PC, ROM chứa chương trình.  "Mỗi dây đi ra từ một khối là một tunnel có tên; cùng tên nghĩa là cùng một dây."

### Bước 2 - Cho xem chương trình trong ROM (30 giây)
Khung ROM trong `main` hiển thị mã máy (`00000513 00a00593 00b50533 ...`).  Chuyển sang trình soạn thảo có `demo.s`: "đây là mã assembly tụi em đã viết; assembler của tụi em đã dịch nó thành những con số này".

### Bước 3 - Reset (10 giây)
**Ctrl+R**.  Tab State: `PC = 00000000`, mọi register bằng 0.

### Bước 4 - Thực thi từng tick (2 phút)
Nhấn **Simulate > Manual Tick Full Cycle** (phím tắt **Ctrl+F9**) một lần = một chu kỳ clock = một lệnh trên CPU single-cycle.  Tab State cập nhật.  Các giá trị mong đợi:

| Sau tick | PC | x10 | x11 | Chuyện gì đã xảy ra |
|---:|---|---|---|---|
| 1 | 0x04 | 0 | 0 | `li x10,0` |
| 2 | 0x08 | 0 | 0x0a | `li x11,10` |
| 3 | 0x0c | **0x0a** | 0x0a | `add x10,x10,x11` đầu tiên: 0 + 10 |
| 4 | 0x10 | 0x0a | 0x09 | `addi x11,x11,-1` |
| 5 | 0x08 | 0x0a | 0x09 | `bnez`: được thực hiện, PC quay lại vòng lặp |
| 6 | 0x0c | **0x13** | 0x09 | lệnh add thứ hai: 10 + 9 = 19 |
| 9 | 0x0c | **0x1b** | 0x08 | 19 + 8 = 27 |
| 12 | 0x0c | **0x22** | 0x07 | 27 + 7 = 34 |

Vừa bấm tick vừa nói: "x10 là tổng đang cộng dồn, x11 là biến đếm. Mỗi tick thực thi đúng một lệnh."  Chỉ vào **hàng theo dõi** ở cuối mạch (các probe màu vàng, mỗi probe có mô tả tiếng Việt phía trên): `PC`, `instr` = lệnh đang được thực thi (ví dụ `00b50533` = `add x10,x10,x11`), `alu_result`, `branch_taken`, `wb_data` = giá trị được ghi vào register (`0000000a`).

### Bước 5 - Chạy đến hết (1 phút)
Nhấn **Ctrl+F9** đến khoảng tick 40 (hoặc giữ phím; hoặc `Simulate > Auto-Tick Enabled`, **Ctrl+K**, rồi tắt đi).  Trạng thái cuối:

| PC | x1 | x10 | x12 | x13 | x14 | từ nhớ 0 |
|---|---|---|---|---|---|---|
| 0x28 (vòng lặp `halt: j halt` cuối cùng) | 0x20 (địa chỉ trả về) | 0x37 = 55 | 0x6e = 110 | 0x37 = 55 | 1 | 0x37 |

Các mốc: tick 34 `lw` đưa 0x37 vào x12; tick 35 `jal` đặt x1 = 0x20 và nhảy vào hàm; tick 36 `double` làm x12 = 0x6e; tick 38 `sub` cho x13 = 0x37; tick 39 `slti` cho x14 = 1.
"55 và 110 là đáp án đúng, và chương trình không hề chạm trực tiếp vào register nào: chỉ có CPU ghi chúng."

### Bước 6 - Nạp một chương trình khác từ file (1 phút)
Bước này cho thấy chương trình thật sự đi qua bộ nhớ lệnh.
1. Trong `main`, nhấp chuột phải vào khung ROM > **Load Image...**
2. Trong hộp thoại chọn file, gõ đường dẫn rồi nhấn Enter:
   `D:\hust\logisim\programs\hazards_demo.hex`
3. ROM bây giờ hiển thị `06400093 00102023 00002103 ...`.  Nhấn **Ctrl+R** (Reset Simulation), rồi nhấn **Ctrl+F9** tám lần.

Mong đợi trên CPU single-cycle sau 8 tick: PC = **0x24**, `x1 = 0x64` (100), `x2 = 0x64`, `x3 = 0x65` (101), `x4 = 0xc9` (201), `x7 = 7`, và **`x5 = x6 = 0`** (hai lệnh này bị bỏ qua do lệnh rẽ nhánh được thực hiện: hãy nói "nhớ điều này nhé").

### Bước 7 - Mở pipeline (30 giây)
Nhấp vào tab **Design**, nhấp đúp vào `Pipeline`.  Circuit này rất rộng (năm tầng và bốn nhóm register).  "Fit to window" (nút **Auto**, góc dưới bên trái) cho thấy toàn bộ nhưng quá nhỏ để đọc: hãy dùng
nút **×½** hoặc **×1** và các thanh cuộn, đi từng tầng, từ trái sang phải: IF, IF/ID, ID, ID/EX, EX, EX/MEM, MEM, MEM/WB, WB (tiêu đề các tầng có trong hình).
Các nhãn màu xanh phía trên các register đặt tên cho chúng (`pc_id`, `instr_id`, `alu_result_mem`, ...) và mỗi khung register hiển thị giá trị của nó.  Tab State liệt kê `PC` và các register `x0..x31` giống như trước.
Mẹo: hình `docs\img\Pipeline.png` trong báo cáo là một slide tổng quan rất tốt.

### Bước 8 - Chạy pipeline và cho xem hazard (2 phút)
`Pipeline` có ROM riêng, chứa `demo.s`.  Nạp chương trình hazard theo cách tương tự (nhấp chuột phải vào ROM của nó, gần phía bên trái của circuit, **Load Image...** > `D:\hust\logisim\programs\hazards_demo.hex`), rồi **Ctrl+R**.
Bấm tick bằng **Ctrl+F9** và quan sát giá trị **PC** trong tab State (đây là địa chỉ fetch).  Hàng theo dõi ở cuối mạch `Pipeline` cho xem trực tiếp cùng thông tin đó: `PC`, `instr_id`, `stall` (bằng 1 ở tick 5), `pc_src_ex` (bằng 1 khi branch được rẽ), `ForwardA` / `ForwardB` (`10` = lấy từ EX/MEM), `alu_result_ex`, `wb_data`:

| Tick | 1 | 2 | 3 | 4 | **5** | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| PC | 04 | 08 | 0c | 10 | **10** | 14 | 18 | 1c | 20 | 24 |

- **Tick 5: PC không nhúc nhích.** Đó chính là **load-use stall**: `lw x2,0(x0)` được theo sau ngay bởi `addi x3,x2,1` cần giá trị vừa đọc; pipeline giữ phần đầu lại một chu kỳ.
- **Tick 6-8**: PC đi tiếp tới `0x14`, `0x18`, `0x1c`: lệnh `beq` tại `0x14` được thực hiện, nhưng hai lệnh nằm sau nó đã được fetch rồi.  Ở tick 9 PC là `0x20` (đích rẽ nhánh; ở đây nó bằng địa chỉ tuần tự kế tiếp, nên chỉ riêng PC không chứng minh được flush).  Bằng chứng của flush là **`x5 = x6 = 0`** ở cuối: hai lệnh nằm sau `beq` đã bị biến thành bubble.
- Giá trị cuối sau khoảng 13 tick: `x1 = 0x64`, `x2 = 0x64`, `x3 = 0x65`, `x4 = 0xc9`, `x7 = 7`, và lại là **`x5 = x6 = 0`**: các lệnh bị flush không làm thay đổi gì cả.
- Forwarding: `x3` và `x4` đúng dù mỗi giá trị phụ thuộc vào lệnh ngay trước nó (giá trị được lấy từ register EX/MEM hoặc MEM/WB, không phải từ register file).
- Sau đó PC cứ quay vòng `0x24, 0x28, 0x2c` trong pipeline: bình thường, lệnh nhảy `halt` flush các lệnh phía sau nó mỗi lần.

"Cùng chương trình, cùng kết quả như CPU single-cycle - nhưng có năm lệnh cùng đang được xử lý một lúc."

### Bước 9 - Chứng minh (2 phút, terminal)
```powershell
python tools\live_proof.py
```
(khoảng 10 giây).  Nó in ra chương trình, rồi **một bảng đặt cạnh nhau gồm trình mô phỏng tham chiếu, CPU single-cycle và pipeline** cho mọi register và mọi từ nhớ, số chu kỳ, và kết luận:

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
Giải thích: "Trình mô phỏng tham chiếu là một chương trình Python riêng, viết độc lập với các circuit.  Nếu các circuit khớp với nó trên cả 32 register, thì chúng tính toán đúng những gì một máy RISC-V phải tính."
Sau đó cho xem bộ kiểm thử (chọn những phần bạn có thời gian; mỗi phần đều in `ALL PASSED`):
```powershell
powershell -File tests\run_tests.ps1                  # 9 module tests, 106 checks (~15 s)
python tests\run_cpu_tests.py --circuit all            # 7 programs on both CPUs (~20 s)
python tests\fuzz.py --count 5                         # 5 random programs on both CPUs (~15 s)
```

### Bước 10 - Kết quả (30 giây)
- Tập lệnh: toàn bộ tập lệnh cơ sở RV32I (R, I, load / store mọi kích thước, cả 6 lệnh rẽ nhánh, `jal`, `jalr`, `lui`, `auipc`).
- CPI của single-cycle = 1; CPI của pipeline = 1.0 với đoạn mã chạy thẳng, +2 chu kỳ cho mỗi lệnh rẽ nhánh được thực hiện, +1 cho mỗi load-use.
- 9 file kiểm thử module (106 phép kiểm tra), 7 chương trình kiểm thử, kiểm thử bằng chương trình ngẫu nhiên (fuzzing), một assembler, một trình mô phỏng tham chiếu.
- Chưa làm (tùy chọn trong đề bài): dự đoán rẽ nhánh, cache, M extension, interrupt, UART, số thực dấu phẩy động.

### Bước 11 - Cho xem cách viết một chương trình (tùy chọn, 1 phút)
```powershell
python tools\rv.py asm programs\demo.s -l -o programs\demo.hex
```
Hiển thị bản liệt kê: địa chỉ, mã máy, mã nguồn.  "Đây là file mà *Load Image* đọc."

### Bước 12 - "Cho tụi em một chương trình bất kỳ" (nếu thầy/cô yêu cầu)
Tạo file `D:\hust\logisim\test1.s`, ví dụ tính 5! :
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
Sau đó chạy **một lệnh**: `python tools\live_proof.py test1.s` - nó dịch chương trình, chạy trên cả hai CPU và trên bản tham chiếu, rồi in kết luận (ở đây `x10 = 0x78` = 120, 76 chu kỳ với single-cycle, 107 với pipeline).
Hoặc nạp `test1.hex` vào ROM ngay tại chỗ: `python tools\rv.py asm test1.s -o test1.hex` rồi *Load Image...*.  (Đừng đề nghị làm việc này nếu chưa tập dượt; nếu ý tưởng của thầy/cô không phù hợp, hãy nói "tụi em có thể thử ngay sau đây".)

---

## 4. Dàn ý các slide

Dùng các hình trong `docs\img\` (`main.png`, `Pipeline.png`, `ALU.png`, `RegisterFile.png`, `MainControl.png`, `Memory.png`, ...).

| # | Tiêu đề | Nội dung | Lời nói |
|---|---|---|---|
| 1 | Mục tiêu | đề bài trong một dòng: máy tính RV32I trong Logisim, single-cycle + pipeline 5 tầng | "Tụi em đã xây dựng và kiểm chứng cả hai." |
| 2 | Kiến trúc | `main.png`; bộ nhớ Harvard; danh sách các khối | "Cùng các khối cho cả hai CPU; các tín hiệu đều có tên." |
| 3 | Tập lệnh | bảng các nhóm lệnh (README), các định dạng lệnh | "Toàn bộ RV32I trừ các lệnh hệ thống." |
| 4 | Datapath single-cycle | năm tầng, bảng điều khiển (`MainControl`) | "Một lệnh mỗi chu kỳ." |
| 5 | Pipeline | `Pipeline.png`; 4 nhóm register; forwarding, stall, flush trong 3 gạch đầu dòng | "Năm lệnh cùng lúc; hazard được giải quyết bằng phần cứng." |
| 6 | Kiểm chứng | 3 mức: kiểm thử module, chương trình, ngẫu nhiên; trình mô phỏng tham chiếu độc lập | "Làm sao tụi em biết nó chạy đúng." |
| 7 | Kết quả | bảng CPI (README); các giá trị trong demo | "55 và 110, trùng với bản tham chiếu." |
| 8 | Giới hạn và hướng phát triển | chưa làm: dự đoán rẽ nhánh, cache, M extension, UART | "Tiếp theo: xử lý jal ở tầng ID, thêm bộ dự đoán." |

Thứ tự trong buổi trình bày: slide 1-3 (2 phút) -> demo trực tiếp bước 1-8 -> slide 6 + bước 9 (chứng minh) -> slide 7-8.

---

## 5. Các câu hỏi thầy/cô có thể hỏi

| Câu hỏi | Trả lời ngắn |
|---|---|
| Làm sao các em biết nó đúng? | Ba mức: 106 phép kiểm tra module do chính Logisim chạy, 7 chương trình và các chương trình ngẫu nhiên được so sánh từng register với một trình mô phỏng tham chiếu được viết riêng, và các chương trình tự kiểm tra có giá trị mong đợi được tính tay (chúng kết thúc với `x31 = 0x600D`). |
| Bản thân trình mô phỏng tham chiếu có đúng không? | Nó tái tạo đúng các mã hóa trong ghi chú thiết kế (`addi x1,x0,5 = 0x00500093`, ...) và các chương trình tự kiểm tra không phụ thuộc vào nó. Nếu cả circuit lẫn trình mô phỏng cùng sai theo một cách, các phép kiểm tra tính tay vẫn sẽ báo lỗi. |
| Các em đã tìm ra những lỗi nào? | Ở các khối đầu tiên: `SLTU` trả về `0xFFFFFFFF` thay vì 1; `SLL` chọn sai mã ALU; JALR / LUI giải mã sai; immediate kiểu U thiếu phép dịch bit; bộ nhớ không bao giờ trả dữ liệu về (RAM là đồng bộ). Tất cả đã được sửa và có kiểm thử bao phủ. |
| Tại sao ở đây pipeline lại không nhanh hơn? | Logisim đếm chu kỳ, không đếm nanosecond.  Pipeline rút ngắn *chu kỳ clock* (mỗi chu kỳ chỉ có một tầng), điều này không được mô phỏng.  Số chu kỳ cao hơn là do phạt 2 chu kỳ cho lệnh rẽ nhánh được thực hiện và 1 chu kỳ stall cho load-use. |
| Forwarding hoạt động thế nào? | `ForwardingUnit` so sánh các register nguồn của lệnh đang ở EX với các register đích của các lệnh ở MEM và WB, rồi chọn giá trị mới hơn đưa vào đầu vào của ALU. |
| Tại sao load-use cần stall? | Dữ liệu đọc ra chỉ có ở cuối MEM, quá muộn một tầng để forward vào EX của lệnh kế tiếp. |
| `x0` là gì? | Một register luôn đọc ra 0; register file liên tục nạp hằng số 0 vào nó. |
| Tại sao tách riêng bộ nhớ lệnh và bộ nhớ dữ liệu? | Tổ chức Harvard: không có structural hazard trong pipeline, đơn giản hơn. |
| Tại sao RAM được đọc bất đồng bộ? | Lệnh load phải trả dữ liệu ngay trong cùng chu kỳ; RAM mặc định của Logisim trả lời chậm một chu kỳ. |
| Chuyện gì xảy ra khi truy cập không căn chỉnh? | Không được hỗ trợ: phần cứng dùng word / halfword đã căn chỉnh. |
| Những lệnh nào còn thiếu? | `fence`, `ecall`, `ebreak`, các lệnh CSR (được coi như no-op), và mọi thứ nằm ngoài tập RV32I cơ sở. |
| Tại sao các em tạo circuit bằng một chương trình? | Phiên bản vẽ tay đầu tiên có những dây chéo dài và các kết nối hở; circuit sinh tự động thì lặp lại được và được kiểm chứng tự động (mọi net đều được kiểm tra sau khi lưu). |
| Các em sẽ cải thiện gì tiếp theo? | Xử lý `jal` ở ID (phạt 1 thay vì 2), một bộ dự đoán rẽ nhánh, một UART, M extension. |
| Tụi em có thể chạy một chương trình khác không? | Có: bước 12; `python tools\live_proof.py yourprogram.s`. |

---

## 6. Nếu có sự cố

| Vấn đề | Cách sửa |
|---|---|
| Logisim không khởi động / báo lỗi về class version | Java cũ hơn 21: cài JDK 21 hoặc chạy với đường dẫn đầy đủ `"C:\Program Files\Java\jdk-21.0.12.1\bin\java.exe" -jar ...` |
| Giá trị hiển thị `x` hoặc `E`, hoặc không có gì thay đổi | **Ctrl+R** (Reset Simulation), đảm bảo `RESET` hiển thị 0, rồi bấm tick lại |
| Bấm tick mà không có gì xảy ra | Dùng menu *Simulate > Manual Tick Full Cycle* một lần (nếu *Auto-Tick Enabled* đang bật, tắt nó bằng Ctrl+K) |
| Tab State chỉ hiển thị vài dòng | cuộn nó, hoặc kéo thanh chia phía trên *Properties \| State* lên trên |
| ROM trống hoặc hiển thị sai chương trình | nhấp chuột phải vào ROM > *Load Image...* > `D:\hust\logisim\programs\demo.hex` > Enter, rồi Ctrl+R |
| Hộp thoại chọn file không nhận đường dẫn | ô Filename đang được focus: gõ đường dẫn đầy đủ với dấu gạch chéo ngược rồi nhấn Enter; hoặc duyệt: thư mục `programs` > file `.hex` |
| Register khác với mong đợi sau khi nạp chương trình khác | Ctrl+R trước khi chạy; các giá trị trong bảng của hướng dẫn này chỉ dành cho `demo.s` và `hazards_demo.s` |
| Logisim bị treo | chờ 10 giây; nếu không thì đóng nó (chọn *Don't save*) và mở lại; chuyển sang cho xem phần chứng minh trong terminal |
| `live_proof.py` thất bại | chạy `powershell -File tools\presentation_check.ps1` để xem bước nào lỗi; kiểm tra `$env:JAVA` |
| Thông báo Windows bật lên | tắt nó đi; lần sau bật Do not disturb |
| Thầy/cô yêu cầu điều không làm được trực tiếp | nói "tụi em có thể cho xem sau"; mở báo cáo (`docs\REPORT.md`) |

**Phương án dự phòng** nếu máy tính hoặc Logisim hỏng hoàn toàn: các hình trong `docs\img\` (mọi circuit), file `proof.txt` đã lưu (kết quả của `live_proof.py`), và video tập dượt của bạn.
Khi đóng Logisim lúc kết thúc, hãy chọn **Don't Save** nếu nó hỏi (vì bạn đã nạp các chương trình khác vào ROM trong lúc demo).

---

## 7. Các bảng tham khảo

### Phím tắt và tên menu (đã kiểm chứng)
| Thao tác | Menu | Phím tắt |
|---|---|---|
| Một chu kỳ clock đầy đủ | Simulate > Manual Tick Full Cycle | **Ctrl+F9** |
| Nửa chu kỳ clock | Simulate > Manual Tick Half Cycle | Ctrl+T |
| Bật / tắt clock chạy liên tục | Simulate > Auto-Tick Enabled | Ctrl+K |
| Reset mô phỏng | Simulate > Reset Simulation | **Ctrl+R** |
| Register trực tiếp | tab **State**, góc dưới bên trái | - |
| Nạp một chương trình | nhấp chuột phải vào ROM > **Load Image...** | - |
| Hiển thị ROM dưới dạng trình soạn hex | nhấp chuột phải vào ROM > Edit Contents... | - |
| Zoom vừa khung / ×½ / ×1 / ×2 | các nút ở góc dưới bên trái | - |

Cũng trong menu Simulate: *Timing diagram* (dạng sóng của các tín hiệu được chọn; không dùng trong hướng dẫn này, hãy thử khi tập dượt nếu bạn muốn xem dạng sóng) và *Test Vector...* (chạy một file test vector).

### Giá trị mong đợi: `demo.s`
Single-cycle, sau N tick (PC trỏ tới lệnh sắp được thực thi): xem bảng ở bước 4; cuối cùng: PC 0x28, x1 0x20, x10 0x37, x12 0x6e, x13 0x37, x14 1, memory[0] 0x37 (đạt được sau 39 tick).
Pipeline: cùng các giá trị cuối sau 64 tick.  Sau đúng 20 tick trên pipeline: PC 0x14, x10 0x1b, x11 0x07.

### Giá trị mong đợi: `hazards_demo.s`
Cuối cùng (cả hai CPU): `x1 = 0x64, x2 = 0x64, x3 = 0x65, x4 = 0xc9, x7 = 7`, mọi register khác bằng 0 (đặc biệt là `x5 = x6 = 0`).  Single-cycle: sau 8 tick (PC 0x24).  Pipeline: sau 13 tick; dãy PC là 04 08 0c 10 **10** 14 18 1c 20 24.

### Lệnh (sao chép và dán)
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
Lệnh cuối cùng in ra vết pipeline theo từng chu kỳ (lệnh nào đang ở IF / ID / EX, `stall`, `pc_src_ex` = flush, các tín hiệu chọn forwarding) dưới dạng bảng: một phương án dự phòng tốt nếu bạn không thể cho xem circuit.
