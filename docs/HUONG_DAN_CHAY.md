# Hướng dẫn chạy

File này trả lời nhanh: **cài gì, chạy Logisim thế nào, file `.hex` ở đâu, mã test ở đâu, chạy test ra sao, sửa gì thì chạy lại gì**. Lệnh viết cho PowerShell trên Windows, chạy ở thư mục gốc của repo (thư mục chứa `RiscVComputer.circ`).

## 1. Cài đặt

| Thứ | Phiên bản | Dùng để |
|---|---|---|
| Java (JDK) | **21 trở lên** (Logisim 4.1.0 không chạy trên Java 17) | chạy Logisim và các công cụ chạy mạch không giao diện |
| Python | 3.10+ | assembler, kiểm thử, bộ sinh mạch |
| Node.js | tùy chọn | chỉ để chạy `node tools/web/test_engine.js` (kiểm thử trang web) |
| Trình duyệt | bất kỳ | xem bản web trực quan `docs/web/index.html` |

Nếu `java` mặc định trên máy là bản cũ, đặt biến môi trường cho phiên làm việc (đổi đường dẫn cho đúng máy bạn):

```powershell
$env:JAVA = "C:\Program Files\Java\jdk-21.0.12.1\bin\java.exe"
```

File `logisim-evolution-4.1.0-all.jar` phải nằm ở thư mục gốc repo (các công cụ tìm nó ở đó).

## 2. Cấu trúc repo

```
RiscVComputer.circ        dự án Logisim: mạch main (single-cycle), Pipeline, và 12 khối con
programs/                 chương trình mẫu: demo.s, hazards_demo.s và các file .hex tương ứng
tests/                    mã kiểm thử (xem mục 5)
tools/                    công cụ: assembler, chạy mạch không giao diện, bộ sinh mạch, trang web (mục 6)
docs/                     tài liệu (mục 7), hình mạch (docs/img), bản web (docs/web)
```

