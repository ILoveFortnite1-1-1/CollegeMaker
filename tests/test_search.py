import pytest
from httpx import ASGITransport, AsyncClient
from server.main import app

@pytest.mark.asyncio
async def test_search_nicknames_and_acronyms():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # FSU
        res = await client.get("/api/colleges?query=FSU")
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) >= 1
        assert "Florida State" in items[0]["name"]

        # UCF
        res = await client.get("/api/colleges?query=UCF")
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) >= 1
        assert "Central Florida" in items[0]["name"]

        # Bama
        res = await client.get("/api/colleges?query=Bama")
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) >= 1
        assert "Alabama" in items[0]["name"]

        # Notre Dame
        res = await client.get("/api/colleges?query=Notre Dame")
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) >= 1
        assert "Notre Dame" in items[0]["name"]

        # Penn State
        res = await client.get("/api/colleges?query=Penn State")
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) >= 1
        assert "Pennsylvania State" in items[0]["name"]

@pytest.mark.asyncio
async def test_search_state_expansion():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Searching "Florida" should return all Florida colleges (e.g. 20)
        res = await client.get("/api/colleges?query=Florida")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 20
        # University of Florida should rank first
        assert "University of Florida" == data["items"][0]["name"]

        # Searching "FL" state code
        res_code = await client.get("/api/colleges?query=FL")
        assert res_code.status_code == 200
        assert res_code.json()["total"] >= 20

@pytest.mark.asyncio
async def test_search_filters_and_sorting():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Sort by net price ascending
        res = await client.get("/api/colleges?sort=net_price_asc&limit=5")
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 5

        # Sort by admit rate ascending
        res_admit = await client.get("/api/colleges?sort=admit_rate_asc&limit=5")
        assert res_admit.status_code == 200
        admit_items = res_admit.json()["items"]
        assert len(admit_items) == 5
        # Caltech, Harvard, etc. are most selective
        assert admit_items[0]["summary"]["acceptance_rate"]["value"] < 0.10
