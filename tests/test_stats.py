import pytest
from httpx import ASGITransport, AsyncClient
from server.main import app

@pytest.mark.asyncio
async def test_visitor_counter_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get current count
        res1 = await client.get("/api/stats/visits")
        assert res1.status_code == 200
        count1 = res1.json()["total_visits"]

        # Record visit (increment)
        res2 = await client.post("/api/stats/visit")
        assert res2.status_code == 200
        count2 = res2.json()["total_visits"]
        assert count2 == count1 + 1

        # Record another visit
        res3 = await client.get("/api/stats/visit")
        assert res3.status_code == 200
        count3 = res3.json()["total_visits"]
        assert count3 == count2 + 1
