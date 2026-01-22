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
from .streaming import router as streaming_router
from app.remote.routes import router as remote_router
from app.config import get_config


def create_app(
    title: str = "Ghost-QC API",
    version: str = "1.0.0",
    cors_origins: Optional[list] = None,
    api_prefix: Optional[str] = None,
) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        title: API title
        version: API version
        cors_origins: Allowed CORS origins
        api_prefix: API route prefix (default: /api/v1)

    Returns:
        Configured FastAPI application
    """
    # Get configuration
    config = get_config()

    # Use provided values or fall back to config
    if api_prefix is None:
        api_prefix = config.api.api_prefix
    if cors_origins is None:
        cors_origins = config.api.cors_origins

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
    origins = cors_origins if cors_origins else ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes with configurable prefix
    app.include_router(router, prefix=api_prefix)
    app.include_router(brain_router, prefix=api_prefix)
    app.include_router(streaming_router, prefix=api_prefix)
    app.include_router(remote_router, prefix=api_prefix)

    # Serve frontend - check for built frontend in dist/ or fallback to dev
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"

    if frontend_dist.exists():
        # Serve production build assets
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    elif frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    # Root endpoint - serve frontend
    @app.get("/", tags=["System"])
    async def root():
        # Check for production build first
        frontend_dist_file = Path(__file__).parent.parent.parent / "frontend" / "dist" / "index.html"
        if frontend_dist_file.exists():
            return FileResponse(str(frontend_dist_file))
        # Fallback to dev
        frontend_file = Path(__file__).parent.parent.parent / "frontend" / "index.html"
        if frontend_file.exists():
            return FileResponse(str(frontend_file))
        return {
            "name": "Ghost-QC API",
            "version": version,
            "base_url": config.api.base_url,
            "docs": "/docs",
            "health": f"{api_prefix}/health",
            "endpoints": {
                "health": f"{config.api.base_url}{api_prefix}/health",
                "tests": f"{config.api.base_url}{api_prefix}/tests",
                "features": f"{config.api.base_url}{api_prefix}/features",
                "generate": f"{config.api.base_url}{api_prefix}/generate",
                "brain": f"{config.api.base_url}{api_prefix}/brain",
            }
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
    host: str = None,
    port: int = None,
    reload: bool = None,
    workers: int = None,
    log_level: str = "info",
):
    """
    Run the API server.

    Args:
        host: Host to bind to (default: from config)
        port: Port to listen on (default: from config)
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

    # Get config for defaults
    config = get_config()

    # Use provided values or fall back to config
    server_host = host if host is not None else config.api.host
    server_port = port if port is not None else config.api.port
    server_reload = reload if reload is not None else config.api.reload
    server_workers = workers if workers is not None else config.api.workers

    print(f"Starting Ghost-QC API server at http://{server_host}:{server_port}")
    print(f"API endpoints available at: http://{server_host}:{server_port}{config.api.api_prefix}/")
    print(f"Health check: http://{server_host}:{server_port}{config.api.api_prefix}/health")

    uvicorn.run(
        "app.api.server:create_app",
        host=server_host,
        port=server_port,
        reload=server_reload,
        workers=server_workers,
        log_level=log_level,
        factory=True,
    )


# Create default app instance for uvicorn
app = create_app()


if __name__ == "__main__":
    run_server(reload=True)
