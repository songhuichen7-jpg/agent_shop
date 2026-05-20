#!/usr/bin/env python3
"""在线入口：OpenClaw 把商户消息作为 argv[1] 传入，打印输出契约 JSON。
副作用：每次自动写飞书多维表格看板；若 decision=escalate 自动建飞书任务。
（评测 harness 不走本脚本，直接 import src.pipeline.handle，互不影响。）
"""
import os, sys, json, pathlib, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
from src.pipeline import handle
from src.llm import DeepSeekClient

ACTIONS = pathlib.Path(__file__).parent / "feishu_actions.sh"


def _run_action(label: str, args: list[str]) -> bool:
    try:
        result = subprocess.run(args, check=False, capture_output=True, text=True, timeout=30)
    except Exception as exc:
        print(f"feishu {label} failed: {exc}", file=sys.stderr)
        return False
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        print(f"feishu {label} failed: {detail[:1000]}", file=sys.stderr)
        return False
    return True


def _side_effect(out: dict, msg: str) -> None:
    """飞书副作用，best-effort、不阻塞主流程。"""
    action_payload = dict(out)
    action_payload["message"] = msg
    if os.environ.get("FEISHU_MESSAGE_ID"):
        action_payload["message_id"] = os.environ["FEISHU_MESSAGE_ID"]
    payload = json.dumps(action_payload, ensure_ascii=False)
    _run_action("log", ["bash", str(ACTIONS), "log", payload])
    if out.get("decision") == "escalate":
        cat = out.get("category", "?")
        why = out.get("escalate_reason", "")
        cits = ",".join(out.get("citations") or []) or "-"
        order_id = out.get("order_id") or "-"
        body = f"订单: {order_id} | 原因: {why} | 引用: {cits} | 商户消息: {msg[:140]}"
        _run_action("escalate", ["bash", str(ACTIONS), "escalate",
                                 f"客诉升级: {cat}", body])


if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    out = handle(msg, DeepSeekClient())
    print(json.dumps(out, ensure_ascii=False))
    _side_effect(out, msg)
