# Bài tập lớn: thiết kế máy tính RISC-V 32-bit

Nguồn: `Yêu cầu BTL.docx`. Cột / mục *Trạng thái* là tình trạng hiện tại của project (xem [../README.md](../README.md) và
[REPORT.md](REPORT.md)).

## 1. Mục tiêu

Thiết kế, mô phỏng và kiểm thử một máy tính 32-bit sử dụng kiến trúc tập lệnh RISC-V, bao gồm CPU,
bộ nhớ chương trình, bộ nhớ dữ liệu và các thành phần điều khiển cần thiết.

Phiên bản cuối cùng phải sử dụng kiến trúc pipeline 5 tầng: **IF → ID → EX → MEM → WB**
và xử lý đúng các data hazard và control hazard cơ bản.

**Trạng thái: đạt.** Mạch `Pipeline` có đủ 5 tầng, forwarding (data hazard), stall khi load-use, flush khi rẽ nhánh / nhảy (control hazard).

## 2. Công cụ

* Logisim Evolution (đang dùng 4.1.0)
* [Optional] công cụ HDL khác để thiết kế mạch bằng VHDL — không dùng

Công cụ phụ trợ tự viết: assembler + mô phỏng tham chiếu (`tools/rv.py`), bộ chạy chương trình trên mạch không cần giao diện (`tools/java/Run.java`),
bộ sinh mạch từ netlist (`tools/build/`).

## 3. Yêu cầu kiến trúc

| Mục | Giá trị | Trạng thái |
|---|---|---|
| Data width | 32 bits | đạt |
| Instruction width | 32 bits | đạt |
| Register | 32 × 32 bit | đạt (`x0` luôn bằng 0) |
| PC | 32 bits | đạt |
| Architecture | RISC-V Base ISA: RV32I | đạt (trừ `fence`, `ecall`, `ebreak`, CSR: coi như `nop`) |

## 4. Tập lệnh tối thiểu

| Nhóm | Lệnh | Trạng thái |
|---|---|---|
| Arithmetic / Logic | ADD, SUB, AND, OR, XOR, SLT, SLTU, SLL, SRL, SRA | đạt, có test |
| Immediate | ADDI, ANDI, ORI, XORI, SLTI, SLTIU, SLLI, SRLI, SRAI | đạt, có test |
| Memory | LW, SW | đạt, có test |
| Memory (optional) | LB, LH, LW, LBU, LHU, SB, SH | **đạt toàn bộ**, có test |
| Branch | BEQ, BNE, JAL, JALR | đạt, có test |
| Branch (optional) | BLT, BGE, BLTU, BGEU | **đạt toàn bộ**, có test |
| Khác của RV32I | LUI, AUIPC | đạt, có test |

Ví dụ: `add t1, t2, t3`, `add s1, zero, t1`, `addi t1, t2, 10` — assembler hỗ trợ cả tên ABI (`t1`, `zero`, ...) và `x0..x31`.

## 5. Thiết kế CPU 2 phiên bản

| Phiên bản | Mạch | Trạng thái |
|---|---|---|
| Đơn chu kỳ (single-cycle) | `main` | đạt, CPI = 1 |
| Pipeline 5 tầng | `Pipeline` | đạt; CPI 1.0 khi không rẽ nhánh, mỗi lần rẽ nhánh / nhảy thực hiện mất thêm 2 chu kỳ |

## 6. Yêu cầu về sản phẩm

**Cơ bản**

* Phải chạy được từ các lệnh nạp vào instruction memory (không chỉnh trực tiếp giá trị các thanh ghi). **Đạt:** chương trình nạp vào ROM
  (Edit Contents > Open file `.hex`), thanh ghi chỉ thay đổi do CPU thực thi.
* Nếu có công cụ từ code assembly sang byte code nạp được vào ROM thì càng tốt. **Đạt:** `python tools/rv.py asm prog.s -o prog.hex`.

**Nâng cao (optional):** branch prediction, cache, multiplier/divider, interrupt, GPIO/UART,
tăng performance cho pipeline (predictor/cache/forwarding nâng cao), floating point. **Chưa làm** (forwarding đầy đủ thì có).

## 7. Báo cáo (mỗi nhóm nộp)

| Hạng mục | Trạng thái |
|---|---|
| Toàn bộ source/project (`.circ`, `.vhd`, `.sv`, testbench, chương trình test) | đạt: `RiscVComputer.circ`, `tools/`, `tests/`, `programs/` |
| Báo cáo kỹ thuật ~10–20 trang: kiến trúc, từng module, pipeline, hazard, kiểm thử, kết quả, mở rộng | **bản nháp đầy đủ** ở [REPORT.md](REPORT.md) (tiếng Anh); nhóm cần đọc lại, bổ sung và xuất ra PDF / Word |
| Bộ test cho từng module và cho toàn CPU | đạt: 9 file test module, 7 chương trình test, fuzz ngẫu nhiên (`tests/`) |
| Demo video hoặc demo trực tiếp (chạy chương trình, quan sát register/memory/pipeline) | kịch bản ở [DEMO.md](DEMO.md); **nhóm cần quay video** |
| README mô tả cách mở project, chạy simulation, nạp chương trình, chạy test | đạt: [../README.md](../README.md) |
