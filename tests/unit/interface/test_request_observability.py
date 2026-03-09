from __future__ import annotations

from fastapi.testclient import TestClient

from src.interface.http.app import create_app


def test_healthz_has_x_request_id_header() -> None:
    client = TestClient(create_app())
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.headers.get("x-request-id")


def test_forward_incoming_x_request_id_header() -> None:
    client = TestClient(create_app())
    response = client.get("/healthz", headers={"x-request-id": "test-rid-1"})

    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "test-rid-1"
