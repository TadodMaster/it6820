#!/usr/bin/env python3
"""Build docs/latex/BaoCao_RV32I.tex: the project report (Vietnamese, LaTeX + TikZ).

The preamble, the TikZ styles and the circuit figures are taken from docs/latex/KienTruc_RV32I.tex (they compile on Overleaf);
the results chart is generated here from the measured cycle counts.

    python tools/build_report_tex.py
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "docs", "latex", "KienTruc_RV32I.tex")
OUT = os.path.join(ROOT, "docs", "latex", "BaoCao_RV32I.tex")

# ------------------------------------------------------------------ pieces of the study guide that are known to compile
guide = open(SRC, encoding="utf-8").read()
pre_end = guide.index("\\title{")
preamble = guide[:pre_end]
preamble = re.sub(r"^%.*\n", "", preamble, count=6, flags=re.M)      # drop the comment header of the guide
parts = guide.split("\\begin{figure}")[1:]
FIG = {}
names = ["big", "dec", "ctl", "imm", "rf", "alu", "mem", "main", "pipe", "fwd", "hazard", "proof"]
for n, p in zip(names, parts):
    body = p.split("\\end{figure}")[0]
    if "\\label{" not in body:
        body = body.rstrip() + f"\n\\label{{fig:{n}}}\n"
    FIG[n] = "\\begin{figure}" + body + "\\end{figure}"


# ------------------------------------------------------------------ results chart (TikZ, generated from the measured numbers)
DATA = [("demo", 39, 64), ("hazards\\_demo", 7, 13), ("alu", 91, 94), ("branch", 69, 104), ("fib", 123, 181), ("hazard", 67, 82), ("jump", 27, 38), ("mem", 69, 73)]


def chart():
    s = 4.0 / 200.0
    out = ["\\begin{figure}[htbp]", "\\centering", "\\begin{tikzpicture}[x=1cm,y=1cm]"]
    for v in range(0, 201, 50):
        out.append(f"  \\draw[gray!40] (-0.2,{v * s:.3f}) -- (14.7,{v * s:.3f});")
        out.append(f"  \\node[font=\\scriptsize,anchor=east] at (-0.25,{v * s:.3f}) {{{v}}};")
    out.append("  \\draw[thick] (-0.2,0) -- (14.7,0);")
    for i, (name, a, b) in enumerate(DATA):
        x0 = 0.2 + i * 1.8
        out.append(f"  \\fill[blue!60] ({x0:.2f},0) rectangle ({x0 + 0.7:.2f},{a * s:.3f});")
        out.append(f"  \\fill[orange!85] ({x0 + 0.75:.2f},0) rectangle ({x0 + 1.45:.2f},{b * s:.3f});")
        out.append(f"  \\node[font=\\tiny,anchor=south] at ({x0 + 0.35:.2f},{a * s:.3f}) {{{a}}};")
        out.append(f"  \\node[font=\\tiny,anchor=south] at ({x0 + 1.10:.2f},{b * s:.3f}) {{{b}}};")
        out.append(f"  \\node[font=\\scriptsize,anchor=north] at ({x0 + 0.72:.2f},-0.05) {{\\texttt{{{name}}}}};")
    out.append("  \\fill[blue!60] (0.2,4.75) rectangle (0.5,5.0); \\node[font=\\scriptsize,anchor=west] at (0.55,4.875) {single-cycle};")
    out.append("  \\fill[orange!85] (3.0,4.75) rectangle (3.3,5.0); \\node[font=\\scriptsize,anchor=west] at (3.35,4.875) {pipeline};")
    out.append("  \\node[font=\\scriptsize,rotate=90] at (-1.0,2.0) {số chu kỳ};")
    out += ["\\end{tikzpicture}",
            "\\caption{Số chu kỳ xung nhịp để hoàn tất (đến lần ghi thanh ghi cuối cùng) của hai CPU trên từng chương trình; cột thấp hơn là nhanh hơn.}",
            "\\label{fig:chart}", "\\end{figure}"]
    return "\n".join(out)


# ------------------------------------------------------------------ the report text
BODY = r"""
\begin{document}

% ===================================================================== trang bìa
\begin{titlepage}
\centering
{\large TRƯỜNG ĐẠI HỌC \underline{\hspace{6cm}}}\\[2pt]
{\large KHOA \underline{\hspace{6cm}}}\\[2.2cm]
{\Large \textbf{BÁO CÁO BÀI TẬP LỚN}}\\[0.6cm]
{\huge \textbf{THIẾT KẾ MÁY TÍNH RISC-V 32-BIT\\[4pt] TRÊN LOGISIM EVOLUTION}}\\[0.8cm]
{\large Kiến trúc tập lệnh RV32I --- CPU đơn chu kỳ và CPU pipeline 5 tầng}\\[2.5cm]
\begin{tabular}{rl}
Môn học: & \underline{\hspace{7cm}}\\[6pt]
Giảng viên hướng dẫn: & \underline{\hspace{7cm}}\\[6pt]
Nhóm thực hiện: & \underline{\hspace{7cm}}\\[6pt]
Thành viên: & \underline{\hspace{7cm}}\\[6pt]
 & \underline{\hspace{7cm}}\\[6pt]
 & \underline{\hspace{7cm}}\\
\end{tabular}
\vfill
{\large \today}
\end{titlepage}

