# Force Redeploy Dashboard Service trên Railway

## 🔍 Vấn đề

- Code fix đã có trên GitHub (commit `d559319d6`)
- Backend service deploy thành công
- **Dashboard service vẫn báo lỗi** `StreamlitAPIException: Expanders may not be nested`
- Dashboard đang chạy code cũ (line 1021 vẫn có `st.expander("📊 Response Metadata")`)

## 🔬 Nguyên nhân

Dashboard service và Backend service deploy **độc lập** trên Railway:
- Backend service đã deploy commit mới → ✅ Thành công
- Dashboard service **chưa deploy** commit mới → ❌ Vẫn chạy code cũ

## ✅ Giải pháp: Force Redeploy Dashboard Service

### Bước 1: Kiểm tra Dashboard Service trên Railway

1. **Railway Dashboard** → **dashboard** service (không phải `stillme-backend`)
2. Click tab **"Deployments"**
3. Kiểm tra commit nào đang được deploy:
   - Nếu thấy commit cũ (trước `d559319d6`) → Cần redeploy
   - Nếu thấy commit `d559319d6` hoặc mới hơn → Có thể là cache issue

### Bước 2: Force Redeploy Dashboard

**Option A: Manual Redeploy (Khuyến nghị)**

1. **Dashboard service** → **Deployments** tab
2. Tìm deployment mới nhất (có commit `d559319d6` hoặc `89380e7f3`)
3. Click **"Redeploy"** button
4. Hoặc click **"Deploy"** để trigger deploy mới từ commit mới nhất

**Option B: Trigger bằng Empty Commit**

Nếu Railway không tự động detect, tạo empty commit để trigger:

```powershell
# Tạo empty commit
git commit --allow-empty -m "chore: trigger dashboard redeploy"

# Push lên GitHub
.\scripts\push_main_with_token.ps1
```

Railway sẽ detect commit mới và auto-deploy cả 2 services.

### Bước 3: Verify Deployment

Sau khi redeploy:
1. **Dashboard service** → **Deployments** tab
2. Kiểm tra deployment mới nhất:
   - Commit phải là `d559319d6` hoặc mới hơn
   - Tất cả steps (Initialization, Build, Deploy, Network, Post-deploy) phải **màu xanh**
3. **Dashboard service** → **Logs** tab
4. Kiểm tra log có: `Starting Streamlit dashboard...` (không phải `Starting FastAPI server...`)

### Bước 4: Test Dashboard

1. Mở dashboard URL
2. Chat với StillMe
3. Nhận câu trả lời
4. **Không còn lỗi** `StreamlitAPIException`
5. Click **"📊 Show Metadata"** để xem metadata

## 🔍 Debug: Kiểm tra Code đang chạy

Nếu vẫn lỗi sau khi redeploy, kiểm tra code đang chạy:

1. **Dashboard service** → **Logs** tab
2. Tìm dòng có `File "/app/dashboard.py", line 1021`
3. Nếu vẫn thấy `st.expander("📊 Response Metadata")` → Code cũ vẫn đang chạy
4. Nếu thấy `st.button("📊 Show Metadata")` → Code mới đã được deploy

## 💡 Lưu ý

- **Dashboard và Backend deploy độc lập** - Cần redeploy riêng
- **Railway có thể cache** - Cần force redeploy để clear cache
- **Commit fix đã có** (`d559319d6`) - Chỉ cần deploy lại
- **Code local đã đúng** - Không cần sửa code nữa

## ✅ Kết quả mong đợi

Sau khi force redeploy dashboard:
- ✅ Dashboard service deploy commit `d559319d6` hoặc mới hơn
- ✅ Tất cả deployment steps màu xanh
- ✅ Dashboard không còn lỗi `StreamlitAPIException`
- ✅ Chat hoạt động bình thường
- ✅ Metadata hiển thị khi click "📊 Show Metadata"

