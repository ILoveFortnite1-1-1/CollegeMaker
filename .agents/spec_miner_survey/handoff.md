# SPECIFICATION MINING REPORT: Full-Stack College Portfolio Platform

**Author**: Specification Miner (`spec_miner_survey`)  
**Date**: 2026-09-02  
**Target Project**: College Portfolio Web Application  
**Authoritative Sources**: 
- `college_portfolio_design_doc_updated.docx` (Generic product specification v1.0)
- `ORIGINAL_REQUEST.md`

---

## 1. Observation

Directly extracted and verified from the authoritative design doc and project requirements:

1. **Product Purpose & Core Architecture**: A standalone, zero-account web application for high school and transfer students to discover, evaluate, compare, and organize colleges into a personalized portfolio, backed by transparent fit scoring, authoritative government data (U.S. Dept. of Education College Scorecard & IPEDS), server-side Gemini AI enrichment, field-level provenance metadata, first-party cookie persistence, and an append-only knowledge ledger.
2. **Hybrid Ingestion & Source Hierarchy**:
   - Master Database acts as runtime structured source of truth.
   - External Structured Sources: U.S. College Scorecard API & IPEDS provide authoritative quantitative metrics (costs, admissions, graduation, earnings, enrollment).
   - Server-Side Gemini Enrichment: Invoked *only* for missing/stale/qualitative data (upsides, tradeoffs, program strengths, recruiting insights, persona fit).
   - Strict Precedence Hierarchy:
     1. Government / Official Structured Data (College Scorecard, IPEDS)
     2. Official Institution Documents & Common Data Set (CDS)
     3. Reputable Primary/Secondary Sources
     4. AI-Extracted/Synthesized Insights (Gemini)
     5. Model Estimates / Projections
     6. User Overrides / Notes
3. **Guest Session & Cookie Persistence**:
   - Cookie Name: `college_portfolio_id` (or `student_portfolio_id`)
   - Opaque random UUID lookup key only (`HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`, long-lived 1-year renewable).
   - Server-side portfolio store holds saved colleges (`college_id`, `status` [reach/target/likely], `saved_at`, `user_note`, `custom_label`), `fit_weights`, and `preferences`.
   - In-memory / sessionStorage fallback when cookies are blocked, with user-facing notification.
4. **Append-Only Knowledge Ledger**:
   - `/knowledge/college-knowledge.md`: Canonical human-readable Markdown ledger recording every enrichment run, provider, model, query, pulled facts, confidence, sources, and unresolved unknowns.
   - `/knowledge/college-knowledge.jsonl`: Machine-auditable fact stream with atomic line-delimited events (`event_id`, `college_id`, `run_id`, `field_path`, `old_value`, `new_value`, `source_ids`, `confidence`, `status`, `observed_at`, `committed_at`).
5. **UI & Routing Specifications**:
   - `/`: Dashboard (Portfolio Summary, Saved School Cards, Insights Row [Cost vs Earnings, Fit Rank], Quick Add, Fit Weight Adjustment).
   - `/colleges`: College Discovery (Faceted search, location/state, ownership, campus size, cost range, acceptance rate, pagination).
   - `/colleges/:id`: College Profile (Hero with key stats strip, Tabs: Overview, Upside/Tradeoffs, ROI & Cost, Career Outcomes, Admissions & Academics, Student Life, Evidence & Provenance Drawer).
   - `/compare`: Comparison Workspace (2–6 colleges side-by-side, normalized rows, best-in-class highlights, visual diffs, row pinning, export).
   - `/settings`: Preferences (Student priorities, fit weight sliders, privacy/cookie controls, data clearing).
6. **Production & Free-Tier Hosting**:
   - Containerized multi-stage Docker build.
   - Render / Railway / Fly.io deployment configs with environment variable isolation (`COLLEGE_SCORECARD_API_KEY`, `GEMINI_API_KEY`, `SESSION_SECRET`).
   - Comprehensive README deployment and verification guide.

---

## 2. Logic Chain & System Architecture Inferences

