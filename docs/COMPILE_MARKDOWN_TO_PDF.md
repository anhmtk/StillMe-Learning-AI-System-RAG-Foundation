# Hướng Dẫn Compile Markdown Sang PDF

## Cách Sử Dụng Script Compile

### 1. Script Đơn Giản (Khuyến Nghị)

```powershell
# Từ thư mục gốc của project
.\scripts\compile.ps1
```

Hoặc chỉ định file cụ thể:

```powershell
.\scripts\compile.ps1 docs\EXECUTIVE_SUMMARY.md
```

Script sẽ tự động:
- Thử dùng **pandoc** (nếu có)
- Nếu không có pandoc, sẽ dùng **Python + weasyprint**
- Tự động cài đặt các package cần thiết

### 2. Script Chi Tiết (Nhiều Tùy Chọn)

```powershell
.\scripts\compile_markdown_to_pdf.ps1 docs\EXECUTIVE_SUMMARY.md docs\EXECUTIVE_SUMMARY.pdf
```

## Cài Đặt Công Cụ

### Phương Pháp 1: Pandoc (Khuyến Nghị - Chất Lượng Cao)

**Cài đặt pandoc:**
```powershell
# Sử dụng Chocolatey
choco install pandoc

# Hoặc tải từ: https://pandoc.org/installing.html
```

**Sử dụng pandoc trực tiếp:**
```powershell
pandoc docs\EXECUTIVE_SUMMARY.md -o docs\EXECUTIVE_SUMMARY.pdf --pdf-engine=xelatex -V geometry:margin=2cm
```

### Phương Pháp 2: Python + WeasyPrint

**Cài đặt:**
```powershell
pip install weasyprint markdown
```

**Sử dụng:**
```powershell
.\scripts\compile.ps1
```

### Phương Pháp 3: Node.js + md-to-pdf

**Cài đặt:**
```powershell
npm install -g md-to-pdf
```

**Sử dụng:**
```powershell
md-to-pdf docs\EXECUTIVE_SUMMARY.md
```

## Kiểm Tra Công Cụ Đã Cài

```powershell
# Kiểm tra pandoc
pandoc --version

# Kiểm tra Python
python --version

# Kiểm tra Node.js
node --version
npm --version
```

## Troubleshooting

### Lỗi: "pandoc not found"
- Cài đặt pandoc từ https://pandoc.org/installing.html
- Hoặc sử dụng phương pháp Python

### Lỗi: "weasyprint installation failed"
- Cài đặt GTK+ runtime: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
- Hoặc sử dụng pandoc

### Lỗi: "PDF generation failed"
- Kiểm tra file markdown có lỗi syntax không
- Thử với file markdown đơn giản trước
- Kiểm tra quyền ghi file trong thư mục output

## Ví Dụ Sử Dụng

```powershell
# Compile file EXECUTIVE_SUMMARY.md
cd D:\StillMe-Learning-AI-System-RAG-Foundation
.\scripts\compile.ps1 docs\EXECUTIVE_SUMMARY.md

# Kết quả: docs\EXECUTIVE_SUMMARY.pdf
```

## Lưu Ý

- File PDF sẽ được tạo cùng thư mục với file markdown
- Tên file PDF = tên file markdown (đổi đuôi .md thành .pdf)
- Script tự động cài đặt các package Python cần thiết nếu chưa có

