"""
Unit tests for ACSplitter.

Tests ensure AC text is split correctly into individual items.
"""
import pytest
from src.parsing.ac_splitter import ACSplitter


class TestACSplitter:
    """Test cases for AC splitting."""
    
    def test_split_numbered_list(self):
        """Test splitting numbered list."""
        ac_text = "1. First item. 2. Second item. 3. Third item."
        items = ACSplitter.split(ac_text)
        assert len(items) == 3
        assert "First item" in items[0]
        assert "Second item" in items[1]
        assert "Third item" in items[2]
    
    def test_split_bullet_list(self):
        """Test splitting bullet list."""
        ac_text = "- First item\n- Second item\n- Third item"
        items = ACSplitter.split(ac_text)
        assert len(items) == 3
    
    def test_split_sentences(self):
        """Test splitting by sentences (fallback)."""
        ac_text = "First sentence. Second sentence. Third sentence."
        items = ACSplitter.split(ac_text)
        assert len(items) >= 2
    
    def test_empty_text(self):
        """Test that empty text returns empty list."""
        assert ACSplitter.split("") == []
        assert ACSplitter.split("   ") == []
    
    def test_single_item(self):
        """Test that single item returns single-element list."""
        ac_text = "Single acceptance criterion."
        items = ACSplitter.split(ac_text)
        assert len(items) >= 1

