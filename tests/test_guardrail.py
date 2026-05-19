from src.guardrail import check_no_overpromise

def test_flags_specific_eta():
    bad = check_no_overpromise("您的包裹将在 3 天内送达。", llm=None)
    assert bad and "eta" in bad[0]

def test_flags_money_promise():
    bad = check_no_overpromise("我们保证赔付 200 美元。", llm=None)
    assert bad and "payout" in bad[0]

def test_clean_reply_ok():
    assert check_no_overpromise("标准时效为 7-12 个工作日[P-TIME-01]。", llm=None) == []
