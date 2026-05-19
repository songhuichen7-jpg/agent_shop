def baseline_handle(message: str, llm) -> dict:
    prompt = ("你是跨境物流客服，直接用中英双语回复以下消息，并输出 JSON "
              '{"category":6选1,"decision":"auto|escalate","citations":[],'
              '"reply_zh":"...","reply_en":"..."}。类目：物流时效|丢件破损|'
              "费用与对账争议|清关问题|退件与拒收|一般咨询。\n消息：" + message)
    out = llm.complete_json(prompt, tag="baseline")
    out.setdefault("citations", [])
    return out
