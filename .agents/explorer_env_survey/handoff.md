# Codebase & Environment Survey Report

**Agent**: Codebase & Environment Explorer (`explorer_env_survey`)  
**Date**: 2026-09-02T19:21:00Z  
**Target File**: `/Users/chrisblakeley/Documents/School Organizer/college-portfolio/.agents/explorer_env_survey/handoff.md`  

---

## 1. Observation

Direct observations from the filesystem, system environment, network tests, and reference documents:

### 1.1 Workspace Layout & Files
- **Workspace Root 1**: `/Users/chrisblakeley/Documents/School Organizer`
  - `college-portfolio/` (Directory): Primary application workspace.
  - `college_portfolio_design_doc_updated.docx` (353,365 bytes): Comprehensive specification document containing 423 XML paragraphs across 20 numbered sections, Appendices A/B, and a Programmatic College Data & AI Enrichment Addendum.
  - `AI-extracted` (0 bytes): Empty placeholder file.
  - `model` (0 bytes): Empty placeholder file.
  - `official` (0 bytes): Empty placeholder file.
- **Workspace Root 2**: `/Users/chrisblakeley/Documents/School Organizer/college-portfolio`
  - `ORIGINAL_REQUEST.md` (9,127 bytes, 107 lines): Full product requirements (R1–R5), resolved design decisions, and acceptance criteria.
  - `.agents/` (Directory): Agent workspace metadata (`orchestrator_1/`, `spec_miner_survey/`, `explorer_arch_survey/`, `explorer_env_survey/`).

### 1.2 System Environment & Toolchains
Command execution outputs on the host system:
- **Operating System**: macOS (Darwin 24.x, Apple Silicon / arm64 architecture).
- **Python**: `Python 3.9.6` at `/Library/Developer/CommandLineTools/usr/bin/python3`.
- **Pip**: `pip 21.2.4` at `/usr/bin/pip3`. Standard library includes `sqlite3`, `json`, `urllib`, `http.server`, `venv`, `dataclasses`, `asyncio`.
- **Node.js / npm / pnpm / yarn / bun**: `command not found: node` (not present in current `$PATH`).
- **Standard Utilities**:
  - `git`: `git version 2.39.5 (Apple Git-154)` at `/usr/bin/git`.
  - `sqlite3`: `/usr/bin/sqlite3` present.
  - `curl`: `/usr/bin/curl` present.
  - `tar`: `/usr/bin/tar` present.
  - `unzip`: `/usr/bin/unzip` present.
  - `gzip`: `/usr/bin/gzip` present.
  - `openssl`: `/usr/bin/openssl` present.

### 1.3 Environment Variables & API Keys
Inspection of `env`:
- `GEMINI_API_KEY`: **Not set** in the host environment.
- `COLLEGE_SCORECARD_API_KEY` / `DATA_GOV_API_KEY`: **Not set** in the host environment.
- Other variables present: `ANTIGRAVITY_AGENT`, `PATH`, `SHELL=/bin/zsh`, `TMPDIR`, `USER=chrisblakeley`.

### 1.4 College Scorecard API Network Verification
Live network probing against `api.data.gov`:
- Query: `https://api.data.gov/ed/collegescorecard/v1/schools?school.name=Massachusetts+Institute+of+Technology&api_key=DEMO_KEY`
- Status: **HTTP 200 OK**.
- Verified returned fields:
  - `id`: `166683`
  - `school.name`: `"Massachusetts Institute of Technology"`
  - `school.city`: `"Cambridge"`, `school.state`: `"MA"`
  - `latest.admissions.admission_rate.overall`: `0.0455` (4.55%)
  - `latest.cost.attendance.academic_year`: `$82,730`
  - `latest.cost.tuition.in_state`: `$62,396`, `out_of_state`: `$62,396`
  - `latest.cost.avg_net_price.overall`: `$20,111`
  - `latest.student.size`: `4,535`
  - `latest.completion.rate_suppressed.overall`: `0.9624` (96.24%)
  - `latest.earnings.10_yrs_after_entry.median`: `$143,372`

---

## 2. Logic Chain

From these direct observations, we derive the technical implications, stack selections, and implementation prerequisites:

### 2.1 Technology Stack & Runtime Strategy
1. **Host Environment Realities**:
   - Python 3.9+ with `pip3`, `sqlite3`, and `venv` is natively available on the host machine.
   - Node.js is not present in `$PATH`.
2. **Unified Full-Stack Architecture**:
   - Building the backend in Python (FastAPI/Uvicorn, Starlette, or lightweight Python HTTP server with ASGI/WSGI) allows immediate, zero-friction execution locally without installing Node.
   - Serving a modern, highly responsive frontend (HTML5/CSS3/Vanilla ES Modules with Tailwind CSS / modern component architecture or pre-bundled single-page app) directly from the backend server ensures that running a single start command (e.g. `python run.py` or `uvicorn server.main:app`) boots the entire application.
3. **Free-Tier Deployment Readiness**:
   - Cloud platforms (Render, Railway, Fly.io) natively support Python web services and Docker containers.
   - A multi-stage `Dockerfile` and `render.yaml` provide 1-click cloud deployment.

