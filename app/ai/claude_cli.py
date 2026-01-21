import subprocess
import shutil

CLAUDE_TIMEOUT = 120

def run_claude_cli(prompt: str) -> str:
    """
    Run Claude CLI with the given prompt using -p (print) mode.
    The prompt is passed via stdin to handle long prompts.
    """
    # Find claude executable - check common locations
    claude_cmd = shutil.which("claude")
    if not claude_cmd:
        # Try common npm global paths on Windows
        import os
        npm_path = os.path.expandvars(r"%APPDATA%\npm\claude.cmd")
        if os.path.exists(npm_path):
            claude_cmd = npm_path
        else:
            raise RuntimeError("Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code")

    result = subprocess.run(
        [claude_cmd, "-p"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=CLAUDE_TIMEOUT,
        shell=True
    )

    if result.returncode != 0:
        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
        raise RuntimeError(f"Claude CLI failed: {error_msg}")

    output = result.stdout.strip()
    if not output:
        raise RuntimeError("Claude CLI returned empty output")

    return output
