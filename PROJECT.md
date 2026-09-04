# Project: College Portfolio — 7 New Features (R1 to R7)

## Architecture
- **Backend Architecture**:
  - FastAPI application in `server/main.py` launched by `run.py`.
  - Pydantic v2 data models in `server/models/` (`canonical.py`, `portfolio.py`, `ledger.py`).
  - Business logic services in `server/services/` (`college_service.py`, `scorecard_client.py`, `fit_scorer.py`, `portfolio_store.py`, `aid_service.py`, `chances_service.py`, `scenario_service.py`).
  - REST API routers in `server/routes/` (`colleges.py`, `portfolio.py`, `compare.py`, `knowledge.py`, `health.py`, `stats.py`).
  - Anonymous guest persistence via `college_portfolio_id` HttpOnly cookie, backed by SQLite (`data/college_portfolio.db`) with in-memory fallback.
  - Data provenance and dual audit ledgers in `knowledge/` (`college-knowledge.md` and `college-knowledge.jsonl`).
- **Frontend Architecture**:
  - Zero-build vanilla JS Single Page Application (ESM modules) served statically by FastAPI.
  - Semantic HTML shell in `client/index.html`.
  - Unified CSS design system in `client/css/styles.css` (neutral slate/navy palette, subtle accents, professional typography, no emoji spam).
  - Hash-based SPA routing and state management in `client/js/app.js`.
  - API abstraction in `client/js/api.js` with `credentials: 'same-origin'`.
  - Page views in `client/js/pages/` exporting `async render(container, state, params)`.
  - Pure SVG/DOM reusable chart components in `client/js/components/`.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | R1: Financial Aid Offer Comparison | Input aid offers per saved college; side-by-side net cost comparison (sticker, total grants, net annual, 4-yr total, loan amortization payment, best-value highlight) | M1, M2, M3 | Follow-up 2026-09-03T17:41:50Z §R1 |
| 2 | R2: Deadline Calendar | Visual month calendar aggregating application deadlines (`priority_deadline`, `regular_deadline`, FAFSA, CSS Profile, scholarships), 14-day upcoming sidebar, 4-tier color coding | M1, M2, M3 | Follow-up 2026-09-03T17:41:50Z §R2 |
| 3 | R3: Essay Tracker | CRUD essay tracker (prompt, word limit, word count, draft status: Not Started/Drafting/Reviewing/Final, applied colleges, reuse badge) | M1, M2, M3 | Follow-up 2026-09-03T17:41:50Z §R3 |
| 4 | R4: Admissions Chances Estimator | Compare student GPA, SAT/ACT against Scorecard 25th/75th percentiles; Reach/Target/Likely/Safety gauge bar; component on profile and dashboard | M1, M2, M3 | Follow-up 2026-09-03T17:41:50Z §R4 |
| 5 | R5: "What If" Scenario Modeling | Temporary hypothetical overrides (major, residency in/out-of-state, aid, budget); recalculate fit score via `fit_scorer.evaluate_college_fit()` without persisting | M1, M2, M3 | Follow-up 2026-09-03T17:41:50Z §R5 |
| 6 | R6: Alumni Outcomes Deep Dive | Scorecard field-of-study earnings by major; sortable table and horizontal bar chart; highlight preferred majors; expandable section on profile page | M1, M2, M3 | Follow-up 2026-09-03T17:41:50Z §R6 |
| 7 | R7: Per-School Requirements Checklist | Checklist items per school (2 Teacher Recs, Portfolio, Interview, CSS Profile) with required/completed status; cross-school matrix and summary counts | M1, M2, M3 | Follow-up 2026-09-03T17:41:50Z §R7 |
| 8 | Regression Prevention & Backward Compatibility | All new portfolio fields Optional with defaults; existing 312 pytest tests continue to pass unmodified; server runs via `python run.py` | M1, M2, M3 | Follow-up 2026-09-03T17:41:50Z §Core |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Complete Backend Implementation | Models, services, routes, persistence, and backend unit/API tests for R1-R7; ensure 100% backward compatibility and passing existing 312 tests | none | DONE |
| M2 | Complete Frontend Implementation | Reusable components (`chances-gauge.js`, `outcomes-chart.js`, `requirements-matrix.js`), client pages (`aid-comparison.js`, `calendar.js`, `essays.js`, `what-if.js`), profile & dashboard & tracker enhancements, `app.js`, `api.js`, `styles.css` | M1 | DONE |
| M3 | Full Integration, E2E Testing & Audit | End-to-end integration tests for R1-R7, empty & multi-college states, server launch verification, regression run, and forensic integrity audit | M2 | DONE |

## Interface Contracts
### R1: Aid Offer Models & Comparison
- `FinancialAidOffer`:
  - `college_id: str`
  - `merit_aid: int = 0`
  - `need_based_grants: int = 0`
  - `institutional_grants: int = 0`
  - `outside_scholarships: int = 0`
  - `federal_loans: int = 0`
  - `work_study: int = 0`
  - `custom_sticker_price: Optional[int] = None`
  - Total grants = merit_aid + need_based_grants + institutional_grants + outside_scholarships
  - Net annual cost = sticker_price - total_grants
  - 4-year total cost = net_annual_cost * 4
  - Estimated monthly loan payment = amortization(federal_loans * 4, rate=0.055, n_months=120)
