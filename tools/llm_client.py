import os
import json
from openai import OpenAI

class LLMClient:
    """
    Universal LLM client wrapper supporting OpenAI and Deepseek APIs.
    """
    
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL")
        self.model = os.getenv("LLM_MODEL", "gpt-4o")
        
        # If base_url is an empty string in .env, set it to None so openai defaults correctly
        if self.base_url and self.base_url.strip() == "":
            self.base_url = None
            
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            self.client = None

    def generate_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> dict:
        """
        Generates a JSON object from the LLM.
        Compatible with any OpenAI-compatible API.
        Uses prompt-based JSON instruction for broad compatibility.
        """
        if not self.client:
            raise ValueError("LLM_API_KEY is not configured.")
            
        try:
            json_instruction = "\n\nIMPORTANT: Return ONLY valid JSON. No markdown, no code fences, no explanation."
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt + json_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=4000,
            )
            
            content = response.choices[0].message.content.strip()
            # Remove markdown code fences if present
            if content.startswith("```"):
                content = content[content.find("\n")+1:]
                if content.endswith("```"):
                    content = content[:-3].strip()
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM JSON response: {e}\nResponse: {content[:500]}")
        except Exception as e:
            raise ValueError(f"LLM API Error: {e}")

def main():
    """CLI verification script for LLMClient."""
    import sys
    from rich.console import Console
    console = Console()
    
    console.print("\n[bold cyan]\U0001f517 LLM API Connection Test[/bold cyan]\n")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        client = LLMClient()
        if not client.client:
            console.print("⚠️  [yellow]LLM_API_KEY not configured. Skipping live test.[/yellow]")
            return
            
        console.print(f"🔄 Testing connection to [bold]{client.model}[/bold] via base URL: [bold]{client.base_url or 'default'}[/bold]...")
        
        response = client.generate_json(
            system_prompt="You are a JSON assistant. Respond with a JSON object.",
            user_prompt="Say 'Connection Verified' in a 'message' field."
        )
        
        console.print(f"\n✅ [bold green]Success![/bold green] Received: {response}")
        
    except Exception as e:
        console.print(f"❌ [bold red]Error:[/bold red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
