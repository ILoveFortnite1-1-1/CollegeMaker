# College Portfolio E2E Test Suite Ready

The complete, opaque-box, requirement-driven E2E test suite has been implemented in `/Users/chrisblakeley/Documents/School Organizer/college-portfolio/tests/`.

## Test Suite Inventory & Coverage

| Tier | File | Scope / Focus | Test Count | Minimum Required | Status |
|:-----|:-----|:--------------|:----------:|:----------------:|:------:|
| **Tier 1** | `tests/test_tier1_features.py` | Feature Isolation (All 16 features, >=5 tests per feature) | **83** | ≥ 80 | **READY** |
| **Tier 2** | `tests/test_tier2_boundaries.py` | Boundaries, Corner Cases, Negative Inputs, Rate Limits | **84** | ≥ 80 | **READY** |
| **Tier 3** | `tests/test_tier3_pairwise.py` | Pairwise Cross-Feature Interactions (16 pairs) | **16** | ≥ 16 | **READY** |
| **Tier 4** | `tests/test_tier4_scenarios.py` | Real-World Student User Journey Workflows | **10** | ≥ 8 | **READY** |
| **Total** | | **Comprehensive Tiers 1-4 Suite** | **193** | ≥ 184 | **READY** |

---

## 16 Core Features Verified in Tier 1

1. **Health & Status API** (`GET /api/health`): Verifies database, Scorecard, Gemini AI, and knowledge ledger health.
2. **Canonical College Data Schema**: Verifies Pydantic canonical models, metrics dictionaries, and classifications.
3. **Scorecard Ingestion & Normalization**: Verifies admissions, costs, graduation rates, SAT/ACT, earnings.
4. **Offline Caching & Seed Data**: Verifies 50+ pre-seeded US flagship institutions and offline reliability.
5. **College Discovery & Faceted Search** (`GET /api/colleges`): Verifies query search, state filter, type filter, cost/admit filters, sorting, and pagination.
6. **College Detail & Profile** (`GET /api/colleges/:id`): Verifies canonical profile, overview, costs, admissions, outcomes, and field-level provenance.
7. **Server-Side Gemini Enrichment** (`POST /api/colleges/:id/refresh`): Verifies structured qualitative insights (strengths, upsides, tradeoffs), schema validation, and key safety.
8. **Strict Source Precedence Hierarchy**: Verifies `government > official_institutional > reputable_secondary > ai_extracted > model_estimate > user`.
9. **Field-Level Provenance Metadata**: Verifies source attribution, retrieval timestamp, confidence rating, and classification badge.
10. **Append-Only Markdown Ledger** (`/knowledge/college-knowledge.md`): Verifies human-readable audit trail generation and append-only semantics.
11. **Machine-Auditable JSONL Stream** (`/knowledge/college-knowledge.jsonl`): Verifies atomic event logging with required schema fields and JSON validity.
12. **Guest Cookie Portfolio Persistence**: Verifies `college_portfolio_id` cookie, session isolation, and server-side portfolio linkage.
13. **Portfolio Tagging & Notes CRUD** (`/api/portfolio/*`): Verifies saving, updating notes/labels, removing colleges, and clearing portfolio.
14. **8-Dimension Fit Scoring Model**: Verifies composite calculation across Career, ROI, Academic, Admissions, Experience, Strength, Location, Cost.
15. **Multi-College Comparison API** (`GET /api/compare`): Verifies 2 to 6 college normalized matrix, best-in-class highlights, and validation.
16. **Single-Service Serving & Static Assets**: Verifies root HTML serving, CSS/JS static delivery, and SPA route fallback.

---

## How to Execute the Test Suite

### 1. Standalone Python Test Runner (No external dependencies required)

```bash
# Run the complete test suite (Tiers 1-4, 193 test cases)
python3 tests/test_runner.py

# Run with verbose per-test reporting
python3 tests/test_runner.py -v

# Run only a specific tier (e.g. Tier 1, Tier 2, Tier 3, or Tier 4)
python3 tests/test_runner.py -t 1
python3 tests/test_runner.py -t 2
python3 tests/test_runner.py -t 3
python3 tests/test_runner.py -t 4

# Run specific test subsets using keyword filter
python3 tests/test_runner.py -k compare
python3 tests/test_runner.py -k portfolio

# Target a custom server host / port
python3 tests/test_runner.py --base-url http://localhost:8000
```

### 2. Pytest Runner (When pytest is installed)

```bash
python3 -m pytest tests/
python3 -m pytest tests/test_tier1_features.py -v
python3 -m pytest tests/test_tier2_boundaries.py -v
python3 -m pytest tests/test_tier3_pairwise.py -v
python3 -m pytest tests/test_tier4_scenarios.py -v
```

---

## Exit Codes & Semantics

- **`0`**: 100% tests passed.
- **`1`**: One or more test failures / errors detected.
