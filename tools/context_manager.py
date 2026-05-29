import os
import json
from pathlib import Path
from typing import Dict, Any, List

class ContextManager:
    """
    Central read/write manager for context.json.
    Provides typed access methods and schema validation.
    """
    
    def __init__(self, context_path: str = ".tmp/context.json"):
        self.context_path = Path(context_path)
        self.context_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize context file if it doesn't exist
        if not self.context_path.exists():
            self._write_context({
                "run_id": None,
                "status": "initializing",
                "input_mode": None,
                "run_type": None,
                "source_ticket_id": None,
                "target_app_url": None,
                "requirements": [],
                "evaluations": [],
                "test_cases": [],
                "scripts": [],
                "bugs": [],
                "report": {
                    "total_test_cases": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "error": 0,
                    "coverage_pct": 0.0,
                    "pass_rate": 0.0,
                    "bug_summary": {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "total": 0},
                    "allure_report_url": None,
                    "summary": "",
                    "generated_at": None,
                    "slack_delivered": False,
                    "jira_comment_posted": False
                },
                "errors": []
            })
            
    def _read_context(self) -> Dict[str, Any]:
        with open(self.context_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def _write_context(self, data: Dict[str, Any]) -> None:
        with open(self.context_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
    def get_status(self) -> str:
        return self._read_context().get("status", "unknown")
        
    def update_status(self, new_status: str) -> None:
        ctx = self._read_context()
        ctx["status"] = new_status
        self._write_context(ctx)
        
    def get_target_app_url(self) -> str:
        return self._read_context().get("target_app_url")
        
    def update_target_app_url(self, url: str) -> None:
        ctx = self._read_context()
        ctx["target_app_url"] = url
        self._write_context(ctx)
        
    def get_requirements(self) -> List[Dict[str, Any]]:
        return self._read_context().get("requirements", [])
        
    def update_requirements(self, requirements: List[Dict[str, Any]]) -> None:
        ctx = self._read_context()
        ctx["requirements"] = requirements
        self._write_context(ctx)
        
    def get_test_cases(self) -> List[Dict[str, Any]]:
        return self._read_context().get("test_cases", [])
        
    def update_test_cases(self, test_cases: List[Dict[str, Any]]) -> None:
        ctx = self._read_context()
        ctx["test_cases"] = test_cases
        self._write_context(ctx)
        
    def get_scripts(self) -> List[Dict[str, Any]]:
        return self._read_context().get("scripts", [])
        
    def update_scripts(self, scripts: List[Dict[str, Any]]) -> None:
        ctx = self._read_context()
        ctx["scripts"] = scripts
        self._write_context(ctx)
        
    def get_bugs(self) -> List[Dict[str, Any]]:
        return self._read_context().get("bugs", [])
        
    def update_bugs(self, bugs: List[Dict[str, Any]]) -> None:
        ctx = self._read_context()
        ctx["bugs"] = bugs
        self._write_context(ctx)
        
    def get_report(self) -> Dict[str, Any]:
        return self._read_context().get("report", {})
        
    def update_report(self, report: Dict[str, Any]) -> None:
        ctx = self._read_context()
        ctx["report"] = report
        self._write_context(ctx)

    def log_error(self, agent: str, error_type: str, message: str) -> None:
        ctx = self._read_context()
        import datetime
        error_entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "agent": agent,
            "error_type": error_type,
            "message": message,
            "resolved": False
        }
        ctx["errors"] = ctx.get("errors", [])
        ctx["errors"].append(error_entry)
        self._write_context(ctx)
        
    def get_full_context(self) -> Dict[str, Any]:
        return self._read_context()

    def update_full_context(self, ctx: Dict[str, Any]) -> None:
        self._write_context(ctx)

    def get_evaluations(self) -> List[Dict[str, Any]]:
        return self._read_context().get("evaluations", [])

    def update_evaluations(self, evaluations: List[Dict[str, Any]]) -> None:
        ctx = self._read_context()
        ctx["evaluations"] = evaluations
        self._write_context(ctx)

    def append_evaluation(self, evaluation: Dict[str, Any]) -> None:
        ctx = self._read_context()
        evs = ctx.get("evaluations", [])
        evs.append(evaluation)
        ctx["evaluations"] = evs
        self._write_context(ctx)
