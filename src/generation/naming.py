"""
Test case naming convention implementation.

This module implements the strict naming rules:
- First test case: {StoryID}-AC1
- Subsequent: {StoryID}-005, {StoryID}-010, {StoryID}-015 (increment by 5)
- Title format: {InternalID}: <Feature> / <Module> / <Category> / <SubCategory> / <Description>

Research Note: Naming conventions are rule-based but can be enhanced with
ML-based feature/module/category extraction from AC content.
"""
from typing import List, Optional
from src.models.test_case import TestCase, TestCaseType


class TestCaseNaming:
    """
    Handles test case ID generation and title formatting according to
    strict naming conventions.
    """
    
    @staticmethod
    def generate_internal_id(story_id: int, index: int) -> str:
        """
        Generate internal test case ID.
        
        Rules:
        - First test case (index 0): {StoryID}-AC1
        - Subsequent: {StoryID}-005, {StoryID}-010, {StoryID}-015, etc.
        - Always increment by 5 to reserve 4 ID gaps for future expansion
        
        Args:
            story_id: User Story ID
            index: Zero-based index of test case
            
        Returns:
            Internal ID string (e.g., "271309-AC1", "271309-005")
            
        Example:
            >>> TestCaseNaming.generate_internal_id(271309, 0)
            '271309-AC1'
            >>> TestCaseNaming.generate_internal_id(271309, 1)
            '271309-005'
            >>> TestCaseNaming.generate_internal_id(271309, 2)
            '271309-010'
        """
        if index == 0:
            return f"{story_id}-AC1"
        else:
            # Increment by 5: 005, 010, 015, 020, etc.
            number = (index - 1) * 5 + 5
            return f"{story_id}-{number:03d}"
    
    @staticmethod
    def generate_title(internal_id: str, feature: str, module: str, 
                      category: str, subcategory: str, description: str) -> str:
        """
        Generate test case title following strict format.
        
        Format: {InternalID}: <Feature> / <Module> / <Category> / <SubCategory> / <Description>
        
        All separators must be preserved as forward slashes with spaces.
        No emojis, markdown, or formatting symbols allowed.
        
        Args:
            internal_id: Internal test case ID
            feature: Feature name
            module: Module name
            category: Category name
            subcategory: Subcategory name
            description: Test case description
            
        Returns:
            Formatted title string
            
        Example:
            >>> TestCaseNaming.generate_title(
            ...     "271309-AC1", "User Management", "Authentication",
            ...     "Login", "Happy Path", "Verify user can login with valid credentials"
            ... )
            '271309-AC1: User Management / Authentication / Login / Happy Path / Verify user can login with valid credentials'
        """
        # Clean all components to remove any formatting artifacts
        components = [feature, module, category, subcategory, description]
        cleaned = [comp.strip().replace("/", "-") for comp in components]  # Replace / in components to avoid confusion
        
        title = f"{internal_id}: {' / '.join(cleaned)}"
        
        # ADO System.Title field has a maximum length of 256 characters
        # Truncate to 250 to be safe, preserving the internal_id prefix
        MAX_TITLE_LENGTH = 250
        if len(title) > MAX_TITLE_LENGTH:
            # Keep internal_id and separators, truncate description
            prefix = f"{internal_id}: {' / '.join(cleaned[:4])} / "
            max_desc_length = MAX_TITLE_LENGTH - len(prefix)
            if max_desc_length > 0:
                truncated_desc = cleaned[4][:max_desc_length - 3] + "..."
                title = prefix + truncated_desc
            else:
                # If even the prefix is too long, just use internal_id
                title = f"{internal_id}: Test Case"
        
        return title
    
    @staticmethod
    def extract_feature_module_from_ac(ac_text: str) -> tuple[str, str]:
        """
        Extract feature and module names from AC text.
        
        This is a simple rule-based extraction. In a research context,
        this could be replaced with ML-based extraction.
        
        Args:
            ac_text: Acceptance criterion text
            
        Returns:
            Tuple of (feature, module)
        """
        # Default values - can be enhanced with ML
        # For now, use generic values that can be customized
        feature = "Application"
        module = "Core Functionality"
        
        # Simple keyword-based extraction (can be enhanced)
        ac_lower = ac_text.lower()
        
        if any(word in ac_lower for word in ["login", "authentication", "auth"]):
            feature = "User Management"
            module = "Authentication"
        elif any(word in ac_lower for word in ["save", "persist", "storage"]):
            feature = "Data Management"
            module = "Persistence"
        elif any(word in ac_lower for word in ["delete", "remove"]):
            feature = "Data Management"
            module = "Deletion"
        elif any(word in ac_lower for word in ["create", "add", "new"]):
            feature = "Data Management"
            module = "Creation"
        elif any(word in ac_lower for word in ["edit", "update", "modify"]):
            feature = "Data Management"
            module = "Modification"
        
        return feature, module
    
    @staticmethod
    def get_category_subcategory(test_type: TestCaseType) -> tuple[str, str]:
        """
        Get category and subcategory based on test type.
        
        Args:
            test_type: Type of test case
            
        Returns:
            Tuple of (category, subcategory)
        """
        mapping = {
            TestCaseType.HAPPY_PATH: ("Functional", "Happy Path"),
            TestCaseType.NEGATIVE: ("Functional", "Negative"),
            TestCaseType.BOUNDARY: ("Functional", "Boundary"),
            TestCaseType.CANCEL_ROLLBACK: ("Functional", "Cancel/Rollback"),
            TestCaseType.PERSISTENCE: ("Functional", "Persistence"),
            TestCaseType.UNDO_REDO: ("Functional", "Undo/Redo"),
            TestCaseType.ACCESSIBILITY: ("Accessibility", "WCAG 2.1 AA"),
            TestCaseType.UMBRELLA: ("Verification", "Sign-off"),
        }
        
        return mapping.get(test_type, ("Functional", "General"))

