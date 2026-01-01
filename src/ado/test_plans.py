"""
Azure DevOps Test Plans and Test Suites API operations.

This module handles adding test cases to test plans and test suites,
which is required for test case organization and execution tracking.

Research Note: This module can be extended for ML-based test case
prioritization and suite optimization.
"""
from typing import List, Dict, Any
from src.ado.client import ADOClient


class TestPlansAPI:
    """
    High-level interface for ADO Test Plans and Test Suites API.
    
    Provides methods for adding test cases to test suites within test plans.
    """
    
    def __init__(self, client: ADOClient):
        """
        Initialize Test Plans API client.
        
        Args:
            client: ADOClient instance for making API calls
        """
        self.client = client
    
    def add_test_cases_to_suite(self, plan_id: int, suite_id: int, 
                                test_case_ids: List[int]) -> Dict[str, Any]:
        """
        Add multiple test cases to a test suite within a test plan.
        
        ADO API requires adding test cases one at a time using the work item ID.
        
        Args:
            plan_id: Test Plan ID
            suite_id: Test Suite ID (within the test plan)
            test_case_ids: List of test case work item IDs to add
            
        Returns:
            Dictionary with 'added' count and any errors
        """
        results = {"added": 0, "errors": []}
        
        # First, get existing test cases in suite to avoid duplicates
        try:
            existing = self.get_suite_test_cases(plan_id, suite_id)
            # Extract work item IDs - handle different possible response structures
            existing_ids = set()
            for tc in existing:
                # Try different possible structures
                if isinstance(tc, dict):
                    # Structure 1: {"workItem": {"id": 123}}
                    if "workItem" in tc and isinstance(tc["workItem"], dict):
                        work_item_id = tc["workItem"].get("id")
                        if work_item_id is not None:
                            existing_ids.add(int(work_item_id))  # Convert to int for comparison
                    # Structure 2: {"id": 123} (direct)
                    elif "id" in tc:
                        existing_ids.add(int(tc["id"]))  # Convert to int for comparison
        except Exception as e:
            # If we can't get existing test cases, continue anyway
            existing_ids = set()
        
        # Add test cases one at a time (ADO API requirement)
        for tc_id in test_case_ids:
            # Skip if already in suite
            if tc_id in existing_ids:
                results["added"] += 1  # Count as added since it's already there
                continue
                
            try:
                # Use the work item ID directly in the path
                path = f"_apis/test/plans/{plan_id}/suites/{suite_id}/testcases/{tc_id}"
                params = {"api-version": "7.1-preview.2"}
                
                # POST with empty body to add the test case
                response = self.client.post(path, json={}, params=params)
                results["added"] += 1
            except Exception as e:
                error_str = str(e).lower()
                error_detail = ""
                
                # Try to extract more details from the error response
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_detail = e.response.text[:500]  # First 500 chars
                    except:
                        pass
                
                # Check if error message indicates duplicate (already in suite)
                is_duplicate = (
                    "already exists" in error_str or 
                    "409" in error_str or 
                    "duplicate" in error_str or
                    ("400" in error_str and "duplicate" in error_detail.lower())
                )
                
                if is_duplicate:
                    results["added"] += 1  # Count as added since it's already there
                else:
                    # For 400 errors, double-check if it's a duplicate by querying the suite again
                    if "400" in error_str:
                        try:
                            existing_check = self.get_suite_test_cases(plan_id, suite_id)
                            existing_ids_check = set()
                            for tc in existing_check:
                                if isinstance(tc, dict):
                                    if "workItem" in tc and isinstance(tc["workItem"], dict):
                                        work_item_id = tc["workItem"].get("id")
                                        if work_item_id is not None:
                                            # Convert to int for comparison
                                            existing_ids_check.add(int(work_item_id))
                                    elif "id" in tc:
                                        existing_ids_check.add(int(tc["id"]))
                            if tc_id in existing_ids_check:
                                results["added"] += 1  # Already in suite, count as added
                                continue
                        except:
                            pass
                    
                    # Include error detail in the error message
                    error_msg = f"Failed to add test case {tc_id}: {str(e)}"
                    if error_detail:
                        error_msg += f" | Details: {error_detail}"
                    results["errors"].append(error_msg)
        
        return results
    
    def get_suite_test_cases(self, plan_id: int, suite_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all test cases currently in a test suite.
        
        Used to check if test cases are already added (idempotency).
        
        Args:
            plan_id: Test Plan ID
            suite_id: Test Suite ID
            
        Returns:
            List of test case entries in the suite
        """
        path = f"_apis/test/plans/{plan_id}/suites/{suite_id}/testcases"
        params = {"api-version": "7.1-preview.2"}
        
        response = self.client.get(path, params=params)
        return response.json().get("value", [])
    
    def remove_test_case_from_suite(self, plan_id: int, suite_id: int, 
                                    test_case_id: int) -> None:
        """
        Remove a test case from a test suite.
        
        Args:
            plan_id: Test Plan ID
            suite_id: Test Suite ID
            test_case_id: Test case work item ID to remove
        """
        path = f"_apis/test/plans/{plan_id}/suites/{suite_id}/testcases/{test_case_id}"
        params = {"api-version": "7.1-preview.2"}
        
        self.client.delete(path, params=params)

