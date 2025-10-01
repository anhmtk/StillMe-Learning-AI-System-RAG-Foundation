#!/usr/bin/env python3
"""
StillMe Desktop Chat App - Giao diện chat như DeepSeek
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import json
import threading
from datetime import datetime

class StillMeChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("StillMe AI Chat")
        self.root.geometry("800x600")
        self.root.configure(bg="#1a1a1a")

        # API endpoint - can be changed in settings
        self.api_url = "http://127.0.0.1:1216/chat"

        # Chat history
        self.chat_history = []

        self.setup_ui()

    def setup_ui(self):
        """Setup giao diện chat"""
        # Main frame
        main_frame = tk.Frame(self.root, bg="#1a1a1a")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Chat display area
        self.chat_display = scrolledtext.ScrolledText(
            main_frame,
            bg="#2d2d2d",
            fg="#ffffff",
            font=("Segoe UI", 11),
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=20
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Input frame
        input_frame = tk.Frame(main_frame, bg="#1a1a1a")
        input_frame.pack(fill=tk.X, pady=(0, 10))

        # Message input
        self.message_input = tk.Text(
            input_frame,
            bg="#2d2d2d",
            fg="#ffffff",
            font=("Segoe UI", 11),
            height=3,
            wrap=tk.WORD
        )
        self.message_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Send button
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            bg="#007acc",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            command=self.send_message,
            width=10
        )
        self.send_button.pack(side=tk.RIGHT)

        # Settings button
        settings_button = tk.Button(
            main_frame,
            text="Settings",
            bg="#444444",
            fg="#ffffff",
            font=("Segoe UI", 9),
            command=self.open_settings
        )
        settings_button.pack(fill=tk.X, pady=(0, 5))

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(
            main_frame,
            textvariable=self.status_var,
            bg="#1a1a1a",
            fg="#888888",
            font=("Segoe UI", 9)
        )
        status_bar.pack(fill=tk.X)

        # Bind Enter key
        self.message_input.bind("<Control-Return>", lambda e: self.send_message())

        # Welcome message
        self.add_message("StillMe AI", "Xin chào! Tôi là StillMe AI. Bạn cần giúp gì?", "assistant")

    def add_message(self, sender, message, role):
        """Thêm message vào chat"""
        self.chat_display.config(state=tk.NORMAL)

        # Timestamp
        timestamp = datetime.now().strftime("%H:%M")

        # Sender color
        if role == "user":
            sender_color = "#007acc"
            message_color = "#ffffff"
        else:
            sender_color = "#00aa00"
            message_color = "#e0e0e0"

        # Add message
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.chat_display.insert(tk.END, f"{sender}: ", "sender")
        self.chat_display.insert(tk.END, f"{message}\n\n", "message")

        # Configure tags
        self.chat_display.tag_configure("timestamp", foreground="#888888")
        self.chat_display.tag_configure("sender", foreground=sender_color, font=("Segoe UI", 11, "bold"))
        self.chat_display.tag_configure("message", foreground=message_color)

        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def send_message(self):
        """Gửi message"""
        message = self.message_input.get("1.0", tk.END).strip()
        if not message:
            return

        # Clear input
        self.message_input.delete("1.0", tk.END)

        # Add user message
        self.add_message("You", message, "user")

        # Update status
        self.status_var.set("Đang gửi...")
        self.send_button.config(state=tk.DISABLED)

        # Send in thread
        thread = threading.Thread(target=self.send_to_api, args=(message,))
        thread.daemon = True
        thread.start()

    def send_to_api(self, message):
        """Gửi message đến API"""
        try:
            payload = {
                "message": message,
                "session_id": "desktop_chat"
            }

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "Không có phản hồi")
                model = data.get("model", "unknown")
                latency = data.get("latency_ms", 0)

                # Update UI in main thread
                self.root.after(0, self.handle_response, response_text, model, latency)
            else:
                error_msg = f"Lỗi {response.status_code}: {response.text}"
                self.root.after(0, self.handle_error, error_msg)

        except requests.exceptions.Timeout:
            self.root.after(0, self.handle_error, "Timeout - Vui lòng thử lại")
        except requests.exceptions.ConnectionError:
            self.root.after(0, self.handle_error, "Không thể kết nối đến StillMe Backend")
        except Exception as e:
            self.root.after(0, self.handle_error, f"Lỗi: {str(e)}")

    def handle_response(self, response_text, model, latency):
        """Xử lý response từ API"""
        # Add assistant message
        self.add_message("StillMe AI", response_text, "assistant")

        # Update status
        self.status_var.set(f"Model: {model} | Latency: {latency:.0f}ms")
        self.send_button.config(state=tk.NORMAL)

    def handle_error(self, error_msg):
        """Xử lý lỗi"""
        self.add_message("System", f"❌ {error_msg}", "system")
        self.status_var.set("Lỗi")
        self.send_button.config(state=tk.NORMAL)

    def open_settings(self):
        """Mở settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x200")
        settings_window.configure(bg="#1a1a1a")

        # API URL setting
        tk.Label(settings_window, text="API URL:", bg="#1a1a1a", fg="#ffffff", font=("Segoe UI", 11)).pack(pady=10)

        url_frame = tk.Frame(settings_window, bg="#1a1a1a")
        url_frame.pack(fill=tk.X, padx=20)

        self.url_var = tk.StringVar(value=self.api_url)
        url_entry = tk.Entry(url_frame, textvariable=self.url_var, bg="#2d2d2d", fg="#ffffff", font=("Segoe UI", 11))
        url_entry.pack(fill=tk.X, pady=5)

        # Help text
        help_text = tk.Label(
            settings_window,
            text="Default: http://127.0.0.1:1216\nFor mobile testing: http://192.168.x.x:1216",
            bg="#1a1a1a",
            fg="#888888",
            font=("Segoe UI", 9),
            justify=tk.LEFT
        )
        help_text.pack(pady=10)

        # Buttons
        button_frame = tk.Frame(settings_window, bg="#1a1a1a")
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        def save_settings():
            self.api_url = self.url_var.get()
            settings_window.destroy()
            self.add_message("System", f"✅ API URL updated: {self.api_url}", "system")

        tk.Button(button_frame, text="Save", command=save_settings, bg="#007acc", fg="#ffffff").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=settings_window.destroy, bg="#444444", fg="#ffffff").pack(side=tk.LEFT, padx=5)

def main():
    root = tk.Tk()
    app = StillMeChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
