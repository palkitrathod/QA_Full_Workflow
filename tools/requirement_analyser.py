import os
import json
from .context_manager import ContextManager
from .llm_client import LLMClient
from .jira_client import JiraClient
from .document_parser import DocumentParser

class RequirementAnalyser:
    """
    Extracts structured requirements from JIRA or Document.
    Updates context.json with requirements.
    """
    
    def __init__(self):
        self.context_manager = ContextManager()
        self.llm_client = LLMClient()

    def run(self):
        self.context_manager.update_status("analysing")
        ctx = self.context_manager.get_full_context()
        input_mode = ctx.get("input_mode")
        
        raw_text = ""
        
        if input_mode == "jira":
            ticket_id = ctx.get("source_ticket_id")
            ticket_data = JiraClient().fetch_ticket(ticket_id)
            raw_text = json.dumps(ticket_data, indent=2)
            
        elif input_mode == "document":
            doc_path = ctx.get("document_path") # Assuming we set this in context during init
            raw_text = DocumentParser.parse(doc_path)
            
        else:
            raise ValueError(f"Unknown input_mode: {input_mode}")
            
        if not raw_text.strip():
            raise ValueError("Requirement Analyser found no content to parse.")
            
        # Read architecture SOP prompt
        try:
            with open("architecture/requirement_analyser.md", "r") as f:
                sop = f.read()
        except FileNotFoundError:
            sop = "Extract testable requirements as JSON array."
            
        system_prompt = (
            f"{sop}\n\n"
            "Return a JSON object with a 'requirements' array and a 'target_app_url' string (if found). Each requirement MUST match the schema: "
            "{ 'id': 'REQ-001', 'title': 'string', 'description': 'string', 'acceptance_criteria': ['string'], 'priority': 'P0|P1|P2|P3', 'source': 'string' }. "
            "If the Target URL is not found, set 'target_app_url' to null."
        )
        
        if os.getenv("DRY_RUN") == "1":
            # Provide dummy requirements for dry-run to allow pipeline progression
            dummy_requirements = [
                {
                    "id": "REQ-001",
                    "title": "Sample Requirement",
                    "description": "A dummy requirement for dry-run.",
                    "acceptance_criteria": ["Criteria 1", "Criteria 2"],
                    "priority": "P2",
                    "source": "dry-run"
                }
            ]
            self.context_manager.update_requirements(dummy_requirements)
            print("[DRY RUN] Generated dummy requirements.")
            return
        
        # Call LLM to extract requirements and target URL
        output = self.llm_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=f"Extract requirements and target URL from this text:\n\n{raw_text}",
            temperature=0.1
        )
        requirements = output.get("requirements", [])
        target_app_url = output.get("target_app_url")
        if not requirements:
            raise ValueError("Requirement Analyser returned 0 requirements from LLM. Aborting pipeline.")
        self.context_manager.update_requirements(requirements)
        if target_app_url:
            self.context_manager.update_target_app_url(target_app_url)
            print(f"[OK] Extracted Target URL: {target_app_url}")
        print(f"[OK] Extracted {len(requirements)} requirements.")
