"""
Azure DevOps Work Items API operations.

This module handles CRUD operations for ADO work items, specifically:
- Retrieving User Stories by ID
- Creating and updating Test Case work items
- Querying existing test cases for idempotency checks

Research Note: This module is designed to be extensible for future ML-based
work item classification and relationship analysis.
"""
from typing import Optional, List, Dict, Any
from urllib.parse import quote
from src.ado.client import ADOClient


class WorkItemsAPI:
    """
    High-level interface for ADO Work Items API operations.
    
    Provides methods for retrieving user stories and managing test case work items
    with proper error handling and data transformation.
    """
    
    # ADO Work Item Types
    WORK_ITEM_TYPE_USER_STORY = "User Story"
    WORK_ITEM_TYPE_TEST_CASE = "Test Case"
    
    # ADO Field Reference Names
    FIELD_TITLE = "System.Title"
    FIELD_DESCRIPTION = "System.Description"
    FIELD_ACCEPTANCE_CRITERIA = "Microsoft.VSTS.Common.AcceptanceCriteria"
    FIELD_STATE = "System.State"
    FIELD_WORK_ITEM_TYPE = "System.WorkItemType"
    FIELD_TAGS = "System.Tags"
    
    def __init__(self, client: ADOClient):
        """
        Initialize Work Items API client.
        
        Args:
            client: ADOClient instance for making API calls
        """
        self.client = client
    
    def get_user_story(self, story_id: int) -> Dict[str, Any]:
        """
        Retrieve a User Story work item by ID.
        
        Args:
            story_id: User Story work item ID
            
        Returns:
            Dictionary containing work item fields and metadata
            
        Raises:
            requests.HTTPError: If story not found or API error occurs
        """
        path = f"_apis/wit/workitems/{story_id}"
        params = {
            "api-version": "7.1",
            "$expand": "all"  # Include relations, fields, etc.
        }
        
        response = self.client.get(path, params=params)
        return response.json()
    
    def get_work_item_fields(self, work_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract fields dictionary from work item response.
        
        Args:
            work_item: Work item JSON response from ADO API
            
        Returns:
            Dictionary of field reference names to values
        """
        return work_item.get("fields", {})
    
    def create_test_case(self, title: str, steps_xml: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new Test Case work item in ADO.
        
        Args:
            title: Test case title
            steps_xml: XML-formatted test steps (Microsoft.VSTS.TCM.Steps format)
            tags: Optional list of tags to apply
            
        Returns:
            Created work item response
        """
        # ADO API requires the work item type in the path
        # Use literal space - requests will handle URL encoding automatically
        path = "_apis/wit/workitems/$Test Case"
        params = {"api-version": "7.1"}
        
        # Build JSON Patch document for work item creation
        patch_document = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": title
            },
            {
                "op": "add",
                "path": "/fields/Microsoft.VSTS.TCM.Steps",
                "value": steps_xml
            }
        ]
        
        # Add tags if provided
        if tags:
            tags_str = "; ".join(tags)
            patch_document.append({
                "op": "add",
                "path": "/fields/System.Tags",
                "value": tags_str
            })
        
        try:
            response = self.client.post(path, json=patch_document, params=params)
            return response.json()
        except Exception as e:
            # Log the actual error response for debugging
            if hasattr(e, 'response') and e.response is not None:
                error_detail = e.response.text
                raise Exception(f"Failed to create test case: {str(e)}\nResponse: {error_detail}")
            raise
    
    def update_test_case(self, work_item_id: int, title: Optional[str] = None, 
                        steps_xml: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Update an existing Test Case work item.
        
        Args:
            work_item_id: Test case work item ID
            title: New title (if provided)
            steps_xml: New steps XML (if provided)
            tags: New tags list (if provided)
            
        Returns:
            Updated work item response
        """
        path = f"_apis/wit/workitems/{work_item_id}"
        params = {"api-version": "7.1"}
        
        patch_document = []
        
        if title:
            patch_document.append({
                "op": "replace",
                "path": "/fields/System.Title",
                "value": title
            })
        
        if steps_xml:
            patch_document.append({
                "op": "replace",
                "path": "/fields/Microsoft.VSTS.TCM.Steps",
                "value": steps_xml
            })
        
        if tags:
            tags_str = "; ".join(tags)
            patch_document.append({
                "op": "replace",
                "path": "/fields/System.Tags",
                "value": tags_str
            })
        
        if not patch_document:
            raise ValueError("At least one field must be provided for update")
        
        try:
            response = self.client.patch(path, json=patch_document, params=params)
            return response.json()
        except Exception as e:
            # Log the actual error response for debugging
            if hasattr(e, 'response') and e.response is not None:
                error_detail = e.response.text
                raise Exception(f"Failed to update test case {work_item_id}: {str(e)}\nResponse: {error_detail}")
            raise
    
    def find_test_cases_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """
        Find test cases that have all specified tags.
        
        This is used for idempotency checks to find existing generated test cases.
        
        Args:
            tags: List of tags to search for (all must match)
            
        Returns:
            List of matching work items
        """
        # Build WIQL (Work Item Query Language) query
        # Escape single quotes in tags for WIQL
        escaped_tags = [tag.replace("'", "''") for tag in tags]
        tags_condition = " AND ".join([f"[System.Tags] CONTAINS '{tag}'" for tag in escaped_tags])
        wiql = f"SELECT [System.Id], [System.Title], [System.Tags] FROM WorkItems WHERE [System.WorkItemType] = 'Test Case' AND {tags_condition} ORDER BY [System.Id]"
        
        path = "_apis/wit/wiql"
        params = {"api-version": "7.1"}
        
        response = self.client.post(path, json={"query": wiql}, params=params)
        query_result = response.json()
        
        # Extract work item IDs from query result
        work_item_ids = [item["id"] for item in query_result.get("workItems", [])]
        
        if not work_item_ids:
            return []
        
        # Fetch full work item details
        ids_str = ",".join(map(str, work_item_ids))
        path = f"_apis/wit/workitems"
        params = {
            "api-version": "7.1",
            "ids": ids_str,
            "$expand": "all"
        }
        
        response = self.client.get(path, params=params)
        return response.json().get("value", [])
    
    def find_test_cases_by_title_prefix(self, title_prefix: str) -> List[Dict[str, Any]]:
        """
        Find test cases with titles starting with the given prefix.
        
        Used as fallback idempotency check when tags are not available.
        
        Args:
            title_prefix: Title prefix to search for
            
        Returns:
            List of matching work items
        """
        # Escape single quotes in title prefix for WIQL
        escaped_prefix = title_prefix.replace("'", "''")
        wiql = f"SELECT [System.Id], [System.Title], [System.Tags] FROM WorkItems WHERE [System.WorkItemType] = 'Test Case' AND [System.Title] STARTS WITH '{escaped_prefix}' ORDER BY [System.Id]"
        
        path = "_apis/wit/wiql"
        params = {"api-version": "7.1"}
        
        response = self.client.post(path, json={"query": wiql}, params=params)
        query_result = response.json()
        
        work_item_ids = [item["id"] for item in query_result.get("workItems", [])]
        
        if not work_item_ids:
            return []
        
        ids_str = ",".join(map(str, work_item_ids))
        path = f"_apis/wit/workitems"
        params = {
            "api-version": "7.1",
            "ids": ids_str,
            "$expand": "all"
        }
        
        response = self.client.get(path, params=params)
        return response.json().get("value", [])

