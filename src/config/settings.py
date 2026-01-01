"""
Configuration management for ADO Test Case Generator.

This module handles all configuration settings including Azure DevOps connection
parameters, test plan/suite IDs, and other system-wide settings.

Research Note: Configuration is separated to allow easy experimentation with
different ADO organizations, projects, and test environments without code changes.
"""
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

# Load .env file explicitly
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    
    Required:
        ado_org: Azure DevOps organization name
        ado_project: Azure DevOps project name
        ado_pat: Personal Access Token for authentication
    
    Optional:
        ado_test_plan_id: Default test plan ID (can be overridden via CLI)
        ado_test_suite_id: Default test suite ID (can be overridden via CLI)
        azure_openai_endpoint: Azure OpenAI endpoint URL
        azure_openai_api_key: Azure OpenAI API key
        azure_openai_api_version: Azure OpenAI API version (default: 2024-02-15-preview)
        azure_openai_deployment: Azure OpenAI deployment name
        llm_temperature: LLM temperature (default: 0.2)
        llm_max_tokens: LLM max tokens (default: 900)
        llm_timeout_seconds: LLM timeout (default: 30)
    """
    ado_org: str
    ado_project: str
    ado_pat: str
    
    ado_test_plan_id: Optional[str] = None
    ado_test_suite_id: Optional[str] = None
    
    # Azure OpenAI settings (optional, required for hybrid mode)
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_api_version: str = "2024-02-15-preview"
    azure_openai_deployment: Optional[str] = None
    
    # LLM configuration
    llm_temperature: float = 0.2
    llm_max_tokens: int = 900
    llm_timeout_seconds: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()

