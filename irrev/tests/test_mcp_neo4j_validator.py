import pytest

from irrev.mcp.neo4j_readonly_server import _require_intent, _validate_read_cypher


def test_require_intent_accepts_known_values():
    assert _require_intent({"intent": "analysis"}) == "analysis"
    assert _require_intent({"intent": "Inspection"}) == "inspection"


def test_require_intent_rejects_missing():
    with pytest.raises(ValueError):
        _require_intent({})


def test_validate_read_cypher_accepts_bounded_match_return():
    _validate_read_cypher("MATCH (n:Note) RETURN n.note_id LIMIT 10")


def test_validate_read_cypher_requires_limit():
    with pytest.raises(ValueError):
        _validate_read_cypher("MATCH (n:Note) RETURN n.note_id")


def test_validate_read_cypher_rejects_writes():
    with pytest.raises(ValueError):
        _validate_read_cypher("MATCH (n) CREATE (m) RETURN 1 LIMIT 1")


def test_validate_read_cypher_does_not_false_positive_on_set_in_string_literal():
    _validate_read_cypher("MATCH (n:Note {note_id: 'concepts/feasible-set'}) RETURN n.note_id LIMIT 1")


def test_validate_read_cypher_rejects_unbounded_star():
    with pytest.raises(ValueError):
        _validate_read_cypher("MATCH p=(a)-[:LINKS_TO*]->(b) RETURN p LIMIT 1")


def test_validate_read_cypher_rejects_excessive_hops():
    with pytest.raises(ValueError):
        _validate_read_cypher("MATCH p=(a)-[:LINKS_TO*1..12]->(b) RETURN p LIMIT 1")
