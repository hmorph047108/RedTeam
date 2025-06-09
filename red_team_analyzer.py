"""
Red Team Analyzer - Core analysis engine using Gemini 2.5 Pro API
Implements chained API calls for comprehensive strategy analysis.
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
import json
import time
from tenacity import retry, stop_after_attempt, wait_exponential

from anthropic import AsyncAnthropic
from config import (
    CLAUDE_MODEL, MAX_RETRIES, REQUEST_TIMEOUT, RATE_LIMIT_DELAY, RED_TEAM_PERSPECTIVES,
    USE_OPENROUTER, OPENROUTER_API_KEY, OPENROUTER_MODEL, 
    OPENROUTER_SITE_URL, OPENROUTER_SITE_NAME, ANTHROPIC_API_KEY
)
from prompts import PERSPECTIVE_PROMPTS, MENTAL_MODEL_PROMPTS, SYNTHESIS_PROMPT
from search_rag import SearchAndRAG
from openrouter_client import AsyncOpenRouterClient
from openrouter_sync import AsyncSyncOpenRouterClient

@dataclass
class AnalysisResult:
    """Structure for individual analysis results."""
    perspective: str
    analysis: str
    confidence_score: float
    key_insights: List[str]
    recommendations: List[str]
    timestamp: str

class RedTeamAnalyzer:
    """Main analyzer class for red team strategy analysis."""
    
    def __init__(self, api_key: str = None, enable_search: bool = True):
        self.session = None
        self.enable_search = enable_search
        
        # Determine which API to use
        if USE_OPENROUTER and OPENROUTER_API_KEY:
            print("Using OpenRouter API for Gemini 2.5 Pro")
            try:
                # Try the async client first
                self.client = AsyncOpenRouterClient(
                    api_key=OPENROUTER_API_KEY,
                    site_url=OPENROUTER_SITE_URL,
                    site_name=OPENROUTER_SITE_NAME
                )
            except Exception as e:
                print(f"Async OpenRouter client failed, using sync fallback: {e}")
                # Fallback to sync client if async fails
                self.client = AsyncSyncOpenRouterClient(
                    api_key=OPENROUTER_API_KEY,
                    site_url=OPENROUTER_SITE_URL,
                    site_name=OPENROUTER_SITE_NAME
                )
            self.model = OPENROUTER_MODEL
            self.use_openrouter = True
        else:
            print("Using direct Anthropic API")
            effective_api_key = api_key or ANTHROPIC_API_KEY
            if not effective_api_key:
                raise ValueError("No API key provided for Anthropic API")
            self.client = AsyncAnthropic(api_key=effective_api_key)
            self.model = CLAUDE_MODEL
            self.use_openrouter = False
        
        # Initialize search and RAG system
        if enable_search:
            try:
                self.search_rag = SearchAndRAG()
            except Exception as e:
                print(f"Warning: Could not initialize search system: {e}")
                self.search_rag = None
                self.enable_search = False
        else:
            self.search_rag = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=2, min=4, max=20),
        reraise=True
    )
    async def _make_api_call(
        self, 
        prompt: str, 
        system_prompt: str = "",
        max_tokens: int = 4000,
        timeout: int = 60
    ) -> str:
        """Make a single API call with improved timeout and error handling."""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            print(f"Making API call with model: {self.model}")  # Debug info
            
            # Add timeout wrapper for API calls
            if self.use_openrouter:
                api_call = self.client.messages_create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=0.6,  # Lower temperature for more consistent JSON
                    system=system_prompt,
                    messages=messages
                )
            else:
                api_call = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=0.6,  # Lower temperature for more consistent JSON
                    system=system_prompt,
                    messages=messages
                )
            
            # Apply timeout
            response = await asyncio.wait_for(api_call, timeout=timeout)
            
            # Handle both Anthropic and OpenRouter response formats
            if hasattr(response.content[0], 'text'):
                return response.content[0].text
            elif isinstance(response.content[0], dict):
                return response.content[0].get('text', str(response.content[0]))
            else:
                return str(response.content[0])
            
        except asyncio.TimeoutError:
            raise Exception(f"API call timed out after {timeout} seconds - will retry")
        except Exception as e:
            error_msg = str(e)
            print(f"API call error details: {type(e).__name__}: {error_msg}")  # Debug info
            
            # Handle specific OpenRouter errors
            if "overloaded" in error_msg.lower():
                # For overloaded errors, add exponential backoff hint
                raise Exception(f"OpenRouter API overloaded - will retry with backoff: {error_msg}")
            elif "rate limit" in error_msg.lower():
                raise Exception(f"Rate limit exceeded - will retry: {error_msg}")
            elif "timeout" in error_msg.lower():
                raise Exception(f"API timeout - will retry: {error_msg}")
            else:
                raise Exception(f"API call failed: {error_msg}")
    
    def _parse_and_validate_json(self, response: str) -> dict:
        """Parse and validate JSON response with multiple fallback strategies."""
        try:
            # Strategy 1: Direct parsing
            parsed = json.loads(response)
            return self._validate_json_structure(parsed)
        except json.JSONDecodeError:
            pass
        
        try:
            # Strategy 2: Remove markdown formatting
            response_clean = response.strip()
            
            # Remove various markdown wrappers
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            elif response_clean.startswith('```'):
                response_clean = response_clean[3:]
            
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            # Remove any leading/trailing text
            json_start = response_clean.find('{')
            json_end = response_clean.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = response_clean[json_start:json_end]
                parsed = json.loads(json_content)
                return self._validate_json_structure(parsed)
        except (json.JSONDecodeError, IndexError):
            pass
        
        try:
            # Strategy 3: More aggressive JSON extraction
            import re
            
            # Look for JSON objects that contain our required fields
            # Use a more flexible pattern that handles nested content
            json_pattern = r'\{(?:[^{}]|\{[^{}]*\})*"analysis"(?:[^{}]|\{[^{}]*\})*"confidence_score"(?:[^{}]|\{[^{}]*\})*"key_insights"(?:[^{}]|\{[^{}]*\})*"recommendations"(?:[^{}]|\{[^{}]*\})*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            if matches:
                # Try the most complete match
                for match in sorted(matches, key=len, reverse=True):
                    try:
                        parsed = json.loads(match)
                        return self._validate_json_structure(parsed)
                    except json.JSONDecodeError:
                        continue
            
            # Strategy 4: Even more flexible - just find complete JSON objects
            all_json_pattern = r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}'
            all_matches = re.findall(all_json_pattern, response, re.DOTALL)
            
            for match in sorted(all_matches, key=len, reverse=True):
                try:
                    parsed = json.loads(match)
                    if isinstance(parsed, dict) and 'analysis' in parsed:
                        return self._validate_json_structure(parsed)
                except json.JSONDecodeError:
                    continue
                    
        except Exception:
            pass
        
        print(f"All JSON parsing strategies failed for response: {response[:200]}...")
        return None
    
    def _validate_json_structure(self, parsed: dict) -> dict:
        """Validate and clean JSON structure."""
        if not isinstance(parsed, dict):
            return None
        
        # Required fields with defaults
        required_fields = {
            'analysis': '',
            'confidence_score': 0.5,
            'key_insights': [],
            'recommendations': []
        }
        
        # Ensure all required fields exist
        for field, default in required_fields.items():
            if field not in parsed:
                parsed[field] = default
        
        # Validate and clean field types
        if not isinstance(parsed['analysis'], str):
            parsed['analysis'] = str(parsed['analysis'])
        
        try:
            parsed['confidence_score'] = float(parsed['confidence_score'])
            # Ensure confidence is between 0 and 1
            parsed['confidence_score'] = max(0.0, min(1.0, parsed['confidence_score']))
        except (ValueError, TypeError):
            parsed['confidence_score'] = 0.5
        
        if not isinstance(parsed['key_insights'], list):
            parsed['key_insights'] = []
        
        if not isinstance(parsed['recommendations'], list):
            parsed['recommendations'] = []
        
        # Ensure lists contain strings
        parsed['key_insights'] = [str(item) for item in parsed['key_insights'] if item]
        parsed['recommendations'] = [str(item) for item in parsed['recommendations'] if item]
        
        # Relaxed validation - allow responses with minimal content
        if len(parsed['analysis'].strip()) < 20:  # Very minimal analysis length requirement
            return None
        
        # Don't require insights - allow empty arrays (some responses may have analysis but parsing issues with arrays)
        
        return parsed
    
    async def analyze_from_perspective(
        self,
        strategy: str,
        perspective: str,
        mental_models: List[str] = None
    ) -> AnalysisResult:
        """Analyze strategy from a specific perspective with enhanced context."""
        
        # Get perspective prompt
        perspective_prompt = PERSPECTIVE_PROMPTS.get(perspective, {})
        if not perspective_prompt:
            raise ValueError(f"Unknown perspective: {perspective}")
        
        # Get enhanced context from search and RAG
        search_context = ""
        if self.enable_search and self.search_rag:
            try:
                context_summary, search_results = await self.search_rag.enhance_analysis_with_context(
                    strategy, perspective
                )
                if context_summary:
                    search_context = f"""

