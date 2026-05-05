# AI Shopping Assistant

Decision-support shopping assistant for the capstone demo. The app combines:

- a FastAPI backend for sessions, preference elicitation, recommendations, refinement, saved products, and lifecycle support
- a React/Vite frontend for the five-scene demo flow
- a local cleaned product catalog in `data/clean/products_clean.json`
- optional Anthropic-powered parsing/explanations with deterministic fallbacks when no API key is available

## Fresh Setup

Use two terminals.

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional. Use "placeholder" to force deterministic fallback behavior.
export ANTHROPIC_API_KEY=placeholder

uvicorn main:app --reload --port 8000
```

The backend can also be started from the repository root:

```bash
uvicorn backend.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Environment Variables

Copy `.env.example` if you want a local reference file:

```bash
cp .env.example .env
```

Important variables:

- `ANTHROPIC_API_KEY`: optional. Enables LLM intent parsing, refinement parsing, and richer explanation text. Use `placeholder` for offline/demo fallback mode.
- `VITE_API_BASE_URL`: documented for deployment clarity. The current frontend code uses `http://localhost:8000` directly in `frontend/src/api.js`.

Do not commit real API keys. `.env` files are ignored by `.gitignore`.

## Demo Flow

1. Start with one of the sample prompts or type a shopper frustration.
2. Answer Scene 2 preference questions.
3. Review the three differentiated picks and optionally expand all options.
4. Use the refine bar, for example:
   - smart display: `larger screen`, `works with Google`, `no camera`
   - water bottle: `leakproof`, `larger capacity`, `under $20`
   - kitchen organizer: `expandable`, `clear`, `under $15`
5. Click `See why` to show grounded explanation, preference checks, and trade-offs.
6. Continue to lifecycle support to show post-purchase assistant value.

For scripted walkthroughs, see `docs/demo_scenarios.md`.

## Validation Commands

```bash
pytest backend/tests
cd frontend && npm run build
```

`npm run lint` currently reports existing frontend lint issues unrelated to backend runnability.
