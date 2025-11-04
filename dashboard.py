import os
import time
from datetime import datetime
from typing import Any, Dict

import requests
import streamlit as st
import plotly.graph_objects as go


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

    st.markdown("## StillMe")
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
    st.subheader("Quick Actions")
    q1, q2 = st.columns(2)
    with q1:
        if st.button("🚀 Run Learning Session"):
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
                st.success(r.json().get("status", "Recorded"))
            except Exception as e:
                st.warning(f"Learning session not recorded: {e}")
    with q2:
        if st.button("📊 Update Metrics"):
            # No explicit update endpoint; just re-fetch metrics by rerun
            st.experimental_rerun()


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
    st.markdown("## Community Voting (Coming Soon)")
    st.info(
        "Secure Voting with min votes, threshold, cooldown and EthicsGuard will be available here."
    )
    if st.button("Mock Vote Approve", help="Placeholder button"):
        st.success("Thanks! Voting API will be wired in a next release.")


def sidebar(page_for_chat: str | None = None):
    st.sidebar.header("Dashboard")
    page = st.sidebar.selectbox(
        "Choose a page:", ["Overview", "RAG", "Learning", "Community"]
    )

    st.sidebar.success("Backend Connected")

    # Chat panel appears only on Overview
    if page == "Overview":
        st.sidebar.markdown("---")
        st.sidebar.subheader("💬 Chat with StillMe")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        user_msg = st.sidebar.text_area("Your message", height=80)
        if st.sidebar.button("Send", use_container_width=True):
            if user_msg.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_msg})
                try:
                    r = requests.post(
                        f"{API_BASE}/api/chat/smart_router",
                        json={"message": user_msg},
                        timeout=30,
                    )
                    data = r.json()
                    reply = data.get("response") or data.get("message") or str(data)
                except Exception as e:
                    reply = f"Demo mode: backend not available ({e})"
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.experimental_rerun()
        # Show last 6 messages inline in sidebar
        for m in st.session_state.chat_history[-6:]:
            speaker = "You" if m["role"] == "user" else "StillMe"
            st.sidebar.caption(f"**{speaker}:** {m['content']}")
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