EXTERNAL CONTEXT INTEGRATION FRAMEWORK:
{context_summary}

CONTEXT ANALYSIS INSTRUCTIONS:
1. RELEVANCE ASSESSMENT: Rate the external context relevance to this strategy (High/Medium/Low)
2. EVIDENCE TRIANGULATION: Compare strategy assumptions against external evidence
3. REALITY CHECK: Use external data to validate or challenge strategy feasibility
4. INSIGHT ENHANCEMENT: Identify additional insights from external context that strengthen analysis

INTEGRATION PRINCIPLES:
• Use external context to enhance, not replace, your core analytical framework
• Clearly distinguish between strategy-internal analysis and external context insights
• Weight external evidence by source credibility and temporal relevance
• Focus on how external context modifies risk assessments and success probabilities
"""
            except Exception as e:
                print(f"Warning: Search context failed: {e}")
        
        # Incorporate mental models if specified
        mental_model_context = ""
        if mental_models:
            model_descriptions = []
            for model in mental_models:
                if model in MENTAL_MODEL_PROMPTS:
                    model_descriptions.append(MENTAL_MODEL_PROMPTS[model])
            
            if model_descriptions:
                mental_model_context = f"""
                
MENTAL MODEL FRAMEWORKS TO APPLY:
{chr(10).join(model_descriptions)}

