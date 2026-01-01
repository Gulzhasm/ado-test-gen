"""
End-to-end orchestration for test case generation and publishing.

This module coordinates the entire workflow:
1. Fetch User Story from ADO
2. Extract Acceptance Criteria
3. Generate test cases
4. Check for existing test cases (idempotency)
5. Create or update test cases in ADO
6. Add test cases to Test Plan and Test Suite

Research Note: This orchestration layer provides clear separation between
data retrieval, processing, generation, and publishing, making it easy to
integrate ML components at each stage.
"""
from typing import List, Dict, Any, Optional, Tuple
from src.ado.client import ADOClient
from src.ado.work_items import WorkItemsAPI
from src.ado.test_plans import TestPlansAPI
from src.parsing.ac_extractor import AcceptanceCriteriaExtractor
from src.models.story import UserStory
from src.models.acceptance_criteria import AcceptanceCriterion
from src.models.test_case import TestCase
from src.generation.testcase_factory import TestCaseFactory
from src.xml.steps_xml import StepsXMLGenerator


class TestCaseOrchestrator:
    """
    Orchestrates the complete test case generation and publishing workflow.
    
    Handles idempotency, error recovery, and provides detailed execution reports.
    """
    
    def __init__(self, client: Optional[ADOClient] = None):
        """
        Initialize orchestrator.
        
        Args:
            client: Optional ADOClient instance (creates new one if not provided)
        """
        self.client = client or ADOClient()
        self.work_items_api = WorkItemsAPI(self.client)
        self.test_plans_api = TestPlansAPI(self.client)
        self.ac_extractor = AcceptanceCriteriaExtractor()
    
    def generate_and_publish(
        self,
        story_id: int,
        plan_id: int,
        suite_id: int
    ) -> Dict[str, Any]:
        """
        Complete workflow: fetch story, generate test cases, and publish to ADO.
        
        Args:
            story_id: User Story work item ID
            plan_id: Test Plan ID
            suite_id: Test Suite ID (within the test plan)
            
        Returns:
            Dictionary with execution summary:
            - created_count: Number of test cases created
            - updated_count: Number of test cases updated
            - skipped_count: Number of test cases skipped (already exist)
            - errors: List of error messages
            - test_case_ids: List of created/updated test case IDs
        """
        result = {
            "created_count": 0,
            "updated_count": 0,
            "skipped_count": 0,
            "errors": [],
            "test_case_ids": []
        }
        
        try:
            # Step 1: Fetch User Story
            story = self._fetch_story(story_id)
            
            # Step 2: Extract Acceptance Criteria
            acceptance_criteria = self._extract_acceptance_criteria(story)
            
            if not acceptance_criteria:
                result["errors"].append(
                    f"No acceptance criteria found for Story {story_id}. "
                    "Cannot generate test cases."
                )
                return result
            
            # Step 3: Generate test cases
            test_cases = self._generate_test_cases(story, acceptance_criteria)
            
            # Step 4: Check for existing test cases (idempotency)
            try:
                existing_test_cases = self._find_existing_test_cases(story_id)
            except Exception as e:
                # If idempotency check fails, continue without it (will create duplicates)
                result["errors"].append(f"Warning: Could not check for existing test cases: {str(e)}")
                existing_test_cases = {}
            
            # Step 5: Create or update test cases
            created_ids, updated_ids, skipped_ids, errors = self._publish_test_cases(
                test_cases, existing_test_cases
            )
            
            result["created_count"] = len(created_ids)
            result["updated_count"] = len(updated_ids)
            result["skipped_count"] = len(skipped_ids)
            result["errors"].extend(errors)
            result["test_case_ids"] = created_ids + updated_ids
            
            # Step 6: Add test cases to Test Plan and Suite
            if result["test_case_ids"]:
                suite_errors = self._add_to_test_suite(plan_id, suite_id, result["test_case_ids"])
                result["errors"].extend(suite_errors)
            
        except Exception as e:
            result["errors"].append(f"Fatal error: {str(e)}")
        
        return result
    
    def _fetch_story(self, story_id: int) -> UserStory:
        """
        Fetch User Story from ADO and convert to model.
        
        Args:
            story_id: User Story work item ID
            
        Returns:
            UserStory model instance
            
        Raises:
            Exception: If story cannot be fetched or is not a User Story
        """
        work_item = self.work_items_api.get_user_story(story_id)
        fields = self.work_items_api.get_work_item_fields(work_item)
        
        # Verify it's a User Story
        work_item_type = fields.get(self.work_items_api.FIELD_WORK_ITEM_TYPE, "")
        if work_item_type != self.work_items_api.WORK_ITEM_TYPE_USER_STORY:
            raise ValueError(
                f"Work item {story_id} is not a User Story. "
                f"Found type: {work_item_type}"
            )
        
        # Extract fields
        title = fields.get(self.work_items_api.FIELD_TITLE, "")
        description_html = fields.get(self.work_items_api.FIELD_DESCRIPTION, None)
        ac_field_html = fields.get(self.work_items_api.FIELD_ACCEPTANCE_CRITERIA, None)
        
        # Extract AC
        ac_extractor = AcceptanceCriteriaExtractor()
        acceptance_criteria = ac_extractor.extract(
            description_html=description_html,
            ac_field_html=ac_field_html
        )
        
        return UserStory(
            id=story_id,
            title=title,
            description_html=description_html,
            description_text=None,  # Can be populated if needed
            acceptance_criteria_html=ac_field_html,
            acceptance_criteria=acceptance_criteria
        )
    
    def _extract_acceptance_criteria(self, story: UserStory) -> List[AcceptanceCriterion]:
        """
        Extract and normalize acceptance criteria from story.
        
        Args:
            story: UserStory model instance
            
        Returns:
            List of AcceptanceCriterion objects
        """
        criteria = []
        for idx, ac_text in enumerate(story.acceptance_criteria, start=1):
            criteria.append(
                AcceptanceCriterion(
                    id=idx,
                    text=ac_text,
                    original_order=idx
                )
            )
        return criteria
    
    def _generate_test_cases(
        self,
        story: UserStory,
        acceptance_criteria: List[AcceptanceCriterion]
    ) -> List[TestCase]:
        """
        Generate test cases from acceptance criteria.
        
        Args:
            story: UserStory model instance
            acceptance_criteria: List of AcceptanceCriterion objects
            
        Returns:
            List of TestCase objects
        """
        factory = TestCaseFactory(story, max_tests_per_ac=2)
        return factory.generate_all_test_cases(acceptance_criteria)
    
    def _find_existing_test_cases(self, story_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Find existing test cases for the story (idempotency check).
        
        Uses tags first, then falls back to title prefix matching.
        
        Args:
            story_id: User Story ID
            
        Returns:
            Dictionary mapping internal_id to work item data
        """
        existing = {}
        
        # Try tag-based search first
        tags = [f"story:{story_id}", "generated-by:ado-testgen"]
        tagged_items = self.work_items_api.find_test_cases_by_tags(tags)
        
        for item in tagged_items:
            fields = self.work_items_api.get_work_item_fields(item)
            title = fields.get(self.work_items_api.FIELD_TITLE, "")
            # Extract internal ID from title (format: "ID: ...")
            if ":" in title:
                internal_id = title.split(":")[0].strip()
                existing[internal_id] = item
        
        # If no tagged items found, try title prefix search
        if not existing:
            title_prefix = f"{story_id}-"
            prefixed_items = self.work_items_api.find_test_cases_by_title_prefix(title_prefix)
            
            for item in prefixed_items:
                fields = self.work_items_api.get_work_item_fields(item)
                title = fields.get(self.work_items_api.FIELD_TITLE, "")
                if ":" in title:
                    internal_id = title.split(":")[0].strip()
                    existing[internal_id] = item
        
        return existing
    
    def _publish_test_cases(
        self,
        test_cases: List[TestCase],
        existing_test_cases: Dict[str, Dict[str, Any]]
    ) -> Tuple[List[int], List[int], List[str], List[str]]:
        """
        Create or update test cases in ADO.
        
        Args:
            test_cases: List of TestCase objects to publish
            existing_test_cases: Dictionary of existing test cases by internal_id
            
        Returns:
            Tuple of (created_ids, updated_ids, skipped_ids, errors)
        """
        created_ids = []
        updated_ids = []
        skipped_ids = []
        errors = []
        
        for test_case in test_cases:
            try:
                # Generate XML steps
                steps_xml = StepsXMLGenerator.generate(test_case.steps)
                
                # Check if test case already exists
                if test_case.internal_id in existing_test_cases:
                    # Update existing
                    existing_item = existing_test_cases[test_case.internal_id]
                    work_item_id = existing_item["id"]
                    
                    # Check if update is needed
                    fields = self.work_items_api.get_work_item_fields(existing_item)
                    existing_steps = fields.get("Microsoft.VSTS.TCM.Steps", "")
                    
                    if existing_steps != steps_xml or fields.get(self.work_items_api.FIELD_TITLE) != test_case.title:
                        # Update needed
                        self.work_items_api.update_test_case(
                            work_item_id=work_item_id,
                            title=test_case.title,
                            steps_xml=steps_xml,
                            tags=test_case.tags
                        )
                        updated_ids.append(work_item_id)
                    else:
                        # No changes needed
                        skipped_ids.append(test_case.internal_id)
                else:
                    # Create new
                    created_item = self.work_items_api.create_test_case(
                        title=test_case.title,
                        steps_xml=steps_xml,
                        tags=test_case.tags
                    )
                    created_ids.append(created_item["id"])
            
            except Exception as e:
                errors.append(
                    f"Error processing test case {test_case.internal_id}: {str(e)}"
                )
        
        return created_ids, updated_ids, skipped_ids, errors
    
    def _add_to_test_suite(
        self,
        plan_id: int,
        suite_id: int,
        test_case_ids: List[int]
    ) -> List[str]:
        """
        Add test cases to test suite.
        
        Args:
            plan_id: Test Plan ID
            suite_id: Test Suite ID
            test_case_ids: List of test case work item IDs
            
        Returns:
            List of error messages (empty if successful)
        """
        errors = []
        
        try:
            # Get existing test cases in suite
            existing_suite_cases = self.test_plans_api.get_suite_test_cases(plan_id, suite_id)
            existing_ids = {tc.get("workItem", {}).get("id") for tc in existing_suite_cases}
            
            # Filter out already-added test cases
            new_ids = [tc_id for tc_id in test_case_ids if tc_id not in existing_ids]
            
            if new_ids:
                result = self.test_plans_api.add_test_cases_to_suite(plan_id, suite_id, new_ids)
                # Extract errors from result
                if result.get("errors"):
                    errors.extend(result["errors"])
        except Exception as e:
            errors.append(f"Error adding test cases to suite: {str(e)}")
        
        return errors

