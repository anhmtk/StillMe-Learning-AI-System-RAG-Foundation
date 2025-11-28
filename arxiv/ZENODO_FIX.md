# 🔧 Fix Lỗi Zenodo: "Invalid ARK identifier"

## ❌ Vấn Đề

Khi publish lên Zenodo, bạn gặp lỗi:
- "The draft was not published. Record saved with validation feedback"
- "Invalid ARK identifier" trong phần "Alternate identifiers"

## 🔍 Nguyên Nhân

Bạn đã nhập **DOI** (`10.5281/zenodo.17637315`) vào field **"Alternate identifiers"** với scheme **"ARK"**, nhưng:
- DOI không phải là ARK identifier
- DOI phải được nhập vào **"Related identifiers"** với scheme **"DOI"**

## ✅ Cách Sửa

### Bước 1: Xóa Entry Sai

1. Scroll xuống phần **"Alternate identifiers"**
2. Tìm entry có identifier `10.5281/zenodo.17637315` với scheme `ARK`
3. Click icon **"X"** (góc phải) để **xóa entry này**

### Bước 2: Thêm Vào Related Identifiers (Đúng Chỗ)

1. Scroll xuống phần **"Related identifiers"** (KHÔNG phải "Alternate identifiers")
2. Click button **"Add identifier"**
3. Điền thông tin:
   ```
   Identifier: 10.5281/zenodo.17637315
   Relation type: IsNewVersionOf (hoặc IsVersionOf)
   Scheme: DOI
   ```
4. Click **"Add identifier"** để lưu

### Bước 3: Kiểm Tra Lại

- ✅ Không còn entry nào trong "Alternate identifiers" (hoặc chỉ có ARK/Handle thật sự)
- ✅ "Related identifiers" có entry với:
  - Identifier: `10.5281/zenodo.17637315`
  - Scheme: `DOI`
  - Relation type: `IsNewVersionOf`

### Bước 4: Publish Lại

1. Scroll lên đầu form
2. Click **"Publish"** (hoặc "Reserve DOI" nếu muốn draft)
3. Lần này sẽ không còn lỗi validation

## 📋 Phân Biệt Các Loại Identifiers

### Alternate Identifiers
- Dùng cho: ARK, Handle, PURL, ISBN, etc.
- **KHÔNG dùng cho DOI**
- Ví dụ hợp lệ:
  - ARK: `ark:/13030/qt5x97x9z3`
  - Handle: `hdl:10214/17925`

### Related Identifiers
- Dùng để link với: version cũ, GitHub repo, arXiv, etc.
- **DOI nên được nhập ở đây**
- Relation types phổ biến:
  - `IsNewVersionOf`: Version mới của record cũ
  - `IsVersionOf`: Version của record khác
  - `IsSupplementTo`: Link đến GitHub repo, dataset, etc.
  - `Cites`: Trích dẫn paper khác

## 🎯 Ví Dụ Đúng

### Related Identifiers (Đúng):
```
Identifier: 10.5281/zenodo.17637315
Relation type: IsNewVersionOf
Scheme: DOI
```

```
Identifier: https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation
Relation type: IsSupplementTo
Scheme: URL
```

### Alternate Identifiers (Nếu cần):
```
Identifier: ark:/13030/qt5x97x9z3
Scheme: ARK
```

## ⚠️ Lưu Ý

- **Alternate identifiers** và **Related identifiers** là 2 phần KHÁC NHAU
- DOI luôn đi vào **Related identifiers**, không bao giờ vào **Alternate identifiers**
- Nếu không chắc, chỉ cần điền **Related identifiers** với DOI của version cũ là đủ

## 🔗 Tham Khảo

- [Zenodo Related Identifiers Guide](https://help.zenodo.org/#versioning)
- [DOI vs ARK](https://www.doi.org/factsheets/DOIIdentifierSpecs.html)

