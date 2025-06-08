"""
Utility functions for the Strategic Red Team Analyzer application.
"""

import re
import time
from typing import Optional, Dict, Any, List
import streamlit as st

def validate_api_key(api_key: str) -> bool:
    """Validate API key configuration."""
    from config import USE_OPENROUTER, OPENROUTER_API_KEY, ANTHROPIC_API_KEY
    
    # If using OpenRouter, check OpenRouter configuration
    if USE_OPENROUTER:
        return bool(OPENROUTER_API_KEY)
    
    # Otherwise validate Anthropic API key
    effective_key = api_key or ANTHROPIC_API_KEY
    if not effective_key:
        return False
    
    # Basic format validation for Anthropic API keys
    # They typically start with 'sk-ant-' and are followed by alphanumeric characters
    pattern = r'^sk-ant-[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, effective_key))

def format_analysis_time(seconds: float) -> str:
    """Format analysis time in a human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"

def truncate_text(text: str, max_length: int = 150) -> str:
    """Truncate text to a maximum length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + "..."

def format_confidence_color(score: float) -> str:
    """Return a color based on confidence score."""
    if score >= 0.8:
        return "#28a745"  # Green
    elif score >= 0.6:
        return "#ffc107"  # Yellow
    else:
        return "#dc3545"  # Red

def calculate_overall_confidence(results: Dict[str, Any]) -> float:
    """Calculate overall confidence from multiple analysis results."""
    if not results:
        return 0.0
    
    scores = [result.confidence_score for result in results.values() if hasattr(result, 'confidence_score')]
    if not scores:
        return 0.0
    
    # Weighted average (could be enhanced with perspective-specific weights)
    return sum(scores) / len(scores)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    return filename

def extract_key_phrases(text: str, max_phrases: int = 5) -> List[str]:
    """Extract key phrases from text using simple heuristics."""
    # This is a simplified implementation
    # In production, you might use NLP libraries like spaCy or NLTK
    
    sentences = text.split('.')
    phrases = []
    
    for sentence in sentences[:max_phrases]:
        sentence = sentence.strip()
        if len(sentence) > 20 and len(sentence) < 100:
            phrases.append(sentence)
    
    return phrases[:max_phrases]

def create_progress_tracker(total_steps: int):
    """Create a progress tracking context manager."""
    class ProgressTracker:
        def __init__(self, total):
            self.total = total
            self.current = 0
            self.progress_bar = st.progress(0)
            self.status_text = st.empty()
        
        def update(self, step_name: str):
            self.current += 1
            progress = self.current / self.total
            self.progress_bar.progress(progress)
            self.status_text.text(f"Step {self.current}/{self.total}: {step_name}")
        
        def complete(self):
            self.progress_bar.progress(1.0)
            self.status_text.text("Analysis complete!")
            time.sleep(1)  # Brief pause to show completion
            self.progress_bar.empty()
            self.status_text.empty()
    
    return ProgressTracker(total_steps)

def format_list_for_display(items: List[str], max_items: int = 3) -> str:
    """Format a list of items for compact display."""
    if not items:
        return "None"
    
    if len(items) <= max_items:
        return ", ".join(items)
    else:
        displayed = ", ".join(items[:max_items])
        remaining = len(items) - max_items
        return f"{displayed}, and {remaining} more"

def calculate_text_readability_score(text: str) -> float:
    """Calculate a simple readability score (0-1, higher is more readable)."""
    if not text:
        return 0.0
    
    # Simple metrics: shorter sentences and common words are more readable
    sentences = text.split('.')
    avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
    
    # Penalize very long sentences
    sentence_score = max(0, 1 - (avg_sentence_length - 15) / 20)
    
    # Simple vocabulary check (this is very basic)
    words = text.lower().split()
    complex_words = sum(1 for word in words if len(word) > 8)
    vocab_score = max(0, 1 - complex_words / len(words)) if words else 0
    
    return (sentence_score + vocab_score) / 2

def generate_summary_stats(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary statistics from analysis results."""
    if not analysis_results:
        return {}
    
    total_perspectives = len(analysis_results)
    avg_confidence = calculate_overall_confidence(analysis_results)
    
    # Count insights and recommendations
    total_insights = sum(
        len(result.key_insights) for result in analysis_results.values()
        if hasattr(result, 'key_insights')
    )
    
    total_recommendations = sum(
        len(result.recommendations) for result in analysis_results.values()
        if hasattr(result, 'recommendations')
    )
    
    # Identify highest/lowest confidence perspectives
    confidence_scores = {
        perspective: result.confidence_score 
        for perspective, result in analysis_results.items()
        if hasattr(result, 'confidence_score')
    }
    
    highest_confidence = max(confidence_scores.items(), key=lambda x: x[1]) if confidence_scores else None
    lowest_confidence = min(confidence_scores.items(), key=lambda x: x[1]) if confidence_scores else None
    
    return {
        "total_perspectives": total_perspectives,
        "average_confidence": avg_confidence,
        "total_insights": total_insights,
        "total_recommendations": total_recommendations,
        "highest_confidence_perspective": highest_confidence,
        "lowest_confidence_perspective": lowest_confidence,
        "analysis_breadth_score": min(1.0, total_perspectives / 7)  # 7 is max perspectives
    }

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_perspective_descriptions() -> Dict[str, str]:
    """Get cached perspective descriptions for UI."""
    from config import RED_TEAM_PERSPECTIVES
    return {
        key: info.get('description', '') 
        for key, info in RED_TEAM_PERSPECTIVES.items()
    }

def validate_strategy_input(text: str) -> tuple[bool, str]:
    """Validate strategy input text."""
    if not text or not text.strip():
        return False, "Please enter a strategy to analyze."
    
    if len(text.strip()) < 50:
        return False, "Strategy description should be at least 50 characters for meaningful analysis."
    
    if len(text) > 10000:
        return False, "Strategy description is too long. Please keep it under 10,000 characters."
    
    # Check for potentially sensitive content (basic check)
    sensitive_patterns = [
        r'\b(password|api[_\s]?key|secret|token)\b',
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email pattern
    ]
    
    for pattern in sensitive_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, "Please remove any sensitive information (passwords, API keys, emails) from your strategy description."
    
    return True, ""