#!/usr/bin/env python
"""Convenience script to start the Reco FastAPI server."""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reco.main import main

if __name__ == "__main__":
    main()
