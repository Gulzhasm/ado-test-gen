# Evaluation Methodology for ADO Test Case Generation System

## Overview

This document describes the evaluation methodology for assessing the effectiveness of the Azure DevOps (ADO) test case generation system. The evaluation compares three approaches: baseline rules-only, NLP-enhanced (spaCy), and hybrid (rules + LLM edge-case suggestions).

## Research Objectives

1. **Coverage**: Percentage of acceptance criteria covered by generated test cases
2. **Correctness**: Accuracy of generated test cases (actionable, complete, accurate)
3. **Duplication**: Rate of duplicate test cases generated
4. **Determinism**: Consistency of output for identical inputs
5. **Human Review Score**: Quality assessment by domain experts
6. **Time Saved**: Reduction in manual test case creation time
7. **Cost**: Computational and API costs for generation
8. **Defect Yield**: Number of defects found by generated test cases

## Evaluation Approaches

### 1. Baseline Rules-Only

**Description**: Pure rule-based system using keyword matching, template selection, and deterministic generation.

**Characteristics**:
- No external dependencies (no NLP libraries, no LLM APIs)
- Fast execution (< 1 second per story)
- Fully deterministic
- Zero API costs
- Limited semantic understanding

**Implementation**:
- Keyword-based AC classification
- Template matching by category
- Rule-based title generation (no raw AC text)
- Fixed step templates

### 2. NLP-Enhanced (spaCy)

**Description**: Rule-based system enhanced with spaCy for sentence splitting and classification.

**Characteristics**:
- Lightweight NLP processing
- Better sentence boundary detection
- Improved AC splitting for complex text
- Slightly slower execution (1-2 seconds per story)
- Minimal cost (local processing)
- Better handling of complex AC structures

**Implementation**:
- spaCy sentence tokenization for AC splitting
- Enhanced keyword matching with POS tagging
- Improved noun phrase extraction for short descriptors
- Template matching remains rule-based

### 3. Hybrid (Rules + LLM Edge-Case Suggestions)

**Description**: Rule-based generation with LLM suggestions for edge cases and additional test scenarios.

**Characteristics**:
- LLM API calls for edge case generation only
- Titles and primary steps remain rule-based
- LLM suggests additional negative/boundary tests
- Higher cost (API calls per story)
- Slower execution (5-10 seconds per story)
- Better edge case coverage

**Implementation**:
- Primary test cases: rule-based (deterministic)
- Edge case suggestions: LLM API (OpenAI GPT-4 or similar)
- Human review of LLM suggestions before inclusion
- Cost tracking per story

## Metrics Definition

### 1. Coverage

**Formula**: `Coverage = (ACs with at least one test case) / (Total ACs) × 100%`

**Measurement**:
- Count ACs with generated test cases
- Identify ACs without coverage
- Categorize by AC type (simple, complex, ambiguous)

**Target**: ≥ 95% coverage

### 2. Correctness

**Formula**: `Correctness = (Valid test cases) / (Total generated test cases) × 100%`

**Criteria for Valid Test Case**:
- Actionable: Steps can be executed by a tester
- Complete: All required steps present (including close step)
- Accurate: Steps match AC intent
- Properly formatted: Valid XML, correct title format

**Measurement**:
- Manual review by 2+ domain experts
- Automated validation (XML structure, title format, step count)
- Inter-rater agreement calculation

**Target**: ≥ 90% correctness

### 3. Duplication

**Formula**: `Duplication Rate = (Duplicate test cases) / (Total test cases) × 100%`

**Definition of Duplicate**:
- Same AC hash
- Identical steps (after normalization)
- Same title (excluding internal ID)

**Measurement**:
- Automated duplicate detection
- Manual verification of false positives

**Target**: ≤ 5% duplication

### 4. Determinism

**Formula**: `Determinism = (Consistent outputs) / (Total runs) × 100%`

**Measurement**:
- Run same story 10 times
- Compare outputs (titles, steps, IDs)
- Check for identical outputs

**Target**: 100% determinism for rules-only and NLP-enhanced; ≥ 80% for hybrid (LLM introduces non-determinism)

### 5. Human Review Score

**Scale**: 1-5 (1 = Poor, 5 = Excellent)

**Criteria**:
- **Relevance**: Test case addresses the AC
- **Clarity**: Steps are clear and unambiguous
- **Completeness**: All necessary steps included
- **Actionability**: Steps can be executed
- **Professional Quality**: Meets senior SDET standards

