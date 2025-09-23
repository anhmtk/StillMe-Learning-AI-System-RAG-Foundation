# 📧 EMAIL NOTIFICATION SETUP GUIDE

## 🎯 **GMAIL SMTP SETUP**

### **Bước 1: Tạo App Password**
1. **Vào Gmail** → **Settings** → **Security**
2. **Enable 2-Factor Authentication** (nếu chưa có)
3. **App Passwords** → **Generate new password**
4. **Chọn "Mail"** và **"Other"**
5. **Nhập tên**: "StillMe VPS Notifications"
6. **Copy password** (16 ký tự)

### **Bước 2: Environment Variables**
```bash
# Trên VPS, set các biến môi trường:
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-16-char-app-password"
export ALERT_EMAIL="your-email@gmail.com"
```

### **Bước 3: Test Email**
```bash
# Test email notification
python simple_notification.py
```

## 🔧 **ALTERNATIVE EMAIL PROVIDERS**

### **Outlook/Hotmail SMTP**
```bash
export SMTP_SERVER="smtp-mail.outlook.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@outlook.com"
export SMTP_PASSWORD="your-password"
```

### **Yahoo SMTP**
```bash
export SMTP_SERVER="smtp.mail.yahoo.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@yahoo.com"
export SMTP_PASSWORD="your-app-password"
```

## 📱 **SMS NOTIFICATIONS (Optional)**

### **Twilio SMS**
```bash
export TWILIO_ACCOUNT_SID="your-account-sid"
export TWILIO_AUTH_TOKEN="your-auth-token"
export TWILIO_PHONE_NUMBER="+1234567890"
export ALERT_PHONE="+84901234567"
```

### **Free SMS Alternatives**
- **Telegram Bot**: Miễn phí, dễ setup
- **Discord Webhook**: Miễn phí
- **Slack Webhook**: Miễn phí

## 🧪 **TEST NOTIFICATIONS**

### **Test Email**
```python
from simple_notification import send_alert

# Test email
send_alert("Test Alert", "This is a test from StillMe VPS", "medium")
```

### **Test Health Alert**
```python
from simple_notification import send_health_alert

# Test health alert
send_health_alert("Gateway", "down", "Service is not responding")
```

## 📋 **CHECKLIST**

- [ ] Gmail App Password created
- [ ] Environment variables set
- [ ] Email test successful
- [ ] Health check script configured
- [ ] Cron job setup for monitoring
