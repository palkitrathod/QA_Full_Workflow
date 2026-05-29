import os
import json
import subprocess
import time
from .context_manager import ContextManager

class ScriptExecutor:
    """
    Executes Playwright tests and parses results.
    Updates context.json with execution status.
    """
    
    def __init__(self):
        self.context_manager = ContextManager()

    def run(self):
        self.context_manager.update_status("executing")
        scripts = self.context_manager.get_scripts()
        
        # Only run scripts that are approved or pending (if regression)
        scripts_to_run = [s for s in scripts if s.get("status") in ["approved", "pending"]]
        
        if not scripts_to_run:
            print("No approved scripts to execute.")
            return

        print(f"[EXEC] Executing {len(scripts_to_run)} Playwright scripts...")
        
        # We assume playwright is installed and can run `npm run test`
        # Playwright reporter should ideally output a JSON file we can parse,
        # but for simplicity we will run it via shell and check exit code.
        # A more robust implementation would use a custom reporter or playwright's json reporter.
        
        start_time = time.time()
        test_results = {}
        results_file = os.path.join(os.getcwd(), "playwright-results.json")
        try:
            env = os.environ.copy()
            ctx = self.context_manager.get_full_context()
            target_url = ctx.get("target_app_url")
            if target_url:
                env["TARGET_APP_URL"] = target_url
            
            subprocess.run(
                ["npx.cmd", "playwright", "test"],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )
        except Exception as e:
            print(f"Failed to run Playwright: {e}")
            
        execution_time = (time.time() - start_time) * 1000

        # Parse all spec results from Playwright JSON (handles nested suites)
        flat_specs = []
        def extract_specs(suites):
            for suite in suites:
                flat_specs.extend(suite.get("specs", []))
                if suite.get("suites"):
                    extract_specs(suite["suites"])
        if os.path.exists(results_file):
            try:
                with open(results_file, "r", encoding="utf-8") as f:
                    pw_data = json.load(f)
                extract_specs(pw_data.get("suites", []))
                for spec in flat_specs:
                    if spec.get("tests") and spec["tests"][0].get("results"):
                        res = spec["tests"][0]["results"][0]
                        test_results[spec["title"]] = {
                            "status": res.get("status"),
                            "error": res.get("error", {}).get("message") if res.get("error") else None
                        }
            except Exception as e:
                print(f"[WARN] Could not parse playwright-results.json: {e}")
        else:
            print("[WARN] playwright-results.json not found")

        # Match scripts to test results by ordering (scripts and spec tests are in the same order)
        spec_titles_ordered = list(test_results.keys())
        for idx, script in enumerate(scripts):
            if idx < len(spec_titles_ordered):
                spec_title = spec_titles_ordered[idx]
                match = test_results.get(spec_title)
                if match:
                    pw_status = match["status"]
                    script["status"] = "passed" if pw_status == "passed" else "failed"
                    if pw_status != "passed":
                        script["error_log"] = match.get("error")
                    script["execution_time_ms"] = execution_time / max(len(scripts_to_run), 1)
                else:
                    script["status"] = "failed"
                    script["error_log"] = "No matching Playwright result found"
            else:
                script["status"] = "failed"
                script["error_log"] = "No matching Playwright result found"
                
        self.context_manager.update_scripts(scripts)
        
        # Generate Allure report
        try:
            subprocess.run(["npx.cmd", "allure", "generate", "allure-results", "-o", "allure-report", "--clean"], check=False, capture_output=True)
            print("[OK] Allure report generated.")
        except Exception as e:
            print(f"[WARN] Failed to generate Allure report: {e}")
