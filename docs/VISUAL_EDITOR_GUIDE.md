# Cursor Visual Editor Guide cho StillMe

## Tổng Quan

Sau khi extract CSS/JS ra file riêng, bạn có thể sử dụng **Cursor Visual Editor** để design và chỉnh sửa giao diện chat widget một cách trực quan, không cần viết code thủ công.

## Cursor Visual Editor Là Gì?

**Visual Editor** là tính năng mới của Cursor cho phép bạn:
- **Drag & Drop**: Kéo thả elements để sắp xếp layout
- **Visual Styling**: Chỉnh màu sắc, font, spacing bằng UI controls
- **Real-time Preview**: Xem thay đổi ngay lập tức
- **Auto Code Generation**: Click "Apply" để tự động generate code

## Cách Sử Dụng Visual Editor với StillMe

### 1. Mở Visual Editor

1. Mở file `frontend/static/chat_widget.css` hoặc `frontend/static/chat_widget.js` trong Cursor
2. Click vào icon **Visual Editor** (hoặc dùng shortcut)
3. Cursor sẽ hiển thị preview của chat widget

### 2. Design Trực Quan

#### **Thay Đổi Màu Sắc:**
- Click vào element (ví dụ: chat button, message bubble)
- Chọn màu từ color picker
- Xem preview ngay lập tức

#### **Điều Chỉnh Layout:**
- Drag & drop để di chuyển elements
- Resize bằng cách kéo edges/corners
- Thay đổi spacing, padding, margin

#### **Typography:**
- Chọn font family, size, weight
- Điều chỉnh line height, letter spacing
- Preview real-time

### 3. Apply Changes

Sau khi design xong:
1. Click nút **"Apply"** trong Visual Editor
2. Cursor sẽ tự động:
   - Generate CSS/JS code tương ứng
   - Update `chat_widget.css` hoặc `chat_widget.js`
   - Giữ nguyên placeholders (`{OVERLAY_DISPLAY}`, `API_BASE`, etc.)

### 4. Test Changes

1. Restart Streamlit dashboard: `streamlit run dashboard.py`
2. Mở chat widget và kiểm tra thay đổi
3. Nếu cần điều chỉnh, quay lại Visual Editor

## Ví Dụ Cụ Thể

### **Ví Dụ 1: Thay Đổi Màu Chat Button**

**Trước (Manual CSS):**
```css
#stillme-chat-button {
    background: linear-gradient(135deg, #46b3ff 0%, #1e90ff 100%);
}
```

**Với Visual Editor:**
1. Click vào chat button trong preview
2. Chọn màu mới từ color picker (ví dụ: `#ff6b6b`)
3. Click "Apply"
4. CSS tự động được update

**Sau:**
```css
#stillme-chat-button {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
}
```

### **Ví Dụ 2: Điều Chỉnh Message Bubble Spacing**

**Trước (Manual CSS):**
```css
.stillme-chat-message {
    padding: 10px 14px;
    margin: 8px 0;
}
```

**Với Visual Editor:**
1. Click vào message bubble
2. Drag để điều chỉnh padding/spacing
3. Xem preview real-time
4. Click "Apply"

**Sau:**
```css
.stillme-chat-message {
    padding: 12px 16px;
    margin: 10px 0;
}
```

### **Ví Dụ 3: Thay Đổi Font Family**

**Trước (Manual CSS):**
```css
#stillme-chat-widget {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
```

**Với Visual Editor:**
1. Select widget container
2. Chọn font từ dropdown (ví dụ: "Inter", "Poppins")
3. Click "Apply"

**Sau:**
```css
#stillme-chat-widget {
    font-family: 'Inter', -apple-system, sans-serif;
}
```

## Lợi Ích So Với Manual Coding

### **Trước (Manual):**
- ❌ Phải viết CSS thủ công
- ❌ Không có preview real-time
- ❌ Phải test nhiều lần để đạt kết quả mong muốn
- ❌ Khó visualize layout changes

### **Sau (Visual Editor):**
- ✅ Design trực quan, drag & drop
- ✅ Preview real-time, thấy ngay kết quả
- ✅ Auto-generate code, ít lỗi hơn
- ✅ Dễ dàng thử nghiệm nhiều variations

## Lưu Ý Quan Trọng

### **1. Giữ Nguyên Placeholders:**
Khi edit CSS/JS, **KHÔNG được xóa** các placeholders:
- `{OVERLAY_DISPLAY}` - Sẽ được replace bằng 'block' hoặc 'none'
- `{PANEL_DISPLAY}` - Sẽ được replace bằng 'flex' hoặc 'none'
- `API_BASE` - Sẽ được replace bằng actual API URL
- `CHAT_HISTORY_JSON` - Sẽ được replace bằng chat history JSON
- `IS_OPEN` - Sẽ được replace bằng 'true' hoặc 'false'

### **2. Test Sau Khi Apply:**
Luôn test chat widget sau khi apply changes để đảm bảo:
- Dynamic values được inject đúng
- Responsive design vẫn hoạt động
- Không có lỗi JavaScript

### **3. Backup Trước Khi Edit:**
Nếu edit nhiều, nên commit hoặc backup trước:
```bash
git add frontend/static/chat_widget.css
git commit -m "Backup before Visual Editor changes"
```

## Workflow Khuyến Nghị

1. **Design Phase:**
   - Mở Visual Editor
   - Design trực quan
   - Preview và iterate

2. **Apply Phase:**
   - Click "Apply" để generate code
   - Review generated code
   - Commit changes

3. **Test Phase:**
   - Restart dashboard
   - Test chat widget
   - Fix nếu cần

4. **Deploy Phase:**
   - Commit final changes
   - Deploy to Railway
   - Monitor for issues

## Kết Luận

Visual Editor giúp bạn:
- **Design nhanh hơn**: Không cần viết CSS thủ công
- **Visualize tốt hơn**: Thấy ngay kết quả
- **Iterate dễ hơn**: Thử nhiều variations nhanh chóng
- **Collaborate tốt hơn**: Designer có thể edit mà không cần biết Python

**Dashboard không thay đổi gì** - đây chỉ là internal refactoring để hỗ trợ Visual Editor tốt hơn. Chat widget vẫn hoạt động như cũ, chỉ cách edit CSS/JS thay đổi.

