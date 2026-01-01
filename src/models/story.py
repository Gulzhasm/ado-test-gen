"""
User Story data model.

This module defines the Pydantic model for User Story work items,
providing type safety and validation for story data.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class UserStory(BaseModel):
    """
    User Story work item model.
    
    Represents a User Story retrieved from Azure DevOps with its
    title, description, and acceptance criteria.
    """
    id: int = Field(..., description="User Story work item ID")
    title: str = Field(..., description="Story title")
    description_html: Optional[str] = Field(None, description="Description in HTML format")
    description_text: Optional[str] = Field(None, description="Description as clean text")
    acceptance_criteria_html: Optional[str] = Field(
        None, 
        description="Acceptance Criteria in HTML format (from dedicated field)"
    )
    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description="Extracted and normalized acceptance criteria items"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable model for data integrity

