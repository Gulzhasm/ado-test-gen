# Azure DevOps Test Case Generator

An AI-driven, fully automated Azure DevOps (ADO) Test Case generation system in Python, designed for Master's dissertation research and production use.

## Overview

This system automatically retrieves User Stories from Azure DevOps, parses their Description and Acceptance Criteria, and creates comprehensive Test Case work items directly via REST APIs. The solution follows strict naming conventions, implements comprehensive QA coverage rules, and is designed for research extensibility.

## Features

- ✅ **Full ADO Integration**: Authenticates via PAT, retrieves User Stories, creates/updates Test Cases
- ✅ **HTML Parsing**: Converts ADO HTML content to clean, structured text
- ✅ **Acceptance Criteria Extraction**: Handles dedicated fields and embedded AC sections
- ✅ **Comprehensive Test Coverage**: Generates happy path, negative, boundary, cancel/rollback, persistence, undo/redo, and accessibility test scenarios
- ✅ **Strict Naming Conventions**: Follows mandatory ID and title format rules
- ✅ **Idempotency**: Safe to re-run; detects and updates existing test cases
- ✅ **Test Plan Integration**: Automatically adds test cases to specified Test Plans and Test Suites
- ✅ **XML Test Steps**: Generates proper ADO Test Case XML format
- ✅ **Modular Architecture**: Clean separation of concerns, ML-ready design
- ✅ **Production-Ready**: Robust error handling, retry logic, timeout management

## Architecture

```
src/
 ├── config/
 │   └── settings.py          # Configuration management
 ├── ado/
 │   ├── client.py            # ADO REST API client
 │   ├── auth.py              # PAT authentication
 │   ├── work_items.py        # Work Items API operations
 │   └── test_plans.py        # Test Plans & Suites API
 ├── parsing/
 │   ├── html_parser.py       # HTML to text conversion
 │   └── ac_extractor.py     # Acceptance Criteria extraction
 ├── generation/
 │   ├── naming.py            # Test case naming conventions
 │   ├── test_case_builder.py # Test case generation logic
 │   └── steps_xml.py         # XML steps generator
 ├── models/
 │   ├── story.py             # User Story Pydantic model
 │   ├── acceptance_criteria.py # AC Pydantic model
 │   └── test_case.py         # Test Case Pydantic model
 ├── orchestration/
 │   └── generate_and_publish.py # End-to-end workflow
 ├── cli.py                   # Command-line interface
 └── main.py                  # Entry point
```

## Installation

1. **Clone the repository** (or ensure you're in the project directory)

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   
   Create a `.env` file in the project root:
   ```env
   ADO_ORG=your-organization
   ADO_PROJECT=your-project
   ADO_PAT=your-personal-access-token
   ```
   
   Or set environment variables:
   ```bash
   export ADO_ORG=your-organization
   export ADO_PROJECT=your-project
   export ADO_PAT=your-personal-access-token
   ```

## Usage

### Command-Line Interface

Generate test cases from a User Story:

```bash
python -m src.cli --story-id 271309 --plan-id 123 --suite-id 456
```

With verbose output:

```bash
python -m src.cli --story-id 271309 --plan-id 123 --suite-id 456 --verbose
```

### Programmatic Usage

```python
from src.orchestration.generate_and_publish import TestCaseOrchestrator

orchestrator = TestCaseOrchestrator()
result = orchestrator.generate_and_publish(
    story_id=271309,
    plan_id=123,
    suite_id=456
)

print(f"Created: {result['created_count']}")
print(f"Updated: {result['updated_count']}")
print(f"Errors: {result['errors']}")
```

## Test Case Naming Conventions

### Internal IDs

- **First test case**: `{StoryID}-AC1` (e.g., `271309-AC1`)
- **Subsequent test cases**: Increment by 5 to reserve gaps
  - `{StoryID}-005`
  - `{StoryID}-010`
  - `{StoryID}-015`
  - etc.

### Title Format

```
{InternalID}: <Feature> / <Module> / <Category> / <SubCategory> / <Description>
```

Example:
```
271309-AC1: User Management / Authentication / Login / Happy Path / Verify user can login with valid credentials
```

## Test Coverage

For each Acceptance Criterion, the system generates:

1. **Happy Path**: Standard successful scenario
2. **Negative**: Invalid input handling
3. **Boundary**: Edge cases and limits
4. **Cancel/Rollback**: Cancellation behavior
5. **Persistence**: Save/reopen verification
6. **Undo/Redo**: Undo/redo functionality (if applicable)
7. **Accessibility**: Keyboard navigation, focus indicators, WCAG 2.1 AA compliance

Plus one **Umbrella Test Case** verifying all AC coverage for sign-off.

## Test Steps Format

All test cases include:
- Multiple action/expected result steps
- Mandatory final step:
  - **Action**: "Close/Exit the application."
  - **Expected**: "Application closes successfully without crash or freeze; no error dialogs are shown."

Steps are formatted as XML using `Microsoft.VSTS.TCM.Steps` format required by ADO.

## Idempotency

The system is safe to re-run:

- Detects existing test cases using tags: `story:{ID}`, `generated-by:ai-testgen`
- Falls back to title prefix matching if tags unavailable
- Updates existing test cases instead of creating duplicates
- Skips test cases that haven't changed

## Research Extensibility

The architecture is designed for ML integration:

- **Clear separation** between rule-based and AI-assisted logic
- **Marked integration points** for:
  - Requirement parsing enhancement
  - Failure classification
  - Locator healing
  - Test scenario generation
  - Feature/module extraction

## Requirements

- Python 3.10+
- Azure DevOps account with PAT (Personal Access Token)
- Test Plan and Test Suite IDs in your ADO project

## Error Handling

The system includes:
- Automatic retries on transient failures (5xx errors)
- Timeout management (30 seconds default)
- Comprehensive error reporting
- Graceful degradation

## Limitations

- Currently uses rule-based test case generation (ML integration points marked for future work)
- Feature/module extraction is keyword-based (can be enhanced with ML)
- Test steps are template-based (can be enhanced with natural language generation)

## Contributing

This is a research project designed for Master's dissertation work. The codebase is structured to support:
- Academic research on AI-driven test generation
- Production deployment
- Extension with ML models

## License

[Specify your license here]

## Author

[Your name/institution]

---

**Note**: This system does NOT use CSV files. All test cases are created/updated directly via Azure DevOps REST APIs.
