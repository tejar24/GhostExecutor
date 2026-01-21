# Ghost-QC

**Autonomous Test Execution Framework** powered by Claude AI

Ghost-QC interprets and executes Gherkin BDD test scenarios without manual step definitions. It uses AI to understand test intent and perform browser automation autonomously.

## Features

- **AI-Powered Test Execution**: No step definitions required - AI interprets Gherkin steps
- **Feature Generation**: Generate Gherkin features from user stories
- **Multi-Framework Support**: Built-in selectors for MUI, Ant Design, Bootstrap, PrimeReact, Chakra UI
- **REST API**: Remote test execution and management
- **Persistence**: SQLite-based storage for test results and history
- **Comprehensive Reporting**: HTML and JSON test reports with screenshots

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js (for Claude CLI)
- Claude CLI installed (`npm install -g @anthropic-ai/claude-cli`)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ghost-qc.git
cd ghost-qc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Running Tests

```bash
# Run a single feature file
python -m app.run_tests features/login.feature

# Run multiple features with glob pattern
python -m app.run_tests "features/*.feature"

# Run in headed mode (visible browser)
python -m app.run_tests features/login.feature --headed

# With slow motion for debugging
python -m app.run_tests features/login.feature --headed --slow-mo 500
```

### Generating Features

```bash
# Interactive generation
python -m app.main
# Then enter your user story when prompted

# Or programmatically
from app.generator import FeatureGenerator

generator = FeatureGenerator()
result = generator.generate("As a user, I want to login to the dashboard")
print(result.feature_content)
```

## Project Structure

```
ghost-qc/
├── app/
│   ├── ai/                    # AI integration layer
│   │   ├── engine.py          # AI execution interface
│   │   └── claude_cli.py      # Claude CLI wrapper
│   │
│   ├── executor/              # Test execution engine
│   │   ├── runner.py          # Test orchestrator
│   │   ├── parser.py          # Gherkin parser
│   │   ├── interpreter.py     # AI step interpreter
│   │   ├── browser.py         # Playwright automation
│   │   └── reporter.py        # Report generation
│   │
│   ├── generator/             # Feature generation
│   │   ├── feature_generator.py
│   │   ├── templates.py       # Prompt templates
│   │   └── enhancer.py        # Feature enhancement
│   │
│   ├── frameworks/            # UI component libraries
│   │   ├── registry.py        # Framework registry
│   │   └── components/        # MUI, Ant Design, etc.
│   │
│   ├── storage/               # Persistence layer
│   │   ├── models.py          # Data models
│   │   ├── database.py        # SQLite database
│   │   └── repository.py      # Data access
│   │
│   ├── api/                   # REST API
│   │   ├── server.py          # FastAPI server
│   │   ├── routes.py          # API endpoints
│   │   └── schemas.py         # Request/response models
│   │
│   ├── utils/                 # Utilities
│   │   ├── logger.py          # Logging configuration
│   │   ├── file_utils.py      # File operations
│   │   ├── retry.py           # Retry logic
│   │   └── helpers.py         # Helper functions
│   │
│   ├── config.py              # Configuration management
│   ├── main.py                # Feature generation CLI
│   └── run_tests.py           # Test execution CLI
│
├── features/                  # Feature files
├── reports/                   # Test reports
└── prompts/                   # Prompt templates
```

## Usage

### Writing Feature Files

Ghost-QC uses standard Gherkin syntax:

```gherkin
@smoke @login
Feature: User Login
  As a user I want to login to access my dashboard

  Scenario: Successful login with valid credentials
    Given I am on the login page "https://example.com/login"
    When I enter "user@example.com" in the email field
    And I enter "password123" in the password field
    And I click the "Login" button
    Then I should see the dashboard
    And the URL should contain "/dashboard"

  Scenario: Login fails with invalid password
    Given I am on the login page "https://example.com/login"
    When I enter "user@example.com" in the email field
    And I enter "wrongpassword" in the password field
    And I click the "Login" button
    Then I should see an error message "Invalid credentials"
```

