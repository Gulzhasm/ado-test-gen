"""
Test case builder for generating comprehensive test scenarios.

This module implements the test case generation logic, creating multiple
test scenarios for each acceptance criterion:
- Happy path
- Negative scenarios
- Boundary cases
- Cancel/rollback behavior
- Persistence (save/reopen)
- Undo/Redo (if applicable)
- Accessibility (keyboard navigation, focus visibility)

Research Note: This module is rule-based but designed to be enhanced with
ML-based scenario generation for more sophisticated test case creation.
"""
from typing import List
from src.models.acceptance_criteria import AcceptanceCriterion
from src.models.test_case import TestCase, TestStep, TestCaseType
from src.models.story import UserStory
from src.generation.naming import TestCaseNaming
from src.xml.steps_xml import StepsXMLGenerator


class TestCaseBuilder:
    """
    Builds test cases from acceptance criteria following comprehensive
    coverage requirements.
    """
    
    def __init__(self, story: UserStory):
        """
        Initialize builder with User Story context.
        
        Args:
            story: User Story model instance
        """
        self.story = story
    
    def build_all_test_cases(self, acceptance_criteria: List[AcceptanceCriterion]) -> List[TestCase]:
        """
        Build all test cases for given acceptance criteria.
        
        Generates multiple test scenarios per AC plus one umbrella test case.
        
        Args:
            acceptance_criteria: List of AcceptanceCriterion objects
            
        Returns:
            List of TestCase objects
        """
        test_cases = []
        test_case_index = 0
        
        # Generate test cases for each AC
        for ac in acceptance_criteria:
            ac_test_cases = self._build_test_cases_for_ac(ac, test_case_index)
            test_cases.extend(ac_test_cases)
            test_case_index += len(ac_test_cases)
        
        # Generate umbrella test case
        umbrella_test_case = self._build_umbrella_test_case(test_case_index)
        test_cases.append(umbrella_test_case)
        
        return test_cases
    
    def _build_test_cases_for_ac(self, ac: AcceptanceCriterion, start_index: int) -> List[TestCase]:
        """
        Build all test scenarios for a single acceptance criterion.
        
        Args:
            ac: AcceptanceCriterion object
            start_index: Starting index for internal ID generation
            
        Returns:
            List of TestCase objects for this AC
        """
        test_cases = []
        current_index = start_index
        
        # Determine which test types are applicable
        test_types = self._determine_applicable_test_types(ac)
        
        for test_type in test_types:
            test_case = self._build_single_test_case(ac, test_type, current_index)
            test_cases.append(test_case)
            current_index += 1
        
        return test_cases
    
    def _determine_applicable_test_types(self, ac: AcceptanceCriterion) -> List[TestCaseType]:
        """
        Determine which test types are applicable for an AC.
        
        Research Note: This logic can be enhanced with ML-based analysis
        of AC content to determine relevant test scenarios.
        
        Args:
            ac: AcceptanceCriterion object
            
        Returns:
            List of applicable TestCaseType values
        """
        ac_lower = ac.text.lower()
        test_types = [TestCaseType.HAPPY_PATH]  # Always include happy path
        
        # Negative scenarios - applicable to most ACs
        test_types.append(TestCaseType.NEGATIVE)
        
        # Boundary cases - if AC mentions limits, ranges, or quantities
        if any(word in ac_lower for word in ["limit", "maximum", "minimum", "range", "between", "at least", "at most"]):
            test_types.append(TestCaseType.BOUNDARY)
        
        # Cancel/Rollback - if AC involves actions that can be cancelled
        if any(word in ac_lower for word in ["cancel", "undo", "back", "close", "exit"]):
            test_types.append(TestCaseType.CANCEL_ROLLBACK)
        
        # Persistence - if AC involves saving or data storage
        if any(word in ac_lower for word in ["save", "store", "persist", "data", "file", "database"]):
            test_types.append(TestCaseType.PERSISTENCE)
        
        # Undo/Redo - if AC involves editing or modifications
        if any(word in ac_lower for word in ["edit", "modify", "change", "update", "undo", "redo"]):
            test_types.append(TestCaseType.UNDO_REDO)
        
        # Accessibility - always include for comprehensive coverage
        test_types.append(TestCaseType.ACCESSIBILITY)
        
        return test_types
    
    def _build_single_test_case(self, ac: AcceptanceCriterion, test_type: TestCaseType, index: int) -> TestCase:
        """
        Build a single test case for an AC and test type.
        
        Args:
            ac: AcceptanceCriterion object
            test_type: Type of test scenario
            index: Index for internal ID generation
            
        Returns:
            TestCase object
        """
        # Generate internal ID
        internal_id = TestCaseNaming.generate_internal_id(self.story.id, index)
        
        # Extract feature/module from AC
        feature, module = TestCaseNaming.extract_feature_module_from_ac(ac.text)
        
        # Get category/subcategory from test type
        category, subcategory = TestCaseNaming.get_category_subcategory(test_type)
        
        # Generate description
        description = self._generate_test_description(ac, test_type)
        
        # Generate title
        title = TestCaseNaming.generate_title(
            internal_id, feature, module, category, subcategory, description
        )
        
        # Generate test steps
        steps = self._generate_test_steps(ac, test_type)
        
        # Add mandatory close step
        steps = StepsXMLGenerator.add_close_application_step(steps)
        
        # Generate tags
        tags = [
            f"story:{self.story.id}",
            "generated-by:ai-testgen",
            f"ac:{ac.id}",
            f"test-type:{test_type.value}"
        ]
        
        return TestCase(
            internal_id=internal_id,
            title=title,
            steps=steps,
            test_type=test_type,
            acceptance_criterion_id=ac.id,
            story_id=self.story.id,
            tags=tags
        )
    
    def _generate_test_description(self, ac: AcceptanceCriterion, test_type: TestCaseType) -> str:
        """
        Generate test case description based on AC and test type.
        
        Args:
            ac: AcceptanceCriterion object
            test_type: Type of test scenario
            
        Returns:
            Description string
        """
        ac_text = ac.text
        
        if test_type == TestCaseType.HAPPY_PATH:
            return f"Verify {ac_text.lower().rstrip('.')}"
        elif test_type == TestCaseType.NEGATIVE:
            return f"Verify system handles invalid input when {ac_text.lower().rstrip('.')}"
        elif test_type == TestCaseType.BOUNDARY:
            return f"Verify boundary conditions for {ac_text.lower().rstrip('.')}"
        elif test_type == TestCaseType.CANCEL_ROLLBACK:
            return f"Verify cancel/rollback behavior for {ac_text.lower().rstrip('.')}"
        elif test_type == TestCaseType.PERSISTENCE:
            return f"Verify data persistence for {ac_text.lower().rstrip('.')}"
        elif test_type == TestCaseType.UNDO_REDO:
            return f"Verify undo/redo functionality for {ac_text.lower().rstrip('.')}"
        elif test_type == TestCaseType.ACCESSIBILITY:
            return f"Verify accessibility compliance for {ac_text.lower().rstrip('.')}"
        else:
            return f"Verify {ac_text.lower().rstrip('.')}"
    
    def _generate_test_steps(self, ac: AcceptanceCriterion, test_type: TestCaseType) -> List[TestStep]:
        """
        Generate test steps for a test case.
        
        Args:
            ac: AcceptanceCriterion object
            test_type: Type of test scenario
            
        Returns:
            List of TestStep objects (without close step)
        """
        steps = []
        step_num = 1
        
        if test_type == TestCaseType.HAPPY_PATH:
            steps = self._generate_happy_path_steps(ac, step_num)
        elif test_type == TestCaseType.NEGATIVE:
            steps = self._generate_negative_steps(ac, step_num)
        elif test_type == TestCaseType.BOUNDARY:
            steps = self._generate_boundary_steps(ac, step_num)
        elif test_type == TestCaseType.CANCEL_ROLLBACK:
            steps = self._generate_cancel_rollback_steps(ac, step_num)
        elif test_type == TestCaseType.PERSISTENCE:
            steps = self._generate_persistence_steps(ac, step_num)
        elif test_type == TestCaseType.UNDO_REDO:
            steps = self._generate_undo_redo_steps(ac, step_num)
        elif test_type == TestCaseType.ACCESSIBILITY:
            steps = self._generate_accessibility_steps(ac, step_num)
        
        return steps
    
    def _generate_happy_path_steps(self, ac: AcceptanceCriterion, start_num: int) -> List[TestStep]:
        """Generate happy path test steps."""
        steps = []
        step_num = start_num
        
        steps.append(TestStep(
            action=f"Launch the application.",
            expected_result="Application launches successfully and main window is displayed.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action=f"Navigate to the feature related to: {ac.text}",
            expected_result="Feature interface is displayed and accessible.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action=f"Perform the action described in the acceptance criterion: {ac.text}",
            expected_result=f"Action completes successfully and {ac.text.lower().rstrip('.')}",
            step_number=step_num
        ))
        
        return steps
    
    def _generate_negative_steps(self, ac: AcceptanceCriterion, start_num: int) -> List[TestStep]:
        """Generate negative scenario test steps."""
        steps = []
        step_num = start_num
        
        steps.append(TestStep(
            action="Launch the application.",
            expected_result="Application launches successfully and main window is displayed.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action=f"Navigate to the feature related to: {ac.text}",
            expected_result="Feature interface is displayed and accessible.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action=f"Attempt to perform the action with invalid input or conditions.",
            expected_result="System displays appropriate error message and prevents invalid operation.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Verify system state remains consistent after error.",
            expected_result="System state is unchanged and no data corruption occurred.",
            step_number=step_num
        ))
        
        return steps
    
    def _generate_boundary_steps(self, ac: AcceptanceCriterion, start_num: int) -> List[TestStep]:
        """Generate boundary condition test steps."""
        steps = []
        step_num = start_num
        
        steps.append(TestStep(
            action="Launch the application.",
            expected_result="Application launches successfully and main window is displayed.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action=f"Navigate to the feature related to: {ac.text}",
            expected_result="Feature interface is displayed and accessible.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Test with minimum boundary value.",
            expected_result="System handles minimum value correctly.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Test with maximum boundary value.",
            expected_result="System handles maximum value correctly.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Test with value just outside boundaries.",
            expected_result="System rejects invalid boundary values with appropriate error message.",
            step_number=step_num
        ))
        
        return steps
    
    def _generate_cancel_rollback_steps(self, ac: AcceptanceCriterion, start_num: int) -> List[TestStep]:
        """Generate cancel/rollback test steps."""
        steps = []
        step_num = start_num
        
        steps.append(TestStep(
            action="Launch the application.",
            expected_result="Application launches successfully and main window is displayed.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action=f"Navigate to the feature related to: {ac.text}",
            expected_result="Feature interface is displayed and accessible.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Initiate the action described in the acceptance criterion.",
            expected_result="Action interface is displayed.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Click Cancel or close the dialog without completing the action.",
            expected_result="Action is cancelled, dialog closes, and no changes are applied to the system.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Verify system state is unchanged.",
            expected_result="System returns to previous state with no modifications applied.",
            step_number=step_num
        ))
        
        return steps
    
    def _generate_persistence_steps(self, ac: AcceptanceCriterion, start_num: int) -> List[TestStep]:
        """Generate persistence test steps."""
        steps = []
        step_num = start_num
        
        steps.append(TestStep(
            action="Launch the application.",
            expected_result="Application launches successfully and main window is displayed.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action=f"Navigate to the feature related to: {ac.text}",
            expected_result="Feature interface is displayed and accessible.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Perform the action and save the data.",
            expected_result="Data is saved successfully and confirmation is displayed.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Close the application completely.",
            expected_result="Application closes successfully.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Reopen the application and navigate to the same feature.",
            expected_result="Previously saved data is displayed correctly and all information is preserved.",
            step_number=step_num
        ))
        
        return steps
    
    def _generate_undo_redo_steps(self, ac: AcceptanceCriterion, start_num: int) -> List[TestStep]:
        """Generate undo/redo test steps."""
        steps = []
        step_num = start_num
        
        steps.append(TestStep(
            action="Launch the application.",
            expected_result="Application launches successfully and main window is displayed.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action=f"Navigate to the feature related to: {ac.text}",
            expected_result="Feature interface is displayed and accessible.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Perform the action described in the acceptance criterion.",
            expected_result="Action is completed and changes are applied.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Execute Undo command.",
            expected_result="Previous action is reversed and system returns to previous state.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Execute Redo command.",
            expected_result="Previously undone action is reapplied and system returns to the modified state.",
            step_number=step_num
        ))
        
        return steps
    
    def _generate_accessibility_steps(self, ac: AcceptanceCriterion, start_num: int) -> List[TestStep]:
        """Generate accessibility test steps."""
        steps = []
        step_num = start_num
        
        steps.append(TestStep(
            action="Launch the application.",
            expected_result="Application launches successfully and main window is displayed.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action=f"Navigate to the feature related to: {ac.text} using keyboard only (Tab, Enter, Arrow keys).",
            expected_result="Feature is accessible via keyboard navigation and focus indicators are visible.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Verify all interactive elements have accessible labels and can be activated via keyboard.",
            expected_result="All elements are keyboard accessible and have proper ARIA labels or text equivalents.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Verify focus indicators are clearly visible for all focusable elements.",
            expected_result="Focus indicators meet WCAG 2.1 AA contrast requirements and are clearly visible.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Perform the action described in the acceptance criterion using keyboard only.",
            expected_result=f"Action completes successfully using keyboard navigation and {ac.text.lower().rstrip('.')}",
            step_number=step_num
        ))
        
        return steps
    
    def _build_umbrella_test_case(self, index: int) -> TestCase:
        """
        Build the final umbrella test case that verifies all AC coverage.
        
        Args:
            index: Index for internal ID generation
            
        Returns:
            TestCase object for umbrella test
        """
        internal_id = TestCaseNaming.generate_internal_id(self.story.id, index)
        
        feature = "Verification"
        module = "Test Coverage"
        category, subcategory = TestCaseNaming.get_category_subcategory(TestCaseType.UMBRELLA)
        description = f"Verify all acceptance criteria for Story {self.story.id} are covered and functional"
        
        title = TestCaseNaming.generate_title(
            internal_id, feature, module, category, subcategory, description
        )
        
        # Generate umbrella test steps
        steps = []
        step_num = 1
        
        steps.append(TestStep(
            action="Launch the application.",
            expected_result="Application launches successfully and main window is displayed.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action=f"Review all test cases generated for User Story {self.story.id}.",
            expected_result="All test cases are available and properly documented.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Verify that each acceptance criterion has corresponding test coverage.",
            expected_result="Every acceptance criterion is covered by at least one test case.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Execute a representative sample of test cases to verify functionality.",
            expected_result="All executed test cases pass and acceptance criteria are met.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Sign off on test coverage completeness.",
            expected_result="Test coverage is complete and ready for sign-off.",
            step_number=step_num
        ))
        
        # Add close step
        steps = StepsXMLGenerator.add_close_application_step(steps)
        
        tags = [
            f"story:{self.story.id}",
            "generated-by:ai-testgen",
            "test-type:umbrella"
        ]
        
        return TestCase(
            internal_id=internal_id,
            title=title,
            steps=steps,
            test_type=TestCaseType.UMBRELLA,
            acceptance_criterion_id=None,
            story_id=self.story.id,
            tags=tags
        )

