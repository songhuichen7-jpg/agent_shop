import json, os
from typing import Optional, Protocol

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

    支持 DeepSeek 与 Mimo 的 OpenAI 兼容接口。优先用 openai SDK；SDK 不可用时
    （如 OpenClaw 容器内 python 无 pip）回退到纯 stdlib urllib，零第三方依赖。
    """
    _SYS = "Return only valid JSON. 输出必须是可解析的 json。"

    def __init__(self, model=None):
        self.provider = os.environ.get("ONLINE_LLM_PROVIDER", "deepseek").lower()
        if self.provider in {"mimo", "xiaomi"}:
            self.provider = "mimo"
        api_key = self._api_key()
        if not api_key:
            raise RuntimeError("缺少 LLM API Key；Mimo 请设置 MIMO_API_KEY 或 ONLINE_LLM_KEY")
        self.api_key = api_key
        self.model = model or self._model()
        self.base_url = self._base_url()
        self.reasoning = os.environ.get("DEEPSEEK_REASONING_EFFORT", "high")
        self.thinking = self._thinking()
        self.temperature = float(os.environ.get("MIMO_TEMPERATURE", "0.3"))
        self.top_p = float(os.environ.get("MIMO_TOP_P", "0.95"))
        self.max_completion_tokens = int(os.environ.get("MIMO_MAX_COMPLETION_TOKENS", "2048"))
        try:
            from openai import OpenAI
            self._sdk = OpenAI(api_key=api_key, base_url=self.base_url)
        except Exception:
            self._sdk = None  # 回退 urllib

    def _api_key(self) -> Optional[str]:
        if self.provider == "mimo":
            return os.environ.get("MIMO_API_KEY") or os.environ.get("ONLINE_LLM_KEY")
        return os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("ONLINE_LLM_KEY")

    def _model(self) -> str:
        if self.provider == "mimo":
            return os.environ.get("ONLINE_LLM_MODEL") or os.environ.get("MIMO_MODEL", "mimo-v2-flash")
        return os.environ.get("ONLINE_LLM_MODEL") or os.environ.get("DEEPSEEK_EVAL_MODEL", "deepseek-v4-pro")

    def _base_url(self) -> str:
        if self.provider == "mimo":
            return (os.environ.get("ONLINE_LLM_BASE_URL") or os.environ.get("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")).rstrip("/")
        return os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")

    def _thinking(self) -> str:
        if self.provider == "mimo":
            return os.environ.get("MIMO_THINKING", "disabled")
        return os.environ.get("DEEPSEEK_THINKING", "enabled")

    def _body(self, prompt: str) -> dict:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._SYS},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "stream": False,
            "thinking": {"type": self.thinking},
        }
        if self.provider == "mimo":
            body.update({
                "temperature": self.temperature,
                "top_p": self.top_p,
                "max_completion_tokens": self.max_completion_tokens,
            })
        else:
            body["reasoning_effort"] = self.reasoning
        return body

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
            body = self._body(prompt)
            extra_body = {"thinking": body.pop("thinking")}
            if "reasoning_effort" in body:
                body["reasoning_effort"] = body.pop("reasoning_effort")
            m = self._sdk.chat.completions.create(**body, extra_body=extra_body)
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
