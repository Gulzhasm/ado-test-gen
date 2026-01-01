"""
Unit tests for TestCaseNaming ID generation.

Tests ensure:
- First test case: {StoryId}-AC1
- Subsequent: increments by 5 (005, 010, 015, etc.)
"""
import pytest
from src.generation.naming import TestCaseNaming


class TestTestCaseNaming:
    """Test cases for ID generation."""
    
    def test_first_id_is_ac1(self):
        """Test that first test case (index 0) gets -AC1 suffix."""
        assert TestCaseNaming.generate_internal_id(270542, 0) == "270542-AC1"
    
    def test_second_id_is_005(self):
        """Test that second test case (index 1) gets -005 suffix."""
        assert TestCaseNaming.generate_internal_id(270542, 1) == "270542-005"
    
    def test_third_id_is_010(self):
        """Test that third test case (index 2) gets -010 suffix."""
        assert TestCaseNaming.generate_internal_id(270542, 2) == "270542-010"
    
    def test_fourth_id_is_015(self):
        """Test that fourth test case (index 3) gets -015 suffix."""
        assert TestCaseNaming.generate_internal_id(270542, 3) == "270542-015"
    
    def test_id_increments_by_five(self):
        """Test that IDs increment by 5 after the first one."""
        story_id = 270542
        assert TestCaseNaming.generate_internal_id(story_id, 1) == "270542-005"
        assert TestCaseNaming.generate_internal_id(story_id, 2) == "270542-010"
        assert TestCaseNaming.generate_internal_id(story_id, 3) == "270542-015"
        assert TestCaseNaming.generate_internal_id(story_id, 4) == "270542-020"
        assert TestCaseNaming.generate_internal_id(story_id, 5) == "270542-025"
    
    def test_id_format_padding(self):
        """Test that numeric IDs are zero-padded to 3 digits."""
        story_id = 270542
        assert TestCaseNaming.generate_internal_id(story_id, 1) == "270542-005"
        assert TestCaseNaming.generate_internal_id(story_id, 20) == "270542-100"

