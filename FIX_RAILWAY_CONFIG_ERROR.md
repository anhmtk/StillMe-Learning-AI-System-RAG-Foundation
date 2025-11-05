# 🔧 Fix Railway Build Error: "config file does not exist"

## **Vấn đề:**
```
config file /railway-disabled.toml does not exist
```

**Nguyên nhân:** 
- Railway vẫn đang tìm config file `/railway-disabled.toml`
- File không tồn tại → Build failed ❌

---

## **✅ Giải pháp: Xóa hoàn toàn config path**

### **Bước 1: Fix Config-as-code**

1. **Service → Settings → Config-as-code**
2. Tìm input field **"Railway Config File"**
3. **XÓA HOÀN TOÀN** tất cả text trong field → Để trống
4. **Save**

→ Railway sẽ skip config file → Không tìm nữa → Build OK ✅

---

### **Bước 2: Verify Command**

1. **Settings → Deploy → Custom Start Command**
2. Verify command là:
   ```
   python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
   ```
3. **Save** (nếu cần)

---

### **Bước 3: Redeploy**

1. **Tab "Deployments"**
2. Click **"Redeploy"** hoặc **"Deploy"**
3. Railway sẽ build lại → Nên thành công!

---

## **Giải thích PORT Variable:**

**Không cần set PORT variable manual!**

- Railway tự động tạo `PORT` environment variable
- Giá trị: `8080`, `8081`, hoặc random
- Railway inject vào container → Service dùng `$PORT` trong command

**Trong command:**
```bash
--port $PORT
```

→ Railway tự động thay `$PORT` → `8080` (hoặc port khác)
→ FastAPI sẽ listen trên port đó

**Check PORT variable (nếu muốn):**
- Settings → Variables
- Sẽ thấy `PORT=8080` (Railway tự động tạo)
- Không cần edit!

---

**Done!** 🎉

