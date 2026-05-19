import re
from src.classify import classify
from src.draft import draft_reply
from src.order_lookup import lookup_order
from src.policy_lookup import lookup_policy

ORDER_RE = re.compile(r"BF\d{4,}")

def handle(message: str, llm, orders_path=None, policy_path=None) -> dict:
    cls = classify(message, llm)
    m = ORDER_RE.search(message)
    order = lookup_order(m.group(0), path=orders_path) if m else None
    clauses = lookup_policy(message, cls["category"], path=policy_path)
    d = draft_reply(message, order, clauses, llm)
    return {
        "category": cls["category"], "urgency": cls["urgency"],
        "language": cls["language"], "sentiment": cls["sentiment"],
        "decision": "auto", "escalate_reason": "",
        "citations": d.get("citations", []), "order_facts": d.get("order_facts", []),
        "confidence": 1.0 if (order or clauses) else 0.3,
        "reply_zh": d.get("reply_zh",""), "reply_en": d.get("reply_en",""),
    }