When analyzing, explicitly apply these mental models where relevant.
"""
        
        # Construct full prompt
        full_prompt = f"""
{perspective_prompt['system_prompt']}{mental_model_context}{search_context}

STRATEGY TO ANALYZE:
{strategy}

{perspective_prompt['analysis_prompt']}

CONFIDENCE CALIBRATION GUIDE:
• 0.8-1.0: Strong evidence from multiple sources, clear logical reasoning, well-established precedents
• 0.6-0.8: Good evidence with some uncertainty, reasonable inferences, moderate precedent support  
• 0.4-0.6: Limited evidence, significant assumptions required, novel or unprecedented elements
• 0.0-0.4: Weak evidence, high uncertainty, speculative analysis, contradictory information

CRITICAL: YOU MUST RESPOND WITH ONLY VALID JSON. NO OTHER TEXT WHATSOEVER.

Here are examples of the EXACT format required:

EXAMPLE 1:
{{
    "analysis": "This strategy faces several challenges. The pricing at $50/month puts it in direct competition with established players who have more resources and brand recognition. Market timing may be problematic as the AI writing space is becoming saturated. Customer acquisition will be expensive given the crowded landscape. However, focusing on freelancers creates a niche opportunity if executed well with specialized features.",
    "confidence_score": 0.7,
    "key_insights": ["Pricing puts strategy in direct competition with established players", "Market timing challenging due to AI writing space saturation", "Freelancer focus creates defendable niche opportunity"],
    "recommendations": ["Differentiate through specialized freelancer-focused features", "Consider lower initial pricing to gain market entry"]
}}

EXAMPLE 2:
{{
    "analysis": "From a systems perspective, this strategy creates multiple interconnected feedback loops. Customer satisfaction drives word-of-mouth marketing, which reduces acquisition costs and improves unit economics. The collaboration features create network effects where teams become locked into the platform. However, high churn in the freelance market creates negative feedback loops that could destabilize growth.",
    "confidence_score": 0.8,
    "key_insights": ["Network effects from collaboration features increase switching costs", "Freelancer market volatility creates churn challenges", "Word-of-mouth loops critical for sustainable unit economics"],
    "recommendations": ["Build strong onboarding to reduce early churn", "Develop features that increase switching costs for established users"]
}}

