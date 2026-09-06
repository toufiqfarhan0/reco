"""Live network verification of FastAPI endpoints."""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import threading
import time
import httpx
import uvicorn

from reco.api.app import app


def run_server():
    """Run uvicorn server in worker thread."""
    config = uvicorn.Config(app, host="127.0.0.1", port=8888, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


def main():
    print("Starting background server on http://127.0.0.1:8888 ...")
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    time.sleep(1.2)  # Wait for server to bind

    base_url = "http://127.0.0.1:8888"
    with httpx.Client(base_url=base_url, timeout=5.0) as client:
        # 1. Health check
        res_health = client.get("/health")
        print(f"GET /health -> HTTP {res_health.status_code}: {res_health.json()}")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "ok"

        # 2. Version check
        res_version = client.get("/version")
        print(f"GET /version -> HTTP {res_version.status_code}: {res_version.json()}")
        assert res_version.status_code == 200
        assert res_version.json()["version"] == "0.1.0"

    print("Live network endpoint verification SUCCESSFUL!")
    sys.exit(0)


if __name__ == "__main__":
    main()