### REST API

Start the API server:

```bash
python -m app.api.server
# or
uvicorn app.api.server:app --reload
```

API Endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/tests/run` | Start a test run |
| GET | `/api/v1/tests/{run_id}` | Get test run status |
| POST | `/api/v1/generate/feature` | Generate feature from user story |
| POST | `/api/v1/generate/enhance` | Enhance existing feature |
| GET | `/api/v1/results` | Get test results |
| GET | `/api/v1/features` | List features |

Example API usage:

```bash
# Generate a feature
curl -X POST http://localhost:8000/api/v1/generate/feature \
  -H "Content-Type: application/json" \
  -d '{"user_story": "As a user, I want to login to the system"}'

# Run tests
curl -X POST http://localhost:8000/api/v1/tests/run \
  -H "Content-Type: application/json" \
  -d '{"feature_files": ["features/login.feature"]}'
```

### Configuration

Create a `ghost-qc.json` file in your project root:

```json
{
  "browser": {
    "headless": true,
    "slow_mo": 100,
    "viewport_width": 1366,
    "viewport_height": 768,
    "default_timeout": 30000
  },
  "ai": {
    "timeout": 120,
    "max_retries": 3
  },
  "storage": {
    "database_path": "ghost_qc.db",
    "reports_dir": "reports"
  }
}
```

Or use environment variables:

```bash
export GHOST_QC_HEADLESS=true
export GHOST_QC_SLOW_MO=100
export GHOST_QC_TIMEOUT=30000
```

### Programmatic Usage

```python
from app.executor.runner import TestRunner
from app.generator import FeatureGenerator, GenerationConfig
from app.storage import TestResultRepository

# Run tests
runner = TestRunner(headless=True)
result = runner.run_feature("features/login.feature")
print(f"Status: {result['status']}")

# Generate features
config = GenerationConfig(
    include_negative_cases=True,
    include_edge_cases=True,
    max_scenarios=5,
)
generator = FeatureGenerator(config=config)
result = generator.generate("User login functionality")
print(result.feature_content)

# Query test history
repo = TestResultRepository()
recent_results = repo.get_recent(days=7)
summary = repo.get_summary()
print(f"Pass rate: {summary.pass_rate}%")
```

## Supported Actions

The AI interpreter supports these browser actions:

| Action | Description |
|--------|-------------|
| `navigate` | Go to a URL |
| `click` | Click an element |
| `fill` | Enter text in a field |
| `select` | Select dropdown option |
| `check/uncheck` | Toggle checkbox |
| `press_key` | Press keyboard key |
| `wait` | Wait for element |
| `verify_visible` | Check element visibility |
| `verify_text` | Verify text content |
| `verify_url` | Verify current URL |

## Component Framework Support

Ghost-QC includes selector definitions for popular UI frameworks:

- **Material-UI (MUI)**: Buttons, TextFields, Select, Dialogs, Tables, etc.
- **Ant Design**: All major components
- **Bootstrap**: Forms, Modals, Navbars, Cards, etc.
- **PrimeReact**: DataTable, Calendar, Dialog, etc.
- **Chakra UI**: All major components

## Reports

Test reports are generated in both HTML and JSON formats:

```
reports/
├── test_report_20240118_143022.html
├── test_report_20240118_143022.json
└── screenshots/
    └── failed_step_1.png
```

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Type checking
mypy app/

# Linting
flake8 app/
```

## Requirements

Create a `requirements.txt`:

```
playwright>=1.40.0
fastapi>=0.100.0
uvicorn>=0.20.0
pydantic>=2.0.0
```

## Troubleshooting

### Claude CLI not found

Ensure Claude CLI is installed globally:

```bash
npm install -g @anthropic-ai/claude-cli
```

### Browser not launching

Install Playwright browsers:

```bash
playwright install chromium
```

### Slow test execution

Reduce AI timeout and use headless mode:

```bash
export GHOST_QC_AI_TIMEOUT=60
export GHOST_QC_HEADLESS=true
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request
