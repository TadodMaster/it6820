# Kịch bản demo

> Bản tiếng Việt của docs/DEMO.md.

Đề bài yêu cầu một buổi demo (video hoặc trực tiếp) trong đó một chương trình chạy trên CPU và các register, memory cùng pipeline được quan sát.  Đây là kịch bản cho buổi demo 5-8 phút của cả hai CPU.  Chuẩn bị: Java 21, mở `RiscVComputer.circ`.

## 0. Thiết lập (30 giây)
* Mở dự án, cho xem cây dự án: `main` (single-cycle), `Pipeline`, và các khối.
* Cho xem `programs/demo.s` trong một editor và phần listing: `python tools\rv.py asm programs\demo.s -l -o programs\demo.hex`.

## 1. CPU single-cycle (2 phút)
1. Mở `main`. Chỉ ra các tiêu đề stage IF, ID, EX, MEM, WB và các tín hiệu có tên (tunnel).
2. ROM đã hiển thị sẵn chương trình; để nạp một file trực tiếp: nhấp chuột phải vào ROM > *Load Image...* và chọn `programs/demo.hex`.
3. Poke `RESET` lên 1 rồi về 0. Dùng *Simulate > Manual Tick Full Cycle* (Ctrl+F9) nhiều lần:
   * quan sát `PC` tăng dần và `instr` thay đổi (probe cạnh ROM hiển thị mã máy);
   * mở `RegisterFile` bằng công cụ Poke (biểu tượng kính lúp trên khối): `x10` tăng dần 10, 19, 27, ... cho đến 55;
   * sau `sw` / `lw` mở `Memory` theo cách tương tự: word RAM 0 chứa 0x37.
4. Kết quả sau 39 chu kỳ: `x10 = 55 (0x37)`, `x12 = 110 (0x6E)`, `x13 = 55`, `x14 = 1`, `x1 = 0x20` (địa chỉ trả về của lệnh call).

## 2. Từng instruction một (1 phút)
Chọn một instruction, ví dụ `add x10,x10,x11`, và lần theo nó: `instr` > các trường của `InstructionDecode` > các cổng đọc của `RegisterFile` > ALU A/B
(`alu_a`, `alu_b`) > `alu_result` > `wb_data` > ghi vào `RegisterFile`.  Cho xem các đầu ra của `MainControl` với lệnh load (`MemRead`, `WBSel = 01`)
và với `jal` (`WBSel = 10`, `IsJAL`).

## 3. Pipeline (2-3 phút)
1. Mở `Pipeline`. Giải thích năm stage và bốn nhóm register (IF/ID, ID/EX, EX/MEM, MEM/WB, có label).
2. Reset, rồi tick: sau mỗi tick cho xem instruction nào đang ở stage nào (`instr_id`, `pc_ex`, `alu_result_ex`, ...).
3. **Forwarding**: chạy đến cặp `add x10,x10,x11` / `addi x11,x11,-1` - các đầu ra `ForwardA / ForwardB` của `ForwardingUnit` đổi từ 00 sang 01 / 10.
4. **Branch flush**: vòng lặp `bnez x11, loop` - khi branch được thực hiện thì `pc_src_ex = 1`, hai instruction theo sau trở thành bubble.
5. **Load-use stall**: load một giá trị và dùng ngay (ví dụ dán `tests/programs/hazard.s` vào ROM) rồi cho xem `stall = 1`, PC được giữ một chu kỳ.
6. Sau 64 chu kỳ kết quả giống hệt CPU single-cycle (cùng các register).

## 4. Test (1 phút)
```powershell
powershell -File tests\run_tests.ps1                  # 9 module test files
python tests\run_cpu_tests.py --circuit all            # programs on both CPUs vs the reference simulator
python tests\fuzz.py --count 10                        # random programs
```
Cho xem các dòng `ALL PASSED` và bảng cycle / CPI.

## Checklist khi nộp bài
* source: `RiscVComputer.circ`, `programs/`, `tools/`, `tests/` (mọi thứ trong thư mục này)
* báo cáo kỹ thuật: `docs/REPORT.md` (xuất ra PDF / Word, 10-20 trang kèm các hình từ `docs/img`)
* module test và CPU test: `tests/`
* buổi demo này
* README: `README.md`
