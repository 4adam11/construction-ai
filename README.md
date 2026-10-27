# BuildSense AI: Multimodal Construction Intelligence Platform

A full-stack decision-support system for construction professionals. It uses a React frontend, a FastAPI backend and a multimodal LLM (Claude) to analyse site photos, text notes and structured project data.

| Feature | Input | Endpoint |
|---|---|---|
| Safety monitoring (PPE, hazards, violations) | Site photo + context | `POST /api/safety/analyze` (multipart) |
| Crack detection & analysis | Crack photo + element | `POST /api/cracks/analyze` (multipart) |
| Real estate valuation | Property data | `POST /api/valuation/estimate` (JSON) |
| Project planning (phases, cost, resources, risks) | Project brief | `POST /api/planning/generate` (JSON) |
| Daily site assistant | Raw notes + optional photo | `POST /api/daily/report` (multipart) |
| Weather-aware advisory | City + activities (live Open-Meteo forecast) | `POST /api/weather/advisory` (JSON) |
| Construction knowledge assistant | Question + chat history | `POST /api/knowledge/ask` (JSON) |

## Architecture

```
React (Vite, :5174) ──/api proxy──▶ FastAPI (:8000) ──▶ Claude (vision + structured outputs)
                                         └──────────▶ Open-Meteo (weather data)
```

**Strict JSON contracts.** Each feature's output is a Pydantic model in `backend/app/schemas.py`. The same model is:
1. sent to Claude as a structured-output schema (`client.messages.parse(output_format=Model)`), so the model can only return valid JSON of that shape;
2. used as FastAPI's `response_model`, so the API validates what it returns.

Every response, including errors, uses one envelope, and `frontend/src/api.js` checks it:

```json
{ "success": true, "feature": "safety", "mode": "live", "data": { ... }, "error": null }
```

**Mock mode.** If `ANTHROPIC_API_KEY` is not set, the backend returns deterministic sample or rule-based data in the same schemas. The full UI works offline and costs nothing. The sidebar shows which mode is active.

## Run it

Backend (Python 3.10+):

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # macOS/Linux: .venv/bin/python
cp .env.example .env        # add ANTHROPIC_API_KEY for live AI
.venv/Scripts/python -m uvicorn app.main:app --port 8000
```

Frontend (Node 18+):

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5174
```

Interactive API docs: http://localhost:8000/docs

## Configuration (`backend/.env`)

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | (empty) | Enables live AI. Empty means mock mode |
| `CLAUDE_MODEL` | `claude-opus-5-5` | Model ID |
| `CLAUDE_EFFORT` | `medium` | `low` / `medium` / `high`: depth vs. speed and cost |
| `CLAUDE_FALLBACKS` | `true` | If the model declines a request, the API re-runs it on a fallback model |
| `MOCK_MODE` | `auto` | `auto`, `true` or `false` |
| `CORS_ORIGINS` | `http://localhost:5174` | Allowed frontend origins |

## Project layout

```
backend/app/
  main.py            FastAPI app, CORS, error envelope
  config.py          env settings
  schemas.py         JSON data contracts (Pydantic)
  llm.py             Claude wrapper: images + structured output + error mapping
  weather.py         Open-Meteo geocoding & forecast
  mock.py            offline responses in the same schemas
  routers/features.py  the 7 feature endpoints
frontend/src/
  api.js             fetch helpers that enforce the envelope
  components/ui.jsx  shared UI (cards, badges, image drop, result states)
  features/*.jsx     one screen per feature
  App.jsx            layout, navigation, dashboard
```

AI output supports professional judgement. It does not replace inspection by a qualified engineer.
