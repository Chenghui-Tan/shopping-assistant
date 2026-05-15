# AI Shopping Assistant — MSBA Capstone

A decision-oriented conversational shopping assistant organized around a strict
trust boundary: Claude (Anthropic) handles natural-language work; the ranking
itself is deterministic, rule-based Python and never invokes the LLM. The
prototype covers smart displays, water bottles, and kitchen organizers (100
products scraped from Amazon and Target).

- **Backend**: FastAPI — sessions, preference elicitation, ranking, refinement, saved products, lifecycle
- **Frontend**: React + Vite — five-stage UI (Frustration → Questions → Recommendations → Why → Lifecycle)
- **Engine**: deterministic scoring in `recommendation_Algorithem/`
- **Data**: cleaned catalog at `data/clean/products_clean.json`

The final report (`docs/capstone_report_v11.pdf`) and slides
(`docs/capstone_presentation_v5.pdf`) describe the architecture, the
trust-boundary decision, and the scenario-based evaluation in detail.

## Setup

Two terminals.

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional. Use "placeholder" to force the deterministic fallback path.
export ANTHROPIC_API_KEY=placeholder

uvicorn main:app --reload --port 8000
```

Or from the repository root:

```bash
uvicorn backend.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

## Environment Variables

```bash
cp .env.example .env
```

- `ANTHROPIC_API_KEY` — optional. Enables LLM intent parsing, refine parsing,
  and richer explanation text. Use `placeholder` for offline/demo fallback
  mode; every Claude call has a deterministic Python fallback so the system
  runs end-to-end without an API key.

Real API keys are never committed (`.env` is gitignored).

## Demo Flow

1. Type a shopper frustration (or pick a sample prompt).
2. Answer the Stage-2 chip questions (sequence is category-specific).
3. Review the three differentiated picks (Best Fit / Budget / Stretch) and
   optionally expand all options.
4. Refine via free text, e.g.:
   - smart display: `larger screen`, `works with Google`, `no camera`
   - water bottle: `leakproof`, `larger capacity`, `under $20`
   - kitchen organizer: `expandable`, `clear`, `under $15`
5. Click **See why** for grounded explanation, preference checks, and
   trade-offs.
6. Continue to the Stage-5 lifecycle dashboard.

Scripted walkthroughs: `docs/demo_scenarios.md`.

## Tests

```bash
pytest backend/tests
cd frontend && npm run build
```

## Repository Layout

```
backend/                 FastAPI service + tests
frontend/                React + Vite app
recommendation_Algorithem/  Deterministic ranking engine
scripts/                 Playwright scrapers + ETL pipeline
data/clean/              Cleaned product catalog (100 SKUs)
docs/                    Final report, slides, figure build scripts
```
