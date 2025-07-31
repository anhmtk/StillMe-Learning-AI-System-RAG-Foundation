# Sử dụng base image Python 3.9 slim (nhẹ hơn nhiều so với bản full)
FROM python:3.9-slim

# Thiết lập biến môi trường cho Unicode
ENV PYTHONIOENCODING=utf-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Cài Docker CLI bên trong container
RUN apt-get update && apt-get install -y docker.io

# Cài các gói hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Cài PyTorch CPU + các thư viện cơ bản trước (tránh bị gián đoạn)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
       torch==2.3.0+cpu \
       torchvision==0.18.0+cpu \
       --index-url https://download.pytorch.org/whl/cpu

# Copy file requirements.txt vào container
WORKDIR /app
COPY requirements.txt .

# Cài đặt dependencies trong requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ project vào container
COPY . .

# Lệnh mặc định khi chạy container
CMD ["python3", "framework.py"]
