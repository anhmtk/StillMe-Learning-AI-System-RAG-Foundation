import os
import time
import hashlib
from typing import Any, Dict

import requests
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd

# Import floating chat widget
try:
    from frontend.components.floating_chat import render_floating_chat
    FLOATING_CHAT_AVAILABLE = True
except ImportError:
    FLOATING_CHAT_AVAILABLE = False

# Import floating community panel
try:
    from frontend.components.floating_community_panel import render_floating_community_panel
    FLOATING_COMMUNITY_AVAILABLE = True
except ImportError:
    FLOATING_COMMUNITY_AVAILABLE = False

# Import chat history service
try:
    from backend.services.chat_history import ChatHistory
    CHAT_HISTORY_AVAILABLE = True
except ImportError:
    CHAT_HISTORY_AVAILABLE = False
    ChatHistory = None


API_BASE = os.getenv("STILLME_API_BASE", "http://localhost:8000")
STILLME_API_KEY = os.getenv("STILLME_API_KEY", "")


def get_api_headers() -> Dict[str, str]:
    """
    Get headers for API requests, including API key if available.
    
    Returns:
        Dictionary with headers including X-API-Key if STILLME_API_KEY is set
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    if STILLME_API_KEY:
        headers["X-API-Key"] = STILLME_API_KEY
    
    return headers


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


def get_json(path: str, default: Dict[str, Any] | None = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Fetch JSON from API endpoint.
    Returns default dict if request fails.
    Does NOT raise exceptions - gracefully handles errors.
    
    Args:
        path: API endpoint path
        default: Default value to return on error
        timeout: Request timeout in seconds (default: 10s)
    """
    url = f"{API_BASE}{path}"
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        result = r.json()
        # Ensure result is never None - return empty dict if None
        if result is None:
            return default or {}
        return result
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
    # Ensure time module is available (avoid UnboundLocalError from shadowing)
    import time as time_module
    status = get_json("/api/status", {})
    rag_stats = get_json("/api/rag/stats", {}).get("stats", {})
    accuracy = get_json("/api/learning/accuracy_metrics", {}).get("metrics", {})
    
    # Get scheduler status (with longer timeout - backend may be busy during learning cycle)
    try:
        scheduler_status = get_json("/api/learning/scheduler/status", {}, timeout=90)
    except requests.exceptions.Timeout:
        # Backend may be busy processing learning cycle - this is OK
        scheduler_status = {}

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
    st.plotly_chart(fig, width='stretch')

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
    st.plotly_chart(gauge, width='stretch')

    # Phase 3: Time-based Learning Analytics
    st.markdown("### 📈 Learning Metrics (Time-based Analytics)")
    try:
        # Get today's metrics
        today_metrics = get_json("/api/learning/metrics/daily", {}, timeout=10)
        
        if today_metrics and today_metrics.get("metrics"):
            metrics = today_metrics["metrics"]
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("📥 Entries Fetched", metrics.get("total_entries_fetched", 0))
            with col_m2:
                st.metric("✅ Entries Added", metrics.get("total_entries_added", 0))
            with col_m3:
                st.metric("🚫 Entries Filtered", metrics.get("total_entries_filtered", 0))
            with col_m4:
                filter_rate = metrics.get("filter_rate", 0.0)
                st.metric("📊 Filter Rate", f"{filter_rate}%")
            
            # Show filter reasons if available
            filter_reasons = metrics.get("filter_reasons", {})
            if filter_reasons:
                with st.expander("🔍 Filter Reasons Breakdown", expanded=False):
                    for reason, count in filter_reasons.items():
                        st.write(f"**{reason}**: {count}")
            
            # Show sources breakdown if available
            sources = metrics.get("sources", {})
            if sources:
                with st.expander("📚 Sources Breakdown", expanded=False):
                    for source, count in sources.items():
                        st.write(f"**{source.replace('_', ' ').title()}**: {count}")
            
            # Show learning cycles for today
            cycles = metrics.get("cycles", [])
            if cycles:
                st.caption(f"📅 Today ({today_metrics.get('date', 'N/A')}): {metrics.get('total_cycles', 0)} learning cycle(s)")
        else:
            st.info("📊 No learning metrics available for today yet. Metrics will appear after the first learning cycle completes.")
            
        # Get summary metrics
        summary = get_json("/api/learning/metrics/summary", {}, timeout=10)
        if summary and summary.get("summary"):
            summary_data = summary["summary"]
            if summary_data.get("total_cycles", 0) > 0:
                with st.expander("📊 Overall Learning Summary", expanded=False):
                    col_s1, col_s2, col_s3 = st.columns(3)
                    with col_s1:
                        st.metric("Total Cycles", summary_data.get("total_cycles", 0))
                    with col_s2:
                        st.metric("Total Fetched", summary_data.get("total_entries_fetched", 0))
                    with col_s3:
                        st.metric("Total Added", summary_data.get("total_entries_added", 0))
                    st.caption(f"Filter Rate: {summary_data.get('filter_rate', 0.0)}% | Add Rate: {summary_data.get('add_rate', 0.0)}%")
    except Exception as e:
        st.caption(f"💡 Learning metrics will be available after the first learning cycle completes. (Error: {str(e)})")

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
            if st.button("🔍 Test Backend Connection", width='stretch'):
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
            if st.button("📤 Test Chat Endpoint", width='stretch'):
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
        st.code(f"STILLME_API_KEY: {'SET (length: ' + str(len(STILLME_API_KEY)) + ')' if STILLME_API_KEY else 'NOT SET'}", language="text")
        if API_BASE == "http://localhost:8000":
            st.warning("⚠️ **WARNING:** API_BASE is still `localhost:8000`! This means `STILLME_API_BASE` environment variable is NOT set in Railway dashboard service. You need to set it to your backend URL (e.g., `https://stillme-backend-production-xxxx.up.railway.app`)")
        if not STILLME_API_KEY:
            st.error("❌ **CRITICAL:** `STILLME_API_KEY` is NOT set! Protected endpoints (scheduler start/stop, database reset, knowledge injection) will fail with 401 Unauthorized. Set `STILLME_API_KEY` in Railway dashboard service variables (must match backend `STILLME_API_KEY`).")
    
    # Get scheduler status with longer timeout (backend may be busy during learning cycle)
    # Use try-except to handle timeout gracefully and show progress if job is running
    try:
        scheduler_status = get_json("/api/learning/scheduler/status", {}, timeout=90)
    except requests.exceptions.Timeout:
        # Backend may be busy processing learning cycle - check if job is running
        if st.session_state.get("learning_job_started"):
            # Job is running - this is expected, don't show error
            st.info("⏳ Backend is processing learning cycle. Showing job progress below...")
            scheduler_status = {}  # Empty to trigger job status display
        else:
            # No job running but timeout - backend may be busy or slow
            st.warning("⏳ Backend is taking longer than usual to respond. This may indicate a learning cycle is running.")
            st.info("💡 **Tip:** If you just clicked 'Run Now', the learning cycle is likely starting. Progress will appear below.")
            scheduler_status = {}
    
    # Debug: Show what we received and test connection
    if not scheduler_status or scheduler_status == {}:
        # Don't show error if we know a job is running (timeout is expected)
        if not st.session_state.get("learning_job_started"):
            st.warning("⚠️ **Warning:** Could not fetch scheduler status from backend.")
            st.info("💡 **Tip:** If you just clicked 'Run Now', the learning cycle is starting. Wait a moment and refresh.")
        
        # Try to provide more specific error info (only if not a known job)
        if not st.session_state.get("learning_job_started"):
            try:
                test_url = f"{API_BASE}/api/status"
                test_r = requests.get(test_url, timeout=10)  # Quick check for backend availability
                if test_r.status_code == 200:
                    st.info("💡 Backend is reachable. Scheduler status may be temporarily unavailable during learning cycle.")
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
        
        # Display source statistics for transparency
        source_stats = scheduler_status.get("source_statistics", {})
        if source_stats and not source_stats.get("error"):
            st.markdown("### 📊 Learning Source Statistics")
            
            # RSS Statistics
            if "rss" in source_stats:
                rss_stats = source_stats["rss"]
                col_rss1, col_rss2, col_rss3, col_rss4 = st.columns(4)
                with col_rss1:
                    st.metric("📡 RSS Feeds", rss_stats.get("feeds_count", 0))
                with col_rss2:
                    st.metric("✅ Successful", rss_stats.get("successful_feeds", 0))
                with col_rss3:
                    st.metric("❌ Failed", rss_stats.get("failed_feeds", 0))
                with col_rss4:
                    status_icon = "🟢" if rss_stats.get("status") == "ok" else "🔴"
                    st.metric("Status", f"{status_icon} {rss_stats.get('status', 'unknown').upper()}")
                
                # Show errors if any
                if rss_stats.get("failed_feeds", 0) > 0:
                    with st.expander("⚠️ RSS Feed Errors", expanded=False):
                        if rss_stats.get("last_error"):
                            st.error(f"**Last Error:** {rss_stats['last_error']}")
                        st.caption(f"💡 {rss_stats.get('failed_feeds', 0)} feed(s) failed. Check backend logs for details.")
            
            # Other sources (arXiv, CrossRef, Wikipedia, etc.)
            other_sources = {k: v for k, v in source_stats.items() if k != "rss"}
            if other_sources:
                with st.expander("📚 Other Learning Sources", expanded=False):
                    for source_name, source_data in other_sources.items():
                        if isinstance(source_data, dict):
                            # Structure: {"enabled": True, "stats": {"status": "ok", ...}}
                            # If stats is None, source hasn't been used yet
                            stats = source_data.get("stats")
                            if stats is None:
                                # Source enabled but not used yet - show as "not_used" or "enabled"
                                status_icon = "🟡" if source_data.get("enabled", False) else "⚪"
                                status_text = "enabled" if source_data.get("enabled", False) else "disabled"
                                st.write(f"**{source_name.replace('_', ' ').title()}**: {status_icon} {status_text}")
                            elif isinstance(stats, dict):
                                # Stats available - check status
                                status = stats.get("status", "unknown")
                                status_icon = "🟢" if status == "ok" else "🔴"
                                st.write(f"**{source_name.replace('_', ' ').title()}**: {status_icon} {status}")
                                if stats.get("error_count", 0) > 0:
                                    st.caption(f"  ⚠️ {stats.get('error_count', 0)} error(s)")
                                if stats.get("last_error"):
                                    st.caption(f"  📝 Last error: {stats['last_error'][:100]}...")
                            else:
                                # Invalid stats format
                                status_icon = "🔴"
                                st.write(f"**{source_name.replace('_', ' ').title()}**: {status_icon} unknown")
        
        # Scheduler controls: Stop and Run Now (Start removed - scheduler auto-starts)
        col_stop, col_run_now, col_stats = st.columns(3)
        with col_stop:
            if st.button("⏹️ Stop Scheduler", width='stretch'):
                try:
                    # Increased timeout to 30s to handle network latency (Railway deployment)
                    r = requests.post(
                        f"{API_BASE}/api/learning/scheduler/stop",
                        headers=get_api_headers(),
                        timeout=30
                    )
                    if r.status_code == 200:
                        st.session_state["last_action"] = "✅ Scheduler stopped successfully!"
                        st.rerun()
                except requests.exceptions.Timeout:
                    # Timeout doesn't mean failure - scheduler may have stopped in background
                    # Check status to confirm
                    try:
                        status_check = get_json("/api/learning/scheduler/status", {}, timeout=10)
                        if not status_check.get("is_running", True):
                            st.session_state["last_action"] = "✅ Scheduler stopped successfully! (Confirmed via status check)"
                            st.rerun()
                        else:
                            st.session_state["last_error"] = "⏱️ Request timed out. Please check scheduler status - it may have stopped in background."
                    except:
                        st.session_state["last_error"] = "⏱️ Request timed out. Scheduler may have stopped - please refresh to check status."
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 401:
                        st.session_state["last_error"] = f"❌ 401 Unauthorized: API key missing or invalid. Please set STILLME_API_KEY in Railway dashboard service variables."
                    elif e.response.status_code == 403:
                        st.session_state["last_error"] = f"❌ 403 Forbidden: Invalid API key. Please verify STILLME_API_KEY matches backend key."
                    else:
                        st.session_state["last_error"] = f"❌ Failed to stop scheduler: {e}"
                except Exception as e:
                    st.session_state["last_error"] = f"❌ Failed to stop scheduler: {e}"
        with col_run_now:
            if st.button("🚀 Run Now", width='stretch'):
                # Store Vector DB stats BEFORE running to compare later
                try:
                    initial_rag_stats = get_json("/api/rag/stats", {}, timeout=10)
                    st.session_state["initial_rag_stats"] = initial_rag_stats.get("stats", {})
                except:
                    st.session_state["initial_rag_stats"] = {}
                
                # Store current cycle count to detect completion
                try:
                    current_status = get_json("/api/learning/scheduler/status", {}, timeout=10)
                    if current_status and current_status.get("status") == "ok":
                        st.session_state["learning_cycle_count_at_start"] = current_status.get("cycle_count", 0)
                except:
                    st.session_state["learning_cycle_count_at_start"] = 0
                
                # Make the API call (with short timeout for immediate feedback)
                try:
                    # Non-blocking: returns 202 immediately
                    r = requests.post(f"{API_BASE}/api/learning/scheduler/run-now", timeout=5)
                    if r.status_code == 202:
                        data = r.json()
                        job_id = data.get("job_id")
                        st.session_state["learning_job_id"] = job_id
                        st.session_state["learning_job_started"] = True
                        st.session_state["learning_job_start_time"] = time_module.time()
                        # IMMEDIATE FEEDBACK
                        st.success("🚀 Learning cycle started! Running in background (2-5 minutes). Results will appear below when complete.")
                    elif r.status_code == 200:
                        # Sync mode (for tests) - immediate results
                        data = r.json()
                        entries = data.get("entries_fetched", 0)
                        filtered = data.get("entries_filtered", 0)
                        added = data.get("entries_added_to_rag", 0)
                        
                        if filtered > 0:
                            st.session_state["last_action"] = f"✅ Learning cycle completed! Fetched {entries} entries, Filtered {filtered} (Low quality/Short), Added {added} to RAG."
                        else:
                            st.session_state["last_action"] = f"✅ Learning cycle completed! Fetched {entries} entries, added {added} to RAG."
                        st.session_state["learning_job_started"] = False
                        st.session_state["learning_cycle_result"] = data
                        st.success("✅ Learning cycle completed immediately!")
                    else:
                        st.session_state["last_error"] = f"❌ Failed: {r.json().get('detail', 'Unknown error')}"
                        st.error(st.session_state["last_error"])
                except requests.exceptions.Timeout:
                    # Timeout is OK - job is running in background
                    st.session_state["learning_job_id"] = None
                    st.session_state["learning_job_started"] = True
                    st.session_state["learning_job_start_time"] = time_module.time()
                    # IMMEDIATE FEEDBACK even on timeout
                    st.success("🚀 Learning cycle started! Running in background (2-5 minutes). Results will appear below when complete.")
                except Exception as e:
                    st.session_state["last_error"] = f"❌ Failed to start: {e}"
                    st.session_state["learning_job_started"] = False
                    st.error(st.session_state["last_error"])
                
                # Rerun to show progress section
                st.rerun()
        
        with col_stats:
            if st.button("📊 Learning Statistics", width='stretch', help="View detailed learning statistics (what StillMe learned/didn't learn and why)"):
                st.session_state["show_learning_stats"] = True
                st.rerun()
        
        # Display Learning Statistics Dialog (Task Manager style)
        if st.session_state.get("show_learning_stats", False):
            st.markdown("---")
            with st.expander("📊 Learning Statistics", expanded=True):
                try:
                    # Get RSS fetch history
                    fetch_history = get_json("/api/learning/rss/fetch-history", {"limit": 200}, timeout=30)
                    
                    # Handle None response
                    if fetch_history is None:
                        st.warning("⚠️ Backend returned no data. RSS fetch history may not be initialized yet.")
                        st.caption("💡 Run a learning cycle first to generate statistics.")
                        if st.button("❌ Close Statistics", use_container_width=True):
                            st.session_state["show_learning_stats"] = False
                            st.rerun()
                        return
                    
                    # Ensure items is a list
                    items = fetch_history.get("items", [])
                    if items is None:
                        items = []
                    
                    if items and len(items) > 0:
                        st.markdown("### 📋 Learning Activity Table")
                        st.caption(f"Showing {len(items)} most recent learning items")
                        
                        # Create Task Manager style table
                        from datetime import datetime
                        
                        # Prepare data for table
                        table_data = []
                        for item in items:
                            source = item.get("source_url", item.get("source", "Unknown"))
                            title = item.get("title", "No title")[:60] + "..." if len(item.get("title", "")) > 60 else item.get("title", "No title")
                            status = item.get("status", "Unknown")
                            # Ensure reason is always a string (never None)
                            reason = item.get("status_reason") or ""
                            if reason is None:
                                reason = ""
                            timestamp = item.get("fetch_timestamp", item.get("timestamp", ""))
                            
                            # Format timestamp - convert UTC to local timezone (GMT+7)
                            try:
                                if timestamp:
                                    if isinstance(timestamp, str):
                                        # Parse UTC timestamp
                                        if timestamp.endswith('Z'):
                                            timestamp = timestamp[:-1] + '+00:00'
                                        dt_utc = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                        
                                        # Convert UTC to GMT+7 (Vietnam timezone)
                                        from datetime import timezone, timedelta
                                        gmt7 = timezone(timedelta(hours=7))
                                        dt_local = dt_utc.astimezone(gmt7)
                                        
                                        formatted_time = dt_local.strftime("%b %d %Y %H:%M:%S")
                                    else:
                                        formatted_time = str(timestamp)
                                else:
                                    formatted_time = "N/A"
                            except:
                                formatted_time = str(timestamp) if timestamp else "N/A"
                            
                            # Determine status icon and color
                            if "Added" in status or "added" in status.lower():
                                status_icon = "✅"
                                status_color = "green"
                            elif "Filtered" in status or "filtered" in status.lower():
                                status_icon = "⚠️"
                                status_color = "orange"
                            elif "Failed" in status or "failed" in status.lower():
                                status_icon = "❌"
                                status_color = "red"
                            else:
                                status_icon = "ℹ️"
                                status_color = "gray"
                            
                            table_data.append({
                                "Source": source[:40] + "..." if len(source) > 40 else source,
                                "Title": title,
                                "Status": f"{status_icon} {status}",
                                "Reason": (reason[:50] + "..." if len(reason) > 50 else reason) if reason else "",
                                "Timestamp": formatted_time
                            })
                        
                        # Create DataFrame and display
                        df = pd.DataFrame(table_data)
                        
                        # Style the DataFrame
                        def highlight_status(row):
                            if "✅" in str(row["Status"]):
                                return ['background-color: #1e3a2e'] * len(row)
                            elif "⚠️" in str(row["Status"]):
                                return ['background-color: #3a2e1e'] * len(row)
                            elif "❌" in str(row["Status"]):
                                return ['background-color: #3a1e1e'] * len(row)
                            return [''] * len(row)
                        
                        st.dataframe(
                            df.style.apply(highlight_status, axis=1),
                            use_container_width=True,
                            height=400
                        )
                        
                        # Summary statistics
                        st.markdown("### 📈 Summary")
                        col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
                        
                        added_count = sum(1 for item in items if "Added" in item.get("status", ""))
                        filtered_count = sum(1 for item in items if "Filtered" in item.get("status", ""))
                        failed_count = sum(1 for item in items if "Failed" in item.get("status", ""))
                        total = len(items)
                        
                        with col_sum1:
                            st.metric("Total Items", total)
                        with col_sum2:
                            st.metric("✅ Learned", added_count, delta=f"{round(added_count/total*100, 1)}%" if total > 0 else "0%")
                        with col_sum3:
                            st.metric("⚠️ Filtered", filtered_count, delta=f"{round(filtered_count/total*100, 1)}%" if total > 0 else "0%")
                        with col_sum4:
                            st.metric("❌ Failed", failed_count, delta=f"{round(failed_count/total*100, 1)}%" if total > 0 else "0%")
                        
                        # Filter reasons breakdown
                        filter_reasons = {}
                        for item in items:
                            if "Filtered" in item.get("status", ""):
                                reason = item.get("status_reason", "Unknown reason")
                                filter_reasons[reason] = filter_reasons.get(reason, 0) + 1
                        
                        if filter_reasons:
                            st.markdown("### 🔍 Filter Reasons Breakdown")
                            for reason, count in sorted(filter_reasons.items(), key=lambda x: x[1], reverse=True):
                                st.write(f"- **{reason}**: {count} items")
                    else:
                        st.info("📭 No learning history available yet. Run a learning cycle to see statistics.")
                        
                except Exception as e:
                    import traceback
                    error_detail = str(e)
                    error_traceback = traceback.format_exc()
                    st.error(f"❌ Failed to load learning statistics: {error_detail}")
                    st.caption("💡 Make sure backend is running and RSS fetch history is enabled.")
                    # Show detailed error for debugging
                    with st.expander("🔍 Error Details (for debugging)", expanded=False):
                        st.code(error_traceback, language="text")
                
                # Close button
                if st.button("❌ Close Statistics", use_container_width=True):
                    st.session_state["show_learning_stats"] = False
                    st.rerun()
        
        # Display learning cycle progress if job is running
        if st.session_state.get("learning_job_started"):
            job_id = st.session_state.get("learning_job_id")
            st.markdown("---")
            st.subheader("📊 Learning Cycle Progress")
            
            # Skip polling if job_id is None or "timeout_fallback" (not a real job ID)
            if not job_id or job_id == "timeout_fallback":
                # Check scheduler status to see if cycle has completed
                # Get current scheduler status to check if cycle finished
                try:
                    current_scheduler_status = get_json("/api/learning/scheduler/status", {}, timeout=90)
                except requests.exceptions.Timeout:
                    # Backend is busy - likely still processing
                    current_scheduler_status = {}
                if current_scheduler_status and current_scheduler_status.get("status") == "ok":
                    is_running = current_scheduler_status.get("is_running", False)
                    last_run_time = current_scheduler_status.get("last_run_time")
                    cycle_count = current_scheduler_status.get("cycle_count", 0)
                    
                    # Check if we have a stored cycle_count to compare
                    stored_cycle_count = st.session_state.get("learning_cycle_count_at_start", None)
                    
                    # If stored_cycle_count is None, set it to current cycle_count (first check after timeout)
                    if stored_cycle_count is None:
                        st.session_state["learning_cycle_count_at_start"] = cycle_count
                        stored_cycle_count = cycle_count
                    
                    # If scheduler is not running AND cycle_count increased, cycle completed
                    if not is_running and cycle_count > stored_cycle_count:
                        # Get current Vector DB stats to show what changed
                        try:
                            current_rag_stats = get_json("/api/rag/stats", {}, timeout=10)
                            current_stats = current_rag_stats.get("stats", {})
                            initial_stats = st.session_state.get("initial_rag_stats", {})
                            
                            # Calculate changes
                            initial_total = initial_stats.get("total_documents", 0)
                            current_total = current_stats.get("total_documents", 0)
                            docs_added = current_total - initial_total
                            
                            initial_knowledge = initial_stats.get("knowledge_documents", 0)
                            current_knowledge = current_stats.get("knowledge_documents", 0)
                            knowledge_added = current_knowledge - initial_knowledge
                            
                            # Show detailed results
                            st.success("✅ Learning cycle completed!")
                            
                            if docs_added > 0:
                                st.info(f"📊 **Results:** Added {docs_added} new documents to Vector DB ({knowledge_added} knowledge docs). Total: {current_total} documents.")
                            elif docs_added == 0 and current_total > 0:
                                st.info(f"📊 **Results:** No new documents added. Total: {current_total} documents (may have filtered out low-quality content).")
                            else:
                                st.info(f"📊 **Results:** Vector DB now has {current_total} documents.")
                            
                            # Try to get more details from scheduler if available
                            if last_run_time:
                                st.caption(f"⏰ Completed at: {last_run_time}")
                        except Exception as stats_error:
                            st.success("✅ Learning cycle completed!")
                            st.info("💡 Check Vector DB Stats above and scheduler status below for details.")
                        
                        # Clear job tracking
                        st.session_state["learning_job_started"] = False
                        st.session_state["learning_job_id"] = None
                        st.session_state["learning_cycle_count_at_start"] = None
                        st.session_state["initial_rag_stats"] = {}
                    elif not is_running and last_run_time:
                        # Scheduler stopped and has a last_run_time - cycle likely completed
                        # Check if Vector DB stats changed to confirm
                        try:
                            current_rag_stats = get_json("/api/rag/stats", {}, timeout=10)
                            current_stats = current_rag_stats.get("stats", {})
                            initial_stats = st.session_state.get("initial_rag_stats", {})
                            
                            initial_total = initial_stats.get("total_documents", 0)
                            current_total = current_stats.get("total_documents", 0)
                            docs_added = current_total - initial_total
                            
                            # If stats changed, cycle definitely completed
                            if docs_added > 0 or (current_total > 0 and initial_total == 0):
                                st.success("✅ Learning cycle completed!")
                                initial_knowledge = initial_stats.get("knowledge_documents", 0)
                                current_knowledge = current_stats.get("knowledge_documents", 0)
                                knowledge_added = current_knowledge - initial_knowledge
                                
                                if docs_added > 0:
                                    st.info(f"📊 **Results:** Added {docs_added} new documents to Vector DB ({knowledge_added} knowledge docs). Total: {current_total} documents.")
                                else:
                                    st.info(f"📊 **Results:** Vector DB now has {current_total} documents.")
                                
                                if st.button("✅ Dismiss", key="dismiss_cycle"):
                                    st.session_state["learning_job_started"] = False
                                    st.session_state["learning_job_id"] = None
                                    st.session_state["learning_cycle_count_at_start"] = None
                                    st.session_state["initial_rag_stats"] = {}
                                    st.rerun()
                            else:
                                # Stats didn't change - may still be processing or no new content
                                st.info("⏳ Learning cycle may have completed. Scheduler is stopped.")
                                st.info("💡 **Tip:** Check Vector DB Stats above and scheduler status below. If cycle completed, you can dismiss this message.")
                                if st.button("✅ Dismiss (Cycle Completed)", key="dismiss_cycle"):
                                    st.session_state["learning_job_started"] = False
                                    st.session_state["learning_job_id"] = None
                                    st.session_state["learning_cycle_count_at_start"] = None
                                    st.session_state["initial_rag_stats"] = {}
                                    st.rerun()
                        except:
                            # Fallback if can't get stats
                            st.info("⏳ Learning cycle may have completed. Scheduler is stopped.")
                            st.info("💡 **Tip:** Check scheduler status below. If cycle completed, you can dismiss this message.")
                            if st.button("✅ Dismiss (Cycle Completed)", key="dismiss_cycle_fallback"):
                                st.session_state["learning_job_started"] = False
                                st.session_state["learning_job_id"] = None
                                st.session_state["learning_cycle_count_at_start"] = None
                                st.session_state["initial_rag_stats"] = {}
                                st.rerun()
                            else:
                                # Auto-refresh to check scheduler status
                                refresh_placeholder = st.empty()
                                refresh_placeholder.info("🔄 Auto-refreshing in 3 seconds...")
                                time.sleep(3)
                                st.rerun()
                    else:
                        # Still running or unknown status - continue auto-refresh
                        st.info("⏳ Learning cycle is running in background. This may take 2-5 minutes.")
                        st.info("💡 **Tip:** Check scheduler status below to see when the cycle completes.")
                        # Auto-refresh to check scheduler status
                        refresh_placeholder = st.empty()
                        refresh_placeholder.info("🔄 Auto-refreshing in 3 seconds...")
                        import time
                        time.sleep(3)
                        st.rerun()
                else:
                    # Could not get scheduler status - continue auto-refresh but with warning
                    st.warning("⚠️ Could not check scheduler status. Learning cycle may still be running.")
                    st.info("💡 **Tip:** Check backend logs to see if learning cycle is still running.")
                    # Auto-refresh to check scheduler status
                    refresh_placeholder = st.empty()
                    refresh_placeholder.info("🔄 Auto-refreshing in 3 seconds...")
                    import time
                    time.sleep(3)
                    st.rerun()
            else:
                # Poll job status (with longer timeout - learning cycle can take 2-5 minutes)
                try:
                    job_status_r = requests.get(f"{API_BASE}/api/learning/scheduler/job-status/{job_id}", timeout=60)
                    if job_status_r.status_code == 200:
                        job_data = job_status_r.json()
                        job_status = job_data.get("status", "unknown")
                        progress = job_data.get("progress", {})
                        logs = job_data.get("logs", [])
                        
                        # Status indicator
                        if job_status == "done":
                            st.success("✅ Learning cycle completed!")
                            
                            result = job_data.get("result", {})
                            entries_fetched = result.get("entries_fetched", 0)
                            entries_filtered = result.get("entries_filtered", 0)
                            entries_added = result.get("entries_added_to_rag", 0)
                            entries_skipped = result.get("entries_skipped_tiered", 0)
                            
                            # Show completion summary with details
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("📥 Fetched", entries_fetched,
                                         help="Total entries fetched from all sources")
                            
                            with col2:
                                st.metric("🔍 Filtered", entries_filtered,
                                         delta=f"-{entries_filtered}" if entries_filtered > 0 else None,
                                         delta_color="inverse",
                                         help="Entries filtered out (low quality, too short, or duplicate)")
                            
                            with col3:
                                st.metric("🧠 Processed", entries_added + entries_skipped,
                                         help="Total entries processed (added + skipped by Nested Learning)")
                            
                            with col4:
                                st.metric("💾 Added to RAG", entries_added,
                                         delta=f"+{entries_added}" if entries_added > 0 else None,
                                         help="Entries successfully added to vector database")
                            
                            # Parse logs for detailed breakdown
                            source_breakdown = {}
                            filter_reasons_detail = {}
                            
                            for log in logs:
                                log_lower = log.lower()
                                # Extract source breakdown
                                if "source breakdown:" in log_lower:
                                    breakdown_text = log.split("Source breakdown:")[-1].strip()
                                    for part in breakdown_text.split(","):
                                        if ":" in part:
                                            try:
                                                source, count = part.strip().split(":", 1)
                                                source_breakdown[source.strip()] = int(count.strip())
                                            except:
                                                pass
                                # Extract filter reasons
                                if "filter reasons:" in log_lower:
                                    reasons_text = log.split("Filter reasons:")[-1].strip()
                                    for part in reasons_text.split(","):
                                        if ":" in part:
                                            try:
                                                reason, count = part.strip().split(":", 1)
                                                filter_reasons_detail[reason.strip()] = int(count.strip())
                                            except:
                                                pass
                            
                            # Show source breakdown if available
                            if source_breakdown:
                                st.markdown("### 📊 Source Breakdown")
                                cols = st.columns(len(source_breakdown) if len(source_breakdown) <= 4 else 4)
                                for idx, (source, count) in enumerate(source_breakdown.items()):
                                    with cols[idx % len(cols)]:
                                        st.metric(source, count, help=f"Items fetched from {source}")
                            
                            # Show filter reasons if available (from result or logs)
                            filter_reasons = result.get("filter_reasons", {})
                            if not filter_reasons and filter_reasons_detail:
                                filter_reasons = filter_reasons_detail
                            
                            if filter_reasons:
                                with st.expander("🔍 Filter Details", expanded=True):
                                    st.write("**Reasons for filtering:**")
                                    for reason, count in filter_reasons.items():
                                        st.write(f"- **{reason}**: {count} entries")
                            elif entries_filtered > 0:
                                st.caption(f"💡 {entries_filtered} entries filtered (low quality, too short, or duplicate)")
                            
                            # Show Nested Learning summary if enabled
                            if entries_skipped > 0:
                                cost_reduction = (entries_skipped / (entries_added + entries_skipped)) * 100 if (entries_added + entries_skipped) > 0 else 0
                                st.success(f"🎯 **Nested Learning**: Skipped {entries_skipped} entries - {cost_reduction:.1f}% cost reduction!")
                            
                            # Show elapsed time
                            if job_data.get("started_at") and job_data.get("completed_at"):
                                from datetime import datetime
                                try:
                                    started_str = job_data["started_at"]
                                    completed_str = job_data["completed_at"]
                                    if started_str.endswith('Z'):
                                        started_str = started_str[:-1] + '+00:00'
                                    if completed_str.endswith('Z'):
                                        completed_str = completed_str[:-1] + '+00:00'
                                    started = datetime.fromisoformat(started_str)
                                    completed = datetime.fromisoformat(completed_str)
                                    elapsed = (completed - started).total_seconds()
                                    elapsed_min = int(elapsed // 60)
                                    elapsed_sec = int(elapsed % 60)
                                    st.caption(f"⏱️ Total time: {elapsed_min}m {elapsed_sec}s")
                                except:
                                    pass
                            
                            # Clear job tracking
                            st.session_state["learning_job_started"] = False
                            st.session_state["learning_job_id"] = None
                        elif job_status == "error":
                            st.error(f"❌ Learning cycle failed: {job_data.get('error', 'Unknown error')}")
                            st.session_state["learning_job_started"] = False
                            st.session_state["learning_job_id"] = None
                        else:
                            # Show detailed progress with percentage
                            phase = progress.get("phase", "pending")
                            
                            # Phase display with progress percentage
                            phase_info = {
                                "pending": ("⏳ Waiting to start...", 0),
                                "fetching": ("📥 Fetching from sources...", 20),
                                "prefilter": ("🔍 Filtering content...", 40),
                                "embedding": ("🧠 Generating embeddings...", 60),
                                "adding_to_rag": ("💾 Adding to RAG...", 80)
                            }.get(phase, (f"🔄 {phase}...", 0))
                            
                            phase_text, phase_percent = phase_info
                            
                            # Show progress bar
                            st.progress(phase_percent / 100, text=f"{phase_text} ({phase_percent}%)")
                            
                            # Show detailed metrics
                            entries_fetched = progress.get("entries_fetched", 0)
                            entries_filtered = progress.get("entries_filtered", 0)
                            entries_added = progress.get("entries_added", 0)
                            entries_skipped = progress.get("entries_skipped_tiered", 0)
                            current_item = progress.get("current_item", "")
                            
                            # Create columns for metrics
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("📥 Fetched", entries_fetched, 
                                         help="Total entries fetched from all sources (RSS, arXiv, CrossRef, Wikipedia)")
                            
                            with col2:
                                st.metric("🔍 Filtered", entries_filtered, 
                                         delta=f"-{entries_filtered}" if entries_filtered > 0 else None,
                                         delta_color="inverse",
                                         help="Entries filtered out (low quality, too short, or duplicate)")
                            
                            with col3:
                                total_processed = entries_added + entries_skipped
                                st.metric("🧠 Processed", total_processed,
                                         help="Total entries processed for embedding (added + skipped by Nested Learning)")
                            
                            with col4:
                                st.metric("💾 Added to RAG", entries_added,
                                         delta=f"+{entries_added}" if entries_added > 0 else None,
                                         help="Entries successfully added to vector database")
                            
                            # Show current item being processed
                            if current_item:
                                st.caption(f"🔄 Currently processing: {current_item}")
                            
                            # Show filtered reasons if available (from result)
                            result = job_data.get("result", {})
                            if result and entries_filtered > 0:
                                filter_reasons = result.get("filter_reasons", {})
                                if filter_reasons:
                                    with st.expander("🔍 Filter Details", expanded=False):
                                        st.write("**Reasons for filtering:**")
                                        for reason, count in filter_reasons.items():
                                            st.write(f"- **{reason}**: {count} entries")
                                else:
                                    # Show general filter info
                                    st.caption(f"💡 {entries_filtered} entries filtered (low quality, too short, or duplicate)")
                            
                            # Show Nested Learning info if enabled
                            if entries_skipped > 0:
                                st.info(f"🎯 **Nested Learning**: Skipped {entries_skipped} entries (tiered update isolation) - Cost saved!")
                            
                            # Show detailed breakdown from logs
                            if logs:
                                # Parse logs to extract source breakdown and filter details
                                source_breakdown = {}
                                filter_reasons_detail = {}
                                
                                for log in logs:
                                    log_lower = log.lower()
                                    # Extract source breakdown
                                    if "source breakdown:" in log_lower:
                                        breakdown_text = log.split("Source breakdown:")[-1].strip()
                                        for part in breakdown_text.split(","):
                                            if ":" in part:
                                                source, count = part.strip().split(":", 1)
                                                source_breakdown[source.strip()] = int(count.strip())
                                    # Extract filter reasons
                                    if "filter reasons:" in log_lower:
                                        reasons_text = log.split("Filter reasons:")[-1].strip()
                                        for part in reasons_text.split(","):
                                            if ":" in part:
                                                reason, count = part.strip().split(":", 1)
                                                filter_reasons_detail[reason.strip()] = int(count.strip())
                                
                                # Show source breakdown if available
                                if source_breakdown:
                                    with st.expander("📊 Source Breakdown", expanded=True):
                                        cols = st.columns(len(source_breakdown))
                                        for idx, (source, count) in enumerate(source_breakdown.items()):
                                            with cols[idx % len(cols)]:
                                                st.metric(source, count)
                                
                                # Show filter reasons detail if available
                                if filter_reasons_detail:
                                    with st.expander("🔍 Filter Reasons Detail", expanded=False):
                                        for reason, count in filter_reasons_detail.items():
                                            st.write(f"- **{reason}**: {count} entries")
                                
                                # Show recent logs
                                with st.expander("📋 Recent Activity Logs", expanded=True):
                                    # Show last 15 logs (increased from 10)
                                    for log in logs[-15:]:
                                        # Highlight important logs
                                        if any(keyword in log.lower() for keyword in ["fetched", "filter", "added", "completed", "error"]):
                                            if "error" in log.lower() or "failed" in log.lower():
                                                st.error(log)
                                            elif "completed" in log.lower() or "added" in log.lower():
                                                st.success(log)
                                            elif "filter" in log.lower():
                                                st.warning(log)
                                            else:
                                                st.info(log)
                                        else:
                                            st.text(log)
                            
                            # Show elapsed time
                            if job_data.get("started_at"):
                                from datetime import datetime
                                try:
                                    started_str = job_data["started_at"]
                                    if started_str.endswith('Z'):
                                        started_str = started_str[:-1] + '+00:00'
                                    started = datetime.fromisoformat(started_str)
                                    elapsed = (datetime.now(started.tzinfo) - started).total_seconds()
                                    elapsed_min = int(elapsed // 60)
                                    elapsed_sec = int(elapsed % 60)
                                    st.caption(f"⏱️ Elapsed time: {elapsed_min}m {elapsed_sec}s | Estimated remaining: {max(0, 3 - elapsed_min)}m")
                                except Exception as e:
                                    pass
                            
                            # Auto-refresh every 2 seconds
                            refresh_placeholder = st.empty()
                            refresh_placeholder.info("🔄 Auto-refreshing in 2 seconds...")
                            import time
                            time.sleep(2)
                            st.rerun()
                    else:
                        st.warning(f"⚠️ Could not fetch job status: {job_status_r.status_code}")
                except requests.exceptions.Timeout:
                    st.warning("⏱️ Job status check timed out (60s). Learning cycle may still be running.")
                    st.info("💡 **Tip:** Backend is processing. This is normal - learning cycles take 2-5 minutes.")
                    st.info("🔄 **Auto-refresh:** This page will auto-refresh every 3 seconds to show progress.")
                    # Keep job tracking active so it continues polling
                    refresh_placeholder = st.empty()
                    refresh_placeholder.info("🔄 Auto-refreshing in 3 seconds...")
                    import time
                    time.sleep(3)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error checking job status: {e}")
                    st.info("💡 **Tip:** Check backend logs to see if learning cycle is still running.")
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
            if st.button("🔄 Reset Vector Database", width='stretch', type="secondary"):
                try:
                    with st.spinner("Resetting database (this may take a moment)..."):
                        r = requests.post(
                            f"{API_BASE}/api/rag/reset-database",
                            headers=get_api_headers(),
                            timeout=60
                        )
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
        if st.button("🚀 Run Learning Session", width='stretch'):
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
                            headers=get_api_headers(),
                            json={
                                "content": content,
                                "source": source,
                                "content_type": content_type,
                            },
                            timeout=180,  # Increased to 180s to handle embedding generation
                        )
                        r.raise_for_status()  # Raise exception for 4xx/5xx errors
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
                                # Note: This is a tracking ID, not the actual ChromaDB vector ID
                                # The actual ChromaDB ID format is: knowledge_<uuid> (generated during embedding)
                                st.write(f"**Tracking ID:** `{item.get('vector_id')}`")
                                st.caption("ℹ️ This is a tracking ID for fetch history. The actual ChromaDB vector ID is generated during embedding.")
                        st.write(f"**Summary:** {item.get('summary', 'N/A')[:200]}...")
    except Exception as e:
        st.error(f"Error fetching data: {e}")


# Community page has been moved to standalone community.py
# Access it via the floating Community button in bottom-left corner


def page_validation():
    """Validation metrics and monitoring page"""
    st.markdown("## Validation Metrics")
    st.caption("Monitor validator chain performance and reduce hallucinations")
    
    # Check if validators are enabled
    try:
        status_data = get_json("/api/status", {})
        validators_enabled = status_data.get("validators_enabled", False)
    except Exception:
        validators_enabled = False
    
    # Get validation metrics
    try:
        metrics_data = get_json("/api/validators/metrics", {}).get("metrics", {})
    except Exception:
        metrics_data = {}
    
    total_validations = metrics_data.get("total_validations", 0)
    
    if total_validations == 0:
        if validators_enabled:
            st.info(
                "✅ **Validators are enabled** (`ENABLE_VALIDATORS=true`)\n\n"
                "📊 **No validation data yet.** Send a chat message via the floating widget to start collecting metrics.\n\n"
                "💡 Validation metrics are recorded automatically when you chat with StillMe through any interface."
            )
        else:
            st.warning(
                "⚠️ **Validators are disabled** (`ENABLE_VALIDATORS=false`)\n\n"
                "To enable validators:\n"
                "1. Set `ENABLE_VALIDATORS=true` in your backend environment variables\n"
                "2. Restart the backend service\n"
                "3. Send a chat message to start collecting validation metrics"
            )
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
                        "Tracking ID": item.get("vector_id", "N/A"),
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
                            st.write(f"**Tracking ID:** `{item.get('vector_id', 'N/A')}`")
                            st.caption("ℹ️ Tracking ID for fetch history. Actual ChromaDB vector ID is generated during embedding.")
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


def page_nested_learning():
    """Nested Learning metrics and visualization page"""
    st.header("🔬 Nested Learning Metrics")
    st.caption("Tiered update frequency system - reduces embedding costs by updating knowledge at different frequencies")
    
    # Fetch metrics
    metrics = get_json("/api/learning/nested-learning/metrics", {}, timeout=30)
    
    if not metrics:
        st.error("❌ **Failed to fetch metrics from backend**")
        st.info("Please check backend logs and ensure backend is running.")
        return
    
    if metrics.get("enabled") is False:
        st.warning("⚠️ **Nested Learning is disabled**")
        message = metrics.get("message", "Nested Learning is disabled")
        st.info(f"{message}\n\n**To enable:** Set `ENABLE_CONTINUUM_MEMORY=true` in backend environment variables, then restart/redeploy backend.")
        
        # Show current API response for debugging
        with st.expander("🔍 Debug: API Response"):
            st.json(metrics)
        return
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Cycle", metrics.get("cycle_count", 0))
    with col2:
        cost_reduction = metrics.get("cost_reduction", {})
        st.metric("Cost Reduction", f"{cost_reduction.get('reduction_percentage', 0):.1f}%")
    with col3:
        total_ops = cost_reduction.get("total_operations", 0)
        st.metric("Total Operations", total_ops)
    with col4:
        skipped_ops = cost_reduction.get("skipped_operations", 0)
        st.metric("Skipped Operations", skipped_ops)
    
    st.markdown("---")
    
    # Tier Distribution
    st.subheader("📊 Tier Distribution")
    tier_dist = metrics.get("tier_distribution", {})
    if tier_dist:
        col1, col2 = st.columns(2)
        with col1:
            # Bar chart
            tiers = ["L0", "L1", "L2", "L3"]
            counts = [tier_dist.get(tier, 0) for tier in tiers]
            fig = go.Figure(data=[
                go.Bar(x=tiers, y=counts, marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
            ])
            fig.update_layout(
                title="Knowledge Items per Tier",
                xaxis_title="Tier",
                yaxis_title="Count",
                height=300
            )
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            # Pie chart
            if sum(counts) > 0:
                fig = go.Figure(data=[go.Pie(
                    labels=tiers,
                    values=counts,
                    hole=0.3,
                    marker_colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
                )])
                fig.update_layout(
                    title="Tier Distribution (%)",
                    height=300
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("No knowledge items in tiers yet. Run a learning cycle to populate tiers.")
    else:
        st.info("No tier distribution data available yet.")
    
    st.markdown("---")
    
    # Update Frequency & Operations
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔄 Update Frequency")
        update_freq = metrics.get("tier_update_frequency", {})
        update_counts = metrics.get("tier_update_counts", {})
        skipped_counts = metrics.get("tier_skipped_counts", {})
        
        for tier in ["L0", "L1", "L2", "L3"]:
            freq = update_freq.get(tier, 0)
            updated = update_counts.get(tier, 0)
            skipped = skipped_counts.get(tier, 0)
            st.write(f"**{tier}**: Every {freq} cycles | Updated: {updated} | Skipped: {skipped}")
    
    with col2:
        st.subheader("💾 Embedding Operations")
        emb_ops = metrics.get("embedding_operations", {})
        total = emb_ops.get("total", 0)
        by_tier = emb_ops.get("by_tier", {})
        
        st.metric("Total Embeddings", total)
        for tier in ["L0", "L1", "L2", "L3"]:
            count = by_tier.get(tier, 0)
            if total > 0:
                pct = (count / total) * 100
                st.write(f"**{tier}**: {count} ({pct:.1f}%)")
    
    st.markdown("---")
    
    # Surprise Score Statistics
    st.subheader("🎯 Surprise Score Statistics")
    surprise_stats = metrics.get("surprise_score_stats", {})
    if surprise_stats and surprise_stats.get("count", 0) > 0:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Count", surprise_stats.get("count", 0))
        with col2:
            st.metric("Min", f"{surprise_stats.get('min', 0):.3f}")
        with col3:
            st.metric("Max", f"{surprise_stats.get('max', 0):.3f}")
        with col4:
            st.metric("Average", f"{surprise_stats.get('avg', 0):.3f}")
        
        st.caption("Surprise score determines tier routing: L0 (<0.4), L1 (0.4-0.6), L2 (0.6-0.8), L3 (≥0.8)")
    else:
        st.info("No surprise score data yet. Run a learning cycle to collect statistics.")
    
    st.markdown("---")
    
    # Cost Reduction Details
    st.subheader("💰 Cost Reduction Analysis")
    cost_reduction = metrics.get("cost_reduction", {})
    total_ops = cost_reduction.get("total_operations", 0)
    skipped_ops = cost_reduction.get("skipped_operations", 0)
    reduction_pct = cost_reduction.get("reduction_percentage", 0)
    
    if total_ops > 0:
        st.info(f"**{reduction_pct}% cost reduction** by skipping {skipped_ops} out of {total_ops} embedding operations")
        
        # Visualize cost reduction
        fig = go.Figure(data=[
            go.Bar(name="Performed", x=["Embedding Operations"], y=[total_ops], marker_color='#2ca02c'),
            go.Bar(name="Skipped", x=["Embedding Operations"], y=[skipped_ops], marker_color='#ff7f0e')
        ])
        fig.update_layout(
            title="Embedding Operations: Performed vs Skipped",
            barmode='stack',
            height=300
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No embedding operations recorded yet. Run a learning cycle to see cost reduction metrics.")


def sidebar(page_for_chat: str | None = None):
    st.sidebar.header("Dashboard")
    
    # Initialize session state for page selector if not exists
    if "page_selector" not in st.session_state:
        st.session_state["page_selector"] = "Overview"
    
    page = st.sidebar.selectbox(
        "Select Page",
        ["Overview", "RAG", "Learning", "Validation", "Memory Health", "Nested Learning"],
        key="page_selector",
        index=0 if st.session_state["page_selector"] not in ["Overview", "RAG", "Learning", "Validation", "Memory Health", "Nested Learning"] else ["Overview", "RAG", "Learning", "Validation", "Memory Health", "Nested Learning"].index(st.session_state["page_selector"])
    )

    st.sidebar.success("Backend Connected")

    st.sidebar.markdown("---")
    
    # Initialize chat history service (for floating widget)
    if CHAT_HISTORY_AVAILABLE:
        if "chat_history_service" not in st.session_state:
            try:
                st.session_state.chat_history_service = ChatHistory()
            except Exception as e:
                st.session_state.chat_history_service = None
    else:
        st.session_state.chat_history_service = None
    
    # Generate session ID from Streamlit session state
    if "chat_session_id" not in st.session_state:
        # Generate a stable session ID based on Streamlit session state
        session_id_str = str(st.session_state.get("_session_id", id(st.session_state)))
        st.session_state.chat_session_id = hashlib.md5(session_id_str.encode()).hexdigest()[:16]
    
    # Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
        # Load chat history from SQLite if available
        if st.session_state.chat_history_service:
            try:
                db_history = st.session_state.chat_history_service.get_history(
                    session_id=st.session_state.chat_session_id,
                    limit=100
                )
                # Convert database format to session state format
                for msg in db_history:
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": msg["user_message"]
                    })
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": msg["assistant_response"],
                        "confidence_score": msg.get("confidence_score"),
                        "validation_info": {
                            "passed": msg.get("validation_passed"),
                            "context_docs_count": msg.get("context_docs_count")
                        } if msg.get("validation_passed") is not None else None,
                        "latency_metrics": f"Latency: {msg.get('latency', 0):.2f}s" if msg.get("latency") else None
                    })
            except Exception as e:
                pass  # Silent fail - history loading is optional
    
    # Render floating chat widget (always enabled, no mode selector)
    if FLOATING_CHAT_AVAILABLE:
        # Render floating chat widget
        render_floating_chat(
            chat_history=st.session_state.chat_history,
            api_base=API_BASE,
            is_open=True
        )
        
        # Note: Floating widget handles its own chat logic via JavaScript
        st.sidebar.success("✅ **Floating Chat Widget Active!**")
        st.sidebar.info("💡 Look for the **💬 chat button** in the **bottom-right corner** of your screen. Click it to open the resizable chat panel!")
        st.sidebar.markdown("---")
        st.sidebar.caption("**Features:** Resize, Drag, Fullscreen, Overlay")
    else:
        st.sidebar.warning("⚠️ Floating chat widget is not available. Please check frontend components.")
    
    # Sidebar chat removed - using floating widget only
    # (Old sidebar chat code removed for cleaner UX)
    
    return page


def main():
    st.set_page_config(
        page_title="StillMe",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    page = sidebar()
    
    # Render floating community panel (always visible, after sidebar to ensure it's on top)
    if FLOATING_COMMUNITY_AVAILABLE:
        try:
            render_floating_community_panel()
        except Exception as e:
            # Fallback: Show link in sidebar if floating panel fails
            st.sidebar.error(f"⚠️ Community panel error: {e}")
            st.sidebar.markdown("---")
            st.sidebar.markdown("💬 [Join StillMe Community](https://discord.gg/stillme)")
    
    # Route to appropriate page
    if page == "Overview":
        page_overview()
    elif page == "RAG":
        page_rag()
    elif page == "Learning":
        page_learning()
    elif page == "Validation":
        page_validation()
    elif page == "Memory Health":
        from dashboard_memory_health import page_memory_health
        page_memory_health()
    elif page == "Nested Learning":
        page_nested_learning()

    # Tiny auto-refresh toggle for live demos
    with st.sidebar.expander("Auto Refresh"):
        enabled = st.checkbox("Always rerun", value=False)
        interval = st.slider("Seconds", 5, 60, 15)
        if enabled:
            time.sleep(interval)
            st.rerun()


if __name__ == "__main__":
    main()


