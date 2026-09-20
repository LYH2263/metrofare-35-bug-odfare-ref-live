import json

import pytest

from app.services.metro_service import DuplicateFlatFareError


def _result(row) -> dict:
    return json.loads(row["result_json"])


def test_readonly_twice_write_nothing(service, count_runs):
    # 当场只读两次，库里条数须保持原样
    before = count_runs()
    a = service.quote("A1", "B2", persist=False)
    b = service.quote("A1", "B2", persist=False)
    assert a["run_id"] is None and b["run_id"] is None
    assert count_runs() == before


def test_flat_hit_then_open_by_id_then_delete(service):
    # register a flat fare cheaper than the 3-hop step price (4.0)
    created = service.create_flat_fare("A1", "B2", 2.5)

    # dry-run quote: payable equals the flat price, path and segment rows given
    dry = service.quote("A1", "B2", persist=False)
    assert dry["fare"] == 2.5 and dry["fare_source"] == "flat"
    assert dry["reference_fare"] == 4.0
    assert dry["path"] == ["A1", "A2", "B1", "B2"]
    assert round(sum(s["price"] for s in dry["segments"]), 2) == 4.0

    # write it; opening by id still shows the flat price
    persisted = service.quote("A1", "B2", persist=True)
    rid = persisted["run_id"]
    assert rid is not None
    opened = _result(service.history_item(rid))
    assert opened["fare"] == 2.5
    assert opened["reference_fare"] == 4.0
    assert opened["segment_total"] == 4.0
    assert opened["fare_source"] == "flat"

    # expand the persisted segments by the current table: row sum is the
    # step-table price by station count, not the flat price
    assert round(sum(s["price"] for s in opened["segments"]), 2) == 4.0

    # delete the flat fare: new read-only quote falls back to the step table
    assert service.delete_flat_fare("A1", "B2") is True
    after = service.quote("A1", "B2", persist=False)
    assert after["fare_source"] == "steps"
    assert after["fare"] == after["reference_fare"] == after["segment_total"] == 4.0

    # the already-written record must not change back with the deletion
    reopened = _result(service.history_item(rid))
    assert reopened["fare"] == 2.5
    assert reopened["reference_fare"] == reopened["segment_total"] == 4.0
    assert reopened["fare_source"] == "flat"


def test_no_flat_hit_pays_step_price_and_persists(service):
    q = service.quote("A1", "B2", persist=True)
    assert q["fare_source"] == "steps"
    assert q["fare"] == q["reference_fare"] == q["segment_total"] == 4.0
    stored = _result(service.history_item(q["run_id"]))
    assert stored["fare"] == stored["reference_fare"] == 4.0


def test_duplicate_pair_rejected_without_touching_existing(service):
    service.create_flat_fare("A1", "B2", 2.5)
    before_rows = service.flat_fares()
    assert len(before_rows) == 1 and before_rows[0]["price"] == 2.5

    # a second registration for the same directed pair must be refused...
    with pytest.raises(DuplicateFlatFareError):
        service.create_flat_fare("A1", "B2", 9.0)

    # ...and must not overwrite or duplicate the existing flat fare
    rows = service.flat_fares()
    assert len(rows) == 1
    assert rows[0]["price"] == 2.5
    # reverse direction is a different pair and is allowed
    service.create_flat_fare("B2", "A1", 3.0)
    assert len(service.flat_fares()) == 2


def test_delete_unknown_pair_is_false(service):
    assert service.delete_flat_fare("A1", "A3") is False
