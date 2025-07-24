# Sử dụng Python 3.13 (có thể thay bằng 3.11 hoặc 3.10 nếu cần)
FROM python:3.13-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy file requirements.txt để cài dependencies trước
COPY requirements.txt .

# Cài đặt các dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ project vào container
COPY . .

# Mặc định chạy agent_dev.py
CMD ["python", "agent_dev.py"]
