"""
Floating Chat Widget Component for Streamlit
Creates a floating chat panel that occupies ~1/3 of screen width when opened.
"""
import streamlit.components.v1 as components
import json

def render_floating_chat(chat_history: list, api_base: str, is_open: bool = False):
    """
    Render a floating chat widget using HTML/CSS/JS.
    
    Args:
        chat_history: List of chat messages in format [{"role": "user|assistant", "content": "..."}]
        api_base: Base URL for the API
        is_open: Whether the chat panel should be open by default
    
    Returns:
        Component instance
    """
    
    # Prepare chat history for JavaScript
    chat_history_json = json.dumps(chat_history)
    
    # HTML/CSS/JS for floating chat widget
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            #stillme-chat-widget {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }}
            
            #stillme-chat-button {{
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, #46b3ff 0%, #1e90ff 100%);
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(70, 179, 255, 0.4);
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            
            #stillme-chat-button:hover {{
                transform: scale(1.1);
                box-shadow: 0 6px 16px rgba(70, 179, 255, 0.6);
            }}
            
            #stillme-chat-panel {{
                position: fixed;
                bottom: 90px;
                right: 20px;
                width: 33vw;
                min-width: 350px;
                max-width: 500px;
                height: 70vh;
                min-height: 400px;
                max-height: 700px;
                background: #0e1117;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                display: {'flex' if is_open else 'none'};
                flex-direction: column;
                border: 1px solid #262730;
                overflow: hidden;
            }}
            
            .stillme-chat-header {{
                background: #262730;
                padding: 16px 20px;
                border-bottom: 1px solid #3a3d47;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .stillme-chat-header h3 {{
                margin: 0;
                color: #46b3ff;
                font-size: 18px;
                font-weight: 600;
            }}
            
            .stillme-chat-close {{
                background: none;
                border: none;
                color: #ffffff;
                font-size: 24px;
                cursor: pointer;
                padding: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                transition: background 0.2s;
            }}
            
            .stillme-chat-close:hover {{
                background: #3a3d47;
            }}
            
            .stillme-chat-messages {{
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}
            
            .stillme-chat-message {{
                padding: 12px 16px;
                border-radius: 8px;
                max-width: 80%;
                word-wrap: break-word;
            }}
            
            .stillme-chat-message.user {{
                background: #46b3ff;
                color: white;
                align-self: flex-end;
                margin-left: auto;
            }}
            
            .stillme-chat-message.assistant {{
                background: #262730;
                color: #ffffff;
                align-self: flex-start;
            }}
            
            .stillme-chat-input-container {{
                padding: 16px 20px;
                border-top: 1px solid #262730;
                background: #0e1117;
            }}
            
            .stillme-chat-input-wrapper {{
                display: flex;
                gap: 8px;
            }}
            
            #stillme-chat-input {{
                flex: 1;
                padding: 12px 16px;
                background: #262730;
                border: 1px solid #3a3d47;
                border-radius: 8px;
                color: #ffffff;
                font-size: 14px;
                font-family: inherit;
                resize: none;
            }}
            
            #stillme-chat-input:focus {{
                outline: none;
                border-color: #46b3ff;
            }}
            
            #stillme-chat-send {{
                padding: 12px 24px;
                background: #46b3ff;
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.2s;
            }}
            
            #stillme-chat-send:hover {{
                background: #1e90ff;
            }}
            
            #stillme-chat-send:disabled {{
                background: #3a3d47;
                cursor: not-allowed;
            }}
            
            /* Scrollbar styling */
            .stillme-chat-messages::-webkit-scrollbar {{
                width: 6px;
            }}
            
            .stillme-chat-messages::-webkit-scrollbar-track {{
                background: #0e1117;
            }}
            
            .stillme-chat-messages::-webkit-scrollbar-thumb {{
                background: #262730;
                border-radius: 3px;
            }}
            
            .stillme-chat-messages::-webkit-scrollbar-thumb:hover {{
                background: #3a3d47;
            }}
        </style>
    </head>
    <body>
        <div id="stillme-chat-widget">
            <div id="stillme-chat-panel">
                <div class="stillme-chat-header">
                    <h3>💬 Chat with StillMe</h3>
                    <button class="stillme-chat-close" onclick="toggleChat()">×</button>
                </div>
                <div class="stillme-chat-messages" id="stillme-chat-messages">
                    <!-- Messages will be rendered here -->
                </div>
                <div class="stillme-chat-input-container">
                    <div class="stillme-chat-input-wrapper">
                        <textarea 
                            id="stillme-chat-input" 
                            placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
                            rows="2"
                        ></textarea>
                        <button id="stillme-chat-send" onclick="sendMessage()">Send</button>
                    </div>
                </div>
            </div>
            <button id="stillme-chat-button" onclick="toggleChat()">💬</button>
        </div>
        
        <script>
            const API_BASE = '{api_base}';
            let chatHistory = {chat_history_json};
            let isOpen = {str(is_open).lower()};
            
            // Initialize chat panel visibility
            if (!isOpen) {{
                document.getElementById('stillme-chat-panel').style.display = 'none';
            }}
            
            // Render chat history
            function renderMessages() {{
                const messagesContainer = document.getElementById('stillme-chat-messages');
                messagesContainer.innerHTML = '';
                
                chatHistory.forEach(msg => {{
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `stillme-chat-message ${{msg.role}}`;
                    messageDiv.textContent = msg.content;
                    messagesContainer.appendChild(messageDiv);
                }});
                
                // Scroll to bottom
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }}
            
            // Toggle chat panel
            function toggleChat() {{
                const panel = document.getElementById('stillme-chat-panel');
                const isVisible = panel.style.display === 'flex';
                panel.style.display = isVisible ? 'none' : 'flex';
                
                if (!isVisible) {{
                    // Focus input when opening
                    setTimeout(() => {{
                        document.getElementById('stillme-chat-input').focus();
                    }}, 100);
                }}
            }}
            
            // Send message
            async function sendMessage() {{
                const input = document.getElementById('stillme-chat-input');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Disable send button
                const sendBtn = document.getElementById('stillme-chat-send');
                sendBtn.disabled = true;
                sendBtn.textContent = 'Sending...';
                
                // Add user message to history
                chatHistory.push({{ role: 'user', content: message }});
                renderMessages();
                
                // Clear input
                input.value = '';
                
                // Send to backend
                try {{
                    const response = await fetch(`${{API_BASE}}/api/chat/smart_router`, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ message: message }}),
                    }});
                    
                    const data = await response.json();
                    const reply = data.response || data.message || JSON.stringify(data);
                    
                    // Add assistant response
                    chatHistory.push({{ role: 'assistant', content: reply }});
                    renderMessages();
                    
                    // Send message to Streamlit parent
                    window.parent.postMessage({{
                        type: 'stillme_chat_message',
                        history: chatHistory
                    }}, '*');
                    
                }} catch (error) {{
                    chatHistory.push({{ 
                        role: 'assistant', 
                        content: `❌ Error: ${{error.message}}` 
                    }});
                    renderMessages();
                }} finally {{
                    sendBtn.disabled = false;
                    sendBtn.textContent = 'Send';
                    input.focus();
                }}
            }}
            
            // Handle Enter key (Enter to send, Shift+Enter for new line)
            document.getElementById('stillme-chat-input').addEventListener('keydown', (e) => {{
                if (e.key === 'Enter' && !e.shiftKey) {{
                    e.preventDefault();
                    sendMessage();
                }}
            }});
            
            // Initial render
            renderMessages();
        </script>
    </body>
    </html>
    """
    
    return components.html(html_content, height=0)

