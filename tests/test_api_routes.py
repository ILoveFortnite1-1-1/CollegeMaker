"""API Integration Tests for All REST Endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient
from server.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_api_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ["healthy", "degraded"]
        assert data["database"]["indexed_colleges"] >= 50


@pytest.mark.asyncio
async def test_api_colleges_list_and_search():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Base list
        resp = await client.get("/api/colleges?page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 50
        assert len(data["items"]) == 10

        # 2. Search query
        resp_search = await client.get("/api/colleges?q=Harvard")
        assert resp_search.status_code == 200
        search_data = resp_search.json()
        assert search_data["total"] >= 1
        assert any("Harvard" in item["name"] for item in search_data["items"])


@pytest.mark.asyncio
async def test_api_college_detail():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # MIT ID 166683
        resp = await client.get("/api/colleges/166683")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "166683"
        assert "Massachusetts Institute of Technology" in data["name"]
        assert "costs" in data
        assert "admissions" in data
        assert "outcomes" in data
        assert data["admissions"]["acceptance_rate"]["source_type"] == "government"


@pytest.mark.asyncio
async def test_api_college_refresh():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/colleges/166027/refresh")
        assert resp.status_code == 200
        data = resp.json()
        assert "college" in data
        assert "run" in data
        assert data["run"]["college_id"] == "166027"


@pytest.mark.asyncio
async def test_api_portfolio_lifecycle_with_cookie():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Get initial portfolio (should set cookie)
        resp = await client.get("/api/portfolio")
        assert resp.status_code == 200
        cookie = resp.cookies.get("college_portfolio_id")
        assert cookie is not None

        # 2. Add college to portfolio
        add_resp = await client.post(
            "/api/portfolio/colleges",
            json={"college_id": "166027", "notes": "Top priority"},
            cookies={"college_portfolio_id": cookie},
        )
        assert add_resp.status_code == 200
        add_data = add_resp.json()
        assert add_data["summary"]["total_colleges"] >= 1
        assert "saved_colleges" in add_data
        assert len(add_data["saved_colleges"]) >= 1
        assert add_data["saved_colleges"][0]["college_id"] == "166027"
        assert "college_name" in add_data["saved_colleges"][0]
        assert "net_price" in add_data["saved_colleges"][0]
        assert "admit_rate" in add_data["saved_colleges"][0]
        assert "median_earnings" in add_data["saved_colleges"][0]
        assert add_data["saved_colleges"][0]["user_note"] == "Top priority"
        assert add_data["summary"]["saved_count"] >= 1
        assert "mix_breakdown" in add_data["summary"]

        # 3. Update preferences
        pref_resp = await client.put(
            "/api/portfolio/preferences",
            json={
                "gpa": 3.9,
                "sat_score": 1520,
                "budget_max_annual": 35000,
                "preferred_majors": ["Engineering"],
            },
            cookies={"college_portfolio_id": cookie},
        )
        assert pref_resp.status_code == 200
        pref_data = pref_resp.json()
        assert pref_data["portfolio"]["preferences"]["sat_score"] == 1520

        # 4. Remove college
        del_resp = await client.delete(
            "/api/portfolio/colleges/166027",
            cookies={"college_portfolio_id": cookie},
        )
        assert del_resp.status_code == 200
        del_data = del_resp.json()
        assert del_data["summary"]["total_colleges"] == 0


@pytest.mark.asyncio
async def test_api_compare_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/compare?ids=166027,243744")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["colleges"]) == 2
        assert "metrics" in data
        assert "best_in_class" in data


@pytest.mark.asyncio
async def test_api_knowledge_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. College audit events
        resp_col = await client.get("/api/knowledge/colleges/166027")
        assert resp_col.status_code == 200
        assert "events" in resp_col.json()

        # 2. Knowledge export
        resp_exp = await client.get("/api/knowledge/export")
        assert resp_exp.status_code == 200
        assert "summary" in resp_exp.json()

        # 3. Raw markdown
        resp_raw = await client.get("/api/knowledge/raw?format=markdown")
        assert resp_raw.status_code == 200
        assert "content" in resp_raw.json()