**Measurement**:
- 3 domain experts review 50 randomly selected test cases
- Average score per test case
- Inter-rater agreement (Cohen's Kappa)

**Target**: ≥ 4.0 average score

### 6. Time Saved

**Formula**: `Time Saved = (Manual creation time - Generation time) / Manual creation time × 100%`

**Measurement**:
- Baseline: Manual creation time for 10 stories (measured)
- Generation time: Automated generation time (measured)
- Review time: Time to review and approve generated tests (measured)

**Target**: ≥ 70% time reduction

### 7. Cost

**Metrics**:
- **Rules-only**: $0 (local processing)
- **NLP-enhanced**: $0 (local processing, spaCy model download one-time)
- **Hybrid**: API cost per story (tracked)

**Measurement**:
- Track API calls and tokens used
- Calculate cost per story
- Project annual cost for 1000 stories

**Target**: Hybrid cost < $0.50 per story

### 8. Defect Yield

**Formula**: `Defect Yield = (Defects found by generated tests) / (Total defects found) × 100%`

**Measurement**:
- Track defects found during test execution
- Categorize by test case source (generated vs. manual)
- Compare defect detection rates

**Target**: Generated tests find ≥ 80% of defects found by manual tests

## Experiment Plan

### Dataset Selection

**Criteria**:
- 50 User Stories from real ADO projects
- Mix of complexity levels:
  - 20 simple (1-3 ACs, clear requirements)
  - 20 medium (4-6 ACs, some ambiguity)
  - 10 complex (7+ ACs, multiple dependencies)
- Diverse categories (Availability, Logging, Ordering, Limits, etc.)
- Representative of production workload

**Selection Process**:
1. Query ADO for stories with ACs
2. Filter by date (last 6 months)
3. Random sample stratified by complexity
4. Anonymize if needed

### Annotation Protocol

**Phase 1: AC Annotation**
- Label each AC with:
  - Category (ground truth)
  - Complexity (simple/medium/complex)
  - Ambiguity level (low/medium/high)
  - Expected test count

**Phase 2: Test Case Annotation**
- For each generated test case:
  - Valid/Invalid (with reason)
  - Relevance score (1-5)
  - Completeness score (1-5)
  - Actionability score (1-5)
  - Duplicate flag (if applicable)

**Phase 3: Execution Results**
- Track test execution results
- Record defects found
- Note false positives/negatives

### Inter-Rater Agreement

**Protocol**:
- 3 annotators independently review same test cases
- Calculate Cohen's Kappa for:
  - Category classification
  - Valid/Invalid judgment
  - Quality scores (after normalization)

**Target**: Kappa ≥ 0.7 (substantial agreement)

### Statistical Tests

**Hypotheses**:
1. **H1**: NLP-enhanced has higher coverage than rules-only
2. **H2**: Hybrid has higher edge case coverage than rules-only
3. **H3**: Rules-only has higher determinism than hybrid
4. **H4**: All approaches have correctness ≥ 90%

**Tests**:
- **Coverage**: Chi-square test for proportions
- **Correctness**: One-way ANOVA (if normally distributed) or Kruskal-Wallis
- **Time Saved**: Paired t-test (manual vs. generated)
- **Human Review Score**: One-way ANOVA with post-hoc tests

**Significance Level**: α = 0.05

## Implementation Details

### Data Collection

**Tools**:
- ADO REST API for story retrieval
- Automated test case generation scripts
- Manual annotation interface (web form or spreadsheet)
- Test execution tracking (ADO Test Plans)

**Timeline**:
- Week 1-2: Dataset selection and AC annotation
- Week 3-4: Test case generation (all three approaches)
- Week 5-6: Test case annotation
- Week 7-8: Test execution and defect tracking
- Week 9-10: Analysis and reporting

### Reporting

**Deliverables**:
1. **Quantitative Report**: Metrics comparison table
2. **Qualitative Analysis**: Common issues, strengths, weaknesses
3. **Cost-Benefit Analysis**: ROI calculation
4. **Recommendations**: Best approach for different scenarios

**Format**: Academic paper format suitable for Master's dissertation

## Limitations

1. **Dataset Size**: 50 stories may not represent all edge cases
2. **Domain Specificity**: Results may vary for different application domains
3. **Human Bias**: Reviewer scores may be subjective
4. **Temporal Effects**: AC quality may improve over time, affecting results

## Future Work

1. **Larger Dataset**: Expand to 200+ stories
2. **Cross-Domain Validation**: Test on different application types
3. **Longitudinal Study**: Track quality over 6+ months
4. **ML Integration**: Train custom models for AC classification
5. **Automated Quality Metrics**: Develop automated correctness scoring

