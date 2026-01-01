"""
Unit tests for StepsXMLGenerator.

Tests ensure:
- XML is valid and contains required fields
- Final exit step is present
- Steps have both action and expected result
"""
import pytest
from xml.etree.ElementTree import fromstring
from src.xml.steps_xml import StepsXMLGenerator
from src.models.test_case import TestStep


class TestStepsXMLGenerator:
    """Test cases for XML step generation."""
    
    def test_generate_valid_xml(self):
        """Test that generated XML is valid."""
        steps = [
            TestStep(
                action="Launch the application.",
                expected_result="Application launches successfully.",
                step_number=1
            ),
            TestStep(
                action="Navigate to feature.",
                expected_result="Feature is displayed.",
                step_number=2
            )
        ]
        xml = StepsXMLGenerator.generate(steps)
        
        # Parse XML to ensure it's valid
        root = fromstring(xml)
        assert root.tag == "steps"
        assert root.get("id") == "0"
        assert root.get("last") == "2"
    
    def test_xml_contains_all_steps(self):
        """Test that all steps are included in XML."""
        steps = [
            TestStep(action="Action 1", expected_result="Expected 1", step_number=1),
            TestStep(action="Action 2", expected_result="Expected 2", step_number=2),
            TestStep(action="Action 3", expected_result="Expected 3", step_number=3)
        ]
        xml = StepsXMLGenerator.generate(steps)
        root = fromstring(xml)
        
        step_elements = root.findall("step")
        assert len(step_elements) == 3
    
    def test_xml_step_has_action_and_expected(self):
        """Test that each step has both action and expected result."""
        steps = [
            TestStep(
                action="Test action",
                expected_result="Test expected",
                step_number=1
            )
        ]
        xml = StepsXMLGenerator.generate(steps)
        root = fromstring(xml)
        
        step = root.find("step")
        param_strings = step.findall("parameterizedString")
        assert len(param_strings) == 2
        assert param_strings[0].text == "Test action"
        assert param_strings[1].text == "Test expected"
    
    def test_empty_steps_raises_error(self):
        """Test that empty steps list raises ValueError."""
        with pytest.raises(ValueError, match="At least one test step is required"):
            StepsXMLGenerator.generate([])
    
    def test_add_close_application_step(self):
        """Test that close step is added correctly."""
        steps = [
            TestStep(
                action="Launch the application.",
                expected_result="Application launches.",
                step_number=1
            )
        ]
        updated_steps = StepsXMLGenerator.add_close_application_step(steps)
        
        assert len(updated_steps) == 2
        assert updated_steps[0].step_number == 1
        assert updated_steps[1].step_number == 2
        assert updated_steps[1].action == "Close/Exit the QuickDraw application."
        assert "Application closes successfully" in updated_steps[1].expected_result
        assert "no error dialogs" in updated_steps[1].expected_result
    
    def test_close_step_renumbers_existing(self):
        """Test that adding close step renumbers existing steps."""
        steps = [
            TestStep(action="Action 1", expected_result="Expected 1", step_number=5),
            TestStep(action="Action 2", expected_result="Expected 2", step_number=10)
        ]
        updated_steps = StepsXMLGenerator.add_close_application_step(steps)
        
        assert updated_steps[0].step_number == 1
        assert updated_steps[1].step_number == 2
        assert updated_steps[2].step_number == 3
        assert updated_steps[2].action == "Close/Exit the QuickDraw application."
    
    def test_xml_step_attributes(self):
        """Test that step elements have correct attributes."""
        steps = [
            TestStep(action="Action", expected_result="Expected", step_number=1)
        ]
        xml = StepsXMLGenerator.generate(steps)
        root = fromstring(xml)
        
        step = root.find("step")
        assert step.get("id") == "1"
        assert step.get("type") == "ActionStep"
        
        param_strings = step.findall("parameterizedString")
        for param in param_strings:
            assert param.get("isformatted") == "true"

