import os
import time
from datetime import datetime
from typing import Any, Dict

import requests
import streamlit as st
import plotly.graph_objects as go

# Import floating chat widget
try:
    from frontend.components.floating_chat import render_floating_chat
    FLOATING_CHAT_AVAILABLE = True
except ImportError:
    FLOATING_CHAT_AVAILABLE = False


API_BASE = os.getenv("STILLME_API_BASE", "http://localhost:8000")


def get_json(path: str, default: Dict[str, Any] | None = None) -> Dict[str, Any]:
    url = f"{API_BASE}{path}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return default or {}


def page_overview():
    status = get_json("/api/status", {})
    rag_stats = get_json("/api/rag/stats", {}).get("stats", {})
    accuracy = get_json("/api/learning/accuracy_metrics", {}).get("metrics", {})
    
    # Get scheduler status
    scheduler_status = get_json("/api/learning/scheduler/status", {})

    # Display logo and title
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        try:
            st.image("assets/logo.png", width=80)
        except:
            st.markdown("🧠")  # Fallback emoji
    with col_title:
        st.markdown("# StillMe")
        st.caption("Self-Evolving AI System")
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Stage", status.get("stage", "Unknown"))
    with col2:
        st.metric("System Age (days)", status.get("system_age_days", 0))
    with col3:
        st.metric("Next Milestone", status.get("milestone_sessions", 100))
    with col4:
        st.metric(
            "Progress",
            f"{status.get('sessions_completed', 0)}/{status.get('milestone_sessions', 100)}",
        )

    st.markdown("### Evolution Progress")
    req = [100, 500, 1000, 5000]
    labels = ["Infant", "Child", "Adolescent", "Adult"]
    current = [
        min(status.get("sessions_completed", 0), req[0]),
        0,
        0,
        0,
    ]
    fig = go.Figure()
    fig.add_bar(name="Required Sessions", x=labels, y=req, marker_color="#8a8f98")
    fig.add_bar(name="Current Progress", x=labels, y=current, marker_color="#46b3ff")
    fig.update_layout(barmode="group", height=360, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Vector DB Stats")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Documents", rag_stats.get("total_documents", 0))
    with c2:
        st.metric("Knowledge Docs", rag_stats.get("knowledge_documents", 0))
    with c3:
        st.metric("Conversation Docs", rag_stats.get("conversation_documents", 0))

    st.markdown("### Learning Performance")
    avg_acc = accuracy.get("average_accuracy", 0.0)
    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=max(0.0, min(1.0, float(avg_acc))) * 100.0,
            number={"suffix": "%"},
            gauge={"axis": {"range": [0, 100]}},
            delta={"reference": 80},
            title={"text": "Success Rate (%)"},
        )
    )
    gauge.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(gauge, use_container_width=True)

    st.markdown("---")
    
    # Auto-Learning Status Section
    st.subheader("🤖 Auto-Learning Status")
    scheduler_status = get_json("/api/learning/scheduler/status", {})
    
    if scheduler_status.get("status") == "ok":
        is_running = scheduler_status.get("is_running", False)
        interval_hours = scheduler_status.get("interval_hours", 4)
        next_run = scheduler_status.get("next_run_time")
        
        col_status, col_info = st.columns([1, 2])
        with col_status:
            if is_running:
                st.success(f"🟢 **Running** (every {interval_hours}h)")
            else:
                st.warning("🟡 **Stopped**")
        with col_info:
            if next_run:
                st.caption(f"Next run: {next_run}")
            else:
                st.caption("Not scheduled")
        
        col_start, col_stop, col_run_now = st.columns(3)
        with col_start:
            if st.button("▶️ Start Scheduler", use_container_width=True):
                try:
                    r = requests.post(f"{API_BASE}/api/learning/scheduler/start", timeout=10)
                    if r.status_code == 200:
                        st.session_state["last_action"] = "✅ Scheduler started successfully!"
                        st.rerun()
                except Exception as e:
                    st.session_state["last_error"] = f"❌ Failed to start scheduler: {e}"
        with col_stop:
            if st.button("⏹️ Stop Scheduler", use_container_width=True):
                try:
                    r = requests.post(f"{API_BASE}/api/learning/scheduler/stop", timeout=10)
                    if r.status_code == 200:
                        st.session_state["last_action"] = "✅ Scheduler stopped successfully!"
                        st.rerun()
                except Exception as e:
                    st.session_state["last_error"] = f"❌ Failed to stop scheduler: {e}"
        with col_run_now:
            if st.button("🚀 Run Now", use_container_width=True):
                try:
                    with st.spinner("Running learning cycle..."):
                        r = requests.post(f"{API_BASE}/api/learning/scheduler/run-now", timeout=120)
                        if r.status_code == 200:
                            data = r.json()
                            entries = data.get("entries_fetched", 0)
                            added = data.get("entries_added_to_rag", 0)
                            st.session_state["last_action"] = f"✅ Learning cycle completed! Fetched {entries} entries, added {added} to RAG."
                            st.rerun()
                        else:
                            st.session_state["last_error"] = f"❌ Failed: {r.json().get('detail', 'Unknown error')}"
                except Exception as e:
                    st.session_state["last_error"] = f"❌ Failed: {e}"
    else:
        status_msg = scheduler_status.get("message", "Unknown error")
        init_error = scheduler_status.get("initialization_error")
        
        st.warning(f"⚠️ **Learning scheduler is not available**")
        
        # Show detailed error if available
        if init_error:
            with st.expander("🔍 View Initialization Error Details", expanded=False):
                st.code(init_error, language="text")
                st.caption("💡 This error occurred when the backend tried to initialize RAG components.")
        
        st.caption(f"**Reason:** {status_msg}")
        
        # Provide actionable tips and reset button
        col_tips, col_reset = st.columns([2, 1])
        with col_tips:
            st.info(
                "💡 **Troubleshooting Tips:**\n"
                "1. Check backend logs in Railway dashboard for detailed error messages\n"
                "2. Verify all dependencies are installed (chromadb, sentence-transformers, etc.)\n"
                "3. Check if data/vector_db directory has write permissions\n"
                "4. Try restarting the backend service"
            )
        with col_reset:
            st.warning("⚠️ **Quick Fix:**")
            if st.button("🔄 Reset Vector Database", use_container_width=True, type="secondary"):
                try:
                    with st.spinner("Resetting database (this may take a moment)..."):
                        r = requests.post(f"{API_BASE}/api/rag/reset-database", timeout=60)
                        if r.status_code == 200:
                            data = r.json()
                            message = data.get("message", "Database reset successfully")
                            if "restart" in message.lower():
                                st.session_state["last_action"] = "✅ Database directory deleted! Please restart backend service on Railway, then refresh this page."
                            else:
                                st.session_state["last_action"] = "✅ Database reset successfully!"
                            st.rerun()
                        else:
                            error_detail = r.json().get('detail', 'Unknown error') if r.status_code != 200 else 'Unknown error'
                            st.session_state["last_error"] = f"❌ Failed to reset database: {error_detail}"
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.session_state["last_error"] = f"❌ Connection error: {e}. Check if backend is running."
                    st.rerun()
                except Exception as e:
                    st.session_state["last_error"] = f"❌ Failed to reset database: {e}"
                    st.rerun()
            st.caption("⚠️ This will delete all vector data!")
            st.caption("💡 If reset fails, restart backend service on Railway")
    
    # Display persistent messages from last action
    if "last_action" in st.session_state:
        st.success(st.session_state["last_action"])
        # Keep message for one more rerun cycle
        if "msg_displayed" not in st.session_state:
            st.session_state["msg_displayed"] = True
        else:
            # Clear after showing once
            del st.session_state["last_action"]
            del st.session_state["msg_displayed"]
    
    if "last_error" in st.session_state:
        st.error(st.session_state["last_error"])
        # Keep error for one more rerun cycle
        if "error_displayed" not in st.session_state:
            st.session_state["error_displayed"] = True
        else:
            # Clear after showing once
            del st.session_state["last_error"]
            del st.session_state["error_displayed"]
    
    st.markdown("---")
    st.subheader("Quick Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Run Learning Session", use_container_width=True):
            try:
                r = requests.post(
                    f"{API_BASE}/api/learning/sessions/run",
                    json={
                        "prompt": "demo: quick session",
                        "response": "demo response",
                        "model_used": "deepseek-chat",
                    },
                    timeout=30,
                )
                if r.status_code == 200:
                    status = r.json().get("status", "Recorded")
                    st.session_state["last_action"] = f"✅ Learning session recorded successfully! Status: {status}"
                    st.rerun()
                else:
                    st.session_state["last_error"] = f"❌ Failed to record session: {r.json().get('detail', 'Unknown error')}"
            except Exception as e:
                st.session_state["last_error"] = f"❌ Learning session not recorded: {e}"
                st.rerun()
    
    with col2:
        if st.button("📊 Refresh Dashboard", use_container_width=True, help="Refresh all metrics and status (this will clear temporary messages)"):
            # Clear any temporary messages before rerun
            if "last_action" in st.session_state:
                del st.session_state["last_action"]
            if "last_error" in st.session_state:
                del st.session_state["last_error"]
            st.rerun()
    
    # Help text
    st.caption("💡 **Tip:** 'Run Learning Session' records a manual learning interaction. 'Refresh Dashboard' updates all displayed metrics.")


