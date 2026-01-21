"""
API Server Module

FastAPI application setup and server runner.
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import router
from .brain_routes import router as brain_router


def create_app(
    title: str = "Ghost-QC API",
    version: str = "1.0.0",
    cors_origins: Optional[list] = None,
) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        title: API title
        version: API version
        cors_origins: Allowed CORS origins

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=title,
        version=version,
        description="""
# Ghost-QC API

Autonomous test execution framework powered by AI with UI Brain integration.

## Features

- **Test Execution**: Run Gherkin feature files with AI-powered step interpretation
- **Feature Generation**: Generate Gherkin features from user stories
- **Feature Enhancement**: Improve existing features with additional test cases
- **Results Management**: Track and analyze test execution history
- **UI Brain**: Intelligent DOM analysis and self-healing element resolution

## Quick Start

1. Generate a feature: `POST /api/v1/generate/feature`
2. Run tests: `POST /api/v1/tests/run`
3. Check results: `GET /api/v1/tests/{run_id}`

## UI Brain Endpoints

- Capture page brain: `POST /api/v1/brain/capture`
- Execute scenario: `POST /api/v1/brain/execute/scenario`
- Execute feature: `POST /api/v1/brain/execute/feature`
- Resolve element: `POST /api/v1/brain/resolve`
- Get DOM snapshot: `POST /api/v1/brain/dom/snapshot`
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Add CORS middleware
    origins = cors_origins or ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(router, prefix="/api/v1")
    app.include_router(brain_router, prefix="/api/v1")

    # Serve frontend
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    # Root endpoint - serve frontend
    @app.get("/", tags=["System"])
    async def root():
        frontend_file = Path(__file__).parent.parent.parent / "frontend" / "index.html"
        if frontend_file.exists():
            return FileResponse(str(frontend_file))
        return {
            "name": "Ghost-QC API",
            "version": version,
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc),
            },
        )

    return app


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1,
    log_level: str = "info",
):
    """
    Run the API server.

    Args:
        host: Host to bind to
        port: Port to listen on
        reload: Enable auto-reload (development)
        workers: Number of worker processes
        log_level: Logging level
    """
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is required to run the server.")
        print("Install it with: pip install uvicorn")
        return

    uvicorn.run(
        "app.api.server:create_app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=log_level,
        factory=True,
    )


# Create default app instance for uvicorn
app = create_app()


if __name__ == "__main__":
    run_server(reload=True)
