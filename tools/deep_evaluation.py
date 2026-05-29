import os
import json
import re
import subprocess
from pathlib import Path
from .llm_client import LLMClient


def _jaccard_similarity(a: str, b: str) -> float:
    a_tokens = set(re.findall(r"\w+", a.lower()))
    b_tokens = set(re.findall(r"\w+", b.lower()))
    if not a_tokens and not b_tokens:
        return 1.0
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)


def evaluate_scripts(scripts, test_cases):
    """Evaluate script quality: exist, has valid content, executed, errors captured."""
    if not scripts:
        return 0.0, [{"script_id": "N/A", "score": 0, "reason": "No scripts generated"}]

    scores = []
    details = []
    for script in scripts:
        checks = 0
        passed = 0
        reasons = []
        path = Path(script.get("file_path", ""))

        # 1) File exists on disk
        checks += 1
        if path.is_file():
            passed += 1
        else:
            reasons.append("File not found")

        # 2) Has valid Playwright structure (test + expect + locator)
        checks += 1
        if path.is_file():
            content = path.read_text(encoding="utf-8", errors="replace")
            has_test = "test(" in content or 'test(' in content
            has_expect = "expect(" in content
            has_actions = bool(re.search(r"locator\(|page\.", content))
            if has_test and has_expect and has_actions:
                passed += 1
            else:
                missing = []
                if not has_test: missing.append("test()")
                if not has_expect: missing.append("expect()")
                if not has_actions: missing.append("page/locator calls")
                reasons.append(f"Missing: {', '.join(missing)}")

        # 3) Execution completed (pass or fail with error captured)
        checks += 1
        status = script.get("status", "unknown")
        if status == "passed":
            passed += 1
        elif status == "failed":
            if script.get("error_log"):
                passed += 1
                reasons.append(f"Failed but error captured")
            else:
                reasons.append("Failed with no error_log")
        else:
            reasons.append(f"Status: {status} (expected passed/failed)")

        score = round((passed / checks) * 100, 1) if checks else 0
        scores.append(score)
        details.append({
            "script_id": script.get("id", "unknown"),
            "score": score,
            "checks_passed": passed,
            "checks_total": checks,
            "reasons": reasons,
            "status": status,
        })

    overall = round((sum(scores) / len(scores)) * 100, 1) if scores else 0.0
    return overall, details


def evaluate_bugs(bugs, scripts):
    """Evaluate bug completeness: every failure filed, all fields present, error match."""
    failed_scripts = [s for s in scripts if s.get("status") == "failed"]

    if not bugs:
        if failed_scripts:
            return 0.0, [{
                "bug_id": "N/A",
                "score": 0,
                "reason": f"{len(failed_scripts)} failed scripts but 0 bugs filed",
            }]
        return 100.0, [{"bug_id": "N/A", "score": 100, "reason": "No failures, no bugs needed"}]

    scores = []
    details = []
    required_fields = [
        "title", "severity", "component", "steps_to_reproduce",
        "expected_result", "actual_result", "environment", "test_data_used",
    ]

    for bug in bugs:
        checks = 0
        passed = 0
        reasons = []

        # 1) Every failed script has a corresponding bug
        checks += 1
        script_id = bug.get("script_id")
        if script_id:
            script = next((s for s in scripts if s.get("id") == script_id), None)
            if script and script.get("status") == "failed":
                passed += 1
            else:
                reasons.append(f"Script '{script_id}' didn't fail — bug may be invalid")
        else:
            passed += 1

        # 2) All required fields present and non-empty
        checks += 1
        missing = [f for f in required_fields if not bug.get(f)]
        if not missing:
            passed += 1
        else:
            reasons.append(f"Missing fields: {', '.join(missing)}")

        # 3) Error message matches script error_log (Jaccard >= 0.3)
        checks += 1
        if script_id:
            script = next((s for s in scripts if s.get("id") == script_id), None)
            script_err = (script.get("error_log") or "") if script else ""
            bug_err = bug.get("error_message") or ""
            sim = _jaccard_similarity(script_err, bug_err) if script_err and bug_err else 1.0
            if sim >= 0.3:
                passed += 1
            else:
                reasons.append(f"Error mismatch (Jaccard: {sim:.0%})")
        else:
            passed += 1

        # 4) Steps to reproduce have at least 3 steps
        checks += 1
        steps = bug.get("steps_to_reproduce", [])
        if len(steps) >= 3:
            passed += 1
        else:
            reasons.append(f"Only {len(steps)} step(s) — need ≥3")

        score = round((passed / checks) * 100, 1) if checks else 0
        scores.append(score)
        details.append({
            "bug_id": bug.get("id") or bug.get("test_case_id", "unknown"),
            "score": score,
            "reasons": reasons,
        })

    overall = round((sum(scores) / len(scores)) * 100, 1) if scores else 0.0
    return overall, details


