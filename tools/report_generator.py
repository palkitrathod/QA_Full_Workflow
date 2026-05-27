import datetime
import os
from .context_manager import ContextManager
from .llm_client import LLMClient
from .slack_notifier import SlackNotifier
from .jira_client import JiraClient

class ReportGenerator:
    """
    Generates QA report and delivers it to Slack and JIRA.
    """
    
    def __init__(self):
        self.context_manager = ContextManager()
        self.llm_client = LLMClient()
        self.slack_notifier = SlackNotifier()
        self.jira_client = JiraClient()

    def run(self):
        self.context_manager.update_status("reporting")
        ctx = self.context_manager.get_full_context()
        
        scripts = ctx.get("scripts", [])
        test_cases = ctx.get("test_cases", [])
        requirements = ctx.get("requirements", [])
        bugs = ctx.get("bugs", [])
        evaluations = ctx.get("evaluations", [])
        
        # Calculate metrics
        total_tc = len(test_cases)
        passed = sum(1 for s in scripts if s.get("status") == "passed")
        failed = sum(1 for s in scripts if s.get("status") == "failed")
        error = sum(1 for s in scripts if s.get("status") == "error")
        skipped = sum(1 for s in scripts if s.get("status") in ["skipped", "pending"])
        
        pass_rate = (passed / total_tc * 100) if total_tc > 0 else 0
        
        reqs_with_tests = set([tc.get("requirement_id") for tc in test_cases])
        coverage_pct = (len(reqs_with_tests) / len(requirements) * 100) if requirements else 0
        
        bug_summary = {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "total": len(bugs)}
        for b in bugs:
            sev = b.get("severity")
            if sev in bug_summary:
                bug_summary[sev] += 1
                
        # Generate Summary
        system_prompt = "You are the Report Generator. Write a brief, professional, data-first summary (1 paragraph) of the QA run based on the metrics. State if the build is stable or unstable based on P0/P1 bugs."
        user_prompt = f"Metrics: Total Tests: {total_tc}, Pass Rate: {pass_rate}%, P0 Bugs: {bug_summary['P0']}, P1 Bugs: {bug_summary['P1']}"
        
        try:
            summary_response = self.llm_client.generate_json(
                system_prompt + " Return JSON: {'summary': 'string'}", 
                user_prompt, 
                temperature=0.3
            )
            summary_text = summary_response.get("summary", "QA Run Completed.")
        except Exception:
            summary_text = f"QA Run Completed. Pass Rate: {pass_rate:.1f}%. Total Bugs: {bug_summary['total']}."
            
        report = {
            "total_test_cases": total_tc,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "error": error,
            "coverage_pct": coverage_pct,
            "pass_rate": pass_rate,
            "bug_summary": bug_summary,
            "evaluations": evaluations,
            "allure_report_url": os.getenv("GITHUB_PAGES_URL", "file://allure-report/index.html"),
            "summary": summary_text,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "slack_delivered": False,
            "jira_comment_posted": False
        }
        
        # Deliver to Slack
        slack_resp = self.slack_notifier.send_report(report, ctx.get("run_id", "N/A"))
        if slack_resp.get("status") == "sent":
            report["slack_delivered"] = True
            
        # Deliver to JIRA
        source_ticket_id = ctx.get("source_ticket_id")
        if source_ticket_id:
            try:
                comment = f"🤖 *QA Automation Run Completed*\n\n{summary_text}\n\n* Pass Rate: {pass_rate:.1f}%\n* Passed: {passed}\n* Failed: {failed}\n* Bugs Filed: {bug_summary['total']}"
                self.jira_client.add_comment(source_ticket_id, comment)
                report["jira_comment_posted"] = True
            except Exception as e:
                print(f"Failed to post JIRA comment: {e}")
                
        self.context_manager.update_report(report)
        self.context_manager.update_status("completed")
        print("[OK] Report generated and delivered.")
