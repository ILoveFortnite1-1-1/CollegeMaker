import asyncio
import httpx
import json
import sys
import os
from pathlib import Path

# Add project root to python path
sys.path.insert(0, os.getcwd())

from server.main import app

async def run_live_audit():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("=== 1. Health Check ===")
        r = await client.get("/api/health")
        print("Status:", r.status_code)
        health = r.json()
        print("Health JSON status:", health.get("status"))
        assert r.status_code == 200
        assert health["status"] == "healthy"

        print("\n=== 2. College Search & Discovery ===")
        r = await client.get("/api/colleges?q=MIT")
        print("Status:", r.status_code)
        search_res = r.json()
        colleges = search_res.get("colleges", [])
        total_found = search_res.get("total")
        print("Total found:", total_found, "Returned:", len(colleges))
        assert len(colleges) > 0
        mit = colleges[0]
        print("First match:", mit.get("name"), "(ID:", mit.get("id"), ")")
        assert "Massachusetts Institute of Technology" in mit.get("name")

        print("\n=== 3. Canonical College Profile & Field Provenance ===")
        r = await client.get(f"/api/colleges/{mit.get('id')}")
        print("Status:", r.status_code)
        detail = r.json()
        print("Name:", detail.get("name"))
        print("Location:", detail.get("location"))
        print("Admissions Admit Rate:", detail.get("admissions", {}).get("acceptance_rate"))
        print("Costs Net Price Avg:", detail.get("costs", {}).get("net_price_average"))
        print("Outcomes 10yr Earnings:", detail.get("outcomes", {}).get("median_earnings_10yr"))
        print("Field Provenance Count:", len(detail.get("provenance", {})))
        print("Sample Provenance for admissions.acceptance_rate:", detail.get("provenance", {}).get("admissions.acceptance_rate"))
        assert "provenance" in detail
        assert len(detail["provenance"]) >= 5

        print("\n=== 4. Cookie-Based Guest Portfolio & Persistence ===")
        # Request portfolio (gets cookie)
        r = await client.get("/api/portfolio")
        print("GET /api/portfolio Status:", r.status_code)
        session_id = r.json().get("session_id")
        print("Assigned session_id:", session_id)
        assert session_id is not None

        # Add college to portfolio
        r = await client.post("/api/portfolio/colleges", json={"college_id": mit.get("id"), "tag": "Reach", "notes": "Top dream school"})
        print("POST /api/portfolio/colleges Status:", r.status_code)
        p_res = r.json()
        p_data = p_res.get("colleges", [])
        print("Saved items count:", len(p_data))
        print("Item tag:", p_data[0].get("tag") if p_data else None)
        print("Summary stats:", p_res.get("summary"))
        assert len(p_data) == 1
        assert p_data[0].get("tag") == "Reach"

        # Verify persistence on subsequent GET
        r = await client.get("/api/portfolio")
        print("GET /api/portfolio Persistence Status:", r.status_code)
        persisted = r.json().get("colleges", [])
        assert len(persisted) == 1
        assert persisted[0]["id"] == mit.get("id")

        print("\n=== 5. Multi-College Comparison Matrix (2-6 Colleges) ===")
        stanford_id = "243744"
        harvard_id = "166027"
        r = await client.get(f"/api/compare?ids={mit.get('id')},{stanford_id},{harvard_id}")
        print("GET /api/compare Status:", r.status_code)
        comp = r.json()
        print("Compared count:", len(comp.get("colleges", [])))
        print("Metrics categories:", list(comp.get("metrics", {}).keys()))
        print("Best in Class awards:", comp.get("best_in_class"))
        print("Comparative Summary:", comp.get("summary"))
        assert len(comp.get("colleges", [])) == 3
        assert "best_in_class" in comp
        assert "summary" in comp

        print("\n=== 6. Server-Side AI Enrichment & Knowledge Ledger Integration ===")
        r = await client.post(f"/api/colleges/{mit.get('id')}/refresh")
        print("POST refresh Status:", r.status_code)
        ref_res = r.json()
        print("Enrichment Run ID:", ref_res.get("run_id"))
        print("Enrichment Status:", ref_res.get("run", {}).get("status"))
        print("Events recorded:", ref_res.get("events_recorded"))
        assert r.status_code == 200

        print("\n=== 7. Verify Knowledge Ledger Endpoints & Files on Disk ===")
        r = await client.get("/api/knowledge/export")
        print("GET /api/knowledge/export Status:", r.status_code)
        export_data = r.json()
        print("Total colleges in audit summary:", export_data.get("total_colleges_audited"))
        print("Recent events count:", len(export_data.get("recent_events", [])))
        assert r.status_code == 200

        r_mit_events = await client.get(f"/api/knowledge/colleges/{mit.get('id')}")
        print(f"GET /api/knowledge/colleges/{mit.get('id')} Status:", r_mit_events.status_code)
        assert r_mit_events.status_code == 200

        r_raw_md = await client.get("/api/knowledge/raw?format=markdown")
        print("GET /api/knowledge/raw?format=markdown Status:", r_raw_md.status_code)
        assert r_raw_md.status_code == 200
        assert len(r_raw_md.json().get("content", "")) > 100

        r_raw_jsonl = await client.get("/api/knowledge/raw?format=jsonl")
        print("GET /api/knowledge/raw?format=jsonl Status:", r_raw_jsonl.status_code)
        assert r_raw_jsonl.status_code == 200
        assert len(r_raw_jsonl.json().get("content", "")) > 100

        md_file = Path("knowledge/college-knowledge.md")
        jsonl_file = Path("knowledge/college-knowledge.jsonl")
        print("MD file on disk exists:", md_file.exists(), "Size (bytes):", md_file.stat().st_size)
        print("JSONL file on disk exists:", jsonl_file.exists(), "Size (bytes):", jsonl_file.stat().st_size)
        assert md_file.exists()
        assert jsonl_file.exists()

        print("\n=== 8. Frontend SPA Root & Static Asset Serving ===")
        r = await client.get("/")
        print("GET / Status:", r.status_code, "Content-Type:", r.headers.get("content-type"))
        assert r.status_code == 200
        assert "College Portfolio" in r.text

        r_css = await client.get("/css/styles.css")
        print("GET /css/styles.css Status:", r_css.status_code)
        assert r_css.status_code == 200

        r_js = await client.get("/js/app.js")
        print("GET /js/app.js Status:", r_js.status_code)
        assert r_js.status_code == 200

        r_spa = await client.get("/compare")
        print("GET /compare (SPA fallback) Status:", r_spa.status_code)
        assert r_spa.status_code == 200
        assert "College Portfolio" in r_spa.text

        print("\n>>> ALL EMPIRICAL INTEGRITY & RUNTIME CHECKS PASSED WITH 100% SUCCESS <<<")

if __name__ == "__main__":
    asyncio.run(run_live_audit())
