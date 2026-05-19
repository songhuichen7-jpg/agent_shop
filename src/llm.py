import json, os
from typing import Protocol

class LLMClient(Protocol):
    def complete_json(self, prompt: str, tag: str) -> dict: ...

class ClaudeClient:
    """离线评测/开发用。在线由 OpenClaw 绑定模型执行 SKILL.md，不走这里。"""
    def __init__(self, model="claude-opus-4-7"):
        from anthropic import Anthropic
        self.c = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = model
    def complete_json(self, prompt: str, tag: str) -> dict:
        m = self.c.messages.create(model=self.model, max_tokens=1024,
              messages=[{"role":"user","content":prompt}])
        text = m.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1].lstrip("json").strip()
        return json.loads(text)
