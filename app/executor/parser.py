"""
Gherkin Feature File Parser

Parses .feature files into structured data for autonomous execution.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Step:
    """Represents a single Gherkin step."""
    keyword: str  # Given, When, Then, And, But
    text: str
    line_number: int


@dataclass
class Scenario:
    """Represents a Gherkin scenario."""
    name: str
    steps: List[Step] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class Feature:
    """Represents a complete Gherkin feature."""
    name: str
    description: str = ""
    scenarios: List[Scenario] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    file_path: Optional[str] = None


class GherkinParser:
    """
    Parser for Gherkin feature files.
    Extracts features, scenarios, and steps into structured data.
    """

    STEP_KEYWORDS = ("Given", "When", "Then", "And", "But")
    SCENARIO_KEYWORDS = ("Scenario:", "Scenario Outline:")

    def parse_file(self, file_path: str) -> Feature:
        """Parse a feature file and return structured Feature object."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Feature file not found: {file_path}")

        content = path.read_text(encoding="utf-8")
        return self.parse_content(content, str(path))

    def parse_content(self, content: str, file_path: str = "") -> Feature:
        """Parse feature content string into structured Feature object."""
        # Remove markdown code block markers if present
        content = self._clean_content(content)

        lines = content.split("\n")
        feature = Feature(name="", file_path=file_path)
        current_scenario: Optional[Scenario] = None
        current_tags: List[str] = []
        in_feature_description = False

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue

            # Parse tags
            if stripped.startswith("@"):
                current_tags = self._parse_tags(stripped)
                continue

            # Parse Feature
            if stripped.startswith("Feature:"):
                feature.name = stripped[8:].strip()
                feature.tags = current_tags
                current_tags = []
                in_feature_description = True
                continue

            # Parse feature description (lines after Feature: before first Scenario)
            if in_feature_description and not any(
                stripped.startswith(kw) for kw in self.SCENARIO_KEYWORDS + self.STEP_KEYWORDS
            ):
                if feature.description:
                    feature.description += "\n"
                feature.description += stripped
                continue

            # Parse Scenario
            if any(stripped.startswith(kw) for kw in self.SCENARIO_KEYWORDS):
                in_feature_description = False
                if current_scenario:
                    feature.scenarios.append(current_scenario)

                scenario_name = stripped.split(":", 1)[1].strip()
                current_scenario = Scenario(
                    name=scenario_name,
                    tags=current_tags,
                    line_number=line_num
                )
                current_tags = []
                continue

            # Parse Steps
            for keyword in self.STEP_KEYWORDS:
                if stripped.startswith(keyword):
                    step_text = stripped[len(keyword):].strip()
                    step = Step(
                        keyword=keyword,
                        text=step_text,
                        line_number=line_num
                    )
                    if current_scenario:
                        current_scenario.steps.append(step)
                    break

        # Don't forget the last scenario
        if current_scenario:
            feature.scenarios.append(current_scenario)

        return feature

    def _clean_content(self, content: str) -> str:
        """Remove markdown code blocks and clean content."""
        # Remove ```gherkin and ``` markers
        content = re.sub(r"^```\w*\s*$", "", content, flags=re.MULTILINE)
        return content.strip()

    def _parse_tags(self, line: str) -> List[str]:
        """Extract tags from a line."""
        return [tag.strip() for tag in line.split() if tag.startswith("@")]


def parse_feature_file(file_path: str) -> Feature:
    """Convenience function to parse a feature file."""
    parser = GherkinParser()
    return parser.parse_file(file_path)
