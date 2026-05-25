# Orchestrator SOP (Layer 1)

**Goal:** Control the sequential execution of the QA Workflow AI Agent pipeline, manage state transitions, enforce abort conditions, and handle error recovery.

## 1. Input
- Command line arguments from `main.py`
  - `--jira PROJ-123` or `--document path/to/doc`
  - `--regression` (optional flag to skip human review)
  - `--dry-run` (optional flag)

## 2. Shared State (`context.json`)
The Orchestrator initializes `.tmp/context.json` and updates the `status` field as the pipeline progresses.

**Status States:**
`initializing` → `analysing` → `generating_cases` → `generating_scripts` → `awaiting_review` → `executing` → `filing_bugs` → `reporting` → `completed` (or `aborted`)

## 3. Pipeline Flow (Deterministic Rules)

1. **Initialization:** Validate inputs, create run ID, initialize context.
2. **Analysis:** Call `RequirementAnalyser`.
3. **Generation:** Call `TestCaseGenerator`, then `ScriptGenerator`.
4. **Human Review Gate:** 
   - If `run_type == "new_feature"`: Pause execution, send Slack notification, prompt CLI for `Approve (Y/N)`.
   - If `run_type == "regression"`: Auto-skip this step.
5. **Execution:** Call `ScriptExecutor`.
6. **Filing:** Call `BugFiler`.
7. **Reporting:** Call `ReportGenerator`.

## 4. Abort Conditions & Error Escalation

The pipeline **MUST ABORT** immediately if any of these conditions are met:
1. **Empty Requirements:** Requirement Analyser returns 0 requirements or unparseable content.
2. **JIRA Unreachable:** Link phase verification fails at the start of the run.
3. **Execution Crash Threshold:** >50% of scripts fail due to execution crashes (tooling errors, not test logic).

**Abort Protocol:**
- Set context `status = "aborted"`.
- Log the specific reason to `progress.md`.
- Send a `send_abort_notification()` to Slack.
- Exit process with code 1.

## 5. Retry Policy
- **Agent API Calls (Claude):** Up to 3 retries with exponential backoff on `RateLimitError` or `APIConnectionError`.
- **Script Execution:** Up to 3 retries for tooling/environment errors. Handled by Playwright configuration.
