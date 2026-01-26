"""FastAPI application for Telemetry Studio."""

import asyncio
import contextlib
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from telemetry_studio.api import command, editor, layouts, options, preview, render, templates, upload
from telemetry_studio.config import settings
from telemetry_studio.services.file_manager import file_manager
from telemetry_studio.services.job_manager import job_manager

# Configure logging to stdout with proper format
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,  # Override any existing configuration
)

# Set our package loggers to DEBUG
for logger_name in ["telemetry_studio", "telemetry_studio.api", "telemetry_studio.services"]:
    logging.getLogger(logger_name).setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


async def cleanup_task():
    """Background task to periodically clean up expired sessions and old jobs."""
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes
        # Clean up expired file sessions (only in upload mode, not local_mode)
        if not settings.local_mode:
            cleaned = file_manager.cleanup_expired()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired session(s)")
        # Clean up old render jobs (older than 24 hours)
        jobs_cleaned = await job_manager.cleanup_old_jobs(max_age_hours=24)
        if jobs_cleaned > 0:
            logger.info(f"Cleaned up {jobs_cleaned} old job(s)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown tasks."""
    # Startup: create cleanup task
    task = asyncio.create_task(cleanup_task())
    yield
    # Shutdown: cancel cleanup task
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Telemetry Studio",
        description="Web interface for telemetry video overlay configuration and preview",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Include API routers
    app.include_router(upload.router, prefix="/api", tags=["upload"])
    app.include_router(layouts.router, prefix="/api", tags=["layouts"])
    app.include_router(options.router, prefix="/api", tags=["options"])
    app.include_router(preview.router, prefix="/api", tags=["preview"])
    app.include_router(command.router, prefix="/api", tags=["command"])
    app.include_router(render.router, prefix="/api", tags=["render"])
    app.include_router(templates.router, tags=["templates"])
    app.include_router(editor.router, tags=["editor"])

    # Mount static files
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Serve unified app at root
    @app.get("/")
    async def root():
        """Serve the unified application page."""
        unified_html = static_dir / "unified" / "index.html"
        if unified_html.exists():
            return FileResponse(unified_html)
        # Fallback to old index
        return FileResponse(static_dir / "index.html")

    # Legacy routes - redirect to unified app
    @app.get("/editor")
    async def editor_page():
        """Redirect to unified app (editor is now integrated)."""
        unified_html = static_dir / "unified" / "index.html"
        if unified_html.exists():
            return FileResponse(unified_html)
        # Fallback to old editor
        editor_html = static_dir / "editor" / "index.html"
        if editor_html.exists():
            return FileResponse(editor_html)
        return FileResponse(static_dir / "index.html")

    # Legacy page (old main page)
    @app.get("/legacy")
    async def legacy_page():
        """Serve the old main page for backwards compatibility."""
        return FileResponse(static_dir / "index.html")

    return app


# Create app instance
app = create_app()
