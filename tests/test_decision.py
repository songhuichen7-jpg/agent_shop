from src.decision import decide

def test_escalate_on_money():
    d, why = decide(category="丢件破损", sentiment="angry",
                     reply="确认丢件后按申报价值赔付[P-LOST-01]。",
                     citations=["P-LOST-01"], order=None, guardrail_flags=[], message="要赔我300美元")
    assert d == "escalate" and "赔付" in why

def test_auto_when_grounded_and_calm():
    d, why = decide(category="物流时效", sentiment="calm",
                     reply="标准时效 7-12 个工作日[P-TIME-01]。",
                     citations=["P-TIME-01"], order={"status":"在途"}, guardrail_flags=[], message="多久到")
    assert d == "auto"

def test_escalate_when_guardrail_fails():
    d, why = decide(category="物流时效", sentiment="calm", reply="3天到",
                     citations=[], order=None, guardrail_flags=["eta_promise"], message="多久")
    assert d == "escalate" and "护栏" in why
