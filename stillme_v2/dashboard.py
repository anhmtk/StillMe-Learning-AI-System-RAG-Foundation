import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="StillMe V2 Dashboard",
    page_icon="assets/logo.png",
    layout="wide"
)

# Header with logo
col1, col2 = st.columns([1, 4])

with col1:
    st.image("assets/logo.png", width=100)

with col2:
    st.title("🧠 StillMe V2 - Self-Evolving AI System")
    st.markdown("**Real-time Learning Analytics & Historical Progress Tracking**")

# Main dashboard content
st.markdown("---")

# System Status
st.subheader("📊 System Status")

try:
    # Get API info - test with existing endpoint
    api_response = requests.get(f"{API_BASE_URL}/api/learning/rss/pipeline-stats", timeout=5)
    if api_response.status_code == 200:
        api_data = api_response.json()
        st.success(f"✅ Backend Connected - Sources: {api_data.get('enabled_sources', 0)}")
    else:
        st.warning("⚠️ Backend not responding")
except Exception as e:
    st.error(f"❌ Error connecting to backend: {str(e)}")

# Ethical Safety Filter Status
st.subheader("🛡️ Ethical Safety Filter")
st.markdown("**Transparent ethical content filtering system**")

try:
    # Get ethical stats
    ethics_response = requests.get(f"{API_BASE_URL}/api/learning/ethics/stats", timeout=5)
    if ethics_response.status_code == 200:
        ethics_data = ethics_response.json()
        safety_stats = ethics_data.get("safety_stats", {})
        ethical_summary = ethics_data.get("ethical_summary", {})
        
        # Display ethical metrics
        ethics_col1, ethics_col2, ethics_col3, ethics_col4 = st.columns(4)
        
        with ethics_col1:
            st.metric(
                "🛡️ Ethics Level", 
                safety_stats.get("ethics_level", "medium").title(),
                help="Current ethical filtering level"
            )
        
        with ethics_col2:
            st.metric(
                "🚫 Total Violations", 
                safety_stats.get("total_violations", 0),
                help="Total ethical violations detected"
            )
        
        with ethics_col3:
            st.metric(
                "📝 Blacklist Keywords", 
                safety_stats.get("blacklist_keywords_count", 0),
                help="Number of blocked keywords"
            )
        
        with ethics_col4:
            st.metric(
                "🔍 Unreliable Sources", 
                safety_stats.get("unreliable_sources_count", 0),
                help="Number of blocked source patterns"
            )
        
        # Ethical principles monitoring
        st.markdown("**📋 Ethical Principles Monitored**")
        principles = safety_stats.get("principles_monitored", [])
        if principles:
            principles_text = " • ".join([p.replace("_", " ").title() for p in principles])
            st.info(f"🔍 **Monitoring:** {principles_text}")
        
        # Violations by principle
        violations_by_principle = ethical_summary.get("violations_by_principle", {})
        if violations_by_principle:
            st.markdown("**⚠️ Violations by Principle**")
            violations_df = pd.DataFrame([
                {"Principle": principle.replace("_", " ").title(), "Count": count}
                for principle, count in violations_by_principle.items()
                if count > 0
            ])
            
            if not violations_df.empty:
                fig_violations = px.bar(
                    violations_df, 
                    x="Principle", 
                    y="Count",
                    title="Ethical Violations by Principle",
                    color="Count",
                    color_continuous_scale="Reds"
                )
                st.plotly_chart(fig_violations, use_container_width=True)
            else:
                st.success("✅ No ethical violations detected!")
        
        # Recent violations
        st.markdown("**📋 Recent Ethical Violations**")
        violations_response = requests.get(f"{API_BASE_URL}/api/learning/ethics/violations", 
                                         params={"limit": 5}, timeout=5)
        if violations_response.status_code == 200:
            violations_data = violations_response.json()
            violations = violations_data.get("violations", [])
            
            if violations:
                for violation in violations:
                    severity_color = {
                        "low": "🟡",
                        "medium": "🟠", 
                        "high": "🔴",
                        "critical": "🚨"
                    }.get(violation["severity"], "⚪")
                    
                    with st.expander(f"{severity_color} {violation['principle'].replace('_', ' ').title()} - {violation['description'][:50]}..."):
                        st.write(f"**Severity:** {violation['severity'].title()}")
                        st.write(f"**Context:** {violation['context']}")
                        st.write(f"**Suggested Action:** {violation['suggested_action']}")
                        st.write(f"**Timestamp:** {violation['timestamp']}")
            else:
                st.success("✅ No recent ethical violations!")
        
        # Ethical controls
        st.markdown("**⚙️ Ethical Filter Controls**")
        control_col1, control_col2, control_col3 = st.columns(3)
        
        with control_col1:
            if st.button("🧹 Clear Violations"):
                clear_response = requests.post(f"{API_BASE_URL}/api/learning/ethics/clear-violations", timeout=5)
                if clear_response.status_code == 200:
                    st.success("✅ Violations cleared!")
                    st.rerun()
                else:
                    st.error("❌ Failed to clear violations")
        
        with control_col2:
            # Test content ethics
            test_content = st.text_area("Test Content Ethics", placeholder="Enter content to test...", height=100)
            if st.button("🔍 Test Content") and test_content:
                test_response = requests.post(f"{API_BASE_URL}/api/learning/ethics/check-content", 
                                            params={"content": test_content}, timeout=5)
                if test_response.status_code == 200:
                    test_data = test_response.json()
                    if test_data.get("is_safe"):
                        st.success(f"✅ Content is safe ({test_data.get('level', 'unknown')})")
                    else:
                        st.error(f"❌ Content blocked: {test_data.get('reason', 'unknown')}")
                        violations = test_data.get("violations", [])
                        for violation in violations:
                            st.warning(f"⚠️ {violation['principle']}: {violation['description']}")
                else:
                    st.error("❌ Failed to test content")
        
        with control_col3:
            # Blacklist management
            st.markdown("**📝 Blacklist Management**")
            new_keyword = st.text_input("Add Keyword", placeholder="Enter keyword to block...")
            if st.button("➕ Add") and new_keyword:
                add_response = requests.post(f"{API_BASE_URL}/api/learning/ethics/add-blacklist-keyword", 
                                           params={"keyword": new_keyword}, timeout=5)
                if add_response.status_code == 200:
                    st.success(f"✅ Added '{new_keyword}' to blacklist!")
                    st.rerun()
                else:
                    st.error("❌ Failed to add keyword")
        
        # Transparency statement
        st.markdown("**🔍 Transparency Statement**")
        st.info("""
        **StillMe V2 Ethical Filtering Transparency:**
        
        - **Complete Visibility:** All ethical violations are logged and visible
        - **Open Source:** Filtering rules and algorithms are publicly available
        - **Community Driven:** Blacklist and rules can be managed by the community
        - **Audit Trail:** Full history of all ethical decisions and violations
        - **Configurable:** Ethics level can be adjusted based on community needs
        
        This transparency ensures StillMe V2 learns responsibly while maintaining community trust.
        """)
        
    else:
        st.error("❌ Cannot get ethical stats")
        
