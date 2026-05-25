# 📜 gemini.md — Project Constitution

> This file is **law**. It defines data schemas, behavioral rules, and architectural invariants for the QA Workflow AI Agent.

---

## 1. Data Schemas

### 1.1 Pipeline Input Schema

```json
{
  "run_id": "string (UUID, auto-generated)",
  "timestamp": "string (ISO 8601)",
  "input_mode": "jira | document",
  "run_type": "new_feature | regression",
  "jira": {
    "ticket_id": "string (e.g., PROJ-123)",
    "base_url": "string (e.g., https://company.atlassian.net)"
  },
  "document": {
    "file_path": "string (path to PDF, DOCX, or MD file)",
    "file_type": "pdf | docx | markdown"
  },
  "config": {
    "target_app_url": "string (URL of the application under test)",
    "project_key": "string (JIRA project key for bug filing)",
    "slack_channel": "string (channel for report delivery)",
    "human_review_required": "boolean (auto-set based on run_type)"
  }
}
```

### 1.2 Shared Context Store (`context.json`)

This is the single source of truth for inter-agent communication. Located in `.tmp/context.json`.

```json
{
  "run_id": "string (UUID)",
  "status": "initializing | analysing | generating_cases | generating_scripts | awaiting_review | executing | filing_bugs | reporting | completed | aborted",
  "input_mode": "jira | document",
  "run_type": "new_feature | regression",
  "source_ticket_id": "string | null",
  "target_app_url": "string | null (Extracted dynamically from source)",
  "requirements": [
    {
      "id": "REQ-001",
      "title": "string",
      "description": "string",
      "acceptance_criteria": ["string"],
      "priority": "P0 | P1 | P2 | P3",
      "source": "string (ticket ID or document section)"
    }
  ],
  "test_cases": [
    {
      "id": "TC-001",
      "requirement_id": "REQ-001",
      "title": "string",
      "type": "positive | negative | edge_case | regression",
      "preconditions": ["string"],
      "steps": [
        {
          "step_number": 1,
          "action": "string",
          "expected_result": "string"
        }
      ],
      "priority": "P0 | P1 | P2 | P3"
    }
  ],
  "scripts": [
    {
      "id": "SCR-001",
      "test_case_id": "TC-001",
      "file_path": "string (relative path in /tests/)",
      "page_objects": ["string (page object file paths)"],
      "status": "pending | approved | executing | passed | failed | error | skipped",
      "retry_count": 0,
      "error_log": "string | null",
      "screenshot_path": "string | null",
      "execution_time_ms": 0
    }
  ],
  "bugs": [
    {
      "id": "BUG-001",
      "test_case_id": "TC-001",
      "script_id": "SCR-001",
      "title": "string (format: [Component] Action causes unexpected behaviour)",
      "severity": "P0 | P1 | P2 | P3",
      "component": "string",
      "error_message": "string",
      "url": "string",
      "steps_to_reproduce": ["string"],
      "expected_result": "string",
      "actual_result": "string",
      "screenshot_path": "string | null",
      "jira_ticket_id": "string | null (e.g., PROJ-456)",
      "jira_ticket_url": "string | null",
      "is_duplicate": false,
      "duplicate_of": "string | null (existing JIRA ticket ID)",
      "filed_at": "string (ISO 8601) | null",
      "slack_alerted": false
    }
  ],
  "report": {
    "total_test_cases": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "error": 0,
    "coverage_pct": 0.0,
    "pass_rate": 0.0,
    "bug_summary": {
      "P0": 0,
      "P1": 0,
      "P2": 0,
      "P3": 0,
      "total": 0
    },
    "allure_report_url": "string | null",
    "summary": "string",
    "generated_at": "string (ISO 8601) | null",
    "slack_delivered": false,
    "jira_comment_posted": false
  },
  "errors": [
    {
      "timestamp": "string (ISO 8601)",
      "agent": "string (agent name)",
      "error_type": "string",
      "message": "string",
      "resolved": false
    }
  ]
}
```

### 1.3 Agent Output Schemas

#### Requirement Analyser Output
```json
{
  "requirements": ["<RequirementObject>"],
  "metadata": {
    "source_type": "jira | document",
    "source_id": "string",
    "total_requirements": 0,
    "parse_warnings": ["string"]
  }
}
```

#### Test Case Generator Output
```json
{
  "test_cases": ["<TestCaseObject>"],
  "coverage_map": {
    "REQ-001": ["TC-001", "TC-002"]
  },
  "total_generated": 0
}
```

#### Script Generator Output
```json
{
  "scripts": ["<ScriptObject>"],
  "page_objects_created": ["string (file paths)"],
  "total_generated": 0
}
```