1. **Separation of Concerns**: The browser must never communicate directly with the Gemini API or hold API secrets. The server acts as a secure mediation gateway that validates requests, caches data in SQLite/PostgreSQL, queries College Scorecard, formats strict schema-bounded prompts for Gemini, validates responses with Zod/JSON-Schema, enforces source precedence, updates the DB and Knowledge Ledger, and returns clean sanitized payloads to the client.
2. **Deterministic Graceful Degradation**: If Scorecard or Gemini is unavailable or rate-limited, the system serves cached or partial records without breaking UI layouts. Missing data points lower the confidence band of the Fit Score rather than penalizing the college.
3. **Data Integrity & Prompt-Injection Defense**: External scraped snippets and unverified text are treated strictly as untrusted data in delimited fields; system instructions instruct the model to produce strict JSON conforming to schema. Model output is parsed and validated by the backend before persistence.

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | R1: Ingestion | College Scorecard API Integration | Fetches authoritative federal data for ~6,000+ US higher ed institutions | Search query, unitid/name, zip/distance, state, ownership, size range | Canonical college record with admissions, costs, outcomes, enrollment | Falls back to cached DB or partial record; retries on transient network errors | Design Doc §8, §Programmatic College Data |
| 2 | R1: Ingestion | Server-Side Gemini Enrichment | Synthesizes qualitative insights, upsides, tradeoffs, career recruiting, persona fit | College canonical name, location, missing field list | Validated structured JSON with fields, sources, confidence, unknowns | Returns existing data, logs enrichment failure, flags `status: failed`, shows retry action | Design Doc §8.1-§8.3, §15 |
| 3 | R1: Ingestion | Source Precedence Enforcement | Reconciles conflicting data points across federal, institutional, AI, and user layers | New field value, source type, existing field metadata | Updated canonical field or dual evidence retention with `needs_review` | Lower-tier source rejected from overwriting higher-tier source; conflict logged | Design Doc §10, §Source Precedence |
| 4 | R2: Provenance | Field-Level Provenance Tracking | Attaches origin, timestamp, confidence (0.0-1.0), and status classification to every metric | Incoming raw/calculated data point | Metric object: `{ value, unit, year, source, confidence, status }` | Missing provenance defaults to `status: estimated`, `confidence: 0.5` | Design Doc §6, §10, §5.2 |
| 5 | R2: Provenance | Append-Only Markdown Ledger | Appends human-readable audit entry for every enrichment run | Run metadata, new/changed facts, unknowns, source URLs | Appended section in `/knowledge/college-knowledge.md` | Non-blocking file append; creates file if missing | Design Doc §9.1-§9.2, Appendix B |
| 6 | R2: Provenance | Machine-Auditable JSONL Ledger | Writes single atomic JSON event line per changed fact | Fact update event payload | Appended JSON line in `/knowledge/college-knowledge.jsonl` | File write error logged to server stderr; does not abort user response | Design Doc §9.1, Appendix B |
| 7 | R3: Persistence | Cookie-Based Guest Portfolio | Assigns anonymous `college_portfolio_id` cookie to guest sessions; links to server store | HTTP Cookie header, Save college request | HTTP Set-Cookie header (`HttpOnly`, `Secure`, `SameSite=Lax`), saved portfolio | In-memory fallback if cookies blocked + banner notification | Design Doc §7, §568 |
| 8 | R3: Persistence | Portfolio Tagging & Notes | Allows student to categorize saved schools as Reach/Target/Likely and attach private notes | `collegeId`, `status`, `user_note`, `custom_label` | Updated `PortfolioCollege` record | Returns 404 if college not in portfolio, 400 for invalid tag | Design Doc §6, §7 |
| 9 | R4: Decision Engine | Adjustable Fit Scoring Engine | Calculates 0–100 composite fit score across 8 weighted dimensions with student customization | College metrics, student weights (`career`, `roi`, `academic`, `admissions`, etc.) | Composite score (0-100), label, component breakdown, confidence rating | Graceful degradation for missing dimensions without zeroing total score | Design Doc §11, §5.2 |
| 10 | R4: UI | Portfolio Dashboard (`/`) | Main landing page displaying saved schools, portfolio signals (avg net price, earnings, admit mix), insights | Guest cookie, portfolio state | Rendered cards, metrics summary, charts, quick add bar | Empty state with starter recommendations if 0 colleges saved | Design Doc §3, §4 |
| 11 | R4: UI | College Search & Discovery (`/colleges`) | Faceted search with filters for location, type, cost, selectivity, size, and sorting | Query string, filter params, sort key, page number | Paginated list of college preview cards with save/compare actions | Empty state with suggested filter resets if no matches found | Design Doc §4, §18 |
| 12 | R4: UI | College Profile (`/colleges/:id`) | Comprehensive institutional dossier with tabbed deep dives, key stats strip, upside/tradeoffs | College ID or slug | Profile hero, Overview, Upside/Tradeoffs, ROI/Cost, Outcomes, Academics, Provenance Drawer | 404 page with search fallback if ID unknown; triggers async enrichment if stale | Design Doc §5, §8.2 |
| 13 | R4: UI | Side-by-Side Comparison (`/compare`) | Compares 2–6 colleges in normalized tabular grid with visual diffs, row pinning, export | Query param `ids=id1,id2,...` | Side-by-side comparison matrix, best-in-class highlights, CSV/print export | Prompt to add colleges if < 2 selected; caps at 6 colleges with alert | Design Doc §4, §12 |
| 14 | R4: UI | Settings & Preferences (`/settings`) | Student preferences, fit weight sliders, cookie management, portfolio data reset | User input for weights, student profile, clear data action | Updated portfolio preferences, cookie deletion / reset | Validates weights sum to 100% or auto-normalizes | Design Doc §4, §11 |
| 15 | R5: DevOps | Free-Tier Hosting & Docker Config | Production containerization and PaaS deploy configurations | Docker build args, environment variables | Multi-stage Docker image, `render.yaml` / `railway.json` blueprint, deployment docs | Healthcheck endpoint (`/api/health`) validates service readiness | ORIGINAL_REQUEST.md, Design Doc |

