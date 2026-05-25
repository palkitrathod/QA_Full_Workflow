"""
GitHub API Client
=================
Handles interaction with GitHub repositories:
- Committing generated Playwright scripts
- Creating branches
- Pushing updates

Uses PyGithub library for REST API interactions.
"""

import os
import sys
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

try:
    from github import Github, GithubException
    from github import Auth
except ImportError:
    print("ERROR: 'PyGithub' package not installed. Run: pip install PyGithub")
    sys.exit(1)


class GithubClient:
    """GitHub API client for committing test scripts."""

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo_name = os.getenv("GITHUB_REPO")
        self.owner = os.getenv("GITHUB_OWNER")

        # In dev/test scenarios, we might want to bypass if not configured yet
        self.is_configured = bool(self.token and self.repo_name and self.owner)
        
        if self.is_configured:
            auth = Auth.Token(self.token)
            self.client = Github(auth=auth)
            self.repo_full_name = f"{self.owner}/{self.repo_name}"
        else:
            self.client = None
            self.repo_full_name = None

    def verify_connection(self) -> dict:
        """Test GitHub API connectivity and repository access."""
        if not self.is_configured:
            return {
                "status": "skipped",
                "message": "GitHub credentials not fully configured in .env"
            }
            
        try:
            # Check authentication
            user = self.client.get_user()
            username = user.login
            
            # Check repo access
            repo = self.client.get_repo(self.repo_full_name)
            
            return {
                "status": "connected",
                "user": username,
                "repo": repo.full_name,
                "default_branch": repo.default_branch,
                "permissions": {
                    "push": repo.permissions.push,
                    "pull": repo.permissions.pull,
                    "admin": repo.permissions.admin
                }
            }
        except GithubException as e:
            return {
                "status": "error",
                "status_code": e.status,
                "error": e.data.get("message", str(e)) if hasattr(e, "data") else str(e)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def commit_files(self, branch: str, commit_message: str, files: List[Dict[str, str]]) -> dict:
        """
        Commit multiple files to a specific branch.
        
        Args:
            branch: Name of the branch to commit to.
            commit_message: The commit message.
            files: List of dicts with 'path' and 'content' keys.
        """
        if not self.is_configured:
            return {"status": "skipped", "message": "Not configured"}
            
        try:
            repo = self.client.get_repo(self.repo_full_name)
            
            # Get the branch reference
            try:
                ref = repo.get_git_ref(f"heads/{branch}")
            except GithubException:
                # If branch doesn't exist, create it from default branch
                default_branch = repo.default_branch
                base_ref = repo.get_git_ref(f"heads/{default_branch}")
                ref = repo.create_git_ref(f"refs/heads/{branch}", base_ref.object.sha)
                
            # Get the tree of the branch
            base_commit = repo.get_git_commit(ref.object.sha)
            base_tree = base_commit.tree
            
            # Create blobs and new tree elements
            elements = []
            for file_data in files:
                blob = repo.create_git_blob(file_data["content"], "utf-8")
                # Add to tree elements list
                from github.InputGitTreeElement import InputGitTreeElement
                element = InputGitTreeElement(file_data["path"], "100644", "blob", sha=blob.sha)
                elements.append(element)
                
            # Create new tree
            new_tree = repo.create_git_tree(elements, base_tree)
            
            # Create new commit
            new_commit = repo.create_git_commit(commit_message, new_tree, [base_commit])
            
            # Update the reference
            ref.edit(new_commit.sha)
            
            return {
                "status": "success",
                "commit_sha": new_commit.sha,
                "branch": branch,
                "files_changed": len(files)
            }
            
        except GithubException as e:
            raise RuntimeError(f"GitHub API error: {e.data.get('message', str(e))}")
        except Exception as e:
            raise RuntimeError(f"Failed to commit files: {e}")


# ─── CLI Verification Entry Point ──────────────────────────────────────
def main():
    """Run GitHub API connection verification from CLI."""
    from rich.console import Console

    console = Console()
    console.print("\n[bold cyan]🔗 GitHub API Connection Test[/bold cyan]\n")

    client = GithubClient()
    result = client.verify_connection()

    if result["status"] == "connected":
        console.print("[green]✅ GitHub connection verified[/green]")
        console.print(f"   User: {result['user']}")
        console.print(f"   Repository: {result['repo']}")
        console.print(f"   Default Branch: {result['default_branch']}")
        
        # Check push permissions
        perms = result.get("permissions", {})
        if perms.get("push"):
            console.print("   [green]Push Access: Yes[/green]")
        else:
            console.print("   [red]Push Access: No (Warning: Cannot save test scripts)[/red]")
            
    elif result["status"] == "skipped":
        console.print("[yellow]⚠️  GitHub integration skipped[/yellow]")
        console.print(f"   {result['message']}")
        console.print("   (Tests will only be saved locally in the tests/ directory)")
    else:
        console.print(f"[red]❌ GitHub connection failed: {result.get('error', 'Unknown error')}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
