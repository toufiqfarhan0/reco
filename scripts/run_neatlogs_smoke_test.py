"""Run live Neatlogs smoke test event.

Sends exactly ONE structured telemetry event/span to Neatlogs using
the configured NEATLOGS_API_KEY and NEATLOGS_BASE_URL.
Never prints or leaks credentials.
"""

import json
import os
import sys
import time

from dotenv import load_dotenv

# Ensure reco is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reco.config import get_settings
from reco.observability.tracer import NeatlogsTracer


def run_smoke_test() -> int:
    load_dotenv()
    get_settings.cache_clear()
    settings = get_settings()

    api_key = settings.neatlogs_api_key or os.getenv("NEATLOGS_API_KEY", "")
    base_url = settings.neatlogs_base_url or os.getenv("NEATLOGS_BASE_URL", "")

    if not api_key:
        print("[ERROR] NEATLOGS_API_KEY is not configured in .env")
        return 1

    print("==================================================")
    print("RECO — STEP 15B: NEATLOGS LIVE SMOKE TEST")
    print("==================================================")
    print(f"Service Name: reco")
    print(f"Base URL: {base_url}")
    print(f"Observability Enabled: True (forced for smoke test)")
    print(f"Key Configured: {'[REDACTED]' if api_key else 'None'}")
    print("--------------------------------------------------")

    # Construct NeatlogsTracer with enabled=True
    tracer = NeatlogsTracer(
        api_key=api_key,
        base_url=base_url,
        enabled=True,
        timeout_seconds=5.0,
        service_name="reco",
    )

    print(f"Target OTLP Endpoint: {tracer.endpoint}")
    print("Sending live smoke test span...")

    t0 = time.time()
    result = tracer.send_smoke_test(environment="smoke_test")
    duration_ms = int((time.time() - t0) * 1000)

    print("--------------------------------------------------")
    print(f"HTTP Result Status: {result.get('status_code', 'unknown')}")
    print(f"Success: {result.get('success', False)}")
    print(f"Roundtrip Latency: {duration_ms} ms")
    print(f"Tracer Stats: {json.dumps(tracer.stats, indent=2)}")
    print(f"Payload Attributes Sent: {json.dumps(result.get('metadata', {}), indent=2)}")
    print("==================================================")

    if result.get("success") and tracer.stats["errors"] == 0:
        print("[SUCCESS] Neatlogs live smoke test passed cleanly!")
        return 0
    else:
        print(f"[FAILURE] Neatlogs smoke test did not succeed: {result.get('error')}")
        return 1


if __name__ == "__main__":
    sys.exit(run_smoke_test())
