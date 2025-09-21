# StillMe AI - Local Development

StillMe AI là một hệ thống chat AI thông minh với khả năng routing tự động giữa các model AI khác nhau.

## 🚀 Quick Start

### 1. Chạy Backend

```bash
# Cài đặt dependencies
pip install requests

# Chạy backend
python app.py
```

Backend sẽ chạy trên `http://0.0.0.0:1216` và có thể truy cập từ:
- **Local**: `http://127.0.0.1:1216`
- **LAN**: `http://192.168.x.x:1216` (cho desktop/mobile app)

### 2. Chạy Desktop App

```bash
python desktop_chat_app.py
```

## 📱 Mobile App Testing

### Cách lấy LAN IP:

**Windows:**
```cmd
ipconfig
```

**Linux/Mac:**
```bash
ifconfig
```

### Cấu hình Mobile App:

1. **Đảm bảo cùng WiFi** với PC chạy backend
2. **Đổi BASE_URL** trong app settings thành: `http://192.168.x.x:1216`
3. **Test kết nối** bằng cách gửi message

## 🧠 Smart Routing

Backend tự động chọn model AI phù hợp:

- **Simple questions** (xin chào, cảm ơn) → **Gemma2:2b** (nhanh)
- **Code questions** (python, function) → **DeepSeek-Coder:6.7b** (chuyên code)
- **Default** → **Gemma2:2b`

## 🔧 API Endpoints

### Health Check
```bash
curl http://192.168.x.x:1216/health
```

### Chat
```bash
curl -X POST http://192.168.x.x:1216/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "xin chào", "session_id": "test"}'
```

## 📋 Requirements

- **Python 3.8+**
- **Ollama** với models:
  - `gemma2:2b`
  - `deepseek-coder:6.7b`

### Cài đặt Ollama Models:
```bash
ollama pull gemma2:2b
ollama pull deepseek-coder:6.7b
```

## 🛠️ Development

### File Structure:
```
stillme_ai/
├── app.py                 # Main backend
├── desktop_chat_app.py    # Desktop chat app
├── README.md             # This file
└── TEST_LOCAL.md         # Testing guide
```

### Testing:
- **Backend**: `python app.py`
- **Desktop**: `python desktop_chat_app.py`
- **Mobile**: Đổi BASE_URL trong app settings

## 🔒 Security Notes

- **Không có API keys** trong mobile app
- **Không log nhạy cảm** trong production
- **Chỉ dùng LAN IP** cho testing
- **Không cần VPS** cho development

## 📞 Support

Nếu gặp vấn đề:
1. Kiểm tra Ollama đang chạy: `ollama list`
2. Kiểm tra backend: `curl http://127.0.0.1:1216/health`
3. Kiểm tra LAN IP: `ipconfig` (Windows) hoặc `ifconfig` (Linux/Mac)
4. Đảm bảo cùng WiFi network

---

**StillMe AI** - Được tạo bởi Anh Nguyễn với sự hỗ trợ từ các tổ chức AI hàng đầu như OpenAI, Google, DeepSeek. Mục đích đồng hành và kết bạn với mọi người.
