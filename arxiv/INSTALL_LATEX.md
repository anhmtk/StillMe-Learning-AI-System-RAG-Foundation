# Hướng dẫn Cài đặt LaTeX trên Windows

Để compile LaTeX document, bạn cần cài một trong các LaTeX distribution sau:

## Option 1: MiKTeX (Khuyến nghị cho Windows)

### Cài đặt MiKTeX:

1. **Download MiKTeX:**
   - Truy cập: https://miktex.org/download
   - Download bản **MiKTeX Installer** (Windows)

2. **Cài đặt:**
   - Chạy installer
   - Chọn "Install packages on-the-fly: Yes" (khuyến nghị)
   - Chọn "Install missing packages automatically: Yes"
   - Chọn thư mục cài đặt (mặc định là `C:\Users\<YourName>\AppData\Local\Programs\MiKTeX`)
   - Click "Next" và chờ cài đặt hoàn tất

3. **Kiểm tra cài đặt:**
   ```powershell
   pdflatex --version
   bibtex --version
   ```

### Cài đặt packages cần thiết (nếu thiếu):

MiKTeX sẽ tự động cài packages khi compile, nhưng bạn có thể cài trước:

```powershell
# Mở MiKTeX Console (tìm trong Start Menu)
# Hoặc dùng command line:
miktex packages install booktabs
miktex packages install hyperref
miktex packages install amsmath
```

---

## Option 2: TeX Live (Full distribution, lớn hơn)

### Cài đặt TeX Live:

1. **Download TeX Live:**
   - Truy cập: https://www.tug.org/texlive/
   - Download "install-tl-windows.exe"

2. **Cài đặt:**
   - Chạy installer (có thể mất 30-60 phút)
   - Chọn "Full scheme" để cài tất cả packages
   - Chờ cài đặt hoàn tất

3. **Kiểm tra:**
   ```powershell
   pdflatex --version
   bibtex --version
   ```

---

## Option 3: Overleaf (Online, không cần cài)

Nếu không muốn cài LaTeX trên máy, bạn có thể:

1. **Upload lên Overleaf:**
   - Truy cập: https://www.overleaf.com
   - Tạo project mới
   - Upload `main.tex`, `refs.bib`, và `figures/`
   - Overleaf sẽ tự động compile

2. **Download PDF:**
   - Sau khi compile thành công, download PDF
   - PDF này có thể dùng để submit arXiv

---

## Sau khi cài đặt

1. **Restart PowerShell** (hoặc terminal) để load PATH mới

2. **Test lại:**
   ```powershell
   cd D:\StillMe-Learning-AI-System-RAG-Foundation\arxiv
   .\compile.ps1
   ```

3. **Nếu vẫn lỗi:**
   - Kiểm tra PATH: `$env:PATH` có chứa đường dẫn MiKTeX/TeX Live không
   - Thêm thủ công vào PATH nếu cần:
     - MiKTeX: `C:\Users\<YourName>\AppData\Local\Programs\MiKTeX\miktex\bin\x64`
     - TeX Live: `C:\texlive\2024\bin\win32` (version có thể khác)

---

## Khuyến nghị

- **Windows users**: Dùng **MiKTeX** (nhẹ hơn, cài nhanh hơn)
- **Nếu không muốn cài**: Dùng **Overleaf** (online editor)
- **Nếu cần full control**: Dùng **TeX Live** (đầy đủ nhất)

---

## Troubleshooting

### Lỗi "pdflatex not found" sau khi cài:

1. **Restart PowerShell/Terminal**
2. **Kiểm tra PATH:**
   ```powershell
   Get-Command pdflatex
   ```
3. **Nếu không tìm thấy, thêm vào PATH:**
   ```powershell
   # Tạm thời (cho session hiện tại)
   $env:PATH += ";C:\Users\<YourName>\AppData\Local\Programs\MiKTeX\miktex\bin\x64"
   
   # Hoặc thêm vĩnh viễn qua System Properties > Environment Variables
   ```

### Lỗi "Package not found" khi compile:

- MiKTeX sẽ tự động hỏi cài package, chọn "Yes"
- Hoặc cài thủ công qua MiKTeX Console

---

## Quick Start (Sau khi cài)

```powershell
# 1. Kiểm tra cài đặt
pdflatex --version
bibtex --version

# 2. Compile paper
cd D:\StillMe-Learning-AI-System-RAG-Foundation\arxiv
.\compile.ps1

# 3. Xem kết quả
# Mở main.pdf để xem
```

