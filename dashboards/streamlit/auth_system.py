"""
Authentication System for StillMe Dashboard
==========================================

Hệ thống xác thực và phân quyền cho dashboard.
"""

import hashlib
import secrets
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

class AuthSystem:
    """Hệ thống xác thực và phân quyền"""
    
    def __init__(self):
        self.users_file = "data/auth/users.json"
        self.sessions_file = "data/auth/sessions.json"
        self._ensure_auth_directories()
        self._load_users()
        self._load_sessions()
    
    def _ensure_auth_directories(self):
        """Tạo thư mục auth nếu chưa có"""
        os.makedirs("data/auth", exist_ok=True)
    
    def _load_users(self):
        """Load danh sách users từ file"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            else:
                # Tạo admin user với mật khẩu mới
                self.users = {
                    "admin": {
                        "username": "admin",
                        "password_hash": self._hash_password("Symbianv3@anhnguyen86"),
                        "role": "admin",
                        "permissions": ["read", "write", "approve", "reject", "admin"],
                        "created_at": datetime.now().isoformat(),
                        "last_login": None
                    }
                }
                self._save_users()
        except Exception as e:
            st.error(f"Error loading users: {e}")
            self.users = {}
    
    def _save_users(self):
        """Lưu danh sách users"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            st.error(f"Error saving users: {e}")
    
    def _load_sessions(self):
        """Load sessions từ file"""
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    self.sessions = json.load(f)
            else:
                self.sessions = {}
        except Exception as e:
            st.error(f"Error loading sessions: {e}")
            self.sessions = {}
    
    def _save_sessions(self):
        """Lưu sessions"""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            st.error(f"Error saving sessions: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password với salt"""
        salt = secrets.token_hex(16)
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() + ":" + salt
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password"""
        try:
            hash_part, salt = password_hash.split(":")
            return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() == hash_part
        except:
            return False
    
    def login(self, username: str, password: str) -> bool:
        """Đăng nhập user"""
        if username not in self.users:
            return False
        
        user = self.users[username]
        if not self._verify_password(password, user["password_hash"]):
            return False
        
        # Tạo session
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            "username": username,
            "role": user["role"],
            "permissions": user["permissions"],
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        # Cập nhật last login
        user["last_login"] = datetime.now().isoformat()
        self._save_users()
        self._save_sessions()
        
        # Lưu vào session state
        st.session_state.auth_session_id = session_id
        st.session_state.auth_username = username
        st.session_state.auth_role = user["role"]
        st.session_state.auth_permissions = user["permissions"]
        
        return True
    
    def logout(self):
        """Đăng xuất"""
        if "auth_session_id" in st.session_state:
            session_id = st.session_state.auth_session_id
            if session_id in self.sessions:
                del self.sessions[session_id]
                self._save_sessions()
        
        # Xóa session state
        for key in ["auth_session_id", "auth_username", "auth_role", "auth_permissions"]:
            if key in st.session_state:
                del st.session_state[key]
    
    def is_authenticated(self) -> bool:
        """Kiểm tra user đã đăng nhập chưa"""
        if "auth_session_id" not in st.session_state:
            return False
        
        session_id = st.session_state.auth_session_id
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        expires_at = datetime.fromisoformat(session["expires_at"])
        
        if datetime.now() > expires_at:
            # Session hết hạn
            del self.sessions[session_id]
            self._save_sessions()
            self.logout()
            return False
        
        return True
    
    def has_permission(self, permission: str) -> bool:
        """Kiểm tra user có quyền không"""
        if not self.is_authenticated():
            return False
        
        return permission in st.session_state.get("auth_permissions", [])
    
    def get_user_role(self) -> str:
        """Lấy role của user"""
        if not self.is_authenticated():
            return "guest"
        
        return st.session_state.get("auth_role", "guest")
    
    def get_username(self) -> str:
        """Lấy username"""
        if not self.is_authenticated():
            return "Guest"
        
        return st.session_state.get("auth_username", "Guest")
    
    def render_login_form(self):
        """Render form đăng nhập"""
        st.markdown("### 🔐 Đăng nhập")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Nhập username")
            password = st.text_input("Password", type="password", placeholder="Nhập password")
            submit = st.form_submit_button("Đăng nhập")
            
            if submit:
                if self.login(username, password):
                    st.success("Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("Username hoặc password không đúng!")
        
        # Thông báo cho admin
        st.info("👑 **Admin Login:** Chỉ admin mới cần đăng nhập để approve/reject proposals.")
    
    def render_user_info(self):
        """Render thông tin user"""
        if self.is_authenticated():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                role_icon = "👑" if self.get_user_role() == "admin" else "👤"
                st.write(f"{role_icon} **{self.get_username()}** ({self.get_user_role()})")
            
            with col2:
                if st.button("Đăng xuất", key="logout_btn"):
                    self.logout()
                    st.success("Đã đăng xuất!")
                    st.rerun()
        else:
            st.write("👤 **Guest** (chưa đăng nhập)")
    
    def require_permission(self, permission: str):
        """Decorator để yêu cầu quyền"""
        if not self.has_permission(permission):
            st.error(f"❌ Bạn không có quyền {permission}!")
            st.stop()
    
    def require_admin(self):
        """Yêu cầu quyền admin"""
        if not self.has_permission("admin"):
            st.error("❌ Chỉ admin mới có quyền này!")
            st.stop()
