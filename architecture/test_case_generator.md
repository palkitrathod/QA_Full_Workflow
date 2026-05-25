# Test Case Generator SOP (Layer 1)

**Goal:** Generate comprehensive test cases (positive, negative, edge cases) based on parsed requirements.

## 1. Input
- `requirements[]` array from `context.json`.

## 2. Tool Logic
1. Read requirements.
2. If `run_type == "regression"`, check if there are filed bugs from previous runs (in practice, regression cases are generated based on a specific prompt or linked bugs).
3. Send requirements to Claude to generate detailed step-by-step test cases.
4. Calculate coverage mapping (ensure every requirement has at least one test case).

## 3. Claude System Prompt
```text
You are the Test Case Generator for an automated QA pipeline.
Your task is to take a list of requirements and generate explicit, step-by-step test cases.

For each requirement, aim to create:
1. A Positive path test case
2. A Negative path test case
3. Any relevant Edge cases

Each test case must include:
- id: Unique identifier (e.g., TC-001)
- requirement_id: The ID of the requirement it covers
- title: Descriptive test title
- type: 'positive', 'negative', 'edge_case', or 'regression'
- preconditions: List of setup steps needed
- steps: Array of objects {step_number, action, expected_result}
- priority: Inherit from requirement or assess independently

Ensure steps are atomic and actionable.
```

## 4. Output
Writes a `test_cases[]` array to `context.json`.
Updates context `status = "generating_scripts"`.

## 5. Edge Cases
- **Missing Coverage:** If a requirement has no associated test case, append a warning to the run report.
- **Overgeneration:** Limit to max 20 test cases per run to prevent excessive script generation time, unless `run_type` dictates otherwise.
