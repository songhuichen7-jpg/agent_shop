from src.classify import classify

def test_classify_uses_llm_and_validates(fake_llm):
    fake_llm.responses["classify"] = {"category":"物流时效","urgency":"normal","language":"zh","sentiment":"annoyed"}
    out = classify("我的包裹很久没到", fake_llm)
    assert out["category"] == "物流时效"
    assert fake_llm.calls[0][0] == "classify"

def test_classify_rejects_bad_category(fake_llm):
    fake_llm.responses["classify"] = {"category":"乱写","urgency":"normal","language":"zh","sentiment":"calm"}
    import pytest
    with pytest.raises(ValueError):
        classify("x", fake_llm)
