#!/usr/bin/env python3
"""
Simple API test script to validate Anthropic API connection and model availability.
Run this to troubleshoot API issues before using the main application.
"""

import asyncio
import os
from dotenv import load_dotenv
from anthropic import AsyncAnthropic
from openrouter_client import AsyncOpenRouterClient

# Load environment variables
load_dotenv()

async def test_openrouter_connection():
    """Test OpenRouter API connection."""
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    if not openrouter_key:
        print("❌ No OpenRouter API key found.")
        return False
    
    print(f"✅ OpenRouter API key found: {openrouter_key[:10]}...")
    
    try:
        client = AsyncOpenRouterClient(api_key=openrouter_key)
        
        print(f"\n🧪 Testing OpenRouter with Claude Opus 4")
        
        response = await client.messages_create(
            model="anthropic/claude-opus-4",
            max_tokens=100,
            messages=[{"role": "user", "content": "Hello! Please respond with 'OpenRouter API test successful' if you can read this."}]
        )
        
        print(f"✅ Claude Opus 4 via OpenRouter: {response.content[0]['text'].strip()}")
        return "anthropic/claude-opus-4"
        
    except Exception as e:
        print(f"❌ OpenRouter test failed: {str(e)}")
        return False

async def test_anthropic_connection():
    """Test direct Anthropic API connection."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("❌ No Anthropic API key found.")
        return False
    
    print(f"✅ Anthropic API key found: {api_key[:10]}...")
    
    # Test with different model names
    models_to_test = [
        "claude-3-5-sonnet-20241022",  # Current stable
        "claude-3-5-sonnet-20240620",  # Previous version
        "claude-3-opus-20240229",     # Opus
        "claude-3-sonnet-20240229",   # Sonnet
    ]
    
    client = AsyncAnthropic(api_key=api_key)
    
    for model in models_to_test:
        try:
            print(f"\n🧪 Testing model: {model}")
            
            response = await client.messages.create(
                model=model,
                max_tokens=100,
                messages=[{"role": "user", "content": "Hello! Please respond with 'API test successful' if you can read this."}]
            )
            
            print(f"✅ {model}: {response.content[0].text.strip()}")
            return model  # Return the first working model
            
        except Exception as e:
            print(f"❌ {model}: {str(e)}")
            continue
    
    print("\n❌ No working models found. Please check your API key and try again.")
    return False

async def main():
    """Main test function."""
    print("🔬 API Connection Test - Strategic Red Team Analyzer")
    print("=" * 60)
    
    # Test OpenRouter first (preferred for Claude Opus 4)
    print("\n🚀 Testing OpenRouter API (Claude Opus 4)")
    openrouter_result = await test_openrouter_connection()
    
    # Test Anthropic API as fallback
    print("\n🔧 Testing Direct Anthropic API")
    anthropic_result = await test_anthropic_connection()
    
    # Provide recommendations
    print("\n" + "=" * 60)
    if openrouter_result:
        print("🎉 RECOMMENDED: Use OpenRouter for Claude Opus 4")
        print("Add to your .env file:")
        print("USE_OPENROUTER=true")
        print(f"OPENROUTER_API_KEY=your_key_here")
    elif anthropic_result:
        print("✅ Direct Anthropic API working")
        print(f"Use model: {anthropic_result}")
        print("Add to your .env file:")
        print("USE_OPENROUTER=false")
        print(f"ANTHROPIC_API_KEY=your_key_here")
    else:
        print("❌ No working API found")
        print("\n🔧 Troubleshooting:")
        print("1. Check API keys at openrouter.ai or console.anthropic.com")
        print("2. Ensure sufficient credits")
        print("3. Try again in a few minutes")

if __name__ == "__main__":
    asyncio.run(main())