"""
StillMe Community Dashboard - Hugging Face Spaces App
====================================================
Gradio app for Hugging Face Spaces deployment
"""

import gradio as gr
import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional

# Configuration
STILLME_API_URL = "https://your-stillme-server.com/api"  # Replace with your actual API URL
VOTE_THRESHOLD = 50

class StillMeDashboard:
    def __init__(self):
        self.user_id = f"user_{int(time.time())}"
        self.chat_history = []
        
    def get_learning_progress(self) -> str:
        """Get StillMe's learning progress"""
        try:
            response = requests.get(f"{STILLME_API_URL}/progress", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return f"""
                📚 **Current Lesson:** {data['current_lesson']}
                ✅ **Completed:** {data['completed_lessons']} lessons
                📊 **Total:** {data['total_lessons']} lessons
                🎯 **Progress:** {data['progress_percentage']}%
                """
            else:
                return "❌ Unable to load learning progress"
        except Exception as e:
            return f"❌ Error loading progress: {str(e)}"
    
    def get_lessons(self) -> str:
        """Get available lessons for voting"""
        try:
            response = requests.get(f"{STILLME_API_URL}/lessons", timeout=10)
            if response.status_code == 200:
                lessons = response.json()
                if not lessons:
                    return "📝 No lessons available for voting"
                
                lessons_text = "🗳️ **Vote for Next Lesson:**\n\n"
                for lesson in lessons:
                    status_icon = "✅" if lesson['status'] == 'completed' else "🔄" if lesson['status'] == 'learning' else "📝"
                    lessons_text += f"{status_icon} **{lesson['title']}**\n"
                    lessons_text += f"   📖 {lesson['description']}\n"
                    lessons_text += f"   🗳️ Votes: {lesson['votes']}/{VOTE_THRESHOLD}\n\n"
                
                return lessons_text
            else:
                return "❌ Unable to load lessons"
        except Exception as e:
            return f"❌ Error loading lessons: {str(e)}"
    
    def vote_for_lesson(self, lesson_id: int) -> str:
        """Vote for a lesson"""
        try:
            response = requests.post(
                f"{STILLME_API_URL}/vote",
                json={
                    "lesson_id": lesson_id,
                    "user_id": self.user_id
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'learning_started':
                    return f"🎉 {data['message']}"
                elif data['status'] == 'already_voted':
                    return f"⚠️ {data['message']}"
                else:
                    return f"✅ {data['message']}"
            else:
                return "❌ Failed to vote. Please try again."
        except Exception as e:
            return f"❌ Error voting: {str(e)}"
    
    def chat_with_stillme(self, message: str, history: List[List[str]]) -> tuple:
        """Chat with StillMe"""
        if not message.strip():
            return history, ""
        
        # Add user message to history
        history.append([message, None])
        
        try:
            response = requests.post(
                f"{STILLME_API_URL}/chat",
                json={
                    "message": message,
                    "user_id": self.user_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                stillme_response = data['response']
                model_info = f"🤖 Model: {data['model']} | ⚡ Latency: {data['latency']}s"
                
                # Update history with StillMe's response
                history[-1][1] = f"{stillme_response}\n\n---\n*{model_info}*"
                
                return history, ""
            else:
                history[-1][1] = "❌ Sorry, I encountered an error. Please try again."
                return history, ""
                
        except Exception as e:
            history[-1][1] = f"❌ Error: {str(e)}"
            return history, ""

# Initialize dashboard
dashboard = StillMeDashboard()

# Create Gradio interface
def create_dashboard():
    with gr.Blocks(
        title="StillMe Community Dashboard",
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="gray",
            neutral_hue="slate"
        ),
        css="""
        .gradio-container {
            max-width: 1200px !important;
            margin: 0 auto !important;
        }
        .progress-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 15px;
            color: white;
            margin-bottom: 20px;
        }
        .lessons-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        .chat-section {
            background: #ffffff;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #e0e0e0;
        }
        """
    ) as demo:
        
        gr.Markdown(
            """
            # 🤖 StillMe Community Dashboard
            
            Welcome to the StillMe Community Dashboard! Here you can:
            - 📚 Track StillMe's learning progress
            - 🗳️ Vote for lessons you want StillMe to learn
            - 💬 Chat with StillMe and see real-time model information
            
            ---
            """
        )
        
        with gr.Row():
            with gr.Column(scale=1):
                # Learning Progress Section
                gr.Markdown("### 📚 Learning Progress")
                progress_display = gr.Markdown(
                    value=dashboard.get_learning_progress(),
                    elem_classes=["progress-section"]
                )
                
                # Refresh Progress Button
                refresh_progress_btn = gr.Button("🔄 Refresh Progress", variant="secondary")
                
            with gr.Column(scale=1):
                # Lessons Section
                gr.Markdown("### 🗳️ Available Lessons")
                lessons_display = gr.Markdown(
                    value=dashboard.get_lessons(),
                    elem_classes=["lessons-section"]
                )
                
                # Refresh Lessons Button
                refresh_lessons_btn = gr.Button("🔄 Refresh Lessons", variant="secondary")
        
        # Chat Section
        gr.Markdown("### 💬 Chat with StillMe")
        
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    value=[[None, "👋 Hello! I'm StillMe, your AI companion. I'm currently learning and growing. How can I help you today?"]],
                    height=400,
                    show_label=False,
                    elem_classes=["chat-section"]
                )
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Ask StillMe anything...",
                        show_label=False,
                        scale=4
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
            
            with gr.Column(scale=1):
                # Model Information
                gr.Markdown("### 🤖 Model Info")
                model_info = gr.Markdown(
                    value="🤖 **Model:** deepseek-v3-0324\n⚡ **Status:** Ready\n🕒 **Last Update:** Just now",
                    elem_classes=["chat-section"]
                )
                
                # Quick Actions
                gr.Markdown("### ⚡ Quick Actions")
                quick_vote_btn = gr.Button("🗳️ Vote for AI Ethics", variant="secondary")
                quick_vote_btn2 = gr.Button("🗳️ Vote for ML Fundamentals", variant="secondary")
        
        # Event Handlers
        def refresh_progress():
            return dashboard.get_learning_progress()
        
        def refresh_lessons():
            return dashboard.get_lessons()
        
        def chat_handler(message, history):
            return dashboard.chat_with_stillme(message, history)
        
        def quick_vote_ai_ethics():
            return dashboard.vote_for_lesson(1)  # Assuming AI Ethics has ID 1
        
        def quick_vote_ml():
            return dashboard.vote_for_lesson(2)  # Assuming ML has ID 2
        
        # Connect events
        refresh_progress_btn.click(
            fn=refresh_progress,
            outputs=[progress_display]
        )
        
        refresh_lessons_btn.click(
            fn=refresh_lessons,
            outputs=[lessons_display]
        )
        
        send_btn.click(
            fn=chat_handler,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        )
        
        msg_input.submit(
            fn=chat_handler,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        )
        
        quick_vote_btn.click(
            fn=quick_vote_ai_ethics,
            outputs=[gr.Textbox(visible=False)]  # Hidden output for notifications
        )
        
        quick_vote_btn2.click(
            fn=quick_vote_ml,
            outputs=[gr.Textbox(visible=False)]  # Hidden output for notifications
        )
        
        # Footer
        gr.Markdown(
            """
            ---
            ### 📝 About StillMe
            
            StillMe is an AI companion created by Anh Nguyễn (Vietnamese) with major support from AI organizations such as OpenAI, Google, DeepSeek. 
            Its purpose is to accompany and befriend everyone.
            
            **🔗 Links:**
            - GitHub: [StillMe Repository](https://github.com/your-username/stillme)
            - Documentation: [StillMe Docs](https://docs.stillme.ai)
            - Community: [Discord Server](https://discord.gg/stillme)
            
            **⚡ Features:**
            - Community-driven learning through voting
            - Real-time chat with model information
            - Transparent learning progress tracking
            - Open source and community-focused
            """
        )
    
    return demo

# Create and launch the app
if __name__ == "__main__":
    demo = create_dashboard()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True
    )
