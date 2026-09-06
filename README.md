# Reco — Autonomous Agent Engineering System

Reco is an autonomous agent engineering system featuring a 5-stage visual engineering console (**BUILD**, **RUN**, **UNDERSTAND**, **IMPROVE**, **VALIDATE**), an empirical 4-axis scorecard, mutation engine, failure diagnostics, distributed tracing with Neatlogs, Supabase cloud persistence, and Dodo Payments monetization.

---

## Unified Single-Service Deployment Architecture (Render)

Reco is engineered as a unified single Web Service on Render, eliminating CORS issues and synchronizing frontend client releases with backend API versions.

- **Backend**: FastAPI (`reco/api/app.py`) serving core health APIs, monetization (`/billing/*`), and static files from `frontend/dist`.
- **Frontend**: Vite + React 19 (TypeScript, Tailwind CSS) Single Page Application (SPA).
- **SPA Routing**: Client-side SPA routes (e.g. `/stages/*`) automatically fall back to `frontend/dist/index.html` while preserving 404 semantics on `/api/*` and `/billing/*` endpoints.

### Render Web Service Specification (`render.yaml`)

```yaml
services:
  - type: web
    name: reco-web-service
    env: python
    buildCommand: npm install --prefix frontend && npm run build --prefix frontend && pip install -r requirements.txt
    startCommand: uvicorn reco.api.app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.4
      - key: DODO_PAYMENTS_ENVIRONMENT
        value: test_mode
```

---

## Local Development & Verification

### 1. Frontend Test Suite
```bash
npm test --prefix frontend
```

### 2. Frontend Production Vite Build
```bash
npm run build --prefix frontend
```

### 3. Backend Test Suite
```bash
python -m pytest tests/ -q
```

### 4. Run Unified Server Locally
```bash
uvicorn reco.api.app:app --host 0.0.0.0 --port 8000 --reload
```
Navigate to `http://localhost:8000` to access the console.
