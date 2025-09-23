# 🔐 GMAIL ADVANCED PROTECTION - HƯỚNG DẪN

## 🚨 **VẤN ĐỀ:**
Bạn đã bật "Khóa truy cập và khóa bảo mật" (Advanced Protection) nên không thể tạo App Passwords.

## 🛠️ **GIẢI PHÁP:**

### **Option 1: Tạm thời tắt Advanced Protection (Khuyến nghị)**

#### **Bước 1: Tắt Advanced Protection**
1. **Truy cập**: [myaccount.google.com/security](https://myaccount.google.com/security)
2. **Tìm "Advanced Protection Program"**
3. **Click "Turn off"** (Tắt)
4. **Confirm** việc tắt

#### **Bước 2: Tạo App Password**
1. **Quay lại Security tab**
2. **Tìm "App passwords"** (sẽ hiện lại)
3. **Click "App passwords"**
4. **Chọn "Mail"** và **"Other"**
5. **Nhập tên**: "StillMe VPS"
6. **Copy password** (16 ký tự)

#### **Bước 3: Bật lại Advanced Protection (Sau khi tạo App Password)**
1. **Quay lại Security tab**
2. **Click "Turn on Advanced Protection"**
3. **Follow hướng dẫn** để bật lại

### **Option 2: Sử dụng OAuth2 (Phức tạp hơn)**

#### **Bước 1: Tạo OAuth2 Credentials**
1. **Truy cập**: [console.developers.google.com](https://console.developers.google.com)
2. **Create Project** → **Enable Gmail API**
3. **Create OAuth2 credentials**
4. **Download JSON file**

#### **Bước 2: Cấu hình OAuth2**
```python
# Thay thế SMTP bằng OAuth2
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds
```

### **Option 3: Sử dụng Email Provider khác (Đơn giản nhất)**

#### **Outlook/Hotmail SMTP:**
```bash
export SMTP_SERVER="smtp-mail.outlook.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@outlook.com"
export SMTP_PASSWORD="your-outlook-password"
export ALERT_EMAIL="your-email@outlook.com"
```

#### **Yahoo SMTP:**
```bash
export SMTP_SERVER="smtp.mail.yahoo.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@yahoo.com"
export SMTP_PASSWORD="your-yahoo-app-password"
export ALERT_EMAIL="your-email@yahoo.com"
```

## 🎯 **KHUYẾN NGHỊ:**

### **Cách nhanh nhất:**
1. **Tạm thời tắt Advanced Protection**
2. **Tạo App Password**
3. **Bật lại Advanced Protection**
4. **Deploy StillMe**

### **Cách an toàn nhất:**
1. **Tạo tài khoản Gmail mới** (chỉ cho StillMe)
2. **Không bật Advanced Protection** trên tài khoản này
3. **Tạo App Password** bình thường
4. **Sử dụng cho StillMe notifications**

## 📧 **ALTERNATIVE EMAIL PROVIDERS:**

### **1. Outlook/Hotmail (Miễn phí)**
- **Link**: [outlook.com](https://outlook.com)
- **SMTP**: smtp-mail.outlook.com:587
- **Không cần App Password**

### **2. Yahoo Mail (Miễn phí)**
- **Link**: [yahoo.com](https://yahoo.com)
- **SMTP**: smtp.mail.yahoo.com:587
- **Cần App Password** (dễ tạo hơn Gmail)

### **3. ProtonMail (Miễn phí)**
- **Link**: [protonmail.com](https://protonmail.com)
- **SMTP**: smtp.protonmail.com:587
- **Bảo mật cao**

## 🚀 **HÀNH ĐỘNG NGAY:**

### **Bước 1: Chọn giải pháp**
- **Nhanh**: Tạm tắt Advanced Protection
- **An toàn**: Tạo Gmail mới
- **Đơn giản**: Dùng Outlook/Yahoo

### **Bước 2: Setup email**
- **Tạo App Password** hoặc **dùng password thường**
- **Test email notification**

### **Bước 3: Deploy StillMe**
- **VPS sẵn sàng**
- **Email configured**
- **Deploy ngay**

## 📋 **CHECKLIST:**

- [ ] **Chọn email provider** (Gmail/Outlook/Yahoo)
- [ ] **Tạo App Password** hoặc **dùng password thường**
- [ ] **Test email notification**
- [ ] **Deploy StillMe lên VPS**
- [ ] **Test end-to-end**

## 💡 **LƯU Ý:**

- **Advanced Protection** là tính năng bảo mật cao cấp
- **Tạm tắt** để tạo App Password là **an toàn**
- **Bật lại** sau khi tạo App Password
- **Hoặc dùng email provider khác** đơn giản hơn
