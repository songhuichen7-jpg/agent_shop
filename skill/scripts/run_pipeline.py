#!/usr/bin/env python3
"""在线入口：OpenClaw 把商户消息作为 argv[1] 传入，打印输出契约 JSON。
副作用：每次自动写飞书多维表格看板；若 decision=escalate 自动建飞书任务。
（评测 harness 不走本脚本，直接 import src.pipeline.handle，互不影响。）
"""
import sys, json, pathlib, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
from src.pipeline import handle
from src.llm import DeepSeekClient

ACTIONS = pathlib.Path(__file__).parent / "feishu_actions.sh"


def _side_effect(out: dict, msg: str) -> None:
    """飞书副作用，best-effort、不阻塞主流程。"""
    payload = json.dumps(out, ensure_ascii=False)
    try:
        subprocess.run(["bash", str(ACTIONS), "log", payload],
                       check=False, capture_output=True, timeout=30)
    except Exception:
        pass
    if out.get("decision") == "escalate":
        cat = out.get("category", "?")
        why = out.get("escalate_reason", "")
        cits = ",".join(out.get("citations") or []) or "-"
        body = f"原因: {why} | 引用: {cits} | 商户消息: {msg[:140]}"
        try:
            subprocess.run(["bash", str(ACTIONS), "escalate",
                            f"客诉升级: {cat}", body],
                           check=False, capture_output=True, timeout=30)
        except Exception:
            pass


if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    out = handle(msg, DeepSeekClient())
    print(json.dumps(out, ensure_ascii=False))
    _side_effect(out, msg)
