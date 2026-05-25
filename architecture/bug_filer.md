# Bug Filer SOP (Layer 1)

**Goal:** Analyze failed test scripts, categorize the bug, check for duplicates, file JIRA tickets, and send real-time Slack alerts for critical bugs.

## 1. Input
- Failed scripts from `scripts[]` array in `context.json`.
- Associated test cases from `test_cases[]` array.

## 2. Tool Logic
1. For each failed script, extract the error log and screenshot.
2. Call Claude to analyze the failure and classify it:
   - Determine Severity (P0, P1, P2, P3).
   - Determine Component.
   - Generate Title (`[Component] Action causes unexpected behaviour`).
   - Extract Steps to Reproduce.
3. Call `JiraClient.search_duplicates()` using Component, Error Message, and URL.
4. If a duplicate is found:
   - Call `JiraClient.add_comment()` on the existing ticket.
   - Set `is_duplicate = true` in the bug object.
5. If NO duplicate is found:
   - Call `JiraClient.create_issue()`.
   - Call `JiraClient.link_issues()` to link to the source requirement ticket.
6. If Severity is P0 or P1:
   - Call `SlackNotifier.send_bug_alert()` immediately.

## 3. Claude System Prompt
```text
You are the Bug Classifier for a QA pipeline.
Your task is to analyze a Playwright test failure and generate a structured bug report.

Inputs:
- Test case intent
- Playwright error log

Required Output (JSON):
- title: Format MUST be "[ComponentName] Short factual description of action causing unexpected behaviour"
- severity: "P0" (Crash/Data loss), "P1" (Broken core flow), "P2" (Degraded UX), or "P3" (Cosmetic)
- component: The primary UI or backend component involved
- error_message: A concise summary of the failure reason
- url: The page URL where it failed (if available)
- steps_to_reproduce: Array of strings
- expected_result: String
- actual_result: String
```

## 4. Output
Writes `bugs[]` array to `context.json`.
Updates context `status = "reporting"`.

## 5. Edge Cases
- **Flaky Tests:** If a test fails but Claude determines it's likely a timing issue, log a warning instead of filing a P0.
