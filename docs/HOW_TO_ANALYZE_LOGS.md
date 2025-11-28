# 🔍 Hướng Dẫn Phân Tích Backend Logs

## 📋 Tổng Quan

Khi logs quá dài, bạn cần **filter và tìm patterns** thay vì đọc toàn bộ.

---

## 🚀 Cách 1: Dùng Script Tự Động (Khuyến Nghị)

### **PowerShell (Windows)**:
```powershell
# Quick check - tìm patterns quan trọng
.\scripts\quick_log_check.ps1

# Hoặc chỉ định file log cụ thể
.\scripts\quick_log_check.ps1 logs\server.log
```

### **Python**:
```bash
# Phân tích chi tiết
python scripts/analyze_evaluation_logs.py logs/server.log

# Hoặc để script tự tìm
python scripts/analyze_evaluation_logs.py
```

**Scripts sẽ tự động**:
- ✅ Đọc last 5,000-10,000 lines (nếu file quá lớn)
- ✅ Tìm patterns quan trọng (fallback, LLM errors, validation failures)
- ✅ Hiển thị summary và suggestions

---

## 🔍 Cách 2: Filter Logs Thủ Công

### **PowerShell - Tìm Fallback Messages**:
```powershell
# Tìm tất cả fallback messages
Get-Content logs\server.log | Select-String -Pattern "fallback|StillMe is experiencing" | Select-Object -Last 20

# Tìm LLM errors
Get-Content logs\server.log | Select-String -Pattern "LLM.*error|LLM.*failed|API.*error" | Select-Object -Last 20

# Tìm validation failures
Get-Content logs\server.log | Select-String -Pattern "validation.*failed|missing_citation" | Select-Object -Last 20
```

### **PowerShell - Tìm Evaluation Requests**:
```powershell
# Tìm requests từ evaluation
Get-Content logs\server.log | Select-String -Pattern "evaluation_bot|truthfulqa" | Select-Object -Last 30

# Tìm errors trong evaluation requests
Get-Content logs\server.log | Select-String -Pattern "evaluation_bot" -Context 5,5 | Select-Object -Last 50
```

### **PowerShell - Tìm Recent Errors**:
```powershell
# Last 100 lines có chứa "ERROR" hoặc "WARNING"
Get-Content logs\server.log | Select-String -Pattern "ERROR|WARNING" | Select-Object -Last 100

# Errors trong 10 phút gần nhất (nếu có timestamp)
Get-Content logs\server.log | Select-String -Pattern "$(Get-Date -Format 'yyyy-MM-dd HH:mm')" -Context 0,10
```

---

## 📊 Cách 3: Xem Logs Real-Time (Khi Backend Đang Chạy)

### **PowerShell - Tail Logs**:
```powershell
# Xem logs real-time (last 50 lines)
Get-Content logs\server.log -Wait -Tail 50

# Filter real-time
Get-Content logs\server.log -Wait -Tail 50 | Where-Object { $_ -match "error|fallback|validation" }
```

### **Python - Monitor Logs**:
```python
# Tạo file: scripts/monitor_logs.py
import time
import subprocess

# Monitor logs và filter errors
proc = subprocess.Popen(
    ['powershell', '-Command', 'Get-Content logs\\server.log -Wait -Tail 20'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

for line in proc.stdout:
    if any(keyword in line.lower() for keyword in ['error', 'fallback', 'validation', 'llm']):
        print(line.strip())
```

---

## 🎯 Patterns Quan Trọng Cần Tìm

### **1. Fallback Messages** (Quan trọng nhất):
```
"StillMe is experiencing a technical issue"
"using fallback"
"get_fallback_message_for_error"
```

### **2. LLM Failures**:
```
"LLM.*failed"
"LLM.*error"
"LLM.*returned.*empty"
"API.*error"
"timeout"
"rate.*limit"
```

### **3. Validation Failures**:
```
"validation.*failed"
"missing_citation"
"language_mismatch"
"Validation.*pass.*False"
```

### **4. Empty Responses**:
```
"empty response"
"response.*is.*None"
"LLM.*returned.*None"
```

---

## 🔧 Cách 4: Tạo Log File Nhỏ Hơn (Chỉ Errors)

### **PowerShell - Extract Only Errors**:
```powershell
# Tạo file chỉ chứa errors và warnings
Get-Content logs\server.log | 
    Select-String -Pattern "ERROR|WARNING|fallback|LLM.*error" | 
    Out-File logs\errors_only.log

# Xem file errors
Get-Content logs\errors_only.log | Select-Object -Last 50
```

---

## 📝 Ví Dụ Phân Tích

### **Scenario 1: Tìm tại sao Citation Rate = 50%**

```powershell
# Bước 1: Tìm evaluation requests
Get-Content logs\server.log | Select-String -Pattern "evaluation_bot" -Context 10,10 | Out-File temp_eval.log

# Bước 2: Trong temp_eval.log, tìm:
# - "missing_citation" → Validation đang reject
# - "LLM.*failed" → LLM đang fail
# - "fallback" → Fallback được trigger

# Bước 3: Xem pattern
Get-Content temp_eval.log | Select-String -Pattern "missing_citation|LLM.*failed|fallback" | Group-Object | Sort-Object Count -Descending
```

### **Scenario 2: Tìm LLM API Issues**

```powershell
# Tìm tất cả LLM errors
Get-Content logs\server.log | 
    Select-String -Pattern "LLM|API.*error|timeout|rate.*limit" | 
    Select-Object -Last 50 |
    Format-Table -AutoSize
```

---

## 💡 Tips

1. **Luôn dùng `-Last N`**: Không đọc toàn bộ file, chỉ đọc last N lines
2. **Filter trước khi đọc**: Dùng `Select-String` để filter patterns
3. **Context**: Dùng `-Context 5,5` để xem context xung quanh error
4. **Group results**: Dùng `Group-Object` để đếm frequency
5. **Export**: Export filtered results ra file nhỏ hơn để phân tích

---

## 🚨 Quick Commands Cheat Sheet

```powershell
# 1. Last 50 errors
Get-Content logs\server.log | Select-String "ERROR" | Select-Object -Last 50

# 2. Evaluation requests với context
Get-Content logs\server.log | Select-String "evaluation_bot" -Context 5,5 | Select-Object -Last 30

# 3. Fallback messages
Get-Content logs\server.log | Select-String "fallback|StillMe is experiencing" | Select-Object -Last 20

# 4. LLM failures
Get-Content logs\server.log | Select-String "LLM.*failed|LLM.*error" | Select-Object -Last 20

# 5. Validation failures  
Get-Content logs\server.log | Select-String "validation.*failed|missing_citation" | Select-Object -Last 20

# 6. Count errors by type
Get-Content logs\server.log | Select-String "ERROR|WARNING" | Group-Object | Sort-Object Count -Descending
```

---

## 📂 Log File Locations

Backend logs thường ở:
- `logs/server.log` - Main server log
- `logs/server_error.log` - Error log
- Console output (nếu chạy trực tiếp)

Nếu không tìm thấy, check:
- Backend process output (console)
- Docker logs (nếu dùng Docker)
- Railway logs (nếu deploy trên Railway)

---

**Lưu ý**: Nếu logs quá dài (>100MB), luôn dùng `-Tail` hoặc filter trước khi đọc!




