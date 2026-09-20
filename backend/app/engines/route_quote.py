from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_path


def build_segments(path: list[str], rules: list[dict]) -> list[dict]:
    """Expand the stepped fare along ``path`` one hop at a time.

    Each row prices the marginal step between two consecutive stations: the
    difference between the step-table price at the new cumulative hop count
    and at the previous one. Summing every row therefore telescopes back to
    ``fare_for_hops(total_hops, rules)`` — the price looked up by total stations.
    """
    rows = []
    prev_total = 0.0
    for i in range(1, len(path)):
        total = fare_for_hops(i, rules)
        rows.append(
            {
                "seq": i,
                "from": path[i - 1],
                "to": path[i],
                "cum_hops": i,
                "price": round(total - prev_total, 2),
            }
        )
        prev_total = total
    return rows


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
    step-table price is still reported as ``reference_fare`` together with the
    per-hop ``segments`` expansion and their ``segment_total``.
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
            "segment_total": None,
            "segments": [],
            "fare_source": None,
            "reachable": False,
        }
    hops = len(path) - 1
    reference_fare = fare_for_hops(hops, rules)
    segments = build_segments(path, rules)
    match = next((f for f in (flat_fares or []) if f["start"] == start and f["end"] == end), None)

    def _payload(fare: float, source: str) -> dict:
        return {
            "start": start,
            "end": end,
            "hops": hops,
            "path": path,
            "fare": fare,
            "reference_fare": reference_fare,
            "segment_total": reference_fare,
            "segments": segments,
            "fare_source": source,
            "reachable": True,
        }

    if match is not None:
        return _payload(round(float(match["price"]), 2), "flat")
    return _payload(reference_fare, "steps")
