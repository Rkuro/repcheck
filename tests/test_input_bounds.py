"""Bounds checks on unauthenticated query parameters.

Covers the unbounded precinct radius (a chained-comparison bug that disabled the
upper bound entirely) and the missing page_size ceiling.
"""

import pytest

from conftest import fake_area

BASE_PARAMS = {"date_type": "creation_date"}
NO_DATA = [[], [], [0], [], []]


# --- radius_miles: `if 100 > radius_miles < 1` never rejected large values ---

@pytest.mark.parametrize("radius", [0.5, 0.0, -1, 101, 500, 100000, 1e9])
def test_radius_outside_1_to_100_is_rejected(client, use_session, radius):
    use_session(results=[[fake_area()]])

    response = client.get("/api/precincts/12345", params={"radius_miles": radius})

    assert response.status_code == 400, (
        f"radius_miles={radius} was accepted; a full-table precinct scan is reachable"
    )
    assert "between 1 and 100" in response.json()["detail"]


@pytest.mark.parametrize("radius", [1, 5, 50, 100])
def test_radius_within_1_to_100_is_accepted(client, use_session, radius):
    use_session(results=[[fake_area()]], query_rows=[])

    response = client.get("/api/precincts/12345", params={"radius_miles": radius})

    assert response.status_code == 200
    assert response.json()["radius_miles"] == radius


def test_default_radius_is_accepted(client, use_session):
    use_session(results=[[fake_area()]], query_rows=[])

    response = client.get("/api/precincts/12345")

    assert response.status_code == 200
    assert response.json()["radius_miles"] == 5.0


# --- page_size: previously unbounded, each bill drags several JSONB blobs ---

@pytest.mark.parametrize("page_size", [101, 500, 10000, 1000000])
def test_page_size_above_ceiling_is_rejected(client, use_session, page_size):
    use_session(results=NO_DATA)

    response = client.get(
        "/api/zipcodes/12345/bills",
        params={**BASE_PARAMS, "page_size": page_size},
    )

    assert response.status_code == 422, (
        f"page_size={page_size} was accepted; the response is unbounded in size"
    )


@pytest.mark.parametrize("page_size", [0, -1])
def test_non_positive_page_size_is_rejected(client, use_session, page_size):
    use_session(results=NO_DATA)

    response = client.get(
        "/api/zipcodes/12345/bills",
        params={**BASE_PARAMS, "page_size": page_size},
    )

    assert response.status_code == 422


@pytest.mark.parametrize("page_size", [1, 20, 100])
def test_page_size_within_ceiling_is_accepted(client, use_session, page_size):
    use_session(results=NO_DATA)

    response = client.get(
        "/api/zipcodes/12345/bills",
        params={**BASE_PARAMS, "page_size": page_size},
    )

    assert response.status_code == 200
    assert response.json()["page_size"] == page_size


def test_non_positive_page_is_rejected(client, use_session):
    use_session(results=NO_DATA)

    response = client.get(
        "/api/zipcodes/12345/bills",
        params={**BASE_PARAMS, "page": 0},
    )

    assert response.status_code == 422