---

## 4. Edge Cases & Handling

| # | Feature | Input / Scenario | Observed / Required Behavior |
|---|---------|------------------|-----------------------------|
| 1 | Cookie Persistence | Cookies disabled in browser | Gracefully fall back to client-side session state; display non-intrusive warning banner informing user data will reset on browser close. |
| 2 | Search Ingestion | User searches for unindexed or misspelled college name | Perform fuzzy matching against local DB; if no match, query College Scorecard API search; if still missing, trigger Gemini AI lookup. |
| 3 | Gemini Enrichment | Gemini API rate limit, quota exhaustion, or network timeout | Return existing DB record immediately; flag background run as `failed`; display subtle \"Data from previous cycle - Retry refresh\" badge. |
| 4 | Data Validation | Gemini returns hallucinated fields or invalid JSON | Server Zod schema validator rejects malformed payload; valid subset accepted into quarantine/staging; invalid payload never touches production metrics table. |
| 5 | Prompt Injection | Scraped website excerpt contains prompt injection attempts | Input is isolated in strict JSON data strings; system prompt reinforces extraction-only role; model cannot execute actions or write directly to DB. |
| 6 | Source Conflict | Gemini estimates tuition at $45,000 but College Scorecard reports $42,150 | Precedence hierarchy enforces Scorecard value ($42,150); Gemini estimate logged in evidence history as lower-tier comparison without overwriting canonical field. |
| 7 | Fit Scoring | School is missing graduation rate or median earnings | Calculate fit score using remaining weighted dimensions; normalize over available weights; lower overall confidence score indicator (e.g. \"Medium Confidence\"). |
| 8 | Comparison Workspace | User selects 1 college or more than 6 colleges | If 1 college: render prompt to select a second college; if > 6: disable adding further colleges with toast notification explaining 6-school comparison limit. |
| 9 | Knowledge Ledger | Concurrent enrichment runs attempt to write to `college-knowledge.md` / `jsonl` | Use atomic file append locks or serialized async queue to prevent write collisions and interleaved JSON lines. |
| 10 | Data Clearing | User clicks \"Clear Portfolio\" in Settings | Remove all `PortfolioCollege` associations from server DB, delete `college_portfolio_id` cookie, reset client state, and redirect to clean Dashboard. |

---

## 5. Detailed Schema & Technical Specifications

### 5.1 Canonical College Entity Schema
```typescript
export interface CanonicalCollege {
  id: string; // URL-safe slug e.g. "university-of-michigan-ann-arbor"
  unitid?: string; // IPEDS/Scorecard UNITID e.g. "170976"
  name: string;
  aliases: string[];
  location: {
    city: string;
    state: string;
    zip?: string;
    country: string;
    localeType: 'urban' | 'suburban' | 'town' | 'rural' | 'other';
  };
  type: 'public' | 'private_nonprofit' | 'private_for_profit' | 'other';
  yearFounded?: number;
  websiteUrl?: string;
  priceCalculatorUrl?: string;
  logoUrl?: string;
  lastRefreshedAt: string; // ISO 8601
  dataStatus: 'complete' | 'partial' | 'stale' | 'needs_refresh';
  
  metrics: {
    enrollment?: MetricField<number>;
    acceptanceRate?: MetricField<number>; // ratio 0.0 - 1.0
    graduationRate?: MetricField<number>; // ratio 0.0 - 1.0
    studentFacultyRatio?: MetricField<number>;
    averageSat?: MetricField<number>;
    averageAct?: MetricField<number>;
    tuitionInState?: MetricField<number>;
    tuitionOutOfState?: MetricField<number>;
    averageNetPrice?: MetricField<number>;
    netPriceByIncome?: {
      tier0_30k?: MetricField<number>;
      tier30_48k?: MetricField<number>;
      tier48_75k?: MetricField<number>;
      tier75_110k?: MetricField<number>;
      tier110k_plus?: MetricField<number>;
    };
    medianEarnings10Yr?: MetricField<number>;
    medianEarnings6Yr?: MetricField<number>;
    medianDebtAtGraduation?: MetricField<number>;
    retentionRate?: MetricField<number>;
    pellGrantPercentage?: MetricField<number>;
  };
  
  qualitative: {
    academicStrengths: string[];
    businessStrengths: string[];
    financeOpportunities: string[];
    notablePrograms: string[];
    upsides: EvidenceClaim[]; // 3-7 claims
    tradeoffs: EvidenceClaim[]; // 3-7 claims
    bestFor: string[]; // student persona patterns
    notBestFor: string[];
    campusLifeSummary?: string;
  };
}

export interface MetricField<T> {
  value: T;
  unit?: string; // 'usd', 'ratio', 'count', 'score'
  year?: number | string;
  source: 'college_scorecard' | 'ipeds' | 'common_data_set' | 'gemini' | 'user' | 'fallback';
  sourceUrl?: string;
  confidence: number; // 0.0 to 1.0
  status: 'reported' | 'calculated' | 'ai_derived' | 'estimated' | 'projected' | 'qualitative';
  updatedAt: string;
}

export interface EvidenceClaim {
  claim: string;
  explanation: string;
  sourceType: string;
  sourceUrl?: string;
  confidence: number;
}
```

### 5.2 Server-Side Gemini Prompt & JSON Output Schema
```json
{
  "college": {
    "canonicalName": "string",
    "aliases": ["string"],
    "location": {
      "city": "string",
      "region": "string",
      "country": "string",
      "localeType": "urban|suburban|town|rural"
    },
    "type": "public|private_nonprofit|private_for_profit|other",
    "yearFounded": 1817,
    "qualitative": {
      "academicStrengths": ["string"],
      "businessStrengths": ["string"],
      "financeOpportunities": ["string"],
      "notablePrograms": ["string"],
      "upsides": [
        {
          "claim": "Top-tier engineering research output",
          "explanation": "Consistently ranked in top 10 nationally for funded research labs.",
          "source": "https://...",
          "confidence": 0.88
        }
      ],
      "tradeoffs": [
        {
          "claim": "High out-of-state tuition burden",
          "explanation": "Limited institutional merit aid available for non-residents.",
          "source": "https://...",
          "confidence": 0.85
        }
      ],
      "bestFor": ["Research-driven STEM students", "High-activity campus seekers"],
      "notBestFor": ["Students requiring ultra-small seminar sizes in year 1"]
    },
    "supplementaryMetrics": [
      {
        "path": "metrics.studentFacultyRatio",
        "value": 15,
        "unit": "ratio",
        "year": 2025,
        "confidence": 0.85,
        "sources": ["https://..."],
        "status": "reported"
      }
    ]
  },
  "unknowns": ["metrics.netPriceByIncome.tier110k_plus"],
  "notes": ["Verified against 2024-2025 Common Data Set"]
}
```

### 5.3 Knowledge Ledger Formats

#### Markdown Ledger (`/knowledge/college-knowledge.md`):
```markdown
# Master College Knowledge Ledger
*Append-Only Audit Record of Institutional Discoveries & Enrichments*

---

## College: University of Michigan - Ann Arbor
### Enrichment: 2026-09-02T19:25:00Z | Run: run_umich_8f93a1
- **Provider / Model**: Google Gemini / gemini-2.5-flash
- **Trigger / Query**: Profile load & missing qualitative metrics
- **Status**: complete

#### Facts Pulled or Updated
- `qualitative.academicStrengths`: Computer Science, Mechanical Engineering, Business Administration [Confidence: 0.90, Status: qualitative]
  - Sources: https://umich.edu/academics, https://nces.ed.gov/collegenavigator/?id=170976
- `qualitative.upsides`: 4 evidence-linked benefits recorded [Confidence: 0.88, Status: qualitative]
- `qualitative.tradeoffs`: 3 verified structural tradeoffs recorded [Confidence: 0.85, Status: qualitative]
- `metrics.studentFacultyRatio`: 15:1 [Year: 2025, Confidence: 0.92, Status: reported]
  - Sources: 2024-2025 Common Data Set Section I

#### Unknown / Unresolved Fields
- None

---
```

#### JSONL Stream (`/knowledge/college-knowledge.jsonl`):
```jsonl
{"event_id":"evt_89f1a23c","college_id":"university-of-michigan-ann-arbor","run_id":"run_umich_8f93a1","field_path":"qualitative.academicStrengths","old_value":null,"new_value":["Computer Science","Mechanical Engineering","Business Administration"],"source_ids":["scorecard","gemini_enrichment"],"confidence":0.90,"status":"qualitative","observed_at":"2026-09-02T19:25:00Z","committed_at":"2026-09-02T19:25:00Z"}
{"event_id":"evt_89f1a23d","college_id":"university-of-michigan-ann-arbor","run_id":"run_umich_8f93a1","field_path":"metrics.studentFacultyRatio","old_value":null,"new_value":15,"source_ids":["common_data_set_2025"],"confidence":0.92,"status":"reported","observed_at":"2026-09-02T19:25:00Z","committed_at":"2026-09-02T19:25:00Z"}
```

---

## 6. Caveats

1. **Scorecard API Key Limits**: The federal College Scorecard API via api.data.gov has standard free rate limits (1,000 requests/hour). Local SQLite caching must be implemented to minimize API calls and prevent 429 errors.
2. **Gemini Free Quotas**: Free-tier Google Gemini API has rate limits (RPM/RPD). Enrichment calls should only trigger for genuinely missing or stale fields (TTL: e.g. 7 days for qualitative, 30 days for quantitative), with query deduplication.
3. **No Account Sync**: Per v1.0 specifications, guest sessions rely purely on the first-party opaque cookie identifier. Cross-device syncing is out of scope for v1.0 but architected cleanly so that account binding can be introduced later without schema rewrites.

---

## 7. Conclusion

The specifications across R1 through R5 are complete, exhaustive, and rigorously verified against the authoritative Word design document and ORIGINAL_REQUEST.md. All key architectural requirements—including Scorecard API ingestion, Gemini structured enrichment, field-level provenance, source precedence hierarchy, cookie-based session persistence, fit scoring engine, comparison workspace, append-only knowledge ledger, and free-tier Docker/PaaS deployment—are fully mapped and ready for specialist implementation.

---

## 8. Verification Method

To verify the completeness and correctness of these specifications:
1. **Design Doc Cross-Reference**: Check each section against `/Users/chrisblakeley/Documents/School Organizer/college_portfolio_design_doc_updated.docx`.
2. **Schema Validation**: Verify that TypeScript interfaces cover all fields in Section 6 & Section 8.3 of the design doc.
3. **Endpoint Contracts**: Verify that the REST endpoints match Table in Section 8.2 and Section 566.
4. **Knowledge Ledger Structure**: Verify compatibility with Appendix B file/event conventions.
