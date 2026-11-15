# Hướng dẫn trình bày cho thầy - ngắn gọn

Tổng thời gian khoảng **10-12 phút**. Mỗi bước ghi: **làm gì**, **cho thầy xem gì**, **nói gì**.

---

## A. Chuẩn bị (làm trước khi thầy vào)

1. Mở terminal ở thư mục dự án và chạy kiểm tra một lần:
   ```powershell
   cd D:\hust\logisim
   powershell -ExecutionPolicy Bypass -File tools\presentation_check.ps1 -Quick
   ```
   Phải thấy dòng **`READY: everything passed.`**
2. **Tắt thông báo** (Win+N > Không làm phiền), đóng Teams / Zalo / mail.
3. Mở Logisim (cần Java 21):
   ```powershell
   java -jar .\logisim-evolution-4.1.0-all.jar .\RiscVComputer.circ
   ```
4. Mở sẵn trong trình duyệt file `D:\hust\logisim\docs\web\index.html` (để dành cho bước 8).
5. Trong Logisim: nhấn **Ctrl+R**, bấm tab **State** (góc dưới bên trái) để thấy `PC` và `x0..x31`.

---

## Phím tắt Logisim dùng trong bài (và cách làm khi không dùng phím tắt)

Mọi phím tắt đều nằm trong menu **Simulate** ở thanh menu trên cùng của Logisim, nên không nhớ phím vẫn làm được bằng chuột.

| Phím | Làm gì | Nếu không dùng phím tắt |
|---|---|---|
| **Ctrl+F9** | **Một chu kỳ xung nhịp** (một "tick" đầy đủ): CPU chạy đúng một lệnh. Dùng để chạy từng bước và quan sát | Menu **Simulate > Manual Tick Full Cycle** (mỗi lần chọn là một chu kỳ) |
| **Ctrl+K** | **Bật / tắt chạy tự động**: Logisim tự phát xung nhịp liên tục, không cần bấm. Bật một lần là chương trình chạy từ đầu đến cuối (mạch tự dừng ở `halt`, chân `DONE` = 1) | Menu **Simulate > Auto-Tick Enabled** (có dấu tích = đang bật; chọn lần nữa để tắt). Chỉnh tốc độ ở **Simulate > Auto-Tick Frequency** |
| **Ctrl+R** | **Đặt lại mô phỏng**: PC và mọi thanh ghi về 0, mạch chạy lại từ đầu | Menu **Simulate > Reset Simulation** |
| Ctrl+T | Nửa chu kỳ xung nhịp (ít dùng) | Menu **Simulate > Manual Tick Half Cycle** |

Cách làm không cần phím tắt, từng bước:
- **Chạy từng bước:** bấm menu **Simulate**, chọn **Manual Tick Full Cycle**; lặp lại cho mỗi lệnh.
- **Chạy một lần bấm:** bấm menu **Simulate**, chọn **Auto-Tick Enabled** (chỉ một lần). Khi xong (đèn `DONE` = 1) mở lại menu và bỏ tích để tắt.
- **Chạy lại từ đầu:** bấm menu **Simulate**, chọn **Reset Simulation**.

Mẹo: bấm vào mạch trước (cho Logisim nhận phím), và chuột phải/giữ phím cũng được; trên laptop có thể cần giữ thêm phím **Fn** để dùng F9.

---

## B. Các bước trình bày

