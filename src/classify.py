from src.rules import load_reference

CATEGORIES = {"物流时效","丢件破损","费用与对账争议","清关问题","退件与拒收","一般咨询"}

def classify(message: str, llm) -> dict:
    prompt = load_reference("classify_prompt.md") + "\n\n商户消息：\n" + message
    out = llm.complete_json(prompt, tag="classify")
    if out.get("category") not in CATEGORIES:
        raise ValueError(f"非法类目：{out.get('category')}")
    out.setdefault("urgency","normal"); out.setdefault("language","zh"); out.setdefault("sentiment","calm")
    return out
