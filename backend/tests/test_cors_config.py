from fastapi.testclient import TestClient
from app.main import app, _origins


def test_cors_origins_include_production_frontend():
    assert "https://docuverify-frontend.vercel.app" in _origins
    assert "http://localhost:5173" in _origins
    assert "http://127.0.0.1:5173" in _origins


def test_cors_preflight_allows_production_frontend():
    client = TestClient(app)
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://docuverify-frontend.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://docuverify-frontend.vercel.app"


def test_cors_rejects_untrusted_origin():
    client = TestClient(app)
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://unauthorized-domain.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") is None

