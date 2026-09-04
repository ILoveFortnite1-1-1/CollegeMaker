# Original User Request

## Initial Request — 2026-09-02T19:17:07Z

Build a full-stack College Portfolio web application — a polished, student-facing tool for discovering, comparing, and saving colleges without requiring an account. The app must be **publicly hosted on the internet** (free tier) so anyone can access it via a URL. Data is sourced programmatically from the U.S. Department of Education College Scorecard API and enriched via a server-side Gemini API call for any remaining gaps. Every data field carries source provenance (source name, retrieval date, confidence classification). An append-only knowledge ledger (Markdown + JSONL files) records every enrichment event for auditability. The UI should be clean, visually polished, and handle errors gracefully.

Working directory: /Users/chrisblakeley/Documents/School Organizer/college-portfolio
Integrity mode: development

Reference design document (comprehensive spec with data model, API contracts, component inventory, fit scoring model, and UI mapping): /Users/chrisblakeley/Documents/School Organizer/college_portfolio_design_doc_updated.docx

This is a .docx file. To read it, extract text from word/document.xml inside the zip. Headings are tagged with styles like Heading1, Heading2. The document contains 20 numbered sections plus appendices covering: product intent, design language, information architecture, college profile spec, data model, cookie strategy, AI enrichment pipeline, knowledge ledger, freshness/provenance, fit scoring, compare experience, accessibility, security, performance, acceptance criteria, implementation sequence, and a programmatic data enrichment addendum.

## Resolved Design Decisions

- "Reach / Target / Likely" college classification is **fixed** (not user-customizable categories).
- Account sync is **omitted entirely** — guest-only experience with cookie-based portfolio.
- Primary data source: **College Scorecard API** (government, free, no key required for basic access). Supplement with any additional public data the team finds useful.
- AI provider: **Gemini only** via server-side endpoint. The API key is read from the `GEMINI_API_KEY` environment variable (placeholder for now — the user will set it later). No fallback provider — on failure, show a user-friendly "try again later" message.
- Knowledge document storage: **local files** alongside the server (`/knowledge/college-knowledge.md` and `/knowledge/college-knowledge.jsonl`).
- No fields require manual review before display, but all AI-derived fields must be schema-validated before acceptance and must carry source provenance metadata.
- The tech stack is the team's choice — pick whatever produces the best result for a polished full-stack app.

## Requirements

### R1. Server-side API with data pipeline

A backend server that exposes a REST API for college data. It must:
- Look up colleges by querying the College Scorecard API for authoritative structured fields (admissions, cost, outcomes, enrollment, etc.).
- Normalize external responses into a canonical college record schema where each non-trivial field carries: value, source, retrieval date, and data classification (Reported / Calculated / AI-derived / Estimated).
- For fields missing from government data, call a server-side Gemini endpoint to fill gaps — require structured JSON responses, validate against a schema, and reject malformed data.
- Enforce source precedence: government data > official institutional data > AI-extracted data > model estimates. AI responses must never silently overwrite higher-confidence data.
- Expose endpoints for: getting a college profile, triggering enrichment/refresh, saving/removing colleges from a portfolio, and retrieving a comparison payload.
- The Gemini API key is never exposed to the frontend.

### R2. Frontend — dashboard, profiles, compare, and search

A web frontend that provides:
- **Portfolio dashboard** (`/`): shows saved colleges as cards, portfolio-level summary stats (saved count, average net price, admit-rate mix), and a search/add action.
- **College search/discovery** (`/colleges`): search by name at minimum.
- **College profile** (`/colleges/:id`): full profile with header (name, location, type, key stats, save button), tabbed or sectioned content (overview, cost, outcomes, admissions, academics), fit score with component breakdown, and source/freshness badges on data fields.
- **Comparison workspace** (`/compare`): side-by-side normalized comparison for 2–6 colleges across cost, outcomes, admissions, and fit.
- **Settings** (`/settings`): student priority weights for fit scoring, and a clear-portfolio control.
- Polished visual design: clean card-based layout, clear typography hierarchy, semantic color usage (blue primary, green positive, amber warning, red destructive), and data-confidence badges (Reported / Estimated / Projected / Qualitative).

### R3. Append-only knowledge ledger

Every successful enrichment writes an entry to:
- `college-knowledge.md` — human-readable append-only log.
- `college-knowledge.jsonl` — machine-auditable event stream with fields: event_id, college_id, run_id, field_path, old_value, new_value, source_ids, confidence, status, observed_at, committed_at.

A lookup for one college should benefit later lookups for the same college (cache/reuse previously enriched data).

### R4. Cookie-based guest portfolio