\section*{Tóm tắt}
\addcontentsline{toc}{section}{Tóm tắt}
Báo cáo trình bày việc thiết kế, mô phỏng và kiểm thử một máy tính 32-bit theo kiến trúc tập lệnh RISC-V RV32I trên Logisim Evolution 4.1.0.
Dự án có hai CPU dùng chung các khối: một CPU \emph{đơn chu kỳ} (circuit \sig{main}) và một CPU \emph{pipeline 5 tầng} (circuit \sig{Pipeline}) xử lý
hazard dữ liệu bằng forwarding và stall load-use, hazard điều khiển bằng flush. Toàn bộ tập lệnh RV32I (trừ các lệnh hệ thống) được cài đặt, kể cả các lệnh
tùy chọn như \texttt{lb}, \texttt{lh}, \texttt{sb}, \texttt{sh}, \texttt{blt}, \texttt{bgeu}. Chương trình được nạp qua bộ nhớ lệnh nhờ một assembler tự viết.
Tính đúng đắn được kiểm chứng ở ba mức: test-vector cho 9 module (106 hàng), 7 chương trình chạy trên cả hai CPU so với một bộ mô phỏng tham chiếu viết độc lập,
và các chương trình ngẫu nhiên. Trên chương trình mẫu, CPU đơn chu kỳ cần 39 chu kỳ còn CPU pipeline cần 64 chu kỳ (CPI $=1{,}64$); sự chênh lệch đến từ mức phạt $2$ chu kỳ
cho mỗi lệnh rẽ nhánh được thực hiện, còn lợi ích của pipeline là chu kỳ xung nhịp ngắn hơn mà mô phỏng không độ trễ cổng của Logisim không thể hiện.

\tableofcontents
\newpage

% ===================================================================== 1
\section{Giới thiệu}
\subsection{Bối cảnh và mục tiêu}
Đề bài yêu cầu thiết kế, mô phỏng và kiểm thử một máy tính 32-bit dùng kiến trúc tập lệnh RISC-V, gồm CPU, bộ nhớ chương trình, bộ nhớ dữ liệu và các thành phần điều khiển.
Phiên bản cuối cùng phải là pipeline 5 tầng \textbf{IF} (nạp lệnh) $\rightarrow$ \textbf{ID} (giải mã) $\rightarrow$ \textbf{EX} (thực thi) $\rightarrow$ \textbf{MEM} (truy cập bộ nhớ)
$\rightarrow$ \textbf{WB} (ghi lại) và xử lý đúng các hazard dữ liệu, hazard điều khiển cơ bản. Công cụ bắt buộc là Logisim Evolution.

\subsection{Phạm vi và mức độ hoàn thành}
\begin{center}
\small
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{5.6cm}X@{}}
\toprule
\textbf{Yêu cầu} & \textbf{Trạng thái}\\
\midrule
Dữ liệu 32 bit, lệnh 32 bit, 32 thanh ghi $\times$ 32 bit, PC 32 bit, RV32I & đạt (\texttt{x0} luôn bằng 0)\\
ADD SUB AND OR XOR SLT SLTU SLL SRL SRA & đạt, có test\\
ADDI ANDI ORI XORI SLTI SLTIU SLLI SRLI SRAI & đạt, có test\\
LW, SW và các lệnh tùy chọn LB LH LBU LHU SB SH & đạt toàn bộ, có test\\
BEQ BNE JAL JALR và BLT BGE BLTU BGEU & đạt toàn bộ, có test\\
LUI, AUIPC & đạt, có test\\
CPU đơn chu kỳ (\sig{main}) & đạt, CPI $=1$\\
Pipeline 5 tầng, hazard dữ liệu và điều khiển (\sig{Pipeline}) & đạt: forwarding, stall load-use, flush\\
Chương trình nạp qua bộ nhớ lệnh, không gán trực tiếp thanh ghi & đạt: ảnh ROM tạo từ assembler\\
Assembler (nên có) & đạt: \texttt{tools/rv.py}\\
Test cho từng module và toàn CPU & đạt: 9 file test module, 7 chương trình, bộ fuzz ngẫu nhiên\\
Tính năng nâng cao (dự đoán rẽ nhánh, cache, nhân/chia, ngắt, GPIO/UART, số thực) & chưa làm (xem mục~\ref{sec:future})\\
\bottomrule
\end{tabularx}
\end{center}

% ===================================================================== 2
\section{Cơ sở lý thuyết}
\subsection{Tập lệnh RV32I}
RISC-V là kiến trúc tập lệnh mở, kiểu RISC (tập lệnh rút gọn). RV32I là tập cơ sở 32 bit số nguyên: 32 thanh ghi \texttt{x0..x31} (\texttt{x0} luôn bằng 0), lệnh dài cố định 4 byte,
chỉ các lệnh load/store mới truy cập bộ nhớ. Có sáu định dạng lệnh; các trường \texttt{opcode}, \texttt{rd}, \texttt{rs1}, \texttt{rs2} luôn nằm ở cùng vị trí bit, nhờ đó
có thể đọc thanh ghi trong khi còn đang giải mã opcode.

\begin{center}
\small
\setlength{\tabcolsep}{3pt}
\begin{tabular}{|c|c|c|c|c|c|c|}
\hline
\textbf{Kiểu} & \textbf{31--25} & \textbf{24--20} & \textbf{19--15} & \textbf{14--12} & \textbf{11--7} & \textbf{6--0}\\
\hline
R & funct7 & rs2 & rs1 & funct3 & rd & opcode\\
\hline
I & \multicolumn{2}{c|}{imm[11:0]} & rs1 & funct3 & rd & opcode\\
\hline
S & imm[11:5] & rs2 & rs1 & funct3 & imm[4:0] & opcode\\
\hline
B & imm[12$|$10:5] & rs2 & rs1 & funct3 & imm[4:1$|$11] & opcode\\
\hline
U & \multicolumn{4}{c|}{imm[31:12]} & rd & opcode\\
\hline
J & \multicolumn{4}{c|}{imm[20$|$10:1$|$11$|$19:12]} & rd & opcode\\
\hline
\end{tabular}
\end{center}

Chín opcode được dùng: \texttt{0x33} (R), \texttt{0x13} (I-ALU), \texttt{0x03} (load), \texttt{0x23} (store), \texttt{0x63} (branch), \texttt{0x37} (LUI),
\texttt{0x17} (AUIPC), \texttt{0x6F} (JAL), \texttt{0x67} (JALR).

