# Tài liệu tham khảo về công cụ: toolchain hoạt động bên trong như thế nào

> Bản tiếng Việt của docs/TOOLS.md.

Mọi thứ không phải là mạch đều nằm trong `tools/` và `tests/`.  Trang này giải thích từng công cụ: mục đích, cách dùng, cách hoạt động và các giới hạn.
Về bản thân CPU, hãy đọc [GUIDE.md](GUIDE.md).

```
programs/*.s --rv.py asm--> *.hex --(ROM contents)--> circuit
                  |                                      |
                  +--rv.py sim (reference)               +--Run.java (headless run) --> registers / memory
                            \                                         /
                             +------------- compare ------------------+   tests/run_cpu_tests.py, tests/fuzz.py

tools/build/*.py --(netlists)--> RiscVComputer.circ --Ends.java--> pin positions   (used while generating)
                                        |
                                        +--Render.java--> docs/img/*.png
                                        +--verify.py  (checks the saved nets)
```

| Công cụ | Tệp | Yêu cầu |
|---|---|---|
| Trình hợp dịch (assembler) + mô phỏng tham chiếu | `tools/rv.py` | Python 3.10 |
| Trình chạy không giao diện (headless) | `tools/java/Run.java` | JDK 21 + tệp jar của Logisim |
| Dò / theo dõi net | `tools/probe.py` | các mục trên |
| Trình vẽ (PNG của một mạch) | `tools/java/Render.java` | các mục trên |
| Xuất vị trí chân (pin) | `tools/java/Ends.java` | các mục trên |
| Bộ sinh mạch | `tools/build/` | các mục trên |
| Các trình chạy kiểm thử | `tests/run_tests.ps1`, `tests/run_cpu_tests.py`, `tests/fuzz.py` | các mục trên |

Đặt biến môi trường `JAVA` thành đường dẫn `java.exe` của JDK 21 nếu `java` trong PATH cũ hơn (`$env:JAVA = "C:\Program Files\Java\jdk-21.0.12.1\bin\java.exe"`).
`powershell -File tools\compile.ps1` biên dịch các tệp Java vào `tools/bin` (cần `javac`).

---

## 1. `tools/rv.py` - trình hợp dịch và mô phỏng tham chiếu

`python tools/rv.py asm prog.s [-o prog.hex] [-l]` và `python tools/rv.py sim prog.s [-n max_steps]`.  Cũng có thể import (`import rv`):
`rv.assemble(text) -> (words, listing, labels)`, `rv.Sim(words)`, `rv.to_hex(words)`.

### Trình hợp dịch
Hai lượt:
1. **Lượt 1** đọc các dòng, loại bỏ chú thích (`#` hoặc `;`), thu thập nhãn (`name:` cho địa chỉ của lệnh *máy* kế tiếp) và **khai triển các lệnh giả (pseudo instruction)** thành
   lệnh thật.  Vì `li` có thể khai triển thành một hoặc hai lệnh, địa chỉ chỉ biết được sau khi khai triển.
2. **Lượt 2** mã hóa mọi lệnh theo bố cục bit của RV32I (`enc_r`, `enc_i`, `enc_s`, `enc_b`, `enc_u`, `enc_j`); toán hạng nhãn trở thành `label - current address`
   cho lệnh rẽ nhánh và nhảy.  Các lỗi phạm vi (immediate quá lớn, rẽ nhánh quá xa, offset lẻ) phát sinh `AsmError` kèm số dòng.

`li rd, v` trở thành `addi rd, x0, v` nếu `v` vừa 12 bit, nếu không thì `lui rd, hi` + `addi rd, rd, lo`, trong đó `lo` là 12 bit thấp được mở rộng dấu và `hi` được hiệu chỉnh +1 khi `lo` âm.
`chk rd, v` là macro tự kiểm tra cho các bài test (`li x30, v` + `bne rd, x30, fail`).

Định dạng đầu ra (ảnh bộ nhớ "raw" của Logisim): dòng đầu `v2.0 raw`, sau đó mỗi dòng một từ 32 bit dạng hex (Logisim cũng chấp nhận nhiều từ trên một dòng).

