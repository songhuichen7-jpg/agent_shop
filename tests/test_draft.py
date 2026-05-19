from src.draft import draft_reply

def test_draft_returns_bilingual_with_citations(fake_llm):
    fake_llm.responses["draft"] = {"reply_zh":"您的包裹在清关中[P-TIME-01]。","reply_en":"Your parcel is in customs [P-TIME-01].","citations":["P-TIME-01"],"order_facts":["status=清关中"]}
    out = draft_reply("消息", order={"status":"清关中"}, clauses=[{"clause_id":"P-TIME-01"}], llm=fake_llm)
    assert out["reply_zh"] and out["reply_en"]
    assert out["citations"] == ["P-TIME-01"]
    assert fake_llm.calls[0][0] == "draft"
