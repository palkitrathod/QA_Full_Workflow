import json
import os
from typing import Any, Dict

try:
    from functions import call_mcp_tool
except Exception:  # pragma: no cover
    call_mcp_tool = None  # type: ignore

def mcp_call(*, ServerName: str, ToolName: str, Arguments: Dict[str, Any], toolAction: str = "MCP call", toolSummary: str = "Invoke MCP tool") -> Any:
    """Convenience wrapper to call a lazy-loaded MCP tool.

    In dry‑run mode (environment variable ``DRY_RUN=1``), a minimal stub response is returned to allow the pipeline to proceed without contacting external services.
    """
    # Dry‑run shortcut – return a generic placeholder structure.
    if os.getenv("DRY_RUN") == "1":
        # Provide a minimal shape expected by callers (e.g., RequirementAnalyser expects .get on dict).
        return {"fields": {"summary": "Dummy issue for dry run", "customfield_target_url": "https://example.com", "customfield_scope": "default", "customfield_e2e_flow": "Login,Cart,Checkout"}}

    if not call_mcp_tool:
        # If MCP tooling is unavailable (e.g., during local dry‑run), return a generic placeholder.
        # This mimics the structure expected by callers.
        return {"fields": {"summary": "Dummy issue for dry run", "customfield_target_url": "https://example.com", "customfield_scope": "default", "customfield_e2e_flow": "Login,Cart,Checkout"}}


    result = call_mcp_tool(
        Arguments=Arguments,
        ServerName=ServerName,
        ToolName=ToolName,
        toolAction=toolAction,
        toolSummary=toolSummary,
    )
    try:
        return json.loads(result) if isinstance(result, str) else result
    except Exception:
        return result

