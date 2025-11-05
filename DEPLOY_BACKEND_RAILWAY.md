# 🚀 Deploy StillMe Backend trên Railway - Step by Step

## **📋 Checklist**

- [ ] Tạo Backend Service
- [ ] Configure Start Command
- [ ] Set Environment Variables
- [ ] Generate Public Domain
- [ ] Update Dashboard với Backend URL
- [ ] Test kết nối

---

## **Step 1: Tìm hoặc Tạo Project chứa Dashboard**

### **Tình huống của bạn: Chưa có Project → Tạo mới**

1. **Tại trang Railway Dashboard:**
   - Bạn thấy button **"Deploy New Project"** (hoặc **"New Project"**)
   - **Click vào button này**

2. **Chọn Source:**
   - Railway sẽ hỏi: **"What do you want to deploy?"**
   - Chọn: **"Deploy from GitHub repo"** (hoặc **"GitHub"**)

3. **Chọn Repository:**
   - Railway sẽ hiển thị danh sách repos của bạn
   - Tìm và chọn: `StillMe---Self-Evolving-AI-System`
   - Hoặc search: `StillMe`
   - **Click vào repo đó**

4. **Railway sẽ tự động:**
   - Tạo project mới
   - Detect `railway.json` → Deploy dashboard service
   - Bạn sẽ thấy service **"dashboard"** đang build/deploy

5. **Đợi Dashboard deploy xong:**
   - Xem tab **"Deployments"** để theo dõi
   - Khi thấy **"Deployment successful"** → Bước tiếp theo

---

## **Step 2: Kiểm tra Service "web" có phải Backend không?**

**Tình huống:** Railway đã tạo service **"web"** khi bạn click "New"

### **Cách kiểm tra:**

1. **Click vào service "web"** trong Architecture view

2. **Check Settings → Deploy → Start Command:**
   - Nếu thấy: `python start_dashboard.py` → Đây là dashboard (nhầm) ❌
   - Nếu thấy: `python -m uvicorn backend.api.main:app...` → Đây là backend ✅
   - Nếu thấy command khác hoặc empty → Cần configure (xem Step 3)

3. **Hoặc check URL (nếu đã generate domain):**
   - Vào URL của service "web"
   - Nếu thấy **Swagger UI** (`/docs`) → Đây là backend ✅
   - Nếu thấy Streamlit dashboard → Đây là dashboard (nhầm) ❌

---

## **Step 2A: Nếu "web" là Backend (đúng rồi!)**

1. **Rename Service:**
   - Service "web" → Settings → Service Name
   - Đổi thành: `stillme-backend` (hoặc `backend`)
   - **Save**

2. **Skip Step 3** → Chuyển sang **Step 4** (Set Environment Variables)

---

## **Step 2B: Nếu "web" là Dashboard (trùng lặp - cần fix)**

**Tình huống của bạn:** Service "web" đang chạy `python start_dashboard.py` → Trùng với service "dashboard"

### **Option 1: Xóa service "web" và tạo Backend mới (Khuyên dùng ✅)**

**Tại sao chọn Option 1:**
- `railway.json` đang set command cho dashboard
- Nếu edit `railway.json` → Cả dashboard và backend sẽ dùng chung command → Conflict
- Tạo service mới → Configure riêng trong Railway UI → Không ảnh hưởng dashboard

**Các bước:**

1. **Xóa service "web":**
   - Click vào service "web"
   - Tab **"Settings"** → Scroll xuống cuối
   - Tìm section **"Danger Zone"**
   - Click **"Delete Service"** → Xác nhận xóa

2. **Tạo Backend Service mới - QUAN TRỌNG: Tạo từ Empty Service!**

   **⚠️ KHÔNG chọn "GitHub Repo"** (vì sẽ auto-apply `railway.json`)
   
   Thay vào đó:
   - Architecture view → Click **"+ Create"** button
   - Chọn **"Empty Service"** (KHÔNG phải "GitHub Repo")
   - Railway tạo empty service → Chuyển sang **Step 3**

3. **Connect GitHub Repo sau:**
   - Service mới → Settings → Source
   - Click **"Connect Repo"** hoặc **"Connect GitHub"**
   - Chọn: `StillMe---Self-Evolving-AI-System`
   - **KHÔNG chọn "Use railway.json"** nếu có option này

**Lưu ý:** Tạo từ Empty Service → Configure manual → Railway sẽ KHÔNG auto-apply `railway.json` → Command bạn set sẽ giữ nguyên!

---

### **Option 2: Convert service "web" thành Backend (Không khuyến khích ⚠️)**

**Vấn đề:** Railway đọc từ `railway.json` → Không thể edit trong UI. Nếu edit `railway.json`:
- Cả dashboard và backend sẽ dùng chung command → Conflict ❌
- Cần edit trên GitHub (cần quyền) → Phức tạp hơn

**Nếu vẫn muốn dùng Option 2:**

1. **Edit `railway.json` local và push:**
   ```powershell
   cd "D:\StillMe - Self-Evolving AI System"
   # Edit railway.json: Đổi startCommand thành backend command
   ```
   ```json
   "startCommand": "python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT"
   ```