- A first-party `college_portfolio_id` cookie (opaque ID, Secure, HttpOnly, SameSite=Lax) identifies the anonymous portfolio.
- Actual saved college IDs are stored server-side, keyed by portfolio ID.
- Save/remove must work instantly without any login.
- Saved state persists across page reloads in the same browser.
- When cookies are blocked, fall back to in-memory state with a clear message that saving across reloads is unavailable.

### R5. Public deployment on a free hosting platform

The finished app must be deployable to a free hosting platform (e.g., Render, Railway, Fly.io, Firebase, or similar) so it is publicly accessible via a URL. Provide clear deployment instructions or scripts. The deployment must:
- Serve both the frontend and backend from a single deployed service (or coordinated services on the same platform).
- Work with environment variables for the `GEMINI_API_KEY` (set via the hosting platform's dashboard/secrets).
- Not require a credit card or paid plan for basic usage and low traffic.
- Include a README section or deployment guide with step-by-step instructions.

## Acceptance Criteria

### Server starts and serves the app
- [ ] Running a single start command (e.g., `npm start` or equivalent) launches both the backend server and serves the frontend.
- [ ] The app is accessible in a browser at localhost on a documented port.

### College lookup returns real data with provenance
- [ ] Searching for a well-known college (e.g., "MIT", "Stanford", "Ohio State") returns a profile with real data fields populated from the College Scorecard API.
- [ ] Each data field in the response includes source metadata (at minimum: source name and retrieval date).
- [ ] The profile page displays source/freshness indicators visibly on the UI.

### Save and remove persists via cookie
- [ ] Clicking save on a college profile stores it in the portfolio.
- [ ] Reloading the dashboard page shows the previously saved college still present.
- [ ] Removing a saved college removes it from the dashboard on the next load.

### Compare works for 2–6 colleges
- [ ] After saving at least 2 colleges, the compare view displays a side-by-side table with normalized metrics.
- [ ] Adding up to 6 colleges to compare does not break the layout.

### Enrichment fails gracefully
- [ ] When `GEMINI_API_KEY` is not set or the Gemini call fails, the college profile still displays available government data and shows a user-friendly message (not a stack trace) for the AI-enriched fields.
- [ ] The app does not crash or hang when the AI endpoint is unavailable.

### Knowledge ledger records enrichments
- [ ] After a successful Gemini enrichment, a new entry appears in both `college-knowledge.md` and `college-knowledge.jsonl` in the `/knowledge/` directory.
- [ ] The JSONL entry contains at minimum: college_id, field_path, new_value, source_ids, and a timestamp.

### UI is polished and usable
- [ ] The dashboard, profile, compare, and search pages all render without visual breakage at standard desktop viewport widths (1280px+).
- [ ] Interactive elements (save button, search, compare selection) provide visible feedback on interaction (loading states, confirmations).
- [ ] No browser console errors during normal usage flows (navigate dashboard → search → view profile → save → compare).

### Deployment is documented and functional
- [ ] The README or a deployment guide includes step-by-step instructions for deploying to at least one free hosting platform.
- [ ] The deployment configuration (e.g., Dockerfile, render.yaml, or platform config) is included in the project.
- [ ] The app can be deployed with environment variables for `GEMINI_API_KEY` without modifying source code.

## Follow-up — 2026-09-02T20:55:21Z

The user's computer died and has come back online. Please check on the orchestrator's progress and resume building the College Portfolio application. The working directory is /Users/chrisblakeley/Documents/School Organizer/college-portfolio. If the orchestrator stalled, re-dispatch it or pick up where things left off. The full prompt and requirements are in the ORIGINAL_REQUEST.md file.

## Follow-up — 2026-09-03T17:41:50Z

Add 7 new features to an existing College Portfolio web application. The app is a FastAPI + vanilla JS SPA at `/Users/chrisblakeley/Documents/School Organizer/college-portfolio`. Follow the existing architecture exactly: Pydantic v2 models in `server/models/`, FastAPI routes in `server/routes/`, service logic in `server/services/`, vanilla JS page modules in `client/js/pages/`, reusable chart components in `client/js/components/`, and hash-based SPA routing in `client/js/app.js`. The app uses cookie-based guest portfolios with no mandatory auth. Scorecard/IPEDS government data is already integrated. Keep the UI professional — avoid excessive emoji usage in the interface; use them sparingly if at all. Match the existing visual style (clean cards, metric displays, source badges, subtle color accents).

Working directory: /Users/chrisblakeley/Documents/School Organizer/college-portfolio
Integrity mode: development

## Requirements

### R1. Scholarship and Financial Aid Offer Comparison
Students can input financial aid offers (merit aid, need-based grants, federal loans, work-study, institutional grants, outside scholarships) for each saved college. The system displays a side-by-side net cost comparison across all schools with offers, showing sticker price, total grants, net annual cost, 4-year total cost, and estimated monthly loan payment at graduation. It highlights the best-value school. Sticker prices should be pre-filled from existing Scorecard cost data when available. This requires new Pydantic models, a new API route, modifications to the portfolio model to store aid offers per college, and a new client page.

### R2. Deadline Calendar
A visual month-view calendar page that aggregates all application deadlines across saved colleges. Deadlines come from the existing `ApplicationTracker` fields (`priority_deadline`, `regular_deadline`) plus new optional fields for FAFSA deadline, CSS Profile deadline, and named scholarship deadlines. Color-code by type (app deadline, financial aid, scholarship, decision date). Include an upcoming-deadlines sidebar showing the next 14 days. Requires a new API endpoint to aggregate deadlines and a new client page.

### R3. Essay Tracker
Students can create, update, and delete essay entries tracking prompt text, word limit, current word count, draft status (Not Started / Drafting / Reviewing / Final), and which colleges each essay applies to (enabling reuse tracking). The page shows essay cards with status indicators, word count progress, and a reuse badge ("Used for 3 schools"). Requires new models, CRUD API routes, storage in the portfolio, and a new client page.

### R4. Admissions Chances Estimator
Compare student GPA and SAT/ACT scores (from existing `StudentPreferences`) against each school's 25th/75th percentile ranges (from existing Scorecard admissions data). Display a visual gauge or range bar showing where the student falls. Classify as Reach/Target/Likely/Safety. Add this as a component on the college profile page and as a summary card on the dashboard. Requires a new service function, API endpoints, and a new reusable chart component.

### R5. "What If" Scenario Modeling
A page where students can toggle hypothetical changes — different major, in-state vs out-of-state residency, different aid amounts, different budget — and see how fit scores and costs change in real-time without persisting the changes. Reuse the existing `fit_scorer.evaluate_college_fit()` with temporary overrides. Display current vs. what-if side by side. Requires a new API endpoint and a new client page that reuses existing fit-ring and metric-card components.

### R6. Alumni Outcomes Deep Dive
Query Scorecard field-of-study data to show earnings by major at each school. Display as a sortable table and horizontal bar chart of top majors by earnings. Highlight the student's preferred majors if set in preferences. Add as an expandable section on the college profile page. Requires a new service function, API endpoint, and a new table/chart component.

### R7. Per-School Requirements Checklist
Extend the existing Application Tracker to include a requirements checklist per school — items like "2 Teacher Recs", "Portfolio", "Interview", "CSS Profile" — each with required/completed status. Show a cross-school requirements matrix on the tracker page (schools as columns, requirements as rows). Add a summary showing aggregated counts ("3 schools need CSS Profile"). This is NOT a full recommendation letter tracker — just a checklist of what each school requires. Modify existing tracker models and the tracker page.

## Acceptance Criteria

### Core Functionality
- [ ] All 7 features are implemented with working API endpoints that return valid JSON
- [ ] All new pages are accessible via hash routes in the SPA and appear in the navigation
- [ ] Financial aid comparison correctly calculates net cost = sticker price - total grants, 4-year totals, and monthly loan estimates
- [ ] Calendar page renders a month grid and populates deadlines from saved colleges' tracker data
- [ ] Essay CRUD operations (create, read, update, delete) work end-to-end through the API and UI
- [ ] Chances estimator correctly positions student stats relative to 25th/75th percentile ranges from Scorecard data
- [ ] Scenario modeling returns recalculated fit scores using the existing fit scorer with overrides applied, without persisting changes
- [ ] Outcomes by major displays data from Scorecard field-of-study queries
- [ ] Requirements checklist items can be added per school and toggled complete/incomplete

### Integration and Consistency
- [ ] All new models use Pydantic v2 BaseModel with proper validation
- [ ] All new routes follow the existing pattern: APIRouter with prefix, proper cookie handling via `_ensure_cookie`
- [ ] New portfolio fields are backward-compatible (Optional with defaults) so existing portfolios don't break
- [ ] New client pages follow the existing module pattern (export object with `async render(container, state)`)
- [ ] The existing test suite (`pytest tests/`) continues to pass without modification

### Verification
- [ ] `python run.py` starts the server without errors
- [ ] Each new API endpoint returns a 200 response with valid JSON when called with test data
- [ ] Navigation between all pages (existing and new) works without console errors
- [ ] The app renders correctly with zero saved colleges (empty states) and with multiple saved colleges

