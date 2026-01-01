"""
LLM-based test step writer.

This module uses Azure OpenAI to generate executable test steps
for scenario proposals.
"""
import json
import re
import requests
from typing import List, Optional
from pydantic import BaseModel, Field
from src.config.settings import settings


class LLMTestStep(BaseModel):
    """Single test step with action and expected result (LLM output format)."""
    action: str = Field(..., description="Step action (plain text)")
    expected: str = Field(..., description="Expected result (plain text)")


class StepWriterResponse(BaseModel):
    """Step writer output schema."""
    steps: List[LLMTestStep] = Field(..., max_length=10, description="Max 10 steps")


class LLMStepWriter:
    """
    LLM-based step writer that generates executable test steps.
    
    Uses Azure OpenAI Chat Completions API to generate test steps
    for validated scenario proposals.
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: Optional[str] = None,
        deployment: Optional[str] = None
    ):
        """
        Initialize LLM step writer.
        
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
    
    def write_steps(
        self,
        story_title: str,
        story_description: str,
        ac_item: str,
        scenario_category: str,
        scenario_subcategory: str,
        scenario_descriptor: str,
        preconditions: List[str],
        steps_hint: List[str]
    ) -> StepWriterResponse:
        """
        Generate test steps for a scenario proposal.
        
        Args:
            story_title: User story title
            story_description: User story description
            ac_item: Related acceptance criterion
            scenario_category: Scenario category
            scenario_subcategory: Scenario subcategory
            scenario_descriptor: Scenario short descriptor
            preconditions: Optional preconditions
            steps_hint: Optional step hints
            
        Returns:
            StepWriterResponse with test steps (empty on failure)
        """
        if not self.is_configured():
            return StepWriterResponse(steps=[])
        
        # Build system prompt
        system_prompt = """You are a test step writer. Return JSON only. No markdown. Follow the exact schema.

Rules:
- Return max 10 steps
- Each step must have "action" and "expected" fields
- Use plain text only (no markdown, no formatting)
- One action per step
- Include expected outcome for each step
- Do NOT include tooltips, hotkeys, or UI details unless explicitly in scope
- Steps should be executable and clear

Output schema:
{
  "steps": [
    {
      "action": "plain text action",
      "expected": "plain text expected result"
    }
  ]
}"""
        
        # Build user prompt
        preconditions_text = "\n".join([f"- {p}" for p in preconditions]) if preconditions else "None"
        hints_text = "\n".join([f"- {h}" for h in steps_hint]) if steps_hint else "None"
        
        user_prompt = f"""Story: {story_title}

Description: {story_description[:500]}

Acceptance Criterion: {ac_item}

Scenario to test:
- Category: {scenario_category}
- Subcategory: {scenario_subcategory}
- Descriptor: {scenario_descriptor}
- Preconditions: {preconditions_text}
- Hints: {hints_text}

Generate executable test steps (action + expected result) for this scenario."""
        
        # Call Azure OpenAI
        for attempt in range(2):  # Max 2 retries
            try:
                response = self._call_azure_openai(system_prompt, user_prompt)
                if response:
                    return response
            except Exception as e:
                if attempt == 1:  # Last attempt
                    # Fail open - return empty steps
                    return StepWriterResponse(steps=[])
                continue
        
        return StepWriterResponse(steps=[])
    
    def _call_azure_openai(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> Optional[StepWriterResponse]:
        """
        Call Azure OpenAI Chat Completions API.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            
        Returns:
            Parsed StepWriterResponse or None on failure
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
        return StepWriterResponse(**data)

