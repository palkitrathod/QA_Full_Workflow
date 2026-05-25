# 📋 Task Plan — QA Workflow AI Agent

> Master Blueprint for the fully automated QA lifecycle system.

---

## Phase 0: Initialization ✅
- [x] Create `task_plan.md`
- [x] Create `findings.md`
- [x] Create `progress.md`
- [x] Initialize `gemini.md` (Project Constitution)
- [x] Discovery Questions answered by user
- [x] Data Schema defined in `gemini.md`
- [x] Research completed — repos & resources cataloged
- [ ] **Blueprint approved by user** ← CURRENT GATE

---

## Phase 1: Blueprint (Vision & Logic) — IN PROGRESS
- [x] North Star defined: Fully automate QA lifecycle
- [x] Integrations identified (JIRA, GitHub, Slack, Playwright, Anthropic, Allure)
- [x] Source of Truth established (`context.json` shared state)
- [x] Delivery Payload shape confirmed (3 tiers)
- [x] Behavioral Rules documented (Human Review Gate, dedup, severity, retries, etc.)
- [x] JSON Data Schema (Input/Output) locked in `gemini.md`
- [x] Research completed — helpful repos/resources cataloged in `findings.md`
- [ ] Architecture SOPs written in `architecture/`

---

## Phase 2: Link (Connectivity)
- [x] Create `.env.example` with all required variables
- [x] Build `tools/jira_client.py` — JIRA API handshake test
- [x] Build `tools/slack_client.py` — Slack webhook handshake test
- [x] Build `tools/anthropic_client.py` — Claude API handshake test
- [x] Build `tools/github_client.py` — GitHub API handshake test
- [x] Verify all connections pass
- [x] Document API quirks in `findings.md`

---

## Phase 3: Architect (3-Layer Build)

### Layer 1: Architecture SOPs
- [x] `architecture/orchestrator.md` — Pipeline flow, abort conditions, retry logic
- [x] `architecture/requirement_analyser.md` — Input modes, parsing rules, output format
- [x] `architecture/test_case_generator.md` — Generation rules, coverage mapping, regression
- [x] `architecture/script_generator.md` — POM pattern, TypeScript standards, file structure
- [x] `architecture/script_executor.md` — Playwright runner, retry policy, Allure integration
- [x] `architecture/bug_filer.md` — Dedup logic, severity mapping, JIRA ticket format
- [x] `architecture/report_generator.md` — Report template, Slack blocks, JIRA comment

### Layer 3: Tools (Deterministic Scripts)
- [x] `tools/orchestrator.py` — Main pipeline controller
- [x] `tools/context_manager.py` — Read/write `context.json` with validation
- [x] `tools/requirement_analyser.py` — JIRA fetch + document parsing
- [x] `tools/document_parser.py` — PDF/DOCX/MD parsing
- [x] `tools/test_case_generator.py` — AI-powered test case generation
- [x] `tools/script_generator.py` — AI-powered Playwright TS script generation
- [x] `tools/script_executor.py` — Playwright test runner with retries
- [x] `tools/bug_filer.py` — JIRA bug filing with dedup
- [x] `tools/report_generator.py` — Report assembly + Slack delivery
- [x] `tools/slack_notifier.py` — Real-time Slack alerts for P0/P1

---

## Phase 4: Stylize (Refinement & UI)
- [x] Slack Block Kit message templates (alerts + report)
- [x] Allure report configuration and theming
- [x] JIRA ticket templates (bug format, completion comment)
- [x] HTML report template
- [x] User feedback on report format

---

## Phase 5: Trigger (Deployment)
- [ ] CLI entry point (`main.py`)
- [ ] End-to-end test with sample JIRA ticket
- [ ] End-to-end test with sample document
- [ ] GitHub Actions CI/CD pipeline (optional)
- [ ] Maintenance log finalized in `gemini.md`
- [ ] Final documentation