def page_rag():
    st.markdown("## Retrieval-Augmented Generation (RAG)")
    st.caption("Add knowledge and test retrieval context")

    with st.expander("Add Knowledge", expanded=True):
        content = st.text_area("Content", height=120)
        source = st.text_input("Source", value="manual")
        content_type = st.selectbox("Type", ["knowledge", "conversation"], index=0)
        if st.button("Add to Vector DB", type="primary"):
            try:
                r = requests.post(
                    f"{API_BASE}/api/rag/add_knowledge",
                    json={
                        "content": content,
                        "source": source,
                        "content_type": content_type,
                    },
                    timeout=60,
                )
                st.success(r.json().get("status", "Added"))
            except Exception as e:
                st.error(f"Failed: {e}")

    st.markdown("---")
    st.subheader("Query RAG")
    query = st.text_input("Your query", value="What is StillMe?")
    k_limit, c_limit = st.columns(2)
    with k_limit:
        knowledge_limit = st.number_input("Knowledge limit", 1, 10, 3)
    with c_limit:
        conversation_limit = st.number_input("Conversation limit", 0, 10, 2)
    if st.button("Retrieve Context"):
        try:
            r = requests.post(
                f"{API_BASE}/api/rag/query",
                json={
                    "query": query,
                    "knowledge_limit": int(knowledge_limit),
                    "conversation_limit": int(conversation_limit),
                },
                timeout=60,
            )
            data = r.json()
            st.success("Context retrieved")
            st.text_area("Context", data.get("context", ""), height=160)
        except Exception as e:
            st.error(f"Failed: {e}")


