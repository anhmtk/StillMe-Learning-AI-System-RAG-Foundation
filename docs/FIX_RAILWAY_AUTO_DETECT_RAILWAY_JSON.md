# Fix: Railway Auto-Detect railway.json After Removing Config-as-Code

## 🔍 Vấn đề

- Khi có Config-as-Code path: Custom Start Command = `python start_dashboard.py` ✅
- Sau khi xóa Config-as-Code path và redeploy: Custom Start Command tự động đổi thành `python start_backend.py` ❌
- Railway tự động detect `railway.json` từ repo ngay cả khi Config-as-Code path bị xóa

## 🔬 Nguyên nhân

Railway có behavior mặc định:
- **Tự động tìm** `railway.json` hoặc `railway.toml` trong repo root
- **Tự động apply** config từ file đó cho MỌI service từ cùng repo
- Không cần Config-as-Code path - Railway tự detect!

→ Đây là lý do tại sao dashboard service bị apply config của backend.

## ✅ Giải pháp: Rename railway.json

### Bước 1: Rename railway.json tạm thời

```bash
git mv railway.json railway-backend.json
git commit -m "Rename railway.json to railway-backend.json to prevent auto-detect for dashboard service"
```

### Bước 2: Push lên GitHub

```bash
.\scripts\push_with_token.ps1
```

### Bước 3: Cấu hình lại trên Railway

#### Backend Service:
1. **stillme-backend** → **Settings** → **Config-as-Code**
2. Set path: `/railway-backend.json`
3. **Save**

#### Dashboard Service:
1. **dashboard** → **Settings** → **Config-as-Code**
2. **Để trống** (không set path)
3. **Settings** → **Deploy** → **Custom Start Command**
4. Set: `python start_dashboard.py`
5. **Save**

### Bước 4: Redeploy cả 2 services

→ Bây giờ Railway sẽ không auto-detect `railway.json` nữa (vì file không tồn tại)
→ Dashboard service sẽ dùng Custom Start Command thủ công
→ Backend service sẽ dùng config từ `railway-backend.json`

## 🔄 Alternative: Giữ nguyên railway.json nhưng disable cho dashboard

Nếu không muốn rename, có thể:

1. **Dashboard service** → **Settings** → **Source**
2. **Disconnect GitHub Repo**
3. **Reconnect** nhưng **KHÔNG chọn "Apply railway.json"** (nếu có option)
4. Set Custom Start Command: `python start_dashboard.py`
5. **Save**

→ Dashboard service sẽ không auto-detect `railway.json` nữa

## 📊 Kết quả mong đợi

Sau khi rename `railway.json` → `railway-backend.json`:
- ✅ Backend service: Dùng `/railway-backend.json` (có volume config)
- ✅ Dashboard service: Dùng Custom Start Command `python start_dashboard.py`
- ✅ Railway không còn auto-detect `railway.json`
- ✅ Dashboard load đúng Streamlit UI

## 💡 Tip

Railway auto-detect behavior:
- Tìm file: `railway.json`, `railway.toml`, `railway.yaml`, `railway.yml`
- Apply cho: TẤT CẢ services từ cùng repo
- Không cần Config-as-Code path - tự động!

→ Nếu có nhiều services với config khác nhau, nên:
- Rename file config để tránh auto-detect
- Hoặc dùng Config-as-Code path để chỉ định file cụ thể

