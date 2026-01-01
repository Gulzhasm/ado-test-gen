"""
Acceptance Criteria classification using keyword-based heuristics.

This module classifies AC items into categories using deterministic
keyword matching and scoring. No LLM or ML is used - purely rule-based.

Research Note: This module is designed to be replaced with ML-based
classification for better accuracy and handling of edge cases.
"""
import re
from typing import Dict, List, Tuple
from enum import Enum


class ACCategory(str, Enum):
    """Categories for Acceptance Criteria classification."""
    AVAILABILITY_ENTRY_POINTS = "Availability/Entry Points"
    LOGGING_TRACKING = "Logging/Tracking"
    ORDERING = "Ordering"
    LIMIT_RETENTION = "Limit/Retention"
    RESTRICTIONS_SCOPE = "Restrictions/Scope"
    DYNAMIC_REFRESH = "Dynamic Refresh"
    RESET_CONDITIONS = "Reset Conditions"
    SCROLLING = "Scrolling"
    ACCESSIBILITY = "Accessibility"
    OTHER_GENERAL = "Other/General"


class AcceptanceCriteriaClassifier:
    """
    Classifies Acceptance Criteria into categories using keyword heuristics.
    
    Uses simple keyword matching with scoring to determine the best category
    for each AC item. Multiple keywords can match, and the highest score wins.
    """
    
    # Keyword patterns for each category with weights
    KEYWORD_PATTERNS: Dict[ACCategory, List[Tuple[str, float]]] = {
        ACCategory.AVAILABILITY_ENTRY_POINTS: [
            ("visible", 2.0),
            ("available", 2.0),
            ("displayed", 2.0),
            ("shown", 2.0),
            ("appears", 1.5),
            ("menu", 1.5),
            ("sidebar", 1.5),
            ("panel", 1.5),
            ("button", 1.0),
            ("link", 1.0),
            ("access", 1.0),
            ("entry point", 2.0),
        ],
        ACCategory.LOGGING_TRACKING: [
            ("log", 2.0),
            ("record", 2.0),
            ("history", 2.0),
            ("list", 1.5),
            ("track", 2.0),
            ("audit", 1.5),
            ("entry", 1.5),
            ("item", 1.0),
            ("updates", 1.5),
            ("adds", 1.0),
            ("appends", 1.0),
        ],
        ACCategory.ORDERING: [
            ("newest", 2.0),
            ("oldest", 2.0),
            ("top", 1.5),
            ("bottom", 1.5),
            ("first", 1.5),
            ("last", 1.5),
            ("chronological", 2.0),
            ("order", 1.5),
            ("sorted", 1.5),
            ("sequence", 1.0),
            ("ascending", 1.5),
            ("descending", 1.5),
        ],
        ACCategory.LIMIT_RETENTION: [
            ("limit", 2.0),
            ("only", 1.5),
            ("last five", 2.0),
            ("last 5", 2.0),
            ("max", 2.0),
            ("maximum", 2.0),
            ("removed", 1.5),
            ("deleted", 1.5),
            ("retention", 2.0),
            ("keep", 1.5),
            ("maintain", 1.0),
            ("preserve", 1.0),
        ],
        ACCategory.RESTRICTIONS_SCOPE: [
            ("no manual", 2.0),
            ("cannot", 2.0),
            ("out of scope", 2.0),
            ("not allowed", 2.0),
            ("restricted", 1.5),
            ("prohibited", 1.5),
            ("disabled", 1.5),
            ("read-only", 1.5),
            ("not editable", 1.5),
            ("not modifiable", 1.5),
        ],
        ACCategory.DYNAMIC_REFRESH: [
            ("updates automatically", 2.0),
            ("real time", 2.0),
            ("real-time", 2.0),
            ("refreshes", 2.0),
            ("auto-update", 2.0),
            ("live", 1.5),
            ("dynamic", 1.5),
            ("immediately", 1.0),
            ("instant", 1.0),
            ("without refresh", 1.5),
        ],
        ACCategory.RESET_CONDITIONS: [
            ("resets", 2.0),
            ("reset", 2.0),
            ("new drawing", 2.0),
            ("new file", 1.5),
            ("loaded", 1.5),
            ("clear", 1.5),
            ("cleared", 1.5),
            ("empty", 1.0),
            ("initial state", 1.5),
        ],
        ACCategory.SCROLLING: [
            ("scroll", 2.0),
            ("scrollable", 2.0),
            ("exceeds visible height", 2.0),
            ("exceeds visible area", 1.5),
            ("overflow", 1.5),
            ("vertical scroll", 2.0),
            ("horizontal scroll", 1.5),
            ("scrollbar", 1.5),
        ],
        ACCategory.ACCESSIBILITY: [
            ("508", 2.0),
            ("wcag", 2.0),
            ("keyboard", 2.0),
            ("focus", 2.0),
            ("accessible", 2.0),
            ("readable labels", 2.0),
            ("aria", 1.5),
            ("screen reader", 1.5),
            ("tab navigation", 1.5),
            ("keyboard navigation", 2.0),
        ],
    }
    
    def __init__(self):
        """Initialize the classifier."""
        pass
    
    def classify(self, ac_text: str) -> ACCategory:
        """
        Classify an AC item into a category.
        
        Uses keyword matching with scoring. The category with the highest
        total score wins. If no keywords match, returns OTHER_GENERAL.
        
        Args:
            ac_text: Acceptance criterion text
            
        Returns:
            ACCategory enum value
            
        Example:
            >>> classifier = AcceptanceCriteriaClassifier()
            >>> classifier.classify("The panel should be visible in the sidebar")
            <ACCategory.AVAILABILITY_ENTRY_POINTS: 'Availability/Entry Points'>
        """
        ac_lower = ac_text.lower()
        scores: Dict[ACCategory, float] = {}
        
        # Score each category
        for category, patterns in self.KEYWORD_PATTERNS.items():
            score = 0.0
            for keyword, weight in patterns:
                # Count occurrences (case-insensitive)
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', ac_lower))
                score += count * weight
            scores[category] = score
        
        # Find category with highest score
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                # Return category with highest score
                for category, score in scores.items():
                    if score == max_score:
                        return category
        
        # Default to Other/General if no matches
        return ACCategory.OTHER_GENERAL
    
    def get_subcategory(self, ac_text: str, category: ACCategory) -> str:
        """
        Get subcategory for a classified AC.
        
        Provides more specific subcategory based on category and AC content.
        
        Args:
            ac_text: Acceptance criterion text
            category: Classified category
            
        Returns:
            Subcategory string
        """
        ac_lower = ac_text.lower()
        
        subcategory_map = {
            ACCategory.AVAILABILITY_ENTRY_POINTS: {
                "menu": "Menu Entry",
                "sidebar": "Sidebar Entry",
                "panel": "Panel Display",
                "button": "Button Display",
                "default": "Visibility"
            },
            ACCategory.LOGGING_TRACKING: {
                "history": "History Logging",
                "audit": "Audit Trail",
                "list": "List Update",
                "default": "Data Logging"
            },
            ACCategory.ORDERING: {
                "newest": "Newest First",
                "oldest": "Oldest First",
                "chronological": "Chronological",
                "default": "Sort Order"
            },
            ACCategory.LIMIT_RETENTION: {
                "last five": "Last Five Retention",
                "last 5": "Last Five Retention",
                "max": "Maximum Limit",
                "default": "Data Retention"
            },
            ACCategory.RESTRICTIONS_SCOPE: {
                "read-only": "Read-Only Restriction",
                "disabled": "Disabled State",
                "default": "Access Restriction"
            },
            ACCategory.DYNAMIC_REFRESH: {
                "real time": "Real-Time Update",
                "real-time": "Real-Time Update",
                "default": "Auto Refresh"
            },
            ACCategory.RESET_CONDITIONS: {
                "new drawing": "New Drawing Reset",
                "loaded": "Load Reset",
                "default": "State Reset"
            },
            ACCategory.SCROLLING: {
                "vertical": "Vertical Scrolling",
                "horizontal": "Horizontal Scrolling",
                "default": "Scroll Behavior"
            },
            ACCategory.ACCESSIBILITY: {
                "keyboard": "Keyboard Navigation",
                "focus": "Focus Management",
                "wcag": "WCAG Compliance",
                "default": "Accessibility"
            },
        }
        
        subcategories = subcategory_map.get(category, {"default": "General"})
        
        # Check for specific subcategory keywords
        for key, subcat in subcategories.items():
            if key != "default" and key in ac_lower:
                return subcat
        
        return subcategories.get("default", "General")

