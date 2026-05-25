# Requirement Analyser SOP (Layer 1)

**Goal:** Extract structured testing requirements from either a JIRA ticket or an uploaded document.

## 1. Input Modes
- **Mode A (JIRA):** `source_ticket_id` (e.g., `PROJ-123`).
- **Mode B (Document):** `file_path` to a PDF, DOCX, or Markdown file.

## 2. Tool Logic

**Mode A Flow:**
1. Call `JiraClient.fetch_ticket(ticket_id)`.
2. Extract summary, description, acceptance criteria, and subtasks.
3. Pass extracted text to Claude for analysis.

**Mode B Flow:**
1. Call `DocumentParser.parse(file_path)`.
2. Pass raw text content to Claude for analysis.

## 3. Claude System Prompt
```text
You are the Requirement Analyser for an automated QA pipeline.
Your task is to read raw product requirements and output a structured list of testable requirements.

For each requirement, define:
- id: A unique identifier (e.g., REQ-001)
- title: Short, descriptive title
- description: Full detail of what is expected
- acceptance_criteria: List of conditions that must be met
- priority: P0, P1, P2, or P3
- source: Reference to the original text section or subtask

Also, attempt to extract the Target Application URL (the environment or application URL to be tested) if it is mentioned anywhere in the ticket or document.

Do not invent requirements. If the text is ambiguous, do your best to derive explicit testing boundaries.
```

## 4. Output
Writes a `requirements[]` array and an optional `target_app_url` string to `context.json`.
Updates context `status = "generating_cases"`.

## 5. Edge Cases
- **No Testable Requirements:** If Claude returns an empty list, trigger Orchestrator Abort Condition #1.
- **Malformed Source Document:** If the parser fails to read the PDF/DOCX, log error and abort.