**File `.hex` nằm ở `programs\`:**

| File | Nội dung |
|---|---|
| `programs\demo.hex` (từ `demo.s`) | cộng 10+9+...+1, lưu và đọc lại bộ nhớ, gọi một hàm. Kết quả: x10 = 55, x12 = 110 |
| `programs\hazards_demo.hex` (từ `hazards_demo.s`) | chương trình thử forwarding, stall (load-use) và flush (rẽ nhánh) của pipeline |

Các chương trình dùng để kiểm thử (`alu`, `mem`, `branch`, `jump`, `fib`, `hazard`) nằm ở `tests\programs\*.s`. Chúng không có sẵn file `.hex`: bộ test tự dịch ra file tạm khi chạy.

## 3. Chạy Logisim

```powershell
java -jar .\logisim-evolution-4.1.0-all.jar .\RiscVComputer.circ
```

(Dùng `& $env:JAVA -jar ...` nếu đã đặt `$env:JAVA`.) Trong cây bên trái chọn mạch:
- `main`: CPU single-cycle (một lệnh mỗi chu kỳ);
- `Pipeline`: CPU pipeline 5 tầng.

**Nạp chương trình vào ROM:** chuột phải vào khối **ROM** trong mạch, chọn **Load Image...**, gõ đường dẫn một file hex rồi Enter, ví dụ `D:\hust\logisim\programs\hazards_demo.hex`. (Mỗi CPU có một ROM riêng; mặc định `main` chứa `demo.s`, `Pipeline` chứa `hazards_demo.s` hoặc `demo.s`, tùy lần lưu gần nhất.)

**Chạy:**
1. Bấm vào vùng trống của mạch, nhấn **Ctrl+R** (Simulate > Reset Simulation) để đặt lại.
2. Nhấn **Ctrl+F9** (Simulate > Manual Tick Full Cycle) để chạy từng chu kỳ.
3. Hoặc bật **Ctrl+K** (Simulate > Auto-Tick Enabled) một lần để chương trình tự chạy từ đầu đến cuối; mạch tự dừng ở lệnh `halt` và chân `DONE` lên 1. Chân `PAUSE` = 1 để tạm dừng.
4. Xem thanh ghi ở tab **State** (góc dưới bên trái) và các hàng probe ở cuối mạch.

Khi đóng Logisim, chọn **Don't Save** nếu bạn không định sửa mạch. Lưu nhầm sẽ ghi đè file mạch (ví dụ đổi chương trình trong ROM).

## 4. Viết và dịch chương trình assembly

Assembler tự viết nằm ở `tools\rv.py` (hỗ trợ toàn bộ RV32I và các lệnh giả như `li`, `mv`, `j`, `ret`, `beqz`).

```powershell
python tools\rv.py asm programs\demo.s -o programs\demo.hex -l   # dịch .s ra .hex, -l in danh sách lệnh
python tools\rv.py sim programs\demo.s                           # chạy bằng bộ mô phỏng tham chiếu
```

Muốn chạy chương trình mới: viết `ten.s` trong `programs\`, dịch ra `ten.hex`, rồi nạp vào ROM như mục 3. Chương trình phải kết thúc bằng một vòng `halt: j halt`.

## 5. Kiểm thử

| Nơi | Là gì |
|---|---|
| `tests\*.vec` | test vector của từng khối: `alu`, `alucontrol`, `maincontrol`, `immgen`, `branchunit`, `loadextract`, `storemerge`, `forwardingunit`, `hazardunit` |
| `tests\programs\*.s` | 6 chương trình tự kiểm tra, mỗi chương trình đặt `x31 = 0x600D` khi mọi thứ đúng |
| `tests\run_tests.ps1` | chạy các file `.vec` bằng bộ test của Logisim |
| `tests\run_cpu_tests.py` | chạy các chương trình trên **cả hai CPU** và so với bộ mô phỏng tham chiếu |
| `tests\fuzz.py` | sinh chương trình ngẫu nhiên, chạy trên cả hai CPU, so với tham chiếu |

```powershell
powershell -File tests\run_tests.ps1          # 9 file test khối, 106 dòng, khoảng 15-35 giây
python tests\run_cpu_tests.py --circuit all    # 7 chương trình x 2 CPU
python tests\fuzz.py --count 20 --seed 1       # 20 chương trình ngẫu nhiên
```

Kết quả đúng là dòng `ALL PASSED`. Muốn kiểm tra tất cả một lần trước khi trình bày:

```powershell
powershell -ExecutionPolicy Bypass -File tools\presentation_check.ps1 -Quick
```

Phải thấy dòng cuối `READY: everything passed.`

## 6. Công cụ

| File | Làm gì |
|---|---|
| `rv.py` | assembler (`asm`) và bộ mô phỏng tham chiếu (`sim`) |
| `live_proof.py` | chạy một chương trình trên bộ tham chiếu, single-cycle và pipeline rồi in bảng so sánh; dòng `VERDICT` nói hai CPU có đúng không: `python tools\live_proof.py [programs\hazards_demo.s]` |
| `probe.py` | xem giá trị các tín hiệu có tên của mạch đang chạy, ví dụ `python tools\probe.py --trace RiscVComputer.circ Pipeline programs\hazards_demo.s 14 stall ForwardB` |
| `java\*.java` (đã dịch ra `tools\bin`) | chạy mạch không giao diện (`Run`), vẽ ảnh mạch (`Render`), dump vị trí chân (`Ends`); dịch lại bằng `tools\compile.ps1` |
| `build\` | bộ sinh mạch: `build_all.py` tạo lại `RiscVComputer.circ` từ các netlist và `build\base.circ` (các khối vẽ tay) |
| `bom.py` | in bảng kê linh kiện của mạch |
| `build_web.py`, `web\` | dựng trang web `docs\web\index.html`; kiểm thử bằng `node tools\web\test_engine.js` |
| `md_to_pdf.py` | đổi một file Markdown thành PDF: `python tools\md_to_pdf.py vao.md ra.pdf` |
| `presentation_check.ps1` | kiểm tra tất cả trước khi trình bày |

## 7. Tài liệu

| File | Đọc để |
|---|---|
| `README.md` (gốc) | tổng quan, bắt đầu nhanh, kết quả |
| `docs\HUONG_DAN.md` | hiểu CPU hoạt động thế nào, và các công cụ |
| `docs\KIEN_TRUC.md` | cấu hình từng component, bảng kê, nhật ký thiết kế, sơ đồ luồng 14 mạch |
| `docs\BAO_CAO.md` | báo cáo kỹ thuật, đề bài, phân công nhóm |
| `docs\web\index.html` | mở bằng trình duyệt: chạy từng tick CPU, xem hazard, biểu đồ |
| `docs\img\` | ảnh của từng mạch |

## 8. Chỉnh sửa và chạy lại

- **Đổi chương trình `.s`:** dịch lại bằng `tools\rv.py asm`, nạp hex vào ROM. Nếu muốn lưu trong mạch, bấm Save trong Logisim.
- **Đổi mạch:** `RiscVComputer.circ` được sinh ra từ mã Python, **đừng sửa tay trong Logisim rồi lưu** nếu bạn định sinh lại, vì sinh lại sẽ ghi đè. Muốn đổi mạch thì sửa trong `tools\build\*.py` rồi chạy:
  ```powershell
  python tools\build\build_all.py tools\build\base.circ RiscVComputer.circ
  ```
  (khoảng 5-7 phút; đóng Logisim trước, vì file tự lưu `.RiscVComputer.circ.autosave` làm bước kiểm tra bị treo). Sau đó chạy lại bộ test ở mục 5.
- **Đổi trang web:** sửa trong `tools\web\`, chạy `python tools\build_web.py`, rồi `node tools\web\test_engine.js`.

## 9. Xử lý lỗi

| Triệu chứng | Cách xử lý |
|---|---|
| Logisim không mở được | dùng Java 21 (xem mục 1) |
| `stall` luôn bằng 0 ở `Pipeline` | ROM đang chứa `demo.s` (không có stall); nạp `programs\hazards_demo.hex` |
| Công cụ chạy mạch báo không đọc được file, hoặc treo | đóng cửa sổ Logisim đang mở và xóa file `.RiscVComputer.circ.autosave` nếu còn |
| Giá trị thanh ghi lạ sau khi chạy | nhấn Ctrl+R trước khi chạy, và nạp đúng file hex |
