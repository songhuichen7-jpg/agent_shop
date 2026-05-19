import json
from src.rules import load_reference

def draft_reply(message: str, order, clauses, llm) -> dict:
    ctx = {"message": message, "order": order, "clauses": clauses}
    prompt = load_reference("draft_prompt.md") + "\n\n上下文：\n" + json.dumps(ctx, ensure_ascii=False)
    out = llm.complete_json(prompt, tag="draft")
    for key in ("reply_zh","reply_en","citations","order_facts"):
        out.setdefault(key, "" if key.startswith("reply") else [])
    return out
