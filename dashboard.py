# ... existing code ...
def _page_meta_learning():
    """Meta-Learning Dashboard tab (Stage 2 features)"""
    st.markdown("### 🧠 Meta-Learning Dashboard")
    st.caption("Stage 2: AI improves HOW it learns - Retention tracking, Curriculum learning, Strategy optimization")
    
    # Sub-tabs for 3 phases
    phase1, phase2, phase3 = st.tabs([
        "Retention Tracking", 
        "Curriculum Learning", 
        "Strategy Optimization"
    ])
    
    with phase1:
        _page_meta_learning_retention()
    
    with phase2:
        _page_meta_learning_curriculum()
    
    with phase3:
        _page_meta_learning_strategy()


def _page_meta_learning_retention():
    """Phase 1: Retention Tracking visualization"""
    st.markdown("#### Retention Tracking")
    st.caption("Track which sources are actually used in responses")
    
    # Days selector
    days = st.slider("Analysis Period (days)", 1, 365, 30, key="retention_days")
    
    # Fetch retention metrics
    try:
        retention_data = get_json(f"/api/meta-learning/retention?days={days}", {}, timeout=30)
        
        if retention_data and "sources" in retention_data:
            sources_data = retention_data["sources"]
            
            if sources_data:
                # Source retention rates chart
                st.markdown("##### Source Retention Rates")
                
                # Prepare data for chart
                source_names = []
                retention_rates = []
                total_retrieved = []
                total_used = []
                
                for source, stats in sources_data.items():
                    source_names.append(source[:40] + "..." if len(source) > 40 else source)
                    retention_rates.append(stats.get("retention_rate", 0.0) * 100)
                    total_retrieved.append(stats.get("total_documents_retrieved", 0))
                    total_used.append(stats.get("documents_used_in_response", 0))
                
                # Bar chart using plotly
                if PANDAS_AVAILABLE:
                    df_retention = pd.DataFrame({
                        "Source": source_names,
                        "Retention Rate (%)": retention_rates,
                        "Total Retrieved": total_retrieved,
                        "Total Used": total_used
                    })
                    
                    # Sort by retention rate
                    df_retention = df_retention.sort_values("Retention Rate (%)", ascending=False)
                    
                    # Bar chart
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=df_retention["Source"],
                        y=df_retention["Retention Rate (%)"],
                        text=[f"{r:.1f}%" for r in df_retention["Retention Rate (%)"]],
                        textposition="auto",
                        marker_color=df_retention["Retention Rate (%)"].apply(
                            lambda x: "green" if x >= 30 else "orange" if x >= 10 else "red"
                        )
                    ))
                    fig.update_layout(
                        title="Source Retention Rates",
                        xaxis_title="Source",
                        yaxis_title="Retention Rate (%)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Table with details
                    st.markdown("##### Detailed Statistics")
                    st.dataframe(df_retention, use_container_width=True)
                else:
                    # Fallback: simple metrics
                    for source, stats in sorted(sources_data.items(), key=lambda x: x[1].get("retention_rate", 0), reverse=True):
                        retention = stats.get("retention_rate", 0.0) * 100
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Source", source[:30] + "..." if len(source) > 30 else source)
                        with col2:
                            st.metric("Retention Rate", f"{retention:.1f}%")
                        with col3:
                            st.metric("Used/Retrieved", f"{stats.get('documents_used_in_response', 0)}/{stats.get('total_documents_retrieved', 0)}")
                        st.markdown("---")
                
                # Source trust scores
                st.markdown("##### Source Trust Scores")
                try:
                    trust_data = get_json(f"/api/meta-learning/source-trust?days={days}", {}, timeout=30)
                    if trust_data and "trust_scores" in trust_data:
                        trust_scores = trust_data["trust_scores"]
                        retention_rates_dict = trust_data.get("retention_rates", {})
                        
                        # Create trust scores table
                        trust_rows = []
                        for source, score in sorted(trust_scores.items(), key=lambda x: x[1], reverse=True):
                            retention = retention_rates_dict.get(source, 0.0) * 100
                            trust_rows.append({
                                "Source": source[:40] + "..." if len(source) > 40 else source,
                                "Trust Score": f"{score:.2f}",
                                "Retention Rate": f"{retention:.1f}%",
                                "Status": "High" if score >= 0.8 else "Medium" if score >= 0.5 else "Low"
                            })
                        
                        if trust_rows and PANDAS_AVAILABLE:
                            df_trust = pd.DataFrame(trust_rows)
                            st.dataframe(df_trust, use_container_width=True)
                        elif trust_rows:
                            for row in trust_rows:
                                st.write(f"**{row['Source']}**: Trust {row['Trust Score']}, Retention {row['Retention Rate']} ({row['Status']})")
                except Exception as e:
                    st.warning(f"Could not load trust scores: {e}")
                
                # Recommended sources
                st.markdown("##### Recommended Sources")
                try:
                    recommended = get_json(f"/api/meta-learning/recommended-sources?days={days}&min_retention=0.20", {}, timeout=30)
                    if recommended and "recommended_sources" in recommended:
                        sources = recommended["recommended_sources"]
                        if sources:
                            for source_info in sources[:10]:  # Top 10
                                source_name = source_info.get("source", "Unknown")
                                retention = source_info.get("retention_rate", 0.0) * 100
                                st.write(f"- **{source_name[:50]}**: {retention:.1f}% retention")
                        else:
                            st.info("No sources meet the minimum retention threshold (20%)")
                except Exception as e:
                    st.warning(f"Could not load recommended sources: {e}")
            else:
                st.info("No retention data available yet. Data will appear after StillMe processes some queries.")
        else:
            st.warning("Could not fetch retention metrics. Make sure backend is running and Stage 2 is enabled.")
    except Exception as e:
        st.error(f"Error loading retention metrics: {e}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())


def _page_meta_learning_curriculum():
    """Phase 2: Curriculum Learning visualization"""
    st.markdown("#### Curriculum Learning")
    st.caption("Analyze learning effectiveness and generate optimal learning order")
    
    # Days selector
    days = st.slider("Analysis Period (days)", 1, 365, 30, key="curriculum_days")
    top_n = st.slider("Top N Topics", 5, 50, 10, key="curriculum_top_n")
    
    # Learning Effectiveness
    st.markdown("##### Learning Effectiveness")
    try:
        effectiveness_data = get_json(f"/api/meta-learning/learning-effectiveness?days={days}&top_n={top_n}", {}, timeout=30)
        
        if effectiveness_data and "effectiveness" in effectiveness_data:
            effectiveness_list = effectiveness_data["effectiveness"]
            
            if effectiveness_list:
                # Prepare data for chart
                topics = []
                improvements = []
                before_rates = []
                after_rates = []
                
                for item in effectiveness_list:
                    topics.append(item.get("topic", "Unknown")[:30])
                    improvements.append(item.get("improvement", 0.0) * 100)
                    before_rates.append(item.get("before_pass_rate", 0.0) * 100)
                    after_rates.append(item.get("after_pass_rate", 0.0) * 100)
                
                if PANDAS_AVAILABLE:
                    df_effectiveness = pd.DataFrame({
                        "Topic": topics,
                        "Improvement (%)": improvements,
                        "Before Pass Rate (%)": before_rates,
                        "After Pass Rate (%)": after_rates,
                        "Source": [item.get("source", "Unknown")[:30] for item in effectiveness_list]
                    })
                    
                    # Sort by improvement
                    df_effectiveness = df_effectiveness.sort_values("Improvement (%)", ascending=False)
                    
                    # Bar chart
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=df_effectiveness["Topic"],
                        y=df_effectiveness["Improvement (%)"],
                        text=[f"+{i:.1f}%" for i in df_effectiveness["Improvement (%)"]],
                        textposition="auto",
                        marker_color=df_effectiveness["Improvement (%)"].apply(
                            lambda x: "green" if x > 0 else "red"
                        )
                    ))
                    fig.update_layout(
                        title="Learning Effectiveness (Validation Pass Rate Improvement)",
                        xaxis_title="Topic",
                        yaxis_title="Improvement (%)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Table
                    st.dataframe(df_effectiveness, use_container_width=True)
                else:
                    # Fallback
                    for item in effectiveness_list:
                        improvement = item.get("improvement", 0.0) * 100
                        st.write(f"**{item.get('topic', 'Unknown')}**: {improvement:+.1f}% improvement")
            else:
                st.info("No learning effectiveness data available yet. Data will appear after StillMe learns and validates responses.")
        else:
            st.warning("Could not fetch learning effectiveness data.")
    except Exception as e:
        st.error(f"Error loading learning effectiveness: {e}")
    
    # Curriculum Recommendations
    st.markdown("##### Curriculum Recommendations")
    try:
        curriculum_data = get_json(f"/api/meta-learning/curriculum?days={days}&max_items=20", {}, timeout=30)
        
        if curriculum_data and "curriculum" in curriculum_data:
            curriculum = curriculum_data["curriculum"]
            
            if curriculum:
                # Display curriculum items
                for i, item in enumerate(curriculum[:20], 1):
                    priority = item.get("priority", 0.0)
                    topic = item.get("topic", "Unknown")
                    source = item.get("source", "Unknown")
                    reason = item.get("reason", "")
                    
                    with st.expander(f"#{i} {topic} (Priority: {priority:.2f})"):
                        st.write(f"**Source**: {source}")
                        st.write(f"**Reason**: {reason}")
                        st.write(f"**Estimated Improvement**: {item.get('estimated_improvement', 0.0):.1%}")
                        st.write(f"**Knowledge Gap Urgency**: {item.get('knowledge_gap_urgency', 0.0):.2f}")
            else:
                st.info("No curriculum recommendations available yet.")
        else:
            st.warning("Could not fetch curriculum data.")
    except Exception as e:
        st.error(f"Error loading curriculum: {e}")


def _page_meta_learning_strategy():
    """Phase 3: Strategy Optimization visualization"""
    st.markdown("#### Strategy Optimization")
    st.caption("Track and optimize strategies (similarity thresholds, keywords, etc.)")
    
    # Days selector
    days = st.slider("Analysis Period (days)", 1, 365, 30, key="strategy_days")
    
    # Strategy Effectiveness
    st.markdown("##### Strategy Effectiveness")
    try:
        strategy_data = get_json(f"/api/meta-learning/strategy-effectiveness?days={days}", {}, timeout=30)
        
        if strategy_data and "strategies" in strategy_data:
            strategies = strategy_data["strategies"]
            
            if strategies:
                # Prepare data
                strategy_names = []
                pass_rates = []
                retention_rates = []
                confidences = []
                
                for name, stats in strategies.items():
                    strategy_names.append(name[:40] + "..." if len(name) > 40 else name)
                    pass_rates.append(stats.get("validation_pass_rate", 0.0) * 100)
                    retention_rates.append(stats.get("retention_rate", 0.0) * 100)
                    confidences.append(stats.get("avg_confidence", 0.0) * 100)
                
                if PANDAS_AVAILABLE:
                    df_strategies = pd.DataFrame({
                        "Strategy": strategy_names,
                        "Pass Rate (%)": pass_rates,
                        "Retention Rate (%)": retention_rates,
                        "Avg Confidence (%)": confidences,
                        "Total Uses": [stats.get("total_uses", 0) for stats in strategies.values()]
                    })
                    
                    # Sort by pass rate
                    df_strategies = df_strategies.sort_values("Pass Rate (%)", ascending=False)
                    
                    # Bar chart
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=df_strategies["Strategy"],
                        y=df_strategies["Pass Rate (%)"],
                        text=[f"{p:.1f}%" for p in df_strategies["Pass Rate (%)"]],
                        textposition="auto"
                    ))
                    fig.update_layout(
                        title="Strategy Effectiveness (Validation Pass Rate)",
                        xaxis_title="Strategy",
                        yaxis_title="Pass Rate (%)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Table
                    st.dataframe(df_strategies, use_container_width=True)
                else:
                    # Fallback
                    for name, stats in sorted(strategies.items(), key=lambda x: x[1].get("validation_pass_rate", 0), reverse=True):
                        pass_rate = stats.get("validation_pass_rate", 0.0) * 100
                        st.write(f"**{name}**: {pass_rate:.1f}% pass rate, {stats.get('total_uses', 0)} uses")
            else:
                st.info("No strategy data available yet. Data will appear after StillMe processes queries with different strategies.")
        else:
            st.warning("Could not fetch strategy effectiveness data.")
    except Exception as e:
        st.error(f"Error loading strategy effectiveness: {e}")
    
    # Optimal Threshold
    st.markdown("##### Optimal Similarity Threshold")
    try:
        threshold_data = get_json(f"/api/meta-learning/optimize-threshold?days={days}", {}, timeout=30)
        
        if threshold_data and "optimal_threshold" in threshold_data:
            optimal = threshold_data["optimal_threshold"]
            analysis = threshold_data.get("analysis", {})
            
            st.metric("Optimal Threshold", f"{optimal:.2f}")
            st.caption(analysis.get("recommendation", ""))
            
            # Show effectiveness comparison if available
            if "effectiveness" in analysis:
                effectiveness = analysis["effectiveness"]
                st.markdown("###### Threshold Comparison")
                for threshold, stats in effectiveness.items():
                    score = stats.get("score", 0.0)
                    pass_rate = stats.get("pass_rate", 0.0)
                    st.write(f"**{threshold}**: Score {score:.2f}, Pass Rate {pass_rate:.1%}")
        else:
            st.warning("Could not fetch optimal threshold data.")
    except Exception as e:
        st.error(f"Error loading optimal threshold: {e}")
    
    # Recommended Strategy
    st.markdown("##### Recommended Strategy")
    try:
        recommended = get_json(f"/api/meta-learning/recommended-strategy?days={days}", {}, timeout=30)
        
        if recommended and "strategy_name" in recommended:
            st.write(f"**Strategy**: {recommended['strategy_name']}")
            st.write(f"**Recommendation**: {recommended.get('recommendation', '')}")
            
            if "effectiveness" in recommended:
                eff = recommended["effectiveness"]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Pass Rate", f"{eff.get('pass_rate', 0.0):.1%}")
                with col2:
                    st.metric("Retention Rate", f"{eff.get('retention_rate', 0.0):.1%}")
                with col3:
                    st.metric("Avg Confidence", f"{eff.get('avg_confidence', 0.0):.1%}")
        else:
            st.info("No recommended strategy available yet.")
    except Exception as e:
        st.error(f"Error loading recommended strategy: {e}")