2. **Commit và Push:**
   ```powershell
   git add railway.json
   git commit -m "fix: Change railway.json to backend command"
   git push origin main
   ```

3. **⚠️ Vấn đề:** 
   - Service "dashboard" cũng sẽ dùng backend command → Cần override riêng
   - Service "dashboard" → Settings → Deploy → Override command → `python start_dashboard.py`

**→ Khuyên dùng Option 1 để tránh conflict!**

---

## **Step 3: Configure Backend Service (QUAN TRỌNG - Làm đúng thứ tự!)**

**Nếu bạn đã tạo Empty Service:**

### **3.1 Disable Config-as-Code (QUAN TRỌNG - Làm trước!)**

**Railway UI đã thay đổi - không có checkbox "Enable config from code"**

**Giải pháp:** Xóa hoàn toàn config file path (QUAN TRỌNG - để trống!):

1. **Service mới → Settings → Config-as-code:**
   - Tìm phần **"Railway Config File"**
   - Input field hiển thị: `/railway.toml` hoặc `/railway.json` hoặc `/railway-disabled.toml`
   - **XÓA HOÀN TOÀN** path này → Để trống (không có gì cả)
   - **Save**

→ Railway sẽ không tìm config file → KHÔNG auto-apply → Command bạn set sẽ giữ nguyên!

**⚠️ Lưu ý:** 
- KHÔNG đặt path không tồn tại như `/railway-disabled.toml` → Railway vẫn tìm file → Build failed ❌
- PHẢI để trống hoàn toàn → Railway skip config file → Build OK ✅

**Hoặc cách 2 (nếu không thấy input):**
- Chỉ cần set command trong UI → Railway có thể vẫn override
- Nếu vẫn bị override → Cần rename `railway.json` trong repo tạm thời

---

### **3.2 Check Config-as-code (QUAN TRỌNG - Verify đã disable!)**

1. **Service "stillme-backend" → Settings → Config-as-code:**
   - Check input field **"Railway Config File"**
   - **PHẢI để trống hoàn toàn** (không có gì cả)
   - Nếu vẫn có `/railway.json` hoặc path khác → Xóa hết → Save

2. **Nếu vẫn không edit được command:**
   - Có thể service được tạo từ GitHub repo → Railway vẫn apply `railway.json`
   - Cần disconnect và reconnect repo (xem Step 3.2A)

---

### **3.2A: Disconnect và Reconnect GitHub Repo (Nếu Config-as-code vẫn không work)**

**Nếu đã xóa config path nhưng vẫn không edit được command:**

1. **Disconnect GitHub Repo:**
   - Service "stillme-backend" → Settings → Source
   - Tìm button **"Disconnect"** hoặc **"Disconnect Repo"**
   - Click → Xác nhận disconnect

2. **Reconnect GitHub Repo (KHÔNG apply railway.json):**
   - Settings → Source → Click **"Connect Repo"**
   - Chọn: `StillMe---Self-Evolving-AI-System`
   - **QUAN TRỌNG:** Nếu có option **"Apply railway.json"** hoặc **"Use config file"** → **UNCHECK/BỎ TÍCH**
   - Connect

3. **Sau khi reconnect:**
   - Settings → Deploy → Custom Start Command
   - Bây giờ sẽ edit được → Set command đúng:
     ```
     python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
     ```
   - Save

**⚠️ Nếu vẫn không edit được sau khi reconnect:**
- Railway vẫn có thể detect `railway.json` từ repo
- Cần dùng **Giải pháp 2**: Rename `railway.json` trong repo (xem Step 3.2B)

---

### **3.2B: Rename railway.json trong Repo (Nếu disconnect/reconnect không work)**

**Nếu đã reconnect nhưng vẫn không edit được command:**

1. **Rename railway.json trong repo:**
   ```powershell
   cd "D:\StillMe - Self-Evolving AI System"
   git mv railway.json railway.json.dashboard-only
   git commit -m "temp: Rename railway.json to disable for backend service"
   git push origin main
   ```
   (Dùng script push_with_token.ps1 nếu cần)

2. **Railway sẽ không detect config file:**
   - Service "stillme-backend" sẽ không dùng `railway.json` nữa
   - Command sẽ edit được trong UI

3. **Sau khi backend đã ổn định:**
   - Có thể rename lại: `railway.json.dashboard-only` → `railway.json`
   - Dashboard service vẫn dùng được

---

### **3.2C: Connect GitHub Repo (Nếu chưa connect - chỉ dùng nếu service mới tạo từ Empty Service)**

1. **Settings → Source:**
   - Click **"Connect Repo"** hoặc **"Connect GitHub"**
   - Chọn: `StillMe---Self-Evolving-AI-System`
   - **KHÔNG chọn "Apply railway.json"** nếu có option

---

### **3.3 Configure Build**

1. **Settings → Build:**
   - **Builder:** Chọn **`Dockerfile`**
   - **Dockerfile Path:** `Dockerfile` (mặc định)

