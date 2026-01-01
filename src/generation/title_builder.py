"""
Test case title builder with strict validation.

This module builds test case titles following strict rules:
- Format: {InternalId}: {Feature} / {Module} / {Category} / {Subcategory} / {Short Descriptor}
- Short Descriptor: <= 8 words, noun-phrase-like, no verbs, no punctuation

Research Note: Title building is rule-based but can be enhanced with
NLP-based noun phrase extraction and summarization.
"""
import re
from typing import List


class TitleBuilder:
    """
    Builds and validates test case titles according to strict rules.
    """
    
    # Forbidden words in short descriptor (verbs and action words)
    FORBIDDEN_WORDS = {
        'verify', 'check', 'test', 'validate', 'ensure', 'confirm',
        'click', 'select', 'choose', 'press', 'type', 'enter', 'input',
        'when', 'then', 'if', 'should', 'must', 'will', 'can', 'may',
        'do', 'does', 'did', 'done', 'make', 'makes', 'made'
    }
    
    # Forbidden punctuation
    FORBIDDEN_PUNCTUATION = {'.', ':', ';', '…', '!', '?', ','}
    
    MAX_WORDS = 8
    
    @staticmethod
    def build(
        internal_id: str,
        feature: str,
        module: str,
        category: str,
        subcategory: str,
        short_descriptor: str
    ) -> str:
        """
        Build test case title with validation.
        
        Format: {InternalId}: {Feature} / {Module} / {Category} / {Subcategory} / {Short Descriptor}
        
        Args:
            internal_id: Internal test case ID (e.g., "270542-AC1")
            feature: Feature name
            module: Module name
            category: Category name
            subcategory: Subcategory name
            short_descriptor: Short descriptor (must be <= 8 words, noun-phrase-like)
            
        Returns:
            Formatted title string
            
        Raises:
            ValueError: If short_descriptor violates rules
        """
        # Validate short descriptor
        TitleBuilder._validate_short_descriptor(short_descriptor)
        
        # Clean all components
        components = [feature, module, category, subcategory, short_descriptor]
        cleaned = [TitleBuilder._clean_component(comp) for comp in components]
        
        # Build title
        title = f"{internal_id}: {' / '.join(cleaned)}"
        
        # Truncate if too long (ADO limit is 256 chars)
        MAX_TITLE_LENGTH = 250
        if len(title) > MAX_TITLE_LENGTH:
            # Keep internal_id and separators, truncate short_descriptor
            prefix = f"{internal_id}: {' / '.join(cleaned[:4])} / "
            max_desc_length = MAX_TITLE_LENGTH - len(prefix)
            if max_desc_length > 0:
                # Truncate short_descriptor by words
                words = short_descriptor.split()
                truncated_words = []
                current_length = 0
                for word in words:
                    if current_length + len(word) + 1 <= max_desc_length - 3:
                        truncated_words.append(word)
                        current_length += len(word) + 1
                    else:
                        break
                if truncated_words:
                    truncated_desc = ' '.join(truncated_words) + "..."
                else:
                    truncated_desc = "Test Case"
                title = prefix + truncated_desc
            else:
                title = f"{internal_id}: Test Case"
        
        return title
    
    @staticmethod
    def _validate_short_descriptor(descriptor: str) -> None:
        """
        Validate short descriptor against rules.
        
        Rules:
        - <= 8 words
        - No forbidden words (verbs, action words)
        - No forbidden punctuation
        
        Args:
            descriptor: Short descriptor to validate
            
        Raises:
            ValueError: If validation fails
        """
        if not descriptor or not descriptor.strip():
            raise ValueError("Short descriptor cannot be empty")
        
        words = descriptor.split()
        
        # Check word count
        if len(words) > TitleBuilder.MAX_WORDS:
            raise ValueError(
                f"Short descriptor must be <= {TitleBuilder.MAX_WORDS} words, "
                f"got {len(words)}: '{descriptor}'"
            )
        
        # Check for forbidden words
        descriptor_lower = descriptor.lower()
        for forbidden in TitleBuilder.FORBIDDEN_WORDS:
            if forbidden in descriptor_lower:
                # Check if it's a whole word (not part of another word)
                pattern = r'\b' + re.escape(forbidden) + r'\b'
                if re.search(pattern, descriptor_lower):
                    raise ValueError(
                        f"Short descriptor contains forbidden word '{forbidden}': '{descriptor}'"
                    )
        
        # Check for forbidden punctuation
        for punct in TitleBuilder.FORBIDDEN_PUNCTUATION:
            if punct in descriptor:
                raise ValueError(
                    f"Short descriptor contains forbidden punctuation '{punct}': '{descriptor}'"
                )
    
    @staticmethod
    def _clean_component(component: str) -> str:
        """
        Clean a title component.
        
        Removes:
        - Forward slashes (to avoid confusion with separators)
        - Excessive whitespace
        
        Args:
            component: Component to clean
            
        Returns:
            Cleaned component
        """
        if not component:
            return ""
        # Replace / with - to avoid confusion
        cleaned = component.strip().replace("/", "-").replace("\\", "-")
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

