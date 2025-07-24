#!/usr/bin/env python3
import os
import sys
from datetime import datetime

# Thêm màu cho terminal
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    print("⚠️  Chưa cài colorama. Hãy chạy: pip install colorama")
    sys.exit(1)

# Import ConversationalCore_v1
sys.path.append(os.path.dirname(__file__))  # Đảm bảo import từ project root
from modules.conversational_core_v1 import ConversationalCore

# Mock PersonaMorph để test nhanh
class MockPersonaEngine:
    def generate_response(self, user_input, history):
        # Giả lập phản hồi đơn giản
        return f"({len(history)}) Em trả lời: {user_input}"

def main():
    core = ConversationalCore(MockPersonaEngine(), max_history=5)
    print(Fore.CYAN + "🤖 [StillMe Chat] - ConversationalCore_v1")
    print(Fore.YELLOW + "Gõ 'exit' để thoát, 'history' để xem lịch sử.\n")

    while True:
        try:
            user_input = input(Fore.GREEN + "👤 A: " + Style.RESET_ALL).strip()
        except (KeyboardInterrupt, EOFError):
            print(Fore.CYAN + "\n🤖 E: Tạm biệt a!")
            break

        if user_input.lower() == "exit":
            print(Fore.CYAN + "🤖 E: Hẹn gặp lại a!")
            break
        elif user_input.lower() == "history":
            history = core.get_history()
            print(Fore.MAGENTA + "\n--- Lịch sử hội thoại ---")
            for msg in history:
                role = "👤 A" if msg["role"] == "user" else "🤖 E"
                print(f"{role}: {msg['content']}")
            print(Fore.MAGENTA + "-------------------------\n")
            continue

        # Gọi core để phản hồi
        response = core.respond(user_input)
        print(Fore.BLUE + "🤖 E: " + response)

if __name__ == "__main__":
    main()