def evaluate_coverage(scripts, test_cases):
    """Every test case has a script, every script has a test case reference."""
    if not test_cases:
        return 0.0, {"coverage": 0, "missing": [], "reasons": ["No test cases provided"]}

    tc_ids = {tc.get("id") for tc in test_cases if tc.get("id")}
    script_tc_ids = {s.get("test_case_id") for s in scripts if s.get("test_case_id")}

    covered = tc_ids & script_tc_ids
    missing = tc_ids - script_tc_ids
    orphaned = script_tc_ids - tc_ids

    coverage = round((len(covered) / len(tc_ids)) * 100, 1) if tc_ids else 100.0
    reasons = []
    if missing:
        reasons.append(f"Test cases w/o scripts: {', '.join(missing)}")
    if orphaned:
        reasons.append(f"Scripts w/o test cases: {', '.join(orphaned)}")
    if not reasons:
        reasons.append("All test cases mapped to scripts")

    return coverage, {"coverage": coverage, "missing": list(missing), "orphaned": list(orphaned), "reasons": reasons}


# ---------------------------------------------------------------------
# Optional LLM-based semantic evaluation layer
_ENABLE_LLM_EVAL = os.getenv("LLM_EVAL", "").lower() in ("1", "true", "yes")


def _llm_available() -> bool:
    if not _ENABLE_LLM_EVAL:
        return False
    try:
        LLMClient()
        return True
    except Exception:
        return False


def _llm_rate_script(script: dict, test_case: dict) -> dict:
    """Ask LLM to rate script quality against the test case (0-100)."""
    client = LLMClient()
    prompt = (
        "You are a QA evaluator. Rate how well a Playwright test script covers its test case.\n"
        "Return JSON: { 'coverage_score': int(0-100), 'assertion_quality': int(0-100), "
        "'edge_case_handling': int(0-100), 'issues': [str], 'overall': int(0-100) }\n\n"
        "Rules:\n"
        "- coverage_score: does the script test ALL acceptance criteria?\n"
        "- assertion_quality: are expect() calls meaningful (not just existence checks)?\n"
        "- edge_case_handling: does it test boundary values, error states?\n"
        "- issues: list specific problems found\n"
        "- overall: weighted average of the above"
    )
    data = {
        "test_case": test_case,
        "script_file": script.get("file_path"),
        "script_status": script.get("status"),
        "error_log": script.get("error_log"),
    }
    return client.generate_json(prompt, json.dumps(data, indent=2))


def _llm_rate_bug(bug: dict, script: dict) -> dict:
    """Ask LLM to rate bug report quality (0-100)."""
    client = LLMClient()
    prompt = (
        "You are a QA evaluator. Rate the quality of a bug report.\n"
        "Return JSON: { 'clarity': int(0-100), 'reproducibility': int(0-100), "
        "'root_cause_analysis': int(0-100), 'issues': [str], 'overall': int(0-100) }\n\n"
        "Rules:\n"
        "- clarity: is the bug title clear, steps detailed, expected vs actual unambiguous?\n"
        "- reproducibility: can a developer reliably reproduce from the description?\n"
        "- root_cause_analysis: does the error message point to the likely cause?\n"
        "- issues: list specific quality problems\n"
        "- overall: weighted average"
    )
    data = {"bug": bug, "script_error": script.get("error_log") if script else None}
    return client.generate_json(prompt, json.dumps(data, indent=2))


def blend_scores(
    script_pct, bug_pct, coverage_pct,
    llm_script_scores=None, llm_bug_scores=None,
    weights=(0.35, 0.20, 0.15, 0.20, 0.10),
):
    """
    Weights: mechanical(scripts)=0.35, mechanical(bugs)=0.20, coverage=0.15,
             llm(scripts+bugs)=0.20, llm(bugs)=0.10
    """
    mechanical = (
        script_pct * weights[0]
        + bug_pct * weights[1]
        + coverage_pct * weights[2]
    )

    if llm_script_scores is not None and llm_bug_scores is not None:
        llm_avg = (llm_script_scores + llm_bug_scores) / 2
        return round(mechanical + llm_avg * weights[3] + llm_bug_scores * weights[4], 1)
    elif llm_script_scores is not None:
        return round(mechanical + llm_script_scores * (weights[3] + weights[4]), 1)

    return round(mechanical / sum(weights[:3]) * 100, 1)  # normalize when no LLM


