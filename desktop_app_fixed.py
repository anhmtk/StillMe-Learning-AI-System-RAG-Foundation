#!/usr/bin/env python3
"""
StillMe Desktop App - Beautiful Modern UI
Desktop app với giao diện đẹp như FlutterFlow
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import json
import threading
from datetime import datetime
import webbrowser
from tkinter import font

class StillMeDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("StillMe AI - Desktop App")
        self.root.geometry("1000x800")
        self.root.configure(bg="#f8fafc")
        self.root.resizable(True, True)
        
        # Set modern font
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family="Segoe UI", size=10)
        
        # Gateway URL
        self.gateway_url = "http://160.191.89.99:21568"
        
        # Tạo giao diện
        self.create_ui()
        
        # Test kết nối
        self.test_connection()
    
    def create_ui(self):
        # Main container
        main_container = tk.Frame(self.root, bg="#f8fafc")
        main_container.pack(fill="both", expand=True)
        
        # Header
        header_frame = tk.Frame(main_container, bg="#3b82f6", height=80)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Logo và title
        title_label = tk.Label(
            header_frame, 
            text="🤖 StillMe AI", 
            font=("Segoe UI", 24, "bold"),
            fg="white",
            bg="#3b82f6"
        )
        title_label.pack(pady=20)
        
        # Content area
        content_frame = tk.Frame(main_container, bg="#f8fafc")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Status bar
        status_frame = tk.Frame(content_frame, bg="#f8fafc")
        status_frame.pack(fill="x", pady=(0, 15))
        
        # Status label
        self.status_label = tk.Label(
            status_frame,
            text="🔍 Đang kiểm tra kết nối...",
            font=("Segoe UI", 12),
            fg="#6b7280",
            bg="#f8fafc"
        )
        self.status_label.pack(side="left")
        
        # Gateway URL label
        url_label = tk.Label(
            status_frame,
            text=f"Gateway: {self.gateway_url}",
            font=("Segoe UI", 10),
            fg="#9ca3af",
            bg="#f8fafc"
        )
        url_label.pack(side="right")
        
        # Chat container
        chat_container = tk.Frame(content_frame, bg="#f8fafc")
        chat_container.pack(fill="both", expand=True)
        
        # Chat history frame
        chat_frame = tk.Frame(chat_container, bg="white", relief="flat", borderwidth=1)
        chat_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Chat history
        self.chat_text = scrolledtext.ScrolledText(
            chat_frame,
            height=25,
            font=("Segoe UI", 11),
            bg="white",
            fg="#374151",
            relief="flat",
            borderwidth=0,
            wrap="word",
            padx=15,
            pady=15
        )
        self.chat_text.pack(fill="both", expand=True)
        
        # Input container
        input_container = tk.Frame(chat_container, bg="#f8fafc")
        input_container.pack(fill="x")
        
        # Input frame with border
        input_frame = tk.Frame(input_container, bg="white", relief="flat", borderwidth=1)
        input_frame.pack(fill="x", pady=(0, 10))
        
        # Message input
        self.message_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 12),
            relief="flat",
            borderwidth=0,
            bg="white",
            fg="#374151",
            insertbackground="#374151"
        )
        self.message_entry.pack(side="left", fill="x", expand=True, padx=15, pady=15)
        self.message_entry.bind("<Return>", self.send_message)
        self.message_entry.bind("<KeyPress>", self.on_key_press)
        
        # Send button
        send_button = tk.Button(
            input_frame,
            text="Gửi",
            font=("Segoe UI", 12, "bold"),
            bg="#3b82f6",
            fg="white",
            relief="flat",
            borderwidth=0,
            padx=25,
            pady=15,
            command=self.send_message,
            cursor="hand2"
        )
        send_button.pack(side="right", padx=15, pady=15)
        
        # Buttons frame
        buttons_frame = tk.Frame(content_frame, bg="#f8fafc")
        buttons_frame.pack(fill="x", pady=(10, 0))
        
        # Test buttons
        test_health_btn = tk.Button(
            buttons_frame,
            text="🔍 Test Health",
            font=("Segoe UI", 10),
            bg="#10b981",
            fg="white",
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=10,
            command=self.test_health,
            cursor="hand2"
        )
        test_health_btn.pack(side="left", padx=(0, 10))
        
        clear_btn = tk.Button(
            buttons_frame,
            text="🗑️ Xóa Chat",
            font=("Segoe UI", 10),
            bg="#ef4444",
            fg="white",
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=10,
            command=self.clear_chat,
            cursor="hand2"
        )
        clear_btn.pack(side="left", padx=(0, 10))
        
        # Add welcome message
        self.add_message("🤖 StillMe AI", "Xin chào! Tôi là StillMe AI. Hãy gửi tin nhắn để bắt đầu trò chuyện!", "ai")
    
    def on_key_press(self, event):
        """Handle key press events"""
        if event.keysym == "Return":
            self.send_message()
            return "break"
    
    def test_connection(self):
        """Test kết nối đến Gateway"""
        def test():
            try:
                response = requests.get(f"{self.gateway_url}/health", timeout=5)
                if response.status_code == 200:
                    self.status_label.config(text="✅ Kết nối thành công", fg="#10b981")
                else:
                    self.status_label.config(text="❌ Kết nối thất bại", fg="#ef4444")
            except Exception as e:
                self.status_label.config(text="❌ Kết nối thất bại", fg="#ef4444")
        
        threading.Thread(target=test, daemon=True).start()
    
    def test_health(self):
        """Test health endpoint"""
        def test():
            try:
                response = requests.get(f"{self.gateway_url}/health", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    self.add_message("🔍 Health Check", f"Status: {data['status']}\nTimestamp: {data['timestamp']}", "system")
                else:
                    self.add_message("❌ Health Check", "Lỗi kết nối", "error")
            except Exception as e:
                self.add_message("❌ Health Check", f"Lỗi: {str(e)}", "error")
        
        threading.Thread(target=test, daemon=True).start()
    
    def send_message(self, event=None):
        """Gửi tin nhắn đến Gateway"""
        message = self.message_entry.get().strip()
        if not message:
            return
        
        # Clear input
        self.message_entry.delete(0, tk.END)
        
        # Add user message
        self.add_message("👤 Bạn", message, "user")
        
        # Send to Gateway
        def send():
            try:
                payload = {
                    "message": message,
                    "language": "vi"
                }
                
                response = requests.post(
                    f"{self.gateway_url}/send-message",
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.add_message("🤖 StillMe AI", data.get("response", "Không có phản hồi"), "ai")
                else:
                    self.add_message("❌ Lỗi", f"HTTP {response.status_code}", "error")
                    
            except Exception as e:
                self.add_message("❌ Lỗi", f"Kết nối thất bại: {str(e)}", "error")
        
        threading.Thread(target=send, daemon=True).start()
    
    def add_message(self, sender, message, msg_type):
        """Thêm tin nhắn vào chat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Configure tags
        self.chat_text.tag_configure("user", foreground="#3b82f6", font=("Segoe UI", 11, "bold"))
        self.chat_text.tag_configure("ai", foreground="#10b981", font=("Segoe UI", 11, "bold"))
        self.chat_text.tag_configure("system", foreground="#6b7280", font=("Segoe UI", 11, "bold"))
        self.chat_text.tag_configure("error", foreground="#ef4444", font=("Segoe UI", 11, "bold"))
        self.chat_text.tag_configure("timestamp", foreground="#9ca3af", font=("Segoe UI", 9))
        
        # Add message
        self.chat_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.chat_text.insert(tk.END, f"{sender}: ", msg_type)
        self.chat_text.insert(tk.END, f"{message}\n\n")
        
        # Scroll to bottom
        self.chat_text.see(tk.END)
    
    def clear_chat(self):
        """Xóa chat history"""
        self.chat_text.delete(1.0, tk.END)
        self.add_message("🤖 StillMe AI", "Chat đã được xóa. Hãy gửi tin nhắn để bắt đầu trò chuyện!", "ai")

def main():
    root = tk.Tk()
    app = StillMeDesktopApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
