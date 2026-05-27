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

import os
from .e2e_helper import E2EHelper
from .deep_evaluation import evaluate_run  # <-- new import


class ScriptGenerator:
    """Generates Playwright scripts (including optional E2E flow)."""

    def __init__(self):
        self.context_manager = ContextManager()
        self.base_dir = os.path.join(os.getcwd(), "tests/specs")
        os.makedirs(self.base_dir, exist_ok=True)

    def run(self):
        ctx = self.context_manager.get_full_context()
        scripts = []
        # Normal per‑test script generation (existing logic omitted for brevity)
        # ... generate individual test spec files based on test_cases ...

        # ==== E2E generation ====
        e2e_flow = ctx.get("e2e_flow")
        if e2e_flow:
            # e2e_flow is expected as a comma‑separated string from JIRA custom field
            flow_list = [p.strip() for p in e2e_flow.split(',') if p.strip()]
            scope = ctx.get("scope") or "default"
            # Ensure each page object exists
            for page_name in flow_list:
                E2EHelper.ensure_page_object(page_name)
            # Build spec content
            spec_content = E2EHelper.build_e2e_spec(flow_list, scope)
            spec_filename = f"e2e_{scope}.spec.ts"
            spec_path = os.path.join(self.base_dir, spec_filename)
            with open(spec_path, "w", encoding="utf-8") as f:
                f.write(spec_content)
            scripts.append({"id": f"E2E-{scope}", "file_path": f"tests/specs/{spec_filename}", "status": "pending"})
        # update context with generated scripts
        self.context_manager.update_scripts(scripts)


class E2EHelper:
    """Utility class for generating page objects and E2E specs dynamically."""

    @staticmethod
    def ensure_page_object(page_name: str, base_dir: str = "tests/pages") -> str:
        """Create a minimal page‑object file if it does not exist.
        Returns the relative import path (e.g. 'tests/pages/CartPage')."""
        filename = f"{page_name}Page.ts"
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path):
            os.makedirs(base_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(
                    f"import {{ Page }} from '@playwright/test';\n\n"
                    f"export class {page_name}Page {{\n"
                    f"  constructor(private page: Page) {{}}\n\n"
                    f"  async navigate() {{\n"
                    f"    // TODO: add navigation URL for {page_name}\n"
                    f"  }}\n"
                    f"}}\n"
                )
        # Return import path without extension
        return f"tests/pages/{page_name}Page"

    @staticmethod
    def build_e2e_spec(flow: list, scope: str, base_url_var: str = "BASE_URL") -> str:
        """Generate the TypeScript content for an end‑to‑end spec.
        * `flow` – ordered list of page names (e.g. ["Login", "Cart", "Checkout"]).
        * `scope` – used in the file name and test title.
        Returns the full spec content as a string."""
        lines = [
            "import { test, expect } from '@playwright/test';",
        ]
        # import page objects
        for page in flow:
            import_path = f"{page}Page"
            lines.append(f"import {{ {page}Page }} from '../pages/{page}Page';")
        lines.append("\n")
        # test definition
        lines.append(f"test.describe('E2E {scope} flow', () => {{")
        lines.append("  let pageObj: any;")
        lines.append("  test.beforeEach(async ({ page }) => {")
        # instantiate first page
        first = flow[0]
        lines.append(f"    pageObj = new {first}Page(page);")
        lines.append("    await pageObj.navigate();")
        lines.append("  });")
        lines.append("\n")
        for idx, page in enumerate(flow):
            if idx > 0:
                lines.append(f"  test('{page} step', async () => {{")
                lines.append(f"    pageObj = new {page}Page(pageObj.page);")
                lines.append("    await pageObj.navigate();")
                lines.append("    // add assertions specific to this page if needed")
                lines.append("  });")
                lines.append("\n")
        lines.append("});")
        return "\n".join(lines)

# End of E2EHelper class

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
            # Fetch JIRA custom fields for E2E flow if input mode is JIRA
            from .mcp_wrapper import mcp_call
            # Use MCP to fetch custom fields for the ticket
            fields = mcp_call(
                ServerName="atlassian",
                ToolName="jira_get_issue",
                Arguments={
                    "base_url": os.getenv("JIRA_BASE_URL"),
                    "ticket_id": source_id,
                    "auth_token": os.getenv("JIRA_API_TOKEN")
                },
                toolAction="MCP call",
                toolSummary="JIRA custom fields"
            )
            # Extract needed fields (assuming the MCP returns full issue JSON)
            ctx["target_app_url"] = fields.get("fields", {}).get("customfield_target_url") or ctx.get("target_app_url")
            ctx["scope"] = fields.get("fields", {}).get("customfield_scope") or ctx.get("scope")
            ctx["e2e_flow"] = fields.get("fields", {}).get("customfield_e2e_flow") or ctx.get("e2e_flow")
            ctx["e2e_credentials"] = {
                "username": fields.get("fields", {}).get("customfield_e2e_username"),
                "password": fields.get("fields", {}).get("customfield_e2e_password")
            }
            ctx["target_app_url"] = fields.get("Target URL") or ctx.get("target_app_url")
            ctx["scope"] = fields.get("Scope") or ctx.get("scope")
            ctx["e2e_flow"] = fields.get("E2E Flow") or ctx.get("e2e_flow")
            ctx["e2e_credentials"] = {
                "username": fields.get("E2E Username"),
                "password": fields.get("E2E Password")
            }
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

            # ==== Deep Evaluation ==== 
            overall = evaluate_run(ctx.get("run_id"))
            threshold = int(os.getenv("EVAL_THRESHOLD", "90"))
            if overall < threshold:
                self.abort(f"Overall evaluation {overall}% below threshold {threshold}%.")
                return

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

class Orchestrator(PipelineController):
    """Alias for backward compatibility."""
    pass
