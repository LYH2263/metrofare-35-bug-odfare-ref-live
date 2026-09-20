"""一口价全链路规约测试（service 层，与路由调用的代码路径一致）。

覆盖：
1. 命中一口价时试算应付=一口价，仍给出途经与分段参考价
2. 写入后按编号打开，应付仍是一口价
3. 记录的分段参考按现行表再展开=按站数分段价，不等于一口价
4. 删除一口价后，新的只读试算回到分段表
5. 已写入记录的应付与当时参考合计不得跟着删除变回分段价
6. 未命中一口价时，应付与参考合计都按站数分段价落
7. 同一对起终点重复登记一口价须拒绝，且失败不得改已有一口价
8. 当场只读两次，库里条数保持原样
"""

import json
import os
import tempfile

# 必须在 import app.db 之前指向临时目录，测试不碰真实库
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="metrofare-test-")

from app import seed  # noqa: E402
from app.db import connect  # noqa: E402
from app.services.metro_service import DuplicateFlatFareError, MetroService  # noqa: E402

seed.init_db()

START, END = "A1", "B2"  # 种子网络中 A1->B2 为 3 站
STEP_FARE = 4.0          # 现行分段表：3 站 -> 4.0
FLAT_FARE = 2.5


def reset_state():
    conn = connect()
    conn.execute("DELETE FROM flat_fares")
    conn.execute("DELETE FROM calc_runs")
    conn.commit()
    conn.close()


def run_count():
    conn = connect()
    n = conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
    conn.close()
    return n


def stored_result(run_id):
    """直接读库里的快照，绕过任何重算逻辑。"""
    conn = connect()
    row = conn.execute("SELECT result_json FROM calc_runs WHERE id=?", (run_id,)).fetchone()
    conn.close()
    return json.loads(row["result_json"])


def opened_result(run_id):
    """按编号打开（GET /api/history/{id} 走的逻辑）。"""
    with MetroService() as s:
        row = s.history_item(run_id)
    return json.loads(row["result_json"])


def register_flat(price=FLAT_FARE):
    with MetroService() as s:
        return s.create_flat_fare(START, END, price)


def test_flat_hit_quote_shows_path_and_reference():
    reset_state()
    register_flat()
    with MetroService() as s:
        q = s.quote(START, END, persist=False)
    assert q["fare"] == FLAT_FARE               # 应付=一口价
    assert q["fare_source"] == "flat"
    assert q["reference_fare"] == STEP_FARE     # 仍给分段参考价
    assert q["path"] == ["A1", "A2", "B1", "B2"]  # 仍给途经
    assert q["hops"] == 3


def test_persisted_record_reopened_by_id():
    reset_state()
    register_flat()
    with MetroService() as s:
        q = s.quote(START, END, persist=True)
    assert q["run_id"] is not None
    opened = opened_result(q["run_id"])
    assert opened["fare"] == FLAT_FARE            # 应付仍是一口价
    assert opened["fare_source"] == "flat"
    # 分段参考按现行表再展开 = 按站数取出的分段价，不等于一口价
    assert opened["reference_fare"] == STEP_FARE != FLAT_FARE


def test_delete_flat_fare_reverts_new_quotes_but_not_history():
    reset_state()
    register_flat()
    with MetroService() as s:
        q = s.quote(START, END, persist=True)
    run_id = q["run_id"]

    with MetroService() as s:
        assert s.delete_flat_fare(START, END) is True

    # 新的只读试算回到分段表
    with MetroService() as s:
        q2 = s.quote(START, END, persist=False)
    assert q2["fare"] == STEP_FARE and q2["fare_source"] == "steps"
    assert q2["reference_fare"] == STEP_FARE

    # 已写入记录：按编号打开，应付与当时参考合计不得跟着删除变回分段价
    opened = opened_result(run_id)
    assert opened["fare"] == FLAT_FARE
    assert opened["fare_source"] == "flat"
    assert opened["reference_fare"] == STEP_FARE
    # 库里的快照本身也不许被回写
    assert stored_result(run_id) == {
        "start": START,
        "end": END,
        "hops": 3,
        "path": ["A1", "A2", "B1", "B2"],
        "fare": FLAT_FARE,
        "reference_fare": STEP_FARE,
        "fare_source": "flat",
        "reachable": True,
    }


def test_quote_without_flat_falls_to_step_table():
    reset_state()
    with MetroService() as s:
        q = s.quote(START, END, persist=False)
    assert q["fare"] == STEP_FARE
    assert q["reference_fare"] == STEP_FARE
    assert q["fare_source"] == "steps"


def test_duplicate_flat_fare_rejected_without_modifying_existing():
    reset_state()
    register_flat(price=FLAT_FARE)
    try:
        register_flat(price=9.9)
        raised = None
    except DuplicateFlatFareError as e:
        raised = e
    assert raised is not None  # 同一对起终点重复登记须拒绝
    with MetroService() as s:
        rows = s.flat_fares()
    assert len(rows) == 1                       # 失败不得新增
    assert rows[0]["price"] == FLAT_FARE        # 失败不得改已有一口价


def test_readonly_quotes_do_not_change_row_count():
    reset_state()
    before = run_count()
    with MetroService() as s:
        s.quote(START, END, persist=False)
        s.quote(START, END, persist=False)      # 当场只读两次
    assert run_count() == before                # 库里条数保持原样
