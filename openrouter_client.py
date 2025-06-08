"""
OpenRouter API client for accessing Claude Opus 4 and other models.
Provides compatibility with the existing Anthropic API interface.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class OpenRouterMessage:
    """Structure for OpenRouter API messages."""
    role: str
    content: str

@dataclass
class OpenRouterResponse:
    """Structure for OpenRouter API responses."""
    content: List[Dict[str, Any]]

class OpenRouterClient:
    """OpenRouter API client with Anthropic-compatible interface."""
    
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
    
    async def messages_create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system: str = ""
    ) -> OpenRouterResponse:
        """Create a message using OpenRouter API with Anthropic-compatible interface."""
        
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
        
        # Make the API request with SSL handling
        import ssl
        
        # Create SSL context that's more permissive
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(
                self.base_url,
                headers=headers,
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error {response.status}: {error_text}")
                
                response_data = await response.json()
                
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

class AsyncOpenRouterClient:
    """Async wrapper for OpenRouter client to match AsyncAnthropic interface."""
    
    def __init__(
        self, 
        api_key: str, 
        site_url: str = "", 
        site_name: str = "Strategic Red Team Analyzer"
    ):
        self.client = OpenRouterClient(api_key, site_url, site_name)
        self.messages = self.client
    
    async def messages_create(self, **kwargs):
        """Async message creation."""
        return await self.client.messages_create(**kwargs)