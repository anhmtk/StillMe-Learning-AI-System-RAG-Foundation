#!/usr/bin/env python3
"""
Change Password Script for StillMe Dashboard
===========================================

Script để đổi mật khẩu an toàn cho dashboard.
"""

import hashlib
import secrets
import json
import os
import sys
from pathlib import Path

def hash_password(password: str) -> str:
    """Hash password với salt"""
    salt = secrets.token_hex(16)
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() + ":" + salt

def change_password():
    """Đổi mật khẩu cho user"""
    users_file = "data/auth/users.json"
    
    # Tạo thư mục nếu chưa có
    os.makedirs("data/auth", exist_ok=True)
    
    # Load users
    try:
        if os.path.exists(users_file):
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
        else:
            print("❌ File users.json không tồn tại!")
            return False
    except Exception as e:
        print(f"❌ Lỗi đọc file users: {e}")
        return False
    
    print("🔐 StillMe Dashboard - Đổi Mật Khẩu")
    print("=" * 40)
    
    # Hiển thị danh sách users
    print("\n📋 Danh sách users hiện tại:")
    for username in users.keys():
        role = users[username].get("role", "unknown")
        print(f"  - {username} ({role})")
    
    # Nhập thông tin
    username = input("\n👤 Nhập username cần đổi mật khẩu: ").strip()
    
    if username not in users:
        print(f"❌ User '{username}' không tồn tại!")
        return False
    
    # Xác nhận
    current_role = users[username].get("role", "unknown")
    print(f"\n✅ Tìm thấy user: {username} (role: {current_role})")
    
    confirm = input("Bạn có chắc chắn muốn đổi mật khẩu? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Hủy bỏ thao tác.")
        return False
    
    # Nhập mật khẩu mới
    while True:
        new_password = input("\n🔑 Nhập mật khẩu mới: ").strip()
        if len(new_password) < 6:
            print("❌ Mật khẩu phải có ít nhất 6 ký tự!")
            continue
        
        confirm_password = input("🔑 Xác nhận mật khẩu mới: ").strip()
        if new_password != confirm_password:
            print("❌ Mật khẩu xác nhận không khớp!")
            continue
        
        break
    
    # Cập nhật mật khẩu
    users[username]["password_hash"] = hash_password(new_password)
    
    # Lưu file
    try:
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Đã đổi mật khẩu thành công cho user '{username}'!")
        print("🔄 Vui lòng khởi động lại dashboard để áp dụng thay đổi.")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi lưu file: {e}")
        return False

def create_new_user():
    """Tạo user mới"""
    users_file = "data/auth/users.json"
    
    # Tạo thư mục nếu chưa có
    os.makedirs("data/auth", exist_ok=True)
    
    # Load users
    try:
        if os.path.exists(users_file):
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
        else:
            users = {}
    except Exception as e:
        print(f"❌ Lỗi đọc file users: {e}")
        return False
    
    print("👤 StillMe Dashboard - Tạo User Mới")
    print("=" * 40)
    
    # Nhập thông tin
    username = input("\n👤 Nhập username mới: ").strip()
    
    if username in users:
        print(f"❌ User '{username}' đã tồn tại!")
        return False
    
    # Chọn role
    print("\n🎭 Chọn role:")
    print("  1. admin (toàn quyền)")
    print("  2. user (quyền hạn chế)")
    
    role_choice = input("Nhập lựa chọn (1/2): ").strip()
    if role_choice == "1":
        role = "admin"
        permissions = ["read", "write", "approve", "reject", "admin", "chat"]
    elif role_choice == "2":
        role = "user"
        permissions = ["read", "chat"]
    else:
        print("❌ Lựa chọn không hợp lệ!")
        return False
    
    # Nhập mật khẩu
    while True:
        password = input("\n🔑 Nhập mật khẩu: ").strip()
        if len(password) < 6:
            print("❌ Mật khẩu phải có ít nhất 6 ký tự!")
            continue
        
        confirm_password = input("🔑 Xác nhận mật khẩu: ").strip()
        if password != confirm_password:
            print("❌ Mật khẩu xác nhận không khớp!")
            continue
        
        break
    
    # Tạo user
    users[username] = {
        "username": username,
        "password_hash": hash_password(password),
        "role": role,
        "permissions": permissions,
        "created_at": "2025-01-16T00:00:00",
        "last_login": None
    }
    
    # Lưu file
    try:
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Đã tạo user '{username}' thành công!")
        print(f"🎭 Role: {role}")
        print(f"🔑 Permissions: {', '.join(permissions)}")
        print("🔄 Vui lòng khởi động lại dashboard để áp dụng thay đổi.")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi lưu file: {e}")
        return False

def main():
    """Main function"""
    print("🔐 StillMe Dashboard - User Management")
    print("=" * 50)
    
    while True:
        print("\n📋 Chọn hành động:")
        print("  1. Đổi mật khẩu user hiện có")
        print("  2. Tạo user mới")
        print("  3. Thoát")
        
        choice = input("\nNhập lựa chọn (1/2/3): ").strip()
        
        if choice == "1":
            change_password()
        elif choice == "2":
            create_new_user()
        elif choice == "3":
            print("👋 Tạm biệt!")
            break
        else:
            print("❌ Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    main()
