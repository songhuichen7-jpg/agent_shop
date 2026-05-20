from src.guardrail import check_no_overpromise
from src.guardrail import check_grounding

def test_flags_specific_eta():
    bad = check_no_overpromise("您的包裹将在 3 天内送达。", llm=None)
    assert bad and "eta" in bad[0]

def test_policy_time_window_is_not_eta_promise():
    assert check_no_overpromise("退件商品须在南非海外仓签收后 7 个工作日内完成质检。") == []
    assert check_no_overpromise("清关失败且无法纠正的包裹将在 14 个工作日内原路退回。") == []

def test_policy_loss_threshold_is_not_eta_promise():
    assert check_no_overpromise("Tracking must show no update for 30 days before the parcel can be declared lost.") == []

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
