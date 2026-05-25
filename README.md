# QA Workflow AI Agent

An end-to-end automated QA pipeline that takes a JIRA ticket or PRD/BRD document as input, generates test cases, creates and executes Playwright scripts, files bugs in JIRA, and delivers a QA report to Slack.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py (CLI Entry)                      │
│  python main.py --jira SCRUM-38 --regression                    │
│  python main.py --document path/to/prd.pdf                      │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Orchestrator (Pipeline Controller)              │
│  - Initializes context in .tmp/context.json                      │
│  - Runs 7 steps sequentially with abort/resume support           │
│  - Human review gate for new features                            │
└──┬───┬───┬───┬───┬───┬───┬──────────────────────────────────────┘
   │   │   │   │   │   │   │
   ▼   ▼   ▼   ▼   ▼   ▼   ▼
┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐
│1 │ │2 │ │3 │ │4 │ │5 │ │6 │ │7 │
│  │ │  │ │  │ │  │ │  │ │  │ │  │
│Re-│ │Test│ │Scr│ │Scr│ │Bug│ │Re-│
│q  │ │Case│ │ipt│ │ipt│ │Fi-│ │p- │
│An-│ │Gen-│ │Ge-│ │Ex-│ │ler│ │ort│
│aly-│ │erat│ │ner│ │ecu│ │   │ │Ge-│
│ser│ │or  │ │ato│ │tor│ │   │ │ner│
│   │ │    │ │r  │ │   │ │   │ │at-│
│   │ │    │ │   │ │   │ │   │ │or │
└──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘
  │    │     │     │     │     │    │
  │    │     │     │     │     │    └──► Slack + JIRA Report
  │    │     │     │     │     │
  │    │     │     │     │     └────────► Allure Report
  │    │     │     │     │
  │    │     │     │     └──────────────► JIRA Bug Tickets
  │    │     │     │
  │    │     │     └────────────────────► playwright-results.json
  │    │     │
  │    │     └──────────────────────────► tests/pages/ + tests/specs/
  │    │
  │    └────────────────────────────────► generated_test_cases.md
  │
  └─────────────────────────────────────► context.json (requirements)
```

## Features

- **Dual Input Mode:** JIRA ticket (`--jira`) or document (`--document`)
- **LLM-Powered:** Uses any OpenAI-compatible API (OpenAI, OpenRouter, Groq, Deepseek)
- **Automated Test Generation:** Generates functional test cases from requirements
- **Playwright Page Object Model:** Auto-generates page objects and spec files
- **Test Execution:** Runs Playwright tests with Allure reporting
- **Automated Bug Filing:** Files bugs in JIRA for failed tests with deduplication
- **Slack Integration:** Sends alerts, reports, and abort notifications (optional)

## Prerequisites

- Python 3.14+
- Node.js 18+
- A JIRA account (Cloud or Server)
- An LLM API key (OpenAI, OpenRouter, Groq, or Anthropic-compatible)

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/palkitrathod/QA_Full_Workflow.git
cd QA_Full_Workflow

# Python dependencies
pip install -r requirements.txt

# Node.js dependencies
npm install

# Install Playwright browsers
npx playwright install chromium
```

### 2. Configure Environment

Copy `.env` and fill in your credentials:

| Variable | Description |
|---|---|
| `JIRA_BASE_URL` | Your JIRA instance URL |
| `JIRA_EMAIL` | Your JIRA email |
| `JIRA_API_TOKEN` | JIRA API token |
| `JIRA_PROJECT_KEY` | JIRA project key (e.g., SCRUM) |
| `LLM_API_KEY` | OpenAI/OpenRouter/Groq API key |
| `LLM_BASE_URL` | API base URL |
| `LLM_MODEL` | Model name (e.g., openai/gpt-4o-mini) |
| `SLACK_WEBHOOK_URL` | (Optional) Slack webhook |
| `TARGET_APP_URL` | Application URL under test |
| `USERNAME` / `PASSWORD` | Test credentials |

### 3. Run the Pipeline

```bash
# From a JIRA ticket (regression mode — skips human review)
python main.py --jira SCRUM-38 --regression

# From a document (new feature — pauses for human review)
python main.py --document path/to/prd.pdf

# Dry run (stops before test execution)
python main.py --jira SCRUM-38 --dry-run
```

## Pipeline Steps

