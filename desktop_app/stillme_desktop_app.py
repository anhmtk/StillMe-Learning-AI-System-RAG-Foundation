#!/usr/bin/env python3
"""
StillMe Desktop App - Enhanced with Mobile Parity
Features: Chat UI, Telemetry, Founder Console, Settings
"""

import json
import threading
import time
import tkinter as tk
import uuid
from datetime import datetime
from tkinter import messagebox, scrolledtext, simpledialog

import requests


class StillMeDesktopApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("StillMe - Personal AI Assistant")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0F172A')

        # Configuration
        self.base_url = "http://160.191.89.99:21568"
        self.session_id = str(uuid.uuid4())
        self.founder_mode = False
        self.founder_passcode = "0000"
        self.telemetry_enabled = True

        # Chat data
        self.messages = []
        self.telemetry_data = []
        self.session_metrics = {
            'total_messages': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'average_latency': 0,
            'models_used': set(),
            'session_start': datetime.now()
        }

        self.setup_ui()
        self.test_connection()

    def setup_ui(self):
        """Setup the main UI"""
        # Main frame
        main_frame = tk.Frame(self.root, bg='#0F172A')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        self.setup_header(main_frame)

        # Content area
        content_frame = tk.Frame(main_frame, bg='#0F172A')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Chat area
        self.setup_chat_area(content_frame)

        # Telemetry panel
        self.setup_telemetry_panel(content_frame)

        # Input area
        self.setup_input_area(main_frame)

    def setup_header(self, parent):
        """Setup header with logo and controls"""
        header_frame = tk.Frame(parent, bg='#1E293B', height=60)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)

        # Logo and title
        logo_frame = tk.Frame(header_frame, bg='#1E293B')
        logo_frame.pack(side=tk.LEFT, padx=20, pady=10)

        logo_label = tk.Label(
            logo_frame,
            text="🧠 StillMe",
            font=('Arial', 16, 'bold'),
            fg='#3B82F6',
            bg='#1E293B'
        )
        logo_label.pack(side=tk.LEFT)

        title_label = tk.Label(
            logo_frame,
            text="Personal AI Assistant",
            font=('Arial', 12),
            fg='#F8FAFC',
            bg='#1E293B'
        )
        title_label.pack(side=tk.LEFT, padx=(10, 0))

        # Founder mode indicator
        if self.founder_mode:
            founder_label = tk.Label(
                header_frame,
                text="👑 FOUNDER MODE",
                font=('Arial', 10, 'bold'),
                fg='#FFD700',
                bg='#1E293B'
            )
            founder_label.pack(side=tk.LEFT, padx=(20, 0), pady=10)

        # Control buttons
        controls_frame = tk.Frame(header_frame, bg='#1E293B')
        controls_frame.pack(side=tk.RIGHT, padx=20, pady=10)

        # Metrics button
        metrics_btn = tk.Button(
            controls_frame,
            text="📊 Metrics",
            command=self.show_metrics,
            bg='#3B82F6',
            fg='white',
            font=('Arial', 10),
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        metrics_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Founder console button
        founder_btn = tk.Button(
            controls_frame,
            text="👑 Founder",
            command=self.show_founder_console,
            bg='#FFD700',
            fg='black',
            font=('Arial', 10, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        founder_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Settings button
        settings_btn = tk.Button(
            controls_frame,
            text="⚙️ Settings",
            command=self.show_settings,
            bg='#6B7280',
            fg='white',
            font=('Arial', 10),
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        settings_btn.pack(side=tk.LEFT)

    def setup_chat_area(self, parent):
        """Setup chat messages area"""
        chat_frame = tk.Frame(parent, bg='#0F172A')
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Chat title
        chat_title = tk.Label(
            chat_frame,
            text="💬 Chat",
            font=('Arial', 14, 'bold'),
            fg='#F8FAFC',
            bg='#0F172A'
        )
        chat_title.pack(anchor=tk.W, pady=(0, 10))

        # Chat messages
        self.chat_text = scrolledtext.ScrolledText(
            chat_frame,
            bg='#1E293B',
            fg='#F8FAFC',
            font=('Arial', 11),
            wrap=tk.WORD,
            state=tk.DISABLED,
            padx=15,
            pady=10
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for styling
        self.chat_text.tag_configure("user", foreground="#3B82F6", font=('Arial', 11, 'bold'))
        self.chat_text.tag_configure("assistant", foreground="#10B981", font=('Arial', 11, 'bold'))
        self.chat_text.tag_configure("system", foreground="#F59E0B", font=('Arial', 10, 'italic'))
        self.chat_text.tag_configure("timestamp", foreground="#6B7280", font=('Arial', 9))
        self.chat_text.tag_configure("metadata", foreground="#9CA3AF", font=('Arial', 9))

    def setup_telemetry_panel(self, parent):
        """Setup telemetry panel"""
        telemetry_frame = tk.Frame(parent, bg='#1E293B', width=300)
        telemetry_frame.pack(side=tk.RIGHT, fill=tk.Y)
        telemetry_frame.pack_propagate(False)

        # Telemetry title
        telemetry_title = tk.Label(
            telemetry_frame,
            text="📊 Live Telemetry",
            font=('Arial', 12, 'bold'),
            fg='#F8FAFC',
            bg='#1E293B'
        )
        telemetry_title.pack(pady=15)

        # Telemetry content
        self.telemetry_text = scrolledtext.ScrolledText(
            telemetry_frame,
            bg='#334155',
            fg='#F8FAFC',
            font=('Consolas', 9),
            wrap=tk.WORD,
            state=tk.DISABLED,
            padx=10,
            pady=10
        )
        self.telemetry_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # Update telemetry display
        self.update_telemetry_display()

    def setup_input_area(self, parent):
        """Setup input area"""
        input_frame = tk.Frame(parent, bg='#1E293B', height=80)
        input_frame.pack(fill=tk.X, pady=(10, 0))
        input_frame.pack_propagate(False)

        # Input field
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            input_frame,
            textvariable=self.input_var,
            bg='#334155',
            fg='#F8FAFC',
            font=('Arial', 11),
            relief=tk.FLAT,
            insertbackground='#F8FAFC'
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
        self.input_entry.bind('<Return>', self.send_message)

        # Send button
        send_btn = tk.Button(
            input_frame,
            text="Send",
            command=self.send_message,
            bg='#3B82F6',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=15
        )
        send_btn.pack(side=tk.RIGHT, padx=(0, 15))

        # Quick actions button
        actions_btn = tk.Button(
            input_frame,
            text="⚡ Actions",
            command=self.show_quick_actions,
            bg='#6B7280',
            fg='white',
            font=('Arial', 10),
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        actions_btn.pack(side=tk.RIGHT, padx=(0, 10))

    def test_connection(self):
        """Test connection to server"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.add_system_message("✅ Connected to StillMe server")
            else:
                self.add_system_message("❌ Server connection failed")
        except Exception as e:
            self.add_system_message(f"❌ Connection error: {e}")

    def send_message(self, event=None):
        """Send message to server"""
        message = self.input_var.get().strip()
        if not message:
            return

        # Add user message to chat
        self.add_user_message(message)
        self.input_var.set("")

        # Send to server in background thread
        threading.Thread(target=self._send_to_server, args=(message,), daemon=True).start()

    def _send_to_server(self, message):
        """Send message to server (background thread)"""
        try:
            # Show typing indicator
            self.root.after(0, lambda: self.add_system_message("🤖 StillMe is typing..."))

            # Prepare request
            payload = {
                "message": message,
                "session_id": self.session_id,
                "metadata": {
                    "persona": "assistant",
                    "language": "vi",
                    "debug": True
                }
            }

            # Send request
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()

            if response.status_code == 200:
                data = response.json()
                latency_ms = int((end_time - start_time) * 1000)

                # Update telemetry
                self.update_telemetry(data, latency_ms)

                # Add assistant response
                self.root.after(0, lambda: self.add_assistant_message(data, latency_ms))
            else:
                self.root.after(0, lambda: self.add_system_message(f"❌ Server error: {response.status_code}"))

        except Exception as e:
            self.root.after(0, lambda err=e: self.add_system_message(f"❌ Error: {str(err)}"))

    def add_user_message(self, message):
        """Add user message to chat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.chat_text.insert(tk.END, "You: ", "user")
        self.chat_text.insert(tk.END, f"{message}\n\n")
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

        # Store message
        self.messages.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now()
        })

    def add_assistant_message(self, data, latency_ms):
        """Add assistant message to chat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        response_text = data.get('response', data.get('text', 'No response'))
        model = data.get('model', 'Unknown')

        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.chat_text.insert(tk.END, "StillMe: ", "assistant")
        self.chat_text.insert(tk.END, f"{response_text}\n")

        # Add metadata
        self.chat_text.insert(tk.END, f"  Model: {model} | Latency: {latency_ms}ms\n", "metadata")
        self.chat_text.insert(tk.END, "\n")
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

        # Store message
        self.messages.append({
            'role': 'assistant',
            'content': response_text,
            'model': model,
            'latency_ms': latency_ms,
            'timestamp': datetime.now()
        })

        # Update session metrics
        self.session_metrics['total_messages'] += 1
        if model:
            self.session_metrics['models_used'].add(model)
        self.session_metrics['average_latency'] = (
            (self.session_metrics['average_latency'] * (self.session_metrics['total_messages'] - 1) + latency_ms)
            / self.session_metrics['total_messages']
        )

    def add_system_message(self, message):
        """Add system message to chat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.chat_text.insert(tk.END, f"{message}\n", "system")
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    def update_telemetry(self, data, latency_ms):
        """Update telemetry data"""
        telemetry = {
            'timestamp': datetime.now(),
            'model': data.get('model', 'Unknown'),
            'latency_ms': latency_ms,
            'usage': data.get('usage', {}),
            'cost_estimate': data.get('cost_estimate_usd', 0.0),
            'routing': data.get('routing', {}),
            'safety': data.get('safety', {})
        }

        self.telemetry_data.append(telemetry)

        # Update session metrics
        usage = telemetry.get('usage', {})
        if usage:
            self.session_metrics['total_tokens'] += usage.get('total_tokens', 0)
        self.session_metrics['total_cost'] += telemetry.get('cost_estimate', 0.0)

        # Update display
        self.root.after(0, self.update_telemetry_display)

    def update_telemetry_display(self):
        """Update telemetry display"""
        if not self.telemetry_data:
            return

        self.telemetry_text.config(state=tk.NORMAL)
        self.telemetry_text.delete(1.0, tk.END)

        # Current session metrics
        self.telemetry_text.insert(tk.END, "📊 SESSION METRICS\n")
        self.telemetry_text.insert(tk.END, f"Messages: {self.session_metrics['total_messages']}\n")
        self.telemetry_text.insert(tk.END, f"Tokens: {self.session_metrics['total_tokens']}\n")
        self.telemetry_text.insert(tk.END, f"Cost: ${self.session_metrics['total_cost']:.4f}\n")
        self.telemetry_text.insert(tk.END, f"Avg Latency: {self.session_metrics['average_latency']:.0f}ms\n")
        self.telemetry_text.insert(tk.END, f"Models: {', '.join(self.session_metrics['models_used'])}\n")
        self.telemetry_text.insert(tk.END, "\n")

        # Recent telemetry
        self.telemetry_text.insert(tk.END, "🔄 RECENT REQUESTS\n")
        for telemetry in self.telemetry_data[-5:]:  # Last 5 requests
            timestamp = telemetry['timestamp'].strftime("%H:%M:%S")
            model = telemetry['model']
            latency = telemetry['latency_ms']
            tokens = telemetry['usage'].get('total_tokens', 0)
            cost = telemetry['cost_estimate']

            self.telemetry_text.insert(tk.END, f"[{timestamp}] {model}\n")
            self.telemetry_text.insert(tk.END, f"  Latency: {latency}ms | Tokens: {tokens} | Cost: ${cost:.4f}\n")

        self.telemetry_text.config(state=tk.DISABLED)

    def show_metrics(self):
        """Show detailed metrics window"""
        metrics_window = tk.Toplevel(self.root)
        metrics_window.title("StillMe Metrics")
        metrics_window.geometry("600x400")
        metrics_window.configure(bg='#0F172A')

        # Metrics content
        metrics_text = scrolledtext.ScrolledText(
            metrics_window,
            bg='#1E293B',
            fg='#F8FAFC',
            font=('Consolas', 10),
            wrap=tk.WORD
        )
        metrics_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Generate metrics report
        report = self.generate_metrics_report()
        metrics_text.insert(tk.END, report)
        metrics_text.config(state=tk.DISABLED)

    def generate_metrics_report(self):
        """Generate detailed metrics report"""
        report = "📊 STILLME METRICS REPORT\n"
        report += "=" * 50 + "\n\n"

        # Session info
        session_duration = datetime.now() - self.session_metrics['session_start']
        report += f"🕐 Session Duration: {session_duration}\n"
        report += f"📝 Total Messages: {self.session_metrics['total_messages']}\n"
        report += f"🔤 Total Tokens: {self.session_metrics['total_tokens']}\n"
        report += f"💰 Total Cost: ${self.session_metrics['total_cost']:.4f}\n"
        report += f"⚡ Average Latency: {self.session_metrics['average_latency']:.0f}ms\n"
        report += f"🤖 Models Used: {', '.join(self.session_metrics['models_used'])}\n\n"

        # Performance metrics
        if self.telemetry_data:
            latencies = [t['latency_ms'] for t in self.telemetry_data]
            report += "📈 Performance Metrics:\n"
            report += f"  Min Latency: {min(latencies)}ms\n"
            report += f"  Max Latency: {max(latencies)}ms\n"
            report += f"  P50 Latency: {sorted(latencies)[len(latencies)//2]}ms\n"
            report += f"  P95 Latency: {sorted(latencies)[int(len(latencies)*0.95)]}ms\n\n"

        # Recent requests
        report += "🔄 Recent Requests:\n"
        for i, telemetry in enumerate(self.telemetry_data[-10:], 1):
            timestamp = telemetry['timestamp'].strftime("%H:%M:%S")
            model = telemetry['model']
            latency = telemetry['latency_ms']
            tokens = telemetry['usage'].get('total_tokens', 0)
            cost = telemetry['cost_estimate']

            report += f"  {i:2d}. [{timestamp}] {model}\n"
            report += f"      Latency: {latency}ms | Tokens: {tokens} | Cost: ${cost:.4f}\n"

        return report

    def show_founder_console(self):
        """Show founder console"""
        if not self.founder_mode:
            # Ask for passcode
            passcode = simpledialog.askstring("Founder Console", "Enter founder passcode:", show='*')
            if passcode != self.founder_passcode:
                messagebox.showerror("Access Denied", "Invalid passcode")
                return
            self.founder_mode = True

        # Create founder console window
        founder_window = tk.Toplevel(self.root)
        founder_window.title("StillMe Founder Console")
        founder_window.geometry("800x600")
        founder_window.configure(bg='#0F172A')

        # Founder console content
        founder_text = scrolledtext.ScrolledText(
            founder_window,
            bg='#1E293B',
            fg='#FFD700',
            font=('Consolas', 10),
            wrap=tk.WORD
        )
        founder_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Founder console content
        founder_content = self.generate_founder_console_content()
        founder_text.insert(tk.END, founder_content)
        founder_text.config(state=tk.DISABLED)

    def generate_founder_console_content(self):
        """Generate founder console content"""
        content = "👑 STILLME FOUNDER CONSOLE\n"
        content += "=" * 50 + "\n\n"

        content += "🔧 AgentDev Commands:\n"
        content += "  /agentdev run <task>     - Execute AgentDev task\n"
        content += "  /agentdev status         - Check AgentDev status\n"
        content += "  /agentdev model <name>   - Set model routing hint\n\n"

        content += "⚙️ System Switches:\n"
        content += f"  Auto-translate: {'ON' if True else 'OFF'}\n"
        content += f"  Safety Level: {'Strict' if False else 'Normal'}\n"
        content += "  Token Cap: 4000\n"
        content += "  Max Latency: 10s\n\n"

        content += "📊 Live Metrics:\n"
        content += f"  Model In-Use: {self.telemetry_data[-1]['model'] if self.telemetry_data else 'N/A'}\n"
        content += f"  Session Messages: {self.session_metrics['total_messages']}\n"
        content += f"  Session Tokens: {self.session_metrics['total_tokens']}\n"
        content += f"  Session Cost: ${self.session_metrics['total_cost']:.4f}\n"
        content += f"  Average Latency: {self.session_metrics['average_latency']:.0f}ms\n\n"

        content += "🌐 Server Status:\n"
        content += f"  Base URL: {self.base_url}\n"
        content += f"  Session ID: {self.session_id}\n"
        content += f"  Connection: {'✅ Active' if self.telemetry_data else '❓ Unknown'}\n\n"

        content += "💡 Quick Actions:\n"
        content += "  - Type '/persona <name>' to change persona\n"
        content += "  - Type '/translate' to toggle auto-translate\n"
        content += "  - Type '/clear' to clear chat history\n"
        content += "  - Type '/export' to export conversation\n"

        return content

    def show_settings(self):
        """Show settings window"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("StillMe Settings")
        settings_window.geometry("500x400")
        settings_window.configure(bg='#0F172A')

        # Settings content
        settings_frame = tk.Frame(settings_window, bg='#0F172A')
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Server settings
        server_frame = tk.LabelFrame(settings_frame, text="Server Settings", bg='#1E293B', fg='#F8FAFC')
        server_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(server_frame, text="Base URL:", bg='#1E293B', fg='#F8FAFC').pack(anchor=tk.W, padx=10, pady=5)
        url_entry = tk.Entry(server_frame, bg='#334155', fg='#F8FAFC', width=50)
        url_entry.insert(0, self.base_url)
        url_entry.pack(padx=10, pady=(0, 10))

        # Features
        features_frame = tk.LabelFrame(settings_frame, text="Features", bg='#1E293B', fg='#F8FAFC')
        features_frame.pack(fill=tk.X, pady=(0, 20))

        telemetry_var = tk.BooleanVar(value=self.telemetry_enabled)
        tk.Checkbutton(features_frame, text="Enable Telemetry", variable=telemetry_var, bg='#1E293B', fg='#F8FAFC', selectcolor='#334155').pack(anchor=tk.W, padx=10, pady=5)

        # Buttons
        button_frame = tk.Frame(settings_frame, bg='#0F172A')
        button_frame.pack(fill=tk.X)

        tk.Button(button_frame, text="Save", command=lambda: self.save_settings(url_entry.get(), telemetry_var.get()), bg='#3B82F6', fg='white').pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(button_frame, text="Test Connection", command=self.test_connection, bg='#10B981', fg='white').pack(side=tk.LEFT)

    def save_settings(self, new_url, telemetry_enabled):
        """Save settings"""
        self.base_url = new_url
        self.telemetry_enabled = telemetry_enabled
        messagebox.showinfo("Settings", "Settings saved successfully!")

    def show_quick_actions(self):
        """Show quick actions menu"""
        actions_window = tk.Toplevel(self.root)
        actions_window.title("Quick Actions")
        actions_window.geometry("400x300")
        actions_window.configure(bg='#0F172A')

        # Quick actions
        actions = [
            ("🎭 Change Persona", "/persona assistant"),
            ("🌐 Toggle Translate", "/translate"),
            ("🔧 Dev Route", "/dev route"),
            ("🗑️ Clear Chat", "/clear"),
            ("📤 Export Chat", "/export"),
        ]

        for action_text, command in actions:
            btn = tk.Button(
                actions_window,
                text=action_text,
                command=lambda cmd=command: self.execute_quick_action(cmd, actions_window),
                bg='#3B82F6',
                fg='white',
                font=('Arial', 10),
                relief=tk.FLAT,
                padx=20,
                pady=10
            )
            btn.pack(fill=tk.X, padx=20, pady=5)

    def execute_quick_action(self, command, window):
        """Execute quick action command"""
        window.destroy()

        if command == "/clear":
            self.chat_text.config(state=tk.NORMAL)
            self.chat_text.delete(1.0, tk.END)
            self.chat_text.config(state=tk.DISABLED)
            self.messages.clear()
            self.telemetry_data.clear()
            self.session_metrics = {
                'total_messages': 0,
                'total_tokens': 0,
                'total_cost': 0.0,
                'average_latency': 0,
                'models_used': set(),
                'session_start': datetime.now()
            }
            self.add_system_message("Chat history cleared")
        elif command == "/export":
            self.export_chat()
        else:
            self.input_var.set(command)

    def export_chat(self):
        """Export chat to file"""
        try:
            filename = f"stillme_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'session_id': self.session_id,
                    'session_start': self.session_metrics['session_start'].isoformat(),
                    'messages': [
                        {
                            'role': msg['role'],
                            'content': msg['content'],
                            'timestamp': msg['timestamp'].isoformat(),
                            **{k: v for k, v in msg.items() if k not in ['role', 'content', 'timestamp']}
                        }
                        for msg in self.messages
                    ],
                    'session_metrics': {
                        **self.session_metrics,
                        'models_used': list(self.session_metrics['models_used']),
                        'session_start': self.session_metrics['session_start'].isoformat()
                    }
                }, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Export", f"Chat exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export chat: {e}")

    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = StillMeDesktopApp()
    app.run()
