"""
Slack Notification Client
=========================
Handles Slack messaging for the QA Workflow AI Agent:
- Real-time P0/P1 bug alerts via webhook
- Final QA report delivery via Block Kit formatted messages

Uses slack_sdk WebhookClient for webhook-based messaging.
"""

import os
import json
import sys
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from slack_sdk.webhook import WebhookClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    print("ERROR: 'slack-sdk' package not installed. Run: pip install slack-sdk")
    sys.exit(1)


# Severity emoji mapping per gemini.md Rule 2.3
SEVERITY_EMOJI = {
    "P0": "🔴",
    "P1": "🟠",
    "P2": "🟡",
    "P3": "🔵",
}

SEVERITY_LABELS = {
    "P0": "CRITICAL — Application crash or data loss",
    "P1": "HIGH — Broken core user flow",
    "P2": "MEDIUM — Degraded or incorrect UX",
    "P3": "LOW — Cosmetic issue",
}


class SlackNotifier:
    """Slack webhook client for QA alerts and reports."""

    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.alert_channel = os.getenv("SLACK_ALERT_CHANNEL", "#qa-alerts")
        self.report_channel = os.getenv("SLACK_REPORT_CHANNEL", "#qa-reports")
        self.enabled = bool(self.webhook_url and self.webhook_url.strip())

        if self.enabled:
            self.client = WebhookClient(self.webhook_url)
        else:
            self.client = None

    def verify_connection(self) -> dict:
        """Test Slack webhook connectivity with a minimal message."""
        if not self.enabled:
            return {"status": "disabled", "message": "Slack not configured (SLACK_WEBHOOK_URL missing)"}
        try:
            response = self.client.send(
                text="🔗 QA Workflow AI Agent — Slack connection verified ✅",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🔗 *QA Workflow AI Agent* — Slack connection verified ✅\n_This is a test message from the Link phase._",
                        },
                    }
                ],
            )
            return {
                "status": "connected" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "body": response.body,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def send_bug_alert(self, bug: dict) -> dict:
        """
        Send a real-time Slack alert for a P0/P1 bug.
        Per gemini.md Rule 2.9: Real-time for P0/P1 bugs (don't wait for run completion).

        Args:
            bug: Bug object from context.json matching the bugs[] schema.
        """
        if not self.enabled:
            return {"status": "disabled", "message": "Slack not configured"}
        severity = bug.get("severity", "P2")
        emoji = SEVERITY_EMOJI.get(severity, "⚪")
        label = SEVERITY_LABELS.get(severity, "Unknown severity")

        # Build steps to reproduce string
        steps = bug.get("steps_to_reproduce", [])
        steps_text = "\n".join(
            [f"{i+1}. {step}" for i, step in enumerate(steps)]
        ) if steps else "_No steps provided_"

        jira_url = bug.get("jira_ticket_url", "")
        jira_link = f"<{jira_url}|{bug.get('jira_ticket_id', 'N/A')}>" if jira_url else "Not yet filed"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {severity} Bug Detected",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Bug Title:*\n{bug.get('title', 'Untitled')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{emoji} {label}",
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Component:*\n{bug.get('component', 'Unknown')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*JIRA Ticket:*\n{jira_link}",
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*URL:*\n{bug.get('url', 'N/A')}",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Steps to Reproduce:*\n{steps_text}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Expected:*\n{bug.get('expected_result', 'N/A')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Actual:*\n{bug.get('actual_result', 'N/A')}",
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🤖 QA Workflow AI Agent | Test Case: {bug.get('test_case_id', 'N/A')}",
                    }
                ],
            },
        ]

        try:
            response = self.client.send(
                text=f"{emoji} {severity} Bug: {bug.get('title', 'Untitled')}",
                blocks=blocks,
            )
            return {
                "status": "sent" if response.status_code == 200 else "error",
                "status_code": response.status_code,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def send_report(self, report: dict, run_id: str = "") -> dict:
        """
        Send the final QA report to Slack.

        Args:
            report: Report object from context.json matching the report schema.
            run_id: The pipeline run ID for reference.
        """
        if not self.enabled:
            return {"status": "disabled", "message": "Slack not configured"}
        bug_summary = report.get("bug_summary", {})
        total_bugs = bug_summary.get("total", 0)

        # Build severity breakdown
        severity_lines = []
        for level in ["P0", "P1", "P2", "P3"]:
            count = bug_summary.get(level, 0)
            if count > 0:
                emoji = SEVERITY_EMOJI.get(level, "⚪")
                severity_lines.append(f"{emoji} {level}: {count}")

        severity_text = "\n".join(severity_lines) if severity_lines else "No bugs found ✅"

        pass_rate = report.get("pass_rate", 0)
        pass_emoji = "✅" if pass_rate >= 90 else "⚠️" if pass_rate >= 70 else "❌"

        allure_url = report.get("allure_report_url")
        allure_text = f"<{allure_url}|View Full Allure Report>" if allure_url else "_Report generated locally_"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 QA Automation Report",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": report.get("summary", "_No summary available_"),
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Test Cases:*\n{report.get('total_test_cases', 0)}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Pass Rate:*\n{pass_emoji} {pass_rate:.1f}%",
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*✅ Passed:* {report.get('passed', 0)}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*❌ Failed:* {report.get('failed', 0)}",
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*⏭️ Skipped:* {report.get('skipped', 0)}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*💥 Errors:* {report.get('error', 0)}",
                    },
                ],
            },
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Coverage:*\n{report.get('coverage_pct', 0):.1f}%",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Bugs:*\n{total_bugs}",
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Bug Breakdown:*\n{severity_text}",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📎 *Allure Report:*\n{allure_text}",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🤖 QA Workflow AI Agent | Run: `{run_id}` | {report.get('generated_at', 'N/A')}",
                    }
                ],
            },
        ]

        try:
            response = self.client.send(
                text=f"📊 QA Report — Pass Rate: {pass_rate:.1f}% | Bugs: {total_bugs}",
                blocks=blocks,
            )
            return {
                "status": "sent" if response.status_code == 200 else "error",
                "status_code": response.status_code,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def send_human_review_request(self, scripts: list, run_id: str = "") -> dict:
        """
        Send a Slack notification requesting human review of generated scripts.
        Per open question #5 answer: Option C — Both Slack notification + CLI approval.
        """
        if not self.enabled:
            return {"status": "disabled", "message": "Slack not configured"}
        script_list = "\n".join(
            [f"• `{s.get('file_path', 'unknown')}` (Test Case: {s.get('test_case_id', 'N/A')})"
             for s in scripts]
        )

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "👁️ Human Review Required",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{len(scripts)} Playwright scripts* have been generated "
                        f"and require your review before execution.\n\n"
                        f"*Scripts:*\n{script_list}"
                    ),
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "⏳ *The pipeline is paused.* Please review the scripts and approve via the CLI.",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🤖 QA Workflow AI Agent | Run: `{run_id}`",
                    }
                ],
            },
        ]

        try:
            response = self.client.send(
                text=f"👁️ Human Review Required — {len(scripts)} scripts awaiting approval",
                blocks=blocks,
            )
            return {
                "status": "sent" if response.status_code == 200 else "error",
                "status_code": response.status_code,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def send_abort_notification(self, reason: str, run_id: str = "") -> dict:
        """Send notification that the pipeline run has been aborted."""
        if not self.enabled:
            return {"status": "disabled", "message": "Slack not configured"}
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🛑 QA Pipeline Aborted",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Reason:*\n{reason}",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🤖 QA Workflow AI Agent | Run: `{run_id}`",
                    }
                ],
            },
        ]

        try:
            response = self.client.send(
                text=f"🛑 QA Pipeline Aborted: {reason}",
                blocks=blocks,
            )
            return {
                "status": "sent" if response.status_code == 200 else "error",
                "status_code": response.status_code,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# ─── CLI Verification Entry Point ──────────────────────────────────────
def main():
    """Run Slack webhook connection verification from CLI."""
    from rich.console import Console

    console = Console()
    console.print("\n[bold cyan]🔗 Slack Webhook Connection Test[/bold cyan]\n")

    try:
        notifier = SlackNotifier()
        result = notifier.verify_connection()

        if result["status"] == "connected":
            console.print("[green]✅ Slack webhook is active and responding[/green]")
            console.print(f"   Status Code: {result['status_code']}")
            console.print(f"   Response: {result['body']}")
        else:
            console.print(f"[red]❌ Slack connection failed: {result.get('error', 'Unknown error')}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