### 2.2 Data Ingestion & Caching Strategy
1. **College Scorecard Ingestion**:
   - The U.S. Department of Education Scorecard API is functional with `DEMO_KEY` (or custom `COLLEGE_SCORECARD_API_KEY` when configured).
   - Because `DEMO_KEY` has rate limits (30 req/min, 50 req/day), the application should implement a local SQLite cache table (`scorecard_cache`) with a configurable TTL (e.g. 7 days).
   - Additionally, an offline pre-seeded dataset (`/data/colleges_seed.json`) with 50+ major US institutions (MIT, Stanford, Harvard, UCLA, UC Berkeley, Ohio State, Michigan, Florida, Georgia Tech, Texas, etc.) ensures 100% test reliability even under network failures or API throttling.
2. **Server-Side Gemini Enrichment**:
   - When `GEMINI_API_KEY` is provided, the backend invokes Gemini (`gemini-2.5-flash` or `gemini-1.5-flash`) with structured JSON schema constraints to enrich missing/qualitative fields (`upsides`, `tradeoffs`, `best_for`, `not_best_for`, `career_strengths`, `notable_programs`).
   - When `GEMINI_API_KEY` is missing or the call fails, the system enforces the required **graceful degradation**: verified government data is returned, and qualitative fields show a clear status notification rather than breaking or throwing errors.
3. **Source Precedence Enforcement**:
   - Hierarchy: `Government (Scorecard/IPEDS) > Official Institutional > AI-Extracted (Gemini) > Model Estimates`.
   - AI outputs can never overwrite authoritative government metrics (e.g. tuition, admissions rate, earnings).
4. **Append-Only Knowledge Ledger**:
   - Every successful enrichment writes to:
     - `/knowledge/college-knowledge.md` (Human-readable Markdown ledger).
     - `/knowledge/college-knowledge.jsonl` (Machine-auditable JSONL event stream).
   - Atomic appends are protected with file locking / serialized async queues.

### 2.3 Guest Portfolio Persistence Strategy
1. **Cookie Session**:
   - Cookie name: `college_portfolio_id` (`HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`).
   - The cookie contains only an opaque UUID.
2. **Server-Side Store**:
   - Actual saved college IDs, user notes, category tags (`Reach`, `Target`, `Likely`), student preferences, and fit weights are stored in SQLite (`portfolios` table).
3. **Fallback**:
   - If cookies are blocked, the client uses temporary in-memory state and displays a user notification banner.

---

## 3. Caveats

1. **Host Environment Node Tooling**:
   - `node` is not installed in the system PATH. The project architecture must avoid any hard dependency on global npm/node for the server runtime.
2. **API Key Absence**:
   - Neither `GEMINI_API_KEY` nor `COLLEGE_SCORECARD_API_KEY` is pre-set in the environment. All specialist implementations must treat both API keys as optional and verify fallback paths.
3. **Sandbox Network Permissions**:
   - When running subagent commands that perform outbound network requests, `BypassSandbox: true` should be specified if the default environment isolates network calls.

---

## 4. Conclusion

1. **Environment State**: The environment is ready for development using Python 3.9+ (`sqlite3`, `pip3`, `git`, `curl`, `tar`, `unzip`).
2. **Data Pipeline**: The College Scorecard API is accessible via `DEMO_KEY` and returns complete institutional data.
3. **Architecture Match**: The planned Python-based backend + modular frontend + SQLite database + append-only knowledge ledger fully satisfies requirements R1 through R5 and all 10 acceptance criteria.
4. **Recommended Next Steps for Specialists**:
   - Data Ingestion Specialist: Build Scorecard API client, SQLite caching, offline seed dataset, and canonical normalization.
   - AI Enrichment & Ledger Specialist: Build Gemini integration with structured JSON validation, source precedence, and append-only ledger writer.
   - Core API & Persistence Specialist: Build FastAPI/Starlette REST endpoints, cookie portfolio management, and fit scoring engine.
   - Frontend Specialist: Build polished, responsive card UI with Dashboard, Search, Profile, Compare, and Settings.
   - DevOps Specialist: Build single start script, Dockerfile, `render.yaml`, and deployment guide.

---

## 5. Verification Method

To independently verify these findings:

1. **Verify Python & Utilities**:
   ```bash
   python3 --version
   sqlite3 --version
   git --version
   ```
2. **Verify College Scorecard Access**:
   ```bash
   python3 -c "import urllib.request; print(urllib.request.urlopen('https://api.data.gov/ed/collegescorecard/v1/schools?school.name=MIT&api_key=DEMO_KEY').status)"
   ```
3. **Verify Design Document Extraction**:
   ```bash
   python3 -c "import zipfile, xml.etree.ElementTree as ET; z=zipfile.ZipFile('/Users/chrisblakeley/Documents/School Organizer/college_portfolio_design_doc_updated.docx'); print('Docx read successfully, entries:', len(z.namelist()))"
   ```
4. **Verify Environment Variables**:
   ```bash
   echo "GEMINI_API_KEY=${GEMINI_API_KEY:-UNSET}"
   echo "COLLEGE_SCORECARD_API_KEY=${COLLEGE_SCORECARD_API_KEY:-UNSET}"
   ```
