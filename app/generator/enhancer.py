"""
Feature Enhancer Module

AI-powered enhancement of existing Gherkin features.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.ai.engine import run_ai


@dataclass
class EnhancementSuggestion:
    """A suggestion for enhancing a feature."""
    type: str  # "scenario", "step", "tag", "background"
    description: str
    content: str
    location: Optional[str] = None  # Where to add (e.g., "after scenario X")
    priority: str = "medium"  # "high", "medium", "low"


class FeatureEnhancer:
    """
    Enhances existing Gherkin features with additional scenarios and improvements.
    """

    ANALYZE_PROMPT = '''You are a Senior QA Engineer reviewing a Gherkin feature file.

Analyze this feature file and identify areas for improvement:

{feature_content}

Consider:
1. Missing test scenarios (edge cases, negative cases, boundaries)
2. Steps that could be more specific or clearer
3. Missing tags or incorrect tagging
4. Opportunities for Background sections
5. Potential data-driven scenarios using Scenario Outline

Provide your analysis in this format:

MISSING_SCENARIOS:
- [Description of missing scenario 1]
- [Description of missing scenario 2]

STEP_IMPROVEMENTS:
- [Current step] -> [Suggested improvement]

TAG_SUGGESTIONS:
- [Suggested tag and reason]

OTHER_IMPROVEMENTS:
- [Other suggestions]'''

    EXPAND_PROMPT = '''You are a QA Engineer expanding test coverage.

Current feature:
{feature_content}

Generate {count} additional scenarios for this feature focusing on:
{focus_areas}

Requirements:
- Use the same step style as existing scenarios
- Include proper Given/When/Then structure
- Add appropriate tags
- Use realistic test data

Output only the new Scenario blocks, not the full feature file.'''

    ADD_NEGATIVE_PROMPT = '''You are a QA Engineer adding negative test cases.

Current feature:
{feature_content}

Generate negative test scenarios that cover:
1. Invalid input data
2. Missing required fields
3. Authentication/authorization failures
4. System error handling
5. Boundary violations

Output only the new Scenario blocks with proper Given/When/Then steps.'''

    CONVERT_TO_OUTLINE_PROMPT = '''You are a QA Engineer optimizing test scenarios.

These similar scenarios could be combined into a Scenario Outline:

{scenarios}

Convert them into a single Scenario Outline with an Examples table.
Preserve the test coverage while reducing duplication.

Output only the Scenario Outline block with Examples.'''

    def __init__(self):
        """Initialize the feature enhancer."""
        pass

    def analyze(self, feature_content: str) -> Dict[str, Any]:
        """
        Analyze a feature and provide enhancement suggestions.

        Args:
            feature_content: Gherkin feature content

        Returns:
            Dictionary with analysis results
        """
        prompt = self.ANALYZE_PROMPT.format(feature_content=feature_content)
        response = run_ai(prompt)

        return self._parse_analysis(response)

    def expand(
        self,
        feature_content: str,
        count: int = 3,
        focus_areas: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Generate additional scenarios for a feature.

        Args:
            feature_content: Existing feature content
            count: Number of scenarios to generate
            focus_areas: Areas to focus on (e.g., "security", "performance")

        Returns:
            List of new scenario blocks
        """
        if focus_areas is None:
            focus_areas = ["edge cases", "error handling", "user variations"]

        prompt = self.EXPAND_PROMPT.format(
            feature_content=feature_content,
            count=count,
            focus_areas=", ".join(focus_areas),
        )

        response = run_ai(prompt)
        return self._extract_scenarios(response)

    def add_negative_cases(self, feature_content: str) -> List[str]:
        """
        Generate negative test scenarios.

        Args:
            feature_content: Existing feature content

        Returns:
            List of negative scenario blocks
        """
        prompt = self.ADD_NEGATIVE_PROMPT.format(feature_content=feature_content)
        response = run_ai(prompt)
        return self._extract_scenarios(response)

    def suggest_tags(self, feature_content: str) -> List[Dict[str, str]]:
        """
        Suggest appropriate tags for scenarios.

        Args:
            feature_content: Feature content

        Returns:
            List of tag suggestions with reasons
        """
        prompt = f'''Analyze this Gherkin feature and suggest appropriate tags:

{feature_content}

Common tag categories:
- @smoke, @regression, @sanity (test level)
- @critical, @high, @medium, @low (priority)
- @wip, @skip, @manual (status)
- @ui, @api, @integration (type)

For each scenario, suggest relevant tags with brief reasons.
Format: @tag_name - reason'''

        response = run_ai(prompt)
        return self._parse_tag_suggestions(response)

    def convert_to_outline(self, scenarios: List[str]) -> Optional[str]:
        """
        Convert similar scenarios to a Scenario Outline.

        Args:
            scenarios: List of similar scenario blocks

        Returns:
            Scenario Outline block or None if not applicable
        """
        if len(scenarios) < 2:
            return None

        prompt = self.CONVERT_TO_OUTLINE_PROMPT.format(
            scenarios="\n\n".join(scenarios)
        )

        response = run_ai(prompt)

        # Validate response contains Scenario Outline
        if "Scenario Outline:" in response and "Examples:" in response:
            return self._clean_scenario_block(response)

        return None

    def add_background(self, feature_content: str) -> Optional[str]:
        """
        Suggest a Background section for common setup steps.

        Args:
            feature_content: Feature content

        Returns:
            Background block or None if not needed
        """
        prompt = f'''Analyze these scenarios and identify common Given steps that could be moved to a Background section:

{feature_content}

If there are common setup steps repeated across scenarios, create a Background section.
If no common steps are found, respond with "NO_BACKGROUND_NEEDED".

Output only the Background block if applicable.'''

        response = run_ai(prompt)

        if "NO_BACKGROUND_NEEDED" in response:
            return None

        if "Background:" in response:
            return self._clean_scenario_block(response)

        return None

    def improve_steps(self, feature_content: str) -> Dict[str, str]:
        """
        Suggest improvements for existing steps.

        Args:
            feature_content: Feature content

        Returns:
            Dictionary mapping original steps to improved versions
        """
        prompt = f'''Review these Gherkin steps and suggest improvements for clarity and automation:

{feature_content}

For each step that could be improved, provide:
ORIGINAL: [original step]
IMPROVED: [improved step]
REASON: [brief reason]

Focus on:
- Making steps more specific and testable
- Using consistent language patterns
- Including necessary details for automation'''

        response = run_ai(prompt)
        return self._parse_step_improvements(response)

    def enhance_feature(
        self,
        feature_content: str,
        add_negative: bool = True,
        add_edge_cases: bool = True,
        optimize_outlines: bool = True,
        add_background: bool = True,
    ) -> str:
        """
        Comprehensively enhance a feature file.

        Args:
            feature_content: Original feature content
            add_negative: Add negative test cases
            add_edge_cases: Add edge case scenarios
            optimize_outlines: Convert similar scenarios to outlines
            add_background: Add background section if appropriate

        Returns:
            Enhanced feature content
        """
        enhanced = feature_content

        # Add background if appropriate
        if add_background:
            background = self.add_background(feature_content)
            if background:
                # Insert background after feature description
                lines = enhanced.split("\n")
                insert_index = 0

                for i, line in enumerate(lines):
                    if line.strip().startswith("Scenario"):
                        insert_index = i
                        break

                if insert_index > 0:
                    lines.insert(insert_index, "\n" + background + "\n")
                    enhanced = "\n".join(lines)

        # Add negative cases
        if add_negative:
            negative_scenarios = self.add_negative_cases(feature_content)
            if negative_scenarios:
                enhanced += "\n\n" + "\n\n".join(negative_scenarios)

        # Add edge cases
        if add_edge_cases:
            edge_scenarios = self.expand(
                feature_content,
                count=2,
                focus_areas=["boundary conditions", "edge cases"],
            )
            if edge_scenarios:
                enhanced += "\n\n" + "\n\n".join(edge_scenarios)

        return enhanced

    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """Parse analysis response into structured data."""
        result = {
            "missing_scenarios": [],
            "step_improvements": [],
            "tag_suggestions": [],
            "other_improvements": [],
        }

        current_section = None
        section_map = {
            "MISSING_SCENARIOS": "missing_scenarios",
            "STEP_IMPROVEMENTS": "step_improvements",
            "TAG_SUGGESTIONS": "tag_suggestions",
            "OTHER_IMPROVEMENTS": "other_improvements",
        }

        for line in response.split("\n"):
            line = line.strip()

            # Check for section headers
            for header, key in section_map.items():
                if line.startswith(header):
                    current_section = key
                    break
            else:
                # Add content to current section
                if current_section and line.startswith("-"):
                    content = line[1:].strip()
                    if content:
                        result[current_section].append(content)

        return result

    def _extract_scenarios(self, response: str) -> List[str]:
        """Extract scenario blocks from response."""
        scenarios = []
        current_scenario = []
        in_scenario = False

        for line in response.split("\n"):
            if line.strip().startswith(("Scenario:", "Scenario Outline:")):
                if current_scenario:
                    scenarios.append("\n".join(current_scenario).strip())
                current_scenario = [line]
                in_scenario = True
            elif in_scenario:
                if line.strip() and not line.strip().startswith("#"):
                    current_scenario.append(line)
                elif not line.strip():
                    current_scenario.append(line)

        if current_scenario:
            scenarios.append("\n".join(current_scenario).strip())

        return scenarios

    def _parse_tag_suggestions(self, response: str) -> List[Dict[str, str]]:
        """Parse tag suggestions from response."""
        suggestions = []

        for line in response.split("\n"):
            if "@" in line and "-" in line:
                parts = line.split("-", 1)
                if len(parts) == 2:
                    tag = parts[0].strip()
                    reason = parts[1].strip()

                    # Extract just the tag
                    tag_match = re.search(r"@\w+", tag)
                    if tag_match:
                        suggestions.append({
                            "tag": tag_match.group(0),
                            "reason": reason,
                        })

        return suggestions

    def _parse_step_improvements(self, response: str) -> Dict[str, str]:
        """Parse step improvement suggestions."""
        improvements = {}
        original = None

        for line in response.split("\n"):
            line = line.strip()

            if line.startswith("ORIGINAL:"):
                original = line[9:].strip()
            elif line.startswith("IMPROVED:") and original:
                improved = line[9:].strip()
                improvements[original] = improved
                original = None

        return improvements

    def _clean_scenario_block(self, response: str) -> str:
        """Clean up a scenario block from AI response."""
        lines = []
        in_block = False

        for line in response.split("\n"):
            stripped = line.strip()

            if stripped.startswith(("Scenario", "Background:", "Examples:")):
                in_block = True

            if in_block:
                if stripped.startswith(("Given", "When", "Then", "And", "But",
                                       "|", "Scenario", "Background:", "Examples:",
                                       "@")):
                    lines.append(line)
                elif not stripped:
                    lines.append(line)
                elif stripped.startswith("#"):
                    lines.append(line)

        return "\n".join(lines).strip()
