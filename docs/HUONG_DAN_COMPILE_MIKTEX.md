# Hướng Dẫn Compile Markdown Sang PDF Với MiKTeX

## Tình Trạng Hiện Tại

✅ **MiKTeX đã được cài đặt** (pdflatex và xelatex đều có sẵn)  
❌ **Pandoc chưa được cài đặt**

## Cài Đặt Pandoc

### Cách 1: Sử dụng Chocolatey (Khuyến Nghị)

```powershell
choco install pandoc
```

### Cách 2: Tải Trực Tiếp

1. Truy cập: https://pandoc.org/installing.html
2. Tải bản cài đặt cho Windows
3. Chạy file cài đặt

### Cách 3: Sử dụng Winget

```powershell
winget install --id JohnMacFarlane.Pandoc
```

## Sử Dụng Script Compile

Sau khi cài đặt pandoc, chạy:

```powershell
.\scripts\compile.ps1
```

Hoặc chỉ định file cụ thể:

```powershell
.\scripts\compile.ps1 docs\EXECUTIVE_SUMMARY.md
```

Script sẽ tự động:
1. Kiểm tra MiKTeX (đã có ✅)
2. Kiểm tra pandoc
3. Sử dụng pandoc + MiKTeX để tạo PDF

## Sử Dụng Pandoc Trực Tiếp (Nếu Đã Cài)

### Với XeLaTeX (Tốt cho tiếng Việt)

```powershell
pandoc docs\EXECUTIVE_SUMMARY.md -o docs\EXECUTIVE_SUMMARY.pdf `
    --pdf-engine=xelatex `
    -V geometry:margin=2cm `
    -V fontsize=11pt `
    -V mainfont="Times New Roman" `
    -V lang=vi `
    --highlight-style=tango `
    --toc `
    --toc-depth=3
```

### Với PDFLaTeX

```powershell
pandoc docs\EXECUTIVE_SUMMARY.md -o docs\EXECUTIVE_SUMMARY.pdf `
    --pdf-engine=pdflatex `
    -V geometry:margin=2cm `
    -V fontsize=11pt `
    --highlight-style=tango `
    --toc `
    --toc-depth=3
```

## Kiểm Tra Cài Đặt

```powershell
# Kiểm tra MiKTeX
pdflatex --version
xelatex --version

# Kiểm tra pandoc (sau khi cài)
pandoc --version
```

## Troubleshooting

### Lỗi: "pandoc: command not found"
- Cài đặt pandoc (xem phần trên)
- Hoặc thêm pandoc vào PATH

### Lỗi: "MiKTeX package not found"
- MiKTeX sẽ tự động cài package khi cần
- Hoặc chạy: `miktex packages install <package-name>`

### Lỗi: "Font not found"
- XeLaTeX cần font hỗ trợ Unicode
- Đảm bảo font "Times New Roman" hoặc font khác có sẵn
- Hoặc dùng pdflatex thay vì xelatex

## Lưu Ý

- **XeLaTeX** tốt hơn cho tiếng Việt (hỗ trợ Unicode tốt)
- **PDFLaTeX** nhanh hơn nhưng cần cấu hình font cho tiếng Việt
- Script tự động chọn engine phù hợp

