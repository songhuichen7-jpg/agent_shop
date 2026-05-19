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
