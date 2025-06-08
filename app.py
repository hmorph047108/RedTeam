"""
Strategic Red Team Analyzer - Main Streamlit Application
A comprehensive strategy analysis tool using multiple Claude Opus 4 perspectives.
"""

import streamlit as st
import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime

from config import (
    APP_TITLE, APP_DESCRIPTION, RED_TEAM_PERSPECTIVES, 
    MENTAL_MODELS, MAX_TEXT_LENGTH
)
from red_team_analyzer import RedTeamAnalyzer
from ui_components import (
    render_sidebar, render_analysis_results, 
    render_synthesis_section, render_export_section,
    render_memory_management_section
)
from utils import validate_api_key, format_analysis_time

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .perspective-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .confidence-score {
        display: inline-block;
        padding: 0.2rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .confidence-high { background-color: #d4edda; color: #155724; }
    .confidence-medium { background-color: #fff3cd; color: #856404; }
    .confidence-low { background-color: #f8d7da; color: #721c24; }
    .analysis-section {
        margin-bottom: 2rem;
        padding: 1rem;
        border-left: 4px solid #1f77b4;
        background-color: #f8f9fa;
    }
    .stButton > button {
        width: 100%;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'synthesis_complete' not in st.session_state:
        st.session_state.synthesis_complete = False

def main():
    """Main application function."""
    initialize_session_state()
    
    # Header
    st.markdown(f'<h1 class="main-header">{APP_TITLE}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{APP_DESCRIPTION}</p>', unsafe_allow_html=True)
    
    # Sidebar
    selected_perspectives, selected_models, api_key, enable_search = render_sidebar()
    
    # Validate API configuration
    if not validate_api_key(api_key):
        from config import USE_OPENROUTER
        if USE_OPENROUTER:
            st.error("❌ OpenRouter API key not configured. Please check your .env file.")
        else:
            st.error("❌ Please enter a valid Anthropic API key in the sidebar to begin analysis.")
        st.stop()
    
    # Initialize analyzer
    if st.session_state.analyzer is None:
        try:
            st.session_state.analyzer = RedTeamAnalyzer(api_key, enable_search=enable_search)
        except Exception as e:
            st.error(f"❌ Failed to initialize analyzer: {str(e)}")
            st.stop()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Strategy Input")
        
        # Strategy input
        strategy_text = st.text_area(
            "Enter your strategy, idea, or plan for analysis:",
            height=200,
            max_chars=MAX_TEXT_LENGTH,
            placeholder="Describe your strategy, business plan, project proposal, or any idea you'd like to analyze from multiple perspectives..."
        )
        
        # Analysis controls
        col_analyze, col_clear = st.columns([3, 1])
        
        with col_analyze:
            analyze_button = st.button(
                "🎯 Start Red Team Analysis",
                type="primary",
                disabled=not strategy_text.strip()
            )
        
        with col_clear:
            if st.button("🗑️ Clear"):
                st.session_state.analysis_results = {}
                st.session_state.analysis_complete = False
                st.session_state.synthesis_complete = False
                st.rerun()
    
    with col2:
        st.subheader("📊 Analysis Status")
        
        if selected_perspectives:
            st.write(f"**Selected Perspectives:** {len(selected_perspectives)}")
            for perspective in selected_perspectives:
                info = RED_TEAM_PERSPECTIVES.get(perspective, {})
                st.write(f"{info.get('icon', '•')} {info.get('name', perspective)}")
        else:
            st.warning("⚠️ Please select at least one perspective in the sidebar.")
        
        if selected_models:
            st.write(f"**Mental Models:** {len(selected_models)}")
            for model in selected_models[:3]:  # Show first 3
                st.write(f"• {MENTAL_MODELS.get(model, model)}")
            if len(selected_models) > 3:
                st.write(f"• ... and {len(selected_models) - 3} more")
    
    # Run analysis
    if analyze_button and strategy_text.strip() and selected_perspectives:
        with st.spinner("🔍 Running comprehensive red team analysis..."):
            start_time = time.time()
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Run analysis
                results = asyncio.run(
                    st.session_state.analyzer.analyze_strategy(
                        strategy_text,
                        selected_perspectives,
                        selected_models,
                        progress_callback=lambda p, s: (
                            progress_bar.progress(p),
                            status_text.text(s)
                        )
                    )
                )
                
                st.session_state.analysis_results = results
                st.session_state.analysis_complete = True
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                analysis_time = time.time() - start_time
                st.success(f"✅ Analysis completed in {format_analysis_time(analysis_time)}")
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                progress_bar.empty()
                status_text.empty()
    
    # Display results
    if st.session_state.analysis_complete and st.session_state.analysis_results:
        st.markdown("---")
        
        # Analysis results
        render_analysis_results(st.session_state.analysis_results)
        
        # Synthesis section
        if st.button("🔗 Generate Synthesis & Recommendations"):
            with st.spinner("🧠 Synthesizing insights and generating recommendations..."):
                try:
                    synthesis = asyncio.run(
                        st.session_state.analyzer.synthesize_results(
                            strategy_text,
                            st.session_state.analysis_results
                        )
                    )
                    st.session_state.synthesis_results = synthesis
                    st.session_state.synthesis_complete = True
                    st.success("✅ Synthesis completed!")
                except Exception as e:
                    st.error(f"❌ Synthesis failed: {str(e)}")
        
        # Display synthesis
        if st.session_state.synthesis_complete and 'synthesis_results' in st.session_state:
            render_synthesis_section(st.session_state.synthesis_results)
        
        # Export section
        render_export_section(
            strategy_text,
            st.session_state.analysis_results,
            st.session_state.get('synthesis_results', {})
        )
        
        # Memory management section (if search is enabled)
        if enable_search:
            render_memory_management_section()

if __name__ == "__main__":
    main()