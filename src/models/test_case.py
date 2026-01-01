"""
Test Case data model.

This module defines the Pydantic model for Test Case work items,
including test steps and metadata.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class TestStep(BaseModel):
    """
    Individual test step model.
    
    Represents a single step in a test case with action and expected result.
    """
    action: str = Field(..., description="Step action description")
    expected_result: str = Field(..., description="Expected result description")
    step_number: int = Field(..., description="Step sequence number (1-based)")
    
    class Config:
        """Pydantic configuration."""
        frozen = True


class TestCaseType(str, Enum):
    """
    Types of test cases generated.
    
    Research Note: This enum supports future ML-based test case
    classification and prioritization.
    """
    HAPPY_PATH = "happy_path"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    CANCEL_ROLLBACK = "cancel_rollback"
    PERSISTENCE = "persistence"
    UNDO_REDO = "undo_redo"
    ACCESSIBILITY = "accessibility"
    UMBRELLA = "umbrella"  # Final verification test case


class TestCase(BaseModel):
    """
    Test Case work item model.
    
    Represents a complete test case with title, steps, and metadata.
    """
    internal_id: str = Field(..., description="Internal test case ID (e.g., '271309-AC1')")
    title: str = Field(..., description="Test case title")
    steps: List[TestStep] = Field(..., description="Test steps")
    test_type: TestCaseType = Field(..., description="Type of test scenario")
    acceptance_criterion_id: Optional[int] = Field(
        None,
        description="Related AC ID (None for umbrella test case)"
    )
    story_id: int = Field(..., description="Related User Story ID")
    tags: List[str] = Field(default_factory=list, description="Test case tags")
    
    class Config:
        """Pydantic configuration."""
        frozen = True