\subsection{Pipeline và hazard}
Pipeline chia việc thực thi một lệnh thành nhiều tầng để nhiều lệnh chạy chồng nhau; khi không có xung đột, mỗi chu kỳ hoàn thành một lệnh (CPI $=1$) với chu kỳ xung nhịp ngắn hơn.
Các xung đột (hazard) gồm: \emph{hazard dữ liệu} (lệnh sau cần giá trị mà lệnh trước chưa ghi xong), giải quyết bằng \emph{forwarding}, và riêng trường hợp load rồi dùng ngay phải \emph{stall};
\emph{hazard điều khiển} (lệnh rẽ nhánh/nhảy làm các lệnh đã nạp phía sau là sai), giải quyết bằng \emph{flush}. Hazard cấu trúc không xảy ra vì dùng hai bộ nhớ riêng (kiến trúc Harvard).

% ===================================================================== 3
\section{Kiến trúc tổng thể}
\subsection{Tổ chức bộ nhớ và tín hiệu}
Máy tính theo tổ chức Harvard: ROM lệnh 256 từ (chỉ đọc) và RAM dữ liệu 256 từ riêng. Địa chỉ từ bằng \texttt{địa chỉ byte / 4}; PC là thanh ghi 32 bit, chỉ \sig{PC[9:2]} đánh địa chỉ ROM;
địa chỉ dữ liệu quấn vòng theo 1 KiB. Mọi tín hiệu giữa các khối đều có tên, và \textbf{các tunnel cùng tên là cùng một dây}; tên theo đặc tả RISC-V và giáo trình
(\sig{rs1}, \sig{rs2}, \sig{rd}, \sig{funct3}, \sig{imm}, \dots).

\begin{center}
\small
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{3.4cm}X@{}}
\toprule
\textbf{Tín hiệu} & \textbf{Ý nghĩa}\\
\midrule
\sig{RegWrite} & ghi \sig{rd} trong register file\\
\sig{ALUSrc} & toán hạng B của ALU: 0 là \sig{rs2}, 1 là hằng số \sig{imm}\\
\sig{ASel} (2 bit) & toán hạng A: 00 \sig{rs1}, 01 PC (AUIPC), 10 số 0 (LUI)\\
\sig{ALUOp} (2 bit) & 00 cộng, 01 trừ, 10 kiểu R, 11 kiểu I (\sig{ALUControl} tra tiếp theo \sig{funct3}/\sig{funct7})\\
\sig{ImmSel} (3 bit) & kiểu hằng số: 0 I, 1 S, 2 B, 3 U, 4 J\\
\sig{MemWrite}, \sig{MemRead} & store, load\\
\sig{WBSel} (2 bit) & giá trị ghi vào \sig{rd}: 00 ALU, 01 bộ nhớ, 10 PC$+4$\\
\sig{IsBranch}, \sig{IsJAL}, \sig{IsJALR} & lệnh rẽ nhánh / nhảy\\
\bottomrule
\end{tabularx}
\end{center}

\subsection{Các circuit của dự án}
Dự án gồm 14 circuit trong file \texttt{RiscVComputer.circ}; hai CPU dùng chung các khối datapath.
\begin{center}
\small
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{3.7cm}X@{}}
\toprule
\textbf{Circuit} & \textbf{Nhiệm vụ}\\
\midrule
\sig{main} & CPU đơn chu kỳ\\
\sig{Pipeline} & CPU pipeline 5 tầng\\
\sig{InstructionDecode} & cắt lệnh thành \sig{opcode rd funct3 rs1 rs2 funct7}\\
\sig{MainControl} & từ \sig{opcode} sinh mọi tín hiệu điều khiển\\
\sig{ImmGen} & dựng hằng số 32 bit theo \sig{ImmSel}\\
\sig{RegisterFile} & 32 thanh ghi, hai cổng đọc, một cổng ghi\\
\sig{ALUControl} & đổi \sig{ALUOp}, \sig{funct3}, \sig{funct7} thành mã \sig{ALUCtrl}\\
\sig{ALU} & tính kết quả theo \sig{ALUCtrl}\\
\sig{BranchUnit} & quyết định lệnh rẽ nhánh có được rẽ hay không\\
\sig{Memory} (cùng \sig{LoadExtract}, \sig{StoreMerge}) & RAM dữ liệu, truy cập byte, nửa từ, từ\\
\sig{ForwardingUnit} & chọn nguồn mới nhất cho toán hạng ở tầng EX\\
\sig{HazardUnit} & phát hiện load-use, phát tín hiệu stall\\
\bottomrule
\end{tabularx}
\end{center}

Hình~\ref{fig:big} cho thấy ý tưởng chung: nạp lệnh, giải mã, thanh ghi, ALU, bộ nhớ rồi ghi lại.

PHANFIG_big

% ===================================================================== 4
\section{Thiết kế các khối}
Mỗi khối là một circuit riêng, có file test-vector riêng trong thư mục \texttt{tests/} (trừ \sig{InstructionDecode} chỉ gồm dây).

\subsection{InstructionDecode}
Một splitter duy nhất cắt lệnh 32 bit thành sáu trường theo vị trí bit cố định; không có cổng logic nào. Vì \texttt{rs1}, \texttt{rs2} luôn ở cùng chỗ, thanh ghi có thể được đọc song song với giải mã opcode.

PHANFIG_dec

\subsection{MainControl}
Chín bộ so sánh 7 bit so \sig{opcode} với chín hằng số, mỗi bộ cho cờ của một nhóm lệnh; các cổng OR gộp cờ thành tín hiệu điều khiển. Opcode lạ làm mọi tín hiệu bằng 0 (lệnh rỗng an toàn).
\[
\mathtt{ALUOp}=\{\mathtt{IsR}\lor\mathtt{IsI},\ \mathtt{IsI}\lor\mathtt{IsBranch}\},\quad
\mathtt{ASel}=\{\mathtt{IsLui},\ \mathtt{IsAuipc}\},\quad
\mathtt{WBSel}=\{\mathtt{IsJAL}\lor\mathtt{IsJALR},\ \mathtt{IsLoad}\}.
\]

PHANFIG_ctl

