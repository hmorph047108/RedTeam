#!/usr/bin/env python3
"""
Quick launcher script for the Strategic Red Team Analyzer.
Run this script to start the Streamlit application with proper configuration.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import streamlit
        import anthropic
        import plotly
        import reportlab
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def check_api_key():
    """Check if API key is configured."""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print("✅ API key found in environment")
        return True
    else:
        print("⚠️  No API key found in .env file")
        print("You can still enter it in the application sidebar")
        return False

def main():
    """Main launcher function."""
    print("🎯 Strategic Red Team Analyzer")
    print("=" * 50)
    
    # Check current directory
    if not Path("app.py").exists():
        print("❌ app.py not found. Please run this script from the RedTeam directory.")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check API key
    check_api_key()
    
    # Launch Streamlit
    print("\n🚀 Starting Strategic Red Team Analyzer...")
    print("📱 The application will open in your default web browser")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "false",
            "--server.address", "localhost",
            "--server.port", "8501"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()