# 📖 Hướng Dẫn Compile và Cập Nhật Release

## 🔧 Bước 1: Compile main.pdf từ main.tex (Windows với MiKTeX)

### Kiểm tra MiKTeX đã cài đặt:

```powershell
# Mở PowerShell và kiểm tra
pdflatex --version
bibtex --version
```

Nếu chưa có trong PATH, thêm MiKTeX vào PATH hoặc dùng full path:
- MiKTeX thường ở: `C:\Program Files\MiKTeX\miktex\bin\x64\`

### Compile bằng script có sẵn:

```powershell
# Di chuyển vào thư mục arxiv
cd D:\StillMe-Learning-AI-System-RAG-Foundation\arxiv

# Chạy script compile
.\compile.ps1
```

### Hoặc compile thủ công (nếu script không chạy):

```powershell
# Bước 1: Compile lần đầu
pdflatex -interaction=nonstopmode main.tex

# Bước 2: Chạy BibTeX (nếu có references)
bibtex main

# Bước 3: Compile lần 2
pdflatex -interaction=nonstopmode main.tex

# Bước 4: Compile lần 3 (final)
pdflatex -interaction=nonstopmode main.tex
```

### Kiểm tra kết quả:

- File `main.pdf` sẽ được tạo trong thư mục `arxiv/`
- Mở `main.pdf` để kiểm tra:
  - ✅ Tất cả tables hiển thị đúng
  - ✅ Tất cả figures hiển thị đúng
  - ✅ References được đánh số đúng
  - ✅ Metrics mới (35%, 13.5%, 91.1%, 85.8%) đã được cập nhật

### Xử lý lỗi:

Nếu gặp lỗi "package not found":
```powershell
# MiKTeX sẽ tự động cài package khi compile
# Hoặc cài thủ công:
miktex packages install <package-name>
```

---

## 📦 Bước 2: Cập Nhật GitHub Release

### 2.1. Tạo Release mới (Khuyến nghị - Version mới):

1. **Vào GitHub Repository:**
   - Truy cập: `https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation`
   - Click vào **"Releases"** (bên phải)

2. **Tạo Release mới:**
   - Click **"Draft a new release"**
   - Hoặc click **"Create a new release"**

3. **Điền thông tin Release:**
   ```
   Tag: v0.2-paper-updated
   Title: StillMe Preprint v0.2 (Updated Evaluation Results)
   
   Description:
   ## StillMe Preprint v0.2 - Updated Evaluation Results
   
   This release contains the updated preprint of the StillMe framework with latest evaluation results:
   
   **StillMe: A Practical Framework for Building Transparent, Validated Retrieval-Augmented Generation Systems**
   
   ### Key Updates:
   - ✅ Updated evaluation results: 35% accuracy (20-question subset), 13.5% (full 790-question)
   - ✅ Updated citation rate: 91.1% (full evaluation)
   - ✅ Updated transparency score: 85.8% (full evaluation)
   - ✅ All metrics now reflect current system performance
   
   ### Files Included:
   - `main.pdf` - Updated preprint with latest results
   - `main.tex` - LaTeX source (updated)
   - `refs.bib` - Bibliography
   - `figures/` - All figures
   
   ### DOI:
   - **DOI**: https://doi.org/10.5281/zenodo.17637315 (will be updated after Zenodo upload)
   - **Zenodo Record**: https://zenodo.org/records/17637315
   
   ### Overview:
   StillMe is a transparency-first framework designed to transform commercial LLMs into fully auditable systems without any model training or labeled datasets.
   
   This paper introduces:
   - A multi-layer Validation Chain to reduce hallucination
   - A continuous learning pipeline updating every 4 hours (RSS, arXiv, CrossRef, Wikipedia)
   ```

4. **Upload Files:**
   - Kéo thả `main.pdf` vào phần "Attach binaries"
   - Hoặc click "Attach files" và chọn `main.pdf`

5. **Publish Release:**
   - Click **"Publish release"** (hoặc "Save draft" nếu muốn chỉnh sửa sau)

### 2.2. Cập Nhật Release cũ (Nếu muốn giữ cùng version):

1. **Vào Release cũ:**
   - Vào Releases page
   - Click vào release "v0.1-paper" (hoặc release cũ nhất)

2. **Edit Release:**
   - Click icon **✏️ (Edit)** ở góc phải trên

3. **Cập nhật:**
   - Upload `main.pdf` mới (thay thế file cũ)
   - Cập nhật description với metrics mới
   - Click **"Update release"**

---

## 🌐 Bước 3: Cập Nhật Zenodo DOI

### 3.1. Tạo Version mới trên Zenodo (Khuyến nghị):

**Lưu ý:** Zenodo không cho phép cập nhật file đã publish. Phải tạo version mới.

1. **Đăng nhập Zenodo:**
   - Truy cập: https://zenodo.org
   - Đăng nhập bằng GitHub account (nếu đã link)

2. **Tạo Upload mới:**
   - Click **"Upload"** (góc trên bên phải)
   - Hoặc truy cập: https://zenodo.org/deposit/new

3. **Upload Files:**
   - Kéo thả `main.pdf` vào
   - Có thể thêm `main.tex`, `refs.bib`, và `figures/` nếu muốn

4. **Điền Metadata:**
   ```
   Title: StillMe: A Practical Framework for Building Transparent, Validated Retrieval-Augmented Generation Systems
   
   Authors:
   - Anh Nguyen Stillme (Independent Researcher)
   
   Description:
   StillMe is a transparency-first framework designed to transform commercial LLMs into fully auditable systems without any model training or labeled datasets.
   
   This paper introduces:
   - A multi-layer Validation Chain to reduce hallucination
   - A continuous learning pipeline updating every 4 hours (RSS, arXiv, CrossRef, Wikipedia)
   
   Evaluation Results (Updated):
   - Accuracy: 35% (20-question subset), 13.5% (full 790-question evaluation)
   - Citation Rate: 91.1% (full evaluation)
   - Transparency Score: 85.8% (full evaluation)
   - Validation Pass Rate: 93.9% (full evaluation)
   
   Keywords: RAG, Transparency, Validation, Hallucination Reduction, Open Source AI, Continuous Learning
   
   Version: 0.2
   
   Related Identifiers:
   - IsNewVersionOf: 10.5281/zenodo.17637315 (DOI của version cũ)
   ```

5. **Link với GitHub (Optional):**
   - Trong "Related Identifiers", thêm:
     - Type: "IsSupplementTo"
     - Identifier: Link đến GitHub repository

6. **Publish:**
   - Click **"Publish"** (hoặc "Reserve DOI" nếu muốn giữ draft)
   - Zenodo sẽ tạo DOI mới (ví dụ: `10.5281/zenodo.XXXXXXX`)

7. **Cập nhật GitHub Release:**
   - Quay lại GitHub Release
   - Edit và cập nhật DOI mới vào description

### 3.2. Cập nhật Metadata của Record cũ (Nếu không muốn tạo version mới):

**Lưu ý:** Chỉ có thể cập nhật metadata, không thể thay file PDF.

1. **Vào Record cũ:**
   - Truy cập: https://zenodo.org/records/17637315
   - Click **"Edit"** (nếu có quyền)

2. **Cập nhật Description:**
   - Thêm note: "Updated evaluation results available in GitHub Release v0.2"
   - Link đến GitHub Release mới

3. **Save Changes**

---

## ✅ Checklist Đồng Bộ

Sau khi hoàn thành, kiểm tra:

- [ ] `main.pdf` đã được compile với metrics mới (35%, 13.5%, 91.1%, 85.8%)
- [ ] GitHub Release đã được tạo/cập nhật với `main.pdf` mới
- [ ] GitHub Release description có DOI mới (nếu tạo version mới trên Zenodo)
- [ ] Zenodo record đã được tạo/cập nhật
- [ ] Tất cả links giữa GitHub và Zenodo đều hoạt động
- [ ] `docs/PAPER.md`, `arxiv/main.tex`, và `README.md` đều có metrics giống nhau

---

## 🔗 Links Tham Khảo

- **MiKTeX Documentation**: https://miktex.org/kb/faq
- **GitHub Releases Guide**: https://docs.github.com/en/repositories/releasing-projects-on-github
- **Zenodo Guide**: https://help.zenodo.org/
- **Zenodo Versioning**: https://help.zenodo.org/#versioning

---

## 💡 Tips

1. **Version Numbering:**
   - GitHub Release: `v0.2-paper-updated`
   - Zenodo Version: `0.2`
   - Giữ consistency giữa hai platforms

2. **DOI Best Practice:**
   - Mỗi version mới trên Zenodo sẽ có DOI riêng
   - DOI cũ vẫn hoạt động và trỏ đến version cũ
   - Có thể link versions bằng "IsNewVersionOf"

3. **File Naming:**
   - GitHub: `StillMe-Preprint-v0.2.pdf` (optional, có thể giữ `main.pdf`)
   - Zenodo: Zenodo sẽ tự đặt tên, nhưng có thể customize

4. **Backup:**
   - Giữ backup của `main.pdf` cũ trước khi upload mới
   - Commit `main.pdf` vào git (optional, thường không commit PDF)

