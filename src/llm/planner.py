"""
LLM-based scenario planner for test case generation.

This module uses Azure OpenAI to propose additional test scenarios
beyond the baseline rule-based generation.
"""
import json
import requests
from typing import List, Optional
from pydantic import BaseModel, Field
from src.config.settings import settings


class ScenarioSuggestion(BaseModel):
    """Single scenario suggestion from LLM planner."""
    category: str = Field(..., description="Test category")
    subcategory: str = Field(..., description="Test subcategory")
    short_descriptor: str = Field(..., description="Short descriptor (<=8 words, no punctuation)")
    risk: str = Field(..., description="Risk level: High|Medium|Low")
    rationale: str = Field(..., description="Why this scenario matters")
    preconditions: List[str] = Field(default_factory=list, description="Optional preconditions")
    steps_hint: List[str] = Field(default_factory=list, description="Optional step hints")


class PlannerResponse(BaseModel):
    """Planner output schema."""
    suggestions: List[ScenarioSuggestion] = Field(..., max_length=2, description="Max 2 suggestions per AC")


class LLMPlanner:
    """
    LLM-based scenario planner that proposes additional test scenarios.
    
    Uses Azure OpenAI Chat Completions API to generate scenario suggestions
    that complement the baseline rule-based test cases.
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: Optional[str] = None,
        deployment: Optional[str] = None
    ):
        """
        Initialize LLM planner.
        
        Args:
            endpoint: Azure OpenAI endpoint (defaults to settings)
            api_key: Azure OpenAI API key (defaults to settings)
            api_version: API version (defaults to settings)
            deployment: Deployment name (defaults to settings)
        """
        self.endpoint = endpoint or settings.azure_openai_endpoint
        self.api_key = api_key or settings.azure_openai_api_key
        self.api_version = api_version or settings.azure_openai_api_version
        self.deployment = deployment or settings.azure_openai_deployment
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.timeout = settings.llm_timeout_seconds
    
    def is_configured(self) -> bool:
        """Check if Azure OpenAI is properly configured."""
        return all([
            self.endpoint,
            self.api_key,
            self.deployment
        ])
    
    def plan_scenarios(
        self,
        story_title: str,
        story_description: str,
        ac_item: str,
        baseline_titles: List[str]
    ) -> PlannerResponse:
        """
        Generate scenario suggestions for a single AC item.
        
        Args:
            story_title: User story title
            story_description: User story description
            ac_item: Single acceptance criterion text
            baseline_titles: List of baseline test case titles (to avoid duplicates)
            
        Returns:
            PlannerResponse with up to 2 suggestions (empty on failure)
        """
        if not self.is_configured():
            return PlannerResponse(suggestions=[])
        
        # Build system prompt
        system_prompt = """You are a test scenario planner. Return JSON only. No markdown. Follow the exact schema.

Rules:
- Return max 2 suggestions per AC
- short_descriptor must be <= 8 words, noun-phrase-like, no punctuation (no . : ; …), no forbidden words (verify, click, when, then)
- Do NOT repeat scenarios already covered in baseline titles
- Suggest edge cases, non-functional tests, accessibility tests when relevant
- Categories: Validation, Ordering, Retention, Accessibility, Reset, Scrolling, Restrictions, Behavior, Availability

Output schema:
{
  "suggestions": [
    {
      "category": "string",
      "subcategory": "string",
      "short_descriptor": "string (<=8 words, no punctuation)",
      "risk": "High|Medium|Low",
      "rationale": "string",
      "preconditions": ["optional strings"],
      "steps_hint": ["optional strings"]
    }
  ]
}"""
        
        # Build user prompt
        baseline_titles_text = "\n".join([f"- {title}" for title in baseline_titles[:10]])  # Limit to 10
        user_prompt = f"""Story: {story_title}

Description: {story_description[:500]}

Acceptance Criterion: {ac_item}

Baseline test cases already generated:
{baseline_titles_text if baseline_titles else "None"}

Propose up to 2 additional test scenarios NOT covered by baseline. Focus on edge cases, negative paths, boundary conditions, accessibility, or non-functional aspects."""
        
        # Call Azure OpenAI
        for attempt in range(2):  # Max 2 retries
            try:
                response = self._call_azure_openai(system_prompt, user_prompt)
                if response:
                    return response
            except Exception as e:
                if attempt == 1:  # Last attempt
                    # Fail open - return empty suggestions
                    return PlannerResponse(suggestions=[])
                continue
        
        return PlannerResponse(suggestions=[])
    
    def _call_azure_openai(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> Optional[PlannerResponse]:
        """
        Call Azure OpenAI Chat Completions API.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            
        Returns:
            Parsed PlannerResponse or None on failure
        """
        url = f"{self.endpoint.rstrip('/')}/openai/deployments/{self.deployment}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        params = {
            "api-version": self.api_version
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        response = requests.post(
            url,
            headers=headers,
            params=params,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Strip markdown code blocks if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON
        data = json.loads(content)
        
        # Validate and parse with Pydantic
        return PlannerResponse(**data)