\begin{center}
\small
\begin{tabular}{@{}lcccccccc@{}}
\toprule
\textbf{Lệnh} & RegWrite & ALUSrc & MemWrite & MemRead & ALUOp & ImmSel & ASel & WBSel\\
\midrule
\texttt{add} (R) & 1 & 0 & 0 & 0 & 10 & -- & 00 & 00\\
\texttt{addi} (I) & 1 & 1 & 0 & 0 & 11 & 000 & 00 & 00\\
\texttt{lw} & 1 & 1 & 0 & 1 & 00 & 000 & 00 & 01\\
\texttt{sw} & 0 & 1 & 1 & 0 & 00 & 001 & 00 & --\\
\texttt{beq} & 0 & 0 & 0 & 0 & 01 & 010 & 00 & --\\
\texttt{lui} & 1 & 1 & 0 & 0 & 00 & 011 & 10 & 00\\
\texttt{auipc} & 1 & 1 & 0 & 0 & 00 & 011 & 01 & 00\\
\texttt{jal} & 1 & -- & 0 & 0 & -- & 100 & -- & 10\\
\texttt{jalr} & 1 & 1 & 0 & 0 & 00 & 000 & 00 & 10\\
\bottomrule
\end{tabular}
\end{center}

\subsection{ImmGen}
Hằng số bị xáo trộn có chủ đích trong lệnh; năm bộ splitter và bộ mở rộng dấu dựng lại hằng số theo từng kiểu, một multiplexer chọn theo \sig{ImmSel}. Kiểu U không mở rộng mà chèn 12 bit 0 (\texttt{imm}$\ll12$).
Ví dụ \texttt{fe059ce3} (\texttt{bnez x11, loop}, kiểu B) cho hằng số \texttt{0xFFFFFFF8} $=-8$.

PHANFIG_imm

\subsection{RegisterFile}
32 thanh ghi 32 bit có nhãn \texttt{x0..x31}; một demultiplexer đưa tín hiệu \sig{RegWrite} tới đúng thanh ghi \sig{rd}, hai multiplexer 32-ra-1 là hai cổng đọc \emph{bất đồng bộ}
(CPU đơn chu kỳ cần toán hạng ngay trong chu kỳ). \texttt{x0} nhận hằng số 0 nên luôn bằng 0. Trong pipeline, khối này dùng xung nhịp đảo để ghi ở \emph{cạnh xuống}.

PHANFIG_rf

\subsection{ALUControl và ALU}
\sig{ALUControl} biến \sig{ALUOp}, \sig{funct3}, \sig{funct7} thành mã 4 bit \sig{ALUCtrl}: 0 ADD, 1 SUB, 2 AND, 3 OR, 4 XOR, 5 SLL, 6 SRL, 7 SRA, 8 SLT, 9 SLTU.
Bit \sig{funct7[5]} phân biệt ADD/SUB và SRL/SRA ở kiểu R; ở kiểu I chỉ các lệnh dịch xét bit này. ALU tính song song mọi phép (cộng, trừ, AND, OR, XOR, ba bộ dịch, hai phép so sánh có dấu/không dấu)
rồi một multiplexer 16-ra-1 chọn kết quả theo \sig{ALUCtrl}. Kết quả SLT/SLTU 1 bit được mở rộng bằng 0 thành 32 bit.

PHANFIG_alu

\subsection{BranchUnit}
Một bộ so sánh không dấu và một bộ có dấu cho các quan hệ ``bằng'' và ``nhỏ hơn''; ba cổng NOT cho các phủ định; một multiplexer 8-ra-1 theo \sig{funct3} chọn điều kiện:
000 \texttt{beq}, 001 \texttt{bne}, 100 \texttt{blt}, 101 \texttt{bge}, 110 \texttt{bltu}, 111 \texttt{bgeu}. Cổng AND với \sig{IsBranch} bảo đảm lệnh khác không bao giờ rẽ nhánh.

\subsection{Memory, LoadExtract, StoreMerge}
RAM $256\times32$ đọc bất đồng bộ và có một chân cho phép ghi. Vì RAM chỉ ghi nguyên từ, \sig{LoadExtract} cắt byte/nửa từ ra khỏi từ đọc được rồi mở rộng dấu hoặc mở rộng 0
(\texttt{lb lh lw lbu lhu}), còn \sig{StoreMerge} thực hiện đọc--sửa--ghi: một ROM $16\times4$ đổi $\{\mathrm{size},\mathrm{addr}[1:0]\}$ thành bốn bit cho phép từng làn byte
(\texttt{1 2 4 8} cho byte, \texttt{3 3 c c} cho nửa từ, \texttt{f} cho từ). Ví dụ từ cũ \texttt{0x11223344}, \texttt{sb} giá trị \texttt{0xAA} vào byte 1 cho từ mới \texttt{0x1122AA44}.

PHANFIG_mem

% ===================================================================== 5
\section{CPU đơn chu kỳ}
\label{sec:single}
Mỗi lệnh đi qua cả năm tầng trong \emph{một} chu kỳ xung nhịp: ROM đọc lệnh tại PC, \sig{InstructionDecode}, \sig{MainControl}, \sig{ImmGen} và \sig{RegisterFile} làm việc song song,
hai multiplexer chọn toán hạng A và B, ALU tính, \sig{BranchUnit} quyết định rẽ nhánh, \sig{Memory} chỉ hoạt động với load/store, và multiplexer \sig{WBSel} chọn giá trị ghi vào \sig{rd}.
PC kế tiếp được chọn như sau:
\[
\mathtt{next\_pc}=
\begin{cases}
(\mathtt{rs1}+\mathtt{imm})\ \&\ \mathtt{0xFFFFFFFE} & \text{nếu } \mathtt{IsJALR}\\
\mathtt{PC}+\mathtt{imm} & \text{nếu } \mathtt{branch\_taken}\lor\mathtt{IsJAL}\\
\mathtt{PC}+4 & \text{còn lại.}
\end{cases}
\]
Các lệnh \texttt{lui}, \texttt{auipc}, \texttt{jal}, \texttt{jalr} dùng lại ALU và đường write-back nhờ \sig{ASel} và \sig{WBSel}, không thêm phần cứng riêng.

Hình~\ref{fig:main} là sơ đồ khối của CPU đơn chu kỳ (nét cam đứt là tín hiệu điều khiển).

PHANFIG_main

