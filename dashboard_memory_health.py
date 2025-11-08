"""
Memory Health Dashboard Page for Continuum Memory System
Displays tier statistics, promotion/demotion audit, and forgetting trends
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Import from main dashboard
from dashboard import get_json


def page_memory_health():
    """Memory Health dashboard page - shows tier stats, audit log, and forgetting trends"""
    
    st.header("🧠 Memory Health")
    st.caption("Continuum Memory System - Tier Management & Forgetting Metrics")
    
    # Check if Continuum Memory is enabled
    enable_continuum_memory = st.sidebar.checkbox(
        "Enable Continuum Memory",
        value=False,
        help="Enable tier-based memory system (requires ENABLE_CONTINUUM_MEMORY=true on backend)"
    )
    
    if not enable_continuum_memory:
        st.info("💡 **Continuum Memory is disabled.** Enable it in the sidebar to view metrics.")
        st.markdown("""
        ### About Continuum Memory
        
        Continuum Memory implements a tiered memory architecture:
        
        - **L0 (Session/Cache)**: Hot, newly fetched knowledge (TTL: hours-days)
        - **L1 (Working KB)**: Validated knowledge with usage tracking (TTL: weeks)
        - **L2 (Canonical KB)**: Standard knowledge with high confidence (TTL: months+)
        - **L3 (Core/Policy)**: Immutable rules and standards (permanent)
        
        **Features:**
        - Surprise-based promotion/demotion
        - Multi-timescale scheduler
        - Forgetting@RAG metrics (Recall@k degradation tracking)
        """)
        return
    
    # Fetch tier stats
    tier_stats = get_json("/api/v1/tiers/stats", {})
    
    if not tier_stats:
        st.warning("⚠️ Could not fetch tier statistics. Backend may not have Continuum Memory enabled.")
        return
    
    # Tier Distribution Chart
    st.subheader("📊 Tier Distribution")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("L0 (Session)", tier_stats.get("L0", 0))
    with col2:
        st.metric("L1 (Working)", tier_stats.get("L1", 0))
    with col3:
        st.metric("L2 (Canonical)", tier_stats.get("L2", 0))
    with col4:
        st.metric("L3 (Core)", tier_stats.get("L3", 0))
    
    # Tier distribution pie chart
    if tier_stats.get("total", 0) > 0:
        fig_pie = go.Figure(data=[go.Pie(
            labels=["L0", "L1", "L2", "L3"],
            values=[
                tier_stats.get("L0", 0),
                tier_stats.get("L1", 0),
                tier_stats.get("L2", 0),
                tier_stats.get("L3", 0)
            ],
            hole=0.3,
            marker_colors=["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]
        )])
        fig_pie.update_layout(
            title="Tier Distribution",
            height=400,
            showlegend=True
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Promotion/Demotion Metrics
    st.subheader("🔄 Promotion & Demotion (Last 7 Days)")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Promoted", tier_stats.get("promoted_7d", 0), delta=None)
    with col2:
        st.metric("Demoted", tier_stats.get("demoted_7d", 0), delta=None)
    
    # Promotion/Demotion trend chart (mock data for PR-1)
    st.markdown("#### Promotion/Demotion Trend")
    mock_trend_data = {
        "Date": [
            (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(7, 0, -1)
        ],
        "Promoted": [2, 3, 1, 4, 2, 3, tier_stats.get("promoted_7d", 0)],
        "Demoted": [1, 0, 2, 1, 0, 1, tier_stats.get("demoted_7d", 0)]
    }
    df_trend = pd.DataFrame(mock_trend_data)
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=df_trend["Date"],
        y=df_trend["Promoted"],
        mode="lines+markers",
        name="Promoted",
        line=dict(color="#4ECDC4", width=2),
        marker=dict(size=8)
    ))
    fig_trend.add_trace(go.Scatter(
        x=df_trend["Date"],
        y=df_trend["Demoted"],
        mode="lines+markers",
        name="Demoted",
        line=dict(color="#FF6B6B", width=2),
        marker=dict(size=8)
    ))
    fig_trend.update_layout(
        title="Promotion/Demotion Trend (Last 7 Days)",
        xaxis_title="Date",
        yaxis_title="Count",
        height=350,
        hovermode="x unified"
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Audit Log Table
    st.subheader("📋 Audit Log")
    audit_log = get_json("/api/v1/tiers/audit?limit=50", {})
    
    if audit_log and audit_log.get("records"):
        records = audit_log.get("records", [])
        df_audit = pd.DataFrame(records)
        
        # Format columns for display
        if not df_audit.empty:
            # Select relevant columns
            display_cols = ["item_id", "from_tier", "to_tier", "reason", "surprise_score", "created_at"]
            available_cols = [col for col in display_cols if col in df_audit.columns]
            df_display = df_audit[available_cols].copy()
            
            # Format surprise_score
            if "surprise_score" in df_display.columns:
                df_display["surprise_score"] = df_display["surprise_score"].apply(
                    lambda x: f"{x:.3f}" if x is not None else "N/A"
                )
            
            st.dataframe(df_display, use_container_width=True, height=400)
        else:
            st.info("No audit records found.")
    else:
        st.info("No audit records available (mock data may be empty).")
    
    # Forgetting Trends
    st.subheader("📉 Forgetting Trends (Recall@k Degradation)")
    forgetting_trends = get_json("/api/v1/tiers/forgetting-trends?days=30", {})
    
    if forgetting_trends and forgetting_trends.get("trends"):
        trends = forgetting_trends.get("trends", [])
        
        if trends:
            df_forgetting = pd.DataFrame(trends)
            
            # Forgetting Delta Chart
            fig_forgetting = go.Figure()
            fig_forgetting.add_trace(go.Scatter(
                x=df_forgetting["evaluation_timestamp"],
                y=df_forgetting["avg_forgetting_delta"],
                mode="lines+markers",
                name="Forgetting Δ",
                line=dict(color="#FF6B6B", width=2),
                marker=dict(size=8),
                fill="tozeroy",
                fillcolor="rgba(255, 107, 107, 0.2)"
            ))
            fig_forgetting.add_hline(
                y=0.1,
                line_dash="dash",
                line_color="orange",
                annotation_text="Warning Threshold (Δ > 0.1)"
            )
            fig_forgetting.update_layout(
                title="Forgetting Delta Over Time",
                xaxis_title="Evaluation Date",
                yaxis_title="Forgetting Δ (Recall Before - Recall After)",
                height=400,
                hovermode="x unified"
            )
            st.plotly_chart(fig_forgetting, use_container_width=True)
            
            # Recall Before/After Comparison
            fig_recall = go.Figure()
            fig_recall.add_trace(go.Scatter(
                x=df_forgetting["evaluation_timestamp"],
                y=df_forgetting["avg_recall_before"],
                mode="lines+markers",
                name="Recall@k Before",
                line=dict(color="#4ECDC4", width=2),
                marker=dict(size=8)
            ))
            fig_recall.add_trace(go.Scatter(
                x=df_forgetting["evaluation_timestamp"],
                y=df_forgetting["avg_recall_after"],
                mode="lines+markers",
                name="Recall@k After",
                line=dict(color="#FF6B6B", width=2),
                marker=dict(size=8)
            ))
            fig_recall.update_layout(
                title="Recall@k Before vs After Knowledge Updates",
                xaxis_title="Evaluation Date",
                yaxis_title="Recall@k Score",
                height=400,
                hovermode="x unified"
            )
            st.plotly_chart(fig_recall, use_container_width=True)
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_delta = df_forgetting["avg_forgetting_delta"].mean()
                st.metric("Avg Forgetting Δ", f"{avg_delta:.3f}")
            with col2:
                avg_recall_before = df_forgetting["avg_recall_before"].mean()
                st.metric("Avg Recall Before", f"{avg_recall_before:.3f}")
            with col3:
                avg_recall_after = df_forgetting["avg_recall_after"].mean()
                st.metric("Avg Recall After", f"{avg_recall_after:.3f}")
        else:
            st.info("No forgetting trend data available.")
    else:
        st.info("Forgetting trends not available (mock data may be empty).")
    
    # Surprise Score Formula Info
    with st.expander("ℹ️ Surprise Score Formula", expanded=False):
        st.markdown("""
        ### Surprise Score Calculation
        
        The surprise score is calculated using the following formula:
        
        ```
        surprise_score = 0.3 × rarity_score + 
                        0.3 × novelty_score + 
                        0.2 × retrieval_frequency + 
                        0.2 × validator_overlap
        ```
        
        **Components:**
        - **rarity_score** (0.0-1.0): Uniqueness of keywords in the content
        - **novelty_score** (0.0-1.0): Cosine distance from centroid of existing knowledge (OOD detection)
        - **retrieval_frequency** (0.0-1.0): Normalized retrieval count in last 7 days
        - **validator_overlap** (0.0-1.0): Evidence overlap from validator chain
        
        **Promotion Rules:**
        - Promote L0→L1: `surprise_score >= 0.65` AND `retrieval_count_7d` increasing
        - Promote L1→L2: `surprise_score >= 0.65` AND `validator_overlap >= 0.8`
        - Demote L2→L1: `retrieval_count_7d == 0` OR `validator_overlap < 0.3`
        - Expire L0: Age > retention_days (default: 2 days)
        
        **Note:** PR-1 uses mock computation. Real computation will be implemented in PR-2.
        """)

