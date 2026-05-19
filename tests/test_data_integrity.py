import json, pathlib, re
DATA = pathlib.Path(__file__).parent.parent / "data"
CATEGORIES = {"物流时效","丢件破损","费用与对账争议","清关问题","退件与拒收","一般咨询"}

def load(name): return json.loads((DATA / name).read_text())

def test_policy_kb_schema():
    kb = load("policy_kb.json")
    assert 20 <= len(kb) <= 30, f"政策条款数应 20-30，实际 {len(kb)}"
    ids = set()
    for c in kb:
        assert set(c) >= {"clause_id","category","zh","en"}
        assert re.fullmatch(r"P-[A-Z]+-\d{2}", c["clause_id"]), c["clause_id"]
        assert c["category"] in CATEGORIES
        assert c["zh"].strip() and c["en"].strip()
        assert c["clause_id"] not in ids, f"重复 clause_id {c['clause_id']}"
        ids.add(c["clause_id"])
    cats = {c["category"] for c in kb}
    assert cats == CATEGORIES, f"每个类目至少 1 条，缺 {CATEGORIES - cats}"

STATUSES = {"在途","清关中","已签收","异常","退件","丢件"}

def test_orders_schema():
    orders = load("orders.json")
    assert 200 <= len(orders) <= 400, f"订单数应 200-400，实际 {len(orders)}"
    ids = set()
    for o in orders:
        assert set(o) >= {"order_id","merchant_id","route","status","events","exception","ship_date"}
        assert o["order_id"] not in ids; ids.add(o["order_id"])
        assert o["status"] in STATUSES
        assert isinstance(o["events"], list) and o["events"]
    assert {o["status"] for o in orders} == STATUSES, "每种状态至少 1 单"

def test_testset_schema_and_refs():
    lines = (DATA / "testset.jsonl").read_text().splitlines()
    rows = [json.loads(l) for l in lines if l.strip()]
    assert 60 <= len(rows) <= 80, f"测试集应 60-80，实际 {len(rows)}"
    kb_ids = {c["clause_id"] for c in load("policy_kb.json")}
    order_ids = {o["order_id"] for o in load("orders.json")}
    n_escalate = 0
    for r in rows:
        assert set(r) >= {"id","message","gold_category","gold_decision","gold_citations","must_not_promise","referenced_order"}
        assert r["gold_category"] in CATEGORIES
        assert r["gold_decision"] in {"auto","escalate"}
        for cid in r["gold_citations"]:
            assert cid in kb_ids, f"{r['id']} 引用了不存在条款 {cid}"
        if r["referenced_order"]:
            assert r["referenced_order"] in order_ids, f"{r['id']} 引用了不存在订单"
        assert isinstance(r["must_not_promise"], bool)
        n_escalate += r["gold_decision"] == "escalate"
    assert n_escalate >= 12, "必须升级样本至少 12 条"
    assert sum(r["must_not_promise"] for r in rows) >= 8, "对抗样本至少 8 条"
