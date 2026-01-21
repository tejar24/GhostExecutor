"""
Feature Generator Module

AI-powered Gherkin feature generation from user stories and requirements.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.ai.engine import run_ai
from app.parser.feature_validator import validate_feature


@dataclass
class GenerationConfig:
    """Configuration for feature generation."""
    max_retries: int = 3
    include_negative_cases: bool = True
    include_edge_cases: bool = True
    include_data_tables: bool = False
    scenario_outline_for_similar: bool = True
    max_scenarios: int = 10
    language: str = "en"
    tags: List[str] = field(default_factory=list)
    custom_instructions: Optional[str] = None


@dataclass
class GenerationResult:
    """Result of a feature generation attempt."""
    success: bool
    feature_content: Optional[str] = None
    feature_name: Optional[str] = None
    scenario_count: int = 0
    error: Optional[str] = None
    attempts: int = 0
    duration_ms: float = 0.0
    user_story: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "feature_content": self.feature_content,
            "feature_name": self.feature_name,
            "scenario_count": self.scenario_count,
            "error": self.error,
            "attempts": self.attempts,
            "duration_ms": self.duration_ms,
            "user_story": self.user_story,
            "timestamp": self.timestamp.isoformat(),
        }


class FeatureGenerator:
    """
    AI-powered feature generator that creates Gherkin features from user stories.
    """

    DEFAULT_TEMPLATE = '''You are a Senior QA Engineer specializing in behavior-driven development (BDD).
Generate a comprehensive Gherkin feature file based on the following user story.

USER STORY:
{user_story}

REQUIREMENTS:
1. Use proper Gherkin syntax (Feature, Scenario, Given, When, Then, And, But)
2. Create meaningful scenario names that describe the test case
3. Include appropriate tags (@tag format)
4. Each scenario must have at least one Given, one When, and one Then step
5. Use concrete, realistic test data in steps
{additional_requirements}

GUIDELINES:
- Write clear, actionable steps that can be automated
- Use present tense for Given steps, action verbs for When steps
- Then steps should verify observable outcomes
- Avoid implementation details in step descriptions
- Include both happy path and error scenarios
{custom_instructions}

Generate ONLY the Gherkin feature file content. Start with "Feature:" and include all scenarios.
Do not include markdown code blocks or explanations.'''

    def __init__(
        self,
        template_path: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
    ):
        """
        Initialize the feature generator.

        Args:
            template_path: Path to custom prompt template
            config: Generation configuration
        """
        self.template_path = template_path
        self.config = config or GenerationConfig()
        self._template: Optional[str] = None

    @property
    def template(self) -> str:
        """Get the prompt template."""
        if self._template is None:
            if self.template_path and Path(self.template_path).exists():
                self._template = Path(self.template_path).read_text(encoding="utf-8")
            else:
                self._template = self.DEFAULT_TEMPLATE
        return self._template

    def generate(
        self,
        user_story: str,
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResult:
        """
        Generate a Gherkin feature from a user story.

        Args:
            user_story: User story or requirement description
            config: Optional config override

        Returns:
            GenerationResult with the generated feature
        """
        start_time = datetime.now()
        cfg = config or self.config

        result = GenerationResult(
            success=False,
            user_story=user_story,
        )

        prompt = self._build_prompt(user_story, cfg)
        last_error = None

        for attempt in range(1, cfg.max_retries + 1):
            result.attempts = attempt

            try:
                # Generate feature using AI
                feature_content = run_ai(prompt)

                # Clean up response
                feature_content = self._clean_response(feature_content)

                # Validate the generated feature
                validate_feature(feature_content)

                # Extract metadata
                feature_name = self._extract_feature_name(feature_content)
                scenario_count = self._count_scenarios(feature_content)

                # Success
                result.success = True
                result.feature_content = feature_content
                result.feature_name = feature_name
                result.scenario_count = scenario_count
                result.error = None
                break

            except Exception as e:
                last_error = str(e)
                result.error = last_error

                # If validation failed, try to provide feedback for retry
                if attempt < cfg.max_retries:
                    prompt = self._build_retry_prompt(prompt, last_error)

        end_time = datetime.now()
        result.duration_ms = (end_time - start_time).total_seconds() * 1000

        return result

    def generate_from_acceptance_criteria(
        self,
        criteria: List[str],
        feature_name: str,
        description: Optional[str] = None,
    ) -> GenerationResult:
        """
        Generate a feature from a list of acceptance criteria.

        Args:
            criteria: List of acceptance criteria
            feature_name: Name for the feature
            description: Optional feature description

        Returns:
            GenerationResult
        """
        # Convert criteria to user story format
        criteria_text = "\n".join(f"- {c}" for c in criteria)

        user_story = f"""
