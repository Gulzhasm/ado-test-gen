"""
Acceptance Criteria data model.

This module defines models for individual acceptance criteria items
and their test coverage requirements.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class TestScenarioType(str, Enum):
    """
    Types of test scenarios to generate for each AC.
    
    Research Note: This enum can be extended with ML-classified
    scenario types based on AC content analysis.
    """
    HAPPY_PATH = "happy_path"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    CANCEL_ROLLBACK = "cancel_rollback"
    PERSISTENCE = "persistence"
    UNDO_REDO = "undo_redo"
    ACCESSIBILITY = "accessibility"


class AcceptanceCriterion(BaseModel):
    """
    Individual Acceptance Criterion model.
    
    Represents a single AC item with its original text and
    metadata for test case generation.
    """
    id: int = Field(..., description="AC sequence number (1-based)")
    text: str = Field(..., description="AC text content")
    original_order: int = Field(..., description="Original position in AC list")
    
    class Config:
        """Pydantic configuration."""
        frozen = True

