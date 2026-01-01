"""
HTML parsing utilities for extracting clean text from Azure DevOps work items.

Azure DevOps stores rich text content (Description, Acceptance Criteria) as HTML.
This module provides utilities to convert HTML to clean, structured text while
preserving semantic structure (lists, paragraphs, etc.).

Research Note: This module can be extended with ML-based content understanding
for better extraction of structured information from unstructured HTML.
"""
import re
from html.parser import HTMLParser
from typing import List


class ADOHTMLParser(HTMLParser):
    """
    Custom HTML parser for Azure DevOps HTML content.
    
    Extracts clean text while preserving list structure and formatting.
    Handles common ADO HTML patterns like lists, paragraphs, and formatting tags.
    """
    
    def __init__(self):
        super().__init__()
        self.text_parts: List[str] = []
        self.current_tag = None
        self.in_list = False
        self.list_items: List[str] = []
        self.current_list_item = ""
    
    def handle_starttag(self, tag: str, attrs: List[tuple]):
        """Handle opening HTML tags."""
        self.current_tag = tag.lower()
        
        if tag.lower() in ["ul", "ol"]:
            self.in_list = True
        elif tag.lower() == "li":
            self.current_list_item = ""
        elif tag.lower() == "br":
            self.text_parts.append("\n")
    
    def handle_endtag(self, tag: str):
        """Handle closing HTML tags."""
        tag_lower = tag.lower()
        
        if tag_lower == "li":
            if self.current_list_item.strip():
                self.list_items.append(self.current_list_item.strip())
            self.current_list_item = ""
        elif tag_lower in ["ul", "ol"]:
            if self.list_items:
                # Add list items with bullet points
                for item in self.list_items:
                    self.text_parts.append(f"• {item}")
                self.text_parts.append("")
                self.list_items = []
            self.in_list = False
        elif tag_lower in ["p", "div"]:
            self.text_parts.append("")
        
        self.current_tag = None
    
    def handle_data(self, data: str):
        """Handle text content within HTML tags."""
        text = data.strip()
        if not text:
            return
        
        if self.current_tag == "li":
            self.current_list_item += " " + text
        else:
            self.text_parts.append(text)
    
    def get_text(self) -> str:
        """
        Get the parsed clean text.
        
        Returns:
            Clean text with preserved structure
        """
        return "\n".join(self.text_parts).strip()


def html_to_text(html_content: str) -> str:
    """
    Convert Azure DevOps HTML content to clean text.
    
    Handles common ADO HTML patterns:
    - Lists (ul, ol)
    - Paragraphs (p, div)
    - Line breaks (br)
    - Basic formatting (strong, em, etc.)
    
    Args:
        html_content: HTML string from ADO work item
        
    Returns:
        Clean text with preserved structure
        
    Example:
        >>> html = "<p>Hello</p><ul><li>Item 1</li><li>Item 2</li></ul>"
        >>> html_to_text(html)
        'Hello\\n\\n• Item 1\\n• Item 2'
    """
    if not html_content:
        return ""
    
    # Remove common ADO-specific HTML artifacts
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Replace common formatting tags with plain text equivalents
    html_content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'\1', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'<b[^>]*>(.*?)</b>', r'\1', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'<em[^>]*>(.*?)</em>', r'\1', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'<i[^>]*>(.*?)</i>', r'\1', html_content, flags=re.IGNORECASE)
    
    # Parse HTML
    parser = ADOHTMLParser()
    parser.feed(html_content)
    text = parser.get_text()
    
    # Clean up excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()

