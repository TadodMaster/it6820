"""Vietnamese explanation blocks for every circuit of RiscVComputer.circ.

For each circuit a block of Logisim Text components is added below the existing content:
what the name stands for, what the circuit is for, what its pins mean, the cases that can happen and why it is built this way.
Called from build_all.py after the circuits are generated (before the fonts are normalised).
"""
import re
from xml.sax.saxutils import quoteattr

H = "#"   # a line that starts with '#' is a heading (bold)

NOTES = {
"InstructionDecode": [
    "# GIẢI MÃ LỆNH (InstructionDecode) - cắt lệnh 32 bit thành các trường",
    "Viết tắt: opcode = Operation Code (mã thao tác); rd = Destination Register (thanh ghi đích); rs1, rs2 = Source Register 1, 2 (thanh ghi nguồn).",
    "Mục đích: tách các trường của lệnh RISC-V ra thành các dây riêng để các khối sau dùng (đọc thanh ghi, điều khiển, ALU).",
    "opcode = bit 6..0 (7 bit): cho biết lệnh thuộc nhóm nào (cộng trừ, load, store, rẽ nhánh, nhảy...).",
    "rd = bit 11..7 (5 bit): số thanh ghi sẽ được ghi kết quả (x0..x31).   funct3 = bit 14..12 (3 bit): chọn biến thể trong nhóm (vd beq/bne/blt).",
    "rs1 = bit 19..15, rs2 = bit 24..20 (5 bit mỗi trường): số thanh ghi cần đọc.   funct7 = bit 31..25 (7 bit): phân biệt ADD/SUB, SRL/SRA.",
    "Các trường hợp: lệnh kiểu U (lui, auipc) và J (jal) không có rs1/rs2/funct3 thật; các bit đó vẫn được cắt ra nhưng các khối sau bỏ qua.",
    "Vì sao không có cổng logic: RISC-V đặt các trường ở vị trí cố định, nên giải mã chỉ là đi dây (một splitter), rất nhanh và rẻ.",
],
"MainControl": [
    "# ĐIỀU KHIỂN CHÍNH (MainControl) - từ opcode sinh mọi tín hiệu điều khiển",
    "Viết tắt: RegWrite = ghi thanh ghi; ALUSrc = nguồn của toán hạng B; MemWrite/MemRead = ghi/đọc RAM; IsBranch/IsJAL/IsJALR = lệnh rẽ nhánh/nhảy.",
    "ALUOp (2 bit) = nhóm phép ALU: 00 cộng (load, store, lui, auipc, jalr), 01 trừ (branch), 10 kiểu R, 11 kiểu I (ALUControl chọn tiếp theo funct3/funct7).",
    "ImmSel (3 bit) = kiểu hằng số: 000 I, 001 S, 010 B, 011 U, 100 J.   ASel (2 bit) = toán hạng A: 00 rs1, 01 PC (auipc), 10 số 0 (lui).",
    "WBSel (2 bit) = giá trị ghi vào rd: 00 kết quả ALU, 01 dữ liệu RAM (load), 10 PC+4 (jal, jalr = địa chỉ trả về).",
    "Cách làm: 9 bộ so sánh 7 bit (mỗi opcode một cái) cho ra cờ của từng nhóm lệnh; cổng OR gộp cờ thành tín hiệu: vd RegWrite = R hoặc I hoặc load hoặc lui hoặc auipc hoặc jal hoặc jalr.",
    "Các trường hợp: opcode lạ (không thuộc 9 nhóm) -> mọi tín hiệu = 0, lệnh không làm gì (NOP an toàn). store/branch không ghi thanh ghi (RegWrite = 0).",
    "Vì sao so sánh từng opcode: mỗi dòng của bảng opcode hiện ra thành một bộ so sánh, dễ đọc và dễ kiểm tra (tests/maincontrol.vec).",
],
"ImmGen": [
    "# SINH HẰNG SỐ (ImmGen = Immediate Generator) - dựng hằng số tức thời 32 bit",
    "Viết tắt: imm = immediate = hằng số nằm ngay trong lệnh (không phải đọc từ thanh ghi).",
    "Mục đích: mỗi kiểu lệnh cất hằng số ở chỗ khác nhau và bị xáo bit; khối này gom lại đúng thứ tự rồi mở rộng dấu thành 32 bit.",
    "ImmSel chọn kiểu: 000 I (addi, load, jalr: 12 bit), 001 S (store: 12 bit), 010 B (branch: 13 bit, bit 0 = 0), 011 U (lui, auipc: imm << 12), 100 J (jal: 21 bit, bit 0 = 0).",
    "Mở rộng dấu (sign extension): bit cao nhất của hằng số được chép vào các bit trên, nên số âm vẫn âm (vd -8 = 0xFFFFFFF8).",
    "Các trường hợp: B và J luôn chẵn (bit 0 = 0) vì lệnh dài 4 byte; U không mở rộng dấu mà chèn 12 bit 0 vào cuối.",
    "Vì sao xáo bit: để bit dấu luôn ở bit 31 của lệnh và nhiều bit nằm cùng vị trí giữa các kiểu, nên mạch giải mã đơn giản hơn.",
],
"RegisterFile": [
    "# TẬP THANH GHI (RegisterFile) - 32 thanh ghi x0..x31, mỗi thanh ghi 32 bit",
    "Viết tắt: x0..x31 = 32 thanh ghi của RISC-V; rd = thanh ghi đích; rs1/rs2 = thanh ghi nguồn; write = RegWrite (cho phép ghi); CLK = xung nhịp.",
    "Đọc: hai cổng đọc độc lập (rs1 -> rs1_data, rs2 -> rs2_data), đọc bất đồng bộ (đổi số thanh ghi là giá trị ra ngay, không chờ xung).",
    "Ghi: nếu write = 1 thì ở cạnh xung nhịp, write_data được ghi vào thanh ghi số rd (bộ DEMUX bật tín hiệu cho phép ghi của đúng một thanh ghi).",
    "Các trường hợp: write = 0 -> không thanh ghi nào đổi (store, branch). rd = 0 -> x0 không đổi, luôn bằng 0 (hằng số 0). Đọc và ghi cùng thanh ghi trong một chu kỳ -> đọc giá trị cũ.",
    "Trong pipeline: khối này nhận xung nhịp ĐẢO (CLK_n) nên ghi ở cạnh xuống: lệnh ở WB ghi nửa đầu chu kỳ, lệnh ở ID đọc nửa sau -> thấy giá trị mới.",
    "Vì sao 32 thanh ghi riêng + mux: mỗi thanh ghi là một hộp có nhãn, nhìn thấy được trong tab State của Logisim.",
],
"ALUControl": [
    "# ĐIỀU KHIỂN ALU (ALUControl) - đổi ALUOp, funct3, funct7 thành mã ALUCtrl 4 bit",
    "Viết tắt: ALU = Arithmetic Logic Unit (khối số học - logic); ALUCtrl = mã chọn phép tính của ALU.",
    "Mã ALUCtrl: 0 ADD (cộng), 1 SUB (trừ), 2 AND, 3 OR, 4 XOR, 5 SLL (dịch trái), 6 SRL (dịch phải logic), 7 SRA (dịch phải số học), 8 SLT (so sánh có dấu), 9 SLTU (không dấu).",
    "ALUOp = 00 -> luôn ADD (tính địa chỉ load/store, lui, auipc, jalr). ALUOp = 01 -> luôn SUB (so sánh cho branch). ALUOp = 10 -> tra bảng kiểu R. ALUOp = 11 -> tra bảng kiểu I.",
    "Kiểu R: funct3 chọn phép; funct7 bit 5 = 1 biến ADD thành SUB và SRL thành SRA. Kiểu I: chỉ lệnh dịch (slli, srli, srai) xét funct7 bit 5; addi bỏ qua funct7.",
    "Vì sao hai tầng điều khiển (MainControl -> ALUOp -> ALUControl): mỗi bảng nhỏ, kiểm thử riêng được (tests/alucontrol.vec).",
],
"ALU": [
    "# ALU (Arithmetic Logic Unit = khối số học - logic) - tính kết quả theo mã ALUCtrl",
    "Vào: rs1_data = toán hạng A, rs2_data = toán hạng B, ALU_Ctrl = mã phép tính. Ra: result = kết quả 32 bit.",
    "Cách làm: mọi phép tính (cộng, trừ, AND, OR, XOR, dịch trái, dịch phải logic, dịch phải số học, SLT, SLTU) chạy song song; một multiplexer 16 ngả chọn một kết quả theo ALU_Ctrl.",
    "SLT/SLTU = Set Less Than (đặt 1 nếu A < B, ngược lại 0): SLT so sánh có dấu (-1 < 1), SLTU không dấu (0xFFFFFFFF > 1). Kết quả 1 bit được mở rộng 0 thành 32 bit.",
    "Các lệnh dịch chỉ dùng 5 bit thấp của B (B[4:0], tối đa dịch 31). SRA giữ nguyên bit dấu, SRL chèn bit 0.",
    "Các trường hợp: tràn số khi cộng/trừ bị bỏ qua (kết quả quấn vòng 32 bit, đúng theo RISC-V). Mã ALU_Ctrl không dùng (10..15) -> kết quả không xác định, không xảy ra vì ALUControl chỉ sinh 0..9.",
    "Vì sao tính song song rồi chọn: đơn giản, dễ đọc; tốc độ không quan trọng trong Logisim (không mô phỏng độ trễ cổng).",
],
"BranchUnit": [
    "# ĐƠN VỊ RẼ NHÁNH (BranchUnit) - quyết định lệnh rẽ nhánh có được rẽ không",
    "Viết tắt: beq = branch if equal (rẽ nếu bằng); bne = not equal (khác); blt = less than (nhỏ hơn, có dấu); bge = greater or equal (lớn hơn hoặc bằng, có dấu); bltu/bgeu = như blt/bge nhưng không dấu.",
    "Vào: rs1_data, rs2_data (hai giá trị cần so), IsBranch (đây có phải lệnh branch), funct3 (chọn phép so). Ra: branch_taken = 1 nếu phải rẽ.",
    "Cách làm: một bộ so sánh không dấu và một có dấu cho ra '=', '<'; cổng NOT cho ra '!=', '>='; multiplexer theo funct3 chọn điều kiện: 000 beq, 001 bne, 100 blt, 101 bge, 110 bltu, 111 bgeu.",
    "Các trường hợp: funct3 = 010 hoặc 011 (không có lệnh branch như vậy) -> điều kiện = 0, không rẽ. IsBranch = 0 (lệnh khác) -> branch_taken = 0 dù hai giá trị thế nào.",
    "Khi branch_taken = 1, PC kế tiếp = PC + hằng số B (xem mạch main / Pipeline).",
],
"LoadExtract": [
    "# TRÍCH DỮ LIỆU LOAD (LoadExtract) - lấy byte / nửa từ ra khỏi từ 32 bit và mở rộng",
    "Viết tắt: lb = load byte (nạp 1 byte, mở rộng dấu); lh = load halfword (nửa từ 16 bit, mở rộng dấu); lw = load word (cả từ 32 bit); lbu/lhu = như lb/lh nhưng mở rộng 0 (không dấu).",
    "Vào: dữ liệu cả từ đọc từ RAM, Address[1:0] (byte nào trong từ), funct3 (loại lệnh load). Ra: giá trị 32 bit đưa về thanh ghi.",
    "funct3: 000 lb, 001 lh, 010 lw, 100 lbu, 101 lhu. Byte được chọn bằng Address[1:0], nửa từ bằng Address[1].",
    "Các trường hợp: lb với byte 0x80 -> 0xFFFFFF80 (mở rộng dấu), lbu cùng byte -> 0x00000080. lw lấy nguyên từ, không cần mở rộng.",
    "Vì sao cần khối này: RAM của dự án đọc nguyên từ 32 bit, nên việc cắt byte/nửa từ phải làm riêng.",
],
"StoreMerge": [
    "# GHÉP DỮ LIỆU STORE (StoreMerge) - tạo từ mới để ghi vào RAM (đọc - sửa - ghi)",
    "Viết tắt: sb = store byte (ghi 1 byte); sh = store halfword (ghi nửa từ); sw = store word (ghi cả từ). size = độ rộng lệnh store (funct3[1:0]): 00 byte, 01 nửa từ, 10 từ.",
    "Vấn đề: RAM chỉ ghi nguyên từ 32 bit. Nên khi ghi 1 byte phải giữ lại 3 byte cũ: đọc từ cũ, thay đúng làn byte, ghi cả từ trở lại.",
    "Cách làm: ROM 16 hàng x 4 bit đổi {size, Address[1:0]} thành 4 bit cho phép từng làn byte (byte: 0001 0010 0100 1000, nửa từ: 0011 1100, từ: 1111). Mỗi làn chọn byte mới hoặc byte cũ.",
    "Các trường hợp: sw -> cả 4 làn lấy dữ liệu mới. sb vào byte 1 -> chỉ làn 1 lấy byte thấp của write_data, các làn khác giữ byte cũ. sh -> 2 làn.",
    "Ví dụ: từ cũ 0x11223344, sb 0xAA vào byte 1 -> từ mới 0x1122AA44.",
],
"Memory": [
    "# BỘ NHỚ DỮ LIỆU (Memory) - RAM 256 từ x 32 bit cùng LoadExtract và StoreMerge",
    "Viết tắt: RAM = Random Access Memory (bộ nhớ đọc ghi, mất dữ liệu khi tắt). Address[9:2] = chỉ số từ (0..255), Address[1:0] = byte trong từ.",
    "Vào: Address (địa chỉ từ ALU), write_data (dữ liệu của lệnh store), MemWrite (cho phép ghi), CLK (xung nhịp), funct3 (loại load/store). Ra: read_data (dữ liệu cho lệnh load).",
    "Đọc: bất đồng bộ - địa chỉ vừa đổi là dữ liệu ra ngay trong cùng chu kỳ (lệnh load cần vậy). Ghi: chỉ khi MemWrite = 1, ở cạnh lên của xung nhịp.",
    "Các trường hợp: lệnh không phải load/store -> MemWrite = 0 nên RAM không đổi; read_data vẫn có giá trị nhưng bị bỏ qua. Địa chỉ >= 1 KiB quấn vòng (chỉ dùng Address[9:2]).",
    "Vì sao RAM đọc bất đồng bộ: RAM đọc đồng bộ chỉ trả dữ liệu sau cạnh xung kế tiếp; khi đó load trả dữ liệu không xác định (lỗi đã gặp và sửa).",
],
"ForwardingUnit": [
    "# ĐƠN VỊ CHUYỂN TIẾP (ForwardingUnit) - lấy toán hạng mới nhất cho tầng EX",
    "Viết tắt: forwarding = chuyển tiếp (bypass): đưa kết quả từ tầng sau về tầng EX mà không chờ ghi vào thanh ghi. EX/MEM, MEM/WB = thanh ghi pipeline giữa các tầng.",
    "Vấn đề: lệnh trước chưa kịp ghi vào register file thì lệnh sau đã cần dùng giá trị đó (phụ thuộc dữ liệu, RAW = Read After Write).",
    "Vào: rs1_ex, rs2_ex (thanh ghi lệnh ở EX cần đọc), rd_mem/RegWrite_mem (đích của lệnh ở MEM), rd_wb/RegWrite_wb (đích của lệnh ở WB). Ra: ForwardA, ForwardB (2 bit).",
    "Forward = 10: lấy từ EX/MEM (lệnh ngay trước). Forward = 01: lấy từ MEM/WB (lệnh cách một). Forward = 00: lấy từ register file (không phụ thuộc).",
    "Các trường hợp: cả hai tầng cùng ghi thanh ghi mà EX cần -> ưu tiên EX/MEM vì mới hơn. rd = 0 (x0) -> không forward, vì x0 luôn bằng 0. RegWrite = 0 (store, branch) -> không forward.",
    "Lưu ý: giá trị lấy từ EX/MEM là kết quả ALU, riêng jal/jalr là PC+4. Phụ thuộc vào lệnh load ngay trước không giải quyết được bằng forwarding -> cần stall (HazardUnit).",
],
"HazardUnit": [
    "# ĐƠN VỊ HAZARD (HazardUnit) - phát hiện 'load-use' và yêu cầu dừng pipeline (stall)",
    "Viết tắt: hazard = rủi ro/xung đột trong pipeline; load-use = lệnh dùng ngay giá trị vừa load; stall = dừng một chu kỳ; bubble = 'bong bóng' (lệnh rỗng NOP chèn vào).",
    "Vấn đề: lệnh load chỉ có dữ liệu ở cuối tầng MEM, nên lệnh liền sau cần nó ở EX sẽ chậm một nhịp; forwarding không cứu được.",
    "Vào: MemRead_ex, rd_ex (lệnh ở EX có phải load và đích là gì), rs1_id, rs2_id (thanh ghi nguồn của lệnh ở ID). Ra: stall = 1 nếu cần dừng.",
    "stall = (lệnh ở EX là load) VÀ (rd_ex khác x0) VÀ (rd_ex = rs1_id HOẶC rd_ex = rs2_id).",
    "Khi stall = 1: PC và thanh ghi IF/ID giữ nguyên (run = 0), còn từ điều khiển đưa vào ID/EX bị xóa thành 0 (bubble); chu kỳ sau forwarding lấy dữ liệu từ MEM/WB.",
    "Các trường hợp: load rồi một lệnh không liên quan rồi mới dùng -> không stall. rd_ex = x0 -> không stall. Chi phí: đúng 1 chu kỳ.",
],
"main": [
    "# CPU SINGLE-CYCLE (main) - mỗi lệnh chạy trọn vẹn trong MỘT chu kỳ xung nhịp",
    "BẢNG VIẾT TẮT: PC = Program Counter (bộ đếm chương trình: địa chỉ lệnh đang chạy). ROM = Read Only Memory (bộ nhớ lệnh chỉ đọc). RAM = bộ nhớ dữ liệu đọc/ghi.",
    "IF = Instruction Fetch (nạp lệnh). ID = Instruction Decode (giải mã, đọc thanh ghi). EX = Execute (thực thi ở ALU). MEM = Memory access (truy cập RAM). WB = Write Back (ghi kết quả vào thanh ghi).",
    "RISC-V RV32I = tập lệnh cơ sở 32 bit số nguyên. imm = hằng số trong lệnh. rd/rs1/rs2 = thanh ghi đích/nguồn 1/nguồn 2. funct3/funct7 = trường chọn biến thể lệnh. NOP = không làm gì.",
    "PC kế tiếp: lệnh thường -> PC + 4. branch được rẽ hoặc jal -> PC + hằng số (PC + imm). jalr -> (rs1 + imm) với bit 0 bị xóa (AND 0xFFFFFFFE).",
    "Các trường hợp theo lệnh: R (add...) ghi ALU vào rd. I (addi...) dùng imm. load: ALU tính địa chỉ, ghi dữ liệu RAM vào rd. store: ghi rs2 vào RAM. branch: so rs1, rs2. lui/auipc/jal/jalr dùng ASel và WBSel.",
    "RESET = 1 giữ PC ở 0. Ctrl+F9 = một chu kỳ = một lệnh. Các probe ở trên cho thấy lệnh sắp chạy và kết quả của nó; tab State cho thấy giá trị thanh ghi sau khi lệnh xong.",
    "Vì sao có mạch này: là CPU đơn giản nhất để hiểu; mạch pipeline dùng lại cùng các khối.",
],
"Pipeline": [
    "# CPU PIPELINE 5 TẦNG (Pipeline) - năm lệnh được xử lý cùng lúc, mỗi lệnh ở một tầng",
    "BẢNG VIẾT TẮT: IF = Instruction Fetch (nạp lệnh), ID = Instruction Decode (giải mã), EX = Execute (thực thi), MEM = Memory access (truy cập RAM), WB = Write Back (ghi lại).",
    "IF/ID, ID/EX, EX/MEM, MEM/WB = bốn thanh ghi pipeline giữa các tầng, giữ mọi thứ lệnh cần ở tầng sau. Hậu tố _id _ex _mem _wb trong tên dây = tín hiệu của lệnh đang ở tầng đó.",
    "Hazard = xung đột giữa các lệnh đang chạy chồng nhau. Forwarding = chuyển tiếp kết quả về EX. Stall = dừng 1 chu kỳ. Bubble = lệnh rỗng NOP. Flush = hủy các lệnh đã nạp nhầm. CPI = số chu kỳ trên mỗi lệnh.",
    "Hazard dữ liệu: lệnh sau cần giá trị lệnh trước chưa ghi xong -> ForwardingUnit lấy từ EX/MEM (Forward = 10) hoặc MEM/WB (01); riêng load rồi dùng ngay -> HazardUnit stall 1 chu kỳ.",
    "Hazard điều khiển: branch/jal/jalr được quyết định ở EX (pc_src_ex = 1) -> PC nhảy tới đích, hai lệnh đã nạp phía sau bị flush thành bubble: mất 2 chu kỳ. Branch không rẽ: không mất gì.",
    "Từ điều khiển (control word): các tín hiệu điều khiển sinh một lần ở ID, đóng gói rồi đi cùng lệnh qua các thanh ghi pipeline; mỗi tầng tách phần mình cần (13 bit ở ID/EX, 5 bit ở EX/MEM, 3 bit ở MEM/WB).",
    "CLK_n = xung nhịp đảo: register file ghi ở cạnh xuống, nên lệnh ở WB ghi và lệnh ở ID đọc trong cùng chu kỳ vẫn thấy giá trị mới.",
    "Xem hiệu quả: bấm Ctrl+F9; các hàng probe ở dưới cho thấy stall, pc_src_ex, ForwardA/B và dữ liệu đi qua từng tầng. Chương trình thử hazard: programs/hazards_demo.hex.",
    "Vì sao pipeline: chu kỳ xung nhịp có thể ngắn hơn (mỗi tầng chỉ làm một việc); trong Logisim không mô phỏng độ trễ nên số chu kỳ trông không giảm.",
],
}


