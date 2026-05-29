import os
import datetime
import json
from pathlib import Path
from .context_manager import ContextManager

class EvaluationTool:
    """Simple rule‑based evaluation layer.

    It is invoked after each major pipeline step (RequirementAnalyser,
    TestCaseGenerator, ScriptGenerator). The checks are lightweight and
    deterministic – no LLM calls are made here.

    The method records an evaluation entry in `context.json` and returns
    a boolean indicating pass/fail.
    """

    @staticmethod
    def evaluate(step_name: str) -> bool:
        """Run validation for *step_name* and store the result.
        Returns ``True`` if the step passes the rules, ``False`` otherwise.
        """
        cm = ContextManager()
        ctx = cm.get_full_context()
        requirements = ctx.get("requirements", [])
        test_cases = ctx.get("test_cases", [])
        scripts = ctx.get("scripts", [])

        # Default pass status – will be flipped to False if any rule fails
        status = "pass"
        issues = []

        if step_name == "RequirementAnalyser":
            if not requirements:
                status = "fail"
                issues.append({
                    "requirement_id": None,
                    "severity": "P0",
                    "message": "No requirements were extracted."
                })
        elif step_name == "TestCaseGenerator":
            # Ensure every requirement has at least one test case linked
            req_ids = {r.get("id") for r in requirements}
            tc_req_ids = {tc.get("requirement_id") for tc in test_cases}
            missing = req_ids - tc_req_ids
            if missing:
                status = "fail"
                for rid in missing:
                    issues.append({
                        "requirement_id": rid,
                        "severity": "P1",
                        "message": f"Requirement {rid} has no generated test case."
                    })
        elif step_name == "ScriptGenerator":
            # Ensure each test case has a corresponding script entry
            tc_ids = {tc.get("id") for tc in test_cases}
            script_tc_ids = {s.get("test_case_id") for s in scripts if s.get("test_case_id")}
            missing = tc_ids - script_tc_ids
            if missing:
                status = "fail"
                for cid in missing:
                    issues.append({
                        "requirement_id": None,
                        "severity": "P2",
                        "message": f"Test case {cid} has no generated script."
                    })
        else:
            # Unknown step – treat as pass
            pass

        evaluation_entry = {
            "evaluation_id": f"EVAL-{len(ctx.get('evaluations', [])) + 1:03d}",
            "tool_name": step_name,
            "status": status,
            "issues": issues,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        # Append to context
        cm.append_evaluation(evaluation_entry)
        return status == "pass"
