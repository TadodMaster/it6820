# Components: cấu hình và lý do sử dụng

> Bản tiếng Việt của docs/COMPONENTS.md.

Trang này giải thích từng **loại component của Logisim** được dùng trong dự án: nó là gì, **ta dùng những cài đặt nào và vì sao**, nó xuất hiện ở đâu, và những cái bẫy mà ta đã vấp phải.  Để xem cấu hình chính xác của từng component trong từng circuit, xem [BOM.md](BOM.md) (sinh ra từ file thật).
Để biết các khối phối hợp với nhau thế nào, xem [GUIDE.md](GUIDE.md).

Trong file circuit, các cài đặt được lưu dưới dạng attribute (`<a name="width" val="32"/>`).  Các bảng dưới đây ghi cả **tên trong file** và **tên hiển thị trong bảng attribute của Logisim** (chọn component bằng công cụ mũi tên; các cài đặt hiện ở góc dưới bên trái).
Mọi giá trị "default" đều được đọc trực tiếp từ Logisim 4.1.0.

Mục lục: [0 Cài đặt toàn dự án](#0-cài-đặt-toàn-dự-án) - [1 Trạng thái](#1-trạng-thái-register-ram-rom) - [2 Chọn và định tuyến](#2-chọn-và-định-tuyến-multiplexer-demultiplexer-splitter) -
[3 Số học](#3-số-học-và-so-sánh-adder-subtractor-comparator-shifter-bit-extender) - [4 Cổng logic](#4-cổng-logic) - [5 Đi dây và I/O](#5-đi-dây-và-io-constant-pin-tunnel-probe-clock-text) -
[6 Sub-circuit](#6-sub-circuit) - [7 Quyết định thiết kế](#7-quyết-định-thiết-kế-vì-sao-chọn-cái-này-mà-không-phải-cái-kia) - [8 Công thức](#8-công-thức-tự-dựng-một-component-bằng-tay)

---

## 0. Cài đặt toàn dự án

| Cài đặt | Giá trị | Ở đâu | Vì sao |
|---|---|---|---|
| Phiên bản Logisim | 4.1.0 (Java 21+) | header của file `source="4.1.0"` | phiên bản cả nhóm đã cài |
| Đầu ra của cổng khi không xác định (`gateUndefined`) | `ignore` | Project > Options > Simulation | các đầu vào cổng không nối sẽ bị bỏ qua thay vì tạo ra giá trị lỗi |
| Giới hạn số vòng lặp (`simlimit`) | 1000 | như trên | số bước trước khi Logisim báo "oscillation"; các CPU ổn định với số bước ít hơn nhiều, nên một vòng lặp thật sẽ bị phát hiện nhanh |
| Nhiễu trên độ trễ component (`simrand`) | 0 (tắt) | như trên | mô phỏng phải mang tính xác định để các test lặp lại được |
| Lưới (Grid) | 10 px | cố định bởi Logisim | mọi component và dây phải nằm trên lưới; các phần tử lệch lưới bị *dịch chuyển* khi nạp file và khi đó dây sẽ lệch khỏi pin |
| Font | `Monospaced` | mọi text và label | theo yêu cầu cho tài liệu / demo; áp dụng bởi `tools/build/fonts.py` |
| Clock | một `Clock` cho mỗi CPU, high 1 tick / low 1 tick (mặc định) | `main`, `Pipeline` | một chu kỳ đầy đủ = 2 tick (cạnh lên + cạnh xuống); `Simulate > Manual Tick Full Cycle` (Ctrl+F9) thực hiện cả hai.  Clock được bước bằng tay nên tần số không quan trọng |
| Các thư viện được dùng | Wiring, Gates, Plexers, Arithmetic, Memory, Base | cây dự án | các thư viện khác trong file (I/O, TTL, FP, ...) chỉ là template mặc định của Logisim và không được dùng |
| Độ rộng dữ liệu | 32 bit ở mọi nơi trong datapath; 5 bit cho số hiệu register, 3 cho `funct3`, 7 cho `opcode` / `funct7` | | RV32I |
| Reset | pin `RESET` (mặc định 0) điều khiển đầu vào *clear* của register PC | `main`, `Pipeline` | đưa PC về 0 mà không reset toàn bộ mô phỏng |

---

## 1. Trạng thái: Register, RAM, ROM

### Register
Một register lưu giá trị ở **cạnh lên của clock** khi enable bằng 1.

| Tên trong file | Tên trong GUI | Giá trị dùng | Default | Vì sao |
|---|---|---|---|---|
| `width` | Data Bits | 32 (PC, register file); 5, 3, 7, 13 cho các trường pipeline | 8 | mỗi trường một register, kích thước theo trường (5 = số hiệu register, 3 = `funct3`, 7 = `funct7`, 13 = control word) |
| `trigger` | Trigger | Rising Edge | rising | mọi thay đổi trạng thái diễn ra ở cạnh lên nên mọi thứ cập nhật "cùng lúc" |
| `appearance` | Appearance | `logisim_evolution` | như nhau | vẽ tên pin D, Q, WE, clk, R trên hộp: dễ đọc hơn hộp classic trơn |
| `label` | Label | `PC`, `x0`..`x31`, tên trong pipeline | không có | test runner tìm PC và các register theo label; các label trong pipeline đặt tên cho các register của từng stage |
| `labelvisible` | (hiển thị label) | true cho các register pipeline | false | hiển thị `pc_ex`, `alu_result_mem`, ... phía trên mỗi register trong hình Pipeline |

Các pin: **D** dữ liệu vào, **Q** dữ liệu ra, **WE** enable, **clk**, **R** clear bất đồng bộ.
* WE: nối với hằng số 1 khi register luôn nạp; nối với `run` (= not stall) cho PC và register IF/ID, những register phải *giữ nguyên* trong lúc stall load-use.
* R: chỉ PC dùng (`RESET`).  R không nối được coi là 0 (không clear).
* Register khởi động với giá trị 0.  Do đó các register pipeline bắt đầu là bubble (instruction 0 = NOP).
* Trong pipeline, pin clock của register file nhận **clock đảo** (`CLK_n`), nên các register của nó nạp ở cạnh *xuống* của `CLK`.

Được dùng: PC (1), register file (32 x 32 bit), các register pipeline (23).

### RAM (data memory) - cài đặt tinh tế nhất
| Tên trong file | Tên trong GUI | Giá trị dùng | Default | Vì sao |
|---|---|---|---|---|
| `addrWidth` | Address Bit Width | 8 | 8 | 256 word |
| `dataWidth` | Data Bit Width | 32 | 8 | một word RV32 |
| `asyncread` | Asynchronous read | **true** | false | lệnh load phải trả dữ liệu ngay trong chu kỳ mà địa chỉ được đưa vào.  Với đọc mặc định (đồng bộ), dữ liệu chỉ xuất hiện sau cạnh clock kế tiếp, nên mọi lệnh load trong dự án gốc đều trả về dữ liệu không xác định |
| `enables` | Enables | **line** (Use line enables) | byte | chế độ line có một pin write-enable và một clock; chế độ byte cần một enable cho mỗi byte.  Việc store dưới một word được làm trong `StoreMerge`, đơn giản hơn và test được |
| `databus` | Data bus implementation | separate (mặc định, trong file gọi là `bibus`) | separate | pin data-in / data-out riêng biệt: không có bus hai chiều nên không có xung đột (contention) |
| `type` | Ram type | volatile | volatile | nội dung mất khi reset (ban đầu toàn 0) |
| `trigger` | Trigger | rising | rising | việc ghi diễn ra ở cạnh lên |
| `appearance` | Appearance | `classic` | `logisim_evolution` | ký hiệu classic có kích thước 240 x 154 px; kiểu kia cao 730 px (nó hiển thị nội dung) |

Các pin ở chế độ line: `addr`, `dout` (luôn được enable: chế độ này không có pin OE), `din`, `we`, `clk`.
Vì `dout` luôn bật nên `StoreMerge` có thể đọc word cũ trong khi chuẩn bị word mới.
Dùng một lần, trong `Memory`.

### ROM (instruction memory và một bảng tra)
| Tên trong file | Tên trong GUI | Instruction ROM | Bảng byte-enable | Vì sao |
|---|---|---|---|---|
| `addrWidth` | Address Bit Width | 8 | 4 | 256 word, 16 hàng |
| `dataWidth` | Data Bit Width | 32 | 4 | instruction / bốn bit enable |
| `contents` | Contents | chương trình | `1 2 4 8 3 3 c c f f f f f f f f` | được nạp bởi bước build; thay đổi trong GUI bằng *Edit Contents* |
| `appearance` | Appearance | classic | classic | gọn |

Vì sao dùng ROM cho byte enable: 16 tổ hợp của `{size, address[1:0]}` là một bảng chân trị; ROM 16 hàng là cách ngắn nhất và đúng để viết ra, và nội dung đọc được
(`1 2 4 8` = từng byte đơn, `3 3 c c` = halfword, `f` = word).  Vì sao dùng ROM cho chương trình: instruction memory chỉ đọc và được đọc tổ hợp theo PC.

---

## 2. Chọn và định tuyến: Multiplexer, Demultiplexer, Splitter

### Multiplexer
Một multiplexer sao chép một trong `2^select` đầu vào ra đầu ra.

| Tên trong file | Tên trong GUI | Default | Ghi chú |
|---|---|---|---|
| `select` | Select Bits | 1 | số bit select: số đầu vào = 2^select |
| `width` | Data Bits | 1 | độ rộng của mỗi đầu vào dữ liệu và của đầu ra |
| `enable` | Include Enable? | no | không bao giờ dùng |
| `facing`, `size`, `selloc`, `disabled` | Facing, Gate Size, Select Location, Disabled Output | east, 40, bottom-left, 0 | mặc định |

Pin select nằm ở cạnh dưới, các đầu vào dữ liệu ở bên trái, đánh số từ trên xuống (đầu vào 0 là đầu trên cùng).

| Ở đâu | select / width | Chọn |
|---|---|---|
| Kết quả ALU | 4 / 32 (16 đầu vào, dùng 10) | một trong 10 phép toán theo `ALUCtrl` |
| Cổng đọc của register file (2) | 5 / 32 | register `rs1` / `rs2` |
| Toán hạng A của ALU | 2 / 32 | `rs1`, PC, 0 (theo `ASel`) |
| Toán hạng B của ALU | 1 / 32 | `rs2` hoặc immediate (theo `ALUSrc`) |
| Write-back | 2 / 32 | ALU, memory, PC+4 (theo `WBSel`) |
| Next PC | 1 / 32 (hai cái nối tiếp) | `PC+4` / `pc_target` / `jalr_target` |
| ImmGen | 3 / 32 (8 đầu vào, dùng 5) | immediate I, S, B, U, J |
| ALUControl | 3 / 4 (nhiều cái) | giải mã `funct3` thành mã `ALUCtrl` |
| BranchUnit | 3 / 1 | phép so sánh được chọn theo `funct3` |
| LoadExtract | 2 / 8, 1 / 16, 3 / 32 | byte, halfword, kết quả cuối theo `funct3` |
| StoreMerge | 2 / 8 (3), 1 / 8 (4) | byte nguồn cho mỗi lane, byte cũ / mới cho mỗi lane |
| Pipeline | 2 / 32 (forwarding A và B), 1 / 32 (giá trị memory được forward, flush của instruction vừa fetch), 1 / 13 (bubble trong control word) | |

Cài đặt quan trọng: **width phải bằng độ rộng của các bus** được nối (sai khác hiện ra là dây màu cam); các đầu vào dữ liệu không dùng có thể để hở, vì chỉ đầu vào được chọn mới tới đầu ra.
Vì sao dùng mux mà không dùng bus tri-state: không xung đột, luồng dữ liệu nhìn thấy được, mô phỏng mang tính xác định.

### Demultiplexer
Gửi đầu vào dữ liệu của nó tới **một** trong `2^select` đầu ra; các đầu ra còn lại xuất 0 (`Disabled Output` = 0, mặc định).

| Cài đặt | Giá trị | Vì sao |
|---|---|---|
| Select Bits | 5 | 32 đầu ra, mỗi register một đầu ra |
| Data Bits | 1 (mặc định) | đầu vào dữ liệu là `RegWrite`, một bit |
| Three-state | no | các đầu ra không được chọn bị kéo về 0, không thả nổi |

Dùng một lần: `RegisterFile`.  Đầu vào = `RegWrite`, select = `rd`, đầu ra *i* = write enable của register *i*.  Khi `RegWrite = 0` mọi write enable đều bằng 0.
Một decoder thường cũng dùng được nhưng sẽ cần thêm một cổng AND với `RegWrite` cho mỗi đầu ra.

### Splitter
Cắt một bus rộng thành các phần hoặc gộp các phần thành một bus.

| Tên trong file | Tên trong GUI | Ghi chú |
|---|---|---|
| `incoming` | Bit Width In | độ rộng của bus đã gộp |
| `fanout` | Fan Out | số phần |
| `bitN` | Bit N | bit N đi tới phần nào (một cài đặt cho mỗi bit) |
| `facing` | Facing | **east**: bus ở bên trái, các phần ở bên phải (tách); **west**: bus ở bên phải, các phần ở bên trái (gộp) |
| `spacing` | Spacing | 3 trong mọi circuit được sinh ra = 30 px giữa các pin (mặc định 1 = 10 px) |

Công dụng: cắt một instruction thành các trường (`fanout 6`), `PC[9:2]` (`fanout 3`: bit 1:0 / 9:2 / 31:10), địa chỉ thành byte offset và word index, đóng gói và giải nén control word của pipeline
(`fanout 10`, rộng `13` bit), tạo bus 2 / 3 bit từ các tín hiệu đơn (`ALUOp`, `ImmSel`, `ASel`, `WBSel`), bốn byte lane của một word.
Vì sao `spacing 3`: với khoảng cách 10 px giữa các pin thì không còn chỗ để gắn một tunnel có label vào từng pin.

---

## 3. Số học và so sánh: Adder, Subtractor, Comparator, Shifter, Bit Extender

### Adder
`Data Bits` = 32.  Đầu vào A, B, carry-in; đầu ra sum, carry-out.  Carry-in và carry-out **để hở**; carry-in không nối được tính là 0 (các test chứng minh điều đó).
Được dùng: `PC + 4`, `PC + imm` (địa chỉ đích branch / JAL), phép ADD của ALU.

### Subtractor
`Data Bits` = 32; tính A - B (các pin borrow để hở).  Dùng một lần: phép SUB của ALU.  Vì sao dùng subtractor riêng thay vì "adder với B đảo": rõ ràng hơn và không tốn gì trong Logisim.

### Comparator
Xuất ba bit: A > B, A = B, A < B.

| Tên trong file | Tên trong GUI | Giá trị | Ghi chú |
|---|---|---|---|
| `width` | Data Bits | 32, 7, 5 | 32 cho dữ liệu, 7 cho opcode, 5 cho số hiệu register |
| `mode` | Numeric Type | `unsigned` hoặc two's complement (mặc định) | **tính có dấu / không dấu rất quan trọng với dữ liệu 32 bit**: SLT và `blt` / `bge` dùng two's complement, SLTU và `bltu` / `bgeu` dùng unsigned.  Với so sánh opcode và số hiệu register thì không quan trọng; dùng unsigned |

Được dùng: 9 comparator opcode trong `MainControl`; ALU (SLT có dấu, SLTU không dấu); `BranchUnit` (mỗi loại một cái); so sánh số hiệu register trong `ForwardingUnit` và `HazardUnit`.

### Shifter
| Tên trong file | Tên trong GUI | Giá trị | Vì sao |
|---|---|---|---|
| `width` | Data Bits | 32 | |
| `shift` | Shift Type | `ll` (logical left, mặc định), `lr` (logical right), `ar` (arithmetic right) | mỗi loại một shifter cho SLL, SRL, SRA |

Đầu vào shift amount rộng 5 bit (`B[4:0]`), đúng như RISC-V quy định.

### Bit Extender
Mở rộng một bus.

| Tên trong file | Tên trong GUI | Giá trị | Dùng cho |
|---|---|---|---|
| `in_width` / `out_width` | Bit Width In / Out | 12, 13, 21 -> 32; 8, 16 -> 32; 1 -> 32 | immediate, byte / halfword được load, kết quả SLT |
| `type` | Extension Type | `sign` (mặc định) hoặc `zero` | **sign** cho immediate và cho `lb` / `lh`; **zero** cho `lbu` / `lhu` và cho kết quả SLT / SLTU 1 bit (kết quả so sánh là 0 hoặc 1, không bao giờ là -1) |

(Một trong các lỗi ban đầu: extender của SLTU là *sign* và trả về `0xFFFFFFFF` thay vì 1.)

---

## 4. Cổng logic

| Cổng | Cài đặt | Dùng |
|---|---|---|
| AND, OR, XOR | `width` (Data Bits): 32 tạo cổng theo từng bit cho ALU; `inputs` (Number Of Inputs): mặc định 2, 3 cho các cây OR của `MainControl` | AND / OR / XOR của ALU (32 bit); mặt nạ địa chỉ JALR (AND 32 bit với `0xFFFFFFFE`); các phương trình control; điều kiện hazard / forwarding |
| NOT | không có | clock đảo `CLK_n`; điều kiện `!=`, `>=`; "not stall" |

Vì sao dùng cây OR tối đa 3 đầu vào: cổng OR rộng có các pin đầu vào cách nhau chỉ 10 px, không còn chỗ cho label; hai cổng nhỏ dễ đọc hơn.  Kích thước cổng để mặc định.
Tùy chọn `gateUndefined = ignore` (mục 0) làm cho các đầu vào không dùng trở nên vô hại.

---

## 5. Đi dây và I/O: Constant, Pin, Tunnel, Probe, Clock, Text

### Constant
| Tên trong file | Tên trong GUI | Default | Ghi chú |
|---|---|---|---|
| `value` | Value | **1** | **bẫy**: mặc định là 1, không phải 0, và Logisim không ghi giá trị mặc định vào file, nên một constant không có dòng `value` *chính là* số một (trong [BOM.md](BOM.md) các constant như vậy được đánh dấu).  Một constant "zero" không được đặt `value=0x0` đã làm `lui` tính ra `x+1` một lần |
| `width` | Data Bits | 1 | phải khớp với bus |

Được dùng: các constant opcode (7 bit, `MainControl`), các mã `ALUCtrl` (4 bit, 19 cái trong `ALUControl`), `0`, `4`, `0xFFFFFFFE` (32 bit), số hiệu register 0 (5 bit), 12 bit không của U-immediate, control word toàn 0.

### Pin
Các pin input và output định nghĩa giao diện của một circuit.

| Tên trong file | Tên trong GUI | Giá trị | Vì sao |
|---|---|---|---|
| `type` | Type | input (mặc định) / `output` | |
| `width` | Data Bits | 1..32 | |
| `label` | Label | tên của tín hiệu | **trở thành tên pin trên hộp sub-circuit** |
| `radix` | Radix | 16 cho pin dữ liệu 32 bit (mặc định 2) | giá trị dễ đọc khi poke |
| `facing` | Facing | east cho input, west cho output (các khối vẽ tay còn dùng north / south) | |
| `appearance` | Appearance | classic | pin hình chữ nhật hiển thị giá trị |
| `initial` | Reset value | 0 (mặc định) | vì vậy `RESET` bắt đầu ở 0 |

**Thứ tự các pin** bên trong một circuit quyết định thứ tự của chúng trên hộp: input ở bên trái sắp xếp từ trên xuống dưới, output ở bên phải.  Các circuit được sinh ra đặt pin thành một cột theo đúng thứ tự mong muốn.

### Tunnel
Một đầu dây có label; mọi tunnel cùng label trong một circuit đều được nối với nhau.

| Tên trong file | Tên trong GUI | Giá trị | Vì sao |
|---|---|---|---|
| `label` | Label | tên tín hiệu | phân biệt hoa thường |
| `width` | Data Bits | = độ rộng của net | **phải bằng độ rộng bus** (mặc định 1), nếu không dây sẽ màu cam |
| `facing` | Facing | west (hộp ở bên phải đầu dây) hoặc east (hộp ở bên trái) | hộp label kéo dài ra xa component |

Vì sao dùng tunnel thay vì dây: một CPU có hàng trăm kết nối; dây dài cắt nhau và trở nên không đọc được.  Tunnel là một *cái tên*, và tên là thứ mà báo cáo và guide nói đến.
Dự án có khoảng 900 tunnel.  Bộ sinh đặt một tunnel trên mọi pin cần kết nối.

### Probe
`radix` = 16 (2 cho tín hiệu 1 bit) và `label` = tên net.  `main` có 15 probe, `Pipeline` có 27, xếp thành các hàng dưới mạch, mỗi probe có mô tả tiếng Việt.  Hiển thị một giá trị mà không là một phần của logic (hình oval màu vàng).  Không cần cho chức năng, hữu ích cho demo.  **Không** dùng radix 10 (`Ends` / Logisim bị treo): dùng 16.

### Clock
`High Duration` = `Low Duration` = 1 tick, `Phase Offset` 0 (tất cả đều mặc định).  Mỗi CPU một cái; đầu ra của nó là tunnel `CLK` cấp cho PC, các register pipeline, RAM và (đảo) register file.

### Text
Chỉ để chú thích (tiêu đề, giải thích, bảng).  Font `Monospaced`.  Dự án có khoảng 200 text; chúng không ảnh hưởng tới circuit.

---

## 6. Sub-circuit

Một circuit được dùng như một component.  Các cài đặt (trên circuit, trong file là `<a name="appearance" val="logisim_evolution"/>` v.v.):

| Cài đặt | Giá trị | Vì sao |
|---|---|---|
| Appearance | `logisim_evolution` (hộp có thanh tên màu đen) | kiểu chuẩn; các pin được đặt tự động theo thứ tự pin |
| `circuitnamedboxfixedsize` | true | kích thước hộp phụ thuộc số pin, không phụ thuộc tên |
| Vị trí pin | input bên trái, output bên phải (sắp xếp theo vị trí pin bên trong) | |
| Vị trí của một instance | vị trí của **pin output đầu tiên** của nó | Logisim neo hộp theo cách đó |

Các instance được liệt kê trong [BOM.md](BOM.md).

---

### Từng khối một: mỗi circuit được tạo nên từ những gì

(Danh sách chính xác kèm số lượng: [BOM.md](BOM.md).)

| Circuit | Component và cài đặt | Vì sao |
|---|---|---|
| `InstructionDecode` | 1 splitter, 32 bit -> 6 phần (7, 5, 5, 3, 5, 7 bit) | các trường của instruction nằm ở vị trí bit cố định: chỉ là đi dây, không có logic |
| `MainControl` | 9 comparator (7 bit, unsigned) mỗi cái với một constant 7 bit; các cổng OR 3 đầu vào; bus 2 bit và 3 bit tạo bằng splitter | một comparator cho mỗi opcode là cách dễ đọc nhất để viết bảng opcode; các OR hiện thực các phương trình "những lớp lệnh nào set tín hiệu này" |
| `ImmGen` | 8 splitter (cắt các trường ra khỏi instruction và gộp lại theo đúng thứ tự), 4 bit extender có dấu (I, S, B, J: 12, 12, 13, 21 -> 32 bit), với loại U dùng constant 0 rộng 12 bit và một splitter gộp thay cho extender, hai constant 0 1 bit cho bit 0 luôn bằng 0 của B và J, một multiplexer 8:1 x 32 | các bit immediate bị xáo trộn được sắp xếp lại bằng splitter; multiplexer chọn định dạng theo `ImmSel` |
| `RegisterFile` | 32 register (32 bit, label `x0..x31`), 1 demultiplexer (select 5), 2 multiplexer (select 5, 32 bit), một constant 0 32 bit cho x0 | ghi: demux chuyển `RegWrite` tới register `rd`; đọc: multiplexer bất đồng bộ; x0 chỉ có thể nạp 0 |
| `ALUControl` | 5 multiplexer 4 bit: hai cái 8:1 (bảng R-type và bảng I-type, chọn theo `funct3`), hai cái 2:1 (ADD / SUB và SRL / SRA, chọn theo bit 5 của `funct7`), một cái 4:1 (chọn theo `ALUOp`: ép add, ép sub, bảng R, bảng I); 19 constant 4 bit (các mã `ALUCtrl`) | một bảng mã là một constant cho mỗi mục được chọn bởi một multiplexer: mỗi hàng của bảng control là một constant nhìn thấy được |
| `ALU` | adder, subtractor, các cổng AND / OR / XOR 32 bit, 3 shifter (`ll`, `lr`, `ar`), comparator có dấu và không dấu + extender 1 -> 32 zero, một multiplexer 16:1 x 32 | mọi phép toán được tính song song, multiplexer chọn một theo `ALUCtrl` (đơn giản; tốc độ không quan trọng trong Logisim) |
| `BranchUnit` | comparator 32 bit unsigned + signed, 3 cổng NOT, một multiplexer 8:1 x 1, một cổng AND | sáu điều kiện branch là ba phép so sánh và phủ định của chúng |
| `LoadExtract` | splitter (4 byte, 2 half), multiplexer 4:1 x 8 và 2:1 x 16, 4 bit extender (sign / zero, 8 / 16 -> 32), một multiplexer 8:1 x 32 | chọn phần của word, mở rộng theo yêu cầu của instruction |
| `StoreMerge` | 6 splitter (word cũ, write data, size, địa chỉ byte-enable, byte enable, word mới), 3 multiplexer byte (byte nguồn cho mỗi lane), một ROM 16 x 4, 4 multiplexer byte hai đường | read-modify-write một word |
| `Memory` | RAM (256 x 32, đọc async, line enables), `LoadExtract`, `StoreMerge`, 1 splitter địa chỉ (byte offset / word index) | xem mục 1 |
| `ForwardingUnit` | 6 comparator (5 bit, unsigned), các cổng AND / NOT, 2 splitter tạo select 2 bit | so sánh số hiệu register, một quy tắc cho mỗi nguồn |
| `HazardUnit` | 3 comparator (5 bit), OR, NOT, AND 3 đầu vào | điều kiện load-use |
| `main` | register PC, ROM, 2 adder (PC+4, PC+imm), một AND 32 bit với mặt nạ 0xFFFFFFFE, một cổng OR, 5 multiplexer (A, B, write-back, hai cái cho next PC), 8 sub-circuit | datapath ở mục 4 của guide |
| `Pipeline` | 24 register (PC + 23 register pipeline), 8 splitter (các bit PC, đóng gói / giải nén control word), 10 sub-circuit, các multiplexer forwarding và flush, một cổng NOT cho `CLK_n` | phiên bản 5 stage |

## 7. Quyết định thiết kế: vì sao chọn cái này mà không phải cái kia

| Quyết định | Phương án thay thế | Vì sao ta chọn như vậy |
|---|---|---|
| Instruction ROM và data RAM tách biệt (Harvard) | một memory dùng chung | không có structural hazard trong pipeline (fetch và truy cập dữ liệu trong cùng chu kỳ); đơn giản |
| Register file làm từ 32 `Register` + mux + demux | RAM làm register file (dual RAM) | nhìn thấy được: mỗi register là một hộp có label để đọc; `x0` có thể nối cứng về 0; pipeline ghi ở cạnh xuống, điều này rất đơn giản với register |
| Register file đọc bất đồng bộ | đọc theo clock | CPU single-cycle cần toán hạng ngay trong cùng chu kỳ |
| RAM đọc bất đồng bộ, line enables | đọc đồng bộ / byte enables | dữ liệu load phải đến trong cùng chu kỳ; byte enables sẽ cần bốn strobe ghi |
| Store dưới một word = read-modify-write trong `StoreMerge` | RAM có byte-enable, 4 RAM 8 bit | một RAM, dễ test bằng test vector |
| Control hai tầng (`MainControl` -> `ALUOp` -> `ALUControl`) | một decoder lớn | các bảng nhỏ, mỗi bảng test riêng; cấu trúc kinh điển trong giáo trình |
| Control word sinh một lần ở ID và đóng gói | giải mã lại ở mỗi stage | một nguồn sự thật duy nhất; đóng gói làm số register pipeline ít và sơ đồ ngắn |
| Register file ghi ở cạnh xuống (pipeline) | forwarding từ WB sang ID | không cần thêm mux / comparator; mẹo trong giáo trình |
| Branch được giải quyết ở EX, luôn "not taken" | giải quyết ở ID, bộ dự đoán | nhỏ hơn và hiển nhiên đúng; tốn 2 chu kỳ cho mỗi branch được thực hiện (có thể cải thiện, xem báo cáo) |
| Adder riêng cho `PC + imm`; ALU dùng cho địa chỉ đích `JALR` | ALU cho mọi thứ | branch và JAL cần kết quả ALU ở chỗ khác; cách này tránh xung đột |
| Bộ chọn `ASel` và `WBSel` | thêm các đường riêng cho từng instruction | `lui`, `auipc`, `jal`, `jalr` dùng lại đường ALU và write-back |
| Tunnel cho mọi kết nối dài | vẽ dây | dễ đọc, sinh tự động, dễ kiểm tra theo tên |
| Circuit được sinh từ netlist (`tools/build`) | vẽ tay | chính xác, lặp lại được, kiểm chứng tự động; `main` vẽ tay ban đầu có các dây dài cắt nhau và đầu hở |
| Tránh pin pitch 10 px (`spacing 3`, fan-out routing) | để label chồng lên nhau | mọi label đều đọc được |

---

## 8. Công thức: tự dựng một component bằng tay

Dùng các công thức này nếu bạn muốn thay đổi một khối trong Logisim thay vì trong bộ sinh.

**Cổng đọc register 32-to-1** - Plexers > Multiplexer: Select Bits 5, Data Bits 32, Include Enable no; nối 32 đầu ra register vào các đầu vào 0..31 (x0 = đầu vào 0), `rs1` vào select.

**Decoder write-enable** - Plexers > Demultiplexer: Select Bits 5, Data Bits 1; đầu vào dữ liệu = `RegWrite`, select = `rd`; đầu ra *i* nối tới pin WE của register *i*.

**PC** - Memory > Register: Data Bits 32, Trigger Rising Edge, Label `PC`; D = `next_pc`, clk = `CLK`, WE = 1 (hoặc `run`), R = `RESET`.

**Data RAM** - Memory > RAM: Address Bit Width 8, Data Bit Width 32, Enables = Use line enables, Asynchronous read = yes, Data bus = separate, Appearance classic.

**Bộ mở rộng sign / zero** - Wiring > Bit Extender: Bit Width In 8 (hoặc 12, 16 ...), Bit Width Out 32, Extension Type sign hoặc zero.

**Comparator có dấu / không dấu** - Arithmetic > Comparator: Data Bits 32, Numeric Type two's complement (signed) hoặc unsigned.

**Bus 3 bit từ ba tín hiệu** - Wiring > Splitter facing west: Fan Out 3, Bit Width In 3; bit 0 -> phần 0, bit 1 -> phần 1, bit 2 -> phần 2; nối ba tín hiệu ở bên trái.

**Hằng số 0 rộng 32 bit** - Wiring > Constant: Data Bits 32, Value 0x0 (nhớ rằng mặc định là 1).

**Nạp chương trình** - nhấp chuột phải vào ROM > Load Image... và chọn một file bắt đầu bằng `v2.0 raw` (Edit Contents... mở một hex editor).
