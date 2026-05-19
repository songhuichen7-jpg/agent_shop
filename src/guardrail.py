import re

_ETA = re.compile(r"(\d+\s*(天|日|个工作日|days?)\s*(内|以内|之内|送达|到达))|保证.*(到货|清关通过)")
_PAYOUT = re.compile(r"(赔付|退款|补偿).{0,6}\d+\s*(元|美元|USD|rmb|人民币)|保证.*赔")

def check_no_overpromise(reply: str, llm=None) -> list[str]:
    """返回违规标签列表，空=通过。llm 非空时追加逐句自检（P3.2）。"""
    flags = []
    if _ETA.search(reply): flags.append("eta_promise")
    if _PAYOUT.search(reply): flags.append("payout_promise")
    return flags

_CITE = re.compile(r"\[[A-Z]+-[A-Z]+-\d{2}\]")
_FACTY = re.compile(r"\d|海关|扣押|赔|退|时效|清关|签收|丢件")

def check_grounding(reply: str, citations: list[str], order_facts: list[str]) -> list[str]:
    flags = []
    for sent in re.split(r"[。.!?！？\n]", reply):
        s = sent.strip()
        if not s: continue
        if _FACTY.search(s) and not _CITE.search(s) and not citations and not order_facts:
            flags.append(f"ungrounded:{s[:20]}")
    return flags
