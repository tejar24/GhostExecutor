from app.ai.claude_cli import run_claude_cli

def run_ai(prompt: str) -> str:
    """
    Primary AI execution entry point using CLI only.
    """
    return run_claude_cli(prompt)
