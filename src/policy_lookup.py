import json, pathlib, re
_DEFAULT = pathlib.Path(__file__).parent.parent / "data" / "policy_kb.json"

def _tokens(q: str):
    # ascii 词 (>=2 字母) + 单个非 ascii 字符（中文等）。中文无 \W 词边界，
    # 必须按字匹配，否则整串中文会变成一个永不命中的巨型 token。
    ascii_toks = [t for t in re.split(r"\W+", q.lower()) if len(t) >= 2 and t.isascii()]
    cjk = [ch for ch in q if not ch.isascii() and not ch.isspace()]
    return ascii_toks + cjk

def _score(q: str, clause: dict) -> int:
    text = (clause["zh"] + clause["en"]).lower()
    return sum(1 for t in _tokens(q) if t in text)

def lookup_policy(query: str, category: str, path=None, k: int = 3):
    kb = json.loads(pathlib.Path(path or _DEFAULT).read_text())
    pool = [c for c in kb if c["category"] == category]
    scored = sorted(((_score(query, c), c) for c in pool), key=lambda x: -x[0])
    return [c for s, c in scored if s > 0][:k]
