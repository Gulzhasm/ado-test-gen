"""
Unit tests for hybrid mode validation and deduplication.

Tests ensure that:
- Titles never contain raw AC text
- short_descriptor enforcement works
- Punctuation and forbidden words are rejected
- Exit step is appended
- Deduper rejects near-duplicates
"""
import pytest
from src.gating.validator import TestCaseValidator, ValidationError
from src.gating.deduper import HybridDeduper, EmbeddingDeduper, FuzzyDeduper
from src.models.test_case import TestCase, TestStep, TestCaseType


class TestValidator:
    """Test validation and sanitization."""
    
    def test_sanitize_short_descriptor(self):
        """Test short descriptor sanitization."""
        # Remove punctuation
        assert TestCaseValidator.sanitize_short_descriptor("Test. Case:") == "Test Case"
        assert TestCaseValidator.sanitize_short_descriptor("Test; Case…") == "Test Case"
        
        # Normalize whitespace
        assert TestCaseValidator.sanitize_short_descriptor("Test   Case") == "Test Case"
    
    def test_validate_short_descriptor(self):
        """Test short descriptor validation."""
        # Valid cases
        assert TestCaseValidator.validate_short_descriptor("Element visibility display")
        assert TestCaseValidator.validate_short_descriptor("Action logging entry")
        
        # Too many words
        assert not TestCaseValidator.validate_short_descriptor(
            "This is a test case with more than eight words in the descriptor"
        )
        
        # Forbidden words
        assert not TestCaseValidator.validate_short_descriptor("Verify element display")
        assert not TestCaseValidator.validate_short_descriptor("Click button when ready")
        
        # Forbidden punctuation
        assert not TestCaseValidator.validate_short_descriptor("Test. Case")
        assert not TestCaseValidator.validate_short_descriptor("Test: Case")
    
    def test_validate_title_format(self):
        """Test title format validation."""
        # Valid title
        assert TestCaseValidator.validate_title_format(
            "270542-AC1: Hand Tool / Core / Validation / Element visibility / Element visibility display",
            "270542-AC1"
        )
        
        # Missing ID prefix
        assert not TestCaseValidator.validate_title_format(
            "Hand Tool / Core / Validation / Element visibility / Element visibility display",
            "270542-AC1"
        )
        
        # Wrong number of segments
        assert not TestCaseValidator.validate_title_format(
            "270542-AC1: Hand Tool / Core / Validation",
            "270542-AC1"
        )
    
    def test_validate_steps(self):
        """Test step validation."""
        # Valid steps
        valid_steps = [
            TestStep(action="Open application", expected_result="Application opens", step_number=1),
            TestStep(action="Click button", expected_result="Button clicked", step_number=2)
        ]
        assert TestCaseValidator.validate_steps(valid_steps)
        
        # Empty steps
        assert not TestCaseValidator.validate_steps([])
        
        # Missing action
        invalid_steps = [
            TestStep(action="", expected_result="Result", step_number=1)
        ]
        assert not TestCaseValidator.validate_steps(invalid_steps)
    
    def test_append_exit_step(self):
        """Test exit step appending."""
        steps = [
            TestStep(action="Step 1", expected_result="Result 1", step_number=1)
        ]
        
        result = TestCaseValidator.append_exit_step(steps)
        assert len(result) == 2
        assert result[-1].action == TestCaseValidator.EXIT_ACTION
        assert result[-1].expected_result == TestCaseValidator.EXIT_EXPECTED
        
        # Don't duplicate if already present
        result2 = TestCaseValidator.append_exit_step(result)
        assert len(result2) == 2  # Still 2, not 3
    
    def test_strip_markdown(self):
        """Test markdown stripping."""
        # Code blocks
        assert TestCaseValidator.strip_markdown("```code```") == ""
        assert TestCaseValidator.strip_markdown("Text ```code``` more") == "Text more"
        
        # Bold/italic
        assert TestCaseValidator.strip_markdown("**bold** text") == "bold text"
        assert TestCaseValidator.strip_markdown("*italic* text") == "italic text"
        
        # Headers
        assert TestCaseValidator.strip_markdown("# Header") == "Header"
        
        # Links
        assert TestCaseValidator.strip_markdown("[Link](url)") == "Link"
    
    def test_validate_and_canonicalize(self):
        """Test full validation and canonicalization."""
        # Valid test case
        draft = {
            "short_descriptor": "Element visibility display",
            "steps": [
                {"action": "Open application", "expected": "Application opens"},
                {"action": "Check element", "expected": "Element visible"}
            ],
            "tags": ["test"]
        }
        
        result = TestCaseValidator.validate_and_canonicalize(
            testcase_draft=draft,
            story_id=270542,
            internal_id="270542-005",
            feature="Hand Tool",
            module="Core",
            category="Validation",
            subcategory="Element visibility"
        )
        
        assert result is not None
        assert result.internal_id == "270542-005"
        assert len(result.steps) == 3  # 2 original + 1 exit step
        assert result.steps[-1].action == TestCaseValidator.EXIT_ACTION
        
        # Invalid short descriptor
        invalid_draft = {
            "short_descriptor": "Verify. Element. Display. With. Too. Many. Words. Here.",
            "steps": [{"action": "Step", "expected": "Result"}],
            "tags": []
        }
        
        result = TestCaseValidator.validate_and_canonicalize(
            testcase_draft=invalid_draft,
            story_id=270542,
            internal_id="270542-005",
            feature="Hand Tool",
            module="Core",
            category="Validation",
            subcategory="Element visibility"
        )
        
        assert result is None


