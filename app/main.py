from pathlib import Path

from app.ai.engine import run_ai
from app.parser.feature_validator import validate_feature

TEMPLATE_PATH = Path("app/core/feature_prompt_template.txt")

def generate_feature(user_story: str) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    prompt = template.replace("<<<USER_STORY_TEXT>>>", user_story)

    last_error = None

    for attempt in range(2):  # one retry allowed
        try:
            feature = run_ai(prompt)
            validate_feature(feature)
            return feature
        except Exception as e:
            last_error = e

    raise RuntimeError(f"Generation failed after retry: {last_error}")

if __name__ == "__main__":
    story = input("Enter user story:\n")

    try:
        feature = generate_feature(story)
        print("\n✅ Generated Valid Feature File:\n")
        print(feature)
    except Exception as e:
        print(f"\n❌ Final failure: {e}")
