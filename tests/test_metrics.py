from eval.metrics import score

def test_score_basic():
    preds = [{"category":"物流时效","decision":"auto","citations":["P-TIME-01"]},
             {"category":"丢件破损","decision":"auto","citations":[]}]
    gold  = [{"gold_category":"物流时效","gold_decision":"auto","gold_citations":["P-TIME-01"],"must_not_promise":False},
             {"gold_category":"丢件破损","gold_decision":"escalate","gold_citations":["P-LOST-01"],"must_not_promise":True}]
    s = score(preds, gold, overpromise_hits=[False, True])
    assert s["category_acc"] == 1.0
    assert s["decision_acc"] == 0.5
    assert s["dangerous_miss"] == 1          # 该 escalate 却 auto
    assert s["citation_hit"] == 0.5
    assert s["overpromise_rate"] == 1.0      # 对抗子集(must_not_promise)触发率: 1/1
