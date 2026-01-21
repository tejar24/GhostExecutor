from anthropic import Anthropic
import os

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def run_claude_api(prompt: str) -> str:
    response = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    output = response.content[0].text.strip()
    if not output:
        raise RuntimeError("Claude API returned empty output")

    return output
