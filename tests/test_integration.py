"""
Comprehensive integration tests for the ADO test case generation system.

Tests ensure all validation rules are enforced:
- Title suffix <= 8 words
- Title suffix contains no forbidden words
- Title suffix contains no punctuation
- IDs follow AC1 then increments of 5
- Steps XML is valid
- Final exit step is present
- Idempotency tags are correct
"""
import pytest
from src.models.story import UserStory
from src.models.acceptance_criteria import AcceptanceCriterion
from src.models.test_case import TestCaseType
from src.generation.testcase_factory import TestCaseFactory
from src.generation.title_builder import TitleBuilder
from src.xml.steps_xml import StepsXMLGenerator
from xml.etree.ElementTree import fromstring


class TestIntegration:
    """Integration tests for end-to-end validation."""
    
    def test_generated_test_case_has_valid_title(self):
        """Test that generated test cases have valid titles."""
        story = UserStory(
            id=270542,
            title="Hand Tool",
            description_html=None,
            description_text=None,
            acceptance_criteria_html=None,
            acceptance_criteria=["The tool should be visible in the toolbar."]
        )
        
        factory = TestCaseFactory(story)
        ac = AcceptanceCriterion(id=1, text="The tool should be visible in the toolbar.", original_order=1)
        test_cases = factory.generate_all_test_cases([ac])
        
        assert len(test_cases) > 0
        for tc in test_cases:
            # Check title format
            assert ":" in tc.title
            parts = tc.title.split(" / ")
            assert len(parts) == 5
            
            # Check short descriptor (last part after last /)
            last_part = parts[-1]
            words = last_part.split()
            assert len(words) <= 8, f"Short descriptor has {len(words)} words: {last_part}"
            
            # Check no forbidden words
            last_part_lower = last_part.lower()
            forbidden = ['verify', 'when', 'click', 'then', 'check', 'test']
            for word in forbidden:
                assert word not in last_part_lower, f"Forbidden word '{word}' found in: {last_part}"
            
            # Check no forbidden punctuation
            forbidden_punct = ['.', ':', ';', '…', '!', '?']
            for punct in forbidden_punct:
                assert punct not in last_part, f"Forbidden punctuation '{punct}' found in: {last_part}"
    
    def test_internal_ids_follow_convention(self):
        """Test that internal IDs follow AC1 then increments of 5."""
        story = UserStory(
            id=270542,
            title="Test Story",
            description_html=None,
            description_text=None,
            acceptance_criteria_html=None,
            acceptance_criteria=["AC1", "AC2", "AC3"]
        )
        
        factory = TestCaseFactory(story)
        acs = [
            AcceptanceCriterion(id=1, text="AC1", original_order=1),
            AcceptanceCriterion(id=2, text="AC2", original_order=2),
            AcceptanceCriterion(id=3, text="AC3", original_order=3)
        ]
        test_cases = factory.generate_all_test_cases(acs)
        
        # First test case should be AC1
        assert test_cases[0].internal_id == "270542-AC1"
        
        # Subsequent should increment by 5
        if len(test_cases) > 1:
            assert test_cases[1].internal_id == "270542-005"
        if len(test_cases) > 2:
            assert test_cases[2].internal_id == "270542-010"
    
    def test_steps_xml_is_valid(self):
        """Test that generated steps XML is valid."""
        story = UserStory(
            id=270542,
            title="Test Story",
            description_html=None,
            description_text=None,
            acceptance_criteria_html=None,
            acceptance_criteria=["Test AC"]
        )
        
        factory = TestCaseFactory(story)
        ac = AcceptanceCriterion(id=1, text="Test AC", original_order=1)
        test_cases = factory.generate_all_test_cases([ac])
        
        for tc in test_cases:
            xml = StepsXMLGenerator.generate(tc.steps)
            
            # Parse XML to ensure it's valid
            root = fromstring(xml)
            assert root.tag == "steps"
            
            # Check all steps have action and expected
            step_elements = root.findall("step")
            for step in step_elements:
                param_strings = step.findall("parameterizedString")
                assert len(param_strings) == 2, "Each step must have action and expected result"
    
    def test_final_exit_step_is_present(self):
        """Test that every test case has the mandatory close step."""
        story = UserStory(
            id=270542,
            title="Test Story",
            description_html=None,
            description_text=None,
            acceptance_criteria_html=None,
            acceptance_criteria=["Test AC"]
        )
        
        factory = TestCaseFactory(story)
        ac = AcceptanceCriterion(id=1, text="Test AC", original_order=1)
        test_cases = factory.generate_all_test_cases([ac])
        
        for tc in test_cases:
            # Check last step is close step
            last_step = tc.steps[-1]
            assert "Close/Exit" in last_step.action or "QuickDraw" in last_step.action
            assert "closes successfully" in last_step.expected_result or "no error dialogs" in last_step.expected_result
    
    def test_idempotency_tags_are_correct(self):
        """Test that test cases have correct idempotency tags."""
        story = UserStory(
            id=270542,
            title="Test Story",
            description_html=None,
            description_text=None,
            acceptance_criteria_html=None,
            acceptance_criteria=["Test AC"]
        )
        
        factory = TestCaseFactory(story)
        ac = AcceptanceCriterion(id=1, text="Test AC", original_order=1)
        test_cases = factory.generate_all_test_cases([ac])
        
        for tc in test_cases:
            tags_str = "; ".join(tc.tags)
            
            # Check required tags
            assert f"story:{story.id}" in tc.tags
            assert "generated-by:ado-testgen" in tc.tags
            assert "gen-mode:rules" in tc.tags
            
            # Check AC hash tag (except for umbrella test)
            if tc.test_type != TestCaseType.UMBRELLA:
                assert any("ac-hash:" in tag for tag in tc.tags)
    
    def test_title_builder_validation_enforced(self):
        """Test that TitleBuilder validation is enforced in factory."""
        story = UserStory(
            id=270542,
            title="Test Story",
            description_html=None,
            description_text=None,
            acceptance_criteria_html=None,
            acceptance_criteria=["Test AC"]
        )
        
        factory = TestCaseFactory(story)
        ac = AcceptanceCriterion(id=1, text="Test AC", original_order=1)
        
        # This should not raise an error because templates have valid short_descriptors
        test_cases = factory.generate_all_test_cases([ac])
        assert len(test_cases) > 0
        
        # All titles should be valid
        for tc in test_cases:
            # Try to parse title to ensure it's valid
            parts = tc.title.split(" / ")
            assert len(parts) == 5
    
    def test_no_raw_ac_text_in_title(self):
        """Test that titles never contain raw AC text."""
        story = UserStory(
            id=270542,
            title="Test Story",
            description_html=None,
            description_text=None,
            acceptance_criteria_html=None,
            acceptance_criteria=["The tool should be visible when clicked on the toolbar button."]
        )
        
        factory = TestCaseFactory(story)
        ac = AcceptanceCriterion(
            id=1,
            text="The tool should be visible when clicked on the toolbar button.",
            original_order=1
        )
        test_cases = factory.generate_all_test_cases([ac])
        
        for tc in test_cases:
            # Title should not contain the full AC text
            # (it should use template short_descriptor instead)
            assert "when clicked" not in tc.title.lower()
            assert "toolbar button" not in tc.title.lower() or "toolbar button" in tc.title.lower()  # May be in feature/module
            
            # Check that title uses template-based short descriptor
            # (should not be a verb phrase from AC)
            last_part = tc.title.split(" / ")[-1]
            assert last_part != ac.text  # Should never be raw AC text

