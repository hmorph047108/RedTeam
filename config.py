"""Configuration settings for the Strategic Red Team Analyzer."""

import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-3-opus-20240229"  # Claude Opus 4

# Application Configuration
APP_TITLE = "Strategic Red Team Analyzer"
APP_DESCRIPTION = """
Comprehensive strategy analysis and red teaming tool using multiple Claude Opus 4 perspectives 
to challenge assumptions, identify risks, and strengthen strategic thinking.
"""

# Analysis Configuration
MAX_RETRIES = 3
REQUEST_TIMEOUT = 60
RATE_LIMIT_DELAY = 1

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