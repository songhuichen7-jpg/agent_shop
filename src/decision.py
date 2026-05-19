import re

# 含威胁/对抗升级（差评/工单/争议/拒付/曝光）
_THREAT = re.compile(
    r"差评|1-?star|一星|曝光|工单|投诉|12315|媒体|\bmedia\b|charge ?back|"
    r"发起争议|raise a dispute|file a dispute|否则.{0,8}(争议|投诉|差评|退|赔)")
# 要求 agent 给死承诺（具体日期/时效/金额）—— 必须人工，不能由 agent 兜底承诺
_DEMAND = re.compile(
    r"承诺.{0,6}(日期|时间|到达|送达|赔)|"
    r"(具体|确切|准确|最终|firm|exact|specific|guaranteed?|definite)\s*的?\s*"
    r"(到达|送达|交付|delivery|arrival)?\s*(日期|时间|date|time|eta)|"
    r"(give|tell|need|want|provide)\b.{0,14}"
    r"(exact|specific|firm|final|guaranteed|definite)?\s*"
    r"(date|eta|arrival date|delivery date|deadline)|deadline|"
    r"保证.{0,4}(到|送|赔|清关)")
# 真正的金额纠纷/索赔诉求（区别于泛泛问“能不能赔/怎么计费”可答咨询）
_MONEY = re.compile(
    r"(必须|马上|立刻|立即|现在|now|immediately|right now).{0,8}(赔|退|pay|refund|compensat)|"
    r"要求.{0,6}(赔偿|赔付|退款|补偿|compensat|refund)|"
    r"(赔|退款|补偿|refund|compensat\w*).{0,10}(\d|多少钱|金额|amount|\$|美元|usd)|"
    r"索赔|claim\b.{0,10}\$?\d|拒付|charge ?back|赔(偿|付).{0,4}(损失|loss)")
# 清关里真正需法务/查扣处置（普通补税/格式/仓储费咨询不在内）
_CUSTOMS_HARD = re.compile(
    r"没收|销毁|查封|查扣|罚没|罚款|法务|律师|涉嫌|违禁|禁运|违规品|"
    r"prohibit|seiz|confiscat|\blegal\b|lawsuit")
# 签收后又报丢失的矛盾纠纷（需人工核实，不能 agent 定论）
_POSTDLV_LOSS = re.compile(
    r"(已?签收|系统.{0,6}签收|delivered|signed for).{0,24}(丢|没收到|未收到|lost|missing|not receiv)|"
    r"(丢失?|lost|missing|没收到|未收到).{0,24}(已?签收|系统.{0,6}签收|delivered|signed)")


def decide(category, sentiment, reply, citations, order, guardrail_flags, message):
    """规则化决策：可自动答 vs 须升级。
    原则：可由政策/订单答复的咨询走 auto；真正的硬承诺要求/威胁/金额纠纷/
    查扣法务/签收后报失/无依据 才升级。安全优先但不过度升级正常咨询。"""
    if guardrail_flags:
        return "escalate", f"护栏未过:{guardrail_flags}"
    m = message or ""
    if _DEMAND.search(m):
        return "escalate", "商户要求具体日期/金额硬承诺，需人工"
    if _THREAT.search(m):
        return "escalate", "含威胁/争议升级（差评/工单/拒付等）"
    if _MONEY.search(m):
        return "escalate", "涉赔付/退款金额认定或索赔诉求"
    if category == "清关问题" and _CUSTOMS_HARD.search(m):
        return "escalate", "海关查扣/法务/禁运"
    if category == "丢件破损" and _POSTDLV_LOSS.search(m):
        return "escalate", "签收后报失纠纷，需人工核实"
    if order is None and not citations:
        return "escalate", "订单查不到且无政策依据，置信低"
    return "auto", ""
