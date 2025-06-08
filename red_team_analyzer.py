"""
Red Team Analyzer - Core analysis engine using Claude Opus 4 API
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
from config import CLAUDE_MODEL, MAX_RETRIES, REQUEST_TIMEOUT, RATE_LIMIT_DELAY
from prompts import PERSPECTIVE_PROMPTS, MENTAL_MODEL_PROMPTS, SYNTHESIS_PROMPT

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
    
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_api_call(
        self, 
        prompt: str, 
        system_prompt: str = "",
        max_tokens: int = 4000
    ) -> str:
        """Make a single API call to Claude with retry logic."""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            response = await self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=max_tokens,
                temperature=0.7,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")
    
    async def analyze_from_perspective(
        self,
        strategy: str,
        perspective: str,
        mental_models: List[str] = None
    ) -> AnalysisResult:
        """Analyze strategy from a specific perspective."""
        
        # Get perspective prompt
        perspective_prompt = PERSPECTIVE_PROMPTS.get(perspective, {})
        if not perspective_prompt:
            raise ValueError(f"Unknown perspective: {perspective}")
        
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
{perspective_prompt['system_prompt']}{mental_model_context}

STRATEGY TO ANALYZE:
{strategy}

{perspective_prompt['analysis_prompt']}

Please structure your response as a JSON object with the following format:
{{
    "analysis": "Your detailed analysis from this perspective",
    "confidence_score": 0.85,
    "key_insights": ["insight 1", "insight 2", "insight 3"],
    "recommendations": ["recommendation 1", "recommendation 2"],
    "critical_assumptions": ["assumption 1", "assumption 2"],
    "potential_failures": ["failure mode 1", "failure mode 2"]
}}
"""
        
        # Make API call
        response = await self._make_api_call(
            full_prompt,
            perspective_prompt['system_role']
        )
        
        # Parse response
        try:
            parsed_response = json.loads(response)
            
            return AnalysisResult(
                perspective=perspective,
                analysis=parsed_response.get('analysis', ''),
                confidence_score=float(parsed_response.get('confidence_score', 0.5)),
                key_insights=parsed_response.get('key_insights', []),
                recommendations=parsed_response.get('recommendations', []),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
        except json.JSONDecodeError:
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
                results[perspective] = AnalysisResult(
                    perspective=perspective,
                    analysis=f"Analysis failed: {str(result)}",
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
        
        # Prepare synthesis input
        synthesis_input = f"""
ORIGINAL STRATEGY:
{strategy}

ANALYSIS RESULTS:
"""
        
        for perspective, result in analysis_results.items():
            synthesis_input += f"""
--- {perspective.upper()} PERSPECTIVE ---
Analysis: {result.analysis}
Key Insights: {', '.join(result.key_insights)}
Recommendations: {', '.join(result.recommendations)}
Confidence: {result.confidence_score:.2f}

"""
        
        synthesis_input += SYNTHESIS_PROMPT
        
        # Make synthesis API call
        response = await self._make_api_call(
            synthesis_input,
            "You are a strategic synthesis expert who combines multiple analytical perspectives into actionable insights.",
            max_tokens=6000
        )
        
        # Parse synthesis response
        try:
            synthesis_result = json.loads(response)
            return synthesis_result
        except json.JSONDecodeError:
            return {
                "executive_summary": response[:500] + "...",
                "critical_insights": ["Unable to parse structured synthesis"],
                "priority_recommendations": ["Review synthesis manually"],
                "risk_mitigation": ["Standard risk management protocols"],
                "implementation_roadmap": ["Plan implementation carefully"],
                "confidence_assessment": 0.5
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