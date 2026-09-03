"""API Routes Package."""
from server.routes.health import router as health_router
from server.routes.colleges import router as colleges_router
from server.routes.portfolio import router as portfolio_router
from server.routes.compare import router as compare_router
from server.routes.knowledge import router as knowledge_router
from server.routes.stats import router as stats_router

__all__ = [
    "health_router",
    "colleges_router",
    "portfolio_router",
    "compare_router",
    "knowledge_router",
    "stats_router",
]

