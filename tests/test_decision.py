from src.decision import decide

def test_escalate_on_money():
    d, why = decide(category="丢件破损", sentiment="angry",
                     reply="确认丢件后按申报价值赔付[P-LOST-01]。",
                     citations=["P-LOST-01"], order=None, guardrail_flags=[], message="要赔我300美元")
    assert d == "escalate" and "赔付" in why

def test_auto_for_policy_compensation_question_without_amount_demand():
    d, why = decide(category="丢件破损", sentiment="calm",
                     reply="缺少开箱视频的破损赔付不予受理[P-LOST-02]。",
                     citations=["P-LOST-02"], order={"status": "已签收"}, guardrail_flags=[],
                     message="没有拍开箱视频，可以赔付吗？订单BF1155")
    assert d == "auto" and why == ""

def test_auto_for_low_value_auto_writeoff_question():
    d, why = decide(category="费用与对账争议", sentiment="calm",
                     reply="低于 50 元的争议条目会自动冲销[P-FEE-04]。",
                     citations=["P-FEE-04"], order=None, guardrail_flags=[],
                     message="账单里有笔48元的争议条目，你们说系统会自动冲销？那我什么都不用做了吗？")
    assert d == "auto" and why == ""

def test_auto_when_buyer_demands_merchant_compensation_but_merchant_asks_sla():
    d, why = decide(category="物流时效", sentiment="annoyed",
                     reply="双 11 期间 SLA 放宽至 18 个工作日[P-TIME-05]。",
                     citations=["P-TIME-05"], order={"status": "在途"}, guardrail_flags=[],
                     message="买家要求我赔偿损失，你们SLA怎么算的？")
    assert d == "auto" and why == ""

def test_escalate_when_merchant_demands_refund_amount():
    d, why = decide(category="费用与对账争议", sentiment="angry",
                     reply="旺季附加费按公告价执行[P-FEE-03]。",
                     citations=["P-FEE-03"], order={"status": "在途"}, guardrail_flags=[],
                     message="I demand a refund of 300 RMB immediately for order BF1130.")
    assert d == "escalate" and "赔付" in why

def test_auto_for_return_process_question_not_refund():
    d, why = decide(category="退件与拒收", sentiment="calm",
                     reply="买家拒收导致的退件，退件运费及仓储费由商家承担[P-RETURN-01]。",
                     citations=["P-RETURN-01"], order={"status": "拒收"}, guardrail_flags=[],
                     message="买家拒收了BF1135的包裹，现在需要退回来，退件运费谁出？")
    assert d == "auto" and why == ""

def test_escalate_when_merchant_demands_exact_return_date():
    d, why = decide(category="清关问题", sentiment="annoyed",
                     reply="无法纠正的清关失败包裹会按政策退回[P-CUSTOMS-04]。",
                     citations=["P-CUSTOMS-04"], order={"status": "清关失败"}, guardrail_flags=[],
                     message="When exactly will it be returned to me? Please promise me a return date.")
    assert d == "escalate" and "承诺" in why

def test_auto_when_grounded_and_calm():
    d, why = decide(category="物流时效", sentiment="calm",
                     reply="标准时效 7-12 个工作日[P-TIME-01]。",
                     citations=["P-TIME-01"], order={"status":"在途"}, guardrail_flags=[], message="多久到")
    assert d == "auto"

def test_escalate_when_guardrail_fails():
    d, why = decide(category="物流时效", sentiment="calm", reply="3天到",
                     citations=[], order=None, guardrail_flags=["eta_promise"], message="多久")
    assert d == "escalate" and "护栏" in why
