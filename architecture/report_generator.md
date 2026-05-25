# Report Generator SOP (Layer 1)

**Goal:** Aggregate pipeline data into a final QA report, deliver to Slack, and post a completion comment to JIRA.

## 1. Input
- The entire `context.json` file.

## 2. Tool Logic
1. Calculate metrics:
   - `total_test_cases`
   - `passed`, `failed`, `skipped`, `error` counts
   - `pass_rate` = `(passed / total) * 100`
   - `coverage_pct` = `(reqs_with_tests / total_reqs) * 100`
   - `bug_summary` = count by severity (P0, P1, P2, P3)
2. Call Claude to write a professional, data-first summary paragraph.
3. Update `report` object in `context.json`.
4. Call `SlackNotifier.send_report()`.
5. Call `JiraClient.add_comment()` on `source_ticket_id` if it exists.
6. (Optional) Call `GithubClient.commit_files()` to save the test scripts to the repository.

## 3. Claude System Prompt
```text
You are the Report Generator for a QA pipeline.
Your task is to write a brief, professional, data-first summary of the QA run.

Inputs:
- Total requirements, total tests, pass rate, bug severity counts.

Rules:
1. Be concise. No filler sentences like "Here is the report."
2. Focus on the impact. If there are P0/P1 bugs, state that the build is unstable.
3. If pass rate > 90% and no P0/P1 bugs, state the build is stable.
```

## 4. Output
Updates `report` object in `context.json`.
Updates context `status = "completed"`.

## 5. Edge Cases
- **Slack API Down:** Log error locally but mark run as completed.
- **Empty Run:** If no tests were run, ensure the report clearly states why (e.g., "Aborted" or "No requirements parsed").
