"""Executable entrypoint for running the Reco API server."""

import uvicorn
from reco.api.app import app
from reco.config import get_settings


def main():
    """Run the Uvicorn server using centralized settings."""
    settings = get_settings()
    uvicorn.run(
        "reco.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=(settings.app_env == "development"),
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
