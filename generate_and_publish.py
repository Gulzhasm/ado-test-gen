#!/usr/bin/env python3
"""
Azure DevOps Test Case Generator - Main CLI Entry Point

Command-line interface for generating and publishing test cases to Azure DevOps.

Usage:
    python3 generate_and_publish.py <story_id> --plan-id <plan_id> --suite-id <suite_id> [--dry-run]

Example:
    python3 generate_and_publish.py 270741 --plan-id 123 --suite-id 456
    python3 generate_and_publish.py 270741 --plan-id 123 --suite-id 456 --dry-run
"""
import argparse
import sys
from typing import Optional
from src.orchestration.generate_and_publish import TestCaseOrchestrator
from src.orchestration.hybrid_pipeline import HybridPipeline
from src.ado.client import ADOClient
from src.ado.work_items import WorkItemsAPI


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate and publish test cases to Azure DevOps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 270741 --plan-id 123 --suite-id 456
  %(prog)s 270741 --plan-id 123 --suite-id 456 --dry-run
        """
    )
    
    parser.add_argument(
        "story_id",
        type=int,
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
        "--dry-run",
        action="store_true",
        help="Generate test cases but do not upload to ADO"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["rules", "hybrid"],
        default="rules",
        help="Generation mode: 'rules' (baseline only) or 'hybrid' (baseline + LLM)"
    )
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    try:
        orchestrator = TestCaseOrchestrator()
    except Exception as e:
        print(f"Error initializing ADO client: {e}", file=sys.stderr)
        print("Please ensure .env file is configured with ADO credentials.", file=sys.stderr)
        sys.exit(1)
    
    # Fetch story info for summary
    try:
        work_items_api = WorkItemsAPI(orchestrator.client)
        story_work_item = work_items_api.get_user_story(args.story_id)
        story_fields = work_items_api.get_work_item_fields(story_work_item)
        story_title = story_fields.get(WorkItemsAPI.FIELD_TITLE, "Unknown")
    except Exception as e:
        print(f"Warning: Could not fetch story details: {e}", file=sys.stderr)
        story_title = "Unknown"
    
    print(f"\n{'='*70}")
    print(f"Azure DevOps Test Case Generator")
    print(f"{'='*70}")
    print(f"Story ID: {args.story_id}")
    print(f"Story Title: {story_title}")
    print(f"Test Plan ID: {args.plan_id}")
    print(f"Test Suite ID: {args.suite_id}")
    if args.dry_run:
        print(f"Mode: DRY RUN (no upload)")
    print(f"Generation Mode: {args.mode.upper()}")
    print(f"{'='*70}\n")
    
    # Use hybrid pipeline if mode is hybrid
    if args.mode == "hybrid":
        try:
            pipeline = HybridPipeline()
            if not pipeline.llm_enabled:
                print("Warning: Azure OpenAI not configured. Falling back to rules-only mode.", file=sys.stderr)
                print("Set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT in .env", file=sys.stderr)
            
            result = pipeline.run_hybrid_pipeline(
                story_id=args.story_id,
                plan_id=args.plan_id,
                suite_id=args.suite_id,
                dry_run=args.dry_run
            )
            
            # Print summary
            print(f"\n{'='*70}")
            print(f"Hybrid Pipeline Summary:")
            print(f"{'='*70}")
            print(f"Story ID: {result['story_id']}")
            print(f"Story Title: {story_title}")
            print(f"Baseline Tests: {result['baseline_count']}")
            print(f"LLM Suggested: {result['llm_suggested']}")
            print(f"LLM Accepted: {result['llm_accepted']}")
            print(f"LLM Rejected (Validation): {result['llm_rejected_validation']}")
            print(f"LLM Rejected (Duplicate): {result['llm_rejected_duplicate']}")
            print(f"Total Final Tests: {result['baseline_count'] + result['llm_accepted']}")
            
            if not args.dry_run:
                print(f"\nPublishing Results:")
                print(f"Created: {result['created_count']}")
                print(f"Updated: {result['updated_count']}")
                print(f"Skipped: {result['skipped_count']}")
                print(f"Added to Suite: {result['added_to_suite']}")
            
            if result['errors']:
                print(f"\nErrors ({len(result['errors'])}):")
                for error in result['errors']:
                    print(f"  - {error}")
            else:
                print(f"\nStatus: SUCCESS (no errors)")
            
            print(f"{'='*70}\n")
            
            if result['errors']:
                sys.exit(1)
            
            return
        
        except Exception as e:
            print(f"Error in hybrid pipeline: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    if args.dry_run:
        # Dry run: generate but don't publish
        try:
            story = orchestrator._fetch_story(args.story_id)
            acceptance_criteria = orchestrator._extract_acceptance_criteria(story)
            
            if not acceptance_criteria:
                print(f"Error: No acceptance criteria found for Story {args.story_id}")
                sys.exit(1)
            
            print(f"Found {len(acceptance_criteria)} acceptance criteria\n")
            
            test_cases = orchestrator._generate_test_cases(story, acceptance_criteria)
            
            print(f"Generated {len(test_cases)} test cases:\n")
            for i, tc in enumerate(test_cases, 1):
                print(f"  {i}. {tc.internal_id}: {tc.title}")
                print(f"     Steps: {len(tc.steps)}")
                print(f"     Tags: {', '.join(tc.tags)}")
                print()
            
            print(f"\n{'='*70}")
            print(f"DRY RUN Summary:")
            print(f"  Story ID: {args.story_id}")
            print(f"  Story Title: {story_title}")
            print(f"  AC Count: {len(acceptance_criteria)}")
            print(f"  Generated Test Cases: {len(test_cases)}")
            print(f"  Would Create: {len(test_cases)}")
            print(f"  Would Update: 0")
            print(f"  Would Add to Suite: {len(test_cases)}")
            print(f"{'='*70}\n")
            
        except Exception as e:
            print(f"Error during dry run: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # Actual run: generate and publish
        try:
            result = orchestrator.generate_and_publish(
                story_id=args.story_id,
                plan_id=args.plan_id,
                suite_id=args.suite_id
            )
            
            # Print summary
            print(f"\n{'='*70}")
            print(f"Execution Summary:")
            print(f"{'='*70}")
            print(f"Story ID: {args.story_id}")
            print(f"Story Title: {story_title}")
            print(f"AC Count: {len(orchestrator._extract_acceptance_criteria(orchestrator._fetch_story(args.story_id)))}")
            print(f"Generated Test Cases: {result['created_count'] + result['updated_count'] + result['skipped_count']}")
            print(f"Created: {result['created_count']}")
            print(f"Updated: {result['updated_count']}")
            print(f"Skipped: {result['skipped_count']}")
            print(f"Added to Suite: {len(result['test_case_ids'])}")
            
            if result['errors']:
                print(f"\nErrors ({len(result['errors'])}):")
                for error in result['errors']:
                    print(f"  - {error}")
            else:
                print(f"\nStatus: SUCCESS (no errors)")
            
            print(f"{'='*70}\n")
            
            # Exit with error code if there were errors
            if result['errors']:
                sys.exit(1)
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()

