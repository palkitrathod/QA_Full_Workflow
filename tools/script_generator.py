import json
import os
from pathlib import Path
from .context_manager import ContextManager
from .llm_client import LLMClient

class ScriptGenerator:
    """
    Generates Playwright TS scripts using POM pattern.
    Updates context.json with script records.
    """
    
    def __init__(self):
        self.context_manager = ContextManager()
        self.llm_client = LLMClient()

    def run(self):
        self.context_manager.update_status("generating_scripts")
        test_cases = self.context_manager.get_test_cases()
        
        if not test_cases:
            print("No test cases found to generate scripts.")
            return

        try:
            with open("architecture/script_generator.md", "r") as f:
                sop = f.read()
        except FileNotFoundError:
            sop = "Generate Playwright tests using Page Object Model."

        ctx = self.context_manager.get_full_context()
        target_url = ctx.get("target_app_url") or os.getenv("TARGET_APP_URL", "http://localhost:3000")

        system_prompt = (
            f"{sop}\n\n"
            f"Target URL is: {target_url}\n"
            "IMPORTANT FORMAT RULES:\n"
            "- Each spec file must contain ONE or MORE test('description', async ({ page }) => {{ ... }}) blocks.\n"
            "- NEVER place await or page references at the top level of the file.\n"
            "- Every test block must import { test, expect } from '@playwright/test'.\n"
            "- Every test MUST contain real assertions (expect()). NEVER use placeholder comments.\n"
            "- Credentials: username=standard_user, password=secret_sauce (for valid login tests).\n"
            "Return a JSON object with a 'files' array. Each file MUST have 'path' (e.g., 'tests/pages/LoginPage.ts' or 'tests/specs/login.spec.ts') and 'content' (raw TS code string).\n"
            "Also return a 'scripts' array of metadata: { 'id': 'SCR-001', 'test_case_id': 'TC-001', 'file_path': 'tests/specs/login.spec.ts', 'page_objects': ['tests/pages/LoginPage.ts'] }"
        )

        user_prompt = f"Generate Playwright TS scripts for these test cases:\n{json.dumps(test_cases, indent=2)}"

        output = self.llm_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1
        )
        
        files = output.get("files", [])
        scripts_meta = output.get("scripts", [])

        # Write files to disk
        for file_data in files:
            file_path = Path(file_data["path"])
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_data["content"])
            print(f"[FILE] Created: {file_path}")

        # Add initial status fields to scripts
        for script in scripts_meta:
            script["status"] = "pending"
            script["retry_count"] = 0
            script["error_log"] = None
            script["screenshot_path"] = None
            script["execution_time_ms"] = 0

        self.context_manager.update_scripts(scripts_meta)
        print(f"[OK] Generated {len(scripts_meta)} executable scripts.")
