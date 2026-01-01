"""
Hybrid test case generation pipeline.

This module orchestrates the hybrid approach:
1. Generate baseline tests (rules/templates)
2. LLM-based scenario expansion
3. Validation and sanitization
4. Deduplication
5. Publishing to ADO
"""
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from src.ado.client import ADOClient
from src.ado.work_items import WorkItemsAPI
from src.ado.test_plans import TestPlansAPI
from src.parsing.ac_extractor import AcceptanceCriteriaExtractor
from src.parsing.ac_splitter import ACSplitter
from src.models.story import UserStory
from src.models.acceptance_criteria import AcceptanceCriterion
from src.models.test_case import TestCase, TestStep
from src.generation.testcase_factory import TestCaseFactory
from src.generation.naming import TestCaseNaming
from src.gating.validator import TestCaseValidator
from src.gating.deduper import HybridDeduper
from src.llm.planner import LLMPlanner
from src.llm.step_writer import LLMStepWriter
from src.xml.steps_xml import StepsXMLGenerator


class HybridPipeline:
    """
    Hybrid test case generation pipeline.
    
    Combines deterministic rule-based generation with LLM-based
    scenario expansion, with strict validation and deduplication.
    """
    
    def __init__(self, client: Optional[ADOClient] = None):
        """
        Initialize hybrid pipeline.
        
        Args:
            client: Optional ADOClient instance
        """
        self.client = client or ADOClient()
        self.work_items_api = WorkItemsAPI(self.client)
        self.test_plans_api = TestPlansAPI(self.client)
        self.ac_extractor = AcceptanceCriteriaExtractor()
        self.ac_splitter = ACSplitter()
        
        # LLM components (may be None if not configured)
        self.planner = LLMPlanner()
        self.step_writer = LLMStepWriter()
        self.llm_enabled = self.planner.is_configured() and self.step_writer.is_configured()
        
        # Validation and deduplication
        self.validator = TestCaseValidator()
        self.deduper = HybridDeduper()
    
    def run_hybrid_pipeline(
        self,
        story_id: int,
        plan_id: int,
        suite_id: int,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Run complete hybrid pipeline.
        
        Args:
            story_id: User Story ID
            plan_id: Test Plan ID
            suite_id: Test Suite ID
            dry_run: If True, don't publish to ADO
            
        Returns:
            Dictionary with execution summary
        """
        result = {
            "story_id": story_id,
            "baseline_count": 0,
            "llm_suggested": 0,
            "llm_accepted": 0,
            "llm_rejected_validation": 0,
            "llm_rejected_duplicate": 0,
            "created_count": 0,
            "updated_count": 0,
            "skipped_count": 0,
            "added_to_suite": 0,
            "errors": [],
            "test_case_ids": []
        }
        
        try:
            # Stage A: Fetch story and ACs
            story = self._fetch_story(story_id)
            acceptance_criteria = self._extract_acceptance_criteria(story)
            
            if not acceptance_criteria:
                result["errors"].append("No acceptance criteria found")
                return result
            
            # Stage B: Generate baseline tests
            baseline_tests = self._generate_baseline(story, acceptance_criteria)
            result["baseline_count"] = len(baseline_tests)
            
            # Stage C: LLM expansion (if enabled)
            llm_tests = []
            if self.llm_enabled:
                llm_tests = self._generate_llm_tests(
                    story,
                    acceptance_criteria,
                    baseline_tests
                )
                result["llm_suggested"] = len(llm_tests)
            
            # Stage D: Merge and deduplicate
            all_tests = baseline_tests + llm_tests
            final_tests, deduped_count = self._deduplicate_tests(all_tests)
            result["llm_rejected_duplicate"] = deduped_count
            
            # Count accepted LLM tests
            llm_accepted = len([t for t in final_tests if "src:llm" in t.tags])
            result["llm_accepted"] = llm_accepted
            result["llm_rejected_validation"] = result["llm_suggested"] - llm_accepted - deduped_count
            
            if dry_run:
                # Dry run: just return summary
                result["test_case_ids"] = [f"DRY-RUN-{i}" for i in range(len(final_tests))]
                return result
            
            # Stage E: Publish to ADO
            publish_result = self._publish_test_cases(
                final_tests,
                story_id,
                plan_id,
                suite_id
            )
            
            result.update(publish_result)
            
        except Exception as e:
            result["errors"].append(f"Pipeline error: {str(e)}")
            import traceback
            result["errors"].append(traceback.format_exc())
        
        return result
    
    def _fetch_story(self, story_id: int) -> UserStory:
        """Fetch user story from ADO."""
        # Use the same pattern as TestCaseOrchestrator
        work_item = self.work_items_api.get_user_story(story_id)
        fields = self.work_items_api.get_work_item_fields(work_item)
        
        title = fields.get(WorkItemsAPI.FIELD_TITLE, "")
        description_html = fields.get(WorkItemsAPI.FIELD_DESCRIPTION, None)
        ac_field_html = fields.get(WorkItemsAPI.FIELD_ACCEPTANCE_CRITERIA, None)
        
        # Extract AC using the extractor (same as TestCaseOrchestrator)
        acceptance_criteria = self.ac_extractor.extract(
            description_html=description_html,
            ac_field_html=ac_field_html
        )
        
        return UserStory(
            id=story_id,
            title=title,
            description_html=description_html,
            description_text=None,
            acceptance_criteria_html=ac_field_html,
            acceptance_criteria=acceptance_criteria
        )
    
    def _extract_acceptance_criteria(self, story: UserStory) -> List[AcceptanceCriterion]:
        """Extract and split acceptance criteria."""
        # Story already has acceptance_criteria as a list of strings
        criteria = []
        for idx, ac_text in enumerate(story.acceptance_criteria, start=1):
            criteria.append(AcceptanceCriterion(
                id=idx,
                text=ac_text,
                original_order=idx
            ))
        return criteria
    
    def _generate_baseline(
        self,
        story: UserStory,
        acceptance_criteria: List[AcceptanceCriterion]
    ) -> List[TestCase]:
        """Generate baseline tests using rules/templates."""
        factory = TestCaseFactory(story, max_tests_per_ac=2)
        baseline_tests = factory.generate_all_test_cases(acceptance_criteria)
        
        # Tag baseline tests
        tagged_baseline = []
        for test in baseline_tests:
            test_dict = test.dict()
            test_dict["tags"] = test.tags + ["src:baseline"]
            tagged_baseline.append(TestCase(**test_dict))
        
        return tagged_baseline
    
    def _generate_llm_tests(
        self,
        story: UserStory,
        acceptance_criteria: List[AcceptanceCriterion],
        baseline_tests: List[TestCase]
    ) -> List[TestCase]:
        """Generate LLM-based test scenarios."""
        llm_tests = []
        baseline_titles = [tc.title for tc in baseline_tests]
        
        # Get story feature/module from first baseline test (if available)
        feature = "Feature"
        module = "Module"
        if baseline_tests:
            # Extract from first baseline title
            title_parts = baseline_tests[0].title.split(" / ")
            if len(title_parts) >= 3:
                feature = title_parts[1] if len(title_parts) > 1 else "Feature"
                module = title_parts[2] if len(title_parts) > 2 else "Module"
        
        # Process each AC item
        for ac in acceptance_criteria:
            # Call planner
            planner_response = self.planner.plan_scenarios(
                story_title=story.title,
                story_description=story.description,
                ac_item=ac.text,
                baseline_titles=baseline_titles
            )
            
            # Process each suggestion
            for suggestion in planner_response.suggestions:
                # Validate short descriptor
                sanitized = self.validator.sanitize_short_descriptor(suggestion.short_descriptor)
                if not self.validator.validate_short_descriptor(sanitized):
                    continue
                
                # Call step writer
                step_response = self.step_writer.write_steps(
                    story_title=story.title,
                    story_description=story.description,
                    ac_item=ac.text,
                    scenario_category=suggestion.category,
                    scenario_subcategory=suggestion.subcategory,
                    scenario_descriptor=sanitized,
                    preconditions=suggestion.preconditions,
                    steps_hint=suggestion.steps_hint
                )
                
                if not step_response.steps:
                    continue
                
                # Convert steps to dict format
                steps_dict = [
                    {"action": step.action, "expected": step.expected}
                    for step in step_response.steps
                ]
                
                # Generate internal ID (use next available ID)
                # Count existing tests to determine next ID
                existing_count = len(baseline_tests) + len(llm_tests)
                internal_id = TestCaseNaming.generate_internal_id(story.id, existing_count)
                
                # Build test case draft
                testcase_draft = {
                    "short_descriptor": sanitized,
                    "steps": steps_dict,
                    "tags": [
                        f"story:{story.id}",
                        "generated-by:ado-testgen",
                        "mode:hybrid",
                        f"ac-hash:{self._hash_ac(ac.text)}",
                        "src:llm"
                    ]
                }
                
                # Validate and canonicalize
                validated_test = self.validator.validate_and_canonicalize(
                    testcase_draft=testcase_draft,
                    story_id=story.id,
                    internal_id=internal_id,
                    feature=feature,
                    module=module,
                    category=suggestion.category,
                    subcategory=suggestion.subcategory
                )
                
                if validated_test:
                    llm_tests.append(validated_test)
        
        return llm_tests
    
    def _deduplicate_tests(
        self,
        all_tests: List[TestCase]
    ) -> Tuple[List[TestCase], int]:
        """
        Deduplicate test cases.
        
        Returns:
            Tuple of (deduplicated_tests, deduped_count)
        """
        if not all_tests:
            return [], 0
        
        deduplicated = []
        deduped_count = 0
        
        for test in all_tests:
            # Check against already accepted tests
            is_duplicate = False
            for existing in deduplicated:
                if self.deduper.is_duplicate(test, existing):
                    is_duplicate = True
                    deduped_count += 1
                    break
            
            if not is_duplicate:
                deduplicated.append(test)
        
        return deduplicated, deduped_count
    
    def _publish_test_cases(
        self,
        test_cases: List[TestCase],
        story_id: int,
        plan_id: int,
        suite_id: int
    ) -> Dict[str, Any]:
        """Publish test cases to ADO."""
        result = {
            "created_count": 0,
            "updated_count": 0,
            "skipped_count": 0,
            "added_to_suite": 0,
            "errors": [],
            "test_case_ids": []
        }
        
        # Find existing test cases
        try:
            existing_test_cases = self._find_existing_test_cases(story_id)
        except Exception as e:
            result["errors"].append(f"Warning: Could not check for existing test cases: {str(e)}")
            existing_test_cases = {}
        
        # Process each test case
        created_ids = []
        updated_ids = []
        skipped_ids = []
        
        for test_case in test_cases:
            try:
                # Generate XML steps
                steps_xml = StepsXMLGenerator.generate(test_case.steps)
                
                # Check if exists
                if test_case.internal_id in existing_test_cases:
                    existing_item = existing_test_cases[test_case.internal_id]
                    work_item_id = existing_item["id"]
                    
                    # Check if update needed
                    fields = self.work_items_api.get_work_item_fields(existing_item)
                    existing_steps = fields.get("Microsoft.VSTS.TCM.Steps", "")
                    
                    if existing_steps != steps_xml or fields.get(WorkItemsAPI.FIELD_TITLE) != test_case.title:
                        # Update
                        self.work_items_api.update_test_case(
                            work_item_id=work_item_id,
                            title=test_case.title,
                            steps_xml=steps_xml,
                            tags=test_case.tags
                        )
                        updated_ids.append(work_item_id)
                    else:
                        skipped_ids.append(work_item_id)
                else:
                    # Create new
                    work_item = self.work_items_api.create_test_case(
                        title=test_case.title,
                        steps_xml=steps_xml,
                        tags=test_case.tags
                    )
                    work_item_id = work_item["id"]
                    created_ids.append(work_item_id)
                
                result["test_case_ids"].append(work_item_id)
                
            except Exception as e:
                result["errors"].append(f"Error processing {test_case.internal_id}: {str(e)}")
        
        result["created_count"] = len(created_ids)
        result["updated_count"] = len(updated_ids)
        result["skipped_count"] = len(skipped_ids)
        
        # Add to suite
        all_ids = created_ids + updated_ids + [id for id in skipped_ids]
        if all_ids:
            suite_result = self.test_plans_api.add_test_cases_to_suite(
                plan_id=plan_id,
                suite_id=suite_id,
                test_case_ids=all_ids
            )
            result["added_to_suite"] = suite_result["added"]
            result["errors"].extend(suite_result["errors"])
        
        return result
    
    def _find_existing_test_cases(self, story_id: int) -> Dict[str, Dict[str, Any]]:
        """Find existing test cases for idempotency."""
        existing = {}
        
        # Try tag-based search
        tags = [f"story:{story_id}", "generated-by:ado-testgen"]
        tagged_items = self.work_items_api.find_test_cases_by_tags(tags)
        
        for item in tagged_items:
            fields = self.work_items_api.get_work_item_fields(item)
            title = fields.get(WorkItemsAPI.FIELD_TITLE, "")
            if ":" in title:
                internal_id = title.split(":")[0].strip()
                existing[internal_id] = item
        
        return existing
    
    def _hash_ac(self, ac_text: str) -> str:
        """Generate SHA1 hash of AC text."""
        return hashlib.sha1(ac_text.encode()).hexdigest()[:8]

