"""Configuration settings for the Strategic Red Team Analyzer."""

import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
USE_OPENROUTER = os.getenv("USE_OPENROUTER", "false").lower() == "true"

# Model configuration
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"  # Fallback for direct Anthropic API
OPENROUTER_MODEL = "google/gemini-2.5-pro-preview-05-06"  # Gemini 2.5 Pro via OpenRouter
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "")
OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", "Strategic Red Team Analyzer")

# Application Configuration
APP_TITLE = "Strategic Red Team Analyzer"
APP_DESCRIPTION = """
Comprehensive strategy analysis and red teaming tool using multiple Gemini 2.5 Pro perspectives 
to challenge assumptions, identify risks, and strengthen strategic thinking.
"""

# Analysis Configuration
MAX_RETRIES = 5  # Increased for OpenRouter reliability
REQUEST_TIMEOUT = 120  # Longer timeout for OpenRouter
RATE_LIMIT_DELAY = 2  # Longer delay between requests

# Red Team Perspectives
RED_TEAM_PERSPECTIVES = {
    "devils_advocate": {
        "name": "Devil's Advocate",
        "icon": "😈",
        "description": "Aggressive challenge of assumptions and weaknesses",
        "enabled": True
    },
    "systems_thinker": {
        "name": "Systems Thinker", 
        "icon": "🔄",
        "description": "Analyze interconnections, feedback loops, unintended consequences",
        "enabled": True
    },
    "historical_analyst": {
        "name": "Historical Analyst",
        "icon": "📚",
        "description": "Compare to past similar strategies/failures",
        "enabled": True
    },
    "stakeholder_advocate": {
        "name": "Stakeholder Advocate",
        "icon": "👥",
        "description": "Represent different stakeholder concerns",
        "enabled": True
    },
    "risk_assessment": {
        "name": "Risk Assessment",
        "icon": "⚠️",
        "description": "Identify failure modes and mitigation strategies",
        "enabled": True
    },
    "resource_realist": {
        "name": "Resource Realist",
        "icon": "💰",
        "description": "Challenge feasibility and resource requirements",
        "enabled": True
    },
    "market_forces": {
        "name": "Market Forces",
        "icon": "📈",
        "description": "Competitive and economic pressures analysis",
        "enabled": True
    }
}

# Mental Model Frameworks
MENTAL_MODELS = {
    "first_principles": "First Principles Thinking",
    "inversion": "Inversion (what could go wrong)",
    "second_order": "Second/Third Order Effects",
    "opportunity_cost": "Opportunity Cost Analysis",
    "base_rate": "Base Rate Neglect",
    "confirmation_bias": "Confirmation Bias Detection",
    "strategic_options": "Strategic Options Theory"
}

# UI Configuration
SIDEBAR_WIDTH = 300
MAX_TEXT_LENGTH = 10000
CONFIDENCE_THRESHOLD = 0.7

# Search and RAG Configuration
ENABLE_SEARCH_BY_DEFAULT = True
SEARCH_CACHE_HOURS = 24
MAX_SEARCH_RESULTS = 5
MEMORY_RETENTION_DAYS = 30