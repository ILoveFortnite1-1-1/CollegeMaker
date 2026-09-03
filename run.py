"""Application Launcher."""
import os
import uvicorn
from server.config import settings

if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.PORT))
    is_prod = os.environ.get("APP_ENV") == "production" or os.environ.get("RENDER") == "true" or os.environ.get("PORT") is not None
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=port,
        reload=not is_prod,
    )