NOW PROVIDE YOUR RESPONSE IN EXACTLY THIS FORMAT - ONLY JSON, NO OTHER TEXT:
"""
        
        # Make API call with JSON-only system prompt
        json_system_prompt = f"{perspective_prompt['system_role']} You MUST respond with ONLY valid JSON. No explanations, no markdown, no additional text."
        
        response = await self._make_api_call(
            full_prompt,
            json_system_prompt,
            max_tokens=2500,  # Optimized for 400-word analyses with JSON overhead
            timeout=45  # Shorter timeout for faster failures and retries
        )
        
        # Enhanced JSON parsing with validation
        parsed_response = self._parse_and_validate_json(response)
        
        if parsed_response:
            return AnalysisResult(
                perspective=perspective,
                analysis=parsed_response.get('analysis', ''),
                confidence_score=float(parsed_response.get('confidence_score', 0.5)),
                key_insights=parsed_response.get('key_insights', []),
                recommendations=parsed_response.get('recommendations', []),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
            # Fallback if JSON parsing fails
            return AnalysisResult(
                perspective=perspective,
                analysis=response,
                confidence_score=0.5,
                key_insights=[],
                recommendations=[],
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
    
    async def analyze_strategy(
        self,
        strategy: str,
        perspectives: List[str],
        mental_models: List[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, AnalysisResult]:
        """Analyze strategy from multiple perspectives."""
        
        results = {}
        total_perspectives = len(perspectives)
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests
        
        async def analyze_with_semaphore(perspective: str, index: int):
            async with semaphore:
                if progress_callback:
                    progress = index / total_perspectives
                    progress_callback(progress, f"Analyzing from {perspective} perspective...")
                
                result = await self.analyze_from_perspective(
                    strategy, perspective, mental_models
                )
                
                # Rate limiting
                await asyncio.sleep(RATE_LIMIT_DELAY)
                
                return perspective, result
        
        # Run analyses concurrently
        tasks = [
            analyze_with_semaphore(perspective, i) 
            for i, perspective in enumerate(perspectives)
        ]
        
        completed_analyses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(completed_analyses):
            if isinstance(result, Exception):
                # Handle failed analysis
                perspective = perspectives[i]
                error_msg = str(result)
                print(f"Analysis failed for {perspective}: {error_msg}")  # Debug info
                
                # Provide more specific error messages
                api_type = "OpenRouter" if self.use_openrouter else "Anthropic"
                model_name = self.model
                
                if "API key" in error_msg.lower() or "unauthorized" in error_msg.lower():
                    analysis_text = f"Analysis failed: Invalid or missing {api_type} API key. Please check your configuration."
                elif "model" in error_msg.lower():
                    analysis_text = f"Analysis failed: Model '{model_name}' not available via {api_type}. Please check model name or try again later."
                elif "rate limit" in error_msg.lower():
                    analysis_text = f"Analysis failed: {api_type} rate limit exceeded. Please wait a moment and try again."
                elif "insufficient" in error_msg.lower() and "credits" in error_msg.lower():
                    analysis_text = f"Analysis failed: Insufficient {api_type} credits. Please check your account balance."
                elif "overloaded" in error_msg.lower():
                    analysis_text = f"Analysis failed: {api_type} servers are currently overloaded. This is temporary - please try again in a few minutes."
                else:
                    analysis_text = f"Analysis failed ({api_type}): {error_msg}"
                
                results[perspective] = AnalysisResult(
                    perspective=perspective,
                    analysis=analysis_text,
                    confidence_score=0.0,
                    key_insights=[],
                    recommendations=[],
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
                )
            else:
                perspective, analysis_result = result
                results[perspective] = analysis_result
        
        if progress_callback:
            progress_callback(1.0, "Analysis complete!")
        
        return results
    
    async def synthesize_results(
        self,
        strategy: str,
        analysis_results: Dict[str, AnalysisResult]
    ) -> Dict[str, Any]:
        """Synthesize multiple analysis results into unified insights."""
        
        # Prepare comprehensive synthesis input
        synthesis_input = f"""
ORIGINAL STRATEGY TO SYNTHESIZE:
{strategy}

RED TEAM ANALYSIS RESULTS FROM MULTIPLE PERSPECTIVES:
"""
        
        # Add detailed results from each perspective
        for perspective, result in analysis_results.items():
            perspective_info = RED_TEAM_PERSPECTIVES.get(perspective, {})
            perspective_name = perspective_info.get('name', perspective)
            
            synthesis_input += f"""
=== {perspective_name.upper()} PERSPECTIVE ===
Confidence Score: {result.confidence_score:.2f}

Full Analysis:
{result.analysis}

Key Insights:
{chr(10).join(f"• {insight}" for insight in result.key_insights)}

Recommendations:
{chr(10).join(f"• {rec}" for rec in result.recommendations)}

"""
        
        synthesis_input += f"""
{SYNTHESIS_PROMPT}
"""
        
        # Enhanced system prompt for synthesis
        system_prompt = """You are an expert strategic synthesis analyst who excels at:
1. Identifying patterns and themes across multiple analytical perspectives
2. Prioritizing insights based on strategic importance and evidence strength
3. Creating actionable, specific recommendations
4. Assessing implementation feasibility and risk factors
5. Providing structured, JSON-formatted strategic assessments

