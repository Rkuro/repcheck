"""Deliberate 4xx responses must survive the handlers' generic exception blocks.

Previously `except Exception` caught the handler's own HTTPException and relabelled
it 500, and areas.py's bare `except:` returned HTTP 200 with an error body for a
nonexistent ZIP. Separately, get_bill dereferenced `bill.id` before its (commented
out) null check, so an unknown bill_id was an AttributeError surfaced as a 500.
"""

import pytest

BASE_PARAMS = {"date_type": "creation_date"}
NO_DATA = [[], [], [0], [], []]


# --- get_bill: null check must precede the dereference ---

def test_unknown_bill_id_is_404_not_500(client, use_session):
    use_session(results=[[]])  # bill lookup returns nothing

    response = client.get("/api/bills", params={"bill_id": "does-not-exist"})

    assert response.status_code == 404, (
        "an unknown bill_id must be a 404, not an AttributeError surfaced as 500"
    )
    assert response.json()["detail"] == "Bill not found"


# --- areas: .one() made the 404 guard unreachable, bare except returned 200 ---

def test_unknown_zipcode_is_404_not_200(client, use_session):
    use_session(results=[[]])  # area lookup returns nothing

    response = client.get("/api/zipcodes/00000")

    assert response.status_code == 404, (
        "a nonexistent ZIP must be a real 404, not HTTP 200 with an error body"
    )
    assert response.json()["detail"] == "ZIP code not found"


def test_unknown_area_is_404_not_200(client, use_session):
    use_session(results=[[]])

    response = client.get("/api/areas/ocd-division/country:us/state:zz")

    assert response.status_code == 404
    assert response.json()["detail"] == "Area not found"


def test_unknown_zipcode_for_precincts_is_404(client, use_session):
    use_session(results=[[]])

    response = client.get("/api/precincts/00000", params={"radius_miles": 5})

    assert response.status_code == 404
    assert response.json()["detail"] == "ZIP code not found"


# --- bills: handler-raised 4xx must not be relabelled 500 ---

def test_invalid_date_type_is_400_not_500(client, use_session):
    use_session(results=NO_DATA)

    response = client.get(
        "/api/zipcodes/12345/bills",
        params={"date_type": "not_a_real_column"},
    )

    assert response.status_code == 400, (
        "a deliberate 400 must not be swallowed by the generic exception handler"
    )
    assert "date_type" in response.json()["detail"]


def test_page_past_last_page_is_404_not_500(client, use_session):
    # A nonzero count with a page beyond the last one triggers the handler's own 404.
    use_session(results=[[], [], [5], [], []])

    response = client.get(
        "/api/zipcodes/12345/bills",
        params={**BASE_PARAMS, "page": 99, "page_size": 10},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Page not found."


def test_unknown_bill_summary_update_is_404(client, use_session, monkeypatch):
    monkeypatch.setenv("REPCHECK_API_KEY", "k")
    use_session(results=[[]])

    response = client.post(
        "/api/bills/summary",
        json={"bill_id": "nope", "summary": "..."},
        headers={"X-REPCHECK-API-KEY": "k"},
    )

    assert response.status_code == 404


@pytest.mark.parametrize("status_code", [401, 403])
def test_auth_failures_keep_their_status(client, use_session, monkeypatch, status_code):
    monkeypatch.setenv("REPCHECK_API_KEY", "correct-key")
    use_session(results=[[]])

    headers = {} if status_code == 401 else {"X-REPCHECK-API-KEY": "wrong-key"}
    response = client.post(
        "/api/bills/summary",
        json={"bill_id": "b", "summary": "..."},
        headers=headers,
    )

    assert response.status_code == status_code


# --- people: generic handler must not mask deliberate 4xx either ---

def test_people_lookup_with_no_results_is_200_empty(client, use_session):
    """No representatives for a ZIP is an empty list, not an error."""
    use_session(results=[[], [], []])

    response = client.get("/api/people/12345")

    assert response.status_code == 200
    assert response.json() == []
