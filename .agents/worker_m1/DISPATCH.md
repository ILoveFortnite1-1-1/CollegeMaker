## 2026-09-02T19:21:42Z

You are the Backend & Ingestion Worker (teamwork_preview_worker).
Read the master specifications at:
- /Users/chrisblakeley/.gemini/antigravity/brain/0e2c5b44-6540-4fc9-845f-a02283fa349e/ORIGINAL_REQUEST.md
- /Users/chrisblakeley/.gemini/antigravity/brain/0e2c5b44-6540-4fc9-845f-a02283fa349e/PROJECT.md

Your working directory is:
/Users/chrisblakeley/Documents/School Organizer/college-portfolio/.agents/worker_m1

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your mission for Milestone 1 (M1: Backend Core, Ingestion & SQLite Store):
1. Setup Python project dependencies in  (fastapi, uvicorn, pydantic, httpx, pytest, etc.).
2. Build canonical data models in :
   - , , , , , , .
   - Complete provenance metadata wrapper (, , , , , , , ).
3. Build the bundled offline seed dataset in  with 50+ real flagship US universities with accurate metrics (MIT, Stanford, Harvard, UC Berkeley, UCLA, Michigan, Ohio State, Georgia Tech, Florida, UT Austin, NYU, Washington, Illinois, Purdue, etc.).
4. Build :
   - Async College Scorecard API query integration (supports searching by name, state, type, cost, admit rate, sorting).
   - SQLite cache with 7-day TTL ().
   - Seamless fallback to  when API key is missing or network is offline.
5. Build FastAPI application and core routes:
   - : FastAPI app configuration, CORS, exception handlers.
   - :  returning system status, API config state, database state.
   - :  (search, filter, sort, pagination) and  (detail profile with full provenance).
6. Verify your implementation by running unit tests and verifying response formats.
7. Write your handoff report to  and notify orchestrator.