\textbf{Ví dụ:} lệnh \texttt{add x10,x10,x11} (\texttt{00b50533}) ở tick 3 của chương trình mẫu: \sig{opcode}=\texttt{0x33}, \sig{ALUOp}=10, \sig{ALUCtrl}=0 (ADD), ALU tính $0+\mathtt{0x0a}=\mathtt{0x0a}$
và ghi vào \texttt{x10} ở cạnh xung nhịp; PC tăng $4$.

% ===================================================================== 6
\section{CPU pipeline 5 tầng}
\label{sec:pipeline}
CPU pipeline dùng đúng các khối của CPU đơn chu kỳ, cắt thành năm tầng bởi bốn thanh ghi pipeline IF/ID, ID/EX, EX/MEM, MEM/WB. Tín hiệu điều khiển được sinh một lần ở tầng ID,
đóng gói thành ``từ điều khiển'' (13 bit ở ID/EX, 5 bit ở EX/MEM, 3 bit ở MEM/WB) và đi cùng lệnh; mỗi tầng chỉ tách phần mình cần.

Hình~\ref{fig:pipe} cho thấy năm tầng, bốn thanh ghi pipeline và hai khối xử lý hazard.

PHANFIG_pipe

\begin{center}
\small
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{2.3cm}X@{}}
\toprule
\textbf{Thanh ghi} & \textbf{Chứa}\\
\midrule
IF/ID & \sig{pc_id}, \sig{instr_id}\\
ID/EX & \sig{pc_ex}, \sig{rs1_data_ex}, \sig{rs2_data_ex}, \sig{imm_ex}, \sig{rs1_ex}, \sig{rs2_ex}, \sig{rd_ex}, \sig{funct3_ex}, \sig{funct7_ex}, từ điều khiển \sig{ctrl_ex}\\
EX/MEM & \sig{alu_result_mem}, \sig{store_data_mem}, \sig{pc_plus4_mem}, \sig{rd_mem}, \sig{funct3_mem}, điều khiển \sig{RegWrite MemWrite MemRead WBSel}\\
MEM/WB & \sig{alu_result_wb}, \sig{mem_rdata_wb}, \sig{pc_plus4_wb}, \sig{rd_wb}, điều khiển \sig{RegWrite WBSel}\\
\bottomrule
\end{tabularx}
\end{center}

\subsection{Thời điểm ghi của register file}
Register file ghi ở \emph{cạnh xuống} của xung nhịp. Lệnh ở tầng WB ghi trong nửa đầu chu kỳ, lệnh ở tầng ID đọc trong nửa sau nên thấy giá trị mới: không cần forwarding cho khoảng cách 3 lệnh.

\subsection{Hazard dữ liệu: forwarding}
\sig{ForwardingUnit} so \sig{rs1_ex}, \sig{rs2_ex} với thanh ghi đích của các lệnh ở MEM và WB:
\[
\mathtt{ForwardA}=
\begin{cases}
10 & \text{nếu } \mathtt{RegWrite\_mem}\wedge\mathtt{rd\_mem}\ne0\wedge\mathtt{rd\_mem}=\mathtt{rs1\_ex}\quad(\text{từ EX/MEM})\\
01 & \text{ngược lại nếu điều tương tự đúng với WB}\quad(\text{từ MEM/WB})\\
00 & \text{còn lại}\quad(\text{từ register file}).
\end{cases}
\]
EX/MEM được ưu tiên vì mới hơn; điều kiện $\mathtt{rd}\ne0$ ngăn forward \texttt{x0}; \texttt{ForwardB} tương tự với \sig{rs2_ex}. Giá trị lấy từ EX/MEM là kết quả ALU, \emph{riêng \texttt{jal}/\texttt{jalr} là PC$+4$}.

Hình~\ref{fig:fwd} minh họa ba nguồn của toán hạng ALU.

PHANFIG_fwd

\subsection{Hazard dữ liệu không forward được: load-use}
Lệnh load chỉ có dữ liệu ở cuối tầng MEM. Nếu lệnh liền sau cần nó ở EX thì phải chờ một chu kỳ. \sig{HazardUnit} phát hiện
$\mathtt{MemRead\_ex}\wedge\mathtt{rd\_ex}\ne0\wedge(\mathtt{rd\_ex}=\mathtt{rs1\_id}\lor\mathtt{rd\_ex}=\mathtt{rs2\_id})$; khi đó PC và IF/ID đứng yên
(\sig{run}$=0$) và từ điều khiển đi vào ID/EX bị thay bằng 0 (một \emph{bubble}). Chi phí đúng một chu kỳ; load, một lệnh không liên quan rồi mới dùng thì không mất gì.

\subsection{Hazard điều khiển: branch, JAL, JALR}
Lệnh rẽ nhánh/nhảy được quyết định ở tầng EX: $\mathtt{pc\_src\_ex}=\mathtt{branch\_taken}\lor\mathtt{IsJAL}\lor\mathtt{IsJALR}$. PC chuyển sang địa chỉ đích, lệnh đang được nạp bị đổi thành 0
và từ điều khiển vào ID/EX bị xóa, nên hai lệnh sau lệnh rẽ nhánh bị hủy. Mức phạt là 2 chu kỳ cho mỗi lệnh rẽ nhánh/nhảy được thực hiện; rẽ nhánh không rẽ không mất gì (dự đoán tĩnh ``không rẽ'').

\begin{center}
\small
\begin{tabular}{@{}lc@{}}
\toprule
\textbf{Tình huống} & \textbf{Chu kỳ thêm}\\
\midrule
lệnh phụ thuộc ngay sau lệnh ALU (forwarding) & 0\\
dùng giá trị vừa load ở lệnh kế tiếp (load-use) & 1\\
load, một lệnh không liên quan, rồi mới dùng & 0\\
branch không rẽ & 0\\
branch được rẽ / \texttt{jal} / \texttt{jalr} & 2\\
\bottomrule
\end{tabular}
\end{center}