### Mô phỏng tham chiếu (`rv.Sim`)
Một mô hình Python thuần của kiến trúc, cố ý độc lập với các mạch:
* 32 thanh ghi (x0 bị ép bằng 0), PC, ROM 256 từ, bộ nhớ dữ liệu 256 từ (`(addr >> 2) & 0xFF`, nên địa chỉ quay vòng giống phần cứng);
* `step()` giải mã opcode và thực thi (R, I, load, store, branch, LUI, AUIPC, JAL, JALR); các opcode không biết (fence, ecall) hoạt động như NOP;
* load và store dưới một từ dùng cùng cách chọn byte / halfword như phần cứng (`lh` ở địa chỉ lẻ dùng halfword đã căn hàng, giống `LoadExtract`);
* `run()` dừng khi một lệnh nhảy về chính nó (quy ước `halt: j halt`) hoặc sau `max_steps`.

Giới hạn: không có CSR, không có trap, không có ngoại lệ truy cập không căn hàng.

---

## 2. `tools/java/Run.java` - chạy chương trình trên mạch không cần GUI

```
java -cp "logisim-evolution-4.1.0-all.jar;tools\bin" Run <file.circ> <circuit> <program.hex> <cycles> [trace|x] [@probe ...]
```

Cách hoạt động (dùng chính các lớp Java của Logisim):
1. `LogisimFile.load` nạp project; mạch tên `<circuit>` phải chứa đúng một ROM; thuộc tính nội dung của nó (`Rom.CONTENTS_ATTR`) bị ghi đè bằng các từ của tệp hex.
2. `CircuitState.createRootState(project, circuit, Thread.currentThread())` tạo một trạng thái mô phỏng mà propagator thuộc về *main thread* (`Project`/`Simulator`
   thông thường tạo luồng riêng và từ chối lời gọi từ nơi khác).
3. Với mỗi chu kỳ: `propagator.toggleClocks(); propagator.propagate();` hai lần (sườn lên và sườn xuống).  Thành phần `Clock` của mạch là thứ được đảo.
4. Sau khi chạy nó in `CYCLES=`, `PC=` (thanh ghi có nhãn `PC`), `x0..x31` (các thanh ghi có nhãn `x0..x31` trong trạng thái mạch con `RegisterFile`) và
   mọi từ khác 0 của RAM trong trạng thái mạch con `Memory`, dưới dạng `MEM[addr]=value`.  Các lớp trạng thái như `RegisterData` là package-private nên được đọc bằng reflection.
5. **Chế độ trace** (`trace`) in `T <cycle> PC=<hex> <probe values...>` sau mỗi chu kỳ.  **Probe** là `@x,y` (một điểm trong mạch trên cùng) hoặc `@Circuit:x,y` (bên trong một
   mạch con); giá trị của dây tại điểm đó được in ra (`U` = bit không xác định, `E` = lỗi, `-` = không có dây tại điểm đó).

Vì sao thanh ghi được gắn nhãn: bộ sinh đặt tên 32 thanh ghi là `x0..x31` và thanh ghi PC là `PC` chính là để các công cụ tìm được chúng.

## 3. `tools/probe.py` - xem các tín hiệu có tên

`python tools/probe.py [--trace] file.circ circuit prog.s cycles label...` hợp dịch chương trình, tra **tên tunnel** trong mạch để tìm vị trí dây cho từng nhãn,
và gọi `Run` với các probe đó.  Không có `--trace` thì in các giá trị sau `cycles` chu kỳ; có `--trace` thì in một bảng mỗi chu kỳ một hàng.  Ví dụ:

```powershell
python tools\probe.py RiscVComputer.circ main programs\demo.s 2 pc instr rs1_data rs2_data alu_result wb_data
python tools\probe.py --trace RiscVComputer.circ Pipeline programs\hazards_demo.s 12 pc_if pc_id pc_ex stall ForwardA
```
Giá trị nhiều bit được in dạng hex không có số 0 đứng đầu đối với bus hẹp (`0a`, `2`).  Giá trị là trạng thái *sau* số chu kỳ xung nhịp đầy đủ đã cho.

## 4. `tools/java/Render.java` và `Ends.java`

* `Render <file.circ> <outdir> <circuit|ALL> <scale>` vẽ một mạch vào `<outdir>/<circuit>.png` bằng chính mã vẽ của Logisim (`Circuit.draw`).  (Dùng từ `ALL`: trên Windows
  `java` khai triển một dấu `*` trần thành tên tệp.)
