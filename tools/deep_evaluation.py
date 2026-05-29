import os
import json
import re
import subprocess
from pathlib import Path

# Helper – simple token Jaccard similarity
def _jaccard_similarity(a: str, b: str) -> float:
    a_tokens = set(re.findall(r"\w+", a.lower()))
    b_tokens = set(re.findall(r"\w+", b.lower()))
    if not a_tokens and not b_tokens:
        return 1.0
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)

# ---------------------------------------------------------------------
def evaluate_test_cases(requirements, test_cases):
    """Compare generated test cases against their source requirements.
    Returns (overall_percentage, list_of_details)."""
    scores = []
    details = []
    for tc in test_cases:
        req = next((r for r in requirements if r["id"] == tc.get("requirement_id")), None)
        if not req:
            score = 0.0
        else:
            title_score = _jaccard_similarity(req.get("title", ""), tc.get("title", ""))
            # acceptance criteria vs steps count similarity (rough proxy)
            crit_len = max(1, len(req.get("acceptance_criteria", [])))
            steps_len = max(1, len(tc.get("steps", [])))
            steps_score = min(1.0, steps_len / crit_len)
            score = (title_score + steps_score) / 2
        scores.append(score)
        details.append({"test_case_id": tc.get("id"), "score": round(score * 100, 1)})
    overall = round((sum(scores) / len(scores)) * 100, 1) if scores else 0.0
    return overall, details

# ---------------------------------------------------------------------
def evaluate_scripts(scripts, page_objects_dir: Path):
    """Validate each generated Playwright spec.
    Returns (overall_percentage, list_of_details)."""
    total_checks = 0
    passed_checks = 0
    details = []
    for script in scripts:
        path = Path(script.get("file_path", ""))
        if not path.is_file():
            details.append({"script_id": script.get("id"), "score": 0})
            continue
        # 1) Syntax check – try tsc if available, else simple regex guard
        try:
            proc = subprocess.run(["tsc", "--noEmit", str(path)], capture_output=True, text=True, timeout=10)
            syntax_ok = proc.returncode == 0
        except Exception:
            syntax_ok = bool(re.search(r"test\(['\"]", path.read_text()))
        # 2) Page‑object imports existence
        content = path.read_text()
        imports = re.findall(r"import\s+{?\s*([\w,\s]+)\s*}?\s+from\s+['\"]([^'\"]+)['\"]", content)
        po_ok = True
        for names, _ in imports:
            for name in names.split(','):
                name_clean = name.strip().replace('Page', '')
                po_path = page_objects_dir / f"{name_clean}Page.ts"
                if not po_path.is_file():
                    po_ok = False
        checks = 2
        passed = int(syntax_ok) + int(po_ok)
        total_checks += checks
        passed_checks += passed
        details.append({"script_id": script.get("id"), "score": round((passed / checks) * 100, 1)})
    overall = round((passed_checks / total_checks) * 100, 1) if total_checks else 0.0
    return overall, details

# ---------------------------------------------------------------------
def evaluate_bugs(bugs, ctx):
    """Check bug title format and error‑message fidelity.
    Returns (overall_percentage, list_of_details)."""
    pattern = re.compile(r"^\[[^\]]+\]\s+.+")
    scores = []
    details = []
    for bug in bugs:
        title_ok = bool(pattern.match(bug.get("title", "")))
        # compare error_message with the stored script error_log (if any)
        script_err = next((s.get("error_log") for s in ctx.get("scripts", []) if s.get("id") == bug.get("script_id")), None)
        error_match = bug.get("error_message") == script_err if script_err else False
        score = (title_ok + error_match) / 2
        scores.append(score)
        details.append({"bug_id": bug.get("id"), "score": round(score * 100, 1)})
    overall = round((sum(scores) / len(scores)) * 100, 1) if scores else 0.0
    return overall, details

# ---------------------------------------------------------------------
def aggregate_scores(test_pct, script_pct, bug_pct, weights=(0.4, 0.4, 0.2)):
    w_test, w_script, w_bug = weights
    return round(test_pct * w_test + script_pct * w_script + bug_pct * w_bug, 1)

# ---------------------------------------------------------------------
def evaluate_run(run_id: str) -> float:
    """Load the run's context, compute evaluation metrics, write back, and post to JIRA.
    Returns the overall accuracy percentage."""
    ctx_path = Path('.tmp') / 'context.json'
    if not ctx_path.is_file():
        raise FileNotFoundError(f"Context file not found for run {run_id}")
    ctx = json.loads(ctx_path.read_text())

    # 1) Test‑case alignment
    tc_score, tc_details = evaluate_test_cases(ctx.get('requirements', []), ctx.get('test_cases', []))
    # 2) Script alignment – page objects live under 'pages' relative to project root
    script_score, script_details = evaluate_scripts(ctx.get('scripts', []), Path('tests/pages'))
    # 3) Bug accuracy
    bug_score, bug_details = evaluate_bugs(ctx.get('bugs', []), ctx)

    overall = aggregate_scores(tc_score, script_score, bug_score)

    ctx['evaluation'] = {
        'test_case_alignment': tc_score,
        'script_alignment': script_score,
        'bug_accuracy': bug_score,
        'overall_accuracy': overall,
        'details': {
            'test_cases': tc_details,
            'scripts': script_details,
            'bugs': bug_details,
        },
    }
    # write back
    ctx_path.write_text(json.dumps(ctx, indent=2))

    # post comment to JIRA if ticket id present
    jira_info = ctx.get('jira', {})
    ticket_id = ctx.get('source_ticket_id') or jira_info.get('ticket_id')
    if ticket_id:
        from .jira_client import JiraClient
        jira = JiraClient()
        comment = (
            f"*Deep Evaluation Summary*\n"
            f"- Test‑case alignment: {tc_score}%\n"
            f"- Script alignment: {script_score}%\n"
            f"- Bug accuracy: {bug_score}%\n"
            f"- **Overall accuracy:** {overall}%"
        )
        jira.add_comment(ticket_id, comment)
    return overall
