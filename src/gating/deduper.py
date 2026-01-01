"""
Deduplication using embeddings and fuzzy matching.

This module provides two-layer deduplication:
1. Embedding similarity (sentence-transformers)
2. Fuzzy string matching (rapidfuzz)
"""
from typing import List, Optional, Tuple
from src.models.test_case import TestCase
import warnings

# Optional imports with graceful fallback
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    SentenceTransformer = None
    cosine_similarity = None
    np = None

try:
    from rapidfuzz import fuzz
    HAS_FUZZY = True
except ImportError:
    HAS_FUZZY = False
    fuzz = None


class EmbeddingDeduper:
    """
    Deduplication using sentence embeddings and cosine similarity.
    
    Uses sentence-transformers to compute embeddings and compares
    test cases using cosine similarity.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding deduper.
        
        Args:
            model_name: Sentence transformer model name
        """
        if not HAS_EMBEDDINGS:
            self.model = None
            self.enabled = False
        else:
            try:
                self.model = SentenceTransformer(model_name)
                self.enabled = True
            except Exception:
                self.model = None
                self.enabled = False
    
    def is_duplicate(
        self,
        candidate: TestCase,
        existing: TestCase,
        threshold: float = 0.88
    ) -> bool:
        """
        Check if candidate is duplicate of existing using embeddings.
        
        Args:
            candidate: Candidate test case
            existing: Existing test case to compare against
            threshold: Cosine similarity threshold (default: 0.88)
            
        Returns:
            True if duplicate, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Build text representations
            candidate_text = self._build_text(candidate)
            existing_text = self._build_text(existing)
            
            # Compute embeddings
            candidate_emb = self.model.encode([candidate_text])
            existing_emb = self.model.encode([existing_text])
            
            # Compute cosine similarity
            similarity = cosine_similarity(candidate_emb, existing_emb)[0][0]
            
            return similarity > threshold
        except Exception:
            # On error, don't consider duplicate
            return False
    
    def _build_text(self, test_case: TestCase) -> str:
        """
        Build text representation of test case for embedding.
        
        Args:
            test_case: Test case to represent
            
        Returns:
            Combined text (title + steps)
        """
        parts = [test_case.title]
        for step in test_case.steps:
            parts.append(step.action)
            parts.append(step.expected_result)
        return " ".join(parts)


class FuzzyDeduper:
    """
    Deduplication using fuzzy string matching.
    
    Uses rapidfuzz to compare normalized titles and step text.
    """
    
    def __init__(self):
        """Initialize fuzzy deduper."""
        self.enabled = HAS_FUZZY
    
    def is_duplicate(
        self,
        candidate: TestCase,
        existing: TestCase,
        threshold: float = 88.0
    ) -> bool:
        """
        Check if candidate is duplicate of existing using fuzzy matching.
        
        Args:
            candidate: Candidate test case
            existing: Existing test case to compare against
            threshold: Similarity ratio threshold (default: 88.0)
            
        Returns:
            True if duplicate, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Normalize and compare titles
            candidate_title = self._normalize(candidate.title)
            existing_title = self._normalize(existing.title)
            
            title_ratio = fuzz.ratio(candidate_title, existing_title)
            if title_ratio > threshold:
                return True
            
            # Compare step text
            candidate_steps = self._build_steps_text(candidate)
            existing_steps = self._build_steps_text(existing)
            
            steps_ratio = fuzz.ratio(candidate_steps, existing_steps)
            if steps_ratio > threshold:
                return True
            
            return False
        except Exception:
            # On error, don't consider duplicate
            return False
    
    def _normalize(self, text: str) -> str:
        """
        Normalize text for comparison.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text (lowercase, no extra whitespace)
        """
        return " ".join(text.lower().split())
    
    def _build_steps_text(self, test_case: TestCase) -> str:
        """
        Build combined steps text.
        
        Args:
            test_case: Test case
            
        Returns:
            Combined steps text
        """
        parts = []
        for step in test_case.steps:
            parts.append(step.action)
            parts.append(step.expected_result)
        return self._normalize(" ".join(parts))


class HybridDeduper:
    """
    Hybrid deduplication combining embeddings and fuzzy matching.
    
    Uses both embedding similarity and fuzzy matching, rejecting
    if either method indicates a duplicate.
    """
    
    def __init__(
        self,
        embedding_threshold: float = 0.88,
        fuzzy_threshold: float = 88.0
    ):
        """
        Initialize hybrid deduper.
        
        Args:
            embedding_threshold: Cosine similarity threshold
            fuzzy_threshold: Fuzzy ratio threshold
        """
        self.embedding_deduper = EmbeddingDeduper()
        self.fuzzy_deduper = FuzzyDeduper()
        self.embedding_threshold = embedding_threshold
        self.fuzzy_threshold = fuzzy_threshold
    
    def is_duplicate(
        self,
        candidate: TestCase,
        existing: TestCase
    ) -> bool:
        """
        Check if candidate is duplicate using hybrid approach.
        
        Returns True if EITHER embedding OR fuzzy matching indicates duplicate.
        
        Args:
            candidate: Candidate test case
            existing: Existing test case to compare against
            
        Returns:
            True if duplicate, False otherwise
        """
        # Try embedding first (if available)
        if self.embedding_deduper.enabled:
            if self.embedding_deduper.is_duplicate(
                candidate, existing, self.embedding_threshold
            ):
                return True
        
        # Try fuzzy matching (if available)
        if self.fuzzy_deduper.enabled:
            if self.fuzzy_deduper.is_duplicate(
                candidate, existing, self.fuzzy_threshold
            ):
                return True
        
        # If neither is enabled, don't consider duplicate
        return False
    
    def find_duplicates(
        self,
        candidate: TestCase,
        existing_list: List[TestCase]
    ) -> List[TestCase]:
        """
        Find all duplicates of candidate in existing list.
        
        Args:
            candidate: Candidate test case
            existing_list: List of existing test cases
            
        Returns:
            List of duplicate test cases
        """
        duplicates = []
        for existing in existing_list:
            if self.is_duplicate(candidate, existing):
                duplicates.append(existing)
        return duplicates