\subsection{Ví dụ: chương trình \texttt{hazards\_demo.s}}
Chương trình nhỏ này gom đủ ba loại hazard: \texttt{li x1,100}; \texttt{sw x1,0(x0)} (forwarding); \texttt{lw x2,0(x0)}; \texttt{addi x3,x2,1} (load-use $\Rightarrow$ stall);
\texttt{add x4,x3,x2}; \texttt{beq x4,x4,skip} (luôn rẽ $\Rightarrow$ flush hai lệnh \texttt{addi x5} và \texttt{addi x6}). Kết quả đúng là $x1=\mathtt{0x64}$, $x3=\mathtt{0x65}$, $x4=\mathtt{0xc9}$, $x7=7$
và $x5=x6=0$ (các lệnh bị hủy không để lại dấu vết).

Hình~\ref{fig:hazard} là giản đồ pipeline của chương trình này: ô cam là lệnh bị giữ ở ID (stall), ô đỏ là lệnh bị flush.

PHANFIG_hazard

\subsection{Chạy một lần bấm}
Mỗi CPU có thêm chân vào \sig{PAUSE} và chân ra \sig{DONE}. Xung nhịp thật của Clock đi qua một cổng AND với điều kiện cho phép chạy; điều kiện này tắt khi \sig{PAUSE}$=1$ hoặc khi chương trình đã kết thúc.
Ở CPU đơn chu kỳ, chương trình kết thúc khi lệnh hiện tại là \texttt{halt: j halt} (\texttt{0x0000006f}); ở CPU pipeline, một thanh ghi 1 bit nhớ lệnh \texttt{jal} có hằng số 0 vừa đi qua tầng EX và xung nhịp dừng một chu kỳ sau,
khi mọi lệnh cũ đã ghi xong. Nhờ vậy chỉ cần bật Auto-Tick một lần (\texttt{Simulate} $\rightarrow$ \texttt{Auto-Tick Enabled}) là chương trình chạy từ đầu đến cuối rồi tự dừng, đèn \sig{DONE} sáng.

% ===================================================================== 7
\section{Chương trình và công cụ hỗ trợ}
\begin{itemize}
  \item \textbf{Assembler} (\texttt{tools/rv.py asm}): nhãn, lệnh giả (\texttt{li}, \texttt{mv}, \texttt{bnez}, \texttt{ret}, \texttt{j}), tên thanh ghi ABI; tạo ảnh ROM dạng \texttt{v2.0 raw} để nạp bằng \emph{Load Image}.
  \item \textbf{Bộ mô phỏng tham chiếu} (\texttt{tools/rv.py sim}): viết độc lập với mạch; là ``chuẩn'' của mọi bài test.
  \item \textbf{Bộ chạy không giao diện} (\texttt{tools/java/Run.java}): nạp ROM, đảo xung nhịp, đọc \texttt{PC}, \texttt{x0..x31} và RAM từ mạch thật.
  \item \textbf{Bộ sinh mạch} (\texttt{tools/build/}): sinh circuit từ netlist, kiểm tra từng net, đặt chú thích tiếng Việt cạnh từng linh kiện.
  \item \textbf{Bản web trực quan} (\texttt{docs/web/index.html}): mô phỏng bằng JavaScript hai CPU cùng tên khối và tên tín hiệu, có băng chuyền lệnh, biểu đồ hiệu năng và sơ đồ luồng; engine được kiểm với bộ mô phỏng tham chiếu.
\end{itemize}

Hình~\ref{fig:proof} tóm tắt cách chứng minh tính đúng đắn.

PHANFIG_proof

% ===================================================================== 8
\section{Kiểm chứng}
Việc kiểm chứng tự động ở ba mức:
\begin{enumerate}
  \item \textbf{Test module} (\texttt{tests/run\_tests.ps1}): 106 hàng test-vector trên 9 module (\sig{MainControl}, \sig{ImmGen}, \sig{ALU}, \sig{ALUControl}, \sig{BranchUnit}, \sig{LoadExtract}, \sig{StoreMerge}, \sig{ForwardingUnit}, \sig{HazardUnit}), do chính Logisim chạy.
  \item \textbf{Chương trình} (\texttt{tests/run\_cpu\_tests.py}): 7 chương trình (\texttt{alu}, \texttt{mem}, \texttt{branch}, \texttt{jump}, \texttt{fib}, \texttt{hazard}, \texttt{demo}) chạy trên cả hai CPU. Sau khi chạy, cả 32 thanh ghi và mọi từ dữ liệu khác 0
  phải bằng kết quả của bộ mô phỏng tham chiếu. Chương trình \texttt{hazard} đánh vào các tình huống: phụ thuộc liên tiếp, phụ thuộc cách 3 lệnh, load-use, load rồi store giá trị vừa load,
  load làm địa chỉ, branch trên giá trị vừa load, branch được rẽ nhảy qua lệnh, liên kết \texttt{jal} dùng ngay, \texttt{jalr} qua thanh ghi vừa ghi, \texttt{x0} làm đích.
  \item \textbf{Chương trình ngẫu nhiên} (\texttt{tests/fuzz.py}): chương trình ngẫu nhiên 60--80 lệnh chỉ dùng 7 thanh ghi (nên hầu hết lệnh đều phụ thuộc lệnh gần đó), load/store đủ kích thước, branch và nhảy tiến;
  30 chương trình (60 lượt chạy trên hai CPU) đã được chạy trên project cuối, tất cả khớp.
\end{enumerate}
Bản thân bộ mô phỏng tham chiếu được kiểm bằng các mã hóa đã biết (\texttt{addi x1,x0,5} $=$ \texttt{00500093}, \texttt{add x3,x1,x2} $=$ \texttt{002081B3}) và bằng các chương trình tự kiểm có kết quả tính tay.
Ngoài ra \texttt{tools/live\_proof.py} chạy một chương trình trên bộ mô phỏng tham chiếu, trên CPU đơn chu kỳ và trên CPU pipeline rồi in bảng so sánh ba cột và dòng kết luận.

