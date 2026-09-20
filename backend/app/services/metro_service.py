import sqlite3

from app.db import connect
from app.engines.route_quote import quote_route
from app.repositories import edges as edges_repo
from app.repositories import fare_rules as rules_repo
from app.repositories import flat_fares as flat_repo
from app.repositories import runs as runs_repo
from app.repositories import settings as settings_repo
from app.repositories import stations as stations_repo


class DuplicateFlatFareError(Exception):
    pass


class ValidationError(Exception):
    pass


class MetroService:
    def __init__(self):
        self._conn = connect()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def stations(self):
        return stations_repo.list_all(self._conn)

    def station(self, code: str):
        return stations_repo.get_by_code(self._conn, code)

    def edges(self):
        return [{"a": a, "b": b} for a, b in edges_repo.list_pairs(self._conn)]

    def fare_rules(self):
        return rules_repo.list_ordered(self._conn)

    def flat_fares(self):
        return flat_repo.list_all(self._conn)

    def create_flat_fare(self, start: str, end: str, price: float) -> dict:
        if start == end:
            raise ValidationError("起终点不能相同")
        if not stations_repo.get_by_code(self._conn, start):
            raise ValidationError(f"起点不存在: {start}")
        if not stations_repo.get_by_code(self._conn, end):
            raise ValidationError(f"终点不存在: {end}")
        if price < 0:
            raise ValidationError("一口价不能为负")
        if flat_repo.get_pair(self._conn, start, end):
            raise DuplicateFlatFareError(f"{start}->{end} 已登记一口价")
        try:
            flat_id = flat_repo.insert(self._conn, start, end, price)
        except sqlite3.IntegrityError:
            raise DuplicateFlatFareError(f"{start}->{end} 已登记一口价")
        row = flat_repo.get_pair(self._conn, start, end)
        row["id"] = flat_id
        return row

    def delete_flat_fare(self, start: str, end: str) -> bool:
        # Only the flat-fare registration is removed. Written calc_runs are
        # point-in-time snapshots: their fare and reference total must stay as
        # they were when the quote was persisted.
        return flat_repo.delete_pair(self._conn, start, end)

    def settings(self):
        return settings_repo.get_map(self._conn)

    def quote(self, start: str, end: str, persist: bool):
        edges = edges_repo.list_pairs(self._conn)
        rules = rules_repo.as_calc_rules(self._conn)
        flat = flat_repo.list_all(self._conn)
        result = quote_route(edges, start, end, rules, flat)
        run_id = None
        if persist and result.get("reachable"):
            run_id = runs_repo.insert(self._conn, "quote", {"start": start, "end": end}, result)
        return {"run_id": run_id, **result}

    def history(self, limit=50):
        return runs_repo.list_recent(self._conn, limit)

    def history_item(self, run_id: int):
        # Return the persisted snapshot verbatim; neither the fare nor the
        # reference total is recomputed against the current tables.
        row = None
        for it in runs_repo.list_recent(self._conn, 200):
            if int(it["id"]) == int(run_id):
                row = dict(it)
                break
        return row

    def dashboard(self):
        st = stations_repo.list_all(self._conn)
        clean = [s for s in st if "种子" not in s["name"]]
        dirty = [s for s in st if "种子" in s["name"]]
        return {
            "station_count": len(st),
            "edge_count": len(edges_repo.list_pairs(self._conn)),
            "clean_stations": len(clean),
            "dirty_stations": len(dirty),
        }