* `Ends <file.circ> [circuit]` in ra cho mỗi thành phần vị trí, hộp bao và **vị trí, độ rộng, hướng chính xác của mọi chân của nó**.  Đây là cách bộ sinh
  biết nơi nối dây: không có offset chân nào được hard-code.

---

## 5. `tools/build/` - bộ sinh mạch

`python tools/build/build_all.py <base.circ> <out.circ>` đọc thư viện vẽ tay (`base.circ`: ALU, InstructionDecode, RegisterFile, ImmGen, ALUControl), (tái) sinh mọi
mạch còn lại và ghi ra project.

| Tệp | Nội dung |
|---|---|
| `circgen.py` | engine sinh mạch: `Project` (văn bản .circ), `Circ` (một mạch đang được xây) |
| `blocks.py` | netlist của `MainControl`, `BranchUnit`, `LoadExtract`, `StoreMerge`, `Memory`, `ForwardingUnit`, `HazardUnit` |
| `cpus.py` | CPU đơn chu kỳ `main`, tìm kiếm bố cục `tightest()` |
| `pipeline.py` | pipeline 5 tầng |
| `fonts.py` | lượt cuối: mọi font trở thành `Monospaced` |
| `verify.py` | kiểm tra mọi mạch đã sinh sau khi lưu |
| `build_all.py` | trình điều khiển: vá, sinh, lưu, xác minh |

### Mô tả một mạch
```python
c = Circ(proj, "HazardUnit", spread=(1.5, 1.3))
c.pin_in("rd_ex", 5, (120, 180))                                   # circuit input pin
c.add("Comparator", (700, 300), {"width": 5, "mode": "unsigned"},  # component, location, attributes
      {"a": "rd_ex", "b": "rs1_id", "eq": "hit1"})                  # pin name -> net name
c.add("AND Gate", (1450, 300), {"inputs": 3}, {"in1": "MemRead_ex", "in2": "rd_ok", "in3": "uses", "out": "stall"})
c.pin_out("stall", 1, (1750, 300))
c.install()
```
Một **net** chỉ là một cái tên; mọi chân có cùng tên đều được nối với nhau.  `c.link(c1, "out", c2, "b")` vẽ trực tiếp một dây thay vì dùng tunnel.  Tên chân của từng thành phần nằm trong `pin_names()`
(`a b out` cho bộ cộng, `d0..dN sel out` cho bộ ghép kênh, `bus b0..` cho splitter, ...); với mạch con thì tên là nhãn của các chân bên trong chúng.

### `build()` làm gì
1. **Dò (Probe)**: ghi một project tạm chứa mọi thành phần (không có dây) và chạy `Ends` trên đó để biết vị trí chân và hộp bao thực.
2. **Độ rộng net**: độ rộng của mỗi net lấy từ các chân của nó (probe báo độ rộng 0 cho đến khi được nối, nên dùng giá trị lớn nhất).
3. **Stub và tunnel**: mỗi chân có một đoạn dây ngắn và một **tunnel** mang tên net.  Bộ định tuyến thử độ dài stub theo bước 10 px, các khúc gấp ngang, và (với chân ở trên hoặc
   dưới của thành phần) cả hai hướng, và chấp nhận cách đặt đầu tiên mà dây và hộp nhãn không chạm vào bất kỳ thành phần, stub hay nhãn nào khác.  Các chân chỉ cách nhau
   10 px (splitter, bộ ghép kênh 8 đầu vào, đầu ra của comparator) được **xòe ra**: các stub uốn về các hàng cách nhau 30 px với các cột gấp không giao nhau và mọi nhãn thẳng hàng.
4. **Chia dây**: Logisim chỉ nối dây tại các đầu mút, nên mọi dây bị chia tại các đầu mút của dây khác.
5. **Đặt văn bản**: các chú thích được đặt sau khi định tuyến và được đẩy ra khỏi mọi thứ chúng chồng lên.
6. **Lint**: sai lệch độ rộng, net không có driver, net có nhiều driver, đầu ra không dùng đều được báo; mọi tọa độ không nằm trên lưới 10 px là lỗi.
7. **Tìm kiếm bố cục** (`cpus.tightest`): hai CPU được xây với một chuỗi hệ số tỉ lệ bố cục (0.5 ... 1.15) cho đến khi bộ định tuyến tìm đủ chỗ cho mọi thứ; cái nhỏ nhất thắng.