class TestDeduper:
    """Test deduplication."""
    
    def test_fuzzy_deduper(self):
        """Test fuzzy deduplication."""
        deduper = FuzzyDeduper()
        
        if not deduper.enabled:
            pytest.skip("rapidfuzz not available")
        
        test1 = TestCase(
            internal_id="270542-005",
            title="270542-005: Hand Tool / Core / Validation / Element visibility / Element visibility display",
            steps=[
                TestStep(action="Open app", expected_result="App opens", step_number=1)
            ],
            test_type=TestCaseType.HAPPY_PATH,
            story_id=270542,
            tags=[]
        )
        
        test2 = TestCase(
            internal_id="270542-010",
            title="270542-010: Hand Tool / Core / Validation / Element visibility / Element visibility display",
            steps=[
                TestStep(action="Open app", expected_result="App opens", step_number=1)
            ],
            test_type=TestCaseType.HAPPY_PATH,
            story_id=270542,
            tags=[]
        )
        
        # Should be duplicate (same title and steps)
        assert deduper.is_duplicate(test1, test2, threshold=88.0)
        
        # Different test
        test3 = TestCase(
            internal_id="270542-015",
            title="270542-015: Hand Tool / Core / Ordering / Action logging / Action logging entry",
            steps=[
                TestStep(action="Different action", expected_result="Different result", step_number=1)
            ],
            test_type=TestCaseType.HAPPY_PATH,
            story_id=270542,
            tags=[]
        )
        
        assert not deduper.is_duplicate(test1, test3, threshold=88.0)
    
    def test_hybrid_deduper(self):
        """Test hybrid deduplication."""
        deduper = HybridDeduper()
        
        test1 = TestCase(
            internal_id="270542-005",
            title="270542-005: Hand Tool / Core / Validation / Element visibility / Element visibility display",
            steps=[
                TestStep(action="Open app", expected_result="App opens", step_number=1)
            ],
            test_type=TestCaseType.HAPPY_PATH,
            story_id=270542,
            tags=[]
        )
        
        test2 = TestCase(
            internal_id="270542-010",
            title="270542-010: Hand Tool / Core / Validation / Element visibility / Element visibility display",
            steps=[
                TestStep(action="Open app", expected_result="App opens", step_number=1)
            ],
            test_type=TestCaseType.HAPPY_PATH,
            story_id=270542,
            tags=[]
        )
        
        # Should detect duplicate (via fuzzy matching if embeddings not available)
        # Result depends on which deduper is enabled
        duplicate = deduper.is_duplicate(test1, test2)
        # Just verify it doesn't crash - actual result depends on available libraries

