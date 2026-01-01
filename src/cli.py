"""
Command-line interface for ADO Test Case Generator.

Provides a user-friendly CLI for generating and publishing test cases
from User Stories in Azure DevOps.
"""
import argparse
import sys
from typing import Optional
from src.orchestration.generate_and_publish import TestCaseOrchestrator
from src.config.settings import settings


def main():
    """
    Main CLI entry point.
    
    Parses command-line arguments and executes test case generation workflow.
    """
    parser = argparse.ArgumentParser(
        description="Generate and publish test cases from Azure DevOps User Stories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli --story-id 271309 --plan-id 123 --suite-id 456
  
  python -m src.cli --story-id 271309 --plan-id 123 --suite-id 456 --verbose
        """
    )
    
    parser.add_argument(
        "--story-id",
        type=int,
        required=True,
        help="User Story work item ID"
    )
    
    parser.add_argument(
        "--plan-id",
        type=int,
        required=True,
        help="Test Plan ID"
    )
    
    parser.add_argument(
        "--suite-id",
        type=int,
        required=True,
        help="Test Suite ID (within the test plan)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Validate configuration
    if not settings.ado_org or not settings.ado_project or not settings.ado_pat:
        print("ERROR: Missing required configuration.")
        print("Please set the following environment variables or create a .env file:")
        print("  - ADO_ORG: Azure DevOps organization name")
        print("  - ADO_PROJECT: Azure DevOps project name")
        print("  - ADO_PAT: Personal Access Token")
        sys.exit(1)
    
    # Execute workflow
    if args.verbose:
        print(f"Fetching User Story {args.story_id}...")
        print(f"Test Plan: {args.plan_id}, Test Suite: {args.suite_id}")
        print()
    
    orchestrator = TestCaseOrchestrator()
    
    try:
        result = orchestrator.generate_and_publish(
            story_id=args.story_id,
            plan_id=args.plan_id,
            suite_id=args.suite_id
        )
        
        # Print summary
        print("=" * 60)
        print("Test Case Generation Summary")
        print("=" * 60)
        print(f"Created:  {result['created_count']} test case(s)")
        print(f"Updated:  {result['updated_count']} test case(s)")
        print(f"Skipped:  {result['skipped_count']} test case(s)")
        print()
        
        if result['test_case_ids']:
            print(f"Test Case IDs: {', '.join(map(str, result['test_case_ids']))}")
            print()
        
        if result['errors']:
            print("Errors:")
            for error in result['errors']:
                print(f"  - {error}")
            print()
            sys.exit(1)
        else:
            print("✓ Success! All test cases generated and published.")
            sys.exit(0)
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

