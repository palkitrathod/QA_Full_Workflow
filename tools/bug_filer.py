import json
import datetime
import os
from pathlib import Path
from .context_manager import ContextManager
from .llm_client import LLMClient
from .jira_client import JiraClient
from .slack_notifier import SlackNotifier

class BugFiler:
    """
    Analyzes failed tests, files bugs in JIRA or local file.
    Set LOCAL_BUGS_FILE env var to write bugs to a local markdown file instead of JIRA.
    """

    def __init__(self):
        self.context_manager = ContextManager()
        self.llm_client = LLMClient()
        self.jira_client = JiraClient()
        self.slack_notifier = SlackNotifier()
        self.local_file = os.getenv("LOCAL_BUGS_FILE")

    def run(self):
        self.context_manager.update_status("filing_bugs")
        ctx = self.context_manager.get_full_context()
        scripts = ctx.get("scripts", [])
        test_cases = ctx.get("test_cases", [])
        bugs = ctx.get("bugs", [])
        source_ticket_id = ctx.get("source_ticket_id")

        failed_scripts = [s for s in scripts if s.get("status") == "failed"]

        if not failed_scripts:
            print("No failed scripts. Skipping bug filing.")
            return

        try:
            with open("architecture/bug_filer.md", "r") as f:
                sop = f.read()
        except FileNotFoundError:
            sop = "Analyze test failures and generate bug reports."

        for script in failed_scripts:
            tc_id = script.get("test_case_id")
            tc = next((t for t in test_cases if t.get("id") == tc_id), {})

            error_log = script.get("error_log", "Unknown error")

            system_prompt = (
                f"{sop}\n\n"
                "You are a QA engineer filing a detailed bug report. Return a JSON object for the bug matching this schema EXACTLY:\n"
                "{ 'title': 'string', 'severity': 'P0|P1|P2|P3', 'component': 'string', 'error_message': 'string', "
                "'url': 'string', 'steps_to_reproduce': ['string'], 'expected_result': 'string', 'actual_result': 'string', "
                "'environment': 'string', 'test_data_used': 'string' }\n\n"
                "RULES:\n"
                "- Title must start with '[Test]' prefix followed by a concise description of the failure\n"
                "- Severity: P0=critical (app crash), P1=high (feature broken), P2=medium (feature partial), P3=low (cosmetic)\n"
                "- component should be the feature area (e.g. 'Login', 'Checkout', 'Cart')\n"
                "- steps_to_reproduce must be detailed step-by-step numbered actions\n"
                "- expected_result and actual_result must be explicit and measurable\n"
                "- url should be the application URL where the bug was found\n"
                "- environment should specify browser and OS\n"
                "- error_message should include the full error from the test log\n"
                "- test_data_used should document what test data/credentials were used"
            )

            user_prompt = f"Test Case Intent:\n{json.dumps(tc, indent=2)}\n\nError Log:\n{error_log}"

            try:
                bug_data = self.llm_client.generate_json(system_prompt, user_prompt)

                bug_data["test_case_id"] = tc_id
                bug_data["script_id"] = script.get("id")
                bug_data["filed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

                if self.local_file:
                    bug_data["is_duplicate"] = False
                    bug_data["jira_ticket_id"] = f"BUG-LOCAL-{tc_id}"
                    bug_data["jira_ticket_url"] = self.local_file

                    markdown_entry = (
                        f"## Bug Report: {bug_data.get('title', f'Bug in {tc_id}')}\n\n"
                        f"- **Test Case:** {tc_id}\n"
                        f"- **Severity:** {bug_data.get('severity', 'N/A')}\n"
                        f"- **Component:** {bug_data.get('component', 'N/A')}\n"
                        f"- **Application URL:** {bug_data.get('url', 'N/A')}\n"
                        f"- **Environment:** {bug_data.get('environment', 'N/A')}\n"
                        f"- **Test Data Used:** {bug_data.get('test_data_used', 'N/A')}\n\n"
                        f"### Steps to Reproduce\n"
                        + "\n".join(f"1. {step}" for step in bug_data.get("steps_to_reproduce", ["Not provided"])) + "\n\n"
                        f"### Expected Result\n{bug_data.get('expected_result', 'N/A')}\n\n"
                        f"### Actual Result\n{bug_data.get('actual_result', 'N/A')}\n\n"
                        f"### Error Log\n```\n{bug_data.get('error_message', 'N/A')}\n```\n\n"
                        f"---\n"
                    )

                    with open(self.local_file, "a", encoding="utf-8") as f:
                        f.write(markdown_entry)

                    print(f"[BUG LOCAL] Written bug for {tc_id} to {self.local_file}")

                else:
                    duplicates = self.jira_client.search_duplicates(
                        component=bug_data.get("component", ""),
                        error_message=bug_data.get("error_message", ""),
                        url=bug_data.get("url", "")
                    )

                    if duplicates:
                        dup = duplicates[0]
                        print(f"[DUP] Found duplicate for {tc_id}: {dup['key']}")
                        bug_data["is_duplicate"] = True
                        bug_data["duplicate_of"] = dup["key"]
                        bug_data["jira_ticket_id"] = dup["key"]
                        bug_data["jira_ticket_url"] = dup["url"]

                        comment = (
                            f"*Regression Detected — {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*\n"
                            f"Test Case: {tc_id}\n"
                            f"Error: {bug_data.get('error_message', 'N/A')}\n"
                            f"Environment: {bug_data.get('environment', 'N/A')}\n"
                            f"Test Data: {bug_data.get('test_data_used', 'N/A')}"
                        )
                        self.jira_client.add_comment(dup["key"], comment)
                    else:
                        header = (
                            f"h2. Bug Report — {tc.get('title', 'N/A')}\n\n"
                            f"*Source Test Case:* {tc_id}\n"
                            f"*Environment:* {bug_data.get('environment', 'Not specified')}\n"
                            f"*Test Data Used:* {bug_data.get('test_data_used', 'Not specified')}\n"
                            f"*Application URL:* {bug_data.get('url', 'N/A')}\n\n"
                        )
                        steps_section = "h3. Steps to Reproduce:\n" + "\n".join(
                            f"# {step}" for step in bug_data.get("steps_to_reproduce", ["Not provided"])
                        ) + "\n\n"
                        results_section = (
                            f"h3. Expected Result:\n{bug_data.get('expected_result', 'N/A')}\n\n"
                            f"h3. Actual Result:\n{bug_data.get('actual_result', 'N/A')}\n\n"
                        )
                        error_section = f"h3. Error Log:\n{{code}}{bug_data.get('error_message', 'N/A')}{{code}}\n\n"
                        footer = (
                            "---\n"
                            "h3. Additional Context:\n"
                            f"- Automation Run: QA Workflow AI Agent\n"
                            f"- Reported: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
                            f"- Linked To: {source_ticket_id or 'N/A'}"
                        )
                        desc = header + steps_section + results_section + error_section + footer

                        issue = self.jira_client.create_issue(
                            summary=bug_data.get("title", f"[Test] Bug in {tc_id}"),
                            description=desc,
                            priority="High" if bug_data.get("severity") in ["P0", "P1"] else "Medium",
                            component=bug_data.get("component")
                        )

                        print(f"[BUG] Filed new bug for {tc_id}: {issue['key']}")
                        bug_data["is_duplicate"] = False
                        bug_data["jira_ticket_id"] = issue["key"]
                        bug_data["jira_ticket_url"] = issue["url"]

                        if source_ticket_id:
                            self.jira_client.link_issues(source_ticket_id, issue["key"], "Blocks")

                    if bug_data.get("severity") in ["P0", "P1"]:
                        self.slack_notifier.send_bug_alert(bug_data)
                        bug_data["slack_alerted"] = True
                    else:
                        bug_data["slack_alerted"] = False

                bugs.append(bug_data)

            except Exception as e:
                print(f"Failed to process bug for {tc_id}: {e}")

        self.context_manager.update_bugs(bugs)
        print(f"[OK] Processed {len(failed_scripts)} failed scripts into bugs.")
