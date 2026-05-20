import re

from src.rules import load_reference

CATEGORIES = {"物流时效","丢件破损","费用与对账争议","清关问题","退件与拒收","一般咨询"}
_LOST_DAMAGE_SIGNAL = re.compile(
    r"丢件|丢失|破损|损坏|少件|缺件|"
    r"\b(lost|damaged?|damage|missing items?|items? missing|declared value)\b"
)
_TRACKING_EXCEPTION_SIGNAL = re.compile(
    r"(轨迹|物流|tracking).{0,20}(异常|exception|no update|hasn'?t updated|not updated|没有更新|未更新)"
)
_FEE_SIGNAL = re.compile(
    r"计费重量|重量系数|体积重|对账|账单|附加费|"
    r"chargeable weight|volumetric|billing|invoice|surcharge"
)
_CUSTOMS_SIGNAL = re.compile(
    r"清关|海关|商业发票|HS\s*编码|"
    r"customs|commercial invoice|HS\s*code"
)


def _normalize_category(message: str, category: str) -> str:
    m = message.lower()
    if _LOST_DAMAGE_SIGNAL.search(m):
        return "丢件破损"
    if _CUSTOMS_SIGNAL.search(m):
        return "清关问题"
    if _FEE_SIGNAL.search(m):
        return "费用与对账争议"
    if _TRACKING_EXCEPTION_SIGNAL.search(m) and category == "一般咨询":
        return "物流时效"
    return category

def classify(message: str, llm) -> dict:
    prompt = load_reference("classify_prompt.md") + "\n\n商户消息：\n" + message
    out = llm.complete_json(prompt, tag="classify")
    if out.get("category") not in CATEGORIES:
        raise ValueError(f"非法类目：{out.get('category')}")
    out["category"] = _normalize_category(message, out["category"])
    out.setdefault("urgency","normal"); out.setdefault("language","zh"); out.setdefault("sentiment","calm")
    return out
