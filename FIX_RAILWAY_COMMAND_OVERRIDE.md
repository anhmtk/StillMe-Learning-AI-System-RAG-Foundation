# 🔧 Fix Railway Command Auto-Override Issue

## **Vấn đề:**
Railway tự động override Custom Start Command từ `railway.json` mỗi khi deploy service mới từ GitHub repo.

**Triệu chứng:**
- Set command trong UI: `python -m uvicorn backend.api.main:app...`
- Sau deploy → Command tự đổi lại: `python start_dashboard.py`
- Xảy ra 3 lần liên tục → Frustrating!

---

## **Nguyên nhân:**
Railway tự động apply `railway.json` cho **MỌI service** từ cùng GitHub repo (không chỉ service đầu tiên).

---

## **✅ Giải pháp: Disable Config-as-Code**

### **Bước 1: Tạo Empty Service (không phải GitHub Repo)**

1. Architecture view → **"+ Create"**
2. Chọn **"Empty Service"** (KHÔNG chọn "GitHub Repo")

### **Bước 2: Disable Config-as-Code (QUAN TRỌNG - Làm ngay!)**

**⚠️ Railway UI đã thay đổi - không có checkbox "Enable config from code"**

**Giải pháp thực tế:**

1. **Service mới → Settings → Config-as-code**
2. Tìm phần **"Railway Config File"**
3. Input field hiển thị path: `/railway.toml` hoặc `/railway.json`
4. **Xóa path** (để trống) hoặc đổi thành: `/railway-disabled.toml`
5. **Save**

→ Railway sẽ không tìm thấy config file → KHÔNG auto-apply!

**Hoặc nếu vẫn bị override:**
- Rename `railway.json` tạm thời: `railway.json.dashboard-only`
- Push lên GitHub
- Railway sẽ không detect config file → Command giữ nguyên

### **Bước 3: Connect GitHub Repo (sau khi đã disable)**

1. **Settings → Source**
2. Click **"Connect Repo"**
3. Chọn: `StillMe---Self-Evolving-AI-System`
4. **KHÔNG chọn "Apply railway.json"** nếu có option

### **Bước 4: Set Command (bây giờ sẽ giữ nguyên!)**

1. **Settings → Deploy → Custom Start Command**
2. Paste:
   ```
   python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
   ```
3. **Save**

→ Command sẽ KHÔNG bị override nữa! ✅

---

## **Tóm tắt:**

| Vấn đề | Giải pháp |
|--------|-----------|
| Railway auto-apply `railway.json` | Disable Config-as-code |
| Command bị override | Tạo Empty Service → Disable config → Set command |
| Service mới từ GitHub repo | Connect repo SAU khi disable config |

---

**Done!** 🎉

