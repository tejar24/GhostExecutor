# Ghost-QC

**Autonomous Test Execution Framework** powered by Claude AI

Ghost-QC interprets and executes Gherkin BDD test scenarios without manual step definitions. It uses AI to understand test intent and perform browser automation autonomously.

## Features

- **AI-Powered Test Execution**: No step definitions required - AI interprets Gherkin steps directly
- **Feature Generation**: Generate Gherkin features from user stories using AI
- **UI Brain**: Intelligent DOM analysis with self-healing selectors and element classification
- **Web UI**: Modern React-based interface for test management and execution
- **Remote Execution**: Distribute tests across multiple machines via WebSocket connections
- **Real-time Streaming**: Live execution logs via Server-Sent Events (SSE)
- **Multi-Framework Support**: Built-in selectors for MUI, Ant Design, Bootstrap, PrimeReact, Chakra UI
- **REST API**: Comprehensive API for remote test execution and management
- **Persistence**: SQLite-based storage for test results and history
- **Comprehensive Reporting**: HTML and JSON test reports with screenshots

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend and Claude CLI)
- Claude CLI installed (`npm install -g @anthropic-ai/claude-cli`) or Anthropic API key

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

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
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
│   ├── ai/                       # AI integration layer
│   │   ├── engine.py             # Entry point (CLI or API mode)
│   │   ├── claude_cli.py         # Claude CLI wrapper
│   │   └── claude_api.py         # Anthropic API wrapper
│   │
│   ├── executor/                 # Test execution engine
│   │   ├── runner.py             # AutonomousTestRunner orchestrator
│   │   ├── parser.py             # Gherkin feature parser
│   │   ├── interpreter.py        # AI step interpreter
│   │   ├── browser.py            # Playwright browser automation
│   │   ├── reporter.py           # Report generation
│   │   ├── soft_assertions.py    # Non-blocking assertion collector
│   │   └── step_logger.py        # Detailed execution logging
│   │
│   ├── generator/                # Feature generation
│   │   ├── feature_generator.py  # AI-powered feature generation
│   │   ├── templates.py          # Prompt templates
│   │   └── enhancer.py           # Feature enhancement
│   │
│   ├── brain/                    # UI Brain - DOM analysis engine
│   │   ├── ui_brain.py           # Element classification & indexing
│   │   ├── element_classifier.py # Element type classification
│   │   ├── page_store.py         # DOM snapshot storage
│   │   └── brain_interpreter.py  # AI interpretation with DOM context
│   │
│   ├── frameworks/               # UI component library support
│   │   ├── registry.py           # Framework registry
│   │   └── components/           # MUI, Ant Design, Bootstrap, etc.
│   │
│   ├── storage/                  # Persistence layer
│   │   ├── models.py             # Data models
│   │   ├── database.py           # SQLite database
│   │   └── repository.py         # Data access patterns
│   │
│   ├── api/                      # REST API layer
│   │   ├── server.py             # FastAPI server
│   │   ├── routes.py             # Main API endpoints
│   │   ├── brain_routes.py       # UI Brain endpoints
│   │   ├── streaming.py          # SSE streaming
│   │   └── schemas.py            # Request/response models
│   │
│   ├── remote/                   # Remote execution infrastructure
│   │   ├── routes.py             # WebSocket & remote endpoints
│   │   ├── session_manager.py    # Client session management
│   │   ├── websocket_hub.py      # WebSocket connection hub
│   │   ├── orchestrator.py       # RemoteBrowserProxy command routing
│   │   └── schemas.py            # WebSocket message types
│   │
│   ├── parser/                   # Feature validation
│   │   └── feature_validator.py  # Syntax validation
│   │
│   ├── utils/                    # Utilities
│   │   ├── logger.py             # Logging configuration
│   │   ├── file_utils.py         # File operations
│   │   ├── retry.py              # Retry logic
│   │   └── helpers.py            # Helper functions
│   │
│   ├── config.py                 # Configuration management
│   ├── main.py                   # Feature generation CLI
│   └── run_tests.py              # Test execution CLI
│
├── frontend/                     # React + TypeScript Web UI
│   ├── src/
│   │   ├── components/
│   │   │   ├── StatusIndicator.tsx      # API connection status
│   │   │   ├── FeatureEditor.tsx        # Feature file editor
│   │   │   ├── ExecutionControls.tsx    # Run/Stop controls
│   │   │   ├── LogConsole.tsx           # Real-time log display
│   │   │   ├── ExecutionSummary.tsx     # Test results summary
│   │   │   ├── FeatureList.tsx          # Saved features list
│   │   │   └── RemoteClientsPanel.tsx   # Remote client management
│   │   │
│   │   ├── hooks/
│   │   │   ├── useTestExecution.ts      # Local test execution
│   │   │   ├── useSSEStream.ts          # SSE streaming
│   │   │   └── useRemoteClients.ts      # Remote client state
│   │   │
│   │   ├── types/
│   │   │   └── index.ts                 # TypeScript definitions
│   │   │
│   │   ├── App.tsx                      # Main app (Local/Remote tabs)
│   │   └── main.tsx                     # React entry point
│   │
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── client/                       # Remote client implementation
│   ├── cli.py                    # Command-line interface
│   ├── remote_client.py          # WebSocket client connector
│   └── quick_start.py            # Quick start helper
│
├── features/                     # Feature files (test cases)
├── reports/                      # Test execution reports
└── requirements.txt              # Python dependencies
```

## Architecture

### Backend Flow

```
Feature File → GherkinParser → StepInterpreter (AI) → BrowserAutomation → Reporter
                                      ↓
                                   UIBrain (DOM Analysis)
