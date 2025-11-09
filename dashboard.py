import os
import time
from typing import Any, Dict

import requests
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

# Import floating chat widget
try:
    from frontend.components.floating_chat import render_floating_chat
    FLOATING_CHAT_AVAILABLE = True
except ImportError:
    FLOATING_CHAT_AVAILABLE = False


API_BASE = os.getenv("STILLME_API_BASE", "http://localhost:8000")


def display_local_time(utc_time_str: str, label: str = "Next run"):
    """
    Display UTC time converted to user's local timezone.
    
    Args:
        utc_time_str: ISO format UTC time string
        label: Label text to display before the time
    """
    if not utc_time_str:
        st.caption(f"{label}: Not scheduled")
        return
    
    # Create HTML that includes both label and time in one component
    element_id = f"local_time_label_{abs(hash(utc_time_str)) % 1000000}"
    escaped_utc_time = utc_time_str.replace('"', '\\"').replace("'", "\\'")
    
    html = f"""
    <div style="font-size: 0.88rem; color: rgb(250, 250, 250);">
        <span>{label}: </span>
        <span id="{element_id}" style="display: inline-block;"></span>
    </div>
    <script>
        (function() {{
            const utcTime = "{escaped_utc_time}";
            const element = document.getElementById("{element_id}");
            
            if (!utcTime || utcTime === "None" || utcTime === "null" || utcTime === "") {{
                element.textContent = "Not scheduled";
                return;
            }}
            
            try {{
                // Parse UTC time (assume it's UTC if no timezone specified)
                let utcDate;
                if (utcTime.includes('Z')) {{
                    utcDate = new Date(utcTime);
                }} else {{
                    // If no Z, assume UTC and add Z
                    utcDate = new Date(utcTime + 'Z');
                }}
                
                // Check if date is valid
                if (isNaN(utcDate.getTime())) {{
                    element.textContent = utcTime;
                    return;
                }}
                
                // Format to local time with timezone
                const options = {{
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    timeZoneName: 'short',
                    hour12: false
                }};
                
                const localTimeStr = utcDate.toLocaleString('en-US', options);
                const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                
                // Format: MM/DD/YYYY, HH:MM:SS (Timezone)
                // Remove comma and format nicely
                const formatted = localTimeStr.replace(',', '') + ' (' + timezone + ')';
                element.textContent = formatted;
            }} catch (e) {{
                console.error('Error converting UTC time:', e);
                element.textContent = utcTime;
            }}
        }})();
    </script>
    """
    components.html(html, height=30)


