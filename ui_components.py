"""
UI Components for the Strategic Red Team Analyzer
Modular components for clean separation of UI logic.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
import re

from config import RED_TEAM_PERSPECTIVES, MENTAL_MODELS, CONFIDENCE_THRESHOLD
from red_team_analyzer import AnalysisResult
from export_utils import export_to_pdf, export_to_markdown

def markdown_to_html(text: str) -> str:
    """Convert markdown formatting to HTML for rich text display."""
    if not text:
        return text
    
    # Convert markdown to HTML
    # Bold text
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__([^_]+)__', r'<b>\1</b>', text)
    
    # Italic text
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    text = re.sub(r'_([^_]+)_', r'<i>\1</i>', text)
    
    # Code blocks
    text = re.sub(r'```([^`]+)```', r'<pre>\1</pre>', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Headers
    text = re.sub(r'^### ([^\n]+)', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## ([^\n]+)', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# ([^\n]+)', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Lists
    text = re.sub(r'^- ([^\n]+)', r'• \1', text, flags=re.MULTILINE)
    text = re.sub(r'^\* ([^\n]+)', r'• \1', text, flags=re.MULTILINE)
    
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    # Line breaks
    text = text.replace('\n', '<br>')
    
    return text

def render_rich_text(text: str, key: str = None):
    """Render text with rich formatting."""
    if not text:
        return
    
    # Clean and format the text
    html_text = markdown_to_html(text)
    
    # Use st.markdown with unsafe_allow_html for rich display
    # Note: st.markdown doesn't accept a key parameter
    st.markdown(html_text, unsafe_allow_html=True)

def render_sidebar() -> tuple:
    """Render the application sidebar with controls."""
    st.sidebar.header("🎯 Analysis Configuration")
    
    # API Key input
    api_key = st.sidebar.text_input(
        "Anthropic API Key",
        type="password",
        help="Enter your Anthropic API key to enable analysis"
    )
    
    st.sidebar.markdown("---")
    
    # Perspective selection
    st.sidebar.subheader("🔍 Red Team Perspectives")
    st.sidebar.caption("Select which analytical perspectives to apply:")
    
    selected_perspectives = []
    
    # Create two columns for perspective checkboxes
    col1, col2 = st.sidebar.columns(2)
    
    perspectives_list = list(RED_TEAM_PERSPECTIVES.keys())
    mid_point = len(perspectives_list) // 2
    
    with col1:
        for key in perspectives_list[:mid_point]:
            info = RED_TEAM_PERSPECTIVES[key]
            if st.checkbox(
                f"{info['icon']} {info['name']}", 
                value=info['enabled'],
                key=f"perspective_{key}",
                help=info['description']
            ):
                selected_perspectives.append(key)
    
    with col2:
        for key in perspectives_list[mid_point:]:
            info = RED_TEAM_PERSPECTIVES[key]
            if st.checkbox(
                f"{info['icon']} {info['name']}", 
                value=info['enabled'],
                key=f"perspective_{key}",
                help=info['description']
            ):
                selected_perspectives.append(key)
    
    # Quick select options
    col_all, col_none = st.sidebar.columns(2)
    if col_all.button("Select All", key="select_all_perspectives"):
        st.rerun()
    if col_none.button("Select None", key="select_none_perspectives"):
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Mental model selection
    st.sidebar.subheader("🧠 Mental Model Frameworks")
    st.sidebar.caption("Choose cognitive frameworks to apply:")
    
    selected_models = []
    for key, name in MENTAL_MODELS.items():
        if st.sidebar.checkbox(name, key=f"model_{key}"):
            selected_models.append(key)
    
    st.sidebar.markdown("---")
    
    # Analysis settings
    st.sidebar.subheader("⚙️ Settings")
    
    # Advanced options expander
    with st.sidebar.expander("Advanced Options"):
        enable_search = st.checkbox(
            "Enable Internet Search & RAG",
            value=True,
            help="Use internet search to gather additional context for analysis"
        )
        
        temperature = st.slider(
            "Analysis Creativity",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Higher values = more creative analysis"
        )
        
        max_tokens = st.selectbox(
            "Response Length",
            options=[2000, 4000, 6000],
            index=1,
            help="Maximum tokens per analysis"
        )
        
        parallel_requests = st.selectbox(
            "Concurrent Analyses",
            options=[1, 2, 3],
            index=2,
            help="Number of parallel API requests"
        )
    
    return selected_perspectives, selected_models, api_key, enable_search

def render_confidence_badge(score: float) -> str:
    """Render a confidence score badge."""
    if score >= 0.8:
        return f'<span class="confidence-score confidence-high">High Confidence ({score:.1%})</span>'
    elif score >= 0.6:
        return f'<span class="confidence-score confidence-medium">Medium Confidence ({score:.1%})</span>'
    else:
        return f'<span class="confidence-score confidence-low">Low Confidence ({score:.1%})</span>'

def render_analysis_results(results: Dict[str, AnalysisResult]):
    """Render the analysis results section."""
    st.subheader("📊 Red Team Analysis Results")
    
    if not results:
        st.info("No analysis results to display.")
        return
    
    # Create confidence score visualization
    confidence_data = []
    for perspective, result in results.items():
        perspective_info = RED_TEAM_PERSPECTIVES.get(perspective, {})
        confidence_data.append({
            'Perspective': perspective_info.get('name', perspective),
            'Confidence': result.confidence_score,
            'Icon': perspective_info.get('icon', '•')
        })
    
    df_confidence = pd.DataFrame(confidence_data)
    
    # Confidence scores chart
    fig = px.bar(
        df_confidence,
        x='Perspective',
        y='Confidence',
        title="Analysis Confidence Scores by Perspective",
        color='Confidence',
        color_continuous_scale='RdYlGn',
        range_color=[0, 1]
    )
    fig.update_layout(height=400, xaxis_tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Individual perspective results
    for perspective, result in results.items():
        perspective_info = RED_TEAM_PERSPECTIVES.get(perspective, {})
        
        with st.expander(
            f"{perspective_info.get('icon', '•')} {perspective_info.get('name', perspective)} Analysis",
            expanded=True
        ):
            # Confidence and metadata
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(
                    render_confidence_badge(result.confidence_score),
                    unsafe_allow_html=True
                )
            with col2:
                st.caption(f"Analyzed: {result.timestamp}")
            with col3:
                st.caption(f"Perspective: {perspective_info.get('name', perspective)}")
            
            # Main analysis
            st.markdown("**Analysis:**")
            render_rich_text(result.analysis)
            
            # Key insights
            if result.key_insights:
                st.markdown("**Key Insights:**")
                for insight in result.key_insights:
                    render_rich_text(f"• {insight}")
            
            # Recommendations
            if result.recommendations:
                st.markdown("**Recommendations:**")
                for rec in result.recommendations:
                    render_rich_text(f"→ {rec}")

def render_synthesis_section(synthesis: Dict[str, Any]):
    """Render the synthesis and recommendations section."""
    st.markdown("---")
    st.subheader("🔗 Strategic Synthesis & Recommendations")
    
    if not synthesis:
        st.info("No synthesis available.")
        return
    
    # Check if this is a fallback synthesis
    if '_synthesis_note' in synthesis:
        st.warning(f"⚠️ Synthesis Note: {synthesis['_synthesis_note']}")
    
    # Executive Summary
    if 'executive_summary' in synthesis:
        st.markdown("### 📋 Executive Summary")
        st.info(synthesis['executive_summary'])
    
    # Overall assessment metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'confidence_assessment' in synthesis:
            confidence = synthesis['confidence_assessment']
            st.metric(
                "Overall Confidence", 
                f"{confidence:.1%}",
                delta=None
            )
    
    with col2:
        if 'consensus_level' in synthesis:
            st.metric(
                "Consensus Level",
                synthesis['consensus_level'],
                delta=None
            )
    
    with col3:
        if 'implementation_difficulty' in synthesis:
            st.metric(
                "Implementation Difficulty",
                synthesis['implementation_difficulty'],
                delta=None
            )
    
    # Create tabs for different synthesis sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Critical Insights",
        "📋 Priority Actions", 
        "⚠️ Risk Mitigation",
        "🗺️ Implementation",
        "🔍 Validation"
    ])
    
    with tab1:
        if 'critical_insights' in synthesis:
            st.markdown("**Most Critical Strategic Insights:**")
            for i, insight in enumerate(synthesis['critical_insights'], 1):
                render_rich_text(f"{i}. {insight}")
        
        if 'key_assumptions_to_validate' in synthesis:
            st.markdown("**Key Assumptions to Validate:**")
            for i, assumption in enumerate(synthesis['key_assumptions_to_validate']):
                st.warning(f"⚠️ {assumption}")
    
    with tab2:
        if 'priority_recommendations' in synthesis:
            st.markdown("**Priority Recommendations:**")
            for i, rec in enumerate(synthesis['priority_recommendations'], 1):
                st.success(f"{i}. {rec}")
        
        if 'alternative_approaches' in synthesis:
            st.markdown("**Alternative Approaches to Consider:**")
            for alt in synthesis['alternative_approaches']:
                st.info(f"💡 {alt}")
    
    with tab3:
        if 'risk_mitigation' in synthesis:
            st.markdown("**Risk Mitigation Strategies:**")
            for risk in synthesis['risk_mitigation']:
                st.error(f"🛡️ {risk}")
    
    with tab4:
        if 'implementation_roadmap' in synthesis:
            st.markdown("**Implementation Roadmap:**")
            for phase in synthesis['implementation_roadmap']:
                st.write(f"📍 {phase}")
        
        if 'success_metrics' in synthesis:
            st.markdown("**Success Metrics to Track:**")
            for metric in synthesis['success_metrics']:
                st.write(f"📊 {metric}")
    
    with tab5:
        if 'key_assumptions_to_validate' in synthesis:
            st.markdown("**Key Assumptions to Validate:**")
            for assumption in synthesis['key_assumptions_to_validate']:
                st.warning(f"🔍 {assumption}")
        
        if 'alternative_approaches' in synthesis:
            st.markdown("**Alternative Approaches to Consider:**")
            for alt in synthesis['alternative_approaches']:
                st.info(f"💡 {alt}")

def render_memory_management_section():
    """Render the memory management section."""
    st.markdown("---")
    st.subheader("🧠 Context Memory Management")
    
    try:
        from search_rag import SearchAndRAG
        search_rag = SearchAndRAG()
        
        # Get memory statistics
        stats = search_rag.get_memory_stats()
        
        if stats['total_items'] > 0:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Context Items", stats['total_items'])
            
            with col2:
                st.metric("Categories", len(stats['categories']))
            
            with col3:
                oldest_days = (datetime.now() - stats['oldest_item']).days
                st.metric("Oldest Item (days)", oldest_days)
            
            # Category breakdown
            if stats['categories']:
                st.markdown("**Context Categories:**")
                for category, count in stats['categories'].items():
                    st.write(f"• {category}: {count} items")
            
            # Memory management controls
            col_clear, col_manage = st.columns(2)
            
            with col_clear:
                if st.button("🗑️ Clear Old Memory (30+ days)"):
                    search_rag.clear_old_memory(days_old=30)
                    st.success("Old memory cleared!")
                    st.rerun()
            
            with col_manage:
                days_to_clear = st.selectbox(
                    "Clear memory older than:",
                    [7, 14, 30, 60, 90],
                    index=2
                )
                if st.button(f"Clear {days_to_clear}+ day old memory"):
                    search_rag.clear_old_memory(days_old=days_to_clear)
                    st.success(f"Memory older than {days_to_clear} days cleared!")
                    st.rerun()
        else:
            st.info("No context memory stored yet. Memory will be built as you perform analyses with search enabled.")
    
    except Exception as e:
        st.warning(f"Memory management not available: {e}")

def render_synthesis_section_continued(synthesis: Dict[str, Any]):
    """Continue rendering synthesis section - separated due to edit conflict."""
    # Overall confidence assessment
    if 'confidence_assessment' in synthesis:
        confidence = synthesis['confidence_assessment']
        st.markdown("### 🎯 Overall Strategic Confidence")
        
        # Create confidence gauge
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = confidence * 100,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Strategic Confidence Score"},
            delta = {'reference': 70},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

def render_export_section(
    strategy: str, 
    analysis_results: Dict[str, AnalysisResult],
    synthesis: Dict[str, Any] = None
):
    """Render the export functionality section."""
    st.markdown("---")
    st.subheader("📁 Export Analysis")
    
    if not analysis_results:
        st.info("Complete an analysis to enable export functionality.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export to PDF", type="secondary"):
            try:
                pdf_data = export_to_pdf(strategy, analysis_results, synthesis)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"red_team_analysis_{timestamp}.pdf"
                
                st.download_button(
                    label="Download PDF",
                    data=pdf_data,
                    file_name=filename,
                    mime="application/pdf"
                )
                st.success("PDF export ready!")
            except Exception as e:
                st.error(f"PDF export failed: {str(e)}")
    
    with col2:
        if st.button("📝 Export to Markdown", type="secondary"):
            try:
                md_content = export_to_markdown(strategy, analysis_results, synthesis)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"red_team_analysis_{timestamp}.md"
                
                st.download_button(
                    label="Download Markdown",
                    data=md_content,
                    file_name=filename,
                    mime="text/markdown"
                )
                st.success("Markdown export ready!")
            except Exception as e:
                st.error(f"Markdown export failed: {str(e)}")
    
    with col3:
        if st.button("📊 Export Data", type="secondary"):
            try:
                # Create JSON export of all data
                export_data = {
                    "strategy": strategy,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "analysis_results": {
                        k: {
                            "perspective": v.perspective,
                            "analysis": v.analysis,
                            "confidence_score": v.confidence_score,
                            "key_insights": v.key_insights,
                            "recommendations": v.recommendations,
                            "timestamp": v.timestamp
                        } for k, v in analysis_results.items()
                    },
                    "synthesis": synthesis or {}
                }
                
                import json
                json_content = json.dumps(export_data, indent=2)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"red_team_analysis_{timestamp}.json"
                
                st.download_button(
                    label="Download JSON",
                    data=json_content,
                    file_name=filename,
                    mime="application/json"
                )
                st.success("JSON export ready!")
            except Exception as e:
                st.error(f"JSON export failed: {str(e)}")