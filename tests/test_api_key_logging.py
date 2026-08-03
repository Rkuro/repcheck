"""Regression tests for the API key disclosure in update_bill_summary.

`log.info(headers_dict)` wrote every request header at INFO -- including the
X-REPCHECK-API-KEY read three lines later for authentication -- into service.log,
which is retained for 7 days.
"""

import logging

import pytest

API_KEY = "super-secret-repcheck-key-do-not-log"


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setenv("REPCHECK_API_KEY", API_KEY)
    return API_KEY


def _log_text(caplog):
    return "\n".join(record.getMessage() for record in caplog.records)


def test_valid_api_key_is_never_logged(client, use_session, api_key, caplog):
    """Authenticated request: the key must not appear in any log record."""
    use_session(results=[[]])  # bill lookup finds nothing -> 404

    with caplog.at_level(logging.DEBUG):
        response = client.post(
            "/api/bills/summary",
            json={"bill_id": "unknown-bill", "summary": "..."},
            headers={"X-REPCHECK-API-KEY": api_key},
        )

    assert response.status_code == 404
    assert api_key not in _log_text(caplog)
    assert api_key not in caplog.text


def test_invalid_api_key_is_never_logged(client, use_session, api_key, caplog):
    """A rejected key is still a credential and must not be logged either."""
    use_session(results=[[]])
    guessed = "attacker-guessed-key"

    with caplog.at_level(logging.DEBUG):
        response = client.post(
            "/api/bills/summary",
            json={"bill_id": "some-bill", "summary": "..."},
            headers={"X-REPCHECK-API-KEY": guessed},
        )

    assert response.status_code == 403
    assert guessed not in _log_text(caplog)
    assert guessed not in caplog.text


def test_no_full_header_dump_in_logs(client, use_session, api_key, caplog):
    """The whole header dict must not be logged; a marker header proves it."""
    use_session(results=[[]])
    marker = "x-canary-header-value"

    with caplog.at_level(logging.DEBUG):
        client.post(
            "/api/bills/summary",
            json={"bill_id": "unknown-bill", "summary": "..."},
            headers={"X-REPCHECK-API-KEY": api_key, "X-Canary": marker},
        )

    assert marker not in _log_text(caplog)
    assert "x-repcheck-api-key" not in _log_text(caplog).lower()


def test_missing_api_key_is_rejected(client, use_session, api_key):
    use_session(results=[[]])

    response = client.post(
        "/api/bills/summary",
        json={"bill_id": "some-bill", "summary": "..."},
    )

    assert response.status_code == 401
