"""
Synchronous OpenRouter client using requests library for better SSL compatibility.
Fallback option when aiohttp has SSL issues.
"""

import requests
import json
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class OpenRouterResponse:
    """Structure for OpenRouter API responses."""
    content: List[Dict[str, Any]]

class SyncOpenRouterClient:
    """Synchronous OpenRouter client with SSL compatibility."""
    
    def __init__(
        self, 
        api_key: str, 
        site_url: str = "", 
        site_name: str = "Strategic Red Team Analyzer"
    ):
        self.api_key = api_key
        self.site_url = site_url
        self.site_name = site_name
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def messages_create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system: str = ""
    ) -> OpenRouterResponse:
        """Create a message using OpenRouter API (synchronous)."""
        
        # Convert Anthropic-style messages to OpenRouter format
        openrouter_messages = []
        
        # Add system message if provided
        if system:
            openrouter_messages.append({
                "role": "system",
                "content": system
            })
        
        # Convert user messages
        for message in messages:
            openrouter_messages.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        # Prepare request data
        request_data = {
            "model": model,
            "messages": openrouter_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Add optional headers
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            headers["X-Title"] = self.site_name
        
        try:
            # Make the request with SSL verification disabled if needed
            response = requests.post(
                self.base_url,
                headers=headers,
                json=request_data,
                timeout=120,
                verify=True  # Try with SSL verification first
            )
            
        except requests.exceptions.SSLError:
            print("⚠️  SSL verification failed, retrying without verification...")
            # Retry without SSL verification
            response = requests.post(
                self.base_url,
                headers=headers,
                json=request_data,
                timeout=120,
                verify=False
            )
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter API error {response.status_code}: {response.text}")
        
        response_data = response.json()
        
        # Check for API errors
        if "error" in response_data:
            error_msg = response_data["error"].get("message", "Unknown error")
            raise Exception(f"OpenRouter API error: {error_msg}")
        
        # Convert response to Anthropic-compatible format
        if "choices" in response_data and len(response_data["choices"]) > 0:
            content_text = response_data["choices"][0]["message"]["content"]
            return OpenRouterResponse(content=[{"text": content_text}])
        else:
            raise Exception("No response content received from OpenRouter API")

class AsyncSyncOpenRouterClient:
    """Async wrapper for sync OpenRouter client."""
    
    def __init__(
        self, 
        api_key: str, 
        site_url: str = "", 
        site_name: str = "Strategic Red Team Analyzer"
    ):
        self.client = SyncOpenRouterClient(api_key, site_url, site_name)
    
    async def messages_create(self, **kwargs):
        """Async wrapper for sync message creation."""
        # Run the sync function in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.client.messages_create(**kwargs))