from src.classify import classify

def test_classify_uses_llm_and_validates(fake_llm):
    fake_llm.responses["classify"] = {"category":"物流时效","urgency":"normal","language":"zh","sentiment":"annoyed"}
    out = classify("我的包裹很久没到", fake_llm)
    assert out["category"] == "物流时效"
    assert fake_llm.calls[0][0] == "classify"

def test_classify_overrides_lost_tracking_misclassification(fake_llm):
    fake_llm.responses["classify"] = {"category":"物流时效","urgency":"normal","language":"zh","sentiment":"calm"}
    out = classify("BF1200的包裹显示轨迹已经3天没有更新了，是不是丢件了？", fake_llm)
    assert out["category"] == "丢件破损"

def test_classify_overrides_tracking_exception_to_logistics(fake_llm):
    fake_llm.responses["classify"] = {"category":"一般咨询","urgency":"normal","language":"en","sentiment":"calm"}
    out = classify("I noticed the tracking for BF1020 shows 'exception'. What does that mean?", fake_llm)
    assert out["category"] == "物流时效"

def test_classify_overrides_declared_value_refund_to_loss(fake_llm):
    fake_llm.responses["classify"] = {"category":"物流时效","urgency":"high","language":"en","sentiment":"angry"}
    out = classify("BF1015 tracking hasn't updated in 32 days. I want a full refund of the declared value today.", fake_llm)
    assert out["category"] == "丢件破损"

def test_classify_overrides_chargeable_weight_to_fee(fake_llm):
    fake_llm.responses["classify"] = {"category":"一般咨询","urgency":"normal","language":"zh","sentiment":"calm"}
    out = classify("我想更改API对接的计费重量系数，流程是怎么样的？", fake_llm)
    assert out["category"] == "费用与对账争议"

def test_classify_commercial_invoice_hs_code_is_customs(fake_llm):
    fake_llm.responses["classify"] = {"category":"费用与对账争议","urgency":"normal","language":"en","sentiment":"calm"}
    out = classify("The commercial invoice for order BF1055 is missing the HS code. Will this cause a problem at customs?", fake_llm)
    assert out["category"] == "清关问题"

def test_classify_rejects_bad_category(fake_llm):
    fake_llm.responses["classify"] = {"category":"乱写","urgency":"normal","language":"zh","sentiment":"calm"}
    import pytest
    with pytest.raises(ValueError):
        classify("x", fake_llm)
