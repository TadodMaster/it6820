# Kịch bản hazard của pipeline: chương trình `hazards_demo.s`

Trước khi chạy, cần nạp `programs\hazards_demo.hex` vào ROM của mạch `Pipeline` (chuột phải vào ROM, chọn Load Image...). ROM mặc định chứa `demo.s`, chương trình đó không có lệnh nào gây stall nên probe `stall` sẽ luôn bằng 0. Sau khi nạp, nhấn Ctrl+R, rồi nhấn Ctrl+F9 từng lần và theo dõi hàng probe ở cuối mạch (`stall`, `ForwardA`, `ForwardB`, `pc_src_ex`). Các lần bấm dưới đây được đếm từ lúc đặt lại: sau lần bấm thứ N thì mạch đang ở "tick N".

## Chương trình làm gì

```
0x00  li   x1, 100
0x04  sw   x1, 0(x0)
0x08  lw   x2, 0(x0)
0x0c  addi x3, x2, 1
0x10  add  x4, x3, x2
0x14  beq  x4, x4, skip
0x18  addi x5, x0, 1
0x1c  addi x6, x0, 2
0x20  skip: addi x7, x0, 7
0x24  halt: j halt
```

Chương trình gán x1 bằng 100, ghi giá trị đó vào bộ nhớ, rồi đọc lại vào x2. Sau đó nó tính x3 bằng x2 cộng 1, tức là 101, và x4 bằng x3 cộng x2, tức là 201. Lệnh `beq x4, x4` so sánh x4 với chính nó nên luôn rẽ nhánh, và nhảy qua hai lệnh gán x5 và x6 để tới lệnh gán x7 bằng 7. Cuối cùng chương trình dừng ở `j halt`, lệnh nhảy về chính nó, lúc này mạch tự tắt xung nhịp và chân `DONE` lên 1. Kết quả đúng là x1 = 0x64, x2 = 0x64, x3 = 0x65, x4 = 0xc9, x7 = 7, còn x5 và x6 vẫn bằng 0 vì hai lệnh gán chúng bị hủy.

## Khi nào xảy ra forwarding, stall, flush

Chương trình được viết để lần lượt gặp cả ba tình huống, theo thứ tự như sau.

**Forwarding đầu tiên, ở tick 3.** Lệnh `sw x1` cần giá trị x1 vừa được `li x1` tính xong, nhưng `li` mới đi tới tầng MEM, chưa kịp ghi vào thanh ghi. Lúc này `sw` đang ở tầng EX và `ForwardB` bằng 2: mạch lấy thẳng x1 từ thanh ghi EX/MEM đưa vào bộ ALU. Không mất chu kỳ nào.

**Stall, ở tick 4.** Lệnh `lw x2` đang ở tầng EX, còn lệnh `addi x3, x2, 1` đứng ngay sau nó, đang ở tầng ID và cần x2. Dữ liệu của `lw` chỉ có sau tầng MEM, nên không thể đi tắt kịp. Khối HazardUnit phát hiện việc này và đặt `stall` bằng 1: PC và thanh ghi IF/ID được giữ nguyên, còn tầng EX nhận một bubble, tức là một lệnh rỗng. Ở tick 5 bạn sẽ thấy PC đứng yên ở 0x10, `stall` đã về 0, và EX chứa bubble. Việc này tốn đúng một chu kỳ.

**Forwarding thứ hai, ở tick 6 và 7.** Sau khi chờ, `lw` đã đi tới tầng WB. Ở tick 6, `addi x3` đang ở EX và lấy x2 từ thanh ghi MEM/WB (`ForwardA` bằng 1). Ở tick 7, lệnh `add x4, x3, x2` đang ở EX và cần x3 mà `addi x3` vừa tính xong ở tầng MEM, nên `ForwardA` bằng 2: lấy từ thanh ghi EX/MEM. Còn x2 đã có trong register file nên không cần forward.

**Forwarding thứ ba và flush, ở tick 8.** Lệnh `beq x4, x4` đang ở EX và cần x4 từ lệnh `add x4` vừa tới MEM, nên cả `ForwardA` và `ForwardB` đều bằng 2. Đồng thời `beq` quyết định rẽ nhánh, nên `pc_src_ex` bằng 1. Lúc này hai lệnh phía sau (`addi x5` và `addi x6`) đã được nạp nhầm. Mạch hủy chúng, tức là biến thành lệnh rỗng, nên chúng không ghi gì vào thanh ghi. Ở tick 9 bạn thấy hai lệnh đó bị đánh dấu hủy, PC nhảy tới 0x20. Mất hai chu kỳ cho lần rẽ nhánh này.

**Kết thúc, ở tick 13.** Lệnh `addi x7` hoàn tất, `j halt` quay về chính nó, mạch dừng xung nhịp và `DONE` bằng 1. Lúc đó x5 và x6 vẫn bằng 0, đúng như mong đợi.

## Lời nói gợi ý khi demo

"Em nạp chương trình thử hazard vào pipeline. Ở lần bấm thứ ba, lệnh `sw` cần x1 mà lệnh `li` chưa kịp ghi, nên mạch đi tắt dữ liệu từ thanh ghi EX/MEM, không mất chu kỳ nào. Ở lần bấm thứ tư là tình huống load rồi dùng ngay: lệnh `lw` chưa có dữ liệu, nên `stall` bằng 1, PC đứng yên một chu kỳ và một bubble được chèn vào. Sau đó mạch lại dùng forwarding để lấy x2 và x3. Ở lần bấm thứ tám, lệnh rẽ nhánh được quyết định ở tầng EX, hai lệnh phía sau bị hủy, nên cuối cùng x5 và x6 vẫn bằng 0. Chương trình dừng ở lần bấm thứ mười ba, chân `DONE` lên 1."

## Chương trình mặc định `demo.s`

Chạy `demo.s` trên `Pipeline` mất 64 chu kỳ. Đã đo trên mạch thật: không có stall nào, vì không có lệnh nào dùng ngay kết quả của lệnh `lw` đứng liền trước. Vì vậy khi cần chỉ cho thầy thấy stall, hãy dùng `hazards_demo`. Trên trang web `docs\web\index.html`, tab Pipeline, chọn `hazards_demo`, các nút "forwarding (tick 3)", "stall load-use (tick 4)" và "flush (rẽ nhánh) (tick 8)" nhảy thẳng tới đúng thời điểm.
