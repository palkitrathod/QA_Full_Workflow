from pydantic import BaseModel
from typing import Optional


class RunRequest(BaseModel):
    mode: str = "document"  # "document" or "jira"
    document_path: Optional[str] = None
    jira_ticket_id: Optional[str] = None
    target_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    run_type: str = "verification"


class RunStatus(BaseModel):
    run_id: str
    status: str  # pending, running, completed, failed, aborted
    progress: str = ""
    overall_accuracy: Optional[float] = None


class RunSummary(BaseModel):
    run_id: str
    status: str
    created_at: str
    overall_accuracy: Optional[float] = None
    source: str = ""