def page_learning():
    st.markdown("## Learning Sessions")
    st.caption("Record a learning session and score responses")

    prompt = st.text_area("Prompt", "Hello StillMe")
    response = st.text_area("Response", "This is a demo response")
    model_used = st.selectbox("Model", ["deepseek-chat", "ollama", "openai"], index=0)
    cols = st.columns(2)
    with cols[0]:
        if st.button("Record Session", type="primary"):
            try:
                r = requests.post(
                    f"{API_BASE}/api/learning/sessions/run",
                    json={
                        "prompt": prompt,
                        "response": response,
                        "model_used": model_used,
                    },
                    timeout=10,
                )
                st.success(r.json().get("status", "Recorded"))
            except Exception as e:
                st.error(f"Failed: {e}")
    with cols[1]:
        if st.button("Score Response"):
            try:
                r = requests.post(
                    f"{API_BASE}/api/learning/score_response",
                    json={
                        "prompt": prompt,
                        "response": response,
                        "model_used": model_used,
                    },
                    timeout=30,
                )
                data = r.json()
                st.success(f"Accuracy: {data.get('accuracy_score', 0):.3f}")
            except Exception as e:
                st.error(f"Failed: {e}")

    st.markdown("---")
    st.subheader("Current Metrics")
    metrics = get_json("/api/learning/accuracy_metrics", {}).get("metrics", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Responses", metrics.get("total_responses", 0))
    c2.metric("Average Accuracy", f"{metrics.get('average_accuracy', 0.0):.3f}")
    c3.metric("Trend", metrics.get("trend", "N/A"))


def page_community():
    st.markdown("## Community Proposals")
    st.caption("Propose learning sources, content, or improvements for StillMe")
    
    # Community Proposal Form
    with st.expander("📝 Propose a Learning Source", expanded=True):
        st.markdown("**Help StillMe learn by proposing new sources of knowledge!**")
        
        proposal_type = st.selectbox(
            "Proposal Type",
            ["RSS Feed", "Website/Article", "API Source", "Other"],
            help="What type of learning source are you proposing?"
        )
        
        source_url = st.text_input(
            "Source URL/Feed",
            placeholder="https://example.com/feed.xml or https://example.com/article",
            help="Enter the URL of the RSS feed, article, or API endpoint"
        )
        
        description = st.text_area(
            "Description",
            placeholder="Describe why this source would be valuable for StillMe to learn from...",
            height=100,
            help="Explain the value and relevance of this source"
        )
        
        your_name = st.text_input(
            "Your Name (Optional)",
            placeholder="Leave blank for anonymous",
            help="Optional: Your name or GitHub username"
        )
        
        if st.button("💡 Submit Proposal", type="primary", use_container_width=True):
            if source_url and description:
                try:
                    # For now, store in a simple way (can be enhanced with proper database later)
                    proposal_data = {
                        "type": proposal_type,
                        "url": source_url,
                        "description": description,
                        "proposer": your_name or "Anonymous",
                        "timestamp": datetime.now().isoformat(),
                        "status": "pending"
                    }
                    
                    # Try to add via RAG API as a proposal (if backend supports it)
                    # Or display success and store suggestion
                    st.success("✅ Proposal submitted! Thank you for contributing to StillMe's learning.")
                    st.info(
                        f"**Proposal Details:**\n"
                        f"- Type: {proposal_type}\n"
                        f"- URL: {source_url}\n"
                        f"- Status: Pending review\n\n"
                        f"*Note: Full proposal system with voting will be implemented in a future release.*"
                    )
                    
                    # In future, this could POST to /api/community/proposals endpoint
                    # For now, we'll show the proposal
                    
                except Exception as e:
                    st.error(f"Failed to submit proposal: {e}")
            else:
                st.warning("Please fill in both Source URL and Description.")
    
    st.markdown("---")
    
    # Community Voting Section (Coming Soon)
    st.subheader("🗳️ Community Voting (Coming Soon)")
    st.info(
        "Secure voting system with minimum votes, threshold, cooldown, and EthicsGuard will be available here. "
        "Community members will be able to vote on proposals and content quality."
    )
    
    if st.button("View Mock Vote", help="Placeholder button"):
        st.success("Thanks! Voting API will be wired in a next release.")


def sidebar(page_for_chat: str | None = None):
    st.sidebar.header("Dashboard")
    page = st.sidebar.selectbox(
        "Choose a page:", ["Overview", "RAG", "Learning", "Community"]
    )

    st.sidebar.success("Backend Connected")

    # Chat panel appears only on Overview
    if page == "Overview":
        # Chat mode selector (Sidebar or Floating Widget)
        chat_mode = st.sidebar.radio(
            "Chat Mode:",
            ["Sidebar Chat", "Floating Widget"],
            horizontal=True,
            help="Choose between sidebar chat or floating widget"
        )
        
        st.sidebar.markdown("---")
        
        # Initialize chat history in session state
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Render floating widget if selected and available
        if chat_mode == "Floating Widget" and FLOATING_CHAT_AVAILABLE:
            # Render floating chat widget
            render_floating_chat(
                chat_history=st.session_state.chat_history,
                api_base=API_BASE,
                is_open=True
            )
            
            # Note: Floating widget handles its own chat logic via JavaScript
            st.sidebar.info("💡 Floating chat widget is active. Use the chat button in the bottom-right corner.")
        
        # Sidebar chat (original implementation)
        elif chat_mode == "Sidebar Chat":
            st.sidebar.subheader("💬 Chat with StillMe")
            
            # Clear chat button (at top for easy access)
            if st.session_state.chat_history:
                if st.sidebar.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat"):
                    st.session_state.chat_history = []
                    st.rerun()
            
            # Display chat history in a larger, scrollable container
            if st.session_state.chat_history:
                # Use expander for better space management
                with st.sidebar.expander("📜 Chat History", expanded=True):
                    # Create chat messages with better styling
                    for idx, m in enumerate(st.session_state.chat_history[-20:]):  # Show last 20 messages
                        speaker = "You" if m["role"] == "user" else "StillMe"
                        speaker_color = "#46b3ff" if m["role"] == "user" else "#ffffff"
                        bg_color = "#1e3a5f" if m["role"] == "user" else "#262730"
                        align = "right" if m["role"] == "user" else "left"
                        
                        st.markdown(
                            f'<div style="margin-bottom: 12px; padding: 12px; background-color: {bg_color}; border-radius: 8px; text-align: {align}; max-width: 90%; margin-left: {"auto" if m["role"] == "user" else "0"}; margin-right: {"0" if m["role"] == "user" else "auto"};">'
                            f'<strong style="color: {speaker_color}; font-size: 0.9em;">{speaker}:</strong><br>'
                            f'<span style="color: #ffffff; font-size: 0.95em;">{m["content"]}</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
            
            st.sidebar.markdown("---")
            
            # Use form for Enter key support
            with st.sidebar.form(key="chat_form", clear_on_submit=True):
                user_msg = st.text_area(
                    "Your message", 
                    height=100,
                    key="chat_input_form",
                    placeholder="Type your message and press Enter (Shift+Enter for new line)...",
                    help="Press Enter to send, Shift+Enter for new line"
                )
                
                send_button = st.form_submit_button("💬 Send", use_container_width=True)
            
            # Refresh button outside form (can't have multiple submit buttons in form)
            if st.sidebar.button("🔄 Refresh", use_container_width=True, key="refresh_chat"):
                st.rerun()
            
            # Process message when form is submitted
            if send_button and user_msg and user_msg.strip():
                # Store message before clearing
                message_to_send = user_msg.strip()
                
                # Add user message to history
                st.session_state.chat_history.append({"role": "user", "content": message_to_send})
                
                # Show loading status (using status instead of spinner in sidebar)
                status_placeholder = st.sidebar.empty()
                status_placeholder.info("🤔 StillMe is thinking...")
                
                try:
                    r = requests.post(
                        f"{API_BASE}/api/chat/smart_router",
                        json={"message": message_to_send},
                        timeout=30,
                    )
                    r.raise_for_status()
                    data = r.json()
                    # Extract response from ChatResponse model
                    reply = data.get("response") or data.get("message") or str(data)
                    if isinstance(reply, dict):
                        reply = reply.get("detail", str(reply))
                    
                    status_placeholder.success("✅ Response received!")
                except requests.exceptions.RequestException as e:
                    reply = f"❌ Error connecting to backend: {str(e)}"
                    status_placeholder.error("❌ Connection error")
                except Exception as e:
                    reply = f"❌ Error: {str(e)}"
                    status_placeholder.error("❌ Error occurred")
                
                # Add assistant response to history
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                
                # Clear status and rerun to show new message
                status_placeholder.empty()
                st.rerun()
    
    return page


def main():
    st.set_page_config(
        page_title="StillMe", 
        page_icon="🧠", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    page = sidebar()

    if page == "Overview":
        page_overview()
    elif page == "RAG":
        page_rag()
    elif page == "Learning":
        page_learning()
    elif page == "Community":
        page_community()

    # Tiny auto-refresh toggle for live demos
    with st.sidebar.expander("Auto Refresh"):
        enabled = st.checkbox("Always rerun", value=False)
        interval = st.slider("Seconds", 5, 60, 15)
        if enabled:
            time.sleep(interval)
            st.rerun()


if __name__ == "__main__":
    main()


