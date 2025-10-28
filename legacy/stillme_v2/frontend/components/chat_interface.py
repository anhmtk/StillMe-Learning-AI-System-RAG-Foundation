"""
Chat Interface Component
Provides chat interface with the AI system
"""

import streamlit as st
import time
from typing import Dict, Any, List
from datetime import datetime

def render_chat_interface(api_client):
    """Render chat interface with AI"""
    
    st.title("💬 Chat with Evolution AI")
    st.markdown("Interact with your evolving AI assistant")
    
    # Initialize chat history
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hello! I'm your Evolution AI assistant. How can I help you today?"}
        ]
    
    if 'waiting_for_response' not in st.session_state:
        st.session_state.waiting_for_response = False
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display evolution context for AI messages
            if message["role"] == "assistant" and message.get("evolution_context"):
                with st.expander("🧠 Evolution Context"):
                    st.json(message["evolution_context"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat history
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Call AI API
            ai_result = generate_ai_response(prompt, api_client)
            assistant_response = ai_result.get('response', 'No response')
            
            # Simulate streaming response
            for chunk in assistant_response.split():
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # Display metadata
            if 'model' in ai_result and 'latency_ms' in ai_result:
                st.caption(f"🤖 Model: {ai_result['model']} | ⏱️ Latency: {ai_result['latency_ms']}ms | 🔢 Tokens: {ai_result.get('tokens_used', 0)}")
            
            # Add evolution context
            evolution_context = get_evolution_context(api_client)
            with st.expander("🧠 Evolution Context"):
                st.json(evolution_context)
        
        # Add assistant response to chat history
        st.session_state.chat_messages.append({
            "role": "assistant", 
            "content": full_response,
            "evolution_context": evolution_context,
            "metadata": {
                "model": ai_result.get('model', 'unknown'),
                "latency_ms": ai_result.get('latency_ms', 0),
                "tokens_used": ai_result.get('tokens_used', 0)
            }
        })
    
    # Chat controls sidebar
    with st.sidebar:
        st.subheader("Chat Settings")
        
        # Clear chat history
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_messages = [
                {"role": "assistant", "content": "Hello! I'm your Evolution AI assistant. How can I help you today?"}
            ]
            st.rerun()
        
        # Export chat history
        if st.button("📤 Export Chat"):
            export_chat_history()
        
        st.markdown("---")
        st.subheader("AI Context")
        
        # Display current AI status
        try:
            status = api_client.get_evolution_status()
            if status:
                st.markdown(f"**Current Stage:** {status.get('current_stage', 'unknown').title()}")
                st.markdown(f"**Knowledge Items:** {status.get('total_knowledge_items', 0)}")
                st.markdown(f"**System Age:** {status.get('system_age_days', 0)} days")
        except Exception as e:
            st.error(f"Failed to load AI status: {str(e)}")

def generate_ai_response(prompt: str, api_client) -> dict:
    """Generate AI response based on user prompt"""
    
    try:
        # Call the actual Chat API
        response = api_client.send_chat_message(prompt)
        return response
    except Exception as e:
        st.error(f"Error calling AI API: {str(e)}")
        return {
            'response': "I apologize, but I'm having trouble connecting to the AI service right now. Please try again later.",
            'model': 'error',
            'latency_ms': 0,
            'tokens_used': 0
        }

def get_evolution_context(api_client) -> Dict[str, Any]:
    """Get current evolution context for the AI"""
    
    try:
        status = api_client.get_evolution_status()
        metrics = api_client.get_evolution_metrics()
        
        return {
            "current_stage": status.get('current_stage', 'unknown') if status else 'unknown',
            "system_age_days": status.get('system_age_days', 0) if status else 0,
            "total_knowledge": metrics.get('total_knowledge_items', 0) if metrics else 0,
            "success_rate": metrics.get('success_rate', 0) if metrics else 0,
            "learning_trend": metrics.get('learning_trend', 'unknown') if metrics else 'unknown',
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def export_chat_history():
    """Export chat history to a file"""
    
    chat_text = "Evolution AI Chat History\n"
    chat_text += "=" * 30 + "\n\n"
    
    for message in st.session_state.chat_messages:
        role = "User" if message["role"] == "user" else "AI Assistant"
        chat_text += f"{role}: {message['content']}\n"
        chat_text += "-" * 50 + "\n"
    
    # Create download button
    st.download_button(
        label="📥 Download Chat History",
        data=chat_text,
        file_name=f"evolution_ai_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )