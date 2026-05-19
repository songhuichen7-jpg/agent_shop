#!/usr/bin/env python3
"""在线入口：OpenClaw 把商户消息作为 argv[1] 传入，打印输出契约 JSON。"""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
from src.pipeline import handle
from src.llm import DeepSeekClient  # 占位：在线由 OpenClaw 模型执行 SKILL.md；此脚本供本地联调

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    print(json.dumps(handle(msg, DeepSeekClient()), ensure_ascii=False))