def evaluate_run(run_id: str) -> dict:
    """Load context, run evaluations (mechanical + optional LLM), write results back.
    Returns dict with overall_accuracy and per-component scores."""
    ctx_path = Path(".tmp") / "context.json"
    if not ctx_path.is_file():
        raise FileNotFoundError(f"Context file not found for run {run_id}")
    ctx = json.loads(ctx_path.read_text())

    test_cases = ctx.get("test_cases", [])
    scripts = ctx.get("scripts", [])
    bugs = ctx.get("bugs", [])

    # --- Mechanical checks (fast, deterministic) ---
    script_score, script_details = evaluate_scripts(scripts, test_cases)
    bug_score, bug_details = evaluate_bugs(bugs, scripts)
    coverage_score, coverage_details = evaluate_coverage(scripts, test_cases)

    eval_data = {
        "script_quality": script_score,
        "bug_quality": bug_score,
        "test_coverage": coverage_score,
        "details": {
            "scripts": script_details,
            "bugs": bug_details,
            "coverage": coverage_details,
        },
    }

    # --- Optional LLM semantic evaluation ---
    llm_script_scores = None
    llm_bug_scores = None
    llm_details_scripts = []
    llm_details_bugs = []

    if _llm_available():
        print("[LLM EVAL] Running semantic evaluation…")

        # Rate each script against its test case
        script_ratings = []
        for script in scripts:
            tc_id = script.get("test_case_id")
            tc = next((t for t in test_cases if t.get("id") == tc_id), {})
            if tc and script.get("file_path"):
                try:
                    rating = _llm_rate_script(script, tc)
                    script_ratings.append(rating.get("overall", 50))
                    llm_details_scripts.append({
                        "script_id": script.get("id"),
                        "llm_coverage": rating.get("coverage_score"),
                        "llm_assertions": rating.get("assertion_quality"),
                        "llm_edge_cases": rating.get("edge_case_handling"),
                        "llm_issues": rating.get("issues", []),
                    })
                except Exception as e:
                    print(f"  [LLM EVAL] Script eval failed: {e}")
                    script_ratings.append(50)
                    llm_details_scripts.append({"script_id": script.get("id"), "error": str(e)})

        if script_ratings:
            llm_script_scores = sum(script_ratings) / len(script_ratings)

        # Rate each bug against its script
        bug_ratings = []
        for bug in bugs:
            script_id = bug.get("script_id")
            script = next((s for s in scripts if s.get("id") == script_id), {})
            try:
                rating = _llm_rate_bug(bug, script)
                bug_ratings.append(rating.get("overall", 50))
                llm_details_bugs.append({
                    "bug_id": bug.get("id") or bug.get("test_case_id"),
                    "llm_clarity": rating.get("clarity"),
                    "llm_reproducibility": rating.get("reproducibility"),
                    "llm_root_cause": rating.get("root_cause_analysis"),
                    "llm_issues": rating.get("issues", []),
                })
            except Exception as e:
                print(f"  [LLM EVAL] Bug eval failed: {e}")
                bug_ratings.append(50)
                llm_details_bugs.append({"bug_id": bug.get("test_case_id"), "error": str(e)})

        if bug_ratings:
            llm_bug_scores = sum(bug_ratings) / len(bug_ratings)

        print(f"  [LLM EVAL] Script avg: {llm_script_scores:.1f}  Bug avg: {llm_bug_scores:.1f}")

    overall = blend_scores(
        script_score, bug_score, coverage_score,
        llm_script_scores, llm_bug_scores,
    )

    eval_data["overall_accuracy"] = overall
    eval_data["llm_enabled"] = _llm_available()
    eval_data["llm_details"] = {
        "scripts": llm_details_scripts,
        "bugs": llm_details_bugs,
    }
    eval_data["weights"] = (
        "mechanical(scripts=0.35, bugs=0.20, coverage=0.15), "
        "llm(semantic=0.20, bug_quality=0.10)"
    )

    ctx["evaluation"] = eval_data
    ctx_path.write_text(json.dumps(ctx, indent=2))

    print(f"\n[EVAL] Mechanical — Scripts: {script_score}%  Bugs: {bug_score}%  Coverage: {coverage_score}%")
    if _llm_available():
        print(f"[EVAL] LLM       — Scripts: {llm_script_scores:.1f}    Bugs: {llm_bug_scores:.1f}")
    print(f"[EVAL] Overall   — {overall}%")
    return eval_data
