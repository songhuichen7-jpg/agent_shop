import re
_THREAT = re.compile(r"差评|1-?star|一星|曝光|工单|投诉|12315|media")

def decide(category, sentiment, reply, citations, order, guardrail_flags, message):
    if guardrail_flags:
        return "escalate", f"护栏未过:{guardrail_flags}"
    if category == "费用与对账争议" or re.search(r"赔|退款|补偿|refund|compensat", message):
        return "escalate", "涉赔付/退款金额认定"
    if category == "清关问题" and re.search(r"海关|扣押|缴税|法务|禁运|customs|seiz", message):
        return "escalate", "海关/法务/禁运"
    if sentiment == "angry" and _THREAT.search(message):
        return "escalate", "情绪激烈且含威胁"
    if order is None and not citations:
        return "escalate", "订单查不到且无政策依据，置信低"
    return "auto", ""
