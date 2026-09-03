"""Application Launcher."""
import uvicorn
from server.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "server.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )

