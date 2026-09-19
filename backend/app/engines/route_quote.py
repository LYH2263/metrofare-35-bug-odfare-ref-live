from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_path


def quote_route(
    edges: list[tuple[str, str]],
    start: str,
    end: str,
    rules: list[dict],
    flat_fares: list[dict] | None = None,
) -> dict:
    """Quote the fare for a directed OD pair.

    flat_fares: rows for the specific start->end pair; each row carries a
    ``price``. When at least one matches, the flat price is charged while the
    step-table price is still reported as ``reference_fare``.
    """
    path = shortest_path(edges, start, end)
    if path is None:
        return {
            "start": start,
            "end": end,
            "hops": None,
            "path": None,
            "fare": None,
            "reference_fare": None,
            "fare_source": None,
            "reachable": False,
        }
    hops = len(path) - 1
    reference_fare = fare_for_hops(hops, rules)
    match = next((f for f in (flat_fares or []) if f["start"] == start and f["end"] == end), None)
    if match is not None:
        flat = round(float(match["price"]), 2)
        return {
            "start": start,
            "end": end,
            "hops": hops,
            "path": path,
            "fare": flat,
            "reference_fare": reference_fare,
            "fare_source": "flat",
            "reachable": True,
        }
    return {
        "start": start,
        "end": end,
        "hops": hops,
        "path": path,
        "fare": reference_fare,
        "reference_fare": reference_fare,
        "fare_source": "steps",
        "reachable": True,
    }