```

### Remote Execution Flow

```
Remote Client (Browser) ←→ WebSocketHub ←→ RemoteBrowserProxy ←→ Test Orchestrator
```

### Frontend Architecture

```
App
├── StatusIndicator        # Connection status
├── ExecutionControls      # Run/stop buttons, options
├── FeatureEditor          # Code editor for features
├── FeatureList            # Saved feature browser
├── LogConsole             # Real-time streaming logs
├── ExecutionSummary       # Results display
└── RemoteClientsPanel     # Remote client management
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

### Web UI

Start the backend server and frontend:

```bash
# Terminal 1: Start API server
python -m app.api.server

# Terminal 2: Start frontend dev server
cd frontend && npm run dev
```

Access the UI at `http://localhost:5173`

The Web UI provides:
- **Local Mode**: Run tests on the server's browser
- **Remote Mode**: Connect and manage remote test clients
- Real-time log streaming
- Feature file editing and management
- Execution controls (headless, slow-mo options)

### Remote Execution

#### Setting Up a Remote Client

```bash
cd client

# Connect to the server
python cli.py --server ws://your-server:8000/api/v1/remote/ws --name "client-1"
```

#### Using Remote Clients from the Server

Once connected, remote clients appear in the Web UI's Remote tab. You can:
- View connected clients and their status
- Run tests on specific clients
- Stream execution logs in real-time

### REST API

Start the API server:

```bash
python -m app.api.server
# or
uvicorn app.api.server:app --reload
```

#### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/info` | API information |

#### Test Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/tests/run` | Start a test run |
| `GET` | `/api/v1/tests/{run_id}` | Get test run status |
| `DELETE` | `/api/v1/tests/{run_id}` | Stop running test |
| `GET` | `/api/v1/stream/{run_id}` | SSE stream of execution events |

#### Feature Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/features` | List saved features |
| `POST` | `/api/v1/features/save` | Save feature content |
| `GET` | `/api/v1/features/{id}` | Get feature details |
| `POST` | `/api/v1/generate/feature` | Generate feature from user story |
| `POST` | `/api/v1/generate/enhance` | Enhance existing feature |

#### UI Brain

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/brain/capture` | Capture DOM snapshot |
| `POST` | `/api/v1/brain/resolve` | Resolve element selector |
| `POST` | `/api/v1/brain/dom/snapshot` | Get DOM snapshot |

#### Remote Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| `WebSocket` | `/api/v1/remote/ws` | Client connection endpoint |
| `POST` | `/api/v1/remote/clients` | List connected clients |
| `POST` | `/api/v1/remote/run` | Run test on specific client |
| `GET` | `/api/v1/remote/run/{run_id}/stream` | Stream remote execution events |

#### Results

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/results` | Get test results |
| `GET` | `/api/v1/results/summary` | Execution summary |

