"""
Acceptance Criteria extraction and normalization.

This module extracts Acceptance Criteria from User Story descriptions,
handles various formats (dedicated field vs. embedded in description),
and normalizes them into a structured format.

Research Note: This module is designed to be replaced or enhanced with
ML-based extraction for better handling of unstructured AC formats.
"""
import re
from typing import List, Optional
from src.parsing.html_parser import html_to_text


class AcceptanceCriteriaExtractor:
    """
    Extracts and normalizes Acceptance Criteria from User Story content.
    
    Handles multiple AC formats:
    - Dedicated Acceptance Criteria field
    - Embedded in Description with headers (e.g., "Acceptance Criteria:", "AC:")
    - Numbered lists
    - Bullet lists
    - Plain text paragraphs
    """
    
    # Common patterns for AC section headers
    AC_HEADER_PATTERNS = [
        r'acceptance\s+criteria:?',
        r'ac:?',
        r'acceptance\s+criteria\s+are:?',
        r'criteria:?',
        r'acceptance\s+requirements:?',
    ]
    
    def __init__(self):
        """Initialize the extractor."""
        pass
    
    def extract_from_field(self, ac_html: Optional[str]) -> List[str]:
        """
        Extract AC from dedicated Acceptance Criteria field.
        
        Args:
            ac_html: HTML content from Microsoft.VSTS.Common.AcceptanceCriteria field
            
        Returns:
            List of individual AC items
        """
        if not ac_html:
            return []
        
        text = html_to_text(ac_html)
        return self._parse_ac_items(text)
    
    def extract_from_description(self, description_html: str) -> List[str]:
        """
        Extract AC from Description field by detecting AC section.
        
        Args:
            description_html: HTML content from Description field
            
        Returns:
            List of individual AC items
        """
        if not description_html:
            return []
        
        text = html_to_text(description_html)
        
        # Try to find AC section
        ac_section = self._find_ac_section(text)
        if ac_section:
            return self._parse_ac_items(ac_section)
        
        return []
    
    def _find_ac_section(self, text: str) -> Optional[str]:
        """
        Find the Acceptance Criteria section in text.
        
        Searches for common AC header patterns and extracts content after them.
        
        Args:
            text: Full text to search
            
        Returns:
            AC section text, or None if not found
        """
        text_lower = text.lower()
        
        for pattern in self.AC_HEADER_PATTERNS:
            regex = re.compile(pattern, re.IGNORECASE)
            match = regex.search(text)
            if match:
                # Extract everything after the header
                start_pos = match.end()
                ac_section = text[start_pos:].strip()
                
                # Try to find where AC section ends (next major header)
                # Look for common section headers
                end_patterns = [
                    r'\n\s*(?:notes?:|additional\s+info:||technical\s+details:||implementation\s+notes:)',
                    r'\n\s*#{1,3}\s+',  # Markdown headers
                ]
                
                for end_pattern in end_patterns:
                    end_match = re.search(end_pattern, ac_section, re.IGNORECASE)
                    if end_match:
                        ac_section = ac_section[:end_match.start()].strip()
                        break
                
                return ac_section
        
        return None
    
    def _parse_ac_items(self, ac_text: str) -> List[str]:
        """
        Parse AC text into individual items.
        
        Handles:
        - Numbered lists (1., 2., etc.)
        - Bullet lists (•, -, *, etc.)
        - Plain paragraphs separated by blank lines
        
        Args:
            ac_text: AC section text
            
        Returns:
            List of normalized AC items
        """
        if not ac_text:
            return []
        
        items = []
        
        # Split by common list patterns
        # Pattern 1: Numbered lists (1., 2., 3., etc. or 1), 2), etc.)
        numbered_pattern = r'^\s*(?:\d+[.)]\s*|\d+\)\s*)'
        if re.search(numbered_pattern, ac_text, re.MULTILINE):
            # Split by numbered items
            parts = re.split(r'\n\s*(?=\d+[.)]\s*|\d+\)\s*)', ac_text)
            for part in parts:
                part = re.sub(numbered_pattern, '', part).strip()
                if part:
                    items.append(part)
        
        # Pattern 2: Bullet lists (•, -, *, etc.)
        elif re.search(r'^\s*[•\-\*]\s+', ac_text, re.MULTILINE):
            parts = re.split(r'\n\s*[•\-\*]\s+', ac_text)
            for part in parts:
                part = part.strip()
                if part:
                    items.append(part)
        
        # Pattern 3: Plain paragraphs (split by double newlines)
        else:
            parts = re.split(r'\n\s*\n', ac_text)
            for part in parts:
                part = part.strip()
                if part:
                    items.append(part)
        
        # Normalize items
        normalized = []
        for item in items:
            item = self._normalize_item(item)
            if item:
                normalized.append(item)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in normalized:
            # Use normalized lowercase for duplicate detection
            item_key = item.lower().strip()
            if item_key and item_key not in seen:
                seen.add(item_key)
                unique_items.append(item)
        
        return unique_items
    
    def _normalize_item(self, item: str) -> str:
        """
        Normalize a single AC item.
        
        - Remove excessive whitespace
        - Remove leading/trailing punctuation artifacts
        - Ensure proper sentence structure
        
        Args:
            item: Raw AC item text
            
        Returns:
            Normalized AC item
        """
        # Remove excessive whitespace
        item = re.sub(r'\s+', ' ', item)
        item = item.strip()
        
        # Remove leading punctuation artifacts
        item = re.sub(r'^[•\-\*]\s*', '', item)
        
        # Ensure it ends with proper punctuation
        if item and not item[-1] in '.!?':
            item += '.'
        
        return item
    
    def extract(self, description_html: Optional[str] = None, 
                ac_field_html: Optional[str] = None) -> List[str]:
        """
        Extract AC from either dedicated field or description.
        
        Priority: AC field > Description section
        
        Args:
            description_html: HTML from Description field
            ac_field_html: HTML from Acceptance Criteria field
            
        Returns:
            List of normalized AC items
        """
        # Try dedicated field first
        if ac_field_html:
            items = self.extract_from_field(ac_field_html)
            if items:
                return items
        
        # Fall back to description
        if description_html:
            return self.extract_from_description(description_html)
        
        return []

