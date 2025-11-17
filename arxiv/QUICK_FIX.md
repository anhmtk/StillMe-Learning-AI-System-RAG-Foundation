# Quick Fix - MiKTeX Dialog Liên Tục Hiện

## Vấn đề

Khi compile LaTeX, MiKTeX liên tục hiện dialog hỏi cài package. Đây là bình thường vì paper cần nhiều packages.

## Giải pháp nhanh nhất (30 giây)

### Cách 1: Tắt Dialog và Để Tự Động Cài

1. **Khi dialog hiện lên:**
   - ✅ **UNCHECK** "Always show this dialog" (bỏ dấu tick)
   - Click **"Install"**

2. **Lần sau:**
   - MiKTeX sẽ tự động cài packages mà không hỏi
   - Chỉ cần chờ compile hoàn tất

### Cách 2: Cài Tất Cả Packages Trước (Khuyến nghị)

1. **Mở MiKTeX Console:**
   - Tìm "MiKTeX Console" trong Start Menu
   - Hoặc chạy: `miktex-console`

2. **Cài packages:**
   - Click tab **"Packages"**
   - Click **"Update"** (hoặc "Synchronize")
   - Chọn **"Update now"** để cài tất cả packages còn thiếu

3. **Hoặc cài từng package:**
   - Search: `booktabs`, `hyperref`, `amsmath`, `graphicx`, `xcolor`, `url`
   - Click "Install" cho mỗi package

4. **Sau khi cài xong:**
   - Chạy lại: `.\compile.ps1`
   - Sẽ không còn dialog nữa

---

## Packages Cần Thiết

Paper cần các packages sau:
- `booktabs` - Table formatting
- `hyperref` - Hyperlinks
- `amsmath`, `amssymb` - Math symbols
- `graphicx` - Figures
- `xcolor` - Colors
- `url` - URLs
- `hycolor` - Required by hyperref
- Và một số packages phụ khác

---

## Nếu Vẫn Còn Dialog

### Kiểm tra MiKTeX Settings:

1. **Mở MiKTeX Console**
2. **Settings** → **General**
3. Đảm bảo:
   - ✅ "Install missing packages on-the-fly: Yes"
   - ✅ "Ask me first: No" (để tự động cài)

### Hoặc cài thủ công:

```powershell
# Mở MiKTeX Console và cài packages:
miktex packages install booktabs
miktex packages install hyperref
miktex packages install amsmath
miktex packages install graphicx
miktex packages install xcolor
miktex packages install url
```

---

## Sau Khi Cài Xong

1. **Chạy lại compile:**
   ```powershell
   .\compile.ps1
   ```

2. **Kết quả:**
   - Không còn dialog
   - Compile tự động hoàn tất
   - File `main.pdf` được tạo

---

## Tips

- **Lần đầu compile** thường mất 5-10 phút (cài packages)
- **Lần sau** chỉ mất 10-30 giây
- **Nếu dialog vẫn hiện**: Cài packages thủ công qua MiKTeX Console

