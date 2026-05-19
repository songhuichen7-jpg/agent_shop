from src.guardrail import check_no_overpromise
from src.guardrail import check_grounding

def test_flags_specific_eta():
    bad = check_no_overpromise("您的包裹将在 3 天内送达。", llm=None)
    assert bad and "eta" in bad[0]

def test_flags_money_promise():
    bad = check_no_overpromise("我们保证赔付 200 美元。", llm=None)
    assert bad and "payout" in bad[0]

def test_clean_reply_ok():
    assert check_no_overpromise("标准时效为 7-12 个工作日[P-TIME-01]。", llm=None) == []

def test_grounding_passes_when_cited():
    r = check_grounding("清关中[P-TIME-01]，预计按标准时效。", citations=["P-TIME-01"], order_facts=[])
    assert r == []

def test_grounding_flags_uncited_factual_claim():
    r = check_grounding("您的包裹已被海关扣押需缴税 50 美元。", citations=[], order_facts=[])
    assert r  # 无引用的事实断言被标记
