# Nhật ký thiết kế

> Bản tiếng Việt của docs/DESIGN_LOG.md.

Được cô đọng từ `RV32I_Logisim_Evolution_Full_Session.pdf` (một phiên chat đã lưu, bằng tiếng Việt) và
cập nhật cho khớp với `RiscVComputer.circ` hiện tại. PDF dừng ở ImmGen; mọi thứ sau đó
(khối điều khiển, ALUControl, BranchUnit, Memory, register file đủ 32 thanh ghi) được xây sau và được mô tả
trong [../README.md](../README.md) và [REPORT.md](REPORT.md).

## Lộ trình đã đi theo

`ADDI/ADD/SUB` -> ALU đầy đủ -> `LW/SW` -> `BEQ/BNE` -> `JAL/JALR/LUI/AUIPC`.
Tất cả các bước đã xong, gồm `JAL/JALR/LUI/AUIPC`, các lệnh load / store tùy chọn và `BLT/BGE/BLTU/BGEU`.
Multi-cycle đã bỏ qua; pipeline 5 tầng (forwarding, stall load-use, flush khi rẽ nhánh / nhảy) đã xong.
Dự đoán rẽ nhánh và cache (tùy chọn) chưa làm.  Xem [REPORT.md](REPORT.md) để biết thiết kế cuối cùng.

Các quy ước chốt từ đầu: datapath 32 bit, địa chỉ thanh ghi 5 bit, opcode 7 bit, funct3 3 bit,
`ALUCtrl` 4 bit. Dùng tunnel cho các tín hiệu dài (`pc`, `instr`, `rs1_data`, `rs2_data`, `imm`, `wb_data`).

## Fetch

* `PC` là thanh ghi 32 bit, kích hoạt sườn lên. `PC + 4` đến từ một bộ cộng 32 bit với hằng số 4.
* ROM là 256 x 32, địa chỉ 8 bit. PC là địa chỉ byte, nên địa chỉ ROM là `PC[9:2]`
  (splitter: fan-out 3 = `PC[1:0]`, `PC[9:2]`, `PC[31:10]`).
* Gỡ lỗi bằng *Manual Tick Full Cycle*: mỗi lần nhấp một sườn lên, nên PC tiến một lần.
* Reset: chân `R` của thanh ghi. Đã thêm vào `main` dưới dạng đầu vào `RESET` (trước đó chưa được nối).

## Decode

`InstructionDecode` chỉ là một splitter:

```
opcode = instr[6:0]    rd  = instr[11:7]    funct3 = instr[14:12]
rs1    = instr[19:15]  rs2 = instr[24:20]   funct7 = instr[31:25]
```

Với lệnh kiểu I, các bit `[24:20]` là một phần của immediate, không phải `rs2`. Bộ giải mã luôn cắt
cùng các trường; khối điều khiển quyết định trường nào quan trọng.

## Register file

* 32 thanh ghi thật (`x0` nạp hằng số 0 nên luôn đọc ra 0), hai bộ ghép kênh 32:1 cho các
  cổng đọc, một bộ phân kênh 1-ra-32 (`data = RegWrite`, `select = rd`) cho các tín hiệu cho phép ghi.
* Các tunnel `x0..x31`, `WE0..WE31`, `CLK`, `wb_data` giúp mạch không thành mớ dây rối.
* Demux so với decoder: decoder chỉ cho one-hot; demux còn chuyển tiếp `RegWrite`, nên khi
  `RegWrite = 0` mọi tín hiệu cho phép ghi đều bằng 0.

## ALU

Mười phép toán được tính song song, sau đó một bộ ghép kênh 16:1 chọn theo `ALUCtrl`:

| ALUCtrl | op | | ALUCtrl | op |
|---|---|---|---|---|
| 0000 | ADD | | 0101 | SLL |
| 0001 | SUB | | 0110 | SRL |
| 0010 | AND | | 0111 | SRA |
| 0011 | OR | | 1000 | SLT (có dấu) |
| 0100 | XOR | | 1001 | SLTU (không dấu) |

Các phép dịch dùng `B[4:0]`. Giá trị test đã dùng: `5 + 7 = 0xC`, `5 - 7 = 0xFFFFFFFE`, `0x80000000 >>> 1 = 0xC0000000`,
`0xFFFFFFFF <s 1 = 1`, `0xFFFFFFFF <u 1 = 0`.
Được bao phủ bởi `tests/alu.vec` (15 hàng). Một lỗi khiến SLTU trả về `0xFFFFFFFF` (kết quả 1 bit bị mở rộng dấu) đã được tìm ra và sửa nhờ test này.

## ImmGen

`ImmSel`: 0 I, 1 S, 2 B, 3 U, 4 J. Các splitter dựng lại từng định dạng, một Bit Extender mở rộng dấu (kiểu U thì thay vào đó nối thêm 12 bit
0 bằng splitter), một bộ ghép kênh với select 3 bit chọn kết quả. Được bao phủ bởi `tests/immgen.vec`.

| Kiểu | imm | Ví dụ | Kết quả |
|---|---|---|---|
| I | `instr[31:20]` | `00500093` `addi x1,x0,5` | `00000005` |
| S | `instr[31:25]`, `instr[11:7]` | `0020A623` `sw x2,12(x1)` | `0000000C` |
| B | `[31]`, `[7]`, `[30:25]`, `[11:8]`, 0 | `00208463` `beq x1,x2,8` | `00000008` |
| U | `instr[31:12] << 12` | `123452B7` `lui x5,0x12345` | `12345000` |
| J | `[31]`, `[19:12]`, `[20]`, `[30:21]`, 0 | `008000EF` `jal x1,8` | `00000008` |

