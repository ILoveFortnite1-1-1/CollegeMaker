"""FastAPI Main Application Entrypoint."""
import os
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from server.config import settings
from server.routes.colleges import router as colleges_router
from server.routes.compare import router as compare_router
from server.routes.health import router as health_router
from server.routes.knowledge import router as knowledge_router
from server.routes.portfolio import router as portfolio_router
from server.routes.stats import router as stats_router
from server.services.scorecard import scorecard_service


def create_app() -> FastAPI:
    """Initialize FastAPI application with middleware, routes, and static assets."""
    app = FastAPI(
        title="College Portfolio API",
        description="Authoritative, provenance-tracked college discovery, fit-scoring, and comparison platform.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routers
    app.include_router(health_router)
    app.include_router(colleges_router)
    app.include_router(portfolio_router)
    app.include_router(compare_router)
    app.include_router(knowledge_router)
    app.include_router(stats_router, prefix="/api")


    # Global Exception Handlers
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "Not Found", "detail": str(getattr(exc, "detail", "Resource not found"))},
            )
        # For non-API routes, if client index.html exists, return index.html for SPA routing
        index_file = settings.CLIENT_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return JSONResponse(status_code=404, content={"error": "Not Found"})

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected server error occurred. Please try again later.",
            },
        )

    # Mount static assets if client folder exists
    client_dir = settings.CLIENT_DIR
    if client_dir.exists():
        css_dir = client_dir / "css"
        js_dir = client_dir / "js"
        if css_dir.exists():
            app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
        if js_dir.exists():
            app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")

        # Root and SPA fallback route
        @app.get("/", include_in_schema=False)
        async def serve_index():
            index_path = client_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return JSONResponse(
                content={"message": "College Portfolio API is running. Client build in progress."}
            )

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            if (
                full_path.startswith("api/")
                or full_path.startswith("docs")
                or full_path.startswith("redoc")
                or full_path.startswith("etc/")
                or full_path.startswith("var/")
                or full_path.startswith("tmp/")
                or full_path.startswith("usr/")
                or ".." in full_path
            ):
                return JSONResponse(status_code=404, content={"error": "Not Found"})
            file_path = client_dir / full_path
            if file_path.is_file():
                return FileResponse(file_path, headers={"Cache-Control": "no-cache, must-revalidate"})
            # Only serve index.html for known client SPA pages
            known_spa_prefixes = ["", "search", "colleges", "portfolio", "compare", "knowledge", "settings", "tracker"]
            first_segment = full_path.split("/")[0]

            if first_segment in known_spa_prefixes:
                index_path = client_dir / "index.html"
                if index_path.exists():
                    return FileResponse(index_path, headers={"Cache-Control": "no-cache, must-revalidate"})
            return JSONResponse(status_code=404, content={"error": "Not Found"})


    return app


app = create_app()
