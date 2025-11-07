# Fix Dashboard Config-as-Code Issue

## 🔍 Vấn đề

- Dashboard service đang chạy backend command (không phải `python start_dashboard.py`)
- Không thể sửa Custom Start Command (bị lock)
- Thử add `/railway.json.dashboard-only` vào Config-as-Code nhưng Railway báo lỗi: `invalid config file extension: .dashboard-only`

## ✅ Giải pháp

### Bước 1: Tạo file `railway-dashboard.json`

File `railway-dashboard.json` đã được tạo trong repo với config đúng cho dashboard:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "python start_dashboard.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Bước 2: Push file lên GitHub

```bash
git add railway-dashboard.json
git commit -m "Add: railway-dashboard.json for dashboard service config"
git push
```

### Bước 3: Cấu hình Config-as-Code trên Railway

1. **Dashboard service** → **Settings** → **Config-as-Code**
2. Trong field **"Railway Config File"**, nhập:
   ```
   /railway-dashboard.json
   ```
3. **Save**

→ Railway sẽ tự động detect file và apply config (start command: `python start_dashboard.py`)

### Bước 4: Redeploy

1. **Dashboard service** → **Deployments**
2. Click **"Redeploy"** hoặc đợi Railway tự động redeploy
3. Kiểm tra logs xem có "Starting Streamlit dashboard..." không

## 🔄 Alternative: Disable Config-as-Code (Nếu vẫn không được)

Nếu vẫn không được, thử disable Config-as-Code hoàn toàn:

1. **Dashboard service** → **Settings** → **Config-as-Code**
2. **Xóa hoàn toàn** path trong field "Railway Config File" (để trống)
3. **Save**
4. Bây giờ bạn có thể sửa **Custom Start Command** thủ công:
   - **Settings** → **Deploy** → **Custom Start Command**
   - Sửa thành: `python start_dashboard.py`
   - **Save**

## 📊 Kiểm tra sau khi fix

1. **Logs** phải có:
   ```
   Starting Streamlit dashboard on port...
   ```

2. **Truy cập URL** phải thấy Streamlit UI, không phải JSON response

3. **Custom Start Command** phải là:
   ```
   python start_dashboard.py
   ```

## 🚨 Lưu ý

- Railway chỉ chấp nhận file config với extension: `.json`, `.toml`, `.yaml`, `.yml`
- Không chấp nhận: `.dashboard-only`, `.backend-only`, etc.
- Nếu có nhiều services, mỗi service nên có file config riêng:
  - Backend: `railway.json` hoặc `railway-backend.json`
  - Dashboard: `railway-dashboard.json`

