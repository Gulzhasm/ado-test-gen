"""
Script to fetch and display User Story data and Acceptance Criteria from Azure DevOps.

Usage:
    python3 fetch_story.py <story_id>
    
Example:
    python3 fetch_story.py 270741
"""
import sys
import json
from src.ado.client import ADOClient
from src.ado.work_items import WorkItemsAPI
from src.parsing.ac_extractor import AcceptanceCriteriaExtractor
from src.parsing.html_parser import html_to_text


def fetch_and_display_story(story_id: int):
    """Fetch and display story data and acceptance criteria."""
    print("=" * 80)
    print(f"Fetching User Story #{story_id} from Azure DevOps")
    print("=" * 80)
    print()
    
    try:
        # Initialize client and API
        client = ADOClient()
        work_items_api = WorkItemsAPI(client)
        ac_extractor = AcceptanceCriteriaExtractor()
        
        # Fetch the work item
        print(f"Fetching work item {story_id}...")
        work_item = work_items_api.get_user_story(story_id)
        fields = work_items_api.get_work_item_fields(work_item)
        
        # Display basic information
        print("\n" + "-" * 80)
        print("WORK ITEM INFORMATION")
        print("-" * 80)
        
        work_item_type = fields.get(WorkItemsAPI.FIELD_WORK_ITEM_TYPE, "Unknown")
        title = fields.get(WorkItemsAPI.FIELD_TITLE, "No Title")
        state = fields.get(WorkItemsAPI.FIELD_STATE, "Unknown")
        
        print(f"ID: {story_id}")
        print(f"Type: {work_item_type}")
        print(f"Title: {title}")
        print(f"State: {state}")
        
        # Display description
        description_html = fields.get(WorkItemsAPI.FIELD_DESCRIPTION, None)
        if description_html:
            description_text = html_to_text(description_html)
            print("\n" + "-" * 80)
            print("DESCRIPTION")
            print("-" * 80)
            print(description_text)
        
        # Display Acceptance Criteria
        print("\n" + "-" * 80)
        print("ACCEPTANCE CRITERIA")
        print("-" * 80)
        
        ac_field_html = fields.get(WorkItemsAPI.FIELD_ACCEPTANCE_CRITERIA, None)
        
        # Extract AC using the extractor
        acceptance_criteria = ac_extractor.extract(
            description_html=description_html,
            ac_field_html=ac_field_html
        )
        
        if acceptance_criteria:
            print(f"\nFound {len(acceptance_criteria)} Acceptance Criteria:\n")
            for i, ac_text in enumerate(acceptance_criteria, 1):
                print(f"AC{i}: {ac_text}")
                print()
        else:
            print("\nNo Acceptance Criteria found.")
            if ac_field_html:
                print("\nRaw AC Field (HTML):")
                print(ac_field_html[:500] + "..." if len(ac_field_html) > 500 else ac_field_html)
        
        # Display raw fields (for debugging)
        print("\n" + "-" * 80)
        print("RAW FIELDS (for reference)")
        print("-" * 80)
        print(f"Description field present: {description_html is not None}")
        print(f"AC field present: {ac_field_html is not None}")
        if ac_field_html:
            ac_text = html_to_text(ac_field_html)
            print(f"\nRaw AC Text (first 500 chars):")
            print(ac_text[:500] + "..." if len(ac_text) > 500 else ac_text)
        
        print("\n" + "=" * 80)
        print("Fetch completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nERROR: Failed to fetch story {story_id}")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_story.py <story_id>")
        print("Example: python3 fetch_story.py 270741")
        sys.exit(1)
    
    try:
        story_id = int(sys.argv[1])
    except ValueError:
        print(f"Error: '{sys.argv[1]}' is not a valid story ID (must be an integer)")
        sys.exit(1)
    
    fetch_and_display_story(story_id)

