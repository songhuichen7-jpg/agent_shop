import re

_ETA = re.compile(r"(\d+\s*(天|日|个工作日|days?)\s*(内|以内|之内|送达|到达))|保证.*(到货|清关通过)")
_PAYOUT = re.compile(r"(赔付|退款|补偿).{0,6}\d+\s*(元|美元|USD|rmb|人民币)|保证.*赔")

def check_no_overpromise(reply: str, llm=None) -> list[str]:
    """返回违规标签列表，空=通过。llm 非空时追加逐句自检（P3.2）。"""
    flags = []
    if _ETA.search(reply): flags.append("eta_promise")
    if _PAYOUT.search(reply): flags.append("payout_promise")
    return flags
