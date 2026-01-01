"""
Test case factory using template-based generation.

This module orchestrates the creation of test cases from Acceptance Criteria
using the template engine and classifier. It handles:
- AC classification
- Template selection and application
- Test case generation with proper naming
- Idempotency via AC hashing

Research Note: This factory is rule-based but designed for ML enhancement
at classification and template selection stages.
"""
import hashlib
from typing import List, Optional
from src.models.story import UserStory
from src.models.acceptance_criteria import AcceptanceCriterion
from src.models.test_case import TestCase, TestCaseType, TestStep
from src.parsing.ac_classifier import AcceptanceCriteriaClassifier, ACCategory
from src.generation.template_engine import TemplateEngine
from src.generation.naming import TestCaseNaming
from src.generation.title_builder import TitleBuilder
from src.xml.steps_xml import StepsXMLGenerator


class TestCaseFactory:
    """
    Factory for generating test cases from Acceptance Criteria using templates.
    
    Uses rule-based classification and template matching to generate
    deterministic test cases.
    """
    
    def __init__(self, story: UserStory, max_tests_per_ac: int = 2):
        """
        Initialize factory.
        
        Args:
            story: User Story model instance
            max_tests_per_ac: Maximum number of test cases per AC (default: 2)
        """
        self.story = story
        self.max_tests_per_ac = max_tests_per_ac
        self.classifier = AcceptanceCriteriaClassifier()
        self.template_engine = TemplateEngine()
    
    def generate_all_test_cases(
        self,
        acceptance_criteria: List[AcceptanceCriterion]
    ) -> List[TestCase]:
        """
        Generate all test cases for given acceptance criteria.
        
        Generates:
        - Primary test case per AC (based on classification)
        - Optional additional test cases (negative, boundary) if applicable
        - One umbrella test case at the end
        
        Args:
            acceptance_criteria: List of AcceptanceCriterion objects
            
        Returns:
            List of TestCase objects
        """
        test_cases = []
        test_case_index = 0
        
        # Generate test cases for each AC
        for ac in acceptance_criteria:
            ac_test_cases = self._generate_test_cases_for_ac(ac, test_case_index)
            test_cases.extend(ac_test_cases)
            test_case_index += len(ac_test_cases)
        
        # Generate umbrella test case
        umbrella_test_case = self._generate_umbrella_test_case(test_case_index)
        test_cases.append(umbrella_test_case)
        
        return test_cases
    
    def _generate_test_cases_for_ac(
        self,
        ac: AcceptanceCriterion,
        start_index: int
    ) -> List[TestCase]:
        """
        Generate test cases for a single AC.
        
        Args:
            ac: AcceptanceCriterion object
            start_index: Starting index for internal ID generation
            
        Returns:
            List of TestCase objects (up to max_tests_per_ac)
        """
        test_cases = []
        current_index = start_index
        
        # Classify AC
        category = self.classifier.classify(ac.text)
        subcategory = self.classifier.get_subcategory(ac.text, category)
        
        # Generate primary test case
        primary_test_case = self._generate_single_test_case(
            ac=ac,
            category=category,
            subcategory=subcategory,
            test_type=TestCaseType.HAPPY_PATH,
            index=current_index
        )
        test_cases.append(primary_test_case)
        current_index += 1
        
        # Generate additional test cases if under limit
        if len(test_cases) < self.max_tests_per_ac:
            # Check if negative test is applicable
            if self._should_generate_negative(ac, category):
                negative_test_case = self._generate_negative_test_case(
                    ac=ac,
                    category=category,
                    subcategory=subcategory,
                    index=current_index
                )
                test_cases.append(negative_test_case)
                current_index += 1
        
        if len(test_cases) < self.max_tests_per_ac:
            # Check if boundary test is applicable
            if self._should_generate_boundary(ac, category):
                boundary_test_case = self._generate_boundary_test_case(
                    ac=ac,
                    category=category,
                    subcategory=subcategory,
                    index=current_index
                )
                test_cases.append(boundary_test_case)
                current_index += 1
        
        return test_cases
    
    def _generate_single_test_case(
        self,
        ac: AcceptanceCriterion,
        category: ACCategory,
        subcategory: str,
        test_type: TestCaseType,
        index: int
    ) -> TestCase:
        """
        Generate a single test case.
        
        Args:
            ac: AcceptanceCriterion object
            category: Classified category
            subcategory: Classified subcategory
            test_type: Type of test case
            index: Index for internal ID generation
            
        Returns:
            TestCase object
        """
        # Generate internal ID
        internal_id = TestCaseNaming.generate_internal_id(self.story.id, index)
        
        # Extract feature/module from story title and AC
        feature, module = self._extract_feature_module(ac.text)
        
        # Get category/subcategory for title
        title_category, title_subcategory = TestCaseNaming.get_category_subcategory(test_type)
        
        # Use classified category/subcategory for more specific title
        if category != ACCategory.OTHER_GENERAL:
            title_category = category.value
            title_subcategory = subcategory
        
        # Get short_descriptor from template (never use raw AC text)
        short_descriptor = self.template_engine.get_short_descriptor(category, subcategory)
        
        # Generate title using TitleBuilder (with strict validation)
        title = TitleBuilder.build(
            internal_id=internal_id,
            feature=feature,
            module=module,
            category=title_category,
            subcategory=title_subcategory,
            short_descriptor=short_descriptor
        )
        
        # Generate test steps from template or custom logic
        if test_type == TestCaseType.HAPPY_PATH:
            steps = self.template_engine.generate_steps(category, subcategory, ac.text)
        elif test_type == TestCaseType.NEGATIVE:
            steps = self._generate_negative_steps(ac, category, subcategory)
        elif test_type == TestCaseType.BOUNDARY:
            steps = self._generate_boundary_steps(ac, category, subcategory)
        else:
            steps = self.template_engine.generate_steps(category, subcategory, ac.text)
        
        # Add mandatory close step
        steps = StepsXMLGenerator.add_close_application_step(steps)
        
        # Generate AC hash for idempotency
        ac_hash = self._generate_ac_hash(ac.text)
        
        # Generate tags
        tags = [
            f"story:{self.story.id}",
            "generated-by:ado-testgen",
            "gen-mode:rules",
            f"ac-hash:{ac_hash}",
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
    
    def _generate_negative_test_case(
        self,
        ac: AcceptanceCriterion,
        category: ACCategory,
        subcategory: str,
        index: int
    ) -> TestCase:
        """Generate a negative test case."""
        return self._generate_single_test_case(
            ac=ac,
            category=category,
            subcategory=subcategory,
            test_type=TestCaseType.NEGATIVE,
            index=index
        )
    
    def _generate_boundary_test_case(
        self,
        ac: AcceptanceCriterion,
        category: ACCategory,
        subcategory: str,
        index: int
    ) -> TestCase:
        """Generate a boundary test case."""
        return self._generate_single_test_case(
            ac=ac,
            category=category,
            subcategory=subcategory,
            test_type=TestCaseType.BOUNDARY,
            index=index
        )
    
    def _should_generate_negative(
        self,
        ac: AcceptanceCriterion,
        category: ACCategory
    ) -> bool:
        """Determine if negative test should be generated."""
        # Generate negative for most categories except restrictions (which are already negative)
        if category == ACCategory.RESTRICTIONS_SCOPE:
            return False
        return True
    
    def _should_generate_boundary(
        self,
        ac: AcceptanceCriterion,
        category: ACCategory
    ) -> bool:
        """Determine if boundary test should be generated."""
        # Generate boundary for limit/retention and ordering
        return category in [ACCategory.LIMIT_RETENTION, ACCategory.ORDERING]
    
    def _extract_feature_module(self, ac_text: str) -> tuple[str, str]:
        """
        Extract feature and module from story title and AC text.
        
        Rules:
        - Feature = story title (cleaned) OR fallback "Work Item"
        - Module = "Properties Panel" if title contains "Properties Panel", else "Core"
        
        Args:
            ac_text: Acceptance criterion text
            
        Returns:
            Tuple of (feature, module)
        """
        # Extract feature from story title
        story_title = self.story.title
        feature = story_title.strip()
        
        # Clean feature name (remove special chars, limit length)
        feature = feature.replace("/", "-").replace("\\", "-")
        if len(feature) > 50:
            feature = feature[:47] + "..."
        
        if not feature:
            feature = "Work Item"
        
        # Determine module
        story_title_lower = story_title.lower()
        if "properties panel" in story_title_lower or "properties panel" in ac_text.lower():
            module = "Properties Panel"
        else:
            module = "Core"
        
        return feature, module
    
    def _generate_description(
        self,
        ac: AcceptanceCriterion,
        test_type: TestCaseType
    ) -> str:
        """
        Generate test case description.
        
        Args:
            ac: AcceptanceCriterion object
            test_type: Type of test case
            
        Returns:
            Description string
        """
        ac_text = ac.text.rstrip('.')
        
        if test_type == TestCaseType.HAPPY_PATH:
            return f"Verify {ac_text.lower()}"
        elif test_type == TestCaseType.NEGATIVE:
            return f"Verify system handles invalid input when {ac_text.lower()}"
        elif test_type == TestCaseType.BOUNDARY:
            return f"Verify boundary conditions for {ac_text.lower()}"
        else:
            return f"Verify {ac_text.lower()}"
    
    def _generate_ac_hash(self, ac_text: str) -> str:
        """
        Generate SHA1 hash of AC text for idempotency.
        
        Args:
            ac_text: Acceptance criterion text
            
        Returns:
            SHA1 hash string (first 8 characters)
        """
        hash_obj = hashlib.sha1(ac_text.encode('utf-8'))
        return hash_obj.hexdigest()[:8]
    
    def _generate_negative_steps(
        self,
        ac: AcceptanceCriterion,
        category: ACCategory,
        subcategory: str
    ) -> List[TestStep]:
        """Generate negative test steps."""
        steps = []
        step_num = 1
        
        # Start with base template steps
        base_steps = self.template_engine.generate_steps(category, subcategory, ac.text)
        
        # Use first step (launch) from template
        if base_steps:
            steps.append(base_steps[0])
            step_num += 1
        
        # Add negative-specific steps
        if step_num == 2:  # We have launch step
            steps.append(TestStep(
                action=f"Navigate to the feature related to: {ac.text}",
                expected_result="Feature interface is displayed and accessible.",
                step_number=step_num
            ))
            step_num += 1
        
        steps.append(TestStep(
            action="Attempt to perform the action with invalid input or conditions that should be rejected.",
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
    
    def _generate_boundary_steps(
        self,
        ac: AcceptanceCriterion,
        category: ACCategory,
        subcategory: str
    ) -> List[TestStep]:
        """Generate boundary test steps."""
        steps = []
        step_num = 1
        
        # Start with base template steps
        base_steps = self.template_engine.generate_steps(category, subcategory, ac.text)
        
        # Use first step (launch) from template
        if base_steps:
            steps.append(base_steps[0])
            step_num += 1
        
        # Add boundary-specific steps
        if step_num == 2:  # We have launch step
            steps.append(TestStep(
                action=f"Navigate to the feature related to: {ac.text}",
                expected_result="Feature interface is displayed and accessible.",
                step_number=step_num
            ))
            step_num += 1
        
        steps.append(TestStep(
            action="Test with minimum boundary value (if applicable).",
            expected_result="System handles minimum value correctly.",
            step_number=step_num
        ))
        step_num += 1
        
        steps.append(TestStep(
            action="Test with maximum boundary value (if applicable).",
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
    
    def _generate_umbrella_test_case(self, index: int) -> TestCase:
        """
        Generate umbrella test case that verifies all AC coverage.
        
        Args:
            index: Index for internal ID generation
            
        Returns:
            TestCase object
        """
        internal_id = TestCaseNaming.generate_internal_id(self.story.id, index)
        
        feature = "Acceptance Criteria Coverage"
        module = "Test Coverage"
        category, subcategory = TestCaseNaming.get_category_subcategory(TestCaseType.UMBRELLA)
        short_descriptor = "All acceptance criteria coverage"
        
        title = TitleBuilder.build(
            internal_id=internal_id,
            feature=feature,
            module=module,
            category=category,
            subcategory=subcategory,
            short_descriptor=short_descriptor
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
            "generated-by:ado-testgen",
            "gen-mode:rules",
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