except Exception as e:
    st.error(f"❌ Ethical safety filter error: {e}")

st.markdown("---")

try:
    # Get RSS Pipeline Stats
    response = requests.get(f"{API_BASE_URL}/api/learning/rss/pipeline-stats", timeout=10)
    if response.status_code == 200:
        pipeline_stats = response.json()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("RSS Sources", pipeline_stats.get("total_rss_sources", 0))
        with col2:
            st.metric("API Sources", pipeline_stats.get("total_api_sources", 0))
        with col3:
            st.metric("Total Sources", pipeline_stats.get("enabled_sources", 0))
        with col4:
            st.metric("Content Fetched", pipeline_stats.get("fetched_content_count", 0))
        
        # Show categories
        categories = pipeline_stats.get("categories", [])
        if categories:
            st.markdown("**Active Categories:**")
            category_chips = " ".join([f"`{cat}`" for cat in categories])
            st.markdown(category_chips)
        
        # Manual fetch controls
        st.markdown("**🔄 Manual Controls**")
        control_col1, control_col2, control_col3 = st.columns(3)
        
        with control_col1:
            if st.button("📡 Fetch Content Now", help="Manually fetch content from RSS and API sources"):
                try:
                    fetch_response = requests.post(f"{API_BASE_URL}/api/learning/rss/fetch-content", timeout=30)
                    if fetch_response.status_code == 200:
                        fetch_data = fetch_response.json()
                        st.success(f"✅ Fetched {fetch_data.get('total_items', 0)} items successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to fetch content")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with control_col2:
            if st.button("🧠 Generate Proposals", help="Generate learning proposals from fetched content"):
                try:
                    # Trigger learning session to generate proposals
                    session_response = requests.post(f"{API_BASE_URL}/api/learning/sessions/run", timeout=60)
                    if session_response.status_code == 200:
                        session_data = session_response.json()
                        st.success(f"✅ Generated {session_data.get('proposals_learned', 0)} proposals!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to generate proposals")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with control_col3:
            if st.button("📊 Update Stats", help="Update today's learning statistics"):
                try:
                    stats_response = requests.post(f"{API_BASE_URL}/api/learning/analytics/update-today", timeout=10)
                    if stats_response.status_code == 200:
                        stats_data = stats_response.json()
                        st.success(f"✅ Updated stats for {stats_data.get('date', 'today')}!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update stats")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        # Learning Growth Metrics with Timeline Selector
        st.markdown("**📈 Learning Progress Analysis**")
        
        # Timeline selector
        today = datetime.now().strftime("%Y-%m-%d")
        
        timeline_col1, timeline_col2, timeline_col3 = st.columns([2, 1, 1])
        
        with timeline_col1:
            timeline_option = st.selectbox(
                "📅 Select Analysis Period",
                ["Today vs Yesterday", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"],
                help="Choose the time period for learning analysis"
            )
        
        with timeline_col2:
            if timeline_option == "Custom Range":
                start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=7))
            else:
                start_date = None
        
        with timeline_col3:
            if timeline_option == "Custom Range":
                end_date = st.date_input("End Date", value=datetime.now())
            else:
                end_date = None
        
        # Get comparison data based on selection
        try:
            if timeline_option == "Today vs Yesterday":
                yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                
                # Get comparison data
                comparison_response = requests.get(f"{API_BASE_URL}/api/learning/analytics/comparison", 
                                                 params={"current_date": today, "compare_date": yesterday}, timeout=5)
                
                if comparison_response.status_code == 200:
                    comparison_data = comparison_response.json()
                    
                    # Display comparison metrics
                    growth_col1, growth_col2, growth_col3, growth_col4 = st.columns(4)
                    
                    with growth_col1:
                        content_data = comparison_data.get("content_fetched", {})
                        st.metric(
                            "📰 Content Today", 
                            content_data.get("current", 0),
                            delta=f"{content_data.get('delta', 0):+d} vs yesterday",
                            help="New content items fetched today"
                        )
                    
                    with growth_col2:
                        proposals_data = comparison_data.get("proposals_generated", {})
                        st.metric(
                            "🧠 Proposals Today", 
                            proposals_data.get("current", 0),
                            delta=f"{proposals_data.get('delta', 0):+d} vs yesterday",
                            help="New learning proposals generated today"
                        )
                    
                    with growth_col3:
                        efficiency_data = comparison_data.get("learning_efficiency", {})
                        st.metric(
                            "⚡ Learning Efficiency", 
                            f"{efficiency_data.get('current', 0):.1f}%",
                            delta=f"{efficiency_data.get('delta_percent', 0):+.1f}% vs yesterday",
                            help="Percentage of content converted to learning proposals"
                        )
                    
                    with growth_col4:
                        sessions_data = comparison_data.get("successful_sessions", {})
                        st.metric(
                            "🔥 Successful Sessions", 
                            sessions_data.get("current", 0),
                            delta=f"{sessions_data.get('delta', 0):+d} vs yesterday",
                            help="Number of successful learning sessions today"
                        )
                else:
                    st.warning("⚠️ Could not load comparison data")
            
            elif timeline_option in ["Last 7 Days", "Last 30 Days", "Last 90 Days"]:
                days_map = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}
                days = days_map[timeline_option]
                
                # Get trends data
                trends_response = requests.get(f"{API_BASE_URL}/api/learning/analytics/trends", 
                                             params={"days": days}, timeout=5)
                
                if trends_response.status_code == 200:
                    trends_data = trends_response.json()
                    
                    # Display trends metrics
                    trends_col1, trends_col2, trends_col3, trends_col4 = st.columns(4)
                    
                    with trends_col1:
                        st.metric(
                            "📊 Total Content", 
                            trends_data.get("total_content_fetched", 0),
                            delta=f"{trends_data.get('growth_rate_percent', 0):+.1f}% growth",
                            help=f"Total content fetched in {days} days"
                        )
                    
                    with trends_col2:
                        st.metric(
                            "🧠 Total Proposals", 
                            trends_data.get("total_proposals_generated", 0),
                            delta=f"{trends_data.get('daily_averages', {}).get('proposals_per_day', 0):.1f}/day",
                            help=f"Total proposals generated in {days} days"
                        )
                    
                    with trends_col3:
                        st.metric(
                            "⚡ Avg Efficiency", 
                            f"{trends_data.get('average_learning_efficiency', 0):.1f}%",
                            delta=f"{trends_data.get('daily_averages', {}).get('efficiency_per_day', 0):.1f}% avg",
                            help=f"Average learning efficiency over {days} days"
                        )
                    
                    with trends_col4:
                        evolution_stages = trends_data.get("evolution_stages", [])
                        current_stage = evolution_stages[-1] if evolution_stages else "infant"
                        st.metric(
                            "🧬 Evolution Stage", 
                            current_stage.title(),
                            delta=f"{len(evolution_stages)} stages",
                            help="Current AI evolution stage"
                        )
                    
                    # Show best day
                    best_day = trends_data.get("best_day")
                    if best_day:
                        st.info(f"🏆 **Best Learning Day:** {best_day['date']} - {best_day['content_fetched']} content items fetched!")
                
                else:
                    st.warning("⚠️ Could not load trends data")
            
            elif timeline_option == "Custom Range" and start_date and end_date:
                # Get historical data for custom range
                historical_response = requests.get(f"{API_BASE_URL}/api/learning/analytics/historical", 
                                                 params={"start_date": start_date.strftime("%Y-%m-%d"), 
                                                        "end_date": end_date.strftime("%Y-%m-%d")}, timeout=5)
                
                if historical_response.status_code == 200:
                    historical_data = historical_response.json()
                    stats = historical_data.get("stats", [])
                    
                    if stats:
                        # Calculate totals
                        total_content = sum(s["content_fetched"] for s in stats)
                        total_proposals = sum(s["proposals_generated"] for s in stats)
                        avg_efficiency = sum(s["learning_efficiency"] for s in stats) / len(stats)
                        
                        # Display custom range metrics
                        custom_col1, custom_col2, custom_col3, custom_col4 = st.columns(4)
                        
                        with custom_col1:
                            st.metric(
                                "📊 Total Content", 
                                total_content,
                                delta=f"{len(stats)} days",
                                help=f"Total content fetched from {start_date} to {end_date}"
                            )
                        
                        with custom_col2:
                            st.metric(
                                "🧠 Total Proposals", 
                                total_proposals,
                                delta=f"{total_proposals/len(stats):.1f}/day avg",
                                help=f"Total proposals generated from {start_date} to {end_date}"
                            )
                        
                        with custom_col3:
                            st.metric(
                                "⚡ Avg Efficiency", 
                                f"{avg_efficiency:.1f}%",
                                delta=f"{len(stats)} days analyzed",
                                help=f"Average learning efficiency from {start_date} to {end_date}"
                            )
                        
                        with custom_col4:
                            evolution_stages = list(set(s["evolution_stage"] for s in stats))
                            st.metric(
                                "🧬 Evolution Stages", 
                                len(evolution_stages),
                                delta=f"{', '.join(evolution_stages)}",
                                help="Evolution stages observed in this period"
                            )
                    else:
                        st.warning("📭 No data available for the selected period")
                else:
                    st.warning("⚠️ Could not load historical data")
        
        except Exception as e:
            st.error(f"❌ Error loading analytics: {e}")
            # Fallback to basic metrics
            current_fetched = pipeline_stats.get("fetched_content_count", 0)
            current_proposals = pipeline_stats.get("proposals_count", 0)
            
            growth_col1, growth_col2, growth_col3, growth_col4 = st.columns(4)
            
            with growth_col1:
                st.metric("📰 Content Today", current_fetched, help="Content fetched today")
            with growth_col2:
                st.metric("🧠 Proposals Today", current_proposals, help="Proposals generated today")
            with growth_col3:
                efficiency = (current_proposals / current_fetched * 100) if current_fetched > 0 else 0
                st.metric("⚡ Learning Efficiency", f"{efficiency:.1f}%", help="Learning efficiency today")
            with growth_col4:
                st.metric("🔥 Learning Streak", "1 day", delta="+1 day", help="Consecutive learning days")
    else:
        st.warning("⚠️ Backend not responding - using demo data")
        # Demo data for transparency
        st.info("**Demo Data (Backend Offline):**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("RSS Sources", "8", help="ArXiv, OpenAI Blog, Google AI, etc.")
        with col2:
            st.metric("API Sources", "5", help="News API, Weather API, etc.")
        with col3:
            st.metric("Total Sources", "13", help="All active data sources")
        with col4:
            st.metric("Content Fetched", "22", help="Items fetched today")

except Exception as e:
    st.error(f"❌ Error getting API info: {str(e)}")

# Recently Fetched Content
st.subheader("📰 Recently Fetched Content")

try:
    # Get fetched content
    fetched_response = requests.get(f"{API_BASE_URL}/api/learning/rss/fetched-content", 
                                  params={"limit": 5}, timeout=5)
    if fetched_response.status_code == 200:
        fetched_data = fetched_response.json()
        items = fetched_data.get("items", [])
        
        if items:
            st.success(f"📊 Showing {len(items)} most recent content items")
            
            # Display content items
            for i, item in enumerate(items):
                with st.expander(f"📄 {item['title'][:60]}..." if len(item['title']) > 60 else f"📄 {item['title']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Source:** {item['source_name']}")
                        st.write(f"**Category:** {item['source_category']}")
                        st.write(f"**Content:** {item['content_preview']}")
                    
                    with col2:
                        st.write(f"**Created:** {item['created_at']}")
                        st.write(f"**Hash:** `{item['content_hash']}`")
        else:
            st.warning("📭 No content fetched yet. Click 'Fetch Content' to start learning!")
            
    else:
        st.warning("⚠️ Could not load fetched content")
        
except Exception as e:
    st.error(f"❌ Error loading fetched content: {e}")

# Learning Proposals
st.subheader("🧠 Learning Proposals")

try:
    # Get learned proposals
    proposals_response = requests.get(f"{API_BASE_URL}/api/learning/proposals/learned", 
                                    params={"limit": 5}, timeout=5)
    if proposals_response.status_code == 200:
        proposals_data = proposals_response.json()
        proposals = proposals_data.get("proposals", [])
        
        if proposals:
            st.success(f"📚 Showing {len(proposals)} most recent learning proposals")
            
            # Display proposals
            for i, proposal in enumerate(proposals):
                status_color = "🟢" if proposal['status'] == 'approved' else "🟡"
                with st.expander(f"{status_color} {proposal['title'][:60]}..." if len(proposal['title']) > 60 else f"{status_color} {proposal['title']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Source:** {proposal['source_name']}")
                        st.write(f"**Category:** {proposal['category']}")
                        st.write(f"**Content:** {proposal['content_preview']}")
                    
                    with col2:
                        st.write(f"**Quality:** {proposal['quality_score']:.2f}")
                        st.write(f"**Relevance:** {proposal['relevance_score']:.2f}")
                        st.write(f"**Novelty:** {proposal['novelty_score']:.2f}")
                        st.write(f"**Status:** {proposal['status']}")
                        st.write(f"**Created:** {proposal['created_at']}")
        else:
            st.warning("📭 No learning proposals yet. Content needs to be processed into proposals!")
            
    else:
        st.warning("⚠️ Could not load learning proposals")
        
except Exception as e:
    st.error(f"❌ Error loading learning proposals: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div align="center">
  <img src="assets/logo.png" alt="StillMe V2 Logo" width="50"/>
  <br>
  <strong>StillMe V2 - Self-Evolving AI System</strong><br>
  <em>Real-time Learning Analytics & Historical Progress Tracking</em>
</div>
""", unsafe_allow_html=True)