% ===================================================================== 9
\section{Kết quả}
Số chu kỳ được đo đến lần ghi thanh ghi cuối cùng (đã tính thời gian làm đầy và xả pipeline); CPU đơn chu kỳ luôn có CPI $=1$.
\begin{center}
\small
\begin{tabularx}{\textwidth}{@{}lrrrrX@{}}
\toprule
\textbf{Chương trình} & \textbf{Lệnh} & \textbf{Đơn chu kỳ} & \textbf{Pipeline} & \textbf{CPI pipeline} & \textbf{Lý do}\\
\midrule
\texttt{alu} & 91 & 91 & 94 & 1,03 & không có branch được rẽ; forwarding che hết phụ thuộc\\
\texttt{mem} & 69 & 69 & 73 & 1,06 & ít branch\\
\texttt{hazard} & 67 & 67 & 82 & 1,22 & stall load-use, 4 branch/nhảy được rẽ\\
\texttt{jump} & 27 & 27 & 38 & 1,41 & 4 lệnh nhảy\\
\texttt{branch} & 69 & 69 & 104 & 1,51 & nhiều branch được rẽ\\
\texttt{fib} & 123 & 123 & 181 & 1,47 & vòng lặp: 1 branch được rẽ mỗi 4 lệnh\\
\texttt{demo} & 39 & 39 & 64 & 1,64 & vòng lặp 10 lần và một lần gọi hàm\\
\bottomrule
\end{tabularx}
\end{center}

Hình~\ref{fig:chart} so sánh số chu kỳ của hai CPU.

PHANFIG_chart

Với \texttt{demo}: 39 lệnh cộng $11$ lần chuyển hướng $\times2=22$ chu kỳ mất (9 lần \texttt{bnez} được rẽ, một \texttt{jal}, một \texttt{ret}) cho $61$ chu kỳ; $3$ chu kỳ còn lại là thời gian làm đầy pipeline.
Về số chu kỳ, pipeline ở đây \emph{không} nhanh hơn CPU đơn chu kỳ, vì mô phỏng của Logisim không có độ trễ cổng. Lợi ích thật của pipeline là chu kỳ xung nhịp ngắn hơn: đường dài nhất rút từ
``nạp lệnh $+$ giải mã $+$ ALU $+$ bộ nhớ $+$ ghi lại'' xuống còn một tầng. Cái giá phải trả là mức phạt 2 chu kỳ cho mỗi lệnh rẽ nhánh được thực hiện; dự đoán rẽ nhánh hoặc quyết định nhánh sớm hơn (ở ID) sẽ loại bỏ phần lớn chi phí này.

% ===================================================================== 10
\section{Các lỗi đã gặp và bài học}
Các khối ban đầu lần đầu được kiểm thử bằng test-vector và chương trình hoàn chỉnh; việc này đã tìm ra lỗi thật.
\begin{center}
\small
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{2.6cm}>{\raggedright\arraybackslash}p{7.2cm}X@{}}
\toprule
\textbf{Ở đâu} & \textbf{Lỗi} & \textbf{Cách sửa}\\
\midrule
ALU & \texttt{SLTU} trả \texttt{FFFFFFFF} thay vì 1 (kết quả 1 bit bị mở rộng dấu) & mở rộng bằng 0\\
ALUControl & \texttt{SLL} kiểu R chọn mã của \texttt{SRL} & sửa hằng số\\
MainControl & JALR so với opcode của JAL; LUI chọn hằng số kiểu B & viết lại phần giải mã\\
ImmGen & kiểu U thiếu $\ll12$; bit 0 của kiểu J bằng 1 & đã sửa\\
Memory & load trả dữ liệu không xác định (RAM đọc đồng bộ) & đọc bất đồng bộ\\
Datapath & JAL, JALR, LUI, AUIPC chưa có đường dữ liệu & thêm \sig{ASel}, \sig{WBSel}, logic PC kế tiếp\\
\bottomrule
\end{tabularx}
\end{center}
\textbf{Bài học về công cụ:} Logisim chỉ nối dây ở các \emph{đầu mút} (không nối ở chỗ giao chữ T), nên file sinh ra phải chia nhỏ dây; mọi vị trí phải nằm trên lưới 10 pixel; \sig{Constant} mặc định bằng 1 chứ không phải 0;
RAM mặc định đọc đồng bộ nên CPU đơn chu kỳ không dùng được; circuit có tên bắt đầu bằng dấu gạch dưới bị đổi tên âm thầm. Bộ sinh mạch hiện kiểm tra tất cả điều này và kiểm chứng các net của từng circuit sau khi ghi.

% ===================================================================== 11
\section{Hướng dẫn chạy lại}
Yêu cầu: Java 21, Python 3.
\begin{enumerate}
  \item Mở project: \texttt{java -jar logisim-evolution-4.1.0-all.jar RiscVComputer.circ}. Circuit \sig{main} là CPU đơn chu kỳ, \sig{Pipeline} là CPU pipeline.
  \item Chạy từng bước: \texttt{Simulate} $\rightarrow$ \texttt{Manual Tick Full Cycle} (Ctrl+F9); chạy tự động: \texttt{Simulate} $\rightarrow$ \texttt{Auto-Tick Enabled} (Ctrl+K); đặt lại: \texttt{Reset Simulation} (Ctrl+R).
  \item Nạp chương trình khác: chuột phải vào ROM $\rightarrow$ \emph{Load Image\dots} $\rightarrow$ chọn file \texttt{.hex}; tạo file bằng \texttt{python tools/rv.py asm prog.s -o prog.hex -l}.
  \item Kiểm thử: \texttt{powershell -File tests/run\_tests.ps1} (module), \texttt{python tests/run\_cpu\_tests.py --circuit all} (chương trình trên hai CPU), \texttt{python tests/fuzz.py --count 20 --seed 1} (ngẫu nhiên).
  \item Kiểm tra trước buổi trình bày: \texttt{powershell -File tools/presentation\_check.ps1}; chứng minh nhanh: \texttt{python tools/live\_proof.py}.
\end{enumerate}

