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
    """离线评测/开发用 + 在线 OpenClaw 容器内本地联调用。

    优先用 openai SDK；SDK 不可用时（如 OpenClaw 容器内 python 无 pip）
    回退到纯 stdlib urllib 直接打 DeepSeek 的 OpenAI 兼容 /chat/completions，
    零第三方依赖，行为等价。
    """
    _SYS = "Return only valid JSON. 输出必须是可解析的 json。"

    def __init__(self, model=None):
        api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("ONLINE_LLM_KEY")
        if not api_key:
            raise RuntimeError("缺少 DEEPSEEK_API_KEY；也可临时复用 ONLINE_LLM_KEY")
        self.api_key = api_key
        self.model = model or os.environ.get("DEEPSEEK_EVAL_MODEL", "deepseek-v4-pro")
        self.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
        self.reasoning = os.environ.get("DEEPSEEK_REASONING_EFFORT", "high")
        self.thinking = os.environ.get("DEEPSEEK_THINKING", "enabled")
        try:
            from openai import OpenAI
            self._sdk = OpenAI(api_key=api_key, base_url=self.base_url)
        except Exception:
            self._sdk = None  # 回退 urllib

    def _body(self, prompt: str) -> dict:
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._SYS},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "stream": False,
            "reasoning_effort": self.reasoning,
            "thinking": {"type": self.thinking},
        }

    def _via_urllib(self, prompt: str) -> str:
        import urllib.request
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(self._body(prompt)).encode("utf-8"),
            headers={"Authorization": "Bearer " + self.api_key,
                     "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    def _raw(self, prompt: str) -> str:
        if self._sdk is not None:
            m = self._sdk.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._SYS},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                stream=False,
                reasoning_effort=self.reasoning,
                extra_body={"thinking": {"type": self.thinking}},
            )
            return m.choices[0].message.content or ""
        return self._via_urllib(prompt) or ""

    def complete_json(self, prompt: str, tag: str) -> dict:
        # 推理模型偶发空/非 JSON 响应或瞬时网络错误：重试，避免一行坏响应
        # 葬送整轮评测。最终仍失败才抛（调用方/run_eval 兜底记录）。
        import time
        last = None
        for attempt in range(4):
            try:
                txt = self._raw(prompt)
                if txt.strip():
                    return parse_json_text(txt)
                last = ValueError("empty LLM content")
            except Exception as e:  # noqa: BLE001 — 含 JSONDecodeError / 网络
                last = e
            time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"complete_json[{tag}] 重试 4 次仍失败: {last}")
