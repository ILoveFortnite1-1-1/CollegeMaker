## 2026-09-02T19:18:24Z
You are the Design Doc & Requirements Spec Miner.
Read the authoritative reference design document at:
/Users/chrisblakeley/Documents/School Organizer/college_portfolio_design_doc_updated.docx
(You can extract/inspect word/document.xml using python's zipfile module or docx tools)
And read ORIGINAL_REQUEST.md at:
/Users/chrisblakeley/.gemini/antigravity/brain/0e2c5b44-6540-4fc9-845f-a02283fa349e/ORIGINAL_REQUEST.md

Your working directory is:
/Users/chrisblakeley/Documents/School Organizer/college-portfolio/.agents/spec_miner_survey

Your mission:
1. Extract and document all specifications, requirements (R1 through R5), acceptance criteria, edge cases, data fields, schemas, and UI requirements.
2. Specifically enumerate:
   - College Scorecard API fields, search filters, pagination, normalization
   - Gemini AI enrichment: prompt schemas, structured JSON output, validation, fallback handling
   - Field-level provenance metadata: source tracking (Scorecard, Gemini, User, Fallback), confidence scores, timestamps
   - Source precedence hierarchy rules
   - Guest portfolio session/cookie persistence: cookie schema, server-side store, sync, fallbacks
   - College comparison workspace requirements: side-by-side metrics, visual diffs, fit score breakdown
   - Append-only Knowledge Ledger format: markdown summary (/knowledge/college-knowledge.md) and JSONL (/knowledge/college-knowledge.jsonl)
   - UI Screens: Dashboard (/), Search (/colleges), Profile (/colleges/:id), Comparison (/compare), Settings (/settings)
   - Free-tier hosting requirements (Docker, Render/Railway configuration, README guide)
3. Write your comprehensive specification report to:
/Users/chrisblakeley/Documents/School Organizer/college-portfolio/.agents/spec_miner_survey/handoff.md

When complete, send a message to orchestrator with your findings.