## Ghi chú gỡ lỗi (các cạm bẫy của Logisim gặp phải khi xây dựng)

* **Độ rộng không tương thích:** kiểm tra Data Bits trên Register, Adder, Constant, Pin, Tunnel, Mux. Con số nhỏ
  cạnh một dây là độ rộng của nó, không phải giá trị.
* **Bus đỏ / `E`:** hai nguồn cùng điều khiển một net (ví dụ một Input Pin và một Constant), hoặc một chân có
  hướng sai. Đầu ra bộ ghép kênh màu đỏ dù thuộc tính đúng thường là một Input Pin ở chỗ lẽ ra phải là
  Output Pin.
* **Poke đúng instance:** một mạch con mở từ cây project có trạng thái riêng. Để đổi
  các thanh ghi mà `main` thực sự dùng, đi theo *Main -> kính lúp trên instance*. Nếu một popup nói chân
  được gắn với mạch cha, chọn *Cancel* và chỉ poke các thanh ghi bên trong.
* **Probe:** một tunnel không hiển thị giá trị. Gắn một Probe (hex cho bus 32 bit, thập phân cho `rs1/rs2/rd`).
* Vị trí thành phần phải nằm trên lưới 10 px; các chân của mạch con nằm ở mép hộp, nên hãy chọn
  vị trí theo hàng chân, không theo góc hộp.

## Ghi chú về công cụ

* Logisim Evolution 4.1.0 cần Java 21 (Java 17 lỗi với `UnsupportedClassVersionError`, class file 65).
* Test headless một mạch con:
  `java -jar logisim-evolution-4.1.0-all.jar --test-vector <circuit> <file.vec> RiscVComputer.circ`.
  Dòng đầu của `.vec` liệt kê nhãn các chân (`name[width]`), giá trị là hex `0x..` hoặc nhị phân.

## Công việc về sau (sau PDF)

Ghi chú theo thứ tự thời gian, giữ lại vì nhiều bài học trong đó không hiển nhiên.

### Dọn bố cục và các test đầu tiên
* `main` được sắp xếp lại bố cục theo thứ tự các tầng với các tunnel có tên; các mạch con được thêm tiêu đề và văn bản.
* Các test vector (`--test-vector`) cho từng module đã tìm ra lỗi trong các khối dựng tay: ALU `SLTU` (mở rộng dấu thay vì mở rộng 0),
  `ALUControl` `SLL` (hằng số 6 thay vì 5), `MainControl` (chọn immediate cho JALR / LUI / JALR), `ImmGen` (dịch kiểu U, bit 0 kiểu J).
* Một mô phỏng tham chiếu + trình chạy headless cho thấy khối `Memory` ban đầu không bao giờ trả về dữ liệu (RAM đọc đồng bộ).

### RV32I đầy đủ và pipeline
* Các tín hiệu điều khiển mới: `ASel` (A = rs1 / PC / 0) và `WBSel` (ALU / bộ nhớ / PC+4); logic PC kế tiếp cho JAL, JALR (xóa bit 0) và rẽ nhánh.
* `BranchUnit` với các comparator có dấu / không dấu; `Memory` được xây lại quanh một RAM đọc bất đồng bộ, với `LoadExtract` và `StoreMerge`
  (store dưới một từ là read-modify-write một từ, byte enable lấy từ một ROM 16 hàng).
* Pipeline: các tín hiệu điều khiển được sinh ở ID và mang theo trong một control word được đóng gói; register file ghi ở sườn xuống;
  `ForwardingUnit` (EX/MEM trước MEM/WB; JAL / JALR forward PC+4), `HazardUnit` (stall load-use), flush theo `pc_src_ex`.

### Sinh mạch từ netlist
Các mạch mới được mô tả dưới dạng thành phần + net có tên và được ghi bởi `tools/build`:
bộ sinh lấy vị trí chân từ chính Logisim, thêm stub và tunnel, tránh va chạm và xác minh kết quả.  Các cạm bẫy đã gặp:

| Cạm bẫy | Hậu quả |
|---|---|
| một dây chỉ đi ngang qua đầu mút của dây khác thì **không được nối** (chỗ nối chữ T) | net bị hở mà không báo; điểm lấy `instr` và các chỗ khác bị hở trong `main` sinh ra đầu tiên |
| thành phần hoặc dây không nằm trên lưới 10 px bị snap | các chân không còn chạm vào dây |
| hai stub kết thúc tại cùng một vị trí tunnel | hai net bị chập - bộ sinh nay định tuyến có kiểm tra va chạm |
| giá trị mặc định của `Constant` là 1 | hằng số "zero" lại bằng 1: `lui` cho ra `x + 1` |
| mặc định của RAM: đọc đồng bộ, byte enable | load trả về rác; cần `asyncread = true`, `enables = line` |
| các chân của splitter cách nhau 10 px | không có chỗ cho tunnel: dùng thuộc tính `spacing` |
| một mạch tên `__x__` bị đổi tên khi nạp | dùng tên thường |
| `java *` khai triển `*` thành tên tệp trên Windows | dùng một từ như `ALL` |
| các hàng test-vector không giữ nội dung RAM giữa các hàng | kiểm thử bộ nhớ qua các chương trình hoàn chỉnh (`Run.java`) |

Một nhận định trước đó rằng `main` đã sắp xếp lại bố cục có "30 trên 30 net giống hệt" đến từ một trình kiểm tra giả định sai các kết nối chữ T;
trình kiểm tra nghiêm ngặt tìm ra 7 net hỏng, đã được sửa trước khi xây thêm bất cứ thứ gì lên trên.
