from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from app.server import app


def test_logs_request_id_from_header(caplog) -> None:
    client = TestClient(app)

    with caplog.at_level(logging.INFO, logger="app.server"):
        response = client.get(
            "/health",
            headers={"X-Request-Id": "test-request-id-123"},
        )

    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == "test-request-id-123"
    assert "test-request-id-123" in caplog.text
    assert "path=/health" in caplog.text


def test_logs_request_id_when_handler_raises(caplog) -> None:
    async def failing_endpoint():
        raise RuntimeError("boom")

    app.add_api_route("/test/correlation-error", failing_endpoint, methods=["GET"])
    client = TestClient(app, raise_server_exceptions=True)

    with caplog.at_level(logging.ERROR, logger="app.server"):
        with pytest.raises(RuntimeError, match="boom"):
            client.get(
                "/test/correlation-error",
                headers={"X-Request-Id": "test-request-id-456"},
            )

    assert "test-request-id-456" in caplog.text
    assert "path=/test/correlation-error" in caplog.text
    assert "status_code=error" in caplog.text
