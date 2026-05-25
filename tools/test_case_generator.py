import json
from .context_manager import ContextManager
from .llm_client import LLMClient

class TestCaseGenerator:
    """
    Generates test cases from parsed requirements.
    Updates context.json.
    """
    
    def __init__(self):
        self.context_manager = ContextManager()
        self.llm_client = LLMClient()

    def run(self):
        self.context_manager.update_status("generating_cases")
        requirements = self.context_manager.get_requirements()
        
        if not requirements:
            print("No requirements found to generate test cases.")
            return

        try:
            with open("architecture/test_case_generator.md", "r") as f:
                sop = f.read()
        except FileNotFoundError:
            sop = "Generate test cases for the given requirements."

        system_prompt = (
            f"{sop}\n\n"
            "IMPORTANT: Generate FUNCTIONAL/BUSINESS-LOGIC test cases (e.g., login flows, add to cart, checkout, "
            "error handling, data validation), NOT just UI element existence checks. "
            "Focus on user workflows and application behavior. Avoid trivial tests like 'Verify element X is displayed'.\n\n"
            "Return a JSON object with a 'test_cases' array. Each test case MUST match the schema: "
            "{ 'id': 'TC-001', 'requirement_id': 'REQ-001', 'title': 'string', 'type': 'positive|negative|edge_case|regression', 'preconditions': ['string'], 'steps': [{ 'step_number': 1, 'action': 'string', 'expected_result': 'string' }], 'priority': 'P0|P1|P2|P3' }"
        )

        user_prompt = f"Generate test cases for these requirements:\n{json.dumps(requirements, indent=2)}"

        output = self.llm_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2
        )
        
        test_cases = output.get("test_cases", [])
        self.context_manager.update_test_cases(test_cases)
        
        # Write test cases to a separate markdown file
        try:
            with open("generated_test_cases.md", "w", encoding="utf-8") as f:
                f.write("# Generated Test Cases\n\n")
                f.write(f"Source: {self.context_manager.get_full_context().get('source_ticket_id', 'N/A')}\n")
                f.write(f"Total: {len(test_cases)}\n\n")
                f.write("---\n\n")
                for tc in test_cases:
                    f.write(f"## {tc.get('id')}: {tc.get('title')}\n")
                    f.write(f"- **Requirement:** {tc.get('requirement_id')}\n")
                    f.write(f"- **Type:** {tc.get('type')}\n")
                    f.write(f"- **Priority:** {tc.get('priority')}\n")
                    steps = tc.get('steps', [])
                    if steps:
                        f.write("- **Steps:**\n")
                        for s in steps:
                            f.write(f"  - Step {s.get('step_number')}: {s.get('action')}\n")
                            f.write(f"    → Expected: {s.get('expected_result')}\n")
                    f.write("\n")
            print(f"[FILE] Created: generated_test_cases.md")
        except Exception as e:
            print(f"[WARN] Could not write test cases file: {e}")
            
        print(f"[OK] Generated {len(test_cases)} test cases.")
