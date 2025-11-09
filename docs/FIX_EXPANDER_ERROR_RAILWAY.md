# Fix: StreamlitAPIException - Expanders may not be nested

## 🔍 Vấn đề

- Dashboard báo lỗi: `StreamlitAPIException: Expanders may not be nested inside other expanders`
- Lỗi xảy ra ở line 1021 trong `dashboard.py`
- Lỗi chỉ xuất hiện **sau khi nhận được câu trả lời từ StillMe**
- Khi clear chat, lỗi biến mất nhưng tin nhắn cũng mất

## 🔬 Nguyên nhân

Code cũ có `st.expander("📊 Response Metadata")` **bên trong** `st.sidebar.expander("📜 Chat History")`, vi phạm quy tắc của Streamlit.

**Code cũ (gây lỗi):**
```python
with st.sidebar.expander("📜 Chat History", expanded=True):
    for idx, m in enumerate(st.session_state.chat_history[-20:]):
        if m["role"] == "assistant":
            with st.expander("📊 Response Metadata", expanded=False):  # ❌ LỖI: Nested expander
                # ... metadata ...
```

**Code mới (đã fix):**
```python
with st.sidebar.expander("📜 Chat History", expanded=True):
    for idx, m in enumerate(st.session_state.chat_history[-20:]):
        if m["role"] == "assistant":
            # ✅ Dùng button + container thay vì expander
            if st.button("📊 Show Metadata", key=f"toggle_{idx}"):
                st.session_state[metadata_key] = not show_metadata
                st.rerun()
            
            if st.session_state.get(metadata_key, False):
                with st.container():  # ✅ Không phải expander
                    # ... metadata ...
```

## ✅ Giải pháp

### Bước 1: Verify Code đã được fix

Commit fix: `d559319d6` - "fix: Replace nested expander with toggle button for metadata display"

Code này đã có trên GitHub, nhưng Railway có thể chưa deploy.

### Bước 2: Trigger Deploy mới trên Railway

**Option A: Manual Redeploy (Khuyến nghị)**

1. **Railway Dashboard** → **dashboard** service
2. Click tab **"Deployments"**
3. Tìm deployment mới nhất (có commit `d559319d6`)
4. Click **"Redeploy"** hoặc **"Deploy"**
5. Đợi deploy hoàn tất (2-3 phút)

**Option B: Push commit mới để trigger auto-deploy**

```powershell
# Push commit docs mới nhất
.\scripts\push_main_with_token.ps1
```

Railway sẽ tự động detect commit mới và deploy.

### Bước 3: Verify Fix

Sau khi deploy xong:
1. Mở dashboard
2. Chat với StillMe
3. Nhận câu trả lời
4. **Không còn lỗi** `StreamlitAPIException`
5. Click **"📊 Show Metadata"** để xem metadata (latency, confidence, etc.)

## 🔍 Tại sao lỗi chỉ xảy ra sau khi nhận câu trả lời?

- Code chỉ render metadata khi `m["role"] == "assistant"` và có metadata
- Khi nhận câu trả lời mới, Streamlit render lại sidebar
- Code cũ cố gắng tạo expander lồng nhau → Lỗi
- Khi clear chat, `chat_history` rỗng → Không render metadata → Không lỗi

## 💡 Lưu ý

- **Commit fix đã có trên GitHub** (`d559319d6`)
- **Railway cần deploy lại** để áp dụng fix
- **Code hiện tại đã đúng** - không còn expander lồng nhau
- **Latency metrics** sẽ hiển thị sau khi fix (trong metadata section)

## ✅ Kết quả mong đợi

Sau khi deploy:
- ✅ Không còn lỗi `StreamlitAPIException`
- ✅ Chat hoạt động bình thường
- ✅ Metadata (latency, confidence) hiển thị khi click "📊 Show Metadata"
- ✅ Không cần clear chat để tiếp tục chat

