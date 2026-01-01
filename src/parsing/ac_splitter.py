"""
Acceptance Criteria splitting module.

This module splits AC text into individual items using bullet-aware
and sentence-based splitting strategies.

Research Note: This module can be enhanced with NLP-based sentence
boundary detection (spaCy) for better handling of complex AC text.
"""
import re
from typing import List


class ACSplitter:
    """
    Splits Acceptance Criteria text into individual items.
    
    Handles:
    - Numbered lists (1., 2., etc.)
    - Bullet lists (•, -, *, etc.)
    - Sentence boundaries (fallback)
    """
    
    # Patterns for list detection
    NUMBERED_PATTERN = r'^\s*(?:\d+[.)]\s*|\d+\)\s*)'
    BULLET_PATTERN = r'^\s*[•\-\*]\s+'
    
    @staticmethod
    def split(ac_text: str) -> List[str]:
        """
        Split AC text into individual items.
        
        Priority:
        1. Numbered lists
        2. Bullet lists
        3. Sentence boundaries (fallback)
        
        Args:
            ac_text: Raw AC text (may contain multiple items)
            
        Returns:
            List of individual AC items
        """
        if not ac_text or not ac_text.strip():
            return []
        
        # Normalize whitespace
        ac_text = re.sub(r'\s+', ' ', ac_text.strip())
        
        # Try numbered list first
        if re.search(ACSplitter.NUMBERED_PATTERN, ac_text, re.MULTILINE):
            return ACSplitter._split_numbered(ac_text)
        
        # Try bullet list
        if re.search(ACSplitter.BULLET_PATTERN, ac_text, re.MULTILINE):
            return ACSplitter._split_bullets(ac_text)
        
        # Fallback to sentence splitting
        return ACSplitter._split_sentences(ac_text)
    
    @staticmethod
    def _split_numbered(text: str) -> List[str]:
        """Split by numbered list items."""
        items = []
        # Split by numbered items
        parts = re.split(r'\n\s*(?=\d+[.)]\s*|\d+\)\s*)', text)
        for part in parts:
            # Remove numbering prefix
            part = re.sub(ACSplitter.NUMBERED_PATTERN, '', part).strip()
            if part:
                items.append(part)
        return items
    
    @staticmethod
    def _split_bullets(text: str) -> List[str]:
        """Split by bullet list items."""
        items = []
        parts = re.split(r'\n\s*[•\-\*]\s+', text)
        for part in parts:
            part = part.strip()
            if part:
                items.append(part)
        return items
    
    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """
        Split by sentence boundaries (fallback).
        
        Uses simple period-based splitting, but can be enhanced
        with NLP sentence tokenization.
        """
        # Simple sentence splitting (can be enhanced with spaCy)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        items = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Filter very short fragments
                items.append(sentence)
        return items if items else [text]  # Return original if no splits

