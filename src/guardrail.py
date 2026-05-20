import re

# 具体时效承诺（无依据时才算违规）
_ETA = re.compile(
    r"((将在?|会在|预计在|保证|承诺).{0,12}\d+\s*(天|日|个工作日|工作日|days?)\s*(内|以内|之内)?.{0,8}(送达|到达|到货|清关通过))|"
    r"(\d+\s*(天|日|个工作日|工作日|days?)\s*(内|以内|之内)?\s*(送达|到达|到货))|"
    r"保证.{0,4}(到货|到达|送达|清关通过)|"
    r"(guarantee\w*|promise\w*|will (deliver|arrive))\b.{0,20}"
    r"(by |on |\d|deliver|arriv|business day)")
_NEGATED_PROMISE = re.compile(
    r"不能|无法|不会|不可|不保证|不承诺|不能承诺|无法保证|"
    r"cannot|can't|can not|unable|not able|do not guarantee|does not guarantee|no guarantee|cannot promise"
)
# 具体赔付承诺（无依据时才算违规）
_PAYOUT = re.compile(
    r"(赔付|退款|补偿).{0,8}\d+\s*(元|美元|USD|usd|rmb|人民币|\$)|"
    r"保证.{0,4}(赔|退|补偿)|"
    r"(will|we'?ll)\s+(pay|refund|compensate)\b.{0,12}(\$?\d|you)")
# 政策条款引用，如 [P-TIME-01]
_CITE = re.compile(r"\[[A-Z]+-[A-Z]+-\d{2}\]")
_FACTY = re.compile(r"\d|海关|扣押|赔|退|时效|清关|签收|丢件")


def check_no_overpromise(reply: str, llm=None) -> list[str]:
    """逐句检查。带政策引用 [clause] 的句子＝有据，不算乱承诺
    （引用的时效/赔付是政策事实，非 agent 私自承诺）；
    无引用的具体时效/赔付承诺才标记。空=通过。
    llm 预留参数（P3.2 逐句自检扩展位）。"""
    flags = []
    for sent in re.split(r"[。.!?！？\n]", reply):
        s = sent.strip()
        if not s or _CITE.search(s):
            continue
        if _ETA.search(s) and not _NEGATED_PROMISE.search(s.lower()) and "eta_promise" not in flags:
            flags.append("eta_promise")
        if _PAYOUT.search(s) and "payout_promise" not in flags:
            flags.append("payout_promise")
    return flags


def check_grounding(reply: str, citations: list[str], order_facts: list[str]) -> list[str]:
    flags = []
    for sent in re.split(r"[。.!?！？\n]", reply):
        s = sent.strip()
        if not s:
            continue
        if _FACTY.search(s) and not _CITE.search(s) and not citations and not order_facts:
            flags.append(f"ungrounded:{s[:20]}")
    return flags
