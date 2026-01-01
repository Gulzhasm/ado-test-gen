"""
XML test steps generator for Azure DevOps Test Case format.

This module generates the Microsoft.VSTS.TCM.Steps XML format required
by ADO Test Case work items. The format is strict and must match ADO's
expected structure exactly.

Research Note: This module is rule-based but could be enhanced with
ML-based step generation for more natural language test steps.
"""
from xml.etree.ElementTree import Element, tostring
from typing import List
from src.models.test_case import TestStep


class StepsXMLGenerator:
    """
    Generates XML-formatted test steps for ADO Test Case work items.
    
    Format:
    <steps id="0" last="N">
      <step id="1" type="ActionStep">
        <parameterizedString isformatted="true">Action text</parameterizedString>
        <parameterizedString isformatted="true">Expected result text</parameterizedString>
      </step>
      ...
    </steps>
    """
    
    @staticmethod
    def generate(steps: List[TestStep]) -> str:
        """
        Generate XML string for test steps.
        
        Args:
            steps: List of TestStep objects
            
        Returns:
            XML string in ADO format
            
        Example:
            >>> steps = [
            ...     TestStep(action="Click Login", expected_result="Login dialog appears", step_number=1),
            ...     TestStep(action="Enter credentials", expected_result="Credentials entered", step_number=2)
            ... ]
            >>> xml = StepsXMLGenerator.generate(steps)
        """
        if not steps:
            raise ValueError("At least one test step is required")
        
        # Create root element
        steps_elem = Element("steps")
        steps_elem.set("id", "0")
        steps_elem.set("last", str(len(steps)))
        
        # Add each step
        for step in steps:
            step_elem = Element("step")
            step_elem.set("id", str(step.step_number))
            step_elem.set("type", "ActionStep")
            
            # Action parameterizedString
            action_elem = Element("parameterizedString")
            action_elem.set("isformatted", "true")
            action_elem.text = step.action
            
            # Expected result parameterizedString
            expected_elem = Element("parameterizedString")
            expected_elem.set("isformatted", "true")
            expected_elem.text = step.expected_result
            
            step_elem.append(action_elem)
            step_elem.append(expected_elem)
            steps_elem.append(step_elem)
        
        # Convert to string
        xml_bytes = tostring(steps_elem, encoding="unicode")
        return xml_bytes
    
    @staticmethod
    def add_close_application_step(steps: List[TestStep]) -> List[TestStep]:
        """
        Add mandatory close application step to the end of steps list.
        
        This is a required final step for all test cases:
        - Action: "Close/Exit the application."
        - Expected: "Application closes successfully without crash or freeze; no error dialogs are shown."
        
        Args:
            steps: Existing test steps
            
        Returns:
            New list with close step appended
        """
        close_step = TestStep(
            action="Close/Exit the application.",
            expected_result="Application closes successfully without crash or freeze; no error dialogs are shown during exit.",
            step_number=len(steps) + 1
        )
        
        # Re-number all steps to ensure sequential numbering
        renumbered_steps = []
        for i, step in enumerate(steps, start=1):
            renumbered_steps.append(
                TestStep(
                    action=step.action,
                    expected_result=step.expected_result,
                    step_number=i
                )
            )
        
        renumbered_steps.append(close_step)
        return renumbered_steps

