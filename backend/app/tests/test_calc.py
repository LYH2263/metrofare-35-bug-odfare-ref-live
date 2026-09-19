from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_hops, shortest_path
from app.engines.route_quote import quote_route

EDGES = [("A1", "A2"), ("A2", "A3"), ("A2", "B1"), ("B1", "B2")]
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]


def test_hops_a1_a3():
    assert shortest_hops(EDGES, "A1", "A3") == 2


def test_hops_a1_b2():
    assert shortest_hops(EDGES, "A1", "B2") == 3


def test_shortest_path():
    assert shortest_path(EDGES, "A1", "B2") == ["A1", "A2", "B1", "B2"]
    assert shortest_path(EDGES, "A1", "A1") == ["A1"]
    assert shortest_path(EDGES, "A1", "X9") is None


def test_fare_by_hops():
    assert fare_for_hops(2, RULES) == 3.0
    assert fare_for_hops(3, RULES) == 4.0
    assert fare_for_hops(10, RULES) == 6.0


def test_quote():
    q = quote_route(EDGES, "A1", "B2", RULES)
    assert q["hops"] == 3 and q["fare"] == 4.0
    assert q["fare_source"] == "steps" and q["reference_fare"] == 4.0
    assert q["path"] == ["A1", "A2", "B1", "B2"]


def test_quote_unreachable():
    q = quote_route(EDGES, "A1", "X9", RULES)
    assert q["reachable"] is False and q["fare"] is None and q["path"] is None


def test_quote_flat_hit():
    flats = [{"start": "A1", "end": "B2", "price": 2.5}]
    q = quote_route(EDGES, "A1", "B2", RULES, flats)
    assert q["fare"] == 2.5
    assert q["reference_fare"] == 4.0
    assert q["fare_source"] == "flat"
    assert q["hops"] == 3
    assert q["path"] == ["A1", "A2", "B1", "B2"]


def test_quote_flat_is_directed():
    # flat only registered A1->B2; reverse OD must fall back to step table
    flats = [{"start": "A1", "end": "B2", "price": 2.5}]
    q = quote_route(EDGES, "B2", "A1", RULES, flats)
    assert q["fare_source"] == "steps" and q["fare"] == 4.0