Your task is to synthesize the red team analysis into a comprehensive strategic assessment that decision-makers can act upon immediately."""
        
        # Make synthesis API call with retries
        max_synthesis_attempts = 3
        for attempt in range(max_synthesis_attempts):
            try:
                response = await self._make_api_call(
                    synthesis_input,
                    system_prompt,
                    max_tokens=8000
                )
                
                # Clean response - remove any non-JSON content
                response_clean = response.strip()
                
                # Find JSON content if wrapped in other text
                json_start = response_clean.find('{')
                json_end = response_clean.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_content = response_clean[json_start:json_end]
                else:
                    json_content = response_clean
                
                # Parse synthesis response
                synthesis_result = json.loads(json_content)
                
                # Validate required fields
                required_fields = [
                    'executive_summary', 'critical_insights', 'priority_recommendations',
                    'risk_mitigation', 'implementation_roadmap', 'confidence_assessment'
                ]
                
                for field in required_fields:
                    if field not in synthesis_result:
                        raise ValueError(f"Missing required field: {field}")
                
                return synthesis_result
                
            except (json.JSONDecodeError, ValueError) as e:
                if attempt == max_synthesis_attempts - 1:
                    # Final fallback with structured data
                    return self._create_fallback_synthesis(strategy, analysis_results, str(e))
                
                # Retry with more explicit instructions
                synthesis_input += f"\n\nPREVIOUS ATTEMPT FAILED: {str(e)}. Please ensure response is valid JSON only."
        
        return self._create_fallback_synthesis(strategy, analysis_results, "Max attempts exceeded")
    
    def _create_fallback_synthesis(
        self, 
        strategy: str, 
        analysis_results: Dict[str, AnalysisResult],
        error_msg: str
    ) -> Dict[str, Any]:
        """Create a fallback synthesis when JSON parsing fails."""
        
        # Extract insights and recommendations manually
        all_insights = []
        all_recommendations = []
        confidence_scores = []
        
        for result in analysis_results.values():
            all_insights.extend(result.key_insights)
            all_recommendations.extend(result.recommendations)
            confidence_scores.append(result.confidence_score)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        return {
            "executive_summary": f"Analysis completed across {len(analysis_results)} perspectives with average confidence of {avg_confidence:.1%}. Manual review recommended due to synthesis parsing issues.",
            "critical_insights": all_insights[:3] if all_insights else ["Comprehensive analysis completed", "Multiple perspectives evaluated", "Further review recommended"],
            "priority_recommendations": all_recommendations[:3] if all_recommendations else ["Review individual perspective analyses", "Validate key assumptions", "Develop implementation plan"],
            "risk_mitigation": [
                "Conduct thorough risk assessment based on individual analyses",
                "Implement monitoring systems for identified concerns",
                "Develop contingency plans for major risks"
            ],
            "implementation_roadmap": [
                "Phase 1: Review and validate individual perspective analyses",
                "Phase 2: Develop detailed implementation plan",
                "Phase 3: Execute with continuous monitoring"
            ],
            "success_metrics": [
                "Achievement of strategic objectives",
                "Risk mitigation effectiveness",
                "Stakeholder satisfaction levels"
            ],
            "confidence_assessment": avg_confidence,
            "key_assumptions_to_validate": [
                "Core strategy assumptions need validation",
                "Implementation feasibility requires verification"
            ],
            "alternative_approaches": [
                "Phased implementation approach",
                "Alternative strategy based on risk assessment"
            ],
            "consensus_level": "Medium",
            "implementation_difficulty": "Medium",
            "_synthesis_note": f"Fallback synthesis used due to: {error_msg}"
        }
    
    async def get_follow_up_questions(
        self, 
        strategy: str, 
        analysis_results: Dict[str, AnalysisResult]
    ) -> List[str]:
        """Generate follow-up questions based on analysis results."""
        
        prompt = f"""
Based on the strategy analysis, generate 5-7 thoughtful follow-up questions that would help strengthen the strategy:

STRATEGY: {strategy}

KEY CONCERNS IDENTIFIED:
"""
        
        for perspective, result in analysis_results.items():
            prompt += f"- {perspective}: {', '.join(result.key_insights[:2])}\n"
        
        prompt += """
Generate specific, actionable questions that address gaps or assumptions identified in the analysis.
Format as a simple list of questions.
"""
        
        response = await self._make_api_call(prompt)
        
        # Extract questions from response
        lines = response.strip().split('\n')
        questions = [line.strip('- ').strip() for line in lines if line.strip()]
        
        return questions[:7]  # Return max 7 questions