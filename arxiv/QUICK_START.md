# Quick Start Guide - Cài MiKTeX và Compile

## Bước 1: Cài MiKTeX

### Download và Cài đặt:

1. **Download MiKTeX:**
   - Truy cập: **https://miktex.org/download**
   - Click "Download" (bản Windows)
   - File tải về: `miktex-setup-x64.exe` (hoặc tương tự)

2. **Chạy Installer:**
   - Double-click file vừa tải
   - Chọn **"Install packages on-the-fly: Yes"** ⚠️ (QUAN TRỌNG)
   - Chọn **"Install missing packages automatically: Yes"**
   - Chọn thư mục cài đặt (mặc định OK)
   - Click "Next" và chờ cài đặt (~5-10 phút)

3. **Hoàn tất:**
   - Click "Finish" khi cài xong
   - **QUAN TRỌNG**: Đóng tất cả PowerShell/Terminal windows

---

## Bước 2: Kiểm tra Cài đặt

1. **Mở PowerShell mới** (quan trọng - phải mở mới để load PATH)

2. **Chạy script kiểm tra:**
   ```powershell
   cd D:\StillMe-Learning-AI-System-RAG-Foundation\arxiv
   .\check_latex.ps1
   ```

3. **Kết quả mong đợi:**
   ```
   [OK] pdflatex found: MiKTeX-pdfTeX ...
   [OK] bibtex found: MiKTeX-BibTeX ...
   [SUCCESS] LaTeX is ready!
   ```

---

## Bước 3: Compile Paper

1. **Chạy compile script:**
   ```powershell
   .\compile.ps1
   ```

2. **Quá trình compile:**
   - Step 1: First pdflatex pass
   - Step 2: Running bibtex
   - Step 3: Second pdflatex pass
   - Step 4: Third pdflatex pass (final)

3. **Kết quả:**
   - File `main.pdf` sẽ được tạo trong thư mục `arxiv/`
   - Mở `main.pdf` để xem kết quả

---

## Troubleshooting

### Lỗi "pdflatex not found" sau khi cài:

**Nguyên nhân**: PowerShell chưa load PATH mới

**Giải pháp**:
1. **Đóng tất cả PowerShell windows**
2. **Mở PowerShell mới**
3. Chạy lại: `.\check_latex.ps1`

### Lỗi "Package not found" khi compile:

**Nguyên nhân**: MiKTeX chưa cài package cần thiết

**Giải pháp**:
- MiKTeX sẽ tự động hỏi cài package
- Chọn **"Yes"** khi được hỏi
- Hoặc cài thủ công qua MiKTeX Console:
  ```powershell
  # Mở MiKTeX Console từ Start Menu
  # Hoặc chạy:
  miktex packages install booktabs
  miktex packages install hyperref
  ```

### Lỗi "Figure not found":

**Bình thường** - vì chưa tạo figures. PDF vẫn được tạo, chỉ thiếu hình.

**Giải pháp**: Tạo figures sau (xem `figures/README.md`)

---

## Checklist

- [ ] Đã download MiKTeX installer
- [ ] Đã cài MiKTeX với "Install packages on-the-fly: Yes"
- [ ] Đã đóng và mở lại PowerShell
- [ ] Đã chạy `.\check_latex.ps1` và thấy [SUCCESS]
- [ ] Đã chạy `.\compile.ps1` và tạo được `main.pdf`

---

## Sau khi Compile Thành công

1. **Review PDF**: Mở `main.pdf` và kiểm tra:
   - Formatting đúng
   - Tables hiển thị đúng
   - References được số hóa
   - Equations hiển thị đúng

2. **Tạo Figures** (nếu chưa có):
   - Xem hướng dẫn trong `figures/README.md`
   - Tạo 3 figures: fig1_architecture, fig2_validation_chain, fig3_results

3. **Compile lại** sau khi có figures:
   ```powershell
   .\compile.ps1
   ```

4. **Chuẩn bị Submit arXiv**:
   - Files cần: `main.tex`, `refs.bib`, `figures/*.pdf`
   - Xem `README.md` để biết metadata cần điền

---

## Help

Nếu gặp vấn đề:
1. Kiểm tra `main.log` để xem lỗi chi tiết
2. Xem `INSTALL_LATEX.md` để biết thêm chi tiết
3. Đảm bảo đã restart PowerShell sau khi cài MiKTeX

