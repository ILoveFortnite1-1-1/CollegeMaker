# 🎓 College Portfolio

> **Intelligent, Data-Driven Student College Planning Platform**  
> Transparent college discovery, side-by-side comparisons, personalized 8-dimension fit scoring, and server-side AI enrichment without requiring an account.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.115+-009688.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Pydantic v2](https://img.shields.io/badge/Validation-Pydantic_v2-E92063.svg?style=flat-square)](https://docs.pydantic.dev)
[![Gemini AI](https://img.shields.io/badge/Enrichment-Google_Gemini_2.5_Flash-4285F4.svg?style=flat-square&logo=google)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

---

## 📋 Table of Contents

1. [System Overview & Value Proposition](#-system-overview--value-proposition)
2. [Architecture & Technology Stack](#-architecture--technology-stack)
3. [Core Feature Walkthrough](#-core-feature-walkthrough)
4. [Data Provenance & Source Precedence](#-data-provenance--source-precedence)
5. [8-Dimension Fit Scoring Formula](#-8-dimension-fit-scoring-formula)
6. [Dual Append-Only Knowledge Ledger](#-dual-append-only-knowledge-ledger)
7. [Cookie-Based Guest Portfolio Security](#-cookie-based-guest-portfolio-security)
8. [Local Development Quickstart](#-local-development-quickstart)
9. [Environment Variables Reference](#-environment-variables-reference)
10. [REST API Documentation](#-rest-api-documentation)
11. [Production Cloud Deployment](#-production-cloud-deployment)
    - [Render Deployment](#1-render-blueprint-one-click)
    - [Railway Deployment](#2-railway)
    - [Fly.io Deployment](#3-flyio)
    - [Docker Container Build](#4-docker-container)
12. [Verification & Testing Suite](#-verification--testing-suite)

---

## 🌟 System Overview & Value Proposition

College Portfolio gives students a private, transparent, and data-driven workspace to discover universities, evaluate trade-offs, estimate actual net costs, project career earnings, and build a personalized portfolio of target institutions.

### Key Architectural Pillars
- **Zero Mandatory Accounts**: Students can start immediately. A secure, first-party cookie (`college_portfolio_id`) links to an anonymous server-side portfolio store with automatic in-memory fallback.
- **Certified Field-Level Provenance**: Every metric displays its authoritative source, retrieval date, and classification badge (`Reported`, `Calculated`, `AI-derived`, `Estimated`, `Qualitative`).
- **Server-Side AI Enrichment with Prompt-Injection Defense**: Google Gemini 2.5 Flash extracts qualitative insights (upsides, tradeoffs, student fit patterns) with strict schema validation. Untrusted web excerpts are isolated in data boundaries and cannot alter core institutional metrics.
- **Strict Source Precedence**: Government data (`Scorecard`/`IPEDS`) is immutable and strictly prioritized over AI estimates.
- **Dual Append-Only Knowledge Ledger**: Every fact ever discovered is permanently committed to human-readable Markdown (`/knowledge/college-knowledge.md`) and machine-auditable JSONL (`/knowledge/college-knowledge.jsonl`).

---

## 🏗 Architecture & Technology Stack

College Portfolio is deployed as a **single unified service** where FastAPI hosts both high-performance REST APIs at `/api/*` and serves compiled responsive SPA assets at `/`.

```
┌────────────────────────────────────────────────────────────────────────┐
│                          BROWSER CLIENT (SPA)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  Dashboard   │  │  Discovery   │  │   Profile    │  │  Compare   │  │
│  │   Route /    │  │ Route /colleges │ Route /colleges/:id│ Route /compare │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘  │
│         │                 │                 │                │         │
│         └─────────────────┼─────────────────┼────────────────┘         │
│                           ▼                 ▼                          │
│                   Client API Wrapper (client/js/api.js)                │
│                 [First-Party Cookie: college_portfolio_id]             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / HTTPS
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND SERVICE                         │
│                                                                        │
│  ┌─────────────────────────── REST ROUTES ──────────────────────────┐  │
│  │  /api/health            /api/colleges         /api/colleges/:id  │  │
│  │  /api/portfolio/*       /api/compare          /api/knowledge/*   │  │
│  └───────────────────────────────┬──────────────────────────────────┘  │
│                                  │                                     │
│  ┌──────────────────────── CORE SERVICES ───────────────────────────┐  │
│  │  • Scorecard Client & SQLite Cache (7-Day TTL)                    │  │
│  │  • Precedence Merge Engine (Gov > Inst > Secondary > AI)         │  │
│  │  • 8-Dimension Fit Scorer (Missing-Data Normalization)           │  │
│  │  • Gemini 2.5 Flash Structured JSON Extraction                   │  │
│  │  • Dual Append-Only Async Ledger Writer                           │  │
│  └───────────────────────────────┬──────────────────────────────────┘  │
│                                  │                                     │
│  ┌─────────────────────── PERSISTENCE & DATA ───────────────────────┐  │
│  │  • SQLite DB (Portfolios & Cache)  • Seed Data (50+ Flagships)   │  │
│  │  • /knowledge/college-knowledge.md • /knowledge/college-knowledge.jsonl │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📱 Core Feature Walkthrough

### 1. Portfolio Dashboard (`#/`)
- **Portfolio Summary Hero**: Real-time aggregated statistics including total saved count, average net price, 10-year median earnings, and Reach/Target/Likely balance pills.
- **Cost vs. Earnings Analytics**: Interactive SVG bar chart comparing annual net prices against 10-year graduate earnings.
- **Saved Institutions Grid**: Interactive cards displaying individual fit scores, custom student notes, and direct compare toggles.
- **Quick Add Search**: Instant search widget to add institutions directly from the home screen.

### 2. Search & Discovery (`#/colleges`)
- **Instant Search**: Debounced real-time query matching college names, cities, and aliases (e.g. "MIT", "Caltech", "Berkeley").
- **Faceted Filters**: Filter by 50 US states, Institution Type (Public, Private Non-profit, For-profit), Max Annual Net Price slider ($10k–$80k), and Acceptance Rate slider (0%–100%).
- **Multi-Parameter Sorting**: Sort by Name (A-Z/Z-A), Net Price (Low-High/High-Low), Graduate Earnings, or Selectivity.

### 3. College Detail Profile (`#/colleges/:id`)
- **Hero Stats Strip**: Total enrollment, Acceptance rate, 4-year graduation rate, Student-faculty ratio, Average net price, and 10-year median earnings.
- **5 Tabbed Intelligence Modules**:
  1. **Overview & Fit**: 8-dimension fit breakdown, Quick facts, Evidence-backed Upsides & Tradeoffs, Best For / Not Best For recommendations.
  2. **Costs & Financial Aid**: In-state vs. Out-of-state tuition, Cost of Attendance, Net Price by Family Income Tiers ($0-30k up to $110k+), Pell Grant rates, Median graduate debt.
  3. **Admissions & Selectivity**: Selectivity category, SAT 25th-75th percentiles (Math & Reading), ACT percentiles, alignment match against student profile.
  4. **Academics & Outcomes**: Top program majors distribution, Carnegie Research classification, graduation velocity, post-graduation earnings.
  5. **Data Provenance & Audit**: Full field-by-field audit table with links to original sources, retrieval timestamps, and exportable ledger streams.
- **Live AI Enrichment Refresh**: On-demand button triggering server-side Gemini research with live status indicator.

### 4. Comparison Workspace (`#/compare`)
- **Side-by-Side Matrix (2–6 Institutions)**: Normalized metrics with sticky headers and sticky metric column.
- **Best-in-Class Highlights**: Automatic visual highlighting for lowest net price, highest earnings, and highest graduation rate.
- **Comparative Visualizations**: Side-by-side bar charts for Cost vs. Earnings and an 8-axis Radar/Spider chart comparing fit dimensions.
- **CSV Export**: One-click spreadsheet export of the full comparison matrix.

### 5. Preferences & Settings (`#/settings`)
- **Student Profile**: Input High School GPA (0.00–4.00), SAT Score (400–1600), ACT Score (1–36), Annual Family Budget ($), Preferred State, and Target Majors.
- **8-Dimension Fit Weight Sliders**: Custom slider controls (0%–50%) with real-time percentage sum validation and reset to default weights.
- **Privacy & Session Controls**: View active anonymous `college_portfolio_id`, export portfolio as JSON, and clear local session.

---

## 🔍 Data Provenance & Source Precedence

Every individual data field carries full provenance metadata:
```json
{
  "value": 20232,
  "unit": "usd",
  "year": 2024,
  "source": "U.S. Department of Education College Scorecard",
  "source_type": "government",
  "confidence": 1.0,
  "status": "reported",
  "retrieved_at": "2026-09-02T18:00:00Z"
}
```

### Source Precedence Hierarchy
When new data is ingested, the system strictly enforces the following merge hierarchy:
$$\text{government} > \text{official\_institutional} > \text{reputable\_secondary} > \text{ai\_extracted} > \text{model\_estimate} > \text{user}$$

Government metrics (e.g. acceptance rates, graduation rates, net price) are **immutable** and cannot be overwritten by AI or automated scrapers.

---

## 📐 8-Dimension Fit Scoring Formula

The Fit Scorer evaluates each institution across 8 dimensions on a normalized scale $[0, 100]$:

$$\text{OverallScore} = \frac{\sum_{i=1}^{8} w_i \cdot s_i \cdot c_i}{\sum_{i=1}^{8} w_i \cdot c_i}$$

| Dimension | Default Weight ($w_i$) | Core Evaluated Inputs |
|---|:---:|---|
| **Career Outcomes** | **25%** | 10-year median earnings, graduation completion velocity, employer recruiting strength |
| **ROI / Value** | **20%** | Ratio of 10-year earnings to average net price, debt payback efficiency |
| **Academic Fit** | **15%** | Alignment with student's preferred major, Carnegie R1/R2 classification, student-faculty ratio |
| **Admissions Probability** | **10%** | Student GPA & SAT/ACT alignment against college 25th-75th percentile and admit rate |
| **Student Experience** | **10%** | First-to-second year retention rate, campus setting, 4-year completion rate |
| **Academic Strength** | **10%** | Program completion density in STEM, Business, Healthcare; faculty depth |
| **Location & Setting** | **5%** | Geographic match with student's target state/region |
| **Cost & Affordability** | **5%** | Proximity of net price to student's annual family budget |

### Missing Data Graceful Degradation
If data for dimension $k$ is missing ($c_k = 0$), the denominator dynamically excludes $w_k \cdot c_k$. Missing data lowers score confidence, but **never automatically penalizes a college with zero points**.

---

## 📜 Dual Append-Only Knowledge Ledger

Every data retrieval and AI enrichment run is permanently recorded in two append-only files in `/knowledge`:

1. **`knowledge/college-knowledge.md`** (Human-Readable Audit Ledger):
   ```markdown
   ## College: Massachusetts Institute of Technology (UnitID: 166683)
   ### Enrichment: 2026-09-02T19:20:00Z | Run: run_01J6ABC789
   - **Provider / Model**: Google / gemini-2.5-flash
   - **Request**: Structured qualitative enrichment
   - **Status**: Completed (5 facts committed)
   #### Facts Pulled / Updated
   - `qualitative.upsides`: ["World-class STEM research", "Unmatched alumni network"] [Confidence: 0.92, Status: AI-derived]
   ```

2. **`knowledge/college-knowledge.jsonl`** (Machine-Auditable Stream):
   ```json
   {"event_id":"evt_01J6ABC","college_id":"166683","run_id":"run_01J6ABC","field_path":"qualitative.upsides","old_value":null,"new_value":["World-class STEM research"],"source_ids":["src_gemini"],"confidence":0.92,"status":"ai_derived","observed_at":"2026-09-02T19:20:00Z","committed_at":"2026-09-02T19:20:01Z"}
   ```

---

## 🍪 Cookie-Based Guest Portfolio Security

- **Cookie Name**: `college_portfolio_id`
- **Security Flags**: `HttpOnly`, `SameSite=Lax`, `Path=/`, `Secure` (in production).
- **Privacy Standard**: No personal student information, passwords, or full college lists are stored inside the cookie. The cookie contains only an opaque session UUID linking to an encrypted server-side SQLite portfolio record.
- **Offline / Blocked Fallback**: If cookies are disabled in the user's browser, the application displays an explicit informational banner and falls back to in-memory session management.

---

## 🚀 Local Development Quickstart

### Prerequisites
- Python 3.9, 3.10, 3.11, or 3.12
- `pip` package manager

### 1-Command Setup & Run
```bash
# 1. Clone repository
git clone https://github.com/your-org/college-portfolio.git
cd college-portfolio

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start application
python run.py
```

Open your browser to **`http://localhost:8000`**.  
Interactive OpenAPI documentation is available at **`http://localhost:8000/docs`**.

---

## ⚙️ Environment Variables Reference

Configure environment variables in `.env` or in your cloud deployment dashboard:

| Variable | Description | Default / Fallback | Required |
|---|---|---|:---:|
| `PORT` | HTTP server port | `8000` | No |
| `HOST` | Network interface to bind | `0.0.0.0` | No |
| `APP_ENV` | Environment (`development` / `production`) | `development` | No |
| `GEMINI_API_KEY` | Google Gemini API key for AI qualitative enrichment | Mock/Degraded fallback | Optional |
| `COLLEGE_SCORECARD_API_KEY` | Data.gov College Scorecard API key | `DEMO_KEY` / Bundled seed | Optional |

> **Note on Zero-Key Execution**: If `GEMINI_API_KEY` or `COLLEGE_SCORECARD_API_KEY` are not set, College Portfolio runs seamlessly using the bundled 50+ flagship seed dataset (`data/colleges_seed.json`) and graceful degradation handlers.

---

## 📚 REST API Documentation

| Method | Endpoint | Description | Query / Body Parameters |
|---|---|---|---|
| `GET` | `/api/health` | System health, database, API, and ledger status | None |
| `GET` | `/api/colleges` | Search & discovery with faceted filters | `q`, `state`, `type`, `max_net_price`, `min_admit_rate`, `max_admit_rate`, `sort`, `limit`, `offset` |
| `GET` | `/api/colleges/:id` | Detailed canonical college profile | `calculate_fit=true` |
| `POST` | `/api/colleges/:id/refresh` | Trigger server-side AI enrichment | `{ "force": false }` |
| `GET` | `/api/portfolio` | Retrieve current guest portfolio | Reads `college_portfolio_id` cookie |
| `POST` | `/api/portfolio/colleges` | Save college to portfolio | `{ "college_id": "166683", "user_note": "Top choice" }` |
| `DELETE` | `/api/portfolio/colleges/:id`| Remove college from portfolio | None |
| `PUT` | `/api/portfolio/preferences` | Update student GPA, SAT, budget, and fit weights | `{ "preferences": {...}, "fit_weights": {...} }` |
| `DELETE` | `/api/portfolio` | Clear all saved colleges | None |
| `GET` | `/api/compare` | Multi-college comparison matrix (2–6 schools) | `ids=166683,243744,110635` |
| `GET` | `/api/knowledge/colleges/:id`| Retrieve audit history for a college | None |
| `GET` | `/api/knowledge/export` | Export master knowledge ledger | `format=md` or `format=jsonl` |

---

## ☁️ Production Cloud Deployment

### 1. Render Blueprint (One-Click)
1. Push this repository to GitHub.
2. Log in to [Render](https://render.com) and click **New + > Blueprint**.
3. Select your repository. Render will automatically detect `render.yaml`.
4. Add your `GEMINI_API_KEY` (optional) in the environment settings.
5. Click **Apply**.

### 2. Railway
```bash
npm i -g @railway/cli
railway login
railway init
railway up
```

### 3. Fly.io
```bash
fly launch
fly deploy
```

### 4. Docker Container
```bash
# Build production container image
docker build -t college-portfolio .

# Run container exposing port 8000
docker run -p 8000:8000 -e GEMINI_API_KEY="your-api-key" college-portfolio
```

---

## 🧪 Verification & Testing Suite

Run the full automated test suite using `pytest`:

```bash
# Run all test tiers
pytest tests/ -v

# Run individual test tiers
pytest tests/test_tier1_features.py -v     # Tier 1: Core Feature Verification
pytest tests/test_tier2_boundaries.py -v   # Tier 2: Boundary & Corner Cases
pytest tests/test_tier3_pairwise.py -v     # Tier 3: Cross-Feature Interactions
pytest tests/test_tier4_scenarios.py -v    # Tier 4: End-to-End User Journeys
pytest tests/test_tier5_adversarial.py -v  # Tier 5: Security & Injection Stress Tests
```

---

## 📄 License
MIT License. Built for students, families, and high school counselors.
# CollegeMaker
