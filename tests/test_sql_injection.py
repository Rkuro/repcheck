"""Regression tests for the SQL injection in get_bills_for_representatives.

`representative_ids` is an unauthenticated query parameter that was f-string
interpolated into a sqlalchemy.text() fragment. json.dumps escapes double quotes but
not single quotes, and a single quote is what terminates a Postgres string literal.
These tests assert the value now travels as a *bound parameter* and never reaches the
SQL text.
"""

from conftest import find_statement

# Closes the JSON string, closes the SQL literal, then comments out the rest.
INJECTION = "x' OR 1=1 --"
# A payload whose intent is unmistakable if it ever lands in SQL text.
DESTRUCTIVE = "x'); DROP TABLE bills; --"

# The endpoint 400s unless date_type is one of these, so every request needs it.
BASE_PARAMS = {"date_type": "creation_date"}

# Canned rows for the five queries the handler runs:
# person_ids, jurisdiction_area_ids, count (must be a scalar), bills, votes.
NO_DATA = [[], [], [0], [], []]


def test_single_quote_payload_is_bound_not_interpolated(client, use_session):
    session = use_session(results=NO_DATA)

    response = client.get(
        "/api/zipcodes/12345/bills",
        params={**BASE_PARAMS, "representative_ids": INJECTION},
    )
    assert response.status_code == 200

    sql, params = find_statement(session, "vote_element")

    # The payload must not appear anywhere in the SQL text.
    assert INJECTION not in sql
    assert "OR 1=1" not in sql
    assert "--" not in sql

    # It must appear as a bound parameter value instead.
    assert '{"voter_id": "x\' OR 1=1 --"}' in params.values()


def test_payload_cannot_reach_sql_text(client, use_session):
    session = use_session(results=NO_DATA)

    response = client.get(
        "/api/zipcodes/12345/bills",
        params={**BASE_PARAMS, "representative_ids": DESTRUCTIVE},
    )
    assert response.status_code == 200

    sql, params = find_statement(session, "vote_element")

    assert "DROP TABLE" not in sql
    assert DESTRUCTIVE not in sql
    assert '{"voter_id": "x\'); DROP TABLE bills; --"}' in params.values()


def test_containment_operand_is_a_placeholder(client, use_session):
    """The @> operand must be a placeholder, and still typed as jsonb."""
    session = use_session(results=NO_DATA)

    client.get(
        "/api/zipcodes/12345/bills",
        params={**BASE_PARAMS, "representative_ids": "ocd-person/abc123"},
    )

    sql, params = find_statement(session, "vote_element")

    # psycopg2 paramstyle renders binds as %(name)s.
    assert "vote_element @> CAST(%(rep_condition_0)s AS jsonb)" in sql
    # No single-quoted literal operand anywhere.
    assert "@> '" not in sql
    assert params["rep_condition_0"] == '{"voter_id": "ocd-person/abc123"}'


def test_multiple_rep_ids_each_get_a_distinct_bind(client, use_session):
    """Several ids still OR together -- the fix must not collapse or drop any."""
    session = use_session(results=NO_DATA)

    client.get(
        "/api/zipcodes/12345/bills",
        params={**BASE_PARAMS, "representative_ids": ["rep-one", "rep-two", INJECTION]},
    )

    sql, params = find_statement(session, "vote_element")

    assert sql.count("vote_element @> CAST(") == 3
    assert INJECTION not in sql

    bound = [params[f"rep_condition_{i}"] for i in range(3)]
    assert bound == [
        '{"voter_id": "rep-one"}',
        '{"voter_id": "rep-two"}',
        '{"voter_id": "x\' OR 1=1 --"}',
    ]


def test_no_rep_ids_means_no_containment_filter(client, use_session):
    """Sanity check that the filter is genuinely conditional."""
    session = use_session(results=NO_DATA)

    response = client.get("/api/zipcodes/12345/bills", params=BASE_PARAMS)
    assert response.status_code == 200

    for statement in session.statements:
        if hasattr(statement, "compile"):
            assert "vote_element" not in str(statement.compile())
