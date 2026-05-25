"""
JIRA REST API Client
====================
Handles all JIRA interactions: fetching tickets, creating issues,
linking issues, adding comments, and searching for duplicates.

Uses Basic Auth with email + API token per Atlassian Cloud REST API v3.
"""

import os
import json
import sys
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from jira import JIRA, JIRAError
except ImportError:
    print("ERROR: 'jira' package not installed. Run: pip install jira")
    sys.exit(1)


class JiraClient:
    """JIRA REST API client for the QA Workflow AI Agent."""

    def __init__(self):
        self.base_url = os.getenv("JIRA_BASE_URL")
        self.email = os.getenv("JIRA_EMAIL")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "SCRUM")

        if not all([self.base_url, self.email, self.api_token]):
            raise ValueError(
                "Missing JIRA credentials. Ensure JIRA_BASE_URL, JIRA_EMAIL, "
                "and JIRA_API_TOKEN are set in .env"
            )

        self.client = JIRA(
            server=self.base_url,
            basic_auth=(self.email, self.api_token),
        )

    def verify_connection(self) -> dict:
        """Test JIRA API connectivity. Returns server info on success."""
        try:
            server_info = self.client.server_info()
            return {
                "status": "connected",
                "server": server_info.get("baseUrl"),
                "version": server_info.get("version"),
                "deployment_type": server_info.get("deploymentType"),
            }
        except JIRAError as e:
            return {
                "status": "error",
                "error": str(e),
                "status_code": getattr(e, "status_code", None),
            }

    def fetch_ticket(self, ticket_id: str) -> dict:
        """
        Fetch a JIRA ticket by its ID (e.g., 'SCRUM-1').
        Returns structured ticket data including description,
        acceptance criteria, and linked subtasks.
        """
        try:
            issue = self.client.issue(ticket_id)
            fields = issue.fields

            # Extract subtasks
            subtasks = []
            if hasattr(fields, "subtasks") and fields.subtasks:
                for subtask in fields.subtasks:
                    subtasks.append({
                        "key": subtask.key,
                        "summary": subtask.fields.summary,
                        "status": str(subtask.fields.status),
                    })

            # Extract linked issues
            linked_issues = []
            if hasattr(fields, "issuelinks") and fields.issuelinks:
                for link in fields.issuelinks:
                    linked = {}
                    if hasattr(link, "outwardIssue"):
                        linked = {
                            "key": link.outwardIssue.key,
                            "summary": link.outwardIssue.fields.summary,
                            "type": link.type.outward,
                        }
                    elif hasattr(link, "inwardIssue"):
                        linked = {
                            "key": link.inwardIssue.key,
                            "summary": link.inwardIssue.fields.summary,
                            "type": link.type.inward,
                        }
                    if linked:
                        linked_issues.append(linked)

            # Extract acceptance criteria from description or custom field
            description = fields.description or ""
            acceptance_criteria = ""
            if hasattr(fields, "customfield_10035"):  # Common AC field
                acceptance_criteria = fields.customfield_10035 or ""

            return {
                "key": issue.key,
                "summary": fields.summary,
                "description": description,
                "acceptance_criteria": acceptance_criteria,
                "issue_type": str(fields.issuetype),
                "status": str(fields.status),
                "priority": str(fields.priority) if fields.priority else "None",
                "assignee": str(fields.assignee) if fields.assignee else "Unassigned",
                "reporter": str(fields.reporter) if fields.reporter else "Unknown",
                "labels": fields.labels or [],
                "components": [str(c) for c in (fields.components or [])],
                "subtasks": subtasks,
                "linked_issues": linked_issues,
                "created": str(fields.created),
                "updated": str(fields.updated),
            }
        except JIRAError as e:
            raise RuntimeError(f"Failed to fetch ticket {ticket_id}: {e}")

    def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str = "Bug",
        priority: str = "Medium",
        component: Optional[str] = None,
        labels: Optional[list] = None,
    ) -> dict:
        """
        Create a new JIRA issue (typically a bug).
        Returns the created issue key and URL.
        """
        issue_dict = {
            "project": {"key": self.project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
        }

        if labels:
            issue_dict["labels"] = labels

        if component:
            issue_dict["components"] = [{"name": component}]

        try:
            new_issue = self.client.create_issue(fields=issue_dict)
            return {
                "key": new_issue.key,
                "url": f"{self.base_url}/browse/{new_issue.key}",
                "id": new_issue.id,
            }
        except JIRAError as e:
            raise RuntimeError(f"Failed to create issue: {e}")

    def link_issues(
        self, inward_key: str, outward_key: str, link_type: str = "Relates"
    ) -> bool:
        """
        Create a link between two JIRA issues.
        Common link types: 'Relates', 'Blocks', 'Duplicate', 'Causes'.
        """
        try:
            self.client.create_issue_link(
                type=link_type,
                inwardIssue=inward_key,
                outwardIssue=outward_key,
            )
            return True
        except JIRAError as e:
            raise RuntimeError(
                f"Failed to link {inward_key} -> {outward_key}: {e}"
            )

    def add_comment(self, ticket_id: str, comment_body: str) -> bool:
        """Add a comment to an existing JIRA ticket."""
        try:
            self.client.add_comment(ticket_id, comment_body)
            return True
        except JIRAError as e:
            raise RuntimeError(
                f"Failed to add comment to {ticket_id}: {e}"
            )

    def search_duplicates(
        self,
        component: str,
        error_message: str,
        url: str,
    ) -> list:
        """
        Search for existing JIRA tickets that match on component,
        error message, and URL — the three fields required for
        duplicate detection per gemini.md Rule 2.2.
        """
        # Build JQL query to search for potential duplicates
        jql_parts = [f'project = "{self.project_key}"', 'issuetype = "Bug"']

        if component:
            jql_parts.append(f'component = "{component}"')

        # Search in summary and description for error message keywords
        if error_message:
            # Escape special JQL characters and take first 100 chars
            safe_msg = error_message[:100].replace('"', '\\"')
            jql_parts.append(f'text ~ "{safe_msg}"')

        jql = " AND ".join(jql_parts)

        try:
            issues = self.client.search_issues(jql, maxResults=20)

            matches = []
            for issue in issues:
                desc = issue.fields.description or ""
                # Secondary filter: check if URL appears in description
                if url and url in desc:
                    matches.append({
                        "key": issue.key,
                        "summary": issue.fields.summary,
                        "status": str(issue.fields.status),
                        "url": f"{self.base_url}/browse/{issue.key}",
                    })

            return matches
        except JIRAError as e:
            raise RuntimeError(f"Failed to search for duplicates: {e}")

    def get_project_components(self) -> list:
        """Get all components for the configured project."""
        try:
            components = self.client.project_components(self.project_key)
            return [{"id": c.id, "name": c.name} for c in components]
        except JIRAError as e:
            raise RuntimeError(f"Failed to fetch components: {e}")


# ─── CLI Verification Entry Point ──────────────────────────────────────
def main():
    """Run JIRA API connection verification from CLI."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    console.print("\n[bold cyan]🔗 JIRA API Connection Test[/bold cyan]\n")

    try:
        client = JiraClient()
        result = client.verify_connection()

        if result["status"] == "connected":
            table = Table(title="JIRA Connection Verified ✅")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Server", result["server"])
            table.add_row("Version", result["version"])
            table.add_row("Deployment", result["deployment_type"])
            table.add_row("Project Key", client.project_key)
            console.print(table)

            # Also test fetching project info
            try:
                components = client.get_project_components()
                console.print(
                    f"\n[green]📦 Project components: {len(components)}[/green]"
                )
                for comp in components:
                    console.print(f"   • {comp['name']}")
            except Exception as e:
                console.print(f"\n[yellow]⚠️  Could not fetch components: {e}[/yellow]")

        else:
            console.print(f"[red]❌ Connection failed: {result['error']}[/red]")
            sys.exit(1)

    except ValueError as e:
        console.print(f"[red]❌ Configuration error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