### Bộ xác minh (`verify.py`)
Sau khi tệp được lưu, nó được đọc lại **một cách độc lập**: lấy vị trí chân từ `Ends`, nối dây tại các đầu mút và tunnel theo nhãn, rồi kiểm tra với mọi mạch đã sinh rằng
* mọi chân của một net dự định thực sự là một net điện (nếu không: "net X is split"),
* không có hai net dự định khác nhau bị nối điện với nhau ("SHORT"),
* mọi tunnel đều nằm trên một đầu mút dây.

Kiểm tra này tồn tại vì những lỗi có thật khi xây công cụ (chỗ nối chữ T hở, tunnel lệch lưới, hai tunnel trên cùng một điểm); xem [DESIGN_LOG.md](DESIGN_LOG.md).
Quá trình build thoát với mã lỗi nếu có mạch nào không đạt.

### Quy tắc chỉnh sửa
* **Không** sửa tay các mạch đã sinh trong Logisim: lần build kế tiếp sẽ ghi đè.  Hãy đổi phần mô tả Python.
* Các khối vẽ tay: mở `tools/build/base.circ` trong Logisim, sửa, lưu, build lại.
* Các loại thành phần Logisim mới cần một mục trong `LIB` (số thư viện) và `pin_names()` trong `circgen.py`.

---

**Chú thích tiếng Việt.**  `tools/build/captions_vi.py` chứa chú thích của từng linh kiện (nó làm gì ở đúng chỗ đó và vì sao), tra theo circuit và net đầu ra; `circgen.py` đặt mỗi chú thích ở chỗ trống gần nhất cạnh linh kiện (bố cục nào có chú thích không tìm được chỗ sẽ bị loại, nên bộ tìm chọn hệ số giãn lớn hơn).  Năm circuit vẽ tay được chú thích bằng `annotate_vi.annotate_components()`; khối giải thích dưới mỗi circuit lấy từ `annotate_vi.NOTES`.  Hàng probe tạo bằng `Circ.monitor()`, chữ của chúng cố định.  Không đặt radix 10 cho probe (`Ends` và Logisim bị treo): dùng 16.  Bộ tìm bố cục thu nhỏ x và y độc lập (`cpus.tightest`), nên một lần dựng lại mất khoảng 6 phút.

---

## 6. Các trình chạy kiểm thử

* `tests/run_tests.ps1 [file.circ]` - với mỗi module chạy `java -jar logisim.jar --test-vector <circuit> tests/<module>.vec <file>` và in `passed N, failed M`.
  Định dạng `.vec`: dòng tiêu đề `pin[width] ...`; mỗi hàng là một test, giá trị dạng hex `0x...` hoặc nhị phân; đầu vào và đầu ra kỳ vọng cùng nằm trên một hàng.
  Hạn chế: trong các thử nghiệm của chúng tôi, nội dung RAM không được giữ từ hàng này sang hàng sau, nên RAM được kiểm thử qua các chương trình hoàn chỉnh.
* `tests/run_cpu_tests.py [--circuit main|Pipeline|all] [--circ file] [programs]` - hợp dịch từng chương trình, chạy mô phỏng tham chiếu, chạy mạch trong
  `2 * steps + 24` chu kỳ, so sánh mọi thanh ghi và mọi từ dữ liệu khác 0, kiểm tra giá trị tự kiểm `x31 = 0x600D` (nếu chương trình dùng) và báo số chu kỳ.
* `tests/fuzz.py [--count N --seed S --length L]` - chương trình ngẫu nhiên: xem hướng dẫn, mục 11.  Các chương trình thất bại được ghi vào thư mục tạm dưới tên `fuzz_fail_<seed>.s`.

## 7. Các giới hạn đã biết của công cụ
* Trình hợp dịch không có directive nào ngoài `.word`, không có `%hi/%lo`, không có section.
* ROM chứa 256 từ; chương trình lớn hơn bị từ chối.
* `Run.java` tìm ROM, thanh ghi và RAM theo tên / nhãn; các mạch không theo cách đặt tên này (`PC`, `x0..x31`, mạch con `RegisterFile`, `Memory`) cần sửa đổi nhỏ.
* Bố cục của các mạch được sinh thiên về chức năng hơn là đẹp: tín hiệu là các tunnel có tên, không phải dây được định tuyến.
