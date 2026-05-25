# Script Executor SOP (Layer 1)

**Goal:** Execute Playwright scripts locally, capture results and artifacts (screenshots/traces), and handle environmental retries.

## 1. Input
- Playwright `.spec.ts` files in `tests/specs/`.
- `scripts[]` array in `context.json` (where status is `"approved"` or `run_type` is `"regression"`).

## 2. Tool Logic
1. Filter scripts in `context.json` that are ready to run.
2. If none are ready, transition to next phase.
3. Run `npm run test`.
4. Parse the Playwright JSON or JUnit reporter output to determine pass/fail for each script.
5. If a script fails due to environment/tooling errors (e.g., timeout before page load, browser crash), retry up to 3 times per gemini.md Rule 2.4.
6. If a script fails due to assertion failure (test logic), mark as `"failed"` without retries.
7. Collect paths to failure screenshots/traces.
8. Generate Allure report using `npm run allure:generate`.

## 3. Output
Updates `scripts[]` array in `context.json` with status (`"passed"`, `"failed"`, `"error"`), error logs, and screenshot paths.
Updates context `status = "filing_bugs"`.

## 4. Edge Cases
- **Crash Threshold:** If >50% of scripts fail with `"error"` status (tooling crash), trigger Orchestrator Abort Condition #3.
