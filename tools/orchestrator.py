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

class Orchestrator:
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

    def run_pipeline(self, dry_run: bool = False):
        try:
            print("\n[START] Starting QA Workflow Pipeline")
            
            print("\n[1/7] Analyzing Requirements...")
            RequirementAnalyser().run()
            
            print("\n[2/7] Generating Test Cases...")
            TestCaseGenerator().run()
            
            print("\n[3/7] Generating Playwright Scripts...")
            ScriptGenerator().run()
            
            # Human Review Gate
            ctx = self.context_manager.get_full_context()
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
            
            print("\n[5/7] Filing Bugs...")
            BugFiler().run()
            
            print("\n[6/7] Generating Report...")
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
