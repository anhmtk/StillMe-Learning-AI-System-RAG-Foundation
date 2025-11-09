# Railway Project Structure - Giải thích

## 🏗️ Cấu trúc Railway

Railway có cấu trúc 2 tầng:
```
Railway Account (anhmtk)
  └── Projects (athletic-victory, beautiful-alignment, successful-healing)
      └── Services (stillme-backend, dashboard, web-production, ...)
```

## 📊 Projects của bạn

### 1. **athletic-victory** (Project chính - Đang dùng)
- **Mục đích**: Project chính cho StillMe
- **Services**: 
  - `stillme-backend` (Backend API)
  - `dashboard` hoặc tên khác (Dashboard Streamlit) - **Cần kiểm tra**

### 2. **beautiful-alignment** (Project cũ/test?)
- **Mục đích**: Có thể là project test hoặc cũ
- **Services**:
  - `dashboard` 
  - `web-production-d638c` (URL: `web-production-d638c.up.railway.app`)

### 3. **successful-healing** (Project cũ/test?)
- **Mục đích**: Có thể là project test hoặc cũ
- **Services**:
  - `dashboard`
  - `web-production-78ed` (URL: `web-production-78ed.up.railway.app`)

## 🔍 Tìm Dashboard Service trong athletic-victory

### Bước 1: Vào Project athletic-victory

1. **Railway Dashboard** → Click vào project **"athletic-victory"**
2. Bạn sẽ thấy danh sách **Services** trong project này

### Bước 2: Kiểm tra Services

Trong project **athletic-victory**, bạn sẽ thấy:
- ✅ **stillme-backend** (chắc chắn có)
- ❓ **Dashboard service** (có thể có tên khác hoặc chưa có)

**Các tên có thể:**
- `dashboard`
- `stillme-dashboard`
- `dashboard-production`
- Hoặc tên khác bạn đã đặt

### Bước 3: Nếu không thấy Dashboard Service

**Có 2 khả năng:**

#### Khả năng 1: Dashboard service chưa được tạo
→ Cần tạo service mới trong project `athletic-victory`

#### Khả năng 2: Dashboard đang chạy trong project khác
→ Có thể dashboard đang chạy trong `beautiful-alignment` hoặc `successful-healing`

## ✅ Giải pháp: Tìm hoặc Tạo Dashboard Service

### Option A: Tìm Dashboard trong athletic-victory

1. **athletic-victory** → Xem danh sách services
2. Tìm service có:
   - **Start Command**: `python start_dashboard.py`
   - **URL**: Có thể là `dashboard-production-xxx.up.railway.app`
   - **Logs**: Có dòng `Starting Streamlit dashboard...`

### Option B: Dashboard đang chạy trong project khác

Nếu dashboard đang chạy trong `beautiful-alignment` hoặc `successful-healing`:

1. **Vào project đó** → **dashboard** service
2. **Settings** → **Source**
3. Kiểm tra **GitHub Repository**:
   - Nếu là repo `StillMe-Learning-AI-System-RAG-Foundation` → Đây là dashboard của bạn
   - Nếu là repo khác → Đây là project khác

### Option C: Tạo Dashboard Service mới trong athletic-victory

Nếu không tìm thấy dashboard service:

1. **athletic-victory** → Click **"+ New"** hoặc **"+ Service"**
2. Chọn **"GitHub Repo"**
3. Chọn repo: `anhmtk/StillMe-Learning-AI-System-RAG-Foundation`
4. Railway sẽ tự động detect và tạo service
5. **Settings** → **Deploy** → **Custom Start Command**
6. Set: `python start_dashboard.py`
7. **Save** → Railway sẽ deploy

## 🔍 Xác định Dashboard Service đang chạy

### Cách 1: Kiểm tra URL Dashboard

1. Mở dashboard URL bạn đang dùng (ví dụ: `dashboard-production-xxx.up.railway.app`)
2. **Railway Dashboard** → Tìm service có URL này
3. Service đó chính là dashboard service của bạn

### Cách 2: Kiểm tra Logs

1. Vào từng service trong các projects
2. **Logs** tab
3. Tìm service có log: `Starting Streamlit dashboard...` hoặc `Running on http://0.0.0.0:8080`
4. Service đó chính là dashboard

## 💡 Lưu ý

- **Mỗi project có services riêng** - Không thể share services giữa projects
- **Dashboard và Backend phải cùng project** để dễ quản lý
- **beautiful-alignment và successful-healing** có thể là projects cũ/test - Có thể xóa nếu không dùng

## ✅ Checklist

- [ ] Đã vào project **athletic-victory**
- [ ] Đã kiểm tra danh sách services
- [ ] Đã tìm thấy dashboard service (hoặc đã tạo mới)
- [ ] Dashboard service có Start Command: `python start_dashboard.py`
- [ ] Dashboard service đã deploy commit mới nhất (`d559319d6`)