% ===================================================================== 12
\section{Mở rộng và hướng phát triển}
\label{sec:future}
Chưa cài đặt (tùy chọn trong đề bài): dự đoán rẽ nhánh, cache, bộ nhân/chia (mở rộng M), ngắt, GPIO/UART, số thực. Các bước tiếp theo tự nhiên, rẻ nhất trước:
quyết định \texttt{JAL} ở tầng ID (mức phạt 1 chu kỳ thay vì 2); bộ dự đoán nhánh 1--2 bit cùng bộ đệm đích nhánh nhỏ; UART ánh xạ bộ nhớ tại một địa chỉ cố định để chương trình có thể in ra;
mở rộng \texttt{M} với bộ chia nhiều chu kỳ và tín hiệu stall dùng lại \sig{HazardUnit}.

% ===================================================================== 13
\section{Kết luận}
Dự án đã hoàn thành đủ các yêu cầu cơ bản của đề: một máy tính 32-bit theo RV32I với đầy đủ lệnh tối thiểu và lệnh tùy chọn, hai phiên bản CPU (đơn chu kỳ và pipeline 5 tầng) xử lý đúng
hazard dữ liệu và điều khiển, chương trình nạp qua bộ nhớ lệnh nhờ assembler, và bộ kiểm thử ba mức cho thấy hai CPU cho kết quả giống hệt bộ mô phỏng tham chiếu độc lập.
Số liệu đo cho thấy pipeline cần nhiều chu kỳ hơn trong mô phỏng không độ trễ cổng, đúng như phân tích lý thuyết, và chi phí chủ yếu đến từ các lệnh rẽ nhánh được thực hiện.

% ===================================================================== phụ lục
\appendix
\section{Mã hóa lệnh RV32I}
\begin{center}
\small
\begin{tabularx}{\textwidth}{@{}lccX@{}}
\toprule
\textbf{Lệnh} & \textbf{opcode} & \textbf{funct3} & \textbf{funct7 / imm}\\
\midrule
add / sub & 0110011 & 000 & 0000000 / 0100000\\
sll & 0110011 & 001 & 0000000\\
slt / sltu & 0110011 & 010 / 011 & 0000000\\
xor & 0110011 & 100 & 0000000\\
srl / sra & 0110011 & 101 & 0000000 / 0100000\\
or / and & 0110011 & 110 / 111 & 0000000\\
addi slti sltiu xori ori andi & 0010011 & 000 010 011 100 110 111 & imm[11:0]\\
slli / srli / srai & 0010011 & 001 / 101 / 101 & 0000000 / 0000000 / 0100000\\
lb lh lw lbu lhu & 0000011 & 000 001 010 100 101 & imm[11:0]\\
sb sh sw & 0100011 & 000 001 010 & imm[11:5], imm[4:0]\\
beq bne blt bge bltu bgeu & 1100011 & 000 001 100 101 110 111 & hằng số kiểu B\\
jal & 1101111 & -- & hằng số kiểu J\\
jalr & 1100111 & 000 & imm[11:0]\\
lui / auipc & 0110111 / 0010111 & -- & imm[31:12]\\
\bottomrule
\end{tabularx}
\end{center}

\section{Cấu trúc thư mục dự án}
\begin{center}
\small
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{4.6cm}X@{}}
\toprule
\textbf{Đường dẫn} & \textbf{Nội dung}\\
\midrule
\texttt{RiscVComputer.circ} & project Logisim (14 circuit, hai CPU)\\
\texttt{programs/} & chương trình mẫu \texttt{demo.s}, \texttt{hazards\_demo.s} và ảnh ROM \texttt{.hex}\\
\texttt{tests/} & test-vector của 9 module, 6 chương trình test, bộ fuzz, bộ chạy test\\
\texttt{tools/rv.py} & assembler và bộ mô phỏng tham chiếu\\
\texttt{tools/java/} & bộ chạy chương trình trên mạch không cần giao diện\\
\texttt{tools/build/} & bộ sinh mạch từ netlist và kiểm chứng\\
\texttt{tools/web/}, \texttt{docs/web/} & bản web trực quan và các file nguồn của nó\\
\texttt{docs/} & báo cáo, hướng dẫn, giải thích, sơ đồ luồng (tiếng Anh và tiếng Việt)\\
\bottomrule
\end{tabularx}
\end{center}

\section{Phân công}
\begin{center}
\small
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{4.2cm}>{\raggedright\arraybackslash}p{5.4cm}X@{}}
\toprule
\textbf{Thành viên} & \textbf{Phần phụ trách} & \textbf{Ghi chú}\\
\midrule
\underline{\hspace{3.6cm}} & CPU đơn chu kỳ, giải mã, register file & \\
\underline{\hspace{3.6cm}} & ALU, bộ nhớ, kiểm thử & \\
\underline{\hspace{3.6cm}} & Pipeline, forwarding, hazard & \\
\bottomrule
\end{tabularx}
\end{center}

\begin{thebibliography}{9}
\bibitem{riscv} A. Waterman, K. Asanović (eds.), \emph{The RISC-V Instruction Set Manual, Volume I: Unprivileged ISA}, RISC-V International.
\bibitem{ph} D. A. Patterson, J. L. Hennessy, \emph{Computer Organization and Design, RISC-V Edition}, Morgan Kaufmann.
\bibitem{logisim} Logisim Evolution, \emph{https://github.com/logisim-evolution/logisim-evolution}.
\end{thebibliography}

\end{document}
"""

# ------------------------------------------------------------------ assemble
head = r"""% =====================================================================
%  Báo cáo bài tập lớn: thiết kế máy tính RISC-V 32-bit trên Logisim Evolution
%  Sinh bởi tools/build_report_tex.py (hình lấy từ KienTruc_RV32I.tex).
%  Biên dịch: pdflatex BaoCao_RV32I.tex  (chạy 2 lần để có mục lục)  hoặc Overleaf (pdfLaTeX).
% =====================================================================
"""
text = head + preamble.lstrip() + "\n" + BODY
for name in list(FIG) + ["chart"]:
    marker = f"PHANFIG_{name}"
    text = text.replace(marker, chart() if name == "chart" else FIG[name])
assert "PHANFIG_" not in text, "unreplaced figure placeholder"
open(OUT, "w", encoding="utf-8", newline="\n").write(text)
print("wrote", os.path.relpath(OUT, ROOT), len(text) // 1024, "KB")
