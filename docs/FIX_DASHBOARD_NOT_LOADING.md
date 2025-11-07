# Fix Dashboard Not Loading - Trả về JSON thay vì Streamlit UI

## 🔍 Vấn đề

Truy cập `https://dashboard-production-e4ca.up.railway.app` nhưng thấy JSON response từ API endpoint `/` thay vì Streamlit dashboard UI.

## 🔬 Nguyên nhân có thể

1. **Dashboard service đang chạy sai start command** (chạy backend code thay vì dashboard)
2. **Config-as-Code đang dùng `railway.json`** (backend config) thay vì dashboard config
3. **Dashboard service bị crash** → Railway route traffic đến backend service
4. **Dashboard service chưa start đúng cách**

## ✅ Giải pháp

### Bước 1: Kiểm tra Logs của Dashboard Service

1. Railway Dashboard → Service **"dashboard"**
2. Tab **"Logs"**
3. Tìm dòng:
   ```
   Starting Streamlit dashboard on port...
   ```
   
**Nếu KHÔNG thấy dòng này:**
- Dashboard service đang chạy sai command
- Xem Bước 2

**Nếu thấy lỗi:**
- Ghi lại lỗi và xem Bước 3

### Bước 2: Kiểm tra Start Command

1. Service **"dashboard"** → **Settings** → **Deploy**
2. Xem **"Custom Start Command"**
3. Phải là:
   ```
   python start_dashboard.py
   ```
   
**Nếu SAI (ví dụ: `python start_backend.py`):**
1. Sửa thành: `python start_dashboard.py`
2. **Save**
3. Railway sẽ tự động redeploy

### Bước 3: Kiểm tra Config-as-Code

1. Service **"dashboard"** → **Settings** → **Config-as-code**
2. Xem **"Railway Config File"** path
3. **Nếu là `/railway.json`:** Đây là vấn đề!
   - File `railway.json` dành cho backend (`start_backend.py`)
   - Dashboard cần dùng `railway.json.dashboard-only` hoặc để trống
4. **Sửa:**
   - Xóa path (để trống) HOẶC
   - Đổi thành: `/railway.json.dashboard-only`
5. **Save**

### Bước 4: Restart Dashboard Service

1. Service **"dashboard"** → Tab **"Deployments"**
2. Click **"Restart"** hoặc **"Redeploy"**
3. Đợi deploy xong
4. Kiểm tra logs xem có "Starting Streamlit dashboard..." không

### Bước 5: Kiểm tra Environment Variables

1. Service **"dashboard"** → **Settings** → **Variables**
2. Đảm bảo có:
   ```
   STILLME_API_BASE=https://stillme-backend-production-xxxx.up.railway.app
   ```
   (Thay `xxxx` bằng URL thực tế của backend service)

## 🔍 Debug Checklist

- [ ] Logs có "Starting Streamlit dashboard on port..."?
- [ ] Start command là `python start_dashboard.py`?
- [ ] Config-as-Code path KHÔNG phải `/railway.json`?
- [ ] Environment variable `STILLME_API_BASE` đã set?
- [ ] Service đã restart sau khi sửa?

## 📊 Logs mong đợi (khi dashboard chạy đúng)

```
Starting Streamlit dashboard on port 8080...
API_BASE: https://stillme-backend-production-xxxx.up.railway.app

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8080
  Network URL: http://0.0.0.0:8080
```

## 🚨 Nếu vẫn không được

1. **Kiểm tra URL:** Đảm bảo đang truy cập đúng URL của dashboard service (không phải backend)
2. **Kiểm tra Networking:** Dashboard service → Settings → Networking → Xem public URL
3. **Thử truy cập:** URL phải khác với backend URL

## 💡 Tip

Nếu dashboard service và backend service có cùng URL → Có thể Railway đang route sai. Tạo service mới hoặc kiểm tra networking settings.

