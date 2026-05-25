import json
import datetime
from .context_manager import ContextManager
from .llm_client import LLMClient
from .jira_client import JiraClient
from .slack_notifier import SlackNotifier

class BugFiler:
    """
    Analyzes failed tests, files bugs in JIRA, and sends Slack alerts.
    """
    
    def __init__(self):
        self.context_manager = ContextManager()
        self.llm_client = LLMClient()
        self.jira_client = JiraClient()
        self.slack_notifier = SlackNotifier()

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
                "Return a JSON object for the bug matching this schema: "
                "{ 'title': 'string', 'severity': 'P0|P1|P2|P3', 'component': 'string', 'error_message': 'string', 'url': 'string', 'steps_to_reproduce': ['string'], 'expected_result': 'string', 'actual_result': 'string' }"
            )
            
            user_prompt = f"Test Case Intent:\n{json.dumps(tc, indent=2)}\n\nError Log:\n{error_log}"
            
            try:
                bug_data = self.llm_client.generate_json(system_prompt, user_prompt)
                
                # Check for duplicates
                duplicates = self.jira_client.search_duplicates(
                    component=bug_data.get("component", ""),
                    error_message=bug_data.get("error_message", ""),
                    url=bug_data.get("url", "")
                )
                
                bug_data["test_case_id"] = tc_id
                bug_data["script_id"] = script.get("id")
                bug_data["filed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                
                if duplicates:
                    dup = duplicates[0]
                    print(f"[DUP] Found duplicate for {tc_id}: {dup['key']}")
                    bug_data["is_duplicate"] = True
                    bug_data["duplicate_of"] = dup["key"]
                    bug_data["jira_ticket_id"] = dup["key"]
                    bug_data["jira_ticket_url"] = dup["url"]
                    
                    self.jira_client.add_comment(dup["key"], f"Regression detected in test case {tc_id}.\nError: {bug_data.get('error_message')}")
                else:
                    # File new bug
                    desc = f"Steps to reproduce:\n" + "\n".join(bug_data.get("steps_to_reproduce", [])) + f"\n\nExpected: {bug_data.get('expected_result')}\nActual: {bug_data.get('actual_result')}\n\nError:\n{bug_data.get('error_message')}"
                    
                    issue = self.jira_client.create_issue(
                        summary=bug_data.get("title", f"Bug in {tc_id}"),
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
                        
                # Send Slack alert for P0/P1
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
