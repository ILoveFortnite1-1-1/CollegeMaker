## 2026-09-02T20:56:00Z

You are the Full-Stack Backend & Data Pipeline Worker (teamwork_preview_worker).
Read the master specifications at:
- /Users/chrisblakeley/.gemini/antigravity/brain/0e2c5b44-6540-4fc9-845f-a02283fa349e/ORIGINAL_REQUEST.md
- /Users/chrisblakeley/.gemini/antigravity/brain/0e2c5b44-6540-4fc9-845f-a02283fa349e/PROJECT.md

Your working directory is:
/Users/chrisblakeley/Documents/School Organizer/college-portfolio/.agents/worker_backend

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your mission:
Implement the complete backend system for the College Portfolio web application in `/Users/chrisblakeley/Documents/School Organizer/college-portfolio/`:
1. `requirements.txt`: Python dependencies (`fastapi`, `uvicorn[standard]`, `pydantic>=2.0`, `httpx`, `pytest`, `python-multipart`, etc.).
2. `data/colleges_seed.json`: Bundled seed dataset with 50+ real flagship US universities with accurate metrics (MIT, Stanford, Harvard, UC Berkeley, UCLA, Michigan, Ohio State, Georgia Tech, Florida, UT Austin, NYU, Washington, Illinois, Purdue, Columbia, Yale, Princeton, Cornell, Penn, Northwestern, Duke, Vanderbilt, Rice, Johns Hopkins, UVA, UNC Chapel Hill, Wisconsin, Texas A&M, Indiana, Minnesota, Colorado Boulder, Arizona State, Penn State, Rutgers, Maryland, Virginia Tech, NC State, Pittsburgh, Miami, Boston University, USC, Emory, Georgetown, Carnegie Mellon, Tufts, Wake Forest, Dartmouth, Brown, Caltech, Notre Dame).
3. `server/models/`:
   - `canonical.py`: `CanonicalCollege`, `MetricField`, `ProvenanceField`, `Location`, `CostData`, `AdmissionsData`, `QualitativeData`, `EvidenceClaim`. All fields must include full provenance metadata (`value`, `source`, `source_type`, `year`, `confidence`, `status`, `retrieved_at`, `notes`).
   - `portfolio.py`: `StudentPortfolio`, `PortfolioCollege`, `Preferences`, `FitWeights`, `PortfolioSummary`.
   - `ledger.py`: `LedgerEvent`, `EnrichmentRun`, `KnowledgeEntry`.
4. `server/services/`:
   - `scorecard.py`: College Scorecard API query client (supports searching, filtering by state/type/cost/admit_rate, sorting, pagination) + SQLite disk cache (`data/college_portfolio.db`) with 7-day TTL + automatic fallback to `colleges_seed.json` when offline or key is missing.
   - `gemini.py`: Server-side Gemini 2.5/1.5 Flash client using structured JSON extraction, strict prompt-injection defense with input delimiters, Pydantic schema validation, and graceful degradation when offline or key is unset.
   - `precedence.py`: Source precedence merge engine (`government > official_institutional > reputable_secondary > ai_extracted > model_estimate > user`).
   - `ledger.py`: Append-only dual ledger manager for `/knowledge/college-knowledge.md` (human-readable Markdown audit log) and `/knowledge/college-knowledge.jsonl` (atomic line-delimited events) with `asyncio.Lock()` concurrency protection.
   - `portfolio.py`: Cookie-based guest portfolio manager (`college_portfolio_id`, `HttpOnly`, `SameSite=Lax`, `Path=/`) with SQLite storage and in-memory fallback.
   - `fit_scorer.py`: 8-dimension student-customizable Fit Scoring algorithm (Career 25%, ROI 20%, Academic 15%, Admissions 10%, Experience 10%, Strength 10%, Location 5%, Cost 5%) with missing-data weight normalization and Reach/Target/Likely classification.
   - `comparison.py`: Multi-college comparison engine for 2–6 colleges returning normalized side-by-side metric matrix, best-in-class highlights, and summary analytics.
5. `server/routes/`:
   - `health.py`: `GET /api/health`
   - `colleges.py`: `GET /api/colleges`, `GET /api/colleges/:id`, `POST /api/colleges/:id/refresh`
   - `portfolio.py`: `GET /api/portfolio`, `POST /api/portfolio/colleges`, `DELETE /api/portfolio/colleges/:collegeId`, `PUT /api/portfolio/preferences`, `DELETE /api/portfolio`
   - `compare.py`: `GET /api/compare?ids=...`
   - `knowledge.py`: `GET /api/knowledge/colleges/:id`, `GET /api/knowledge/export`
6. `server/main.py`: FastAPI application mounting all API routes, CORS middleware, cookie parser, error handlers, and static files mount.
7. Test your backend code thoroughly with unit/integration tests to ensure all endpoints respond correctly with proper status codes and schemas.
8. Write your handoff report to `/Users/chrisblakeley/Documents/School Organizer/college-portfolio/.agents/worker_backend/handoff.md` and notify orchestrator.
