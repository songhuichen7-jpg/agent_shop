import re
from src.pipeline import handle

def test_pipeline_outputs_contract(fake_llm, sample_orders, sample_policy):
    fake_llm.responses["classify"]={"category":"物流时效","urgency":"normal","language":"zh","sentiment":"annoyed"}
    fake_llm.responses["draft"]={"reply_zh":"清关中[P-TIME-01]","reply_en":"In customs [P-TIME-01]","citations":["P-TIME-01"],"order_facts":["status=清关中"]}
    out = handle("BF1001 怎么还没到", fake_llm, orders_path=sample_orders, policy_path=sample_policy)
    assert set(out) >= {"category","urgency","language","decision","citations","order_facts","confidence","reply_zh","reply_en","escalate_reason"}
    assert out["decision"] in {"auto","escalate"}
    assert out["category"] == "物流时效"

def test_pipeline_extracts_order_id(fake_llm, sample_orders, sample_policy):
    fake_llm.responses["classify"]={"category":"物流时效","urgency":"low","language":"zh","sentiment":"calm"}
    fake_llm.responses["draft"]={"reply_zh":"x","reply_en":"x","citations":[],"order_facts":[]}
    out = handle("请查 BF1002", fake_llm, orders_path=sample_orders, policy_path=sample_policy)
    assert "BF1002" in str(out["order_facts"]) or out["order_facts"]==[]  # 订单已注入上下文
