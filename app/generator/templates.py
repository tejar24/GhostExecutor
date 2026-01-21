"""
Template Management Module

Manages prompt templates for feature generation.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PromptTemplate:
    """A prompt template with metadata."""
    name: str
    content: str
    description: Optional[str] = None
    variables: List[str] = field(default_factory=list)
    category: str = "general"
    version: str = "1.0"

    def __post_init__(self):
        """Extract variables from content if not provided."""
        if not self.variables:
            self.variables = self._extract_variables()

    def _extract_variables(self) -> List[str]:
        """Extract placeholder variables from template."""
        # Match {variable} and <<<VARIABLE>>> patterns
        patterns = [
            r"\{(\w+)\}",
            r"<<<(\w+)>>>",
        ]

        variables = set()
        for pattern in patterns:
            matches = re.findall(pattern, self.content)
            variables.update(matches)

        return sorted(variables)

    def render(self, **kwargs: Any) -> str:
        """
        Render template with provided variables.

        Args:
            **kwargs: Variable values

        Returns:
            Rendered template string
        """
        result = self.content

        for key, value in kwargs.items():
            # Replace both formats
            result = result.replace(f"{{{key}}}", str(value))
            result = result.replace(f"<<<{key.upper()}>>>", str(value))
            result = result.replace(f"<<<{key}>>>", str(value))

        return result

    def validate(self, **kwargs: Any) -> List[str]:
        """
        Validate that all required variables are provided.

        Args:
            **kwargs: Variable values

        Returns:
            List of missing variable names
        """
        provided = set(kwargs.keys())
        required = set(v.lower() for v in self.variables)

        # Also check uppercase versions
        provided_lower = set(k.lower() for k in provided)

        missing = []
        for var in self.variables:
            if var.lower() not in provided_lower:
                missing.append(var)

        return missing


class TemplateManager:
    """
    Manages a collection of prompt templates.
    """

    # Built-in templates
    BUILTIN_TEMPLATES = {
        "feature_basic": PromptTemplate(
            name="feature_basic",
            description="Basic feature generation template",
            category="generation",
            content='''You are a QA Engineer creating Gherkin feature files.

Generate a feature file for the following user story:

{user_story}

Requirements:
- Use proper Gherkin syntax
- Include positive and negative test cases
- Each scenario needs Given, When, Then steps

Generate only the feature file content, starting with "Feature:".''',
        ),

        "feature_comprehensive": PromptTemplate(
            name="feature_comprehensive",
            description="Comprehensive feature generation with all case types",
            category="generation",
            content='''You are a Senior QA Engineer specializing in BDD test automation.

Create a comprehensive Gherkin feature file based on this requirement:

{user_story}

Include the following:
1. Feature description explaining the functionality
2. Happy path scenarios (normal use cases)
3. Negative scenarios (invalid inputs, error handling)
4. Edge cases (boundary conditions, limits)
5. Security considerations if applicable

Guidelines:
- Use descriptive scenario names
- Include appropriate @tags
- Use concrete test data
- Steps should be atomic and reusable
- Use Background for common setup steps
- Consider Scenario Outline for data-driven tests

Output only the Gherkin feature file. Start with "Feature:".''',
        ),

        "feature_api": PromptTemplate(
            name="feature_api",
            description="API-focused feature generation",
            category="generation",
            content='''You are an API Testing Specialist creating Gherkin features.

Generate an API test feature for:

{user_story}

API Details:
{api_details}

Include scenarios for:
1. Successful requests with valid data
2. Authentication/authorization tests
3. Input validation (missing fields, invalid formats)
4. Error responses (404, 500, etc.)
5. Rate limiting if applicable

Use steps like:
- Given I have a valid API token
- When I send a POST request to "/endpoint"
- Then the response status should be 200
- And the response should contain "field"

Generate only the feature file content.''',
        ),

        "feature_ui": PromptTemplate(
            name="feature_ui",
            description="UI-focused feature generation",
            category="generation",
            content='''You are a UI Test Automation Engineer creating Gherkin features.

Generate a UI test feature for:

{user_story}

Application URL: {app_url}

Include scenarios for:
1. Page navigation and loading
2. Form submissions with valid data
3. Form validations (required fields, formats)
4. User interactions (clicks, selections)
5. Visual feedback (messages, indicators)

Use steps like:
- Given I am on the "Login" page
- When I enter "user@example.com" in the email field
- When I click the "Submit" button
- Then I should see "Welcome" message
- And the URL should contain "/dashboard"

Generate only the feature file content.''',
        ),

        "scenario_expand": PromptTemplate(
            name="scenario_expand",
            description="Expand a single scenario into multiple test cases",
            category="enhancement",
            content='''You are a QA Engineer expanding test coverage.

Given this existing scenario:

{scenario}

Generate additional scenarios to cover:
1. Boundary conditions
2. Invalid inputs
3. Error handling
4. Alternative paths

Context from the feature:
{feature_context}

Generate only the new Scenario blocks (not the full feature file).
Each scenario should have proper Given/When/Then steps.''',
        ),

        "step_suggestions": PromptTemplate(
            name="step_suggestions",
            description="Suggest additional steps for a scenario",
            category="enhancement",
            content='''You are a QA Engineer reviewing test scenarios.

Current scenario:
{scenario}

Suggest additional steps that could improve this scenario:
1. Additional validations
2. Setup steps that might be missing
3. Cleanup or teardown steps
4. Edge case handling

Format suggestions as Gherkin steps (Given/When/Then/And).''',
        ),
    }

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize template manager.

        Args:
            template_dir: Directory containing custom templates
        """
        self.template_dir = Path(template_dir) if template_dir else None
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_builtin_templates()

        if self.template_dir:
            self._load_custom_templates()

    def _load_builtin_templates(self) -> None:
        """Load built-in templates."""
        self._templates.update(self.BUILTIN_TEMPLATES)

    def _load_custom_templates(self) -> None:
        """Load custom templates from directory."""
        if not self.template_dir or not self.template_dir.exists():
            return

        for file_path in self.template_dir.glob("*.txt"):
            try:
                content = file_path.read_text(encoding="utf-8")
                name = file_path.stem

                # Try to extract metadata from first line comment
                description = None
                if content.startswith("#"):
                    first_line = content.split("\n")[0]
                    description = first_line[1:].strip()
                    content = "\n".join(content.split("\n")[1:]).strip()

                template = PromptTemplate(
                    name=name,
                    content=content,
                    description=description,
                    category="custom",
                )

                self._templates[name] = template

            except Exception:
                continue  # Skip invalid templates

    def get(self, name: str) -> Optional[PromptTemplate]:
        """
        Get a template by name.

        Args:
            name: Template name

        Returns:
            PromptTemplate or None
        """
        return self._templates.get(name)

    def list_templates(
        self,
        category: Optional[str] = None,
    ) -> List[PromptTemplate]:
        """
        List available templates.

        Args:
            category: Filter by category

        Returns:
            List of templates
        """
        templates = list(self._templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return sorted(templates, key=lambda t: t.name)

    def register(self, template: PromptTemplate) -> None:
        """
        Register a custom template.

        Args:
            template: Template to register
        """
        self._templates[template.name] = template

    def render(self, name: str, **kwargs: Any) -> str:
        """
        Render a template by name.

        Args:
            name: Template name
            **kwargs: Template variables

        Returns:
            Rendered template string

        Raises:
            KeyError: If template not found
            ValueError: If required variables missing
        """
        template = self.get(name)
        if not template:
            raise KeyError(f"Template not found: {name}")

        missing = template.validate(**kwargs)
        if missing:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")

        return template.render(**kwargs)

    def save_template(
        self,
        template: PromptTemplate,
        overwrite: bool = False,
    ) -> str:
        """
        Save a template to the template directory.

        Args:
            template: Template to save
            overwrite: Whether to overwrite existing

        Returns:
            Path to saved template file
        """
        if not self.template_dir:
            raise RuntimeError("No template directory configured")

        self.template_dir.mkdir(parents=True, exist_ok=True)

        file_path = self.template_dir / f"{template.name}.txt"

        if file_path.exists() and not overwrite:
            raise FileExistsError(f"Template already exists: {template.name}")

        content = template.content
        if template.description:
            content = f"# {template.description}\n{content}"

        file_path.write_text(content, encoding="utf-8")
        self._templates[template.name] = template

        return str(file_path)

    def delete_template(self, name: str) -> bool:
        """
        Delete a custom template.

        Args:
            name: Template name

        Returns:
            True if deleted
        """
        template = self.get(name)
        if not template or template.category != "custom":
            return False

        if self.template_dir:
            file_path = self.template_dir / f"{name}.txt"
            if file_path.exists():
                file_path.unlink()

        del self._templates[name]
        return True