| Step | Component | Description |
|---|---|---|
| 1 | `RequirementAnalyser` | Extracts requirements from JIRA ticket or document |
| 2 | `TestCaseGenerator` | Generates functional test cases using LLM |
| 3 | `ScriptGenerator` | Creates Playwright Page Objects and spec files |
| — | *Human Review Gate* | Pauses for approval (new feature mode only) |
| 4 | `ScriptExecutor` | Runs Playwright tests, generates Allure report |
| 5 | `BugFiler` | Files bugs in JIRA for failed tests |
| 6 | `ReportGenerator` | Delivers QA report to Slack and JIRA |

## Project Structure

```
├── main.py                         # CLI entry point
├── .env                            # Environment variables
├── generated_test_cases.md         # Latest generated test cases
├── playwright-results.json         # Test execution results
│
├── architecture/                   # LLM SOPs
│   ├── orchestrator.md
│   ├── requirement_analyser.md
│   ├── test_case_generator.md
│   ├── script_generator.md
│   ├── script_executor.md
│   ├── bug_filer.md
│   └── report_generator.md
│
├── tools/                          # Core pipeline tools
│   ├── orchestrator.py             # Pipeline controller
│   ├── context_manager.py          # .tmp/context.json I/O
│   ├── requirement_analyser.py     # Step 1
│   ├── test_case_generator.py      # Step 2
│   ├── script_generator.py         # Step 3
│   ├── script_executor.py          # Step 4
│   ├── bug_filer.py                # Step 5
│   ├── report_generator.py         # Step 6
│   ├── jira_client.py              # JIRA API wrapper
│   ├── slack_notifier.py           # Slack webhook wrapper
│   ├── llm_client.py               # Universal LLM client
│   ├── github_client.py            # GitHub API wrapper
│   └── document_parser.py          # PDF/DOCX parser
│
├── tests/                          # Generated Playwright tests
│   ├── pages/                      # Page Object classes
│   └── specs/                      # Test spec files
│
├── allure-results/                 # Allure raw results
├── allure-report/                  # Allure HTML report
├── playwright-report/              # Playwright HTML report
├── test-results/                   # Test artifacts
└── .tmp/
    └── context.json                # Pipeline state
```

## Configured Target Application

- **URL:** https://www.saucedemo.com/
- **Test Users:** `standard_user` / `secret_sauce`
- **Locator Strategy:** `[data-test="..."]` attributes

## Key Design Decisions

- **LLM-Agnostic:** Works with any OpenAI-compatible API via `LLM_BASE_URL`
- **JSON Mode:** Uses OpenAI JSON mode where available; falls back to prompt-based JSON for broader model compatibility
- **Atomic Context:** Pipeline state stored in `.tmp/context.json` with typed access methods
- **Optional Integrations:** Slack and GitHub are fully optional — pipeline runs without them
- **Single Browser:** Configured for Chromium only with 1 worker for reliability on Windows

## Generated Bugs (Sample)

| JIRA Key | Test Case | Status |
|---|---|---|
| SCRUM-39 | TC-001: Verify presence of Login Page elements | Fixed |
| SCRUM-40 | TC-003: Validate Username field with valid input | Fixed |
| SCRUM-41 | TC-004: Validate Username field with empty input | Fixed |
| SCRUM-42 | TC-005: Validate Password field with valid input | Fixed |
| SCRUM-43 | TC-006: Validate Password field with empty input | Fixed |
| SCRUM-44 | TC-007: Test Login button with valid credentials | Fixed |
| SCRUM-45 | TC-008: Verify successful login | Fixed |
| SCRUM-46 | TC-009: Error messages for invalid username | Fixed |
| SCRUM-47 | TC-010: Error messages for invalid password | Fixed |
| SCRUM-48 | TC-011: Session management after page refresh | Fixed |
| SCRUM-49 | TC-012: Access restriction for locked users | Fixed |
| SCRUM-50 | TC-014: Cross-browser compatibility | Fixed |

## Troubleshooting

**LLM JSON parsing errors:** If the model doesn't support `response_format`, the client strips markdown fences and retries. Switch to a model with better JSON support (e.g., `openai/gpt-4o-mini`).

**Playwright timeouts:** Ensure locators match the target app. For SauceDemo, use `[data-test="..."]` selectors.

**Rate limiting:** Groq free tier is 100K tokens/day. Use OpenRouter or a paid OpenAI key for larger workloads.