### Example API Usage

```bash
# Generate a feature
curl -X POST http://localhost:8000/api/v1/generate/feature \
  -H "Content-Type: application/json" \
  -d '{"user_story": "As a user, I want to login to the system"}'

# Run tests
curl -X POST http://localhost:8000/api/v1/tests/run \
  -H "Content-Type: application/json" \
  -d '{"feature_files": ["features/login.feature"]}'

# Run on remote client
curl -X POST http://localhost:8000/api/v1/remote/run \
  -H "Content-Type: application/json" \
  -d '{"client_id": "client-1", "feature_content": "Feature: ..."}'
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
    "model": "claude-sonnet-4-20250514",
    "timeout": 120,
    "max_retries": 3
  },
  "storage": {
    "database_path": "ghost_qc.db",
    "reports_dir": "reports"
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8000
  }
}
```

Or use environment variables:

```bash
# Browser settings
export GHOST_QC_HEADLESS=true
export GHOST_QC_SLOW_MO=100
export GHOST_QC_TIMEOUT=30000

# AI settings
export GHOST_QC_AI_MODEL=claude-sonnet-4-20250514
export GHOST_QC_AI_TIMEOUT=120
export GHOST_QC_AI_RETRIES=3
export GHOST_QC_USE_CLI=false  # Use API by default
export ANTHROPIC_API_KEY=your-api-key

# API settings
export GHOST_QC_API_HOST=0.0.0.0
export GHOST_QC_API_PORT=8000
```

### Programmatic Usage

```python
from app.executor.runner import AutonomousTestRunner
from app.generator import FeatureGenerator, GenerationConfig
from app.storage import TestResultRepository

# Run tests
runner = AutonomousTestRunner(headless=True)
result = await runner.run_feature("features/login.feature")
print(f"Status: {result.status}")

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

Ghost-QC includes intelligent selector definitions for popular UI frameworks:

- **Material-UI (MUI)**: Buttons, TextFields, Select, Dialogs, Tables, etc.
- **Ant Design**: All major components
- **Bootstrap**: Forms, Modals, Navbars, Cards, etc.
- **PrimeReact**: DataTable, Calendar, Dialog, etc.
- **Chakra UI**: All major components

## UI Brain

The UI Brain provides intelligent DOM analysis:

- **Element Classification**: Automatically identifies interactive elements (buttons, inputs, links, etc.)
- **Self-Healing Selectors**: Generates robust selectors that adapt to minor DOM changes
- **Element Descriptors**: Creates human-readable descriptions for elements
- **Page Snapshots**: Stores DOM state for analysis and debugging
- **Confidence Scoring**: Rates selector reliability

## Reports

Test reports are generated in both HTML and JSON formats:

```
reports/
├── test_report_20240118_143022.html
├── test_report_20240118_143022.json
└── screenshots/
    └── failed_step_1.png
```

## Tech Stack

**Backend:**
- Python 3.10+
- FastAPI (REST API)
- Playwright (Browser automation)
- SQLite (Database)
- Anthropic SDK / Claude CLI (AI)
- SSE-Starlette (Server-Sent Events)

**Frontend:**
- React 18
- TypeScript
- Vite
- Tailwind CSS

**Communication:**
- WebSockets (Remote clients)
- Server-Sent Events (Log streaming)

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

# Frontend linting
cd frontend && npm run lint
```

## Troubleshooting

### Claude CLI not found

Ensure Claude CLI is installed globally:

```bash
npm install -g @anthropic-ai/claude-cli
```

Or use the Anthropic API instead:

```bash
export GHOST_QC_USE_CLI=false
export ANTHROPIC_API_KEY=your-api-key
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

### Remote client connection issues

Ensure the server is accessible and the WebSocket endpoint is correct:

```bash
# Check server is running
curl http://localhost:8000/api/v1/health

# Connect client with verbose logging
python client/cli.py --server ws://localhost:8000/api/v1/remote/ws --name "test-client" --verbose
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request
