import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.presentation.api.middleware.rate_limit import RateLimitMiddleware


def test_rate_limiter_allows_and_blocks() -> None:
    # Create a separate, isolated FastAPI test application
    test_app = FastAPI()
    # Configure it to only allow 2 requests per minute
    test_app.add_middleware(RateLimitMiddleware, rate_limit=2, period=60)

    @test_app.get("/api/v1/test-route")
    def test_route() -> dict:
        return {"status": "ok"}

    @test_app.get("/non-api-route")
    def non_api_route() -> dict:
        return {"status": "ok"}

    client = TestClient(test_app)

    # 1. Non-API route should bypass rate limiting
    for _ in range(5):
        resp = client.get("/non-api-route")
        assert resp.status_code == 200
        assert "X-RateLimit-Limit" not in resp.headers

    # 2. First API request: Allowed
    response = client.get("/api/v1/test-route")
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "2"
    assert response.headers["X-RateLimit-Remaining"] == "1"

    # 3. Second API request: Allowed
    response = client.get("/api/v1/test-route")
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "2"
    assert response.headers["X-RateLimit-Remaining"] == "0"

    # 4. Third API request: Blocked (429)
    response = client.get("/api/v1/test-route")
    assert response.status_code == 429
    assert response.json()["detail"] == "Too many requests. Please try again later."
    assert response.headers["X-RateLimit-Limit"] == "2"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert "Retry-After" in response.headers
