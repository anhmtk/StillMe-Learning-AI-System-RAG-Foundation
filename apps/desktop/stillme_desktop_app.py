#!/usr/bin/env python3
"""
StillMe Desktop Chat App - Beautiful UI like FlutterFlow
"""

import os
import re
import sys
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext

import requests

# Add libs to path for language detection
sys.path.append(os.path.join(os.path.dirname(__file__), "../../libs"))
from design_tokens import design_tokens
from lang.detect import detect_language, get_language_name
from performance_tracker import performance_tracker
from system_prompt import system_prompt_manager

# Add config to path for branding
sys.path.append(os.path.join(os.path.dirname(__file__), "../../config"))
from brand import get_about_text, get_header_text, get_settings_text, get_window_title

# Add runtime to path for policy loading
sys.path.append(os.path.join(os.path.dirname(__file__), "../../runtime"))
from policy_loader import load_policies


class StillMeDesktopApp:
    def __init__(self, root):
        # Load policies first
        try:
            load_policies()
            print("✅ Policies loaded successfully")
        except Exception as e:
            print(f"❌ Policy loading failed: {e}")
            # Continue anyway for development

        self.root = root
        self.root.title(get_window_title())
        self.root.geometry("1200x800")
        self.root.configure(bg=design_tokens.get_tkinter_color("backgroundPrimary"))

        # API endpoint - can be changed in settings
        self.api_url = "http://127.0.0.1:1216/chat"

        # Chat history and session management
        self.chat_history = []
        self.session_id = "desktop_user"
        self.message_count = 0

        # Performance tracking
        self.current_metrics = None

        # Web search toggle
        self.web_search_enabled = True  # Default enabled

        self.setup_ui()
        self.add_welcome_message()

    def setup_ui(self):
        """Setup beautiful UI like FlutterFlow"""
        # Main container with padding
        main_container = tk.Frame(
            self.root, bg=design_tokens.get_tkinter_color("backgroundPrimary")
        )
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        self.setup_header(main_container)

        # Main content area
        content_frame = tk.Frame(
            main_container, bg=design_tokens.get_tkinter_color("backgroundPrimary")
        )
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

        # Chat area
        self.setup_chat_area(content_frame)

        # Input area
        self.setup_input_area(content_frame)

        # Status bar
        self.setup_status_bar(main_container)

    def setup_header(self, parent):
        """Setup header with logo and settings"""
        header_frame = tk.Frame(
            parent, bg=design_tokens.get_tkinter_color("backgroundPrimary")
        )
        header_frame.pack(fill=tk.X, pady=(0, 20))

        # Logo and title
        title_frame = tk.Frame(
            header_frame, bg=design_tokens.get_tkinter_color("backgroundPrimary")
        )
        title_frame.pack(side=tk.LEFT)

        # StillMe logo (text-based)
        header_text = get_header_text()
        logo_label = tk.Label(
            title_frame,
            text=header_text["title"],
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 24, "bold"),
            fg=design_tokens.get_tkinter_color("textPrimary"),
            bg=design_tokens.get_tkinter_color("backgroundPrimary"),
        )
        logo_label.pack(side=tk.LEFT)

        # Subtitle
        subtitle_label = tk.Label(
            title_frame,
            text=header_text["subtitle"],
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 12),
            fg=design_tokens.get_tkinter_color("textSecondary"),
            bg=design_tokens.get_tkinter_color("backgroundPrimary"),
        )
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))

        # Web search toggle
        self.web_search_var = tk.BooleanVar(value=self.web_search_enabled)
        web_search_toggle = tk.Checkbutton(
            header_frame,
            text="🌐 Web Search",
            variable=self.web_search_var,
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 10),
            bg=design_tokens.get_tkinter_color("backgroundPrimary"),
            fg=design_tokens.get_tkinter_color("textPrimary"),
            selectcolor=design_tokens.get_tkinter_color("accentCyan"),
            activebackground=design_tokens.get_tkinter_color("backgroundPrimary"),
            activeforeground=design_tokens.get_tkinter_color("textPrimary"),
            command=self.toggle_web_search,
        )
        web_search_toggle.pack(side=tk.RIGHT, padx=(0, 10))

        # Settings button
        settings_btn = tk.Button(
            header_frame,
            text="⚙️ Settings",
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 10),
            bg=design_tokens.get_tkinter_color("buttonSecondary"),
            fg=design_tokens.get_tkinter_color("textPrimary"),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            command=self.open_settings,
        )
        settings_btn.pack(side=tk.RIGHT)

        # About button
        about_btn = tk.Button(
            header_frame,
            text="ℹ️ About",
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 10),
            bg=design_tokens.get_tkinter_color("buttonSecondary"),
            fg=design_tokens.get_tkinter_color("textPrimary"),
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=8,
            command=self.open_about,
        )
        about_btn.pack(side=tk.RIGHT, padx=(0, 10))

    def setup_chat_area(self, parent):
        """Setup chat display area"""
        # Chat container with rounded corners effect
        chat_container = tk.Frame(
            parent,
            bg=design_tokens.get_tkinter_color("backgroundSecondary"),
            relief=tk.FLAT,
            bd=0,
        )
        chat_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            chat_container,
            bg=design_tokens.get_tkinter_color("backgroundSecondary"),
            fg=design_tokens.get_tkinter_color("textPrimary"),
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 12),
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=20,
            insertbackground=design_tokens.get_tkinter_color("textPrimary"),
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Configure text tags for different message types
        self.chat_display.tag_configure(
            "user",
            foreground=design_tokens.get_tkinter_color("accentCyan"),
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 12, "bold"),
        )
        self.chat_display.tag_configure(
            "ai",
            foreground=design_tokens.get_tkinter_color("success"),
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 12),
        )
        self.chat_display.tag_configure(
            "system",
            foreground=design_tokens.get_tkinter_color("warning"),
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 10, "italic"),
        )
        self.chat_display.tag_configure(
            "error",
            foreground=design_tokens.get_tkinter_color("error"),
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 10, "bold"),
        )
        self.chat_display.tag_configure(
            "timestamp",
            foreground=design_tokens.get_tkinter_color("textMuted"),
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 9),
        )
        self.chat_display.tag_configure(
            "performance",
            foreground=design_tokens.get_tkinter_color("textAccent"),
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 9, "italic"),
        )
        self.chat_display.tag_configure(
            "attribution",
            foreground=design_tokens.get_tkinter_color("textMuted"),
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 9, "italic"),
        )

    def setup_input_area(self, parent):
        """Setup input area"""
        input_container = tk.Frame(
            parent, bg=design_tokens.get_tkinter_color("backgroundPrimary")
        )
        input_container.pack(fill=tk.X, pady=(0, 10))

        # Input frame with rounded corners effect
        input_frame = tk.Frame(
            input_container,
            bg=design_tokens.get_tkinter_color("backgroundSecondary"),
            relief=tk.FLAT,
            bd=0,
        )
        input_frame.pack(fill=tk.X, padx=2, pady=2)

        # Message input
        self.message_input = tk.Text(
            input_frame,
            bg=design_tokens.get_tkinter_color("backgroundSecondary"),
            fg=design_tokens.get_tkinter_color("textPrimary"),
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 12),
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=12,
            height=3,
            wrap=tk.WORD,
            insertbackground=design_tokens.get_tkinter_color("textPrimary"),
        )
        self.message_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Send button
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 12, "bold"),
            bg=design_tokens.get_tkinter_color("accentCyan"),
            fg=design_tokens.get_tkinter_color("textPrimary"),
            relief=tk.FLAT,
            padx=20,
            pady=12,
            command=self.send_message,
            state=tk.NORMAL,
        )
        self.send_button.pack(side=tk.RIGHT, padx=2, pady=2)

        # Bind Enter key - Enter = Send, Shift+Enter = newline
        self.message_input.bind("<Return>", self._on_enter_key)
        self.message_input.bind("<Shift-Return>", self._on_shift_enter_key)

        # Settings for Enter behavior
        self.enter_to_send = True  # Default: Enter = Send

        # Language detection and tracking
        self.user_turn_locale = "vi-VN"  # Current turn language
        self.session_preferred_locale = "vi-VN"  # Session preferred language
        self.language_override = None  # Manual language override

    def setup_status_bar(self, parent):
        """Setup status bar"""
        status_frame = tk.Frame(
            parent, bg=design_tokens.get_tkinter_color("backgroundPrimary")
        )
        status_frame.pack(fill=tk.X, pady=(10, 0))

        # Status label
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 10),
            fg=design_tokens.get_tkinter_color("textSecondary"),
            bg=design_tokens.get_tkinter_color("backgroundPrimary"),
        )
        self.status_label.pack(side=tk.LEFT)

        # Performance metrics label
        self.performance_label = tk.Label(
            status_frame,
            text="",
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 9),
            fg=design_tokens.get_tkinter_color("textAccent"),
            bg=design_tokens.get_tkinter_color("backgroundPrimary"),
        )
        self.performance_label.pack(side=tk.LEFT, padx=(20, 0))

        # Web search status indicator
        self.web_search_status_label = tk.Label(
            status_frame,
            text="🌐 Web Search: ON",
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 10),
            fg=design_tokens.get_tkinter_color("success"),
            bg=design_tokens.get_tkinter_color("backgroundPrimary"),
        )
        self.web_search_status_label.pack(side=tk.RIGHT)

        # Language indicator
        self.language_label = tk.Label(
            status_frame,
            text="🌐 VI",
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 10),
            fg=design_tokens.get_tkinter_color("warning"),
            bg=design_tokens.get_tkinter_color("backgroundPrimary"),
        )
        self.language_label.pack(side=tk.RIGHT, padx=(0, 10))

        # Connection status
        self.connection_label = tk.Label(
            status_frame,
            text="● Connected",
            font=(design_tokens.TYPOGRAPHY["fontFamily"], 10),
            fg=design_tokens.get_tkinter_color("success"),
            bg=design_tokens.get_tkinter_color("backgroundPrimary"),
        )
        self.connection_label.pack(side=tk.RIGHT)

    def add_welcome_message(self):
        """Add welcome message"""
        self.add_message(
            "StillMe AI", "Xin chào! Tôi là StillMe AI. Bạn cần giúp gì?", "ai"
        )

    def add_message(self, sender, message, msg_type="user", metrics=None):
        """Add message to chat with optional performance metrics"""
        self.chat_display.config(state=tk.NORMAL)

        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")

        # Add sender and message
        self.chat_display.insert(tk.END, f"{sender}: ", msg_type)
        self.chat_display.insert(tk.END, f"{message}\n", "default")

        # Add performance metrics if available
        if metrics and msg_type == "ai":
            self.chat_display.insert(
                tk.END, f"  📊 {metrics.get_display_text()}\n", "performance"
            )

        self.chat_display.insert(tk.END, "\n", "default")

        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def normalize_bot_identity(self, text):
        """Normalize bot identity - replace any model self-identification with StillMe"""
        if not text:
            return text

        # Patterns to replace model self-identification
        patterns = [
            # English patterns
            (
                r"\b(I am|I\'m)\s+(Gemma|OpenAI|DeepSeek|GPT|ChatGPT|Claude|Anthropic|model|AI assistant)\b",
                "I am StillMe",
            ),
            (
                r"\b(My name is|I\'m called)\s+(Gemma|OpenAI|DeepSeek|GPT|ChatGPT|Claude|Anthropic|model|AI assistant)\b",
                "My name is StillMe",
            ),
            (
                r"\b(I\'m a|I am a)\s+(Gemma|OpenAI|DeepSeek|GPT|ChatGPT|Claude|Anthropic|model|AI assistant)\b",
                "I am StillMe",
            ),
            # Vietnamese patterns
            (
                r"\b(Mình là|Tôi là|Mình tên|Tôi tên)\s+(Gemma|OpenAI|DeepSeek|GPT|ChatGPT|Claude|Anthropic|model|AI assistant|trợ lý AI)\b",
                "Mình là StillMe",
            ),
            (
                r"\b(Mình là|Tôi là)\s+(một|một con|một cái)\s+(Gemma|OpenAI|DeepSeek|GPT|ChatGPT|Claude|Anthropic|model|AI assistant|trợ lý AI)\b",
                "Mình là StillMe",
            ),
            # Generic patterns
            (
                r"\b(Gemma|OpenAI|DeepSeek|GPT|ChatGPT|Claude|Anthropic)\s+(here|đây|speaking|nói)\b",
                "StillMe here",
            ),
            (
                r"\b(As a|Là một)\s+(Gemma|OpenAI|DeepSeek|GPT|ChatGPT|Claude|Anthropic|model|AI assistant)\b",
                "As StillMe",
            ),
        ]

        normalized_text = text
        for pattern, replacement in patterns:
            normalized_text = re.sub(
                pattern, replacement, normalized_text, flags=re.IGNORECASE
            )

        return normalized_text

    def _on_enter_key(self, event):
        """Handle Enter key - Send message if enter_to_send is True"""
        if self.enter_to_send:
            self.send_message()
            return "break"  # Prevent default behavior
        return None  # Allow default behavior (newline)

    def _on_shift_enter_key(self, event):
        """Handle Shift+Enter key - Always insert newline"""
        # Insert newline at cursor position
        self.message_input.insert(tk.INSERT, "\n")
        return "break"  # Prevent default behavior

    def send_message(self):
        """Send message to StillMe AI"""
        message = self.message_input.get("1.0", tk.END).strip()
        if not message:
            return

        # Increment message count
        self.message_count += 1

        # Add user message to chat
        self.add_message("You", message, "user")

        # Clear input
        self.message_input.delete("1.0", tk.END)

        # Disable send button
        self.send_button.config(state=tk.DISABLED)
        self.status_label.config(
            text="Sending...", fg=design_tokens.get_tkinter_color("warning")
        )

        # Send in background thread
        threading.Thread(
            target=self._send_message_thread, args=(message,), daemon=True
        ).start()

    def _send_message_thread(self, message):
        """Send message in background thread"""
        try:
            # Start performance tracking
            performance_tracker.start_timing()

            # Detect language from user message
            detected_locale = detect_language(message)
            self.user_turn_locale = detected_locale

            # Update session preferred locale if user switches language consistently
            if hasattr(self, "_last_languages"):
                self._last_languages.append(detected_locale)
                if len(self._last_languages) > 3:
                    self._last_languages.pop(0)

                # If user uses same language for 2+ consecutive turns, update preference
                if len(self._last_languages) >= 2 and all(
                    lang == detected_locale for lang in self._last_languages[-2:]
                ):
                    self.session_preferred_locale = detected_locale
            else:
                self._last_languages = [detected_locale]

            # Use manual override if set
            current_locale = (
                self.language_override
                if self.language_override
                else self.user_turn_locale
            )
            language_name = get_language_name(current_locale)

            # Update language indicator in UI
            lang_code = current_locale.split("-")[0].upper()
            self.root.after(
                0, lambda: self.language_label.config(text=f"🌐 {lang_code}")
            )

            # Check if this is the first message in session
            is_first_message = self.message_count == 1

            # Get system prompt from manager
            system_prompt = system_prompt_manager.get_system_prompt(
                language_name=language_name,
                locale=current_locale,
                session_id=self.session_id,
                is_first_message=is_first_message,
            )

            payload = {
                "message": message,
                "session_id": self.session_id,
                "system_prompt": system_prompt,
                "web_search_enabled": self.web_search_enabled,
            }

            response = requests.post(self.api_url, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "No response")
                model = result.get("model", "unknown")
                engine = result.get("engine", "unknown")
                latency = result.get("latency_ms", 0)

                # Check if this is a web request with attribution
                attribution = result.get("attribution")
                is_web_request = result.get("is_web_request", False)

                # Create performance metrics
                metrics = performance_tracker.create_metrics(
                    model=model,
                    engine=engine,
                    input_text=message,
                    output_text=ai_response,
                    latency_ms=latency,
                    session_id=self.session_id,
                )

                # Update UI in main thread
                self.root.after(
                    0,
                    self._handle_success,
                    ai_response,
                    metrics,
                    attribution,
                    is_web_request,
                )
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                self.root.after(0, self._handle_error, error_msg)

        except Exception as e:
            self.root.after(0, self._handle_error, str(e))

    def _handle_success(
        self, response, metrics, attribution=None, is_web_request=False
    ):
        """Handle successful response with optional attribution"""
        # Normalize bot identity before displaying
        normalized_response = self.normalize_bot_identity(response)
        self.add_message("StillMe AI", normalized_response, "ai", metrics)

        # Add attribution if this is a web request
        if is_web_request and attribution:
            self._add_attribution_message(attribution)

        # Update performance display
        self.performance_label.config(text=metrics.get_display_text())

        # Show status
        self.status_label.config(
            text="Ready", fg=design_tokens.get_tkinter_color("success")
        )
        self.send_button.config(state=tk.NORMAL)

    def _add_attribution_message(self, attribution):
        """Add attribution message for web content"""
        try:
            source_name = attribution.get("source_name", "Unknown Source")
            attribution.get("url", "")
            retrieved_at = attribution.get("retrieved_at", "")
            domain = attribution.get("domain", "")

            # Format timestamp
            if retrieved_at:
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
                    formatted_time = dt.strftime("%H:%M")
                except:
                    formatted_time = "Unknown"
            else:
                formatted_time = "Unknown"

            # Create attribution text
            attribution_text = f"📰 Source: {source_name} • {formatted_time} • {domain}"

            # Add attribution message with special styling
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, f"    {attribution_text}\n", "attribution")
            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)

        except Exception as e:
            print(f"Error adding attribution: {e}")

    def _handle_error(self, error_msg):
        """Handle error"""
        self.add_message("System", f"Error: {error_msg}", "error")
        self.status_label.config(
            text="Error", fg=design_tokens.get_tkinter_color("error")
        )
        self.performance_label.config(text="")
        self.send_button.config(state=tk.NORMAL)

    def toggle_web_search(self):
        """Toggle web search functionality"""
        self.web_search_enabled = self.web_search_var.get()

        # Update status indicator
        if self.web_search_enabled:
            self.web_search_status_label.config(
                text="🌐 Web Search: ON", fg=design_tokens.get_tkinter_color("success")
            )
        else:
            self.web_search_status_label.config(
                text="🌐 Web Search: OFF", fg=design_tokens.get_tkinter_color("error")
            )

        # Log the change
        status = "enabled" if self.web_search_enabled else "disabled"
        print(f"🌐 Web search {status}")

    def open_settings(self):
        """Open settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_text = get_settings_text()
        settings_window.title(settings_text["title"])
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
            text=settings_text["title"],
            font=("Segoe UI", 18, "bold"),
            fg="#ffffff",
            bg="#0f0f23",
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
            bg="#0f0f23",
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
            insertbackground="#ffffff",
        )
        url_entry.pack(fill=tk.X, pady=(5, 0), ipady=8)

        # Enter behavior setting
        enter_frame = tk.Frame(settings_window, bg="#0f0f23")
        enter_frame.pack(fill=tk.X, padx=20, pady=10)

        enter_label = tk.Label(
            enter_frame,
            text="Enter Key Behavior:",
            font=("Segoe UI", 12),
            fg="#ffffff",
            bg="#0f0f23",
        )
        enter_label.pack(anchor=tk.W)

        self.enter_to_send_var = tk.BooleanVar(value=self.enter_to_send)
        enter_checkbox = tk.Checkbutton(
            enter_frame,
            text="Enter to send message (Shift+Enter for newline)",
            variable=self.enter_to_send_var,
            font=("Segoe UI", 10),
            fg="#ffffff",
            bg="#0f0f23",
            selectcolor="#1a1a2e",
            activebackground="#0f0f23",
            activeforeground="#ffffff",
        )
        enter_checkbox.pack(anchor=tk.W, pady=(5, 0))

        # Language override setting
        lang_frame = tk.Frame(settings_window, bg="#0f0f23")
        lang_frame.pack(fill=tk.X, padx=20, pady=10)

        lang_label = tk.Label(
            lang_frame,
            text="Language Override:",
            font=("Segoe UI", 12),
            fg="#ffffff",
            bg="#0f0f23",
        )
        lang_label.pack(anchor=tk.W)

        lang_help = tk.Label(
            lang_frame,
            text="Override auto-detected language (leave empty for auto-detection)",
            font=("Segoe UI", 9),
            fg="#888888",
            bg="#0f0f23",
        )
        lang_help.pack(anchor=tk.W)

        self.lang_override_var = tk.StringVar(value=self.language_override or "")
        lang_entry = tk.Entry(
            lang_frame,
            textvariable=self.lang_override_var,
            font=("Segoe UI", 11),
            bg="#1a1a2e",
            fg="#ffffff",
            relief=tk.FLAT,
            bd=0,
            insertbackground="#ffffff",
        )
        lang_entry.pack(fill=tk.X, pady=(5, 0), ipady=8)

        # Language options
        lang_options_frame = tk.Frame(lang_frame, bg="#0f0f23")
        lang_options_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Button(
            lang_options_frame,
            text="VI (Vietnamese)",
            command=lambda: self.lang_override_var.set("vi-VN"),
            font=("Segoe UI", 9),
            bg="#1a1a2e",
            fg="#ffffff",
            relief=tk.FLAT,
            bd=1,
            padx=10,
            pady=5,
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            lang_options_frame,
            text="EN (English)",
            command=lambda: self.lang_override_var.set("en-US"),
            font=("Segoe UI", 9),
            bg="#1a1a2e",
            fg="#ffffff",
            relief=tk.FLAT,
            bd=1,
            padx=10,
            pady=5,
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            lang_options_frame,
            text="Auto",
            command=lambda: self.lang_override_var.set(""),
            font=("Segoe UI", 9),
            bg="#1a1a2e",
            fg="#ffffff",
            relief=tk.FLAT,
            bd=1,
            padx=10,
            pady=5,
        ).pack(side=tk.LEFT)

        # Help text
        help_text = tk.Label(
            settings_window,
            text="Default: http://127.0.0.1:1216/chat\nFor mobile testing: http://192.168.1.12:1216/chat",
            font=("Segoe UI", 10),
            fg="#a0a0a0",
            bg="#0f0f23",
            justify=tk.LEFT,
        )
        help_text.pack(pady=10)

        # Buttons
        button_frame = tk.Frame(settings_window, bg="#0f0f23")
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        def save_settings():
            self.api_url = self.url_var.get()
            self.enter_to_send = self.enter_to_send_var.get()

            # Update language override
            lang_override = self.lang_override_var.get().strip()
            self.language_override = lang_override if lang_override else None

            settings_window.destroy()
            lang_status = f", Language override = {self.language_override or 'Auto'}"
            self.add_message(
                "System",
                f"Settings updated: API URL = {self.api_url}, Enter to send = {self.enter_to_send}{lang_status}",
                "system",
            )

        def test_connection():
            try:
                response = requests.get(
                    self.url_var.get().replace("/chat", "/health"), timeout=5
                )
                if response.status_code == 200:
                    messagebox.showinfo("Success", "Connection successful!")
                else:
                    messagebox.showerror(
                        "Error", f"Connection failed: {response.status_code}"
                    )
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
            command=test_connection,
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
            command=save_settings,
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
            command=settings_window.destroy,
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(0, 10))

    def open_about(self):
        """Open about dialog"""
        about_window = tk.Toplevel(self.root)
        about_text = get_about_text()
        about_window.title(about_text["title"])
        about_window.geometry("600x400")
        about_window.configure(bg="#0f0f23")
        about_window.resizable(False, False)

        # Center the window
        about_window.transient(self.root)
        about_window.grab_set()

        # Header
        header_frame = tk.Frame(about_window, bg="#0f0f23")
        header_frame.pack(fill=tk.X, padx=20, pady=20)

        title_label = tk.Label(
            header_frame,
            text=about_text["title"],
            font=("Segoe UI", 18, "bold"),
            fg="#ffffff",
            bg="#0f0f23",
        )
        title_label.pack()

        # Content
        content_frame = tk.Frame(about_window, bg="#0f0f23")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Description
        desc_text = tk.Text(
            content_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            bg="#1a1a2e",
            fg="#ffffff",
            relief=tk.FLAT,
            bd=0,
            padx=15,
            pady=15,
        )
        desc_text.pack(fill=tk.BOTH, expand=True)
        desc_text.insert(tk.END, about_text["description"])
        desc_text.config(state=tk.DISABLED)

        # Version info
        version_frame = tk.Frame(about_window, bg="#0f0f23")
        version_frame.pack(fill=tk.X, padx=20, pady=10)

        version_label = tk.Label(
            version_frame,
            text="Version 2.1.1 | Enterprise Grade Framework",
            font=("Segoe UI", 10),
            fg="#a0a0a0",
            bg="#0f0f23",
        )
        version_label.pack()

        # Close button
        close_btn = tk.Button(
            about_window,
            text="Close",
            font=("Segoe UI", 11),
            bg="#1a1a2e",
            fg="#ffffff",
            relief=tk.FLAT,
            bd=1,
            padx=20,
            pady=8,
            command=about_window.destroy,
        )
        close_btn.pack(pady=20)


def main():
    root = tk.Tk()
    StillMeDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
