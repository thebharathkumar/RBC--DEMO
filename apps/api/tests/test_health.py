"""Smoke tests for the FastAPI surface that ships at milestone 1."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src import __version__
from src.main import create_app
from src.observability.logging import REQUEST_ID_HEADER


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200


def test_version_reports_package_version(client: TestClient) -> None:
    response = client.get("/version")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == __version__
    assert body["env"] == "test"


def test_metrics_exposes_prometheus_format(client: TestClient) -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


def test_request_id_is_echoed_when_supplied(client: TestClient) -> None:
    rid = "test-request-id-1234"
    response = client.get("/healthz", headers={REQUEST_ID_HEADER: rid})
    assert response.headers[REQUEST_ID_HEADER] == rid


def test_request_id_is_minted_when_absent(client: TestClient) -> None:
    response = client.get("/healthz")
    assert REQUEST_ID_HEADER in response.headers
    assert len(response.headers[REQUEST_ID_HEADER]) >= 16


def test_unknown_route_returns_structured_error(client: TestClient) -> None:
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["type"] == "http_error"
