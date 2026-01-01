"""
Template engine for applying test case templates to Acceptance Criteria.

This module loads templates from YAML and applies them to AC items based on
category and subcategory classification.

Research Note: This module is rule-based but can be enhanced with ML-based
template selection and customization.
"""
import yaml
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.models.test_case import TestStep
from src.parsing.ac_classifier import ACCategory


class TemplateEngine:
    """
    Engine for loading and applying test case templates.
    
    Loads templates from YAML file and matches them to AC items based on
    category and subcategory classification.
    """
    
    def __init__(self, templates_path: Optional[str] = None):
        """
        Initialize template engine.
        
        Args:
            templates_path: Optional path to templates YAML file.
                           Defaults to src/generation/templates.yaml
        """
        if templates_path is None:
            # Get the directory of this file
            current_dir = Path(__file__).parent
            templates_path = current_dir / "templates.yaml"
        
        self.templates_path = templates_path
        self.templates: List[Dict[str, Any]] = []
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load templates from YAML file."""
        if not os.path.exists(self.templates_path):
            raise FileNotFoundError(
                f"Templates file not found: {self.templates_path}"
            )
        
        with open(self.templates_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.templates = data.get('templates', [])
    
    def get_template(
        self,
        category: ACCategory,
        subcategory: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get template for a category and subcategory.
        
        Args:
            category: ACCategory enum value
            subcategory: Subcategory string
            
        Returns:
            Template dictionary with steps, short_descriptor, and requires, or None if not found
        """
        # Try exact match first
        for template in self.templates:
            if (template.get('category') == category.value and
                template.get('subcategory') == subcategory):
                return template
        
        # Fallback to category match with any subcategory
        for template in self.templates:
            if template.get('category') == category.value:
                return template
        
        # Fallback to Other/General
        for template in self.templates:
            if template.get('category') == ACCategory.OTHER_GENERAL.value:
                return template
        
        return None
    
    def get_short_descriptor(
        self,
        category: ACCategory,
        subcategory: str
    ) -> str:
        """
        Get short descriptor from template.
        
        Args:
            category: ACCategory enum value
            subcategory: Subcategory string
            
        Returns:
            Short descriptor string, or fallback if not found
        """
        template = self.get_template(category, subcategory)
        if template and template.get('short_descriptor'):
            return template.get('short_descriptor')
        # Fallback
        return "General functionality"
    
    def apply_template(
        self,
        template: Dict[str, Any],
        ac_text: str
    ) -> List[TestStep]:
        """
        Apply a template to generate test steps.
        
        Customizes template steps by replacing placeholders with AC-specific
        content where applicable.
        
        Args:
            template: Template dictionary
            ac_text: Acceptance criterion text for customization
            
        Returns:
            List of TestStep objects
        """
        steps = []
        step_num = 1
        
        template_steps = template.get('steps', [])
        for step_def in template_steps:
            action = step_def.get('action', '')
            expected = step_def.get('expected', '')
            
            # Customize steps with AC text where it makes sense
            # Replace generic placeholders with AC-specific content
            if '{ac}' in action.lower() or 'acceptance criterion' in action.lower():
                # Don't replace, keep as is - templates are already generic
                pass
            
            steps.append(TestStep(
                action=action,
                expected_result=expected,
                step_number=step_num
            ))
            step_num += 1
        
        return steps
    
    def generate_steps(
        self,
        category: ACCategory,
        subcategory: str,
        ac_text: str
    ) -> List[TestStep]:
        """
        Generate test steps for an AC using appropriate template.
        
        Args:
            category: Classified category
            subcategory: Classified subcategory
            ac_text: Acceptance criterion text
            
        Returns:
            List of TestStep objects
        """
        template = self.get_template(category, subcategory)
        if not template:
            # Fallback to minimal steps
            return [
                TestStep(
                    action="Launch the application.",
                    expected_result="Application launches successfully and main window is displayed.",
                    step_number=1
                ),
                TestStep(
                    action=f"Perform the action described in the acceptance criterion: {ac_text}",
                    expected_result=f"Action completes successfully and {ac_text.lower().rstrip('.')}",
                    step_number=2
                )
            ]
        
        return self.apply_template(template, ac_text)

