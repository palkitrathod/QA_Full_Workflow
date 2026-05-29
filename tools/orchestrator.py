import os
import sys
import uuid
import datetime
from .context_manager import ContextManager
from .requirement_analyser import RequirementAnalyser
from .test_case_generator import TestCaseGenerator
from .script_generator import ScriptGenerator
from .script_executor import ScriptExecutor
from .bug_filer import BugFiler
from .report_generator import ReportGenerator
from .slack_notifier import SlackNotifier
from .e2e_helper import E2EHelper
from .deep_evaluation import evaluate_run
from .evaluation import EvaluationTool

class PipelineController:
    """
    Main pipeline controller.
    """
    
    def __init__(self, input_mode: str, run_type: str, source_id: str, document_path: str = None):
        self.context_manager = ContextManager()
        self.slack_notifier = SlackNotifier()
        
        run_id = str(uuid.uuid4())
        
        # Initialize context
        ctx = self.context_manager.get_full_context()
        ctx["run_id"] = run_id
        ctx["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        ctx["input_mode"] = input_mode
        ctx["run_type"] = run_type
        if input_mode == "jira":
            ctx["source_ticket_id"] = source_id
        else:
            ctx["document_path"] = document_path
            
        self.context_manager.update_full_context(ctx)

    def _fetch_jira_custom_fields(self):
        ctx = self.context_manager.get_full_context()
        if ctx.get("input_mode") != "jira":
            return
        from .jira_client import JiraClient
        ticket = JiraClient().fetch_ticket(ctx.get("source_ticket_id"))
        ctx["target_app_url"] = ticket.get("target_app_url") or ctx.get("target_app_url")
        ctx["scope"] = ticket.get("scope") or ctx.get("scope")
        ctx["e2e_flow"] = ticket.get("e2e_flow") or ctx.get("e2e_flow")
        ctx["e2e_credentials"] = {
            "username": ticket.get("e2e_username"),
            "password": ticket.get("e2e_password")
        }
        self.context_manager.update_full_context(ctx)

    def run_pipeline(self, dry_run: bool = False):
        try:
            print("\n[START] Starting QA Workflow Pipeline")
            self._fetch_jira_custom_fields()
            
            print("\n[1/7] Analyzing Requirements...")
            RequirementAnalyser().run()
            # Evaluate after requirement analysis
            EvaluationTool.evaluate("RequirementAnalyser")
            
            print("\n[2/7] Generating Test Cases...")
            TestCaseGenerator().run()
            # Evaluate after test case generation
            EvaluationTool.evaluate("TestCaseGenerator")
            
            print("\n[3/7] Generating Playwright Scripts...")
            ScriptGenerator().run()
            # Evaluate after script generation
            EvaluationTool.evaluate("ScriptGenerator")

            # ==== E2E flow scripts ====
            ctx = self.context_manager.get_full_context()
            e2e_flow = ctx.get("e2e_flow")
            if e2e_flow:
                flow_list = [p.strip() for p in e2e_flow.split(',') if p.strip()]
                scope = ctx.get("scope") or "default"
                for page_name in flow_list:
                    E2EHelper.ensure_page_object(page_name)
                spec_content = E2EHelper.build_e2e_spec(flow_list, scope)
                spec_filename = f"e2e_{scope}.spec.ts"
                spec_path = os.path.join("tests/specs", spec_filename)
                os.makedirs("tests/specs", exist_ok=True)
                with open(spec_path, "w", encoding="utf-8") as f:
                    f.write(spec_content)
                existing = ctx.get("scripts", [])
                existing.append({"id": f"E2E-{scope}", "file_path": f"tests/specs/{spec_filename}", "status": "pending"})
                self.context_manager.update_scripts(existing)
                ctx = self.context_manager.get_full_context()
                print(f"[OK] Generated E2E spec: {spec_filename}")
            
            # Human Review Gate
            if ctx.get("run_type") == "new_feature" and not dry_run:
                self.context_manager.update_status("awaiting_review")
                print("\n[PAUSE] HUMAN REVIEW REQUIRED")
                self.slack_notifier.send_human_review_request(ctx.get("scripts", []), ctx.get("run_id"))
                
                ans = input("Approve generated scripts for execution? (Y/N): ")
                if ans.lower() != 'y':
                    self.abort("User rejected generated scripts.")
                    return

            scripts = ctx.get("scripts", [])
            for s in scripts:
                s["status"] = "approved"
            self.context_manager.update_scripts(scripts)

            if dry_run:
                print("\n[DRY RUN] Complete. Stopping before execution.")
                return

            print("\n[4/7] Executing Scripts...")
            ScriptExecutor().run()

            print("\n[5/7] Filing Bugs for Failed Tests...")
            BugFiler().run()

            print("\n[6/7] Running Deep Evaluation...")
            eval_result = evaluate_run(ctx.get("run_id"))
            overall = eval_result.get("overall_accuracy", 0)
            threshold = int(os.getenv("EVAL_THRESHOLD", "90"))
            if overall < threshold:
                self.abort(f"Overall evaluation {overall}% below threshold {threshold}%.")
                return

            print("\n[7/7] Generating Report...")
            ReportGenerator().run()
            
            print("\n[DONE] Pipeline Completed Successfully!")
            
        except ValueError as ve:
            self.abort(str(ve))
        except Exception as e:
            self.abort(f"Unexpected error: {e}")

    def abort(self, reason: str):
        print(f"\n[ABORT] PIPELINE ABORTED: {reason}")
        self.context_manager.update_status("aborted")
        ctx = self.context_manager.get_full_context()
        self.slack_notifier.send_abort_notification(reason, ctx.get("run_id", "N/A"))
        sys.exit(1)

class Orchestrator(PipelineController):
    """Alias for backward compatibility."""
    pass
