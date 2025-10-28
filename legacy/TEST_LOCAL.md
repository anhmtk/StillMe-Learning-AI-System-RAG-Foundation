# StillMe AI - Local Testing Guide

Hướng dẫn test StillMe AI trên mạng LAN cho desktop và mobile app.

## 🎯 Mục tiêu

Test desktop app và mobile app kết nối với backend local qua LAN IP, không cần VPS hay tunnel.

## 📋 Chuẩn bị

### 1. Cài đặt Ollama Models
```bash
ollama pull gemma2:2b
ollama pull deepseek-coder:6.7b
```

### 2. Lấy LAN IP của PC

**Windows:**
```cmd
ipconfig
```
Tìm `IPv4 Address` trong `Wireless LAN adapter Wi-Fi`
Ví dụ: `192.168.1.12`

**Linux/Mac:**
```bash
ifconfig
```
Tìm `inet` trong `wlan0` hoặc `en0`
Ví dụ: `192.168.1.12`

## 🚀 Test Backend

### 1. Chạy Backend
```bash
python app.py
```

### 2. Test Health Check
```bash
# Local test
curl http://127.0.0.1:1216/health

# LAN test (thay 192.168.1.12 bằng IP thực tế)
curl http://192.168.1.12:1216/health
```

### 3. Test Chat API
```bash
curl -X POST http://192.168.1.12:1216/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "xin chào", "session_id": "test"}'
```

## 🖥️ Test Desktop App

### 1. Chạy Desktop App
```bash
python desktop_chat_app.py
```

### 2. Test với Local Backend
- App mặc định dùng `http://127.0.0.1:1216`
- Gửi message "xin chào" để test

### 3. Test với LAN IP
- Click **Settings** button
- Đổi API URL thành `http://192.168.1.12:1216`
- Gửi message để test

## 📱 Test Mobile App

### 1. Cấu hình Mobile App
- **Đảm bảo cùng WiFi** với PC chạy backend
- **Đổi BASE_URL** trong app settings thành: `http://192.168.1.12:1216`
- **Lưu settings**

### 2. Test Kết nối
- Gửi message "xin chào"
- Kiểm tra response từ Gemma2:2b
- Gửi message "how to write python function"
- Kiểm tra response từ DeepSeek-Coder:6.7b

## 🔧 Troubleshooting

### Backend không start được
```bash
# Kiểm tra port 1216 có bị chiếm không
netstat -an | findstr 1216

# Kill process nếu cần
taskkill /f /im python.exe
```

### Desktop app không kết nối được
- Kiểm tra backend đang chạy: `curl http://127.0.0.1:1216/health`
- Kiểm tra API URL trong settings
- Kiểm tra firewall Windows

### Mobile app không kết nối được
- **Kiểm tra cùng WiFi**: PC và mobile phải cùng network
- **Kiểm tra LAN IP**: Dùng `ipconfig` để lấy IP chính xác
- **Kiểm tra firewall**: Tắt Windows Firewall tạm thời để test
- **Test từ browser**: Mở `http://192.168.1.12:1216` trên mobile browser

### Ollama không phản hồi
```bash
# Kiểm tra Ollama đang chạy
ollama list

# Restart Ollama nếu cần
ollama serve
```

## 📊 Test Cases

### 1. Simple Questions
- **Input**: "xin chào"
- **Expected**: Response từ Gemma2:2b
- **Latency**: < 5 giây

### 2. Code Questions
- **Input**: "how to write python function"
- **Expected**: Response từ DeepSeek-Coder:6.7b
- **Latency**: < 60 giây

### 3. Error Handling
- **Input**: Empty message
- **Expected**: Error message
- **Status**: 400 Bad Request

### 4. Network Issues
- **Scenario**: Backend offline
- **Expected**: Connection error message
- **Recovery**: Restart backend

## ✅ Success Criteria

- [ ] Backend chạy trên `http://0.0.0.0:1216`
- [ ] Desktop app kết nối được qua local IP
- [ ] Desktop app kết nối được qua LAN IP
- [ ] Mobile app kết nối được qua LAN IP
- [ ] Simple questions → Gemma2:2b
- [ ] Code questions → DeepSeek-Coder:6.7b
- [ ] Error handling hoạt động
- [ ] Settings có thể đổi API URL

## 🎉 Kết quả mong đợi

Sau khi test thành công:
- **Desktop app** chat được với StillMe AI
- **Mobile app** chat được với StillMe AI
- **Smart routing** hoạt động đúng
- **Không cần VPS** hay tunnel
- **Chỉ cần LAN IP** để test

---

**Lưu ý**: Đây là hướng dẫn test local development. Không dùng cho production deployment.