| Bước | Làm gì | Cho thầy xem gì | Nói gì |
|---|---|---|---|
| **1. Giới thiệu** (30 giây) | Ở cây bên trái chỉ vào `main` và `Pipeline` | Hai CPU dùng chung các khối: ALU, RegisterFile, MainControl... | "Em làm máy tính RISC-V 32-bit, có bản single-cycle và bản pipeline 5 tầng." |
| **2. Chương trình** (30 giây) | Mở mạch `main`, chỉ vào ROM; mở file `programs\demo.s` | Mã máy trong ROM và mã assembly tương ứng | "Chương trình cộng 10+9+...+1, lưu vào bộ nhớ, đọc lại, gọi một hàm nhân đôi." |
| **3. Chạy từng bước** (2 phút) | **Ctrl+R**, rồi nhấn **Ctrl+F9** nhiều lần (mỗi lần = 1 chu kỳ = 1 lệnh) | Tab State: sau tick 3 thì **x10 = 0x0a**; tick 6 thì **x10 = 0x13**; tick 12 thì **x10 = 0x22**. Hàng probe màu vàng dưới mạch cho thấy lệnh đang chạy | "Mỗi lần bấm là một lệnh. x10 là tổng cộng dồn, x11 là biến đếm." |
| **4. Chạy một lần bấm** (1 phút) | **Ctrl+R**, rồi bật **Simulate > Auto-Tick Enabled (Ctrl+K)** một lần | Chương trình tự chạy hết, tự dừng; chân **DONE = 1**. Kết quả: **PC = 0x28, x10 = 0x37 (55), x12 = 0x6e (110), x13 = 0x37, x14 = 1** | "Chỉ bật một lần là chạy từ đầu đến cuối; mạch tự dừng khi gặp lệnh halt. Chân PAUSE để tạm dừng." (Tắt Ctrl+K sau khi xong.) |
| **5. Nạp chương trình khác** (1 phút) | Chuột phải vào ROM > **Load Image...** > gõ `D:\hust\logisim\programs\hazards_demo.hex` > Enter. **Ctrl+R**, bấm **Ctrl+F9** 8 lần | Sau 8 tick: **PC = 0x24, x1 = 0x64, x3 = 0x65, x4 = 0xc9, x7 = 7** và **x5 = x6 = 0** | "Chương trình đi qua ROM, không gán thanh ghi trực tiếp. x5, x6 bằng 0 vì lệnh rẽ nhánh đã bỏ qua hai lệnh đó." |
| **6. Pipeline** (3 phút) | Bấm tab **Design**, mở mạch **`Pipeline`**. Nạp `hazards_demo.hex` vào **ROM của Pipeline** như bước 5. **Ctrl+R**, bấm **Ctrl+F9** từng tick, nhìn hàng probe ở cuối mạch | **Tick 3:** `ForwardB = 10` (forwarding). **Tick 4:** `stall = 1`, tick 5 PC **đứng yên** ở 0x10 (stall load-use). **Tick 8:** `pc_src_ex = 1` (rẽ nhánh, hủy 2 lệnh). Cuối cùng vẫn **x5 = x6 = 0** | "Năm lệnh chạy chồng nhau. Forwarding giải quyết phụ thuộc dữ liệu, load rồi dùng ngay thì stall 1 chu kỳ, rẽ nhánh thì hủy 2 lệnh." |
| **7. Chứng minh đúng** (2 phút) | Ở terminal: `python tools\live_proof.py` | Bảng 3 cột: bộ mô phỏng tham chiếu, single-cycle, pipeline, mọi dòng ghi **OK**, và dòng cuối **`VERDICT: both CPUs produce exactly the reference result`** | "Bộ mô phỏng tham chiếu viết độc lập bằng Python. Hai CPU cho kết quả giống hệt ở cả 32 thanh ghi và bộ nhớ." |
| **8. Hình ảnh trực quan** (1-2 phút) | Chuyển sang trình duyệt (`docs\web\index.html`). Tab **Pipeline**: chọn `hazards_demo`, bấm **▶ Chạy tự động đến hết**. Tab **Biểu đồ hiệu năng** | Băng chuyền lệnh: thẻ đứng yên khi stall, thẻ đỏ khi bị hủy, mũi tên xanh là forwarding. Biểu đồ so sánh số chu kỳ hai CPU | "Đây là bản mô phỏng trên web để dễ nhìn dữ liệu chạy qua từng tầng." |
| **9. Kết quả** (30 giây) | Chỉ vào bảng ở tab Biểu đồ hiệu năng (hoặc phần Results của báo cáo) | `demo.s`: single-cycle **39 chu kỳ**, pipeline **64 chu kỳ** (CPI 1,64) | "Trong mô phỏng pipeline không ít chu kỳ hơn vì Logisim không có độ trễ cổng; lợi ích thật là chu kỳ xung nhịp ngắn hơn, vì mỗi tầng chỉ làm một việc." |

---

## C. Kết thúc (nói 20 giây)

"Em đã làm đủ tập lệnh RV32I, hai CPU (single-cycle và pipeline), kiểm thử từng module, chương trình mẫu, và so sánh với bộ mô phỏng độc lập."

---

## D. Nếu có sự cố

| Sự cố | Cách xử lý nhanh |
|---|---|
| Bấm Ctrl+F9 mà không có gì xảy ra | Dùng menu **Simulate > Manual Tick Full Cycle**; nếu Auto-Tick đang bật thì tắt bằng Ctrl+K |
| Giá trị lệch so với bảng | **Ctrl+R**, làm lại từ bước đó, bấm chậm từng lần |
| Mạch `Pipeline` quá rộng | Dùng nút thu phóng và thanh cuộn, xem lần lượt từng tầng từ trái sang phải |
| Mạch không chạy sau khi đã dừng | **Ctrl+R** (Reset Simulation); kiểm tra chân `PAUSE` = 0 |
| Trình duyệt không hiện sơ đồ luồng | Cần mạng để tải thư viện; các phần khác vẫn chạy bình thường |
| Lệnh `java` báo lỗi phiên bản | Dùng `& "C:\Program Files\Java\jdk-21.0.12.1\bin\java.exe" -jar .\logisim-evolution-4.1.0-all.jar .\RiscVComputer.circ` |

---

## E. Thầy hay hỏi

- **Pipeline khác single-cycle thế nào?** Single-cycle xong một lệnh trong một chu kỳ; pipeline chia thành 5 tầng để 5 lệnh chạy chồng nhau.
- **Forwarding là gì?** Lấy kết quả của lệnh trước ngay từ thanh ghi pipeline thay vì chờ ghi vào register file.
- **Vì sao load-use phải stall?** Dữ liệu của lệnh load chỉ có ở cuối tầng MEM, lệnh sau cần nó ở tầng EX nên phải chờ 1 chu kỳ.
- **Branch mất bao nhiêu chu kỳ?** Rẽ nhánh được rẽ mất 2 chu kỳ (hủy 2 lệnh đã nạp); không rẽ thì không mất gì.
- **Làm sao biết CPU đúng?** Test từng module bằng test-vector, 7 chương trình so với bộ mô phỏng độc lập, và chương trình ngẫu nhiên.

Giải thích đầy đủ hơn: `docs/vi/PRESENTATION.md` và `docs/vi/DEMO_EXPLAIN.md`.
