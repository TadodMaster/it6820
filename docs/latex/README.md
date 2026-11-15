# Các file LaTeX trong thư mục này

| File | Dùng để làm gì | Nộp cho thầy? |
|---|---|---|
| **`BaoCao_RV32I.tex`** | **Báo cáo bài tập lớn** (kiến trúc, từng module, pipeline, hazard, kiểm thử, kết quả, mở rộng). Một file duy nhất, tự chứa: hình TikZ nằm ngay trong file, không cần file phụ | **Có: đây là bản nộp** |
| `KienTruc_RV32I.tex` | Tài liệu học cho nhóm: giải thích từng khối từng bước, có thí nghiệm và câu hỏi tự kiểm tra | Không (tài liệu nội bộ) |
| `HuongDan_TrinhBay.tex` | Hướng dẫn ngắn khi trình bày demo: làm gì, cho thầy xem gì, nói gì | Không (cho người thuyết trình) |

## Tạo PDF của báo cáo

**Overleaf:** tạo project mới, tải duy nhất file `BaoCao_RV32I.tex` lên, chọn **pdfLaTeX** (Menu > Compiler), bấm Recompile (chạy 2 lần để có mục lục), rồi tải PDF về.

**Trên máy:** cài MiKTeX hoặc TeX Live, rồi `pdflatex BaoCao_RV32I.tex` hai lần.

## Trước khi nộp

1. Điền trang bìa: trường, khoa, môn học, giảng viên, nhóm, thành viên.
2. Điền bảng phân công ở Phụ lục C.
3. Đọc lại một lượt; nếu muốn đổi nội dung thì sửa trong `tools/build_report_tex.py` rồi chạy `python tools/build_report_tex.py` (file `.tex` được sinh ra từ script đó, hình lấy từ `KienTruc_RV32I.tex`).
