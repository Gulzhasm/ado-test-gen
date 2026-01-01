"""
Hard validation and sanitization for test cases.

This module enforces strict ADO naming and step rules,
rejecting any test case that doesn't comply.
"""
import re
from typing import List, Optional
from src.models.test_case import TestCase, TestStep, TestCaseType
from src.generation.title_builder import TitleBuilder


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class TestCaseValidator:
    """
    Validates and sanitizes test cases according to strict ADO rules.
    
    All LLM-generated content must pass through this validator before
    being published to ADO.
    """
    
    # Forbidden words in short descriptor
    FORBIDDEN_WORDS = TitleBuilder.FORBIDDEN_WORDS
    
    # Forbidden punctuation
    FORBIDDEN_PUNCTUATION = TitleBuilder.FORBIDDEN_PUNCTUATION
    
    # Exit step constants
    EXIT_ACTION = "Close/Exit the QuickDraw application."
    EXIT_EXPECTED = "Application closes successfully without crash or freeze; no error dialogs are shown during exit."
    
    @staticmethod
    def sanitize_short_descriptor(text: str) -> str:
        """
        Sanitize short descriptor text.
        
        Removes forbidden punctuation and normalizes whitespace.
        
        Args:
            text: Raw short descriptor text
            
        Returns:
            Sanitized text
        """
        # Remove forbidden punctuation
        for punct in TestCaseValidator.FORBIDDEN_PUNCTUATION:
            text = text.replace(punct, "")
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def validate_short_descriptor(text: str) -> bool:
        """
        Validate short descriptor against rules.
        
        Rules:
        - <= 8 words
        - No forbidden words
        - No forbidden punctuation
        
        Args:
            text: Short descriptor to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check word count
        words = text.split()
        if len(words) > 8:
            return False
        
        # Check for forbidden words (case-insensitive)
        text_lower = text.lower()
        for word in TestCaseValidator.FORBIDDEN_WORDS:
            if word in text_lower:
                return False
        
        # Check for forbidden punctuation
        for punct in TestCaseValidator.FORBIDDEN_PUNCTUATION:
            if punct in text:
                return False
        
        return True
    
    @staticmethod
    def validate_title_format(title: str, internal_id: str) -> bool:
        """
        Validate title format.
        
        Format: {InternalId}: {Feature} / {Module} / {Category} / {Subcategory} / {Short Descriptor}
        
        Args:
            title: Title to validate
            internal_id: Expected internal ID
            
        Returns:
            True if format is valid, False otherwise
        """
        # Must start with internal ID
        if not title.startswith(f"{internal_id}:"):
            return False
        
        # Must have 4 slashes (5 segments after ID)
        parts = title.split(" / ")
        if len(parts) != 5:
            return False
        
        # Last part is short descriptor - validate it
        short_descriptor = parts[-1]
        return TestCaseValidator.validate_short_descriptor(short_descriptor)
    
    @staticmethod
    def validate_steps(steps: List[TestStep]) -> bool:
        """
        Validate test steps.
        
        Rules:
        - Non-empty list
        - Each step has action and expected
        - Plain text only (no markdown)
        
        Args:
            steps: List of test steps
            
        Returns:
            True if valid, False otherwise
        """
        if not steps:
            return False
        
        for step in steps:
            if not step.action or not step.expected_result:
                return False
            
            # Check for markdown (basic check)
            if step.action.startswith("#") or step.expected_result.startswith("#"):
                return False
            if "```" in step.action or "```" in step.expected_result:
                return False
        
        return True
    
    @staticmethod
    def strip_markdown(text: str) -> str:
        """
        Strip markdown formatting from text.
        
        Args:
            text: Text that may contain markdown
            
        Returns:
            Plain text
        """
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        # Remove inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # Remove headers
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        # Remove bold/italic
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        # Remove links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def append_exit_step(steps: List[TestStep]) -> List[TestStep]:
        """
        Append mandatory exit step to test steps.
        
        Args:
            steps: Existing test steps
            
        Returns:
            Steps with exit step appended
        """
        # Check if exit step already exists
        has_exit = any(
            step.action == TestCaseValidator.EXIT_ACTION
            for step in steps
        )
        
        if has_exit:
            return steps
        
        # Create exit step
        exit_step = TestStep(
            action=TestCaseValidator.EXIT_ACTION,
            expected_result=TestCaseValidator.EXIT_EXPECTED,
            step_number=len(steps) + 1
        )
        
        return steps + [exit_step]
    
    @staticmethod
    def validate_and_canonicalize(
        testcase_draft: dict,
        story_id: int,
        internal_id: str,
        feature: str,
        module: str,
        category: str,
        subcategory: str
    ) -> Optional[TestCase]:
        """
        Validate and canonicalize a test case draft.
        
        This is the main validation entry point. It:
        1. Validates short descriptor
        2. Builds title using TitleBuilder
        3. Validates steps
        4. Strips markdown from steps
        5. Appends exit step
        6. Creates final TestCase object
        
        Args:
            testcase_draft: Draft test case with:
                - short_descriptor: str
                - steps: List[dict] with "action" and "expected"
                - tags: List[str] (optional)
            story_id: User Story ID
            internal_id: Internal test case ID
            feature: Feature name
            module: Module name
            category: Category name
            subcategory: Subcategory name
            
        Returns:
            Validated TestCase or None if validation fails
        """
        try:
            # Sanitize and validate short descriptor
            short_descriptor = testcase_draft.get("short_descriptor", "")
            short_descriptor = TestCaseValidator.sanitize_short_descriptor(short_descriptor)
            
            if not TestCaseValidator.validate_short_descriptor(short_descriptor):
                return None
            
            # Build title using TitleBuilder
            from src.generation.title_builder import TitleBuilder
            title = TitleBuilder.build(
                internal_id=internal_id,
                feature=feature,
                module=module,
                category=category,
                subcategory=subcategory,
                short_descriptor=short_descriptor
            )
            
            # Validate title format
            if not TestCaseValidator.validate_title_format(title, internal_id):
                return None
            
            # Process steps
            raw_steps = testcase_draft.get("steps", [])
            if not raw_steps:
                return None
            
            # Convert to TestStep objects, stripping markdown
            steps = []
            for i, step_dict in enumerate(raw_steps, 1):
                action = TestCaseValidator.strip_markdown(step_dict.get("action", ""))
                expected = TestCaseValidator.strip_markdown(step_dict.get("expected", ""))
                
                if not action or not expected:
                    return None
                
                steps.append(TestStep(
                    action=action,
                    expected_result=expected,
                    step_number=i
                ))
            
            # Validate steps
            if not TestCaseValidator.validate_steps(steps):
                return None
            
            # Append exit step
            steps = TestCaseValidator.append_exit_step(steps)
            
            # Re-number steps
            for i, step in enumerate(steps, 1):
                # TestStep is frozen, so we need to recreate
                steps[i-1] = TestStep(
                    action=step.action,
                    expected_result=step.expected_result,
                    step_number=i
                )
            
            # Get tags
            tags = testcase_draft.get("tags", [])
            
            # Create TestCase
            return TestCase(
                internal_id=internal_id,
                title=title,
                steps=steps,
                test_type=TestCaseType.HAPPY_PATH,  # Default for LLM-generated
                acceptance_criterion_id=None,  # LLM tests may span multiple ACs
                story_id=story_id,
                tags=tags
            )
            
        except Exception as e:
            # Validation failed
            return None