#### Bug Filer Output
```json
{
  "bugs_filed": ["<BugObject with jira_ticket_id populated>"],
  "bugs_updated": ["<BugObject where is_duplicate=true>"],
  "total_filed": 0,
  "total_duplicates": 0
}
```

#### Report Generator Output
```json
{
  "report": "<ReportObject>",
  "slack_message_ts": "string | null",
  "html_report_path": "string | null"
}
```

---

## 2. Behavioral Rules

### 2.1 Human Review Gate
- **MANDATORY** for `run_type: "new_feature"` — all generated Playwright scripts must be reviewed and approved before execution.
- **AUTO-SKIPPED** for `run_type: "regression"` — scripts execute immediately.

### 2.2 Duplicate Bug Prevention
Before filing any bug in JIRA, the Bug Filer agent MUST search existing tickets matching on ALL THREE fields:
1. Component name
2. Error message
3. URL where the bug occurred

If a match is found → **update** the existing ticket (add comment). Do NOT create a new ticket.

### 2.3 Severity Mapping
| Level | Meaning | Slack Emoji |
|-------|---------|-------------|
| P0 | Complete application crash or data loss | 🔴 |
| P1 | Broken core user flow | 🟠 |
| P2 | Degraded or incorrect UX | 🟡 |
| P3 | Cosmetic issue | 🔵 |

### 2.4 Retry Policy
- **Max retries:** 3 per script
- **Applies to:** Environment/tooling errors ONLY (not test logic failures)
- **On 3rd failure:** Stop script, log to `progress.md`, send Slack alert to human

### 2.5 Regression Feedback Loop
- Every filed bug MUST trigger the Test Case Generator to create a regression test case in the **next** cycle.
- This is fully automatic — no manual action required.

### 2.6 Script Standards
- Language: **TypeScript** (no exceptions)
- Pattern: **Page Object Model** (no exceptions)
- No hardcoded credentials anywhere

### 2.7 Orchestrator Abort Conditions
The Orchestrator MUST abort the entire run if:
1. Requirement Analyser returns empty or unparseable content
2. JIRA API is unreachable at run start
3. More than 50% of scripts fail due to execution crashes (not test logic)

On abort: Log reason to `progress.md` + send Slack notification.

### 2.8 Naming Conventions
- Bug titles: `[ComponentName] Short factual description of action causing unexpected behaviour`
- Test files: `{feature}.spec.ts`
- Page objects: `{PageName}Page.ts`
- Component objects: `{ComponentName}Component.ts`

### 2.9 Communication Rules
- Slack alerts: Real-time for P0/P1 bugs (don't wait for run completion)
- Report language: Professional, data-first, no filler sentences
- JIRA comment on source ticket upon run completion

---

## 3. Architectural Invariants

- **3-Layer Architecture (A.N.T.):**
  - `architecture/` — Layer 1: SOPs (Markdown). If logic changes, update the SOP *before* updating code.
  - Navigation — Layer 2: Decision-making/routing layer (Orchestrator). Calls tools in the correct order.
  - `tools/` — Layer 3: Deterministic Python scripts. Atomic and testable.
- **Environment:** All secrets/tokens live in `.env`. Never hardcode credentials.
- **Temp files:** All intermediates go to `.tmp/`. Ephemeral by design.
- **Data-First:** No tool is built until its Input/Output schema is locked here.
- **Self-Annealing:** On failure → Analyze → Patch → Test → Update Architecture docs.
- **Sequential Pipeline:** Agents execute in strict order: Analyser → Generator → Script Gen → [Human Gate] → Execution → Bug Filer → Reporter.
- **Single Writer:** Only one agent writes to `context.json` at a time (enforced by sequential pipeline).
- **Shared Context:** `context.json` in `.tmp/` is the ONLY inter-agent communication channel.

---

## 4. Pipeline Flow

```
Input (JIRA ID or Document)
    │
    ▼
┌─────────────────────┐
│ 1. Requirement      │
│    Analyser          │──→ context.json (requirements[])
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ 2. Test Case        │
│    Generator         │──→ context.json (test_cases[])
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ 3. Script           │
│    Generator         │──→ context.json (scripts[]) + /tests/*.spec.ts
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ 4. Human Review     │ (if run_type == "new_feature")
│    Gate              │──→ context.json (scripts[].status = "approved")
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ 5. Script Executor  │
│    (Playwright)      │──→ context.json (scripts[].status) + allure-results/
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ 6. Bug Filer        │──→ context.json (bugs[]) + JIRA tickets
│    (+ Slack P0/P1)   │──→ Slack real-time alerts
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ 7. Report Generator │──→ Slack report + HTML + JIRA comment
└─────────────────────┘
```

---

## 5. Maintenance Log
_To be populated during Phase 5 (Trigger/Deployment)._
