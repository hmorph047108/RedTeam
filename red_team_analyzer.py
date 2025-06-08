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
from config import CLAUDE_MODEL, MAX_RETRIES, REQUEST_TIMEOUT, RATE_LIMIT_DELAY, RED_TEAM_PERSPECTIVES
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