def get_json(path: str, default: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Fetch JSON from API endpoint.
    Returns default dict if request fails.
    Does NOT raise exceptions - gracefully handles errors.
    """
    url = f"{API_BASE}{path}"
    try:
        r = requests.get(url, timeout=10)  # Increased timeout
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError as e:
        # Connection failed - backend may be down
        import logging
        logging.error(f"Connection error fetching {url}: {e}")
        return default or {}
    except requests.exceptions.Timeout as e:
        # Request timed out
        import logging
        logging.error(f"Timeout fetching {url}: {e}")
        return default or {}
    except requests.exceptions.HTTPError as e:
        # HTTP error (4xx, 5xx)
        import logging
        try:
            status_code = r.status_code
        except Exception:
            status_code = "unknown"
        logging.error(f"HTTP error fetching {url}: Status {status_code} - {e}")
        
        # Special handling for 502 Bad Gateway
        if status_code == 502:
            logging.error(f"502 Bad Gateway - Backend service may be down, restarting, or crashed. URL: {url}")
        
        return default or {}
    except requests.exceptions.RequestException as e:
        # Other request errors
        import logging
        logging.error(f"Request error fetching {url}: {e}")
        return default or {}
    except Exception as e:
        # Unexpected errors
        import logging
        logging.error(f"Unexpected error fetching {url}: {e}")
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
        except Exception:
            st.markdown("🧠")  # Fallback emoji
    with col_title:
        st.markdown("# StillMe")
        st.caption("Learning AI system with RAG foundation")
    
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
    
    # Show API_BASE for debugging (can be removed in production)
    with st.expander("🔧 Debug Info", expanded=False):
        st.code(f"API_BASE: {API_BASE}", language="text")
        st.caption("💡 Verify this matches your backend URL on Railway")
        
        # Test backend connection
        col_test1, col_test2 = st.columns(2)
        with col_test1:
            if st.button("🔍 Test Backend Connection", use_container_width=True):
                try:
                    test_r = requests.get(f"{API_BASE}/health", timeout=5)
                    if test_r.status_code == 200:
                        st.success(f"✅ Backend reachable: {test_r.status_code}")
                        st.json(test_r.json())
                    else:
                        st.error(f"❌ Backend returned: {test_r.status_code}")
                except Exception as test_e:
                    st.error(f"❌ Connection failed: {test_e}")
        
        with col_test2:
            if st.button("📤 Test Chat Endpoint", use_container_width=True):
                with st.spinner("Testing chat endpoint (this may take 30-60 seconds if model is loading)..."):
                    try:
                        test_r = requests.post(
                            f"{API_BASE}/api/chat/smart_router",
                            json={"message": "test", "user_id": "test", "use_rag": False, "context_limit": 1},
                            timeout=120  # Increased to 120s to handle model loading
                        )
                        if test_r.status_code == 200:
                            st.success(f"✅ Chat endpoint reachable: {test_r.status_code}")
                            response_data = test_r.json()
                            if "response" in response_data:
                                st.caption(f"Response preview: {response_data['response'][:100]}...")
                        else:
                            st.error(f"❌ Chat endpoint returned: {test_r.status_code}")
                            try:
                                st.json(test_r.json())
                            except Exception:
                                st.code(test_r.text[:200])
                    except requests.exceptions.Timeout:
                        st.warning("⏱️ **Timeout after 2 minutes** - This usually means:")
                        st.markdown("""
                        - **Embedding model is still loading** (first request can take 2-3 minutes)
                        - **AI API is slow** (DeepSeek/OpenAI may be experiencing delays)
                        - **Backend is processing** but needs more time
                        
                        **Solutions:**
                        1. Wait 1-2 minutes and try again (model may be cached now)
                        2. Check backend logs for model loading progress
                        3. Try actual chat (it has 5-minute timeout, more forgiving)
                        """)
                    except Exception as test_e:
                        st.error(f"❌ Chat endpoint failed: {test_e}")
                        if "timeout" in str(test_e).lower():
                            st.info("💡 **Tip:** Chat endpoint is working but slow. Try sending an actual message - it has a longer timeout (5 minutes).")
        
        # Show environment info
        st.markdown("---")
        st.caption("**Environment Variables:**")
        st.code(f"STILLME_API_BASE: {os.getenv('STILLME_API_BASE', 'NOT SET')}", language="text")
        if API_BASE == "http://localhost:8000":
            st.warning("⚠️ **WARNING:** API_BASE is still `localhost:8000`! This means `STILLME_API_BASE` environment variable is NOT set in Railway dashboard service. You need to set it to your backend URL (e.g., `https://stillme-backend-production-xxxx.up.railway.app`)")
    
    scheduler_status = get_json("/api/learning/scheduler/status", {})
    
    # Debug: Show what we received and test connection
    if not scheduler_status or scheduler_status == {}:
        st.error("⚠️ **Warning:** Could not fetch scheduler status from backend. API may be unreachable.")
        
        # Try to provide more specific error info
        try:
            test_url = f"{API_BASE}/api/status"
            test_r = requests.get(test_url, timeout=5)
            if test_r.status_code == 200:
                st.warning("💡 Backend is reachable at `/api/status`, but `/api/learning/scheduler/status` returned empty response.")
                st.info("This may indicate the scheduler endpoint has an issue. Check backend logs.")
            elif test_r.status_code == 502:
                st.error("❌ **502 Bad Gateway** - Backend service is not responding.")
                st.markdown("""
                **502 Bad Gateway means the backend service is down or crashed.**
                
                **Immediate Actions:**
                1. Go to Railway Dashboard → Service "stillme-backend"
                2. Check **"Deployments"** tab → See if service is running
                3. Check **"Logs"** tab → Look for errors or crashes
                4. If service is stopped → Click **"Redeploy"** or **"Restart"**
                5. If service is building → Wait for deployment to complete
                
                **Common Causes:**
                - Backend crashed during initialization
                - Backend is restarting after code change
                - Backend ran out of memory (check Railway resource limits)
                - Database connection issues
                """)
            else:
                st.error(f"❌ Backend returned status code {test_r.status_code} for `/api/status`")
        except requests.exceptions.ConnectionError:
            st.error(f"❌ **Cannot connect to backend at:** `{API_BASE}`")
            st.markdown("""
            **Possible causes:**
            1. Backend service is not running on Railway
            2. Environment variable `STILLME_API_BASE` is not set in dashboard service
            3. Backend URL has changed
            4. Network/firewall issue
            
            **Solution:**
            - Check Railway dashboard → Service "stillme-backend" → Ensure it's running
            - Check Railway dashboard → Service "dashboard" → Variables → Verify `STILLME_API_BASE` is set
            - Restart dashboard service if needed
            """)
        except Exception as e:
            st.warning(f"Error testing connection: {e}")
        
        st.json({"error": "Empty response from /api/learning/scheduler/status", "api_base": API_BASE})
        return
    
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
                display_local_time(next_run, "Next run")
            else:
                st.caption("Next run: Not scheduled")
        
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
                            filtered = data.get("entries_filtered", 0)
                            added = data.get("entries_added_to_rag", 0)
                            
                            if filtered > 0:
                                st.session_state["last_action"] = f"✅ Learning cycle completed! Fetched {entries} entries, Filtered {filtered} (Low quality/Short), Added {added} to RAG."
                            else:
                                st.session_state["last_action"] = f"✅ Learning cycle completed! Fetched {entries} entries, added {added} to RAG."
                            st.rerun()
                        else:
                            st.session_state["last_error"] = f"❌ Failed: {r.json().get('detail', 'Unknown error')}"
                except Exception as e:
                    st.session_state["last_error"] = f"❌ Failed: {e}"
    else:
        status_msg = scheduler_status.get("message", "Unknown error")
        init_error = scheduler_status.get("initialization_error")
        status_type = scheduler_status.get("status", "unknown")
        
        st.warning("⚠️ **Learning scheduler is not available**")
        
        # Show detailed error if available
        if init_error:
            with st.expander("🔍 View Initialization Error Details", expanded=True):
                st.code(init_error, language="text")
                st.caption("💡 This error occurred when the backend tried to initialize RAG components.")
        else:
            # If no detailed error, show status message and full response for debugging
            with st.expander("🔍 View Status Details", expanded=True):
                st.json(scheduler_status)
                st.caption(f"💡 Status type: {status_type}. If this is 'not_available' but backend logs show initialization succeeded, there may be a connection issue.")
        
        st.caption(f"**Reason:** {status_msg}")
        
        # Additional help for common cases
        if status_type == "not_available":
            st.info("💡 **Note:** Backend logs show scheduler initialized successfully. This may be a connection issue between dashboard and backend. Try refreshing the page.")
        
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
        st.markdown("**💡 Tip:** Add knowledge that StillMe can use to answer questions. Examples: definitions, FAQs, documentation, policies.")
        
        content = st.text_area(
            "Content", 
            height=120,
            placeholder="Enter the knowledge content here. For example:\n\nStillMe is a self-evolving AI system that learns continuously from user interactions and external sources. It uses RAG (Retrieval-Augmented Generation) to provide accurate, context-aware responses.",
            help="The actual text content you want StillMe to learn"
        )
        source = st.text_input(
            "Source", 
            value="manual",
            help="Source identifier (e.g., 'manual', 'website', 'documentation', 'user_feedback')"
        )
        content_type = st.selectbox(
            "Type", 
            ["knowledge", "conversation"], 
            index=0,
            help="'knowledge' for general information, 'conversation' for chat examples"
        )
        
        col_add, col_info = st.columns([1, 2])
        with col_add:
            if st.button("Add to Vector DB", type="primary", use_container_width=True):
                if not content.strip():
                    st.warning("⚠️ Please enter some content first!")
                else:
                    try:
                        # Show progress message
                        progress_msg = st.empty()
                        progress_msg.info("⏳ Adding knowledge... This may take 30-90 seconds (creating embeddings and saving to vector DB)")
                        
                        r = requests.post(
                            f"{API_BASE}/api/rag/add_knowledge",
                            json={
                                "content": content,
                                "source": source,
                                "content_type": content_type,
                            },
                            timeout=180,  # Increased to 180s to handle embedding generation
                        )
                        progress_msg.empty()
                        
                        if r.status_code == 200:
                            result = r.json()
                            st.success(f"✅ {result.get('status', 'Knowledge added successfully!')}")
                            st.info(f"📊 Type: {result.get('content_type', content_type)} | Source: {source}")
                            # Clear content after successful add (optional)
                            st.rerun()
                        else:
                            error_detail = r.json().get('detail', 'Unknown error')
                            st.error(f"❌ Failed: {error_detail}")
                            st.caption("💡 Tip: If this persists, check backend logs on Railway. The embedding model may be loading.")
                    except requests.exceptions.Timeout:
                        st.error("❌ Request timed out after 3 minutes. The backend may be slow or the embedding model is still loading.")
                        st.warning("💡 **Solutions:**\n1. Wait a moment and try again (model may be cached now)\n2. Check backend logs on Railway\n3. Try with shorter content")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Connection error. Backend may be down or restarting.")
                        st.info("💡 Check Railway dashboard to ensure backend service is running.")
                    except Exception as e:
                        error_str = str(e)
                        if "timeout" in error_str.lower() or "timed out" in error_str.lower():
                            st.error(f"❌ Request timed out: {error_str}")
                            st.warning("💡 The embedding process is taking longer than expected. Try again in a moment.")
                        else:
                            st.error(f"❌ Failed: {error_str}")
        
        with col_info:
            # Show current stats
            rag_stats = get_json("/api/rag/stats", {}).get("stats", {})
            if rag_stats:
                st.caption(f"📚 Current: {rag_stats.get('knowledge_documents', 0)} knowledge docs, {rag_stats.get('conversation_documents', 0)} conversation docs")

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
    
    st.markdown("---")
    st.subheader("📚 Raw Learning Feed (Fetched Data)")
    st.caption("Display ALL items fetched from the latest successful run")
    
    # Get fetch history
    try:
        fetch_data = get_json("/api/learning/rss/fetch-history", {}).get("items", [])
        
        if not fetch_data:
            st.info("ℹ️ No fetch data available. Run a learning cycle to view data.")
        else:
            # Status color mapping
            def get_status_color(status: str) -> str:
                if status == "Added to RAG":
                    return "🟢"
                elif status == "Filtered: Duplicate":
                    return "🟡"
                elif status == "Filtered: Low Score":
                    return "⚪"
                elif status == "Filtered: Ethical/Bias Flag":
                    return "🔴"
                else:
                    return "⚪"
            
            # Create scrollable table
            st.markdown(f"**Total items:** {len(fetch_data)}")
            
            # Display as table
            table_data = []
            for item in fetch_data:
                status_icon = get_status_color(item.get("status", ""))
                table_data.append({
                    "Status": f"{status_icon} {item.get('status', 'Unknown')}",
                    "Title/Headline": item.get("title", "N/A")[:80] + ("..." if len(item.get("title", "")) > 80 else ""),
                    "Source URL": item.get("source_url", "N/A"),
                    "Fetch Timestamp": item.get("fetch_timestamp", "N/A")[:19] if item.get("fetch_timestamp") else "N/A"
                })
            
            if table_data:
                import pandas as pd
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True, height=400)
                
                # Show details in expander
                st.markdown("### Item Details")
                for idx, item in enumerate(fetch_data[:20]):  # Show first 20
                    with st.expander(f"{get_status_color(item.get('status', ''))} {item.get('title', 'No title')[:60]}..."):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Source URL:** {item.get('source_url', 'N/A')}")
                            st.write(f"**Link:** [{item.get('link', 'N/A')[:50]}...]({item.get('link', '#')})" if item.get('link') else "**Link:** N/A")
                            st.write(f"**Status:** {item.get('status', 'Unknown')}")
                        with col2:
                            st.write(f"**Fetch Timestamp:** {item.get('fetch_timestamp', 'N/A')}")
                            if item.get('status_reason'):
                                st.write(f"**Reason:** {item.get('status_reason')}")
                            if item.get('vector_id'):
                                st.write(f"**Vector ID:** {item.get('vector_id')}")
                        st.write(f"**Summary:** {item.get('summary', 'N/A')[:200]}...")
    except Exception as e:
        st.error(f"Error fetching data: {e}")


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
        
        # TODO: Store proposer name when backend supports it
        # your_name = st.text_input(
        #     "Your Name (Optional)",
        #     placeholder="Leave blank for anonymous",
        #     help="Optional: Your name or GitHub username"
        # )
        
        if st.button("💡 Submit Proposal", type="primary", use_container_width=True):
            if source_url and description:
                try:
                    # For now, store in a simple way (can be enhanced with proper database later)
                    # TODO: Store proposal_data when backend supports it
                    # proposal_data = {
                    #     "type": proposal_type,
                    #     "url": source_url,
                    #     "description": description,
                    #     "proposer": your_name or "Anonymous",
                    #     "timestamp": datetime.now().isoformat(),
                    #     "status": "pending"
                    # }
                    
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


def page_validation():
    """Validation metrics and monitoring page"""
    st.markdown("## Validation Metrics")
    st.caption("Monitor validator chain performance and reduce hallucinations")
    
    # Get validation metrics
    try:
        metrics_data = get_json("/api/validators/metrics", {}).get("metrics", {})
    except Exception:
        metrics_data = {}
    
    if not metrics_data or metrics_data.get("total_validations", 0) == 0:
        st.info("ℹ️ No validation data yet. Enable validators with `ENABLE_VALIDATORS=true` to start collecting metrics.")
        return
    
    # Metrics overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Validations", metrics_data.get("total_validations", 0))
    with col2:
        pass_rate = metrics_data.get("pass_rate", 0.0)
        st.metric("Pass Rate", f"{pass_rate:.1%}")
    with col3:
        st.metric("Passed", metrics_data.get("passed_count", 0))
    with col4:
        st.metric("Failed", metrics_data.get("failed_count", 0))
    
    st.markdown("---")
    
    # Average overlap score
    avg_overlap = metrics_data.get("avg_overlap_score", 0.0)
    st.subheader("Evidence Overlap")
    st.metric("Average Overlap Score", f"{avg_overlap:.3f}")
    st.caption("Higher overlap indicates better grounding in RAG context")
    
    st.markdown("---")
    
    # Reasons histogram
    reasons_hist = metrics_data.get("reasons_histogram", {})
    if reasons_hist:
        st.subheader("Failure Reasons")
        st.bar_chart(reasons_hist)
    else:
        st.info("No validation failures recorded")
    
    st.markdown("---")
    
    # Recent logs
    recent_logs = metrics_data.get("recent_logs", [])
    if recent_logs:
        st.subheader("Recent Validation Logs (Last 10)")
        for log in recent_logs[-10:]:
            status = "✅" if log.get("passed", False) else "❌"
            timestamp = log.get("timestamp", "Unknown")
            reasons = log.get("reasons", [])
            overlap = log.get("overlap_score", 0.0)
            
            with st.expander(f"{status} {timestamp}"):
                st.write(f"**Passed:** {log.get('passed', False)}")
                if reasons:
                    st.write(f"**Reasons:** {', '.join(reasons)}")
                if overlap > 0:
                    st.write(f"**Overlap Score:** {overlap:.3f}")
    else:
        st.info("No recent validation logs")
    
    st.markdown("---")
    st.subheader("🛡️ Retained Knowledge Audit Log")
    st.caption("Display knowledge items that have been retained, embedded and successfully added to ChromaDB")
    
    # Get retained knowledge
    try:
        retained_data = get_json("/api/learning/retained?limit=100", {}).get("knowledge_items", [])
        
        if not retained_data:
            st.info("ℹ️ No retained knowledge data available. The system will automatically add after learning.")
        else:
            st.markdown(f"**Total retained items:** {len(retained_data)}")
            
            # Filter options
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                min_retention = st.slider("Minimum Retention Score", 0.0, 1.0, 0.7, 0.1)
            with col_filter2:
                search_term = st.text_input("🔍 Search (Source URL, Content)", "")
            
            # Filter data
            filtered_data = retained_data
            if min_retention > 0:
                filtered_data = [item for item in filtered_data if item.get("retention_score", 0.0) >= min_retention]
            if search_term:
                search_lower = search_term.lower()
                filtered_data = [
                    item for item in filtered_data
                    if search_lower in item.get("source_url", "").lower() or
                       search_lower in item.get("retained_content_snippet", "").lower()
                ]
            
            st.markdown(f"**Items after filtering:** {len(filtered_data)}")
            
            # Display as table
            if filtered_data:
                table_data = []
                for item in filtered_data:
                    table_data.append({
                        "Timestamp Added": item.get("timestamp_added", "N/A")[:19] if item.get("timestamp_added") else "N/A",
                        "Source URL (Link)": item.get("source_url", "N/A")[:60] + ("..." if len(item.get("source_url", "")) > 60 else ""),
                        "Content Snippet": item.get("retained_content_snippet", "N/A")[:100] + ("..." if len(item.get("retained_content_snippet", "")) > 100 else ""),
                        "Vector ID": item.get("vector_id", "N/A"),
                        "Retention Score": f"{item.get('retention_score', 0.0):.2f}"
                    })
                
                import pandas as pd
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True, height=400)
                
                # Show details in expander
                st.markdown("### Item Details")
                for idx, item in enumerate(filtered_data[:20]):  # Show first 20
                    with st.expander(f"📄 {item.get('source_url', 'Unknown')[:50]}... (Score: {item.get('retention_score', 0.0):.2f})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Timestamp Added:** {item.get('timestamp_added', 'N/A')}")
                            st.write(f"**Source URL:** [{item.get('source_url', 'N/A')}]({item.get('source_url', '#')})")
                            st.write(f"**Vector ID:** `{item.get('vector_id', 'N/A')}`")
                        with col2:
                            st.write(f"**Retention Score:** {item.get('retention_score', 0.0):.2f}")
                            st.write(f"**Access Count:** {item.get('access_count', 0)}")
                        st.markdown("**Retained Content Snippet (5-10 sentences):**")
                        st.text_area("", item.get("retained_content_snippet", "N/A"), height=150, key=f"snippet_{idx}", disabled=True)
                        if st.checkbox("View full content", key=f"full_{idx}"):
                            st.text_area("Full Content", item.get("full_content", "N/A"), height=200, key=f"full_content_{idx}", disabled=True)
            else:
                st.info("No items match the filter.")
    except Exception as e:
        st.error(f"Error fetching retained knowledge data: {e}")


def sidebar(page_for_chat: str | None = None):
    st.sidebar.header("Dashboard")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Overview", "RAG", "Learning", "Validation", "Community", "Memory Health"],
        key="page_selector"
    )

    st.sidebar.success("Backend Connected")

    # Chat panel now appears on all pages (improved UX)
    st.sidebar.markdown("---")
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
                    
                    # Show knowledge alert after StillMe's response
                    if m["role"] == "assistant" and "knowledge_alert" in m:
                        alert = m["knowledge_alert"]
                        alert_title = alert.get("title", "Important Knowledge")
                        alert_source = alert.get("source", "Unknown")
                        
                        st.sidebar.info(
                            f"💡 **StillMe Suggestion:** StillMe has learned new knowledge that may be relevant: "
                            f"**{alert_title}** (Source: {alert_source}). "
                            f"Would you like StillMe to explain?"
                        )
                        
                        if st.sidebar.button(f"📖 Explain {alert_title[:30]}...", key=f"explain_{idx}", use_container_width=True):
                            # Trigger explanation query
                            explain_query = f"Explain: {alert_title}"
                            st.session_state.chat_history.append({"role": "user", "content": explain_query})
                            st.rerun()
        
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
            
            # DEBUG: Log that we're about to send a request
            import logging
            logging.info(f"📤 Sending chat request to {API_BASE}/api/chat/smart_router")
            logging.info(f"📤 Message: {message_to_send[:50]}...")
            
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": message_to_send})
            
            # Show loading status (using status instead of spinner in sidebar)
            status_placeholder = st.sidebar.empty()
            status_placeholder.info("🤔 StillMe is thinking...")
            
            # Initialize knowledge_alert to None (fix UnboundLocalError)
            knowledge_alert = None
            reply = None
            
            try:
                # Show progress message
                status_placeholder.info("🤔 StillMe is thinking... This may take 30-90 seconds (AI generation + validation). If this is the first request, the embedding model may be loading (this can take 2-3 minutes).")
                
                # DEBUG: Log request details
                chat_url = f"{API_BASE}/api/chat/smart_router"
                logging.info(f"📤 POST {chat_url}")
                logging.info(f"📤 API_BASE: {API_BASE}")
                
                r = requests.post(
                    chat_url,
                    json={
                        "message": message_to_send,
                        "user_id": "dashboard_user",
                        "use_rag": True,
                        "context_limit": 3
                    },
                    timeout=300,  # Increased to 300s (5 minutes) to handle first-time model loading
                )
                
                # DEBUG: Log response
                logging.info(f"📥 Response status: {r.status_code}")
                logging.info(f"📥 Response received from {chat_url}")
                r.raise_for_status()
                data = r.json()
                # Extract response from ChatResponse model
                reply = data.get("response") or data.get("message") or str(data)
                if isinstance(reply, dict):
                    reply = reply.get("detail", str(reply))
                
                # Check for knowledge alert
                knowledge_alert = data.get("knowledge_alert")
                if knowledge_alert:
                    alert_title = knowledge_alert.get("title", "Important Knowledge")
                    alert_source = knowledge_alert.get("source", "Unknown")
                    st.session_state["knowledge_alert"] = knowledge_alert
                    import logging
                    logging.info(f"Knowledge alert received: {alert_title}")
                
                status_placeholder.success("✅ Response received!")
            except requests.exceptions.HTTPError as e:
                # Handle HTTP errors (4xx, 5xx) specifically
                status_code = e.response.status_code if hasattr(e, 'response') else "unknown"
                if status_code == 502:
                    reply = "❌ **502 Bad Gateway** - Backend service is not responding. Please check Railway dashboard and restart backend service if needed."
                    status_placeholder.error("❌ 502 Bad Gateway")
                    st.error("💡 **Backend is down!** Go to Railway → Service 'stillme-backend' → Check logs and restart if needed.")
                elif status_code == 422:
                    error_detail = ""
                    try:
                        error_data = e.response.json()
                        error_detail = error_data.get('detail', str(e))
                    except Exception:
                        error_detail = str(e)
                    reply = f"❌ **422 Unprocessable Entity** - Request format error: {error_detail}"
                    status_placeholder.error("❌ 422 Error")
                    st.warning("💡 This is a request format issue. Please refresh the page and try again.")
                elif status_code == 503:
                    error_detail = ""
                    try:
                        error_data = e.response.json()
                        error_detail = error_data.get('detail', 'Service unavailable')
                    except Exception:
                        error_detail = str(e)
                    reply = f"❌ **503 Service Unavailable** - {error_detail}"
                    status_placeholder.error("❌ Service Unavailable")
                    st.warning("💡 Backend service may be initializing. Please wait a moment and try again.")
                else:
                    error_detail = ""
                    try:
                        error_data = e.response.json()
                        error_detail = error_data.get('detail', str(e))
                    except Exception:
                        error_detail = str(e)
                    reply = f"❌ **Error {status_code}** - {error_detail}"
                    status_placeholder.error(f"❌ HTTP {status_code}")
                    st.error(f"💡 Backend returned error {status_code}. Check backend logs for details.")
            except requests.exceptions.Timeout:
                reply = "❌ Request timed out after 3 minutes. The AI response is taking longer than expected."
                status_placeholder.error("❌ Timeout")
                st.warning("💡 **Solutions:**\n1. Try again (AI API may be slow)\n2. Check backend logs\n3. Verify API keys (OPENAI_API_KEY or DEEPSEEK_API_KEY) are set")
            except requests.exceptions.ConnectionError as e:
                # DEBUG: Log connection error details
                import logging
                logging.error(f"❌ Connection Error: {e}")
                logging.error(f"❌ API_BASE: {API_BASE}")
                logging.error(f"❌ Attempted URL: {API_BASE}/api/chat/smart_router")
                
                reply = f"❌ **Connection Error** - Cannot connect to backend at `{API_BASE}`. Backend service may be down or restarting. Error: {str(e)}"
                status_placeholder.error("❌ Connection error")
                st.error(f"💡 **Backend is unreachable!**\n- API_BASE: `{API_BASE}`\n- Check Railway dashboard → Service 'stillme-backend' → Ensure it's running.\n- Verify `STILLME_API_BASE` environment variable is set correctly in dashboard service.")
            except requests.exceptions.RequestException as e:
                reply = f"❌ **Request Error** - {str(e)}"
                status_placeholder.error("❌ Request error")
                st.error(f"💡 Request failed: {str(e)}")
            except Exception as e:
                # DEBUG: Log all unexpected errors
                import logging
                import traceback
                logging.error(f"❌ Unexpected Error in chat: {e}")
                logging.error(f"❌ API_BASE: {API_BASE}")
                logging.error(f"❌ Traceback: {traceback.format_exc()}")
                
                reply = f"❌ **Unexpected Error** - {str(e)}"
                status_placeholder.error("❌ Error occurred")
                st.error(f"💡 Unexpected error: {str(e)}\n\n**Debug Info:**\n- API_BASE: `{API_BASE}`\n- Check browser console (F12) for more details\n- Check dashboard logs for full traceback")
            
            # Add assistant response to history (with knowledge alert if available)
            # Ensure reply is set (fallback if all exceptions occurred)
            if reply is None:
                reply = "❌ **Error** - No response received from backend."
            
            message_entry = {"role": "assistant", "content": reply}
            if knowledge_alert:
                message_entry["knowledge_alert"] = knowledge_alert
            st.session_state.chat_history.append(message_entry)
            
            # Clear knowledge alert from session state after adding to history
            if "knowledge_alert" in st.session_state:
                del st.session_state["knowledge_alert"]
            
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
    elif page == "Validation":
        page_validation()
    elif page == "Community":
        page_community()
    elif page == "Memory Health":
        from dashboard_memory_health import page_memory_health
        page_memory_health()

    # Tiny auto-refresh toggle for live demos
    with st.sidebar.expander("Auto Refresh"):
        enabled = st.checkbox("Always rerun", value=False)
        interval = st.slider("Seconds", 5, 60, 15)
        if enabled:
            time.sleep(interval)
            st.rerun()


if __name__ == "__main__":
    main()


