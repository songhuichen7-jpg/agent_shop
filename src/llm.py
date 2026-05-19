import json, os
from typing import Protocol

class LLMClient(Protocol):
    def complete_json(self, prompt: str, tag: str) -> dict: ...

def parse_json_text(text: str) -> dict:
    text = (text or "").strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        text = text.lstrip("json").strip()
    return json.loads(text)

class DeepSeekClient:
    """离线评测/开发用。在线由 OpenClaw 绑定 DeepSeek 模型执行 SKILL.md。"""
    def __init__(self, model=None):
        from openai import OpenAI
        api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("ONLINE_LLM_KEY")
        if not api_key:
            raise RuntimeError("缺少 DEEPSEEK_API_KEY；也可临时复用 ONLINE_LLM_KEY")
        self.model = model or os.environ.get("DEEPSEEK_EVAL_MODEL", "deepseek-v4-pro")
        self.c = OpenAI(
            api_key=api_key,
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )

    def complete_json(self, prompt: str, tag: str) -> dict:
        m = self.c.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Return only valid JSON. 输出必须是可解析的 json。"},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            stream=False,
            reasoning_effort=os.environ.get("DEEPSEEK_REASONING_EFFORT", "high"),
            extra_body={"thinking": {"type": os.environ.get("DEEPSEEK_THINKING", "enabled")}},
        )
        return parse_json_text(m.choices[0].message.content)
