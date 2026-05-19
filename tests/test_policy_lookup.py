from src.policy_lookup import lookup_policy

def test_category_filter_and_keyword(sample_policy):
    hits = lookup_policy("包裹丢了要赔偿", category="丢件破损", path=sample_policy, k=2)
    assert hits and hits[0]["clause_id"] == "P-LOST-01"

def test_returns_empty_when_no_signal(sample_policy):
    hits = lookup_policy("???", category="清关问题", path=sample_policy, k=2)
    assert hits == []
