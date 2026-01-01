"""
Unit tests for TitleBuilder validation rules.

Tests ensure:
- Title suffix <= 8 words
- No forbidden words (verify, when, click, then, etc.)
- No forbidden punctuation
- Proper title format
"""
import pytest
from src.generation.title_builder import TitleBuilder


class TestTitleBuilder:
    """Test cases for TitleBuilder validation."""
    
    def test_valid_title(self):
        """Test building a valid title."""
        title = TitleBuilder.build(
            internal_id="270542-AC1",
            feature="Hand Tool",
            module="Core",
            category="Functional",
            subcategory="Happy Path",
            short_descriptor="Element visibility display"
        )
        assert title.startswith("270542-AC1:")
        assert "Element visibility display" in title
    
    def test_title_suffix_too_many_words(self):
        """Test that title suffix with > 8 words raises ValueError."""
        with pytest.raises(ValueError, match="must be <= 8 words"):
            TitleBuilder.build(
                internal_id="270542-AC1",
                feature="Feature",
                module="Module",
                category="Category",
                subcategory="Subcategory",
                short_descriptor="one two three four five six seven eight nine ten"
            )
    
    def test_title_suffix_forbidden_word_verify(self):
        """Test that 'verify' in short descriptor raises ValueError."""
        with pytest.raises(ValueError, match="forbidden word 'verify'"):
            TitleBuilder.build(
                internal_id="270542-AC1",
                feature="Feature",
                module="Module",
                category="Category",
                subcategory="Subcategory",
                short_descriptor="verify element display"
            )
    
    def test_title_suffix_forbidden_word_when(self):
        """Test that 'when' in short descriptor raises ValueError."""
        with pytest.raises(ValueError, match="forbidden word 'when'"):
            TitleBuilder.build(
                internal_id="270542-AC1",
                feature="Feature",
                module="Module",
                category="Category",
                subcategory="Subcategory",
                short_descriptor="element display when clicked"
            )
    
    def test_title_suffix_forbidden_word_click(self):
        """Test that 'click' in short descriptor raises ValueError."""
        with pytest.raises(ValueError, match="forbidden word 'click'"):
            TitleBuilder.build(
                internal_id="270542-AC1",
                feature="Feature",
                module="Module",
                category="Category",
                subcategory="Subcategory",
                short_descriptor="button click behavior"
            )
    
    def test_title_suffix_forbidden_punctuation_period(self):
        """Test that period in short descriptor raises ValueError."""
        with pytest.raises(ValueError, match="forbidden punctuation"):
            TitleBuilder.build(
                internal_id="270542-AC1",
                feature="Feature",
                module="Module",
                category="Category",
                subcategory="Subcategory",
                short_descriptor="element display."
            )
    
    def test_title_suffix_forbidden_punctuation_colon(self):
        """Test that colon in short descriptor raises ValueError."""
        with pytest.raises(ValueError, match="forbidden punctuation"):
            TitleBuilder.build(
                internal_id="270542-AC1",
                feature="Feature",
                module="Module",
                category="Category",
                subcategory="Subcategory",
                short_descriptor="element display: test"
            )
    
    def test_title_suffix_forbidden_punctuation_semicolon(self):
        """Test that semicolon in short descriptor raises ValueError."""
        with pytest.raises(ValueError, match="forbidden punctuation"):
            TitleBuilder.build(
                internal_id="270542-AC1",
                feature="Feature",
                module="Module",
                category="Category",
                subcategory="Subcategory",
                short_descriptor="element display; test"
            )
    
    def test_title_suffix_empty(self):
        """Test that empty short descriptor raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            TitleBuilder.build(
                internal_id="270542-AC1",
                feature="Feature",
                module="Module",
                category="Category",
                subcategory="Subcategory",
                short_descriptor=""
            )
    
    def test_title_format(self):
        """Test that title follows correct format."""
        title = TitleBuilder.build(
            internal_id="270542-AC1",
            feature="Hand Tool",
            module="Core",
            category="Functional",
            subcategory="Happy Path",
            short_descriptor="element visibility"
        )
        parts = title.split(" / ")
        assert len(parts) == 5
        assert parts[0].startswith("270542-AC1:")
        assert parts[1] == "Hand Tool"
        assert parts[2] == "Core"
        assert parts[3] == "Functional"
        assert parts[4] == "Happy Path"
        # Last part should be after the last /
        assert "element visibility" in title
    
    def test_title_truncation(self):
        """Test that very long titles are truncated."""
        title = TitleBuilder.build(
            internal_id="270542-AC1",
            feature="Very Long Feature Name That Exceeds Normal Length",
            module="Very Long Module Name",
            category="Very Long Category Name",
            subcategory="Very Long Subcategory Name",
            short_descriptor="element visibility display"
        )
        assert len(title) <= 250
        assert title.startswith("270542-AC1:")

