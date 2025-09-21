#!/usr/bin/env python3
"""
StillMe Desktop Chat App - Beautiful UI like FlutterFlow
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import json
import threading
from datetime import datetime
import webbrowser

class StillMeDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("StillMe AI Chat")
        self.root.geometry("1200x800")
        self.root.configure(bg="#0f0f23")  # Dark blue background like FlutterFlow
        
        # API endpoint - can be changed in settings
        self.api_url = "http://127.0.0.1:1216/chat"
        
        # Chat history
        self.chat_history = []
        
        self.setup_ui()
        self.add_welcome_message()
        
    def setup_ui(self):
        """Setup beautiful UI like FlutterFlow"""
        # Main container with padding
        main_container = tk.Frame(self.root, bg="#0f0f23")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self.setup_header(main_container)
        
        # Main content area
        content_frame = tk.Frame(main_container, bg="#0f0f23")
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Chat area
        self.setup_chat_area(content_frame)
        
        # Input area
        self.setup_input_area(content_frame)
        
        # Status bar
        self.setup_status_bar(main_container)
        
    def setup_header(self, parent):
        """Setup header with logo and settings"""
        header_frame = tk.Frame(parent, bg="#0f0f23")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Logo and title
        title_frame = tk.Frame(header_frame, bg="#0f0f23")
        title_frame.pack(side=tk.LEFT)
        
        # StillMe logo (text-based)
        logo_label = tk.Label(
            title_frame,
            text="StillMe AI",
            font=("Segoe UI", 24, "bold"),
            fg="#ffffff",
            bg="#0f0f23"
        )
        logo_label.pack(side=tk.LEFT)
        
        # Subtitle
        subtitle_label = tk.Label(
            title_frame,
            text="Your AI Companion",
            font=("Segoe UI", 12),
            fg="#a0a0a0",
            bg="#0f0f23"
        )
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Settings button
        settings_btn = tk.Button(
            header_frame,
            text="⚙️ Settings",
            font=("Segoe UI", 10),
            bg="#1a1a2e",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            command=self.open_settings
        )
        settings_btn.pack(side=tk.RIGHT)
        
    def setup_chat_area(self, parent):
        """Setup chat display area"""
        # Chat container with rounded corners effect
        chat_container = tk.Frame(parent, bg="#1a1a2e", relief=tk.FLAT, bd=0)
        chat_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            chat_container,
            bg="#1a1a2e",
            fg="#ffffff",
            font=("Segoe UI", 12),
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=20,
            insertbackground="#ffffff"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Configure text tags for different message types
        self.chat_display.tag_configure("user", foreground="#4fc3f7", font=("Segoe UI", 12, "bold"))
        self.chat_display.tag_configure("ai", foreground="#81c784", font=("Segoe UI", 12))
        self.chat_display.tag_configure("system", foreground="#ffb74d", font=("Segoe UI", 10, "italic"))
        self.chat_display.tag_configure("error", foreground="#f48fb1", font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_configure("timestamp", foreground="#757575", font=("Segoe UI", 9))
        
    def setup_input_area(self, parent):
        """Setup input area"""
        input_container = tk.Frame(parent, bg="#0f0f23")
        input_container.pack(fill=tk.X, pady=(0, 10))
        
        # Input frame with rounded corners effect
        input_frame = tk.Frame(input_container, bg="#1a1a2e", relief=tk.FLAT, bd=0)
        input_frame.pack(fill=tk.X, padx=2, pady=2)
        
        # Message input
        self.message_input = tk.Text(
            input_frame,
            bg="#1a1a2e",
            fg="#ffffff",
            font=("Segoe UI", 12),
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=12,
            height=3,
            wrap=tk.WORD,
            insertbackground="#ffffff"
        )
        self.message_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Send button
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            font=("Segoe UI", 12, "bold"),
            bg="#4fc3f7",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=12,
            command=self.send_message,
            state=tk.NORMAL
        )
        self.send_button.pack(side=tk.RIGHT, padx=2, pady=2)
        
        # Bind Enter key
        self.message_input.bind("<Control-Return>", lambda e: self.send_message())
        
    def setup_status_bar(self, parent):
        """Setup status bar"""
        status_frame = tk.Frame(parent, bg="#0f0f23")
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Status label
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            font=("Segoe UI", 10),
            fg="#a0a0a0",
            bg="#0f0f23"
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Connection status
        self.connection_label = tk.Label(
            status_frame,
            text="● Connected",
            font=("Segoe UI", 10),
            fg="#81c784",
            bg="#0f0f23"
        )
        self.connection_label.pack(side=tk.RIGHT)
        
    def add_welcome_message(self):
        """Add welcome message"""
        self.add_message("StillMe AI", "Xin chào! Tôi là StillMe AI. Bạn cần giúp gì?", "ai")
        
    def add_message(self, sender, message, msg_type="user"):
        """Add message to chat"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Add sender and message
        self.chat_display.insert(tk.END, f"{sender}: ", msg_type)
        self.chat_display.insert(tk.END, f"{message}\n\n", "default")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
    def send_message(self):
        """Send message to StillMe AI"""
        message = self.message_input.get("1.0", tk.END).strip()
        if not message:
            return
            
        # Add user message to chat
        self.add_message("You", message, "user")
        
        # Clear input
        self.message_input.delete("1.0", tk.END)
        
        # Disable send button
        self.send_button.config(state=tk.DISABLED)
        self.status_label.config(text="Sending...", fg="#ffb74d")
        
        # Send in background thread
        threading.Thread(target=self._send_message_thread, args=(message,), daemon=True).start()
        
    def _send_message_thread(self, message):
        """Send message in background thread"""
        try:
            payload = {
                "message": message,
                "session_id": "desktop_user"
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "No response")
                model = result.get("model", "unknown")
                latency = result.get("latency_ms", 0)
                
                # Update UI in main thread
                self.root.after(0, self._handle_success, ai_response, model, latency)
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                self.root.after(0, self._handle_error, error_msg)
                
        except Exception as e:
            self.root.after(0, self._handle_error, str(e))
            
    def _handle_success(self, response, model, latency):
        """Handle successful response"""
        self.add_message("StillMe AI", response, "ai")
        self.status_label.config(text=f"Model: {model} | Latency: {latency:.0f}ms", fg="#81c784")
        self.send_button.config(state=tk.NORMAL)
        
    def _handle_error(self, error_msg):
        """Handle error"""
        self.add_message("System", f"Error: {error_msg}", "error")
        self.status_label.config(text="Error", fg="#f48fb1")
        self.send_button.config(state=tk.NORMAL)
        
    def open_settings(self):
        """Open settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x300")
        settings_window.configure(bg="#0f0f23")
        settings_window.resizable(False, False)
        
        # Center the window
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Header
        header_frame = tk.Frame(settings_window, bg="#0f0f23")
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        title_label = tk.Label(
            header_frame,
            text="Settings",
            font=("Segoe UI", 18, "bold"),
            fg="#ffffff",
            bg="#0f0f23"
        )
        title_label.pack()
        
        # API URL setting
        url_frame = tk.Frame(settings_window, bg="#0f0f23")
        url_frame.pack(fill=tk.X, padx=20, pady=10)
        
        url_label = tk.Label(
            url_frame,
            text="API URL:",
            font=("Segoe UI", 12),
            fg="#ffffff",
            bg="#0f0f23"
        )
        url_label.pack(anchor=tk.W)
        
        self.url_var = tk.StringVar(value=self.api_url)
        url_entry = tk.Entry(
            url_frame,
            textvariable=self.url_var,
            font=("Segoe UI", 11),
            bg="#1a1a2e",
            fg="#ffffff",
            relief=tk.FLAT,
            bd=0,
            insertbackground="#ffffff"
        )
        url_entry.pack(fill=tk.X, pady=(5, 0), ipady=8)
        
        # Help text
        help_text = tk.Label(
            settings_window,
            text="Default: http://127.0.0.1:1216/chat\nFor mobile testing: http://192.168.1.12:1216/chat",
            font=("Segoe UI", 10),
            fg="#a0a0a0",
            bg="#0f0f23",
            justify=tk.LEFT
        )
        help_text.pack(pady=10)
        
        # Buttons
        button_frame = tk.Frame(settings_window, bg="#0f0f23")
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def save_settings():
            self.api_url = self.url_var.get()
            settings_window.destroy()
            self.add_message("System", f"API URL updated: {self.api_url}", "system")
            
        def test_connection():
            try:
                response = requests.get(self.url_var.get().replace("/chat", "/health"), timeout=5)
                if response.status_code == 200:
                    messagebox.showinfo("Success", "Connection successful!")
                else:
                    messagebox.showerror("Error", f"Connection failed: {response.status_code}")
            except Exception as e:
                messagebox.showerror("Error", f"Connection failed: {str(e)}")
        
        test_btn = tk.Button(
            button_frame,
            text="Test Connection",
            font=("Segoe UI", 10),
            bg="#1a1a2e",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            command=test_connection
        )
        test_btn.pack(side=tk.LEFT)
        
        save_btn = tk.Button(
            button_frame,
            text="Save",
            font=("Segoe UI", 10, "bold"),
            bg="#4fc3f7",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=save_settings
        )
        save_btn.pack(side=tk.RIGHT)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            font=("Segoe UI", 10),
            bg="#1a1a2e",
            fg="#ffffff",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            command=settings_window.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(0, 10))

def main():
    root = tk.Tk()
    app = StillMeDesktopApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
