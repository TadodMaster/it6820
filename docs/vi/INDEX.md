# Mục lục tài liệu

> Bản tiếng Việt của docs/INDEX.md.

| Tài liệu | Đối tượng | Nội dung |
|---|---|---|
| [README.md](README.md) | mọi người | dự án là gì, bắt đầu nhanh, các lệnh, kết quả kiểm thử |
| [GUIDE.md](GUIDE.md) | người mới, đồng đội, giám khảo | phần giải thích đầy đủ: kiến thức cơ bản về CPU, từng khối, giá trị tín hiệu thực tế, pipeline, hiệu năng, chương trình, kiểm thử, xử lý sự cố, bảng thuật ngữ |
| [REPORT.md](REPORT.md) | người chấm | báo cáo kỹ thuật chính thức theo yêu cầu của đề bài |
| [COMPONENTS.md](COMPONENTS.md) | người xây dựng mạch | từng loại component: các thiết lập đã dùng, tên của từng thiết lập trong giao diện Logisim, lý do, các cạm bẫy; các quyết định thiết kế; công thức để tự dựng lại một khối bằng tay |
| [BOM.md](BOM.md) | người xây dựng mạch | bảng kê vật tư được sinh tự động: mọi component của mọi circuit cùng cấu hình của nó |
| [TOOLS.md](TOOLS.md) | lập trình viên | cách hoạt động của assembler, trình mô phỏng, headless runner, bộ sinh circuit và bộ kiểm tra |
| [DESIGN_LOG.md](DESIGN_LOG.md) | lập trình viên | lịch sử thiết kế và các cạm bẫy đã gặp |
| [DEMO.md](DEMO.md) | người thuyết trình | kịch bản và danh sách kiểm tra cho video demo / demo trực tiếp |
| [DEMO_EXPLAIN.md](DEMO_EXPLAIN.md) | người thuyết trình, đồng đội | mọi thứ xảy ra trong demo: từng lệnh, từng tick, pipeline từng chu kỳ |
| [../latex/KienTruc_RV32I.tex](../latex/KienTruc_RV32I.tex) | người học | tài liệu \LaTeX{} tiếng Việt học từng bước từng khối, có hình TikZ (biên dịch bằng pdfLaTeX); kế hoạch tiếng Anh: [../LEARNING_PLAN.md](../LEARNING_PLAN.md) |
| [TEAM_SPLIT.md](TEAM_SPLIT.md) | nhóm ba người | ai học circuit nào, cần giải thích gì, câu hỏi có thể gặp |
| [REQUIREMENTS.md](REQUIREMENTS.md) | mọi người | đề bài (tiếng Việt) kèm trạng thái của từng mục |
| [commands.txt](commands.txt) | mọi người | các lệnh để sao chép và dán |
| `img/` | - | hình của mọi circuit (sinh bởi `tools/java/Render.java`) |

## Thứ tự đọc gợi ý

* **"Tôi muốn hiểu chiếc máy tính này"**: GUIDE phần 1 -> 5, rồi 6 (bộ nhớ), 7 -> 8 (pipeline).
* **"Tôi phải thuyết trình nó"**: README phần bắt đầu nhanh, DEMO.md, GUIDE phần 5 và 8 (các vết thực tế để nói về).
* **"Tôi phải viết / chấm báo cáo"**: REPORT.md; các hình nằm trong `img/`; GUIDE phần 9 cho các số đo.
* **"Chính xác thì các circuit được cấu hình những gì, và vì sao?"**: COMPONENTS.md (theo loại component), rồi BOM.md (theo circuit).
* **"Tôi muốn thay đổi một thứ gì đó"**: GUIDE phần 12, rồi TOOLS phần 5 (bộ sinh circuit), rồi chạy các bài kiểm thử.

## Mỗi thứ nằm ở đâu (sơ đồ kho mã)

```
RiscVComputer.circ       the project: circuits main (single-cycle) and Pipeline + all blocks
programs/                demo.s (in the ROM), hazards_demo.s, .hex images
tests/                   *.vec module tests, programs/*.s, run_tests.ps1, run_cpu_tests.py, fuzz.py
tools/rv.py              assembler + reference simulator
tools/java/              Run, Render, Ends (Java helpers);  tools/compile.ps1 builds them into tools/bin
tools/probe.py           show / trace named signals of a running circuit
tools/build/             circuit generator (blocks.py, cpus.py, pipeline.py ...) and base.circ (hand-drawn blocks)
docs/                    this documentation
backup/                  earlier versions of the .circ file
logisim-mcp/             MCP server that lets an AI assistant read / test circuits
```

## Các phần ghép với nhau thế nào (một hình)

```
        write assembly                 run                       compare
  programs/*.s ---> tools/rv.py asm ---> .hex ---> circuit (main / Pipeline) via Run.java  \
        |                                                                                   +--> tests pass / fail
        +--------> tools/rv.py sim  (reference simulator) ---------------------------------/

  tools/build (netlists) --> RiscVComputer.circ --> Logisim GUI (poke, tick, look inside)
```
