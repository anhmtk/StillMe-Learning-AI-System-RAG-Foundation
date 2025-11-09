# Fix: Railway Config File Path Error

## 🔍 Vấn đề

- Build logs báo: `config file /railway-backend.json does not exist`
- Build logs báo: `config file /railway-dashboard.json does not exist`
- Deploy logs: "No logs in this time range"
- **NHƯNG**: Service vẫn hoạt động bình thường (dashboard vẫn xem được, chat vẫn được)

## 🔬 Nguyên nhân

Railway đang tìm file với **absolute path** (`/railway-backend.json`) nhưng file thực tế ở **root** (`railway-backend.json`).

Railway Config-as-Code path format:
- ❌ **Sai**: `/railway-backend.json` (absolute path - tìm ở root filesystem)
- ✅ **Đúng**: `railway-backend.json` (relative path - tìm ở repo root)

## ✅ Giải pháp: Sửa Config-as-Code Path

### Bước 1: Sửa Backend Service

1. **Railway Dashboard** → **stillme-backend** service → **Settings** → **Config-as-Code**
2. Trong field **"Railway Config File"**, sửa từ:
   ```
   /railway-backend.json
   ```
   Thành:
   ```
   railway-backend.json
   ```
   (Bỏ dấu `/` ở đầu)
3. **Save**

### Bước 2: Sửa Dashboard Service

1. **Railway Dashboard** → **dashboard** service → **Settings** → **Config-as-Code**
2. Trong field **"Railway Config File"**, sửa từ:
   ```
   /railway-dashboard.json
   ```
   Thành:
   ```
   railway-dashboard.json
   ```
   (Bỏ dấu `/` ở đầu)
3. **Save**

### Bước 3: Redeploy

1. **Backend service** → **Deployments** → **Redeploy**
2. **Dashboard service** → **Deployments** → **Redeploy**
3. Kiểm tra build logs - không còn lỗi "does not exist"

## 🔄 Alternative: Disable Config-as-Code (Nếu không cần)

Nếu Custom Start Command đã đúng rồi, bạn có thể disable Config-as-Code:

### Backend Service:
1. **Settings** → **Config-as-Code**
2. **Xóa hoàn toàn** path (để trống)
3. **Settings** → **Deploy** → **Custom Start Command**
4. Verify: `python start_backend.py`
5. **Save**

### Dashboard Service:
1. **Settings** → **Config-as-Code**
2. **Xóa hoàn toàn** path (để trống)
3. **Settings** → **Deploy** → **Custom Start Command**
4. Verify: `python start_dashboard.py`
5. **Save**

## 📊 Kết quả mong đợi

Sau khi sửa path hoặc disable Config-as-Code:
- ✅ Build logs không còn lỗi "config file does not exist"
- ✅ Deploy logs hiển thị bình thường
- ✅ Service vẫn hoạt động như cũ (không bị ảnh hưởng)

## 💡 Lưu ý

- Lỗi này chỉ là **warning** trong build logs, không ảnh hưởng đến runtime
- Service vẫn hoạt động vì Custom Start Command đã được set thủ công
- Config-as-Code chỉ cần thiết nếu bạn muốn Railway tự động apply config từ file

