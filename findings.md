# 🔍 Findings

> Research, discoveries, constraints, and external resources collected during the project.

---

## Discovery Notes (from User Responses)

### North Star
- **Goal:** Fully automate the QA lifecycle end-to-end.
- **Input:** JIRA ticket ID or PRD/BRD document.
- **Output:** Test cases generated → Playwright scripts created & executed → Bugs filed in JIRA → QA report to Slack.
- **Completion criteria:** Bugs are filed in JIRA AND report is delivered to Slack.
- **Human Review Gate:** Mandatory for new features (scripts must be approved before execution). Auto-skipped for regression.

### Five AI Agents (all Claude Sonnet via Anthropic API)
1. **Requirement Analyser** — Extracts requirements from JIRA ticket or PRD/BRD doc
2. **Test Case Generator** — Generates test cases from parsed requirements
3. **Script Generator** — Creates Playwright TypeScript scripts (Page Object Model)
4. **Bug Filer** — Files bugs in JIRA with deduplication
5. **Report Generator** — Produces QA report, delivers to Slack

### Integrations Required
| Service | Purpose | Auth Type |
|---------|---------|-----------|
| JIRA REST API | Fetch tickets (input) + File bugs (output) | Basic Auth (email + API token) |
| GitHub | Store/version Playwright test scripts | Personal Access Token |
| Playwright + Node.js + TS | Script execution engine (local) | N/A (local install) |
| Slack (Webhook/Bot) | QA report delivery + real-time P0/P1 alerts | Webhook URL or Bot Token |
| Anthropic API | Powers all 5 AI agents (claude-sonnet-4) | API Key |
| Google Drive (optional) | PRD/BRD document source | Service Account or OAuth |
| Allure Reporter (npm) | Visual HTML test report generation | N/A (local install) |

### Input Modes
- **Mode A:** JIRA ticket ID (e.g., `PROJ-123`) → fetch via JIRA REST API
- **Mode B:** PRD/BRD document (PDF, DOCX, Markdown) → direct file parse

### Shared Context Store (`context.json` in `.tmp/`)
All 5 agents read/write to this shared state file. Fields:
- `requirements[]` — Parsed requirements
- `test_cases[]` — Generated test cases
- `scripts[]` — Each has `file_path` and `status` (pending|approved|executed|failed)
- `bugs[]` — Each has `severity` and `jira_ticket_id`
- `report{}` — `coverage_pct`, `pass_rate`, `summary`

### Delivery Tiers
1. **Real-time Slack alerts** — P0/P1 bugs posted immediately with title, severity, steps, JIRA link
2. **Final QA report** — Total tests, pass/fail/skip, coverage %, bug summary, screenshots, Allure link
3. **JIRA updates** — Bug tickets filed + source ticket gets completion comment

### Behavioral Rules
- Human Review Gate mandatory for new features; auto-skip for regression
- Duplicate bug check: match on component + error message + URL
- Severity mapping: P0=crash/data-loss, P1=broken-core-flow, P2=degraded-UX, P3=cosmetic
- Max retry = 3 for execution errors (not test logic failures)
- Regression feedback loop: every filed bug → auto-generates regression test
- Playwright scripts: TypeScript + Page Object Model (mandatory)
- No hardcoded credentials
- Orchestrator abort conditions: empty requirements, JIRA unreachable, >50% execution crashes
- Bug title format: `[ComponentName] Action causes unexpected behaviour`
- Slack emojis: 🔴 P0, 🟠 P1, 🟡 P2, 🔵 P3
- Report language: professional, data-first, no filler

---

## External Resources (Research)

### Reference GitHub Repos
1. **[huangmingxia/test-generation-assistant](https://github.com/huangmingxia/test-generation-assistant)** — AI-assisted system: generates test cases from JIRA, creates E2E test code, executes tests, submits PRs, updates JIRA. Uses Claude/Cursor/Gemini agents with MCP.
2. **[dogkeeper886/ai-qa-workflow](https://github.com/dogkeeper886/ai-qa-workflow)** — MCP-based toolkit connecting AI agents with test management. Full lifecycle from JIRA requirements to Playwright execution. Has "dual-judge" quality verification.
3. **[skc147283/smarttestgen](https://github.com/skc147283/smarttestgen)** — Parses markdown requirements, uses LLMs to generate JUnit tests, integrates with Jira/Xray.

### Playwright Page Object Model Best Practices
- Folder structure: `tests/` (specs), `pages/` (page objects), `components/` (reusable UI), `fixtures/`, `utils/`
- Use getter methods for lazy locator evaluation
- Prefer role-based locators (`getByRole`, `getByText`)
- Keep actions atomic; keep assertions in test files
- Use Playwright fixtures for dependency injection
- Break large page objects into components (<50 methods per class)

### Allure Reporter Setup
- Install: `npm install -D allure-playwright allure-commandline`
- Config in `playwright.config.ts`: add `['allure-playwright', { resultsDir: 'allure-results' }]` to reporter array
- Generate report: `npx allure generate allure-results -o allure-report --clean`
- **Requires Java** installed on the system

### Claude Multi-Agent Architecture
- **Supervisor pattern** is ideal for our use case — central Orchestrator delegates to specialized sub-agents
- Each agent should have its own write domain (we use `context.json` with structured fields)
- Prefer workflows over implicit reasoning — codify orchestration in Python
- Implement heartbeat/watchdog timers for each agent
- Budget gates before expensive API calls
- Structured logging for decision traceability

### JIRA API (Python `jira` library)
- `jira.search_issues(jql)` for duplicate detection
- `jira.create_issue()` for bug filing
- `jira.create_issue_link()` for linking bugs to source tickets
- `jira.add_comment()` for posting QA completion summary
- Use JQL with component, summary, and description fields for duplicate matching

### Slack API
- Incoming Webhooks for simple message posting
- Block Kit for rich formatting (sections, dividers, context blocks)
- Use `slack_sdk.webhook.WebhookClient` for Python integration
- Block Kit Builder available at app.slack.com/block-kit-builder

---

## Constraints & Gotchas
- Allure report generation requires **Java** installed on the system
- JIRA Cloud rate limits apply — need to handle 429 responses
- Playwright scripts must be TypeScript — no JS fallback
- PDF/DOCX parsing will need additional Python libraries (`PyPDF2`/`pdfplumber`, `python-docx`)
- `context.json` is single-file shared state — agents must not write concurrently (sequential pipeline mitigates this)
- GitHub commits from automation should use a dedicated bot account or PAT
- Slack webhook URLs are channel-specific — need separate webhooks for alerts vs. reports or use Bot Token with `chat.postMessage`
