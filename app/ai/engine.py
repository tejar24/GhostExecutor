from app.config import get_config

def run_ai(prompt: str) -> str:
    """
    Primary AI execution entry point.
    Uses API or CLI based on configuration.
    """
    config = get_config()

    if config.ai.use_cli:
        from app.ai.claude_cli import run_claude_cli
        return run_claude_cli(prompt)
    else:
        from app.ai.claude_api import run_claude_api
        return run_claude_api(prompt)