Feature: {feature_name}
{f'Description: {description}' if description else ''}

Acceptance Criteria:
{criteria_text}
        """.strip()

        return self.generate(user_story)

    def generate_batch(
        self,
        user_stories: List[str],
        config: Optional[GenerationConfig] = None,
    ) -> List[GenerationResult]:
        """
        Generate features for multiple user stories.

        Args:
            user_stories: List of user stories
            config: Optional config override

        Returns:
            List of GenerationResult
        """
        return [self.generate(story, config) for story in user_stories]

    def _build_prompt(self, user_story: str, config: GenerationConfig) -> str:
        """Build the AI prompt from template and config."""
        additional_requirements = []

        if config.include_negative_cases:
            additional_requirements.append(
                "6. Include negative test cases (invalid inputs, error conditions)"
            )

        if config.include_edge_cases:
            additional_requirements.append(
                "7. Include edge cases and boundary conditions"
            )

        if config.include_data_tables:
            additional_requirements.append(
                "8. Use data tables for related test data where appropriate"
            )

        if config.scenario_outline_for_similar:
            additional_requirements.append(
                "9. Use Scenario Outline with Examples for similar test variations"
            )

        if config.max_scenarios:
            additional_requirements.append(
                f"10. Limit to maximum {config.max_scenarios} scenarios"
            )

        # Check if template has placeholder
        if "<<<USER_STORY_TEXT>>>" in self.template:
            prompt = self.template.replace("<<<USER_STORY_TEXT>>>", user_story)
        elif "{user_story}" in self.template:
            prompt = self.template.format(
                user_story=user_story,
                additional_requirements="\n".join(additional_requirements),
                custom_instructions=config.custom_instructions or "",
            )
        else:
            prompt = self.template + f"\n\nUser Story:\n{user_story}"

        # Add tags if specified
        if config.tags:
            tags_str = " ".join(f"@{t}" if not t.startswith("@") else t for t in config.tags)
            prompt += f"\n\nInclude these tags at the feature level: {tags_str}"

        return prompt

    def _build_retry_prompt(self, original_prompt: str, error: str) -> str:
        """Build a retry prompt with error feedback."""
        return f"""{original_prompt}

IMPORTANT: The previous generation attempt failed with this error:
{error}

Please fix the issue and generate a valid Gherkin feature file.
Ensure proper Given/When/Then structure in each scenario."""

    def _clean_response(self, response: str) -> str:
        """Clean up AI response to extract pure Gherkin."""
        # Remove markdown code blocks
        response = re.sub(r"```(?:gherkin|feature)?\s*", "", response)
        response = re.sub(r"```\s*$", "", response, flags=re.MULTILINE)

        # Find where Feature: starts
        feature_match = re.search(r"^Feature:", response, re.MULTILINE)
        if feature_match:
            response = response[feature_match.start():]

        # Remove trailing explanations
        lines = response.split("\n")
        clean_lines = []
        in_feature = False

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("Feature:"):
                in_feature = True

            if in_feature:
                # Stop if we hit explanatory text
                if stripped and not any([
                    stripped.startswith(("Feature:", "Scenario", "Given", "When",
                                        "Then", "And", "But", "@", "#", "|",
                                        "Background:", "Examples:", "Scenario Outline:")),
                    stripped == "",
                    line.startswith("  "),  # Indented content
                ]):
                    # Check if it looks like a description or step
                    if not re.match(r"^[A-Z].*:$", stripped):
                        break

                clean_lines.append(line)

        return "\n".join(clean_lines).strip()

    def _extract_feature_name(self, content: str) -> str:
        """Extract feature name from content."""
        for line in content.split("\n"):
            if line.strip().startswith("Feature:"):
                return line.strip()[8:].strip()
        return "Unnamed Feature"

    def _count_scenarios(self, content: str) -> int:
        """Count scenarios in feature content."""
        count = len(re.findall(r"^\s*Scenario:", content, re.MULTILINE))
        count += len(re.findall(r"^\s*Scenario Outline:", content, re.MULTILINE))
        return count

    def save_feature(
        self,
        result: GenerationResult,
        output_dir: str,
        filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Save generated feature to a file.

        Args:
            result: GenerationResult to save
            output_dir: Output directory
            filename: Optional filename (auto-generated if not provided)

        Returns:
            Path to saved file or None if failed
        """
        if not result.success or not result.feature_content:
            return None

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not filename:
            # Generate filename from feature name
            safe_name = re.sub(r"[^\w\s-]", "", result.feature_name or "feature")
            safe_name = re.sub(r"\s+", "_", safe_name).lower()
            filename = f"{safe_name}.feature"

        file_path = output_path / filename
        file_path.write_text(result.feature_content, encoding="utf-8")

        return str(file_path)