---

### **3.4 Configure Deploy (Sau khi đã disable config-as-code)**

1. **Settings → Deploy:**
   - Scroll xuống phần **"Custom Start Command"**
   - Paste command:
     ```
     python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Save**

2. **Rename Service:**
   - Settings → Service Name → Đổi thành `stillme-backend`

**Lưu ý:** 
- **PHẢI disable Config-as-code TRƯỚC** (xóa path để trống) → Command sẽ không bị override
- **PORT Variable:** Railway tự động inject `$PORT` environment variable → Không cần set manual
- Sau khi save, Railway sẽ tự động trigger build/deploy

---

### **3.5 Giải thích PORT Variable:**

**PORT là gì?**
- Railway tự động tạo environment variable `PORT` khi deploy service
- Giá trị thường là: `8080`, `8081`, hoặc random port
- Railway tự inject vào container → Service chỉ cần dùng `$PORT` trong command

**Trong command của bạn:**
```bash
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
```

→ `$PORT` sẽ được Railway tự động thay bằng port thật (ví dụ: `8080`)
→ FastAPI sẽ listen trên port đó

**Không cần làm gì thêm!** Railway tự động xử lý.

---

## **Step 4: Set Environment Variables**

**Settings → Variables → Add Variable:**

Thêm các variables sau:

```
PYTHONPATH=/app
ENVIRONMENT=production
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
OPENAI_API_KEY=sk-your-openai-key-here
```

**Lưu ý:** 
- Thay `sk-your-deepseek-key-here` bằng API key thật
- Thay `sk-your-openai-key-here` bằng API key thật (nếu có)

---

## **Step 5: Generate Public Domain**

1. **Settings → Networking**
2. Click **"Generate Domain"**
3. Railway sẽ tạo URL như: `https://stillme-backend-production-xxxx.up.railway.app`
4. **Copy URL này** → Lưu lại để dùng ở Step 5

---

## **Step 6: Update Dashboard Service**

1. **Vào Dashboard Service** (service `dashboard` hiện tại)

2. **Settings → Variables → Add Variable:**
   - **Key:** `STILLME_API_BASE`
   - **Value:** URL backend vừa copy (ví dụ: `https://stillme-backend-production-xxxx.up.railway.app`)

3. **Save**

4. **Redeploy Dashboard:**
   - Tab **"Deployments"**
   - Click **"Redeploy"** (hoặc đợi Railway auto-redeploy)

---

## **Step 7: Verify Setup**

### **6.1 Test Backend API:**

1. Mở URL backend: `https://stillme-backend-production-xxxx.up.railway.app/docs`
2. Sẽ thấy **Swagger UI** (API documentation) ✅
3. Test `/health` endpoint:
   - Vào: `https://stillme-backend-production-xxxx.up.railway.app/health`
   - Sẽ thấy: `{"status": "healthy", ...}` ✅

### **6.2 Test Dashboard Connection:**

1. Vào Dashboard: `https://dashboard-production-595e.up.railway.app`
2. Check sidebar:
   - **"Backend Connected"** → Phải là **green** ✅
3. Test Chat:
   - Nhập message → Click **"Send"**
   - Nếu có response từ AI → ✅ Success!

---

## **🔧 Troubleshooting**

### **Backend không start:**

**Check logs:**
- Service → Tab **"Logs"**
- Tìm lỗi:
  - `ModuleNotFoundError` → Check `requirements.txt`
  - `ImportError` → Check `PYTHONPATH=/app`
  - `Port already in use` → Railway tự xử lý

### **Dashboard không kết nối Backend:**

1. **Verify `STILLME_API_BASE`:**
   - Dashboard Service → Variables
   - Check `STILLME_API_BASE` URL đúng chưa
   - URL phải có `https://` prefix

2. **Test Backend trực tiếp:**
   - Mở backend URL: `/health`
   - Nếu không response → Backend chưa start
   - Nếu response → Backend OK, check dashboard config

3. **Check CORS:**
   - Backend đã có CORS middleware (`allow_origins=["*"]`)
   - Không cần config thêm

### **Environment Variables không work:**

- Verify set trong Railway dashboard (không phải `.env` file)
- Redeploy service sau khi thêm variables

---

## **✅ Done!**

Sau khi hoàn thành tất cả steps:

- ✅ Backend API: `https://stillme-backend-production-xxxx.up.railway.app`
- ✅ Dashboard: `https://dashboard-production-595e.up.railway.app`
- ✅ Dashboard ↔ Backend kết nối thành công
- ✅ Community có thể chat, add knowledge, xem metrics

**🎉 StillMe đã sẵn sàng cho community!**

---

## **📝 Notes**

- **Backend và Dashboard là 2 services riêng** → Dễ scale và maintain
- **Railway tự động handle HTTPS** → Không cần config SSL
- **Free tier Railway:** $5 credit/month → Đủ dùng cho MVP
- **Nếu hết free tier:** Có thể migrate sang Render.com (free 750h/month)