def _extent(block):
    xs, ys = [], []
    for m in re.finditer(r'loc="\((-?\d+),(-?\d+)\)"', block):
        xs.append(int(m.group(1)))
        ys.append(int(m.group(2)))
    for m in re.finditer(r'<wire from="\((-?\d+),(-?\d+)\)" to="\((-?\d+),(-?\d+)\)"', block):
        xs += [int(m.group(1)), int(m.group(3))]
        ys += [int(m.group(2)), int(m.group(4))]
    return (min(xs), max(xs), min(ys), max(ys)) if xs else (0, 0, 0, 0)


def annotate(proj):
    """Append the Vietnamese notes below the content of every circuit that has an entry in NOTES."""
    done = []
    for name, lines in NOTES.items():
        blk = proj.block(name)
        if blk is None:
            continue
        x0, x1, y0, y1 = _extent(blk)
        x0 = max(x0, 50) // 10 * 10
        y = (y1 + 110) // 10 * 10
        body = ""
        for ln in lines:
            head = ln.startswith(H)
            s = ln[1:].strip() if head else ln
            cx = (x0 + int(len(s) * (4.3 if head else 3.6)) + 20) // 10 * 10
            font = "Monospaced bold 14" if head else "Monospaced plain 12"
            body += (f'    <comp lib="9" loc="({cx},{y})" name="Text">\n'
                     f'      <a name="font" val={quoteattr(font)}/>\n'
                     f'      <a name="text" val={quoteattr(s)}/>\n    </comp>\n')
            y += 30 if head else 24
        i = blk.rindex("  </circuit>")
        proj.set(name, blk[:i] + body + blk[i:])
        done.append(name)
    return done
