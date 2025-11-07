# Fix: Config file /railway-dashboard.json does not exist

## 🔍 Vấn đề

- File `railway-dashboard.json` đã được push lên GitHub
- Đã set Config-as-Code path: `/railway-dashboard.json`
- Custom Start Command đã có: `python start_dashboard.py`
- Nhưng deploy vẫn báo: `config file /railway-dashboard.json does not exist`

## ✅ Giải pháp: Disable Config-as-Code (Vì command đã đúng rồi!)

Vì Custom Start Command đã là `python start_dashboard.py` (đúng rồi), bạn không cần Config-as-Code nữa. Chỉ cần disable nó:

### Bước 1: Disable Config-as-Code

1. **Dashboard service** → **Settings** → **Config-as-Code**
2. **Xóa hoàn toàn** path trong field "Railway Config File" (để trống)
3. **Save**

→ Railway sẽ không tìm config file nữa → Không báo lỗi → Command hiện tại (`python start_dashboard.py`) sẽ giữ nguyên!

### Bước 2: Verify Custom Start Command

1. **Dashboard service** → **Settings** → **Deploy**
2. Kiểm tra **Custom Start Command** phải là:
   ```
   python start_dashboard.py
   ```
3. Nếu đúng rồi → Không cần làm gì thêm!
4. Nếu sai → Sửa thành `python start_dashboard.py` → **Save**

### Bước 3: Redeploy

1. **Dashboard service** → **Deployments**
2. Click **"Redeploy"**
3. Kiểm tra logs xem có "Starting Streamlit dashboard..." không

## 🔍 Tại sao Config-as-Code không work?

Có thể do:
1. **Railway cache:** Railway chưa pull code mới từ GitHub
2. **Timing issue:** File vừa được push, Railway chưa detect
3. **Path issue:** Railway có thể tìm file ở location khác

Nhưng **không sao** - vì Custom Start Command đã đúng rồi, bạn không cần Config-as-Code!

## 💡 Tip

Config-as-Code chỉ cần thiết khi:
- Bạn muốn Railway tự động apply config từ file
- Bạn không muốn set command thủ công

Nếu Custom Start Command đã đúng, **disable Config-as-Code** là giải pháp đơn giản nhất!

## ✅ Kết quả mong đợi

Sau khi disable Config-as-Code và redeploy:
- ✅ Không còn lỗi "config file does not exist"
- ✅ Custom Start Command: `python start_dashboard.py` (giữ nguyên)
- ✅ Logs có: "Starting Streamlit dashboard..."
- ✅ Dashboard load đúng Streamlit UI