- Endpoints:
  - `POST /api/portfolio/aid/{college_id}`: save offer
  - `DELETE /api/portfolio/aid/{college_id}`: remove offer
  - `GET /api/portfolio/aid/comparison`: return side-by-side comparison with best-value highlight

### R2: Deadline Calendar
- Model: `ApplicationDeadlineEvent`:
  - `college_id: str`, `college_name: str`, `title: str`, `date: str` (YYYY-MM-DD), `deadline_type: str` ('application' | 'financial_aid' | 'scholarship' | 'decision')
- Endpoints:
  - `GET /api/portfolio/calendar`: aggregates deadlines across all saved colleges in portfolio, plus 14-day upcoming list

### R3: Essay Tracker
- Model: `EssayEntry`:
  - `id: str`, `prompt: str`, `word_limit: Optional[int] = None`, `current_word_count: int = 0`, `draft_status: str` ('Not Started' | 'Drafting' | 'Reviewing' | 'Final'), `colleges: List[str] = []`, `created_at: str`, `updated_at: str`
- Endpoints:
  - `GET /api/portfolio/essays`
  - `POST /api/portfolio/essays`
  - `PUT /api/portfolio/essays/{essay_id}`
  - `DELETE /api/portfolio/essays/{essay_id}`

### R4: Admissions Chances Estimator
- Model: `ChancesEstimate`:
  - `college_id: str`, `college_name: str`, `classification: str` ('Reach' | 'Target' | 'Likely' | 'Safety'), `gpa_status: dict`, `test_status: dict`, `overall_probability: float`, `acceptance_rate: float`
- Endpoints:
  - `GET /api/colleges/{college_id}/chances`: computes chances based on current student preferences
  - `GET /api/portfolio/chances`: computes chances for all saved colleges

### R5: What-If Scenario Modeling
- Model: `ScenarioOverrideRequest`:
  - `college_id: str`
  - `hypothetical_major: Optional[str] = None`
  - `is_in_state: Optional[bool] = None`
  - `annual_aid_amount: Optional[int] = None`
  - `budget_max_annual: Optional[int] = None`
- Endpoint:
  - `POST /api/portfolio/scenario`: evaluates fit with overrides using `fit_scorer.evaluate_college_fit()` and returns baseline vs what-if without persisting

### R6: Alumni Outcomes Deep Dive
- Model: `FieldOfStudyItem`:
  - `cip_code: str`, `major_title: str`, `credential_level: str`, `median_earnings: Optional[int]`, `median_debt: Optional[int]`, `is_preferred: bool`
- Endpoint:
  - `GET /api/colleges/{college_id}/field-of-study`: returns majors sorted by earnings with preferred majors flagged

### R7: Per-School Requirements Checklist
- Model: `ChecklistItem`:
  - `id: str`, `name: str`, `required: bool = True`, `completed: bool = False`, `deadline: Optional[str] = None`
- Extended `ApplicationTracker`:
  - `requirements: List[ChecklistItem] = Field(default_factory=list)`
- Endpoints:
  - `PUT /api/portfolio/tracker/{college_id}/checklist/{item_id}`: toggle item status
  - `POST /api/portfolio/tracker/{college_id}/checklist`: add custom requirement

## Code Layout
- `server/models/`:
  - `canonical.py`: Core college models
  - `portfolio.py`: Portfolio, preferences, tracker, aid offers, essays, checklist
- `server/services/`:
  - `college_service.py`: College data retrieval
  - `portfolio_store.py`: Persistence and CRUD for portfolios
  - `scorecard_client.py`: API queries including field-of-study
  - `fit_scorer.py`: Fit evaluation
  - `aid_service.py`: Financial aid comparison and loan amortization
  - `chances_service.py`: Chances classification algorithm
  - `scenario_service.py`: What-if simulation
- `server/routes/`:
  - `colleges.py`: College lookups, chances, field-of-study
  - `portfolio.py`: Saved colleges, preferences, tracker, aid, essays, calendar, scenario
- `client/js/components/`:
  - `chances-gauge.js`: R4 visual range bar
  - `outcomes-chart.js`: R6 major earnings table & bar chart
  - `requirements-matrix.js`: R7 cross-school checklist matrix
- `client/js/pages/`:
  - `aid-comparison.js`: R1 page (`#/aid`)
  - `calendar.js`: R2 page (`#/calendar`)
  - `essays.js`: R3 page (`#/essays`)
  - `what-if.js`: R5 page (`#/what-if`)
  - `profile.js`: R4 & R6 integrations
  - `dashboard.js`: R4 summary card
  - `tracker.js`: R7 checklist matrix integration
- `client/js/app.js`: SPA routing and nav updates
- `client/js/api.js`: API client methods
- `client/css/styles.css`: Styles for new components and pages
- `tests/`:
  - Existing tests: `test_api.py`, `test_canonical_models.py`, `test_fit_scorer.py`, `test_portfolio.py`, etc.
  - New test files:
    - `test_financial_aid.py`
    - `test_calendar.py`
    - `test_essay_tracker.py`
    - `test_chances_estimator.py`
    - `test_scenario_modeling.py`
    - `test_alumni_outcomes.py`
    - `test_requirements_checklist.py`